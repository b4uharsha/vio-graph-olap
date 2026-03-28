# Flow

Complete end-to-end journey — from analyst intent to a running graph with query results.

---

## Full Flow Diagram

``` mermaid
flowchart TD
    A([👤 Analyst]) --> B[POST /api/mappings\nDefine nodes + edges from SQL]
    B --> C[(PostgreSQL\nMapping stored)]
    C --> D[POST /api/instances\nttl: PT4H]
    D --> E[Snapshot created\nExport jobs queued]
    E --> F[Export Worker\nStarburst UNLOAD]
    F --> G[(GCS\nParquet files)]
    G --> H{Reconciliation\nloop ~30s}
    H --> I[K8s spawns\nWrapper Pod]
    I --> J[Pod downloads Parquet\nLoads graph in memory\n~200k rows/sec]
    J --> K([✅ Status: running])
    K --> L[POST /instances/id/query\nCypher query]
    L --> M([⚡ Result in ms\nFully in-memory])
    K --> N{TTL expired\nor idle?}
    N -->|Yes| O[Pod deleted\nStatus: stopped]
    O --> P[(Parquet stays in GCS\nRe-create anytime)]

    style A fill:#00695c,color:#fff,stroke:none
    style K fill:#00695c,color:#fff,stroke:none
    style M fill:#00695c,color:#fff,stroke:none
    style O fill:#b71c1c,color:#fff,stroke:none
    style P fill:#1a237e,color:#fff,stroke:none
    style G fill:#0277bd,color:#fff,stroke:none
    style C fill:#4a148c,color:#fff,stroke:none
```

---

## Phase by Phase

=== ":material-map: Phase 1 — Define the Graph Shape"

    **One-time setup · ~5 minutes**

    The analyst creates a **Mapping** — a reusable blueprint that says which warehouse tables become graph nodes and which relationships become edges. It is saved in PostgreSQL and can be reused for many instances.

    ```bash
    POST /api/mappings
    {
      "name": "Customer Network",
      "node_definitions": [
        { "label": "Customer",
          "sql": "SELECT custkey, name, acctbal FROM tpch.sf1.customer",
          "primary_key": {"name": "custkey", "type": "INT64"} },
        { "label": "Nation",
          "sql": "SELECT nationkey, name FROM tpch.sf1.nation",
          "primary_key": {"name": "nationkey", "type": "INT64"} }
      ],
      "edge_definitions": [
        { "type": "BELONGS_TO", "from_node": "Customer", "to_node": "Nation",
          "sql": "SELECT custkey, nationkey FROM tpch.sf1.customer",
          "from_key": "custkey", "to_key": "nationkey" }
      ]
    }
    # ← Returns: mapping_id
    ```

    !!! tip
        One Mapping can power many instances — for different analysts, time periods, or engine types.

=== ":material-play-circle: Phase 2 — Create an Instance"

    **Triggers the export pipeline · Status: `waiting_for_snapshot`**

    The analyst creates a **Graph Instance** from the mapping. This is the moment data starts moving.

    ```bash
    POST /api/instances
    {
      "mapping_id": 42,
      "wrapper_type": "falkordb",   # or "ryugraph"
      "name": "My Q1 Analysis",
      "ttl": "PT4H"                 # pod lives for 4 hours
    }
    # ← Returns: instance_id, snapshot_id
    # ← Status:  waiting_for_snapshot
    ```

    Internally the control plane:

    1. Creates a **Snapshot** record (point-in-time)
    2. Creates one **Export Job** per node/edge definition
    3. The Export Worker connects to Starburst, runs `UNLOAD` queries
    4. Parquet files land in `gs://bucket/snapshot-{id}/nodes/...` and `.../edges/...`
    5. All jobs done → snapshot status set to **`ready`**

=== ":material-server: Phase 3 — Pod Spawned & Data Loaded"

    **Automatic · ~30 sec – 5 min depending on data size**

    The control plane's **reconciliation loop** runs every ~30 seconds. When it sees a `ready` snapshot with no wrapper pod, it acts:

    1. Calls the Kubernetes API → creates a **Pod + Service**
    2. The wrapper pod boots and:
        - Fetches the Mapping from the control plane
        - Creates the graph schema in FalkorDB or KuzuDB
        - Downloads Parquet files from GCS
        - Loads **nodes first** via `UNWIND` batches of 5,000 rows
        - Loads **edges after**, resolving foreign keys
        - Speed: **~200,000 rows/second**
    3. Reports `running` to the control plane

    ```
    waiting_for_snapshot  →  starting  →  running ✅
    ```

=== ":material-lightning-bolt: Phase 4 — Query"

    **The payoff · Sub-millisecond traversal · Fully in-memory**

    Queries go directly to the wrapper pod (via the SDK inside Jupyter, or `kubectl port-forward`):

    ```python
    # Inside Jupyter Labs
    conn = client.instances.connect(instance_id)
    rows = conn.query(
        "MATCH (c:Customer)-[:BELONGS_TO]->(n:Nation) RETURN n.name, count(c) ORDER BY count(c) DESC"
    )
    print(rows.df())
    ```

    Response from the wrapper pod:

    ```json
    {
      "columns": ["n.name", "count(c)"],
      "rows": [
        ["UNITED KINGDOM", 1823],
        ["GERMANY",        1654],
        ["FRANCE",         1601]
      ],
      "row_count": 3,
      "execution_time_ms": 3
    }
    ```

    No warehouse touched. Traversal queries that take minutes in SQL return in **milliseconds**.

    More examples:

    ```cypher
    -- Top spenders
    MATCH (c:Customer)-[:PLACED]->(o:SalesOrder)
    RETURN c.name, sum(o.totalprice) AS spend ORDER BY spend DESC LIMIT 10

    -- Shared-segment neighbours
    MATCH (c1:Customer)-[:BELONGS_TO]->(n:Nation)<-[:BELONGS_TO]-(c2:Customer)
    WHERE c1.mktsegment = c2.mktsegment AND id(c1) <> id(c2)
    RETURN n.name, c1.name, c2.name LIMIT 20

    -- PageRank (Ryugraph / KuzuDB only)
    CALL algo.pageRank({nodeLabel: "Customer", relationshipType: "BELONGS_TO"})
    YIELD nodeId, score ORDER BY score DESC LIMIT 10
    ```

=== ":material-timer-off: Phase 5 — Auto-Expiry"

    **Zero manual cleanup · Parquet always preserved**

    Every instance has a **TTL** set at creation time. When the TTL expires — or the pod is idle — the control plane:

    1. Deletes the Kubernetes Pod and Service
    2. Sets instance status to `stopped`
    3. Parquet files **stay in GCS** — re-create the instance instantly from the same snapshot

    | TTL format | Duration |
    | --- | --- |
    | `PT1H` | 1 hour |
    | `PT4H` | 4 hours (typical) |
    | `PT24H` | 24 hours |
    | `P7D` | 7 days |

    !!! warning "In-memory only"
        The graph lives entirely in the pod's memory. Pod deleted = graph gone.
        The **source Parquet in GCS is always preserved** — re-create the instance at any time with one API call.
