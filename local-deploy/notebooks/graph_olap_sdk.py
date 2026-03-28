"""
graph_olap_sdk.py — Lightweight SDK for Graph OLAP local deployment.

Mirrors the interface of the full graph_olap package used in production.
Drop this file alongside your notebook to get a clean, reusable client.

Quick start:
    from graph_olap_sdk import GraphOLAPClient

    client = GraphOLAPClient(username="demo@example.com")
    inst   = client.instances.create_and_wait(mapping_id, snapshot_id)
    conn   = client.instances.connect(inst)

    result = conn.query("MATCH (n:Movie) RETURN n.title AS title LIMIT 5")
    print(result.df())

    conn.algo.top_n(conn.algo.pagerank(result.nx()), n=10)
"""

from __future__ import annotations

import datetime
import time
from typing import Optional, Union

import networkx as nx
import pandas as pd
import requests

API_DEFAULT = "http://graph-olap-control-plane:8080"


# ---------------------------------------------------------------------------
# QueryResult
# ---------------------------------------------------------------------------

class QueryResult:
    """Wraps raw Cypher query results with multi-format output."""

    def __init__(self, raw: list[dict]):
        self._raw = raw

    def __repr__(self) -> str:
        return f"QueryResult({len(self._raw)} rows)"

    def __len__(self) -> int:
        return len(self._raw)

    def __iter__(self):
        return iter(self._raw)

    @property
    def data(self) -> list[dict]:
        """Raw list of row dicts."""
        return self._raw

    def df(self) -> pd.DataFrame:
        """Return results as a pandas DataFrame."""
        if not self._raw:
            return pd.DataFrame()
        return pd.DataFrame(self._raw)

    def nx(
        self,
        source: Optional[str] = None,
        target: Optional[str] = None,
        edge_attr: Optional[str] = None,
        directed: bool = True,
    ) -> nx.Graph:
        """
        Convert results to a NetworkX graph.

        If source/target columns are present (or auto-detected), each row
        becomes an edge. Otherwise rows are treated as nodes.

        Auto-detected column pairs (in order of preference):
          source/target, from/to, src/dst, node1/node2, a/b
        """
        G: nx.Graph = nx.DiGraph() if directed else nx.Graph()
        if not self._raw:
            return G

        cols = set(self._raw[0].keys())

        # Auto-detect source/target
        if source is None or target is None:
            for s, t in [
                ("source", "target"), ("from", "to"), ("src", "dst"),
                ("node1", "node2"), ("a", "b"),
            ]:
                if s in cols and t in cols:
                    source, target = s, t
                    break

        if source and target and source in cols and target in cols:
            for row in self._raw:
                s_val = row[source]
                t_val = row[target]
                attrs = {k: v for k, v in row.items() if k not in (source, target)}
                if edge_attr and edge_attr in attrs:
                    attrs["weight"] = attrs.pop(edge_attr)
                G.add_edge(s_val, t_val, **attrs)
        else:
            # Treat rows as nodes; first column is the node ID
            for row in self._raw:
                node_id = next(iter(row.values()))
                attrs = dict(list(row.items())[1:])
                G.add_node(node_id, **attrs)

        return G


# ---------------------------------------------------------------------------
# Algorithms
# ---------------------------------------------------------------------------

