# Python SDK

`graph_olap_sdk` is the local development SDK — a lightweight Python module pre-loaded in Jupyter Labs at `/home/jovyan/work/graph_olap_sdk.py`. It wraps the REST API with a Pythonic interface and adds helpers for graph algorithms and visualisation.

!!! note "Local SDK vs production package"
    In production, the equivalent package is `graph_olap` (installed via pip). The local SDK mirrors its interface so notebooks are easy to port. In Jupyter, always import from `graph_olap_sdk`.

---

## Quick Start

```python
import sys
sys.path.insert(0, "/home/jovyan/work")
from graph_olap_sdk import GraphOLAPClient

client = GraphOLAPClient(
    api_url="http://graph-olap-control-plane:8080",  # in-cluster URL (Jupyter)
    username="analyst@example.com",
    role="analyst"
)

print(client.health())  # → {"status": "healthy"}
```

!!! tip "From outside the cluster"
    Use `http://localhost:30081` as `api_url` when running from your laptop instead of Jupyter.

---

## Full End-to-End Pattern

Every notebook follows this pattern:

```python
from graph_olap_sdk import GraphOLAPClient

client = GraphOLAPClient(api_url="http://graph-olap-control-plane:8080",
                         username="demo@example.com", role="analyst")

# 1. Create a mapping (schema definition)
mapping_id = "..."   # returned from POST /api/mappings

# 2. Create a snapshot
snapshot_id = "..."  # returned from POST /api/snapshots

# 3. Upload Parquet files to fake-gcs-local, mark snapshot ready in PostgreSQL

# 4. Create instance and wait for it to be running
inst = client.instances.create_and_wait(mapping_id, snapshot_id, ttl="PT4H")

# 5. Connect and query
conn = client.instances.connect(inst)
df   = conn.query("MATCH (n:Movie) RETURN n.title, n.year ORDER BY n.year DESC").df()

# 6. Cleanup
client.instances.terminate(inst["id"])
```

---

## GraphOLAPClient

```python
GraphOLAPClient(api_url, username, role)
```

| Attribute | Type | Description |
| --- | --- | --- |
| `client.instances` | `InstanceResource` | Create, connect, terminate, list, bulk-delete instances |
| `client.health()` | `dict` | Returns `{"status": "healthy"}` |

---

## InstanceResource

Access via `client.instances`.

### create_and_wait

```python
inst = client.instances.create_and_wait(
    mapping_id,
    snapshot_id,
    name="My Analysis",   # optional
    ttl="PT4H",           # ISO 8601 duration — default PT4H
    timeout=300           # seconds to wait — default 300
)
```

Polls until the instance is `running` or raises `TimeoutError`. Returns the instance dict.

### connect

```python
conn = client.instances.connect(inst)
```

Returns a `Connection` object ready for Cypher queries.

### terminate

```python
client.instances.terminate(instance_id)
```

Deletes the instance and its wrapper pod.

### list

```python
instances = client.instances.list()
for i in instances:
    print(i["id"], i["name"], i["status"])
```

### bulk_delete

Delete multiple instances at once with optional filters:

```python
# Delete all instances older than 2 hours (preview first)
client.instances.bulk_delete(older_than_hours=2, dry_run=True)

# Actually delete
client.instances.bulk_delete(older_than_hours=2)

# Delete only instances owned by a specific user
client.instances.bulk_delete(owner="alice@example.com")

# Delete by name prefix
client.instances.bulk_delete(name_prefix="test-")

# Combined filters
client.instances.bulk_delete(older_than_hours=4, status_filter=["running", "starting"])
```

| Parameter | Type | Description |
| --- | --- | --- |
| `older_than_hours` | `float` | Only delete instances older than N hours |
| `owner` | `str` | Only delete instances owned by this username |
| `name_prefix` | `str` | Only delete instances whose name starts with this prefix |
| `status_filter` | `list[str]` | Only delete instances with these statuses (default: `running`, `starting`, `waiting_for_snapshot`) |
| `dry_run` | `bool` | Print what would be deleted without actually deleting (default: `False`) |

---

## Connection

Returned by `client.instances.connect(inst)`.

### query

```python
result = conn.query("MATCH (n:Movie) RETURN n.title, n.year LIMIT 10")
```

Returns a `QueryResult`.

---

## QueryResult

| Method / Property | Description |
| --- | --- |
| `.data` | Raw list of result rows (list of dicts) |
| `.df()` | Pandas DataFrame |
| `.nx()` | NetworkX graph — for results with `src`, `src_label`, `dst`, `dst_label` columns |

