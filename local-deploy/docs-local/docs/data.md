# Loading Data

There are two ways to get data into a graph instance:

| Method | When to use |
| --- | --- |
| **Via Starburst** | You have a Starburst Galaxy account and want to export from your warehouse |
| **Direct Parquet upload** | You don't have Starburst, or want to load your own data immediately |

---

## Method 1 — Connecting to Starburst Galaxy

Starburst Galaxy is the data source for the export pipeline. The export worker connects to your Starburst cluster, runs an `UNLOAD` query against your tables, and writes Parquet files to GCS.

### Step 1 — Get your credentials and cluster URL

In Starburst Galaxy, go to **Clusters → your cluster → Connection info → Drivers & Clients → Trino JDBC**.

You'll see a JDBC URL like:

```text
jdbc:trino://your-org-free-cluster.trino.galaxy.starburst.io:443?user=you@example.com/accountadmin
```

Your credentials are:

| Field | Where to find it | Example |
| --- | --- | --- |
| Cluster host | JDBC URL, between `://` and `?user=` | `your-org-cluster.trino.galaxy.starburst.io:443` |
| Username | `?user=` value from the JDBC URL | `you@example.com/accountadmin` |
| Password | Your Galaxy account password | — |

!!! tip "Free account users"
    On a free Starburst Galaxy account your username is `your-email@gmail.com/accountadmin`. No separate service account creation needed.

### Step 2 — Set credentials in `.env`

```bash
export STARBURST_USER=you@example.com/accountadmin
export STARBURST_PASSWORD=your-galaxy-password
```

Then re-source and redeploy the secret:

```bash
source .env
make deploy
```

### Step 3 — Set your cluster URL in `helm/values-local.yaml`

```yaml
starburst:
  url: "your-org-cluster.trino.galaxy.starburst.io:443"
  user: "you@example.com/accountadmin"
  catalog: "tpch"          # catalog name from Starburst Galaxy → Catalogs
  schema: "tiny"           # "tiny" = SF0.01 (1,500 customers — fastest). Use "sf1" for 150k customers.
```

!!! info "TPC-H schema sizes"
    | Schema | Customers | Orders | Export time |
    | --- | --- | --- | --- |
    | `tiny` | 1,500 | 15,000 | ~1 min |
    | `sf1` | 150,000 | 1,500,000 | ~10–15 min |
    | `sf10` | 1,500,000 | 15,000,000 | ~60+ min |

    The demo notebook uses `tiny`. Run `SHOW SCHEMAS IN tpch` in the Starburst query editor to see what's available on your cluster.

### Step 4 — Create a Mapping

A Mapping tells the platform which warehouse tables become graph nodes and edges.

```bash
curl -s -X POST http://localhost:30081/api/mappings \
  -H "Content-Type: application/json" \
  -H "X-Username: you@example.com" \
  -H "X-User-Role: admin" \
  -d '{
    "name": "TPC-H Customer Graph",
    "description": "Customers and nations from TPC-H",
    "node_definitions": [
      {
        "label": "Customer",
        "sql": "SELECT custkey, name, acctbal, mktsegment FROM tpch.sf1.customer",
        "primary_key": {"name": "custkey", "type": "INT64"},
        "properties": [
          {"name": "name",       "type": "STRING"},
          {"name": "acctbal",    "type": "DOUBLE"},
          {"name": "mktsegment", "type": "STRING"}
        ]
      },
      {
        "label": "Nation",
        "sql": "SELECT nationkey, name FROM tpch.sf1.nation",
        "primary_key": {"name": "nationkey", "type": "INT64"},
        "properties": [
          {"name": "name", "type": "STRING"}
        ]
      }
    ],
    "edge_definitions": [
      {
        "type": "BELONGS_TO",
        "from_node": "Customer",
        "to_node": "Nation",
        "sql": "SELECT custkey, nationkey FROM tpch.sf1.customer",
        "from_key": "custkey",
        "to_key": "nationkey",
        "properties": []
      }
    ]
  }'
```

### Step 5 — Create an Instance

```bash
curl -s -X POST http://localhost:30081/api/instances \
  -H "Content-Type: application/json" \
  -H "X-Username: you@example.com" \
  -H "X-User-Role: admin" \
  -d '{
    "mapping_id": <mapping_id>,
    "wrapper_type": "falkordb",
    "name": "My TPC-H Graph",
    "ttl": "PT4H"
  }'
```

The platform will:

1. Create a snapshot record
2. Queue an export job for the export worker
3. The export worker runs the `UNLOAD` queries on Starburst
4. Parquet files land in GCS
5. A wrapper pod is spawned and loads the data
6. Instance status moves: `waiting_for_snapshot` → `starting` → `running`