class Algorithms:
    """
    Graph algorithm helpers powered by NetworkX.

    Works on any NetworkX graph — typically built via QueryResult.nx()
    or assembled manually.

    Example:
        G      = conn.query("MATCH (a)-[r]->(b) RETURN a.name AS source, b.name AS target").nx()
        scores = conn.algo.pagerank(G)
        top10  = conn.algo.top_n(scores, n=10)
    """

    # --- Centrality --------------------------------------------------------

    @staticmethod
    def pagerank(G: nx.Graph, alpha: float = 0.85, **kwargs) -> dict:
        """PageRank centrality — higher score = more influential node."""
        return nx.pagerank(G, alpha=alpha, **kwargs)

    @staticmethod
    def betweenness_centrality(G: nx.Graph, normalized: bool = True, **kwargs) -> dict:
        """Betweenness centrality — nodes that act as bridges between others."""
        return nx.betweenness_centrality(G, normalized=normalized, **kwargs)

    @staticmethod
    def closeness_centrality(G: nx.Graph, **kwargs) -> dict:
        """Closeness centrality — how quickly a node can reach all others."""
        return nx.closeness_centrality(G, **kwargs)

    @staticmethod
    def degree_centrality(G: nx.Graph) -> dict:
        """Degree centrality — normalized connection count per node."""
        return nx.degree_centrality(G)

    @staticmethod
    def eigenvector_centrality(G: nx.Graph, max_iter: int = 1000, **kwargs) -> dict:
        """Eigenvector centrality — importance weighted by neighbor importance."""
        return nx.eigenvector_centrality(G, max_iter=max_iter, **kwargs)

    # --- Community detection -----------------------------------------------

    @staticmethod
    def community_detection(G: nx.Graph, resolution: float = 1.0) -> list[set]:
        """
        Louvain community detection.

        Returns a list of sets, where each set contains node IDs belonging
        to the same community. Tries louvain_communities (NetworkX >= 2.8),
        then python-louvain, then falls back to greedy modularity.
        """
        undirected = G.to_undirected() if G.is_directed() else G

        # NetworkX >= 2.8
        try:
            from networkx.algorithms.community import louvain_communities
            return [set(c) for c in louvain_communities(undirected, resolution=resolution)]
        except (ImportError, AttributeError):
            pass

        # python-louvain (community package)
        try:
            from community import best_partition  # type: ignore
            partition = best_partition(undirected, resolution=resolution)
            groups: dict[int, set] = {}
            for node, cid in partition.items():
                groups.setdefault(cid, set()).add(node)
            return list(groups.values())
        except ImportError:
            pass

        # Fallback
        from networkx.algorithms.community import greedy_modularity_communities
        return [set(c) for c in greedy_modularity_communities(undirected)]

    # --- Connectivity ------------------------------------------------------

    @staticmethod
    def connected_components(G: nx.Graph) -> list[set]:
        """
        Weakly connected components (directed) or connected components (undirected).
        Returns list of node sets sorted by size, largest first.
        """
        if G.is_directed():
            comps = list(nx.weakly_connected_components(G))
        else:
            comps = list(nx.connected_components(G))
        return sorted(comps, key=len, reverse=True)

    # --- Path finding ------------------------------------------------------

    @staticmethod
    def shortest_path(
        G: nx.Graph,
        source,
        target,
        weight: Optional[str] = None,
    ) -> Optional[list]:
        """
        Shortest path between two nodes.
        Returns the list of nodes on the path, or None if unreachable.
        """
        try:
            return nx.shortest_path(G, source=source, target=target, weight=weight)
        except nx.NetworkXNoPath:
            return None
        except nx.NodeNotFound as e:
            raise ValueError(str(e)) from e

    @staticmethod
    def all_shortest_paths(G: nx.Graph, source, target, weight: Optional[str] = None) -> list[list]:
        """All shortest paths between two nodes."""
        try:
            return list(nx.all_shortest_paths(G, source=source, target=target, weight=weight))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    # --- Structural --------------------------------------------------------

    @staticmethod
    def triangle_count(G: nx.Graph) -> dict:
        """Number of triangles each node participates in."""
        undirected = G.to_undirected() if G.is_directed() else G
        return nx.triangles(undirected)

    @staticmethod
    def clustering_coefficient(G: nx.Graph) -> dict:
        """Local clustering coefficient for each node (0 = no clustering, 1 = full clique)."""
        undirected = G.to_undirected() if G.is_directed() else G
        return nx.clustering(undirected)

    # --- Helpers -----------------------------------------------------------

    @staticmethod
    def top_n(scores: dict, n: int = 10, ascending: bool = False) -> list[tuple]:
        """Return top N nodes by score as (node, score) tuples."""
        return sorted(scores.items(), key=lambda x: x[1], reverse=not ascending)[:n]

    @staticmethod
    def write_scores(G: nx.Graph, scores: dict, attr_name: str) -> nx.Graph:
        """Write algorithm scores back as node attributes on the graph in-place."""
        nx.set_node_attributes(G, scores, attr_name)
        return G

    @staticmethod
    def scores_df(scores: dict, node_col: str = "node", score_col: str = "score") -> pd.DataFrame:
        """Convert a scores dict to a pandas DataFrame, sorted descending."""
        df = pd.DataFrame(list(scores.items()), columns=[node_col, score_col])
        return df.sort_values(score_col, ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

class Connection:
    """Active connection to a FalkorDB wrapper pod."""

    def __init__(self, client: "GraphOLAPClient", instance_id: str, wrapper_url: str):
        self._client = client
        self.instance_id = instance_id
        self.wrapper_url = wrapper_url.rstrip("/")
        self.algo = Algorithms()

    def __repr__(self) -> str:
        return f"Connection(instance={self.instance_id}, wrapper={self.wrapper_url})"

    def query(
        self,
        cypher: str,
        params: Optional[dict] = None,
        retries: int = 10,
        retry_delay: float = 3.0,
    ) -> QueryResult:
        """
        Execute a Cypher query against the wrapper pod.

        Retries on connection errors — the wrapper pod may still be
        initialising right after the instance reaches 'running' status.
        """
        payload: dict = {"query": cypher}
        if params:
            payload["params"] = params

        last_err: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            try:
                r = requests.post(
                    f"{self.wrapper_url}/query",
                    json=payload,
                    timeout=30,
                )
                r.raise_for_status()
                result = r.json()
                data = result.get("data") or result.get("results") or result

                # Wrapper returns {"columns": [...], "rows": [[...], ...], ...}
                if isinstance(data, dict) and "columns" in data and "rows" in data:
                    cols = data["columns"]
                    row_dicts = [dict(zip(cols, row)) for row in data["rows"]]
                    return QueryResult(row_dicts)

                if isinstance(data, list):
                    return QueryResult(data)
                return QueryResult([data] if data else [])

            except (requests.ConnectionError, requests.Timeout) as e:
                last_err = e
                if attempt < retries:
                    print(f"  Wrapper not ready (attempt {attempt}/{retries}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)

            except requests.HTTPError:
                raise

        raise RuntimeError(
            f"Wrapper at {self.wrapper_url} unreachable after {retries} attempts: {last_err}"
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

class InstanceResource:
    def __init__(self, client: "GraphOLAPClient"):
        self._c = client

    def list(self) -> list[dict]:
        """List all instances."""
        return self._c._get("/api/instances").get("data", [])

    def get(self, instance_id: str) -> dict:
        """Get a single instance by ID."""
        return self._c._get(f"/api/instances/{instance_id}").get("data", {})

    def create(
        self,
        mapping_id: str,
        snapshot_id: str,
        ttl: str = "PT4H",
        engine: str = "falkordb",
    ) -> dict:
        """Create a new instance (returns immediately, does not wait)."""
        payload = {
            "mapping_id": mapping_id,
            "snapshot_id": snapshot_id,
            "ttl": ttl,
            "engine": engine,
        }
        return self._c._post("/api/instances", json=payload).get("data", {})

    def create_and_wait(
        self,
        mapping_id: str,
        snapshot_id: str,
        ttl: str = "PT4H",
        engine: str = "falkordb",
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> dict:
        """
        Create an instance and block until it reaches 'running' status.

        Returns the instance dict (includes pod_name, wrapper_url, etc.).
        Raises RuntimeError if the instance fails, TimeoutError if it times out.
        """
        inst = self.create(mapping_id, snapshot_id, ttl, engine)
        inst_id = inst["id"]
        print(f"Instance {inst_id} created — waiting for it to start...")

        deadline = time.time() + timeout
        while time.time() < deadline:
            inst = self.get(inst_id)
            status = inst.get("status", "unknown")
            if status == "running":
                wrapper = inst.get("wrapper_url") or f"http://{inst.get('pod_name')}:8000"
                print(f"Instance {inst_id} running — wrapper: {wrapper}")
                return inst
            if status in ("failed", "error", "terminated"):
                raise RuntimeError(f"Instance {inst_id} ended with status: {status}")
            time.sleep(poll_interval)

        raise TimeoutError(f"Instance {inst_id} not ready after {timeout}s")

    def connect(self, instance: Union[str, dict]) -> Connection:
        """
        Get a Connection to an instance.

        Pass either the instance ID (str) or the instance dict returned by
        create_and_wait / get.
        """
        if isinstance(instance, dict):
            inst_id = instance["id"]
            pod_name = instance.get("pod_name") or ""
        else:
            inst_id = instance
            inst_data = self.get(inst_id)
            pod_name = inst_data.get("pod_name") or ""

        wrapper_url = f"http://{pod_name}:8000"
        return Connection(self._c, inst_id, wrapper_url)

    def terminate(self, instance_id: str) -> None:
        """Terminate an instance. Silently ignores 404 (already gone)."""
        try:
            self._c._delete(f"/api/instances/{instance_id}")
            print(f"Instance {instance_id} terminated.")
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Instance {instance_id} already gone (404).")
            else:
                raise

    def bulk_delete(
        self,
        older_than_hours: Optional[float] = None,
        status_filter: Optional[Union[str, set]] = None,
        name_prefix: Optional[str] = None,
        owner: Optional[str] = None,
        dry_run: bool = False,
    ) -> list[dict]:
        """
        Bulk delete instances matching optional filters.

        Parameters
        ----------
        older_than_hours : float, optional
            Only delete instances older than this many hours.
        status_filter : str or set, optional
            Only delete instances with this status (or set of statuses).
            Defaults to {"running", "starting", "waiting_for_snapshot"}.
        name_prefix : str, optional
            Only delete instances whose name starts with this prefix.
        owner : str, optional
            Only delete instances created by this user.
        dry_run : bool
            Print what would be deleted without actually deleting anything.

        Returns
        -------
        list[dict]
            The instances that were deleted (or would be deleted in dry-run).
        """
        active_statuses = {"running", "starting", "waiting_for_snapshot"}

        if status_filter is None:
            allowed = active_statuses
        elif isinstance(status_filter, str):
            allowed = {status_filter}
        else:
            allowed = set(status_filter)

        now = datetime.datetime.now(datetime.timezone.utc)
        targets = []

        for inst in self.list():
            if inst.get("status") not in allowed:
                continue
            if owner and inst.get("created_by") != owner:
                continue
            if name_prefix and not inst.get("name", "").startswith(name_prefix):
                continue
            if older_than_hours is not None:
                created_str = inst.get("created_at", "")
                if created_str:
                    created_at = datetime.datetime.fromisoformat(
                        created_str.replace("Z", "+00:00")
                    )
                    age_hours = (now - created_at).total_seconds() / 3600
                    if age_hours < older_than_hours:
                        continue
            targets.append(inst)

        if not targets:
            print("No instances match the filter criteria.")
            return []

        tag = "[DRY RUN] " if dry_run else ""
        print(f"{tag}Found {len(targets)} instance(s) to delete:")
        for inst in targets:
            age_str = ""
            if inst.get("created_at"):
                created_at = datetime.datetime.fromisoformat(
                    inst["created_at"].replace("Z", "+00:00")
                )
                age_h = (now - created_at).total_seconds() / 3600
                age_str = f"  age={age_h:.1f}h"
            print(f"  id={inst['id']}  status={inst['status']}{age_str}")

        if dry_run:
            print("[DRY RUN] No instances deleted.")
            return targets

        deleted = []
        for inst in targets:
            try:
                self._c._delete(f"/api/instances/{inst['id']}")
                print(f"  Deleted {inst['id']}")
                deleted.append(inst)
            except Exception as e:
                print(f"  Failed to delete {inst['id']}: {e}")

        return deleted


class AdminResource:
    """Privileged operations (bulk delete, config)."""

    def __init__(self, client: "GraphOLAPClient"):
        self._c = client

    def bulk_delete(self, **kwargs) -> list[dict]:
        """Alias for instances.bulk_delete — same parameters."""
        return self._c.instances.bulk_delete(**kwargs)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class GraphOLAPClient:
    """
    Top-level client for the Graph OLAP local platform.

    Parameters
    ----------
    api_url : str
        Control-plane base URL (default: http://graph-olap-control-plane:8080)
    username : str
        Username passed in X-Username header (dev-mode auth).
    role : str
        Role passed in X-User-Role header (default: "analyst").

    Example
    -------
        client = GraphOLAPClient(username="alice@example.com")
        instances = client.instances.list()
    """

    def __init__(
        self,
        api_url: str = API_DEFAULT,
        username: str = "demo@example.com",
        role: str = "analyst",
    ):
        self.api = api_url.rstrip("/")
        self.headers = {"X-Username": username, "X-User-Role": role}
        self.instances = InstanceResource(self)
        self.admin = AdminResource(self)

    def __repr__(self) -> str:
        return f"GraphOLAPClient(api={self.api}, user={self.headers['X-Username']})"

    # -- Internal HTTP helpers (thin wrappers, not for external use) --------

    def _get(self, path: str, **kwargs) -> dict:
        r = requests.get(f"{self.api}{path}", headers=self.headers, **kwargs)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, **kwargs) -> dict:
        r = requests.post(f"{self.api}{path}", headers=self.headers, **kwargs)
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str, **kwargs) -> requests.Response:
        r = requests.delete(f"{self.api}{path}", headers=self.headers, **kwargs)
        r.raise_for_status()
        return r

    # -- Public API ---------------------------------------------------------

    def health(self) -> dict:
        """Check control-plane health."""
        return self._get("/health")