=== "Raw data"

    ```python
    result = conn.query("MATCH (n:Actor) RETURN n.name AS name, n.born AS born")
    print(result.data)
    # [{"name": "Tom Hanks", "born": 1956}, ...]
    ```

=== "DataFrame"

    ```python
    df = conn.query("MATCH (n:Movie) RETURN n.title, n.year ORDER BY n.year").df()
    df.head(10)
    ```

=== "NetworkX graph"

    ```python
    G = conn.query("""
        MATCH (a:Actor)-[:ACTED_IN]->(m:Movie)
        RETURN a.name AS src, 'Actor' AS src_label,
               m.title AS dst, 'Movie' AS dst_label
    """).nx()

    print(G.number_of_nodes(), G.number_of_edges())
    ```

---

## Algorithms

`Algorithms` is available on the connection as `conn.algo`, or instantiated directly:

```python
from graph_olap_sdk import Algorithms
algo = Algorithms()

# Or via the connection:
algo = conn.algo
```

All algorithms operate on a **NetworkX graph** (`nx.Graph` or `nx.DiGraph`) — fetch your graph data via Cypher first, then run algorithms locally.

### PageRank

```python
scores = algo.pagerank(G, alpha=0.85)    # → {node: score}
top10  = algo.top_n(scores, n=10)        # → [(node, score), ...]
```

### Betweenness Centrality

```python
scores = algo.betweenness_centrality(G)  # → {node: score}
top10  = algo.top_n(scores, n=10)
```

### Community Detection (Louvain)

```python
communities = algo.community_detection(G)  # → list of sets
for i, comm in enumerate(communities):
    print(f"Community {i+1}: {sorted(comm)}")
```

### Shortest Path

```python
path = algo.shortest_path(G, source="Tom Hanks", target="Meryl Streep")
# → ["Tom Hanks", "Film A", "Meryl Streep"]  or  None if no path
```

### Connected Components

```python
components = algo.connected_components(G)  # → list of sets
```

### Clustering Coefficient

```python
scores = algo.clustering_coefficient(G)  # → {node: score}
avg    = sum(scores.values()) / len(scores)
```

### Combined Scores DataFrame

```python
import pandas as pd
from graph_olap_sdk import Algorithms

algo   = Algorithms()
pr     = algo.pagerank(G)
bc     = algo.betweenness_centrality(G)
cc     = algo.clustering_coefficient(G)

df = pd.DataFrame({
    "Node":        list(G.nodes()),
    "Degree":      [G.degree(n) for n in G.nodes()],
    "PageRank":    [round(pr.get(n, 0), 4) for n in G.nodes()],
    "Betweenness": [round(bc.get(n, 0), 4) for n in G.nodes()],
    "Clustering":  [round(cc.get(n, 0), 4) for n in G.nodes()],
}).sort_values("PageRank", ascending=False)

display(df)
```

---

## AdminResource

Access admin operations via the REST API directly (no SDK wrapper needed for admin tasks):

```python
import requests

H = {"X-Username": "admin@example.com", "X-User-Role": "admin"}
API = "http://graph-olap-control-plane:8080"

# List all instances (admin sees all users)
instances = requests.get(f"{API}/api/instances", headers=H).json()["data"]

# Delete a specific instance
requests.delete(f"{API}/api/instances/{instance_id}", headers=H)
```

---

## SDK Reference

| Class / Method | Description |
| --- | --- |
| `GraphOLAPClient(api_url, username, role)` | Create a client |
| `client.health()` | Health check |
| `client.instances.create_and_wait(mapping_id, snapshot_id, ...)` | Create instance + wait until running |
| `client.instances.connect(inst)` | Get a `Connection` for querying |
| `client.instances.terminate(instance_id)` | Delete instance |
| `client.instances.list()` | List all instances visible to this user |
| `client.instances.bulk_delete(...)` | Delete multiple instances with filters |
| `conn.query(cypher)` | Run Cypher, returns `QueryResult` |
| `result.data` | Raw list of row dicts |
| `result.df()` | Pandas DataFrame |
| `result.nx()` | NetworkX graph |
| `conn.algo` | `Algorithms` instance |
| `Algorithms().pagerank(G)` | PageRank scores |
| `Algorithms().betweenness_centrality(G)` | Betweenness centrality scores |
| `Algorithms().community_detection(G)` | Louvain community detection |
| `Algorithms().shortest_path(G, src, dst)` | Shortest path between two nodes |
| `Algorithms().connected_components(G)` | List of connected component node sets |
| `Algorithms().clustering_coefficient(G)` | Local clustering coefficient per node |
| `Algorithms().top_n(scores, n)` | Top N nodes by score |
