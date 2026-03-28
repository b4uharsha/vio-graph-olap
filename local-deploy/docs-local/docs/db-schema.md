# DB & Schema

Two types of schema in the platform — the **PostgreSQL control plane database** and the **graph schema** inside each wrapper pod.

---

## PostgreSQL — Control Plane Database

The control plane stores all state in PostgreSQL. Connect directly for debugging:

```bash
# From your terminal
kubectl exec -n graph-olap-local deploy/postgres -- \
  psql -U control_plane -d control_plane
```

Or from inside Jupyter:

```python
import psycopg2
conn = psycopg2.connect(
    host="postgres", port=5432,
    dbname="control_plane",
    user="control_plane", password="control_plane"
)
```

---

### Table: `mappings`

Stores the graph blueprint — which warehouse tables become nodes and edges.

| Column | Type | Description |
| --- | --- | --- |
| `id` | serial | Primary key |
| `name` | text | Human-readable name |
| `description` | text | Optional description |
| `node_definitions` | jsonb | Array of node definition objects |
| `edge_definitions` | jsonb | Array of edge definition objects |
| `created_by` | text | Username who created it |
| `created_at` | timestamptz | Creation timestamp |
| `updated_at` | timestamptz | Last update timestamp |

```sql
-- View all mappings
SELECT id, name, created_by, created_at FROM mappings ORDER BY id;

-- Inspect a mapping's node definitions
SELECT id, name, jsonb_pretty(node_definitions) FROM mappings WHERE id = 1;
```

---

### Table: `snapshots`

A snapshot is a point-in-time export of a mapping's data. One snapshot per instance creation.

| Column | Type | Description |
| --- | --- | --- |
| `id` | serial | Primary key |
| `mapping_id` | int | FK → mappings.id |
| `status` | text | `pending` · `exporting` · `ready` · `failed` |
| `gcs_path` | text | GCS prefix where Parquet files are stored |
| `created_at` | timestamptz | When snapshot was triggered |
| `completed_at` | timestamptz | When all exports finished |

**Status lifecycle:**

```
pending  →  exporting  →  ready
                       ↘  failed
```

```sql
-- Check snapshot status
SELECT id, mapping_id, status, created_at, completed_at
FROM snapshots ORDER BY id DESC LIMIT 10;

-- Manually mark a snapshot as ready (bypass export worker)
UPDATE snapshots SET status = 'ready' WHERE id = <snapshot_id>;
```

!!! warning "Manual `ready` update"
    Only do this if you've uploaded Parquet files to GCS yourself (see [Loading Data](data.md)).

---

### Table: `export_jobs`

One export job per node/edge definition per snapshot. The export worker polls this table.

| Column | Type | Description |
| --- | --- | --- |
| `id` | serial | Primary key |
| `snapshot_id` | int | FK → snapshots.id |
| `definition_type` | text | `node` or `edge` |
| `definition_label` | text | Node label or edge type name |
| `sql_query` | text | The UNLOAD query to run on Starburst |
| `starburst_catalog` | text | Catalog name (⚠ currently hardcoded to `bigquery`) |
| `status` | text | `pending` · `running` · `done` · `failed` |
| `gcs_output_path` | text | Where output Parquet files land |
| `error_message` | text | Set on failure |
| `created_at` | timestamptz | |
| `updated_at` | timestamptz | |

```sql
-- Check export job status for a snapshot
SELECT id, definition_type, definition_label, status, error_message
FROM export_jobs WHERE snapshot_id = <snapshot_id>;

-- Fix the starburst_catalog bug
UPDATE export_jobs
SET starburst_catalog = 'tpch'
WHERE snapshot_id = <snapshot_id> AND starburst_catalog = 'bigquery';

-- Retry failed jobs
UPDATE export_jobs SET status = 'pending', error_message = NULL
WHERE snapshot_id = <snapshot_id> AND status = 'failed';
```

---

### Table: `instances`

Running (or stopped) graph pods.

| Column | Type | Description |
| --- | --- | --- |
| `id` | serial | Primary key |
| `name` | text | Human-readable name |
| `mapping_id` | int | FK → mappings.id |
| `snapshot_id` | int | FK → snapshots.id |
| `wrapper_type` | text | `falkordb` or `ryugraph` |
| `status` | text | `waiting_for_snapshot` · `starting` · `running` · `stopped` |
| `k8s_pod_name` | text | The Kubernetes pod name (null if not yet spawned) |
| `k8s_service_name` | text | The Kubernetes service name |
| `ttl` | interval | Time-to-live (e.g. `04:00:00` for PT4H) |
| `created_by` | text | Username |
| `created_at` | timestamptz | |
| `expires_at` | timestamptz | `created_at + ttl` |
| `stopped_at` | timestamptz | When pod was deleted |

