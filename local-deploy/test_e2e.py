"""
End-to-end test: Launch Graph -> Explore -> Delete.

Covers the full lifecycle against a local K8s deployment:
  1. Create a mapping via the control plane API
  2. Upload parquet data to fake-GCS
  3. Create an instance from the mapping (auto-creates a snapshot)
  4. Patch the snapshot to "ready" (no Starburst locally)
  5. Wait for the instance to reach "running" status
  6. Run Cypher queries against the wrapper and verify results
  7. Terminate the instance and verify it is gone
  8. Clean up (delete mapping)

Prerequisites:
  - Local K8s cluster deployed via `make deploy` (OrbStack / Docker Desktop)
  - Control plane reachable at http://localhost:30081
  - Postgres port-forwarded: kubectl port-forward svc/postgres 5432:5432 -n graph-olap-local
  - Fake GCS port-forwarded: kubectl port-forward svc/fake-gcs-local 4443:4443 -n graph-olap-local

Run:
  pytest local-deploy/test_e2e.py -v -s
"""

from __future__ import annotations

import io
import time
from typing import Generator

import pandas as pd
import psycopg2
import pytest
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API = "http://localhost:30081"
GCS = "http://localhost:4443"
BUCKET = "graph-olap-local-dev"
HEADERS = {
    "X-Username": "demo@example.com",
    "X-User-Role": "admin",
    "Content-Type": "application/json",
}
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "control_plane"
DB_USER = "control_plane"
DB_PASS = "control_plane"
K8S_NAMESPACE = "graph-olap-local"

# Timeouts
INSTANCE_TIMEOUT = 240  # seconds to wait for instance to reach "running"
POLL_INTERVAL = 5  # seconds between status polls


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def api_get(path: str) -> requests.Response:
    """GET against the control plane API."""
    return requests.get(f"{API}{path}", headers=HEADERS, timeout=15)


def api_post(path: str, json: dict | None = None) -> requests.Response:
    """POST against the control plane API."""
    return requests.post(f"{API}{path}", headers=HEADERS, json=json, timeout=15)


def api_delete(path: str) -> requests.Response:
    """DELETE against the control plane API."""
    return requests.delete(f"{API}{path}", headers=HEADERS, timeout=15)


def db_execute(sql: str, params: tuple = ()) -> list:
    """Run a single SQL statement against the control-plane Postgres."""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASS,
    )
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        try:
            rows = cur.fetchall()
        except psycopg2.ProgrammingError:
            rows = []
        cur.close()
        return rows
    finally:
        conn.close()


def upload_parquet_to_gcs(df: pd.DataFrame, object_path: str) -> None:
    """Upload a DataFrame as parquet to fake-GCS."""
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    buf.seek(0)
    resp = requests.post(
        f"{GCS}/upload/storage/v1/b/{BUCKET}/o?uploadType=media&name={object_path}",
        data=buf.read(),
        headers={"Content-Type": "application/octet-stream"},
        timeout=15,
    )
    assert resp.status_code in (200, 201), (
        f"GCS upload failed for {object_path}: {resp.status_code} {resp.text[:200]}"
    )