!!! warning "Known bug: starburst_catalog hardcoded to 'bigquery'"
    After creating an instance, you must patch the export jobs to use the correct catalog name. See [Known Issues → starburst_catalog bug](setup.md#known-issues) for the full fix.

---

## Method 2 — Direct Parquet Upload (No Starburst Needed)

If you don't have Starburst credentials, you can load your own data by uploading Parquet files directly to GCS. The wrapper pod only talks to GCS — it never touches Starburst.

### The GCS folder structure

The wrapper pod looks for Parquet files at this exact path layout:

```text
gs://{bucket}/{owner_email}/{mapping_id}/v{mapping_version}/{snapshot_id}/
    ├── nodes/
    │   ├── Customer/
    │   │   └── data.parquet
    │   └── Nation/
    │       └── data.parquet
    └── edges/
        └── BELONGS_TO/
            └── data.parquet
```

For example, if your username is `you@example.com`, mapping_id=1, snapshot_id=1:

```text
gs://graph-olap-local-dev/you@example.com/1/v1/1/nodes/Customer/data.parquet
gs://graph-olap-local-dev/you@example.com/1/v1/1/nodes/Nation/data.parquet
gs://graph-olap-local-dev/you@example.com/1/v1/1/edges/BELONGS_TO/data.parquet
```

!!! tip "Use the demo notebooks instead"
    The demo notebooks (01–04) handle this automatically — they create the mapping, instance, compute the correct GCS path, and upload via the fake-gcs HTTP API. If you just want to load custom data locally, copy the upload cell from any notebook as your template.

### Step 1 — Create your Parquet files

```python
import pandas as pd
import os

# --- Nodes ---
customers = pd.DataFrame({
    "custkey":    [1, 2, 3],
    "name":       ["Alice Corp", "Bob Ltd", "Carol Inc"],
    "acctbal":    [1200.50, 850.00, 3400.75],
    "mktsegment": ["FINANCE", "RETAIL", "FINANCE"],
})

nations = pd.DataFrame({
    "nationkey": [1, 2],
    "name":      ["UNITED KINGDOM", "GERMANY"],
})

# --- Edges ---
belongs_to = pd.DataFrame({
    "custkey":   [1, 2, 3],
    "nationkey": [1, 2, 1],
})

# Save
os.makedirs("nodes/Customer",    exist_ok=True)
os.makedirs("nodes/Nation",      exist_ok=True)
os.makedirs("edges/BELONGS_TO",  exist_ok=True)

customers.to_parquet("nodes/Customer/data.parquet",    index=False)
nations.to_parquet("nodes/Nation/data.parquet",        index=False)
belongs_to.to_parquet("edges/BELONGS_TO/data.parquet", index=False)
```

### Step 2 — Create a Mapping

```bash
curl -s -X POST http://localhost:30081/api/mappings \
  -H "Content-Type: application/json" \
  -H "X-Username: you@example.com" \
  -H "X-User-Role: admin" \
  -d '{
    "name": "My Custom Graph",
    "description": "Loaded from local Parquet files",
    "node_definitions": [
      {
        "label": "Customer",
        "sql": "SELECT custkey, name, acctbal, mktsegment FROM placeholder",
        "primary_key": {"name": "custkey", "type": "INT64"},
        "properties": [
          {"name": "name",        "type": "STRING"},
          {"name": "acctbal",     "type": "DOUBLE"},
          {"name": "mktsegment",  "type": "STRING"}
        ]
      },
      {
        "label": "Nation",
        "sql": "SELECT nationkey, name FROM placeholder",
        "primary_key": {"name": "nationkey", "type": "INT64"},
        "properties": [
          {"name": "name", "type": "STRING"}
        ]
      }
    ],
    "edge_definitions": [
      {
        "type": "BELONGS_TO",
        "from_node": "Customer",
        "to_node": "Nation",
        "sql": "SELECT custkey, nationkey FROM placeholder",
        "from_key": "custkey",
        "to_key": "nationkey",
        "properties": []
      }
    ]
  }'
```

Note the `mapping_id` from the response.

### Step 3 — Create an Instance

```bash
curl -s -X POST http://localhost:30081/api/instances \
  -H "Content-Type: application/json" \
  -H "X-Username: you@example.com" \
  -H "X-User-Role: admin" \
  -d '{
    "mapping_id": <mapping_id>,
    "wrapper_type": "falkordb",
    "name": "My Custom Instance",
    "ttl": "PT4H"
  }'
```

Note the `snapshot_id` from the response. The instance will be stuck at `waiting_for_snapshot` — that's expected.

### Step 4 — Upload Parquet files to GCS

For **local development** (fake-gcs-local), use the HTTP API — no `gsutil` or GCP credentials needed.
Get the correct prefix from the instance response (`snapshot_id` + your username):

```python
import requests, os

OWNER       = "you@example.com"   # same as X-Username header
MAPPING_ID  = <mapping_id>
SNAPSHOT_ID = <snapshot_id>
BUCKET      = "graph-olap-local-dev"
GCS         = "http://localhost:4443"   # or fake-gcs-local:4443 from inside Jupyter
PREFIX      = f"{OWNER}/{MAPPING_ID}/v1/{SNAPSHOT_ID}"

files = {
    f"{PREFIX}/nodes/Customer/data.parquet":   "nodes/Customer/data.parquet",
    f"{PREFIX}/nodes/Nation/data.parquet":     "nodes/Nation/data.parquet",
    f"{PREFIX}/edges/BELONGS_TO/data.parquet": "edges/BELONGS_TO/data.parquet",
}
for remote, local in files.items():
    with open(local, "rb") as f:
        data = f.read()
    r = requests.post(f"{GCS}/upload/storage/v1/b/{BUCKET}/o",
        params={"uploadType": "media", "name": remote}, data=data,
        headers={"Content-Type": "application/octet-stream"})
    print(f"  {remote.split('/')[-2:]}: HTTP {r.status_code}")
```

For **real GCS** (when `make secrets` has been run with a service account key), use `gsutil`:

```bash
OWNER=you@example.com
MAPPING_ID=<mapping_id>
SNAPSHOT_ID=<snapshot_id>
BUCKET=your-gcs-bucket
PREFIX="$OWNER/$MAPPING_ID/v1/$SNAPSHOT_ID"

gsutil cp nodes/Customer/data.parquet   gs://$BUCKET/$PREFIX/nodes/Customer/data.parquet
gsutil cp nodes/Nation/data.parquet     gs://$BUCKET/$PREFIX/nodes/Nation/data.parquet
gsutil cp edges/BELONGS_TO/data.parquet gs://$BUCKET/$PREFIX/edges/BELONGS_TO/data.parquet
```

### Step 5 — Mark the snapshot as ready

```bash
kubectl exec -n graph-olap-local deploy/postgres -- \
  psql -U control_plane -d control_plane -c \
  "UPDATE snapshots SET status='ready' WHERE id=$SNAPSHOT_ID;"
```

Within ~10 seconds, the reconciliation job detects the ready snapshot and starts the wrapper pod. The instance progresses: `waiting_for_snapshot` → `starting` → `running`.

### Step 6 — Query your graph

Check instance status via the API:

```bash
curl -s http://localhost:30081/api/instances/<instance_id> \
  -H "X-Username: you@example.com" \
  -H "X-User-Role: admin" | jq '.data.status'
```

Once `running`, query using the SDK inside Jupyter Labs — the SDK resolves the wrapper pod URL automatically:

```python
# Inside Jupyter Labs (http://localhost:30081/jupyter/lab)
import sys; sys.path.insert(0, "/home/jovyan/work")
from graph_olap_sdk import GraphOLAPClient

client = GraphOLAPClient("http://graph-olap-control-plane:8080", "you@example.com", "admin")
conn = client.instances.connect(<instance_id>)

rows = conn.query("MATCH (c:Customer)-[:BELONGS_TO]->(n:Nation) RETURN n.name, count(c) ORDER BY count(c) DESC")
print(rows.df())
```

To query from outside Jupyter (e.g. a script on your laptop), use `kubectl port-forward`:

```bash
# Find the pod name
kubectl get pods -n graph-olap-local | grep wrapper

# Port-forward it
kubectl port-forward -n graph-olap-local pod/<wrapper-pod-name> 8000:8000

# Then query via HTTP
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (c:Customer)-[:BELONGS_TO]->(n:Nation) RETURN n.name, count(c) ORDER BY count(c) DESC"}'
```

---

## The Demo Dataset — TPC-H

The included demo notebook uses the **TPC-H benchmark dataset** — a standard test dataset for analytical systems representing a wholesale supplier business.

### What's in TPC-H

| Node/Edge | Description | Key fields | SF0.01 rows |
| --- | --- | --- | --- |
| **Customer** | Wholesale customers | `custkey`, `name`, `acctbal`, `mktsegment` | 1,500 |
| **Nation** | Countries | `nationkey`, `name` | 25 |
| **SalesOrder** | Purchase orders | `orderkey`, `totalprice`, `orderstatus` | 15,000 |
| **BELONGS_TO** | Customer → Nation edge | `custkey`, `nationkey` | 1,500 |
| **PLACED** | Customer → SalesOrder edge | `custkey`, `orderkey` | 15,000 |

!!! info "Scale factor"
    The demo notebook uses **TPC-H SF0.01** (scale factor 0.01) — a small dataset suitable for local development. Larger scale factors (`sf0.1`, `sf1`) exist in Starburst but will take proportionally longer to export.

### Interesting queries you can run

```cypher
-- Customers per nation
MATCH (c:Customer)-[:BELONGS_TO]->(n:Nation)
RETURN n.name, count(c) AS customers
ORDER BY customers DESC

-- Top spenders
MATCH (c:Customer)-[:PLACED]->(o:SalesOrder)
RETURN c.name, sum(o.totalprice) AS total_spend
ORDER BY total_spend DESC
LIMIT 10

-- Market segment breakdown by nation
MATCH (c:Customer)-[:BELONGS_TO]->(n:Nation)
RETURN n.name, c.mktsegment, count(c) AS count
ORDER BY n.name, count DESC
```

---

## Parquet Column Requirements

The Parquet file columns must exactly match what you declared in the Mapping:

| Mapping field | Required Parquet column |
| --- | --- |
| `primary_key.name` | Must be present (used as graph node ID) |
| `properties[].name` | Must be present |
| `from_key` (edge) | Must be present (FK to source node's primary key) |
| `to_key` (edge) | Must be present (FK to target node's primary key) |

Extra columns in the Parquet file are ignored.