```sql
-- View all running instances
SELECT id, name, wrapper_type, status, expires_at
FROM instances WHERE status = 'running';

-- View instance status transitions
SELECT id, name, status, created_at, expires_at, stopped_at
FROM instances ORDER BY id DESC LIMIT 20;

-- Find instances about to expire (next 30 mins)
SELECT id, name, expires_at
FROM instances
WHERE status = 'running'
  AND expires_at < NOW() + INTERVAL '30 minutes';
```

---

### Table: `users`

User registry for access control.

| Column | Type | Description |
| --- | --- | --- |
| `id` | serial | Primary key |
| `username` | text | Email/username (must match `X-Username` header) |
| `role` | text | `analyst` · `admin` · `ops` |
| `created_at` | timestamptz | |

```sql
-- View all users
SELECT id, username, role, created_at FROM users ORDER BY created_at;

-- Add a user directly
INSERT INTO users (username, role) VALUES ('analyst@example.com', 'analyst');
```

---

### Entity Relationship Diagram

``` mermaid
erDiagram
    mappings {
        int id PK
        text name
        jsonb node_definitions
        jsonb edge_definitions
        text created_by
    }
    snapshots {
        int id PK
        int mapping_id FK
        text status
        text gcs_path
    }
    export_jobs {
        int id PK
        int snapshot_id FK
        text definition_label
        text starburst_catalog
        text status
    }
    instances {
        int id PK
        int mapping_id FK
        int snapshot_id FK
        text wrapper_type
        text status
        text k8s_pod_name
        timestamptz expires_at
    }
    users {
        int id PK
        text username
        text role
    }

    mappings ||--o{ snapshots : "exported as"
    snapshots ||--o{ export_jobs : "has jobs"
    snapshots ||--o{ instances : "powers"
    mappings ||--o{ instances : "defines shape of"
```

---

## Graph Schema — Inside the Wrapper Pod

The graph schema is derived from the **Mapping** at pod startup. There is no separate schema file — it is built dynamically.

### Node schema

Each node definition in the Mapping becomes a **node label** in the graph:

```
Mapping node_definition:              Graph node label:
  label: "Customer"          →        (:Customer)
  primary_key: custkey       →        node ID = custkey value
  properties: [name, acctbal] →       node properties: name, acctbal
```

### Edge schema

Each edge definition becomes a **relationship type**:

```
Mapping edge_definition:              Graph relationship:
  type: "BELONGS_TO"         →        -[:BELONGS_TO]->
  from_node: "Customer"      →        (:Customer)-...
  to_node: "Nation"          →        ...-(:Nation)
  from_key: custkey          →        resolved from Customer node
  to_key: nationkey          →        resolved from Nation node
```

### Inspect the schema at runtime

```bash
GET /api/instances/{instance_id}/schema
```

```json
{
  "data": {
    "nodes": [
      { "label": "Customer",   "count": 1500,  "properties": ["custkey","name","acctbal","mktsegment"] },
      { "label": "Nation",     "count": 25,    "properties": ["nationkey","name"] },
      { "label": "SalesOrder", "count": 15000, "properties": ["orderkey","totalprice","orderstatus"] }
    ],
    "relationships": [
      { "type": "BELONGS_TO", "from": "Customer",   "to": "Nation",     "count": 1500  },
      { "type": "PLACED",     "from": "Customer",   "to": "SalesOrder", "count": 15000 }
    ]
  }
}
```

Or via Cypher:

```cypher
-- Count all node labels
MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count

-- Count all relationship types
MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count

-- Sample 5 nodes of a label
MATCH (c:Customer) RETURN c LIMIT 5
```

### Property type mapping

| Mapping type | FalkorDB type | KuzuDB type |
| --- | --- | --- |
| `STRING` | String | STRING |
| `INT64` | Integer | INT64 |
| `DOUBLE` | Float | DOUBLE |
| `BOOLEAN` | Boolean | BOOL |
| `DATE` | String (ISO 8601) | DATE |
| `DATETIME` | String (ISO 8601) | TIMESTAMP |

!!! warning "Parquet columns must match exactly"
    The Parquet file must contain a column matching every `primary_key.name` and `properties[].name` declared in the Mapping. Extra columns are ignored. Missing columns cause the load to fail.