def ensure_gcs_bucket() -> None:
    """Create the GCS bucket if it does not already exist."""
    requests.post(
        f"{GCS}/storage/v1/b",
        json={"name": BUCKET},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

TEAMS = pd.DataFrame([
    {"team_id": 1, "name": "MI"},
    {"team_id": 2, "name": "CSK"},
    {"team_id": 3, "name": "RCB"},
])

PLAYERS = pd.DataFrame([
    {"player_id": 1, "name": "Rohit", "role": "Bat"},
    {"player_id": 2, "name": "Dhoni", "role": "WK"},
    {"player_id": 3, "name": "Virat", "role": "Bat"},
])

PLAYS_FOR = pd.DataFrame([
    {"player_id": 1, "team_id": 1},
    {"player_id": 2, "team_id": 2},
    {"player_id": 3, "team_id": 3},
])

MAPPING_PAYLOAD = {
    "name": "E2E Test IPL",
    "node_definitions": [
        {
            "label": "Team",
            "sql": "SELECT team_id, name FROM teams",
            "primary_key": {"name": "team_id", "type": "INT64"},
            "properties": [{"name": "name", "type": "STRING"}],
        },
        {
            "label": "Player",
            "sql": "SELECT player_id, name, role FROM players",
            "primary_key": {"name": "player_id", "type": "INT64"},
            "properties": [
                {"name": "name", "type": "STRING"},
                {"name": "role", "type": "STRING"},
            ],
        },
    ],
    "edge_definitions": [
        {
            "type": "PLAYS_FOR",
            "sql": "SELECT player_id, team_id FROM plays_for",
            "from_node": "Player",
            "to_node": "Team",
            "from_key": "player_id",
            "to_key": "team_id",
            "properties": [],
        },
    ],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def check_prerequisites():
    """Verify the local cluster is reachable before running any tests."""
    try:
        r = api_get("/health")
        r.raise_for_status()
    except (requests.ConnectionError, requests.HTTPError) as exc:
        pytest.skip(
            f"Control plane not reachable at {API} - is the local cluster running? ({exc})"
        )


@pytest.fixture(scope="module")
def mapping_id() -> Generator[int, None, None]:
    """Create a mapping and yield its ID; delete it after all tests."""
    r = api_post("/api/mappings", json=MAPPING_PAYLOAD)
    assert r.status_code == 201, f"Failed to create mapping: {r.status_code} {r.text[:300]}"
    mid = r.json()["data"]["id"]

    yield mid

    # Cleanup: delete snapshots first (mapping delete fails if snapshots exist)
    rows = db_execute("SELECT id FROM snapshots WHERE mapping_id = %s", (mid,))
    for (sid,) in rows:
        db_execute("DELETE FROM export_jobs WHERE snapshot_id = %s", (sid,))
        db_execute("DELETE FROM snapshots WHERE id = %s", (sid,))

    resp = api_delete(f"/api/mappings/{mid}")
    assert resp.status_code in (204, 404), (
        f"Mapping cleanup failed: {resp.status_code} {resp.text[:200]}"
    )


@pytest.fixture(scope="module")
def instance_and_snapshot(mapping_id: int) -> Generator[dict, None, None]:
    """
    Create an instance from the mapping, patch snapshot to ready,
    upload data, and wait for 'running'. Yield instance info dict.
    Clean up the instance afterwards.
    """
    # Create instance (auto-creates snapshot in 'pending' status)
    r = api_post("/api/instances", json={
        "mapping_id": mapping_id,
        "wrapper_type": "falkordb",
        "name": "E2E Test Instance",
        "ttl": "PT4H",
    })
    assert r.status_code == 201, f"Failed to create instance: {r.status_code} {r.text[:300]}"
    inst = r.json()["data"]
    instance_id = inst["id"]
    snapshot_id = inst["snapshot_id"]

    # Build GCS path matching control plane convention
    gcs_prefix = f"demo@example.com/{mapping_id}/v1/{snapshot_id}"
    gcs_full = f"gs://{BUCKET}/{gcs_prefix}"

    # Ensure GCS bucket exists and upload parquet files
    ensure_gcs_bucket()
    upload_parquet_to_gcs(TEAMS, f"{gcs_prefix}/nodes/Team/data.parquet")
    upload_parquet_to_gcs(PLAYERS, f"{gcs_prefix}/nodes/Player/data.parquet")
    upload_parquet_to_gcs(PLAYS_FOR, f"{gcs_prefix}/edges/PLAYS_FOR/data.parquet")

    # Patch snapshot to "ready" (bypasses Starburst export)
    db_execute(
        "UPDATE snapshots SET status = 'ready', gcs_path = %s WHERE id = %s",
        (gcs_full, snapshot_id),
    )
    db_execute("DELETE FROM export_jobs WHERE snapshot_id = %s", (snapshot_id,))

    info = {
        "instance_id": instance_id,
        "snapshot_id": snapshot_id,
        "mapping_id": mapping_id,
        "gcs_prefix": gcs_prefix,
    }

    yield info

    # Cleanup: terminate instance (ignore 404 if already deleted by tests)
    resp = api_delete(f"/api/instances/{instance_id}")
    if resp.status_code not in (204, 404):
        print(f"WARNING: instance cleanup returned {resp.status_code}: {resp.text[:200]}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHealthCheck:
    """Smoke test: control plane is healthy."""

    def test_health_endpoint(self):
        r = api_get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body.get("status") == "healthy" or body.get("status") == "ok"


class TestMappingCreation:
    """Step 1: Mapping CRUD."""

    def test_mapping_created(self, mapping_id: int):
        """Mapping was created and has a valid ID."""
        assert isinstance(mapping_id, int)
        assert mapping_id > 0

    def test_mapping_retrievable(self, mapping_id: int):
        """Mapping can be fetched back from the API."""
        r = api_get(f"/api/mappings/{mapping_id}")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["name"] == "E2E Test IPL"
        assert len(data["node_definitions"]) == 2
        assert len(data["edge_definitions"]) == 1

    def test_mapping_has_correct_nodes(self, mapping_id: int):
        """Node definitions match what we sent."""
        r = api_get(f"/api/mappings/{mapping_id}")
        nodes = r.json()["data"]["node_definitions"]
        labels = {n["label"] for n in nodes}
        assert labels == {"Team", "Player"}

    def test_mapping_has_correct_edges(self, mapping_id: int):
        """Edge definitions match what we sent."""
        r = api_get(f"/api/mappings/{mapping_id}")
        edges = r.json()["data"]["edge_definitions"]
        assert len(edges) == 1
        assert edges[0]["type"] == "PLAYS_FOR"
        assert edges[0]["from_node"] == "Player"
        assert edges[0]["to_node"] == "Team"


class TestInstanceLifecycle:
    """Steps 3-7: Full instance lifecycle."""

    def test_instance_created(self, instance_and_snapshot: dict):
        """Instance was created and has a valid ID."""
        assert instance_and_snapshot["instance_id"] > 0
        assert instance_and_snapshot["snapshot_id"] > 0

    def test_snapshot_patched_to_ready(self, instance_and_snapshot: dict):
        """Snapshot was successfully patched to 'ready' in the DB."""
        sid = instance_and_snapshot["snapshot_id"]
        rows = db_execute("SELECT status FROM snapshots WHERE id = %s", (sid,))
        assert len(rows) == 1
        assert rows[0][0] == "ready"

    def test_instance_reaches_running(self, instance_and_snapshot: dict):
        """Instance reaches 'running' status within the timeout."""
        iid = instance_and_snapshot["instance_id"]
        start = time.time()
        final_status = None

        while time.time() - start < INSTANCE_TIMEOUT:
            r = api_get(f"/api/instances/{iid}")
            assert r.status_code == 200, f"GET instance failed: {r.status_code}"
            inst = r.json()["data"]
            final_status = inst["status"]

            if final_status == "running":
                # Store the instance URL for later tests
                instance_and_snapshot["instance_url"] = inst.get("instance_url")
                instance_and_snapshot["pod_name"] = inst.get("pod_name")
                return

            if final_status in ("failed", "stopped", "terminated"):
                error_msg = inst.get("error_message", "no error message")
                pytest.fail(
                    f"Instance {iid} ended with status '{final_status}': {error_msg}"
                )

            elapsed = int(time.time() - start)
            print(f"  [{elapsed:3d}s] status={final_status}")
            time.sleep(POLL_INTERVAL)

        pytest.fail(
            f"Instance {iid} did not reach 'running' within {INSTANCE_TIMEOUT}s "
            f"(last status: {final_status})"
        )

    def test_cypher_node_count(self, instance_and_snapshot: dict):
        """Cypher query returns correct node counts (3 Team + 3 Player = 6)."""
        self._ensure_running(instance_and_snapshot)
        url = instance_and_snapshot.get("instance_url")
        assert url, "No instance_url available"

        result = self._query_wrapper(
            url, "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt"
        )
        # Flatten into {label: count}
        counts = {row.get("label"): row.get("cnt") for row in result}
        assert counts.get("Team") == 3, f"Expected 3 Team nodes, got {counts}"
        assert counts.get("Player") == 3, f"Expected 3 Player nodes, got {counts}"

    def test_cypher_edge_count(self, instance_and_snapshot: dict):
        """Cypher query returns correct edge count (3 PLAYS_FOR edges)."""
        self._ensure_running(instance_and_snapshot)
        url = instance_and_snapshot.get("instance_url")
        assert url, "No instance_url available"

        result = self._query_wrapper(
            url, "MATCH ()-[r:PLAYS_FOR]->() RETURN count(r) AS cnt"
        )
        assert len(result) >= 1
        assert result[0].get("cnt") == 3, f"Expected 3 edges, got {result}"

    def test_cypher_traversal(self, instance_and_snapshot: dict):
        """Cypher traversal returns Rohit -> MI relationship."""
        self._ensure_running(instance_and_snapshot)
        url = instance_and_snapshot.get("instance_url")
        assert url, "No instance_url available"

        result = self._query_wrapper(
            url,
            "MATCH (p:Player {name: 'Rohit'})-[:PLAYS_FOR]->(t:Team) RETURN t.name AS team",
        )
        assert len(result) == 1
        assert result[0]["team"] == "MI"

    def test_delete_instance(self, instance_and_snapshot: dict):
        """Deleting the instance returns 204 and it becomes inaccessible."""
        iid = instance_and_snapshot["instance_id"]

        r = api_delete(f"/api/instances/{iid}")
        assert r.status_code == 204, f"Delete returned {r.status_code}: {r.text[:200]}"

        # Give reconciliation a moment to clean up
        time.sleep(2)

        # Instance should be gone (404) or in a terminal state
        r2 = api_get(f"/api/instances/{iid}")
        if r2.status_code == 200:
            status = r2.json()["data"]["status"]
            assert status in ("stopping", "terminated", "failed"), (
                f"Instance still alive with status '{status}' after delete"
            )
        else:
            assert r2.status_code == 404

    # -- helpers --

    def _ensure_running(self, info: dict) -> None:
        """Skip if instance never reached running (dependency on earlier test)."""
        if "instance_url" not in info:
            pytest.skip("Instance did not reach 'running' status")

    def _query_wrapper(
        self, wrapper_url: str, cypher: str, retries: int = 10, delay: float = 3.0
    ) -> list[dict]:
        """
        Execute a Cypher query against the wrapper, with retries.

        The wrapper pod may still be loading data right after the instance
        transitions to 'running'.
        """
        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                r = requests.post(
                    f"{wrapper_url}/query",
                    json={"query": cypher},
                    timeout=30,
                )
                r.raise_for_status()
                body = r.json()
                data = body.get("data") or body.get("results") or body

                # Handle {columns: [...], rows: [[...], ...]} format
                if isinstance(data, dict) and "columns" in data and "rows" in data:
                    cols = data["columns"]
                    return [dict(zip(cols, row)) for row in data["rows"]]
                if isinstance(data, list):
                    return data
                return [data] if data else []

            except (requests.ConnectionError, requests.Timeout) as exc:
                last_err = exc
                if attempt < retries:
                    print(f"  Wrapper not ready (attempt {attempt}/{retries}), retrying...")
                    time.sleep(delay)
            except requests.HTTPError:
                raise

        pytest.fail(f"Wrapper at {wrapper_url} unreachable after {retries} attempts: {last_err}")


class TestCleanup:
    """Step 8: Mapping deletion after instance is gone."""

    def test_mapping_deleted(self, mapping_id: int, instance_and_snapshot: dict):
        """
        Mapping can be deleted after instance cleanup.

        The mapping_id fixture handles the actual deletion in its finalizer.
        Here we verify the mapping still exists at this point (the fixture
        teardown runs after all tests).
        """
        r = api_get(f"/api/mappings/{mapping_id}")
        # Mapping should still exist before fixture teardown
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Standalone runner (outside pytest)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
