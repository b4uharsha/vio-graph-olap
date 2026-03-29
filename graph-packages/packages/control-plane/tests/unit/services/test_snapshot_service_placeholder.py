"""Tests for snapshot service placeholder SQL skip logic.

When all node/edge SQL references "placeholder", the export step is skipped
and the snapshot is immediately marked READY (data is pre-uploaded to GCS).
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, UTC

from control_plane.models import (
    Mapping,
    MappingVersion,
    NodeDefinition,
    EdgeDefinition,
    PrimaryKeyDefinition,
    PropertyDefinition,
    Snapshot,
    SnapshotStatus,
    User,
)
from control_plane.models.requests import CreateSnapshotRequest
from control_plane.services.snapshot_service import SnapshotService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_node(label: str, sql: str) -> NodeDefinition:
    """Create a node definition with the given label and SQL."""
    return NodeDefinition(
        label=label,
        sql=sql,
        primary_key=PrimaryKeyDefinition(name=f"{label.lower()}_id", type="INT64"),
        properties=[PropertyDefinition(name="name", type="STRING")],
    )


def _make_edge(edge_type: str, sql: str) -> EdgeDefinition:
    """Create an edge definition with the given type and SQL."""
    return EdgeDefinition(
        type=edge_type,
        from_node="A",
        to_node="B",
        sql=sql,
        from_key="a_id",
        to_key="b_id",
        properties=[],
    )


def _make_mapping(mapping_id: int = 1) -> Mapping:
    """Create a minimal mapping for mocking get_by_id."""
    now = datetime.now(UTC)
    return Mapping(
        id=mapping_id,
        owner_username="test.user",
        name="Test Mapping",
        description=None,
        current_version=1,
        created_at=now,
        updated_at=now,
    )


def _make_mapping_version(
    mapping_id: int = 1,
    nodes: list[NodeDefinition] | None = None,
    edges: list[EdgeDefinition] | None = None,
) -> MappingVersion:
    """Create a mapping version with the given node/edge definitions."""
    return MappingVersion(
        mapping_id=mapping_id,
        version=1,
        node_definitions=nodes or [],
        edge_definitions=edges or [],
        change_description=None,
        created_at=datetime.now(UTC),
        created_by="test.user",
    )


def _make_snapshot(snapshot_id: int = 1, status: SnapshotStatus = SnapshotStatus.PENDING) -> Snapshot:
    """Create a snapshot domain object for mock return values."""
    now = datetime.now(UTC)
    return Snapshot(
        id=snapshot_id,
        mapping_id=1,
        mapping_version=1,
        owner_username="test.user",
        name="Test Snapshot",
        description=None,
        gcs_path=f"gs://test-bucket/test.user/1/v1/{snapshot_id}/",
        status=status,
        size_bytes=None,
        node_counts=None,
        edge_counts=None,
        progress=None,
        error_message=None,
        created_at=now,
        updated_at=now,
        ttl=None,
        inactivity_timeout=None,
        last_used_at=None,
    )


def _make_user() -> User:
    """Create a test user."""
    return User(
        username="test.user",
        email="test.user@example.com",
        display_name="Test User",
        is_active=True,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def snapshot_service():
    """Build a SnapshotService wired to AsyncMock repositories."""
    svc = SnapshotService(
        snapshot_repo=AsyncMock(),
        mapping_repo=AsyncMock(),
        export_job_repo=AsyncMock(),
        config_repo=AsyncMock(),
        favorites_repo=AsyncMock(),
        gcs_bucket="test-bucket",
    )
    return svc


def _wire_repos(
    service: SnapshotService,
    nodes: list[NodeDefinition] | None = None,
    edges: list[EdgeDefinition] | None = None,
):
    """Configure the mock repositories with a standard mapping + version.

    Returns the pending snapshot that create() will return.
    """
    mapping = _make_mapping()
    version = _make_mapping_version(nodes=nodes, edges=edges)
    pending_snapshot = _make_snapshot(snapshot_id=42, status=SnapshotStatus.PENDING)
    ready_snapshot = _make_snapshot(snapshot_id=42, status=SnapshotStatus.READY)

    service._mapping_repo.get_by_id = AsyncMock(return_value=mapping)
    service._mapping_repo.get_version = AsyncMock(return_value=version)
    service._snapshot_repo.create = AsyncMock(return_value=pending_snapshot)
    service._snapshot_repo.update_gcs_path = AsyncMock(return_value=pending_snapshot)
    service._snapshot_repo.update_status = AsyncMock(return_value=ready_snapshot)
    service._config_repo.get_lifecycle_config = AsyncMock(
        return_value={"default_ttl": "P7D", "default_inactivity": "P3D"},
    )

    return pending_snapshot, ready_snapshot


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPlaceholderSnapshotSkip:
    """Tests for skipping export when SQL references 'placeholder'."""

    @pytest.mark.asyncio
    async def test_placeholder_sql_skips_export_and_marks_ready(self, snapshot_service):
        """When all SQL contains 'placeholder', skip export jobs and mark READY."""
        nodes = [
            _make_node("Customer", "placeholder"),
            _make_node("Product", "PLACEHOLDER -- pre-uploaded"),
        ]
        edges = [
            _make_edge("PURCHASED", "Placeholder data in GCS"),
        ]
        pending, ready = _wire_repos(snapshot_service, nodes=nodes, edges=edges)

        request = CreateSnapshotRequest(
            mapping_id=1,
            name="Placeholder Snapshot",
        )
        user = _make_user()
        result = await snapshot_service.create_snapshot(user, request)

        # Export jobs must NOT be created
        snapshot_service._export_job_repo.create_batch.assert_not_called()

        # Snapshot must be moved to READY
        snapshot_service._snapshot_repo.update_status.assert_called_once_with(
            snapshot_id=pending.id,
            status=SnapshotStatus.READY,
        )

        # Returned snapshot should be the ready one
        assert result.status == SnapshotStatus.READY

    @pytest.mark.asyncio
    async def test_real_sql_creates_export_jobs(self, snapshot_service):
        """When SQL has real queries, export jobs should be created."""
        nodes = [
            _make_node("Customer", "SELECT id, name FROM customers"),
        ]
        edges = [
            _make_edge("PURCHASED", "SELECT a_id, b_id FROM purchases"),
        ]
        pending, _ = _wire_repos(snapshot_service, nodes=nodes, edges=edges)

        request = CreateSnapshotRequest(
            mapping_id=1,
            name="Real Snapshot",
        )
        user = _make_user()
        result = await snapshot_service.create_snapshot(user, request)

        # Export jobs MUST be created
        snapshot_service._export_job_repo.create_batch.assert_called_once()
        call_args = snapshot_service._export_job_repo.create_batch.call_args
        assert call_args[0][0] == pending.id  # snapshot_id
        jobs = call_args[0][1]
        assert len(jobs) == 2  # 1 node + 1 edge

        # Snapshot should NOT be force-marked READY (stays pending for export)
        snapshot_service._snapshot_repo.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_mixed_sql_creates_export_jobs(self, snapshot_service):
        """When some SQL has placeholder and some doesn't, still create export jobs."""
        nodes = [
            _make_node("Customer", "placeholder"),
            _make_node("Product", "SELECT id, name FROM products"),
        ]
        edges = []
        pending, _ = _wire_repos(snapshot_service, nodes=nodes, edges=edges)

        request = CreateSnapshotRequest(
            mapping_id=1,
            name="Mixed Snapshot",
        )
        user = _make_user()
        result = await snapshot_service.create_snapshot(user, request)

        # Not all SQL is placeholder, so export jobs must be created
        snapshot_service._export_job_repo.create_batch.assert_called_once()
        jobs = snapshot_service._export_job_repo.create_batch.call_args[0][1]
        assert len(jobs) == 2  # both nodes get jobs

        # Snapshot should NOT be force-marked READY
        snapshot_service._snapshot_repo.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_mapping_no_jobs(self, snapshot_service):
        """When mapping has no nodes/edges, no export jobs and no ready transition."""
        _wire_repos(snapshot_service, nodes=[], edges=[])

        request = CreateSnapshotRequest(
            mapping_id=1,
            name="Empty Snapshot",
        )
        user = _make_user()
        result = await snapshot_service.create_snapshot(user, request)

        # No jobs to create, no status change
        snapshot_service._export_job_repo.create_batch.assert_not_called()
        snapshot_service._snapshot_repo.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_placeholder_case_insensitive(self, snapshot_service):
        """Placeholder detection should be case-insensitive."""
        nodes = [
            _make_node("Customer", "PLACEHOLDER"),
            _make_node("Product", "PlAcEhOlDeR"),
        ]
        pending, ready = _wire_repos(snapshot_service, nodes=nodes, edges=[])

        request = CreateSnapshotRequest(
            mapping_id=1,
            name="Case Test",
        )
        user = _make_user()
        result = await snapshot_service.create_snapshot(user, request)

        # Should still skip export
        snapshot_service._export_job_repo.create_batch.assert_not_called()
        snapshot_service._snapshot_repo.update_status.assert_called_once_with(
            snapshot_id=pending.id,
            status=SnapshotStatus.READY,
        )
        assert result.status == SnapshotStatus.READY

    @pytest.mark.asyncio
    async def test_placeholder_embedded_in_longer_sql(self, snapshot_service):
        """SQL that contains 'placeholder' as a substring should still trigger skip."""
        nodes = [
            _make_node("Customer", "SELECT * FROM placeholder_table WHERE 1=1"),
        ]
        pending, ready = _wire_repos(snapshot_service, nodes=nodes, edges=[])

        request = CreateSnapshotRequest(
            mapping_id=1,
            name="Substring Test",
        )
        user = _make_user()
        result = await snapshot_service.create_snapshot(user, request)

        # "placeholder" is present in the SQL, so export should be skipped
        snapshot_service._export_job_repo.create_batch.assert_not_called()
        snapshot_service._snapshot_repo.update_status.assert_called_once_with(
            snapshot_id=pending.id,
            status=SnapshotStatus.READY,
        )
