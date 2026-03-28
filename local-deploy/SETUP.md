# Graph OLAP — Local Setup Guide

Complete step-by-step guide to get the full Graph OLAP stack running on your machine.

---

## What You Will End Up With

| Endpoint | What it is |
|---|---|
| `http://localhost:30081` | Documentation site |
| `http://localhost:30081/api/...` | Control Plane REST API |
| `http://localhost:30081/jupyter/lab` | Jupyter Labs (5 demo notebooks + SDK included) |
| `http://localhost:30081/health` | Health check |

---

## Prerequisites

### 1. Required Tools

Install all of the following before starting:

| Tool | Min Version | Install |
|---|---|---|
| Docker | 24+ | https://docs.docker.com/get-docker/ |
| kubectl | any | `brew install kubectl` |
| Helm | 3+ | `brew install helm` |
| Local Kubernetes | any | see below |

**Pick one Kubernetes option (OrbStack recommended on macOS):**

```bash
# OrbStack (macOS) — recommended
brew install orbstack
# Then open OrbStack → Settings → Kubernetes → Enable

# OR Rancher Desktop
# https://rancherdesktop.io — enable Kubernetes in preferences

# OR Docker Desktop
# Preferences → Kubernetes → Enable Kubernetes

# OR minikube
brew install minikube && minikube start

# OR kind
brew install kind && kind create cluster
```

### 2. Credentials (Optional)

The demo notebooks work without any credentials — they use synthetic data and a local GCS emulator.

Credentials are only needed if you want to run the full export pipeline against a real Starburst Galaxy cluster and a real GCS bucket:

| Credential | What it's for | Where to get it |
|---|---|---|
| **Starburst Galaxy** username + password | Exporting data from the warehouse | Galaxy UI → Settings → Service Accounts → Create |
| **GCP Service Account key** (JSON file) | Reading/writing Parquet files on GCS | GCP Console → IAM → Service Accounts → Create Key |

Configure them via `make secrets` (Step 2).

---

## Step 1 — Clone Both Repositories

The local-deploy repo must be a sibling of the `graph-olap` source repo:

```
your-workspace/
├── graph-olap/               ← source code (monorepo)
└── graph-olap-local-deploy/  ← this repo
```

```bash
cd your-workspace
git clone <graph-olap-repo-url> graph-olap
git clone <graph-olap-local-deploy-repo-url> graph-olap-local-deploy
```

If you place them somewhere else, set `MONOREPO_ROOT`:

```bash
export MONOREPO_ROOT=/path/to/graph-olap
```

---

## Step 2 — Configure Credentials

> **Demo notebooks work without credentials** — all 6 notebooks generate synthetic data and use the local GCS emulator (fake-gcs-local). Skip to Step 3 if you just want to run the demos.

Run the interactive credential setup:

```bash
cd graph-olap-local-deploy
make secrets
```

This prompts for each value with inline instructions showing exactly where to find it in the Starburst Galaxy UI and GCP Console. It writes `.env` and updates `helm/values-local.yaml` automatically.

Then source the generated file:

```bash
source .env
```

---

## Step 3 — Check Prerequisites

```bash
make prereqs
```

All items should show `[OK]`. Fix any failures before continuing.

---

## Step 4 — Build Docker Images

This builds all 6 service images from source. Takes 10–20 minutes the first time (subsequent builds are fast due to Docker layer caching).

```bash
make build
```

To build a single service only:

```bash
make build SVC=control-plane
```

Available services: `control-plane`, `export-worker`, `falkordb-wrapper`, `ryugraph-wrapper`, `documentation`, `jupyter-labs`

---

## Step 5 — Deploy to Kubernetes

```bash
make deploy
```

This runs in 5 phases:
1. **nginx ingress** — installs the ingress controller on NodePort 30081
2. **local-infra** — deploys PostgreSQL + extension-server + secrets
3. **graph-olap** — deploys control-plane + export-worker
4. **jupyter-labs** — deploys the Jupyter pod
5. **demo notebooks** — copies all 5 demo notebooks + `graph_olap_sdk.py` into the Jupyter pod

When complete you will see:

```
================================================
[OK]    Deployment complete!
================================================

  Documentation:      http://localhost:30081
  Jupyter Labs:       http://localhost:30081/jupyter/lab
  Control Plane API:  http://localhost:30081/api/...
  Health endpoint:    http://localhost:30081/health
```

---

## Step 6 — Verify Everything Is Running

```bash
make status
```

All pods should show `Running`. Example output:

```
NAME                                    READY   STATUS
graph-olap-control-plane-xxx            1/1     Running
graph-olap-export-worker-xxx            1/1     Running
graph-olap-documentation-xxx            1/1     Running
jupyter-labs-xxx                        1/1     Running
fake-gcs-local-xxx                      1/1     Running
postgres-xxx                            1/1     Running
extension-server-xxx                    1/1     Running
```

Check the API health:

```bash
curl http://localhost:30081/health
```

Expected response:
```json
{"status": "healthy", "database": "unknown", "version": "0.1.0"}
```

---

## Step 7 — Make Your First API Call

No JWT or login required. Pass `X-Username` and `X-User-Role` headers directly:

```bash
# List all mappings (empty on fresh install)
curl http://localhost:30081/api/mappings \
  -H "X-Username: you@example.com" \
  -H "X-User-Role: admin"
```

Available roles: `analyst`, `admin`, `ops`

---

## Step 8 — Run the Demo Notebooks (End-to-End)

Open Jupyter Labs:

```
http://localhost:30081/jupyter/lab
```

Six demo notebooks are pre-loaded — no Starburst or GCP credentials needed:

| Notebook | Graph | Nodes | Edges |
|---|---|---|---|
| `01-movie-graph-demo.ipynb` | Movies + Actors + Directors | 3 types | ACTED_IN, DIRECTED |
| `02-music-graph-demo.ipynb` | Artists + Albums + Songs | 3 types | RELEASED, CONTAINS |
| `03-ecommerce-graph-demo.ipynb` | Customers + Products + SalesOrders | 3 types | PURCHASED, PLACED |
| `04-ipl-t20-graph-demo.ipynb` | IPL Teams + Players + Games | 3 types | PLAYS_FOR, PLAYED_IN, WON |
| `05-algorithms-demo.ipynb` | Co-actor network (30 actors, 25 movies) | 2 types | ACTED_IN |
| `00-cleanup.ipynb` | Instance management + bulk delete | — | — |

Each notebook:

1. Generates synthetic data as Parquet files
2. Creates a mapping + instance via the API (using `graph_olap_sdk`)
3. Uploads Parquet directly to local GCS (fake-gcs-local)
4. Polls until the FalkorDB wrapper pod is running
5. Runs Cypher queries against the live graph
6. Renders an interactive PyVis graph visualisation

---

## Demo Notebooks

All notebooks follow the same pipeline: generate synthetic data → upload Parquet to GCS → create FalkorDB instance → Cypher queries → interactive PyVis graph. No Starburst or GCP credentials needed.

---

### `movie-graph-demo.ipynb`

**Graph:** Movies · Actors · Directors

**Edges:** `ACTED_IN`, `DIRECTED`

**Cypher queries included:**

- Node counts by label
- Christopher Nolan filmography
- Actors who appeared in 2+ Nolan films
- Keanu Reeves filmography
- Co-star pairs (actors who share movies)
- Connection path: Keanu Reeves → Cillian Murphy

**Visualisation:** Actor–Movie–Director network coloured by node type.

---

### `music-graph-demo.ipynb`

**Graph:** Artists · Albums · Songs

**Edges:** `RELEASED`, `CONTAINS`

**Cypher queries included:**

- Node counts by label
- Albums per artist
- Top 10 longest songs
- Artists ranked by number of albums
- Song count per genre

**Visualisation:** Artist → Album → Song hierarchy, coloured by node type.

---

### `ecommerce-graph-demo.ipynb`

**Graph:** Customers · Products · SalesOrders

**Edges:** `PURCHASED`, `PLACED`

**Cypher queries included:**

- Node counts by label
- Top customers by total spend
- Most popular products
- Co-purchaser pairs (customers who bought the same product)
- Revenue by product category (delivered orders only)

**Visualisation:** Customer–Product purchase network, sized by spend.

---

### `ipl-t20-graph-demo.ipynb`

**Graph:** IPL Teams · Players · Games

**Edges:** `PLAYS_FOR`, `PLAYED_IN`, `WON`

**Cypher queries included:**

- Node counts by label
- All-time top run scorers
- Best bowlers by total wickets
- Teams with most wins
- Man of the Match awards
- Players by nationality
- Players who featured in their team's wins

**Visualisation:** Teams (gold stars) → Players (blue) → Games (green), interactive and draggable.

![IPL T20 graph visualisation](docs/screenshots/ipl-graph-demo.png)

---

### Running all notebooks in parallel (multi-tenancy demo)

**To prove multi-tenancy — run multiple notebooks in parallel:**

- Open any combination of notebooks in separate tabs
- Run each one (Kernel → Restart Kernel and Run All Cells)
- Each spawns its own independent FalkorDB wrapper pod
- Check with `make status` or `make dashboard` to see all pods running simultaneously

> All notebooks are designed for local, credential-free execution and are copied automatically by `make deploy`.
> Each notebook cleans up its wrapper pod at the end — the last cell deletes the instance automatically.

---

### `algorithms-demo.ipynb`

**Graph:** Co-actor network — 30 actors and 25 movies (synthetic data)

**What it demonstrates:**

| Algorithm | What it answers |
|---|---|
| **PageRank** | Which actors are most influential in the network? |
| **Betweenness Centrality** | Which actors act as bridges between communities? |
| **Community Detection (Louvain)** | Which groups of actors frequently work together? |
| **Shortest Path** | How many degrees of separation between two actors? |
| **Connected Components** | Are there isolated sub-networks? |
| **Clustering Coefficient** | How tightly-knit is each actor's immediate circle? |

**How it works:**

1. Loads movie/actor data into FalkorDB (same pipeline as other demos)
2. Runs a Cypher query to fetch all `(actor)-[:ACTED_IN]->(movie)` pairs
3. Builds a **co-actor graph** in NetworkX (actors connected if they share a movie, edge weight = number of shared movies)
4. Runs NetworkX algorithms on the in-memory graph
5. Renders an interactive PyVis visualisation — node size = PageRank, colour = community

**Visualisation:** Actors coloured by community, sized by PageRank. Hover for centrality scores.

---

## Python SDK (`graph_olap_sdk`)

A lightweight SDK is available in every Jupyter session at `/home/jovyan/work/graph_olap_sdk.py`.
It wraps all raw HTTP calls with a clean, typed API — the same interface used in the production `graph_olap` package.

### Quick start

```python
import sys
sys.path.insert(0, "/home/jovyan/work")
from graph_olap_sdk import GraphOLAPClient, Algorithms

client = GraphOLAPClient(username="you@example.com")

# Create instance and connect
inst = client.instances.create_and_wait(mapping_id, snapshot_id)
conn = client.instances.connect(inst)

# Query → DataFrame
df = conn.query("MATCH (n:Movie) RETURN n.title AS title, n.year AS year").df()

# Query → NetworkX graph
G = conn.query(
    "MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) RETURN a.name AS source, m.title AS target"
).nx()

# Run algorithms
algo    = conn.algo          # Algorithms() instance
scores  = algo.pagerank(G)
top10   = algo.top_n(scores, n=10)

# Cleanup
client.instances.terminate(inst["id"])
```

### SDK classes

| Class | Purpose |
| --- | --- |
| `GraphOLAPClient` | Top-level client — configure API URL, username, role |
| `InstanceResource` | `client.instances` — list, create, connect, terminate, bulk_delete |
| `Connection` | Active link to a wrapper pod — `.query()` returns `QueryResult` |
| `QueryResult` | Wraps raw results — `.data`, `.df()`, `.nx()` |
| `Algorithms` | NetworkX algorithm helpers via `conn.algo` |
| `AdminResource` | `client.admin` — bulk_delete alias |

### QueryResult output formats

```python
result = conn.query("MATCH (n:Actor) RETURN n.name AS name, n.age AS age")

result.data      # list of dicts
result.df()      # pandas DataFrame
result.nx()      # NetworkX graph (auto-detects source/target columns)
result.nx(source="a", target="b")  # specify columns explicitly
```

### Available algorithms (via `conn.algo`)

```python
algo = conn.algo

# Centrality
algo.pagerank(G)
algo.betweenness_centrality(G)
algo.closeness_centrality(G)
algo.degree_centrality(G)
algo.eigenvector_centrality(G)

# Community
algo.community_detection(G)     # Louvain — returns list of node sets

# Connectivity
algo.connected_components(G)    # sorted by size, largest first

# Path finding
algo.shortest_path(G, "Alice", "Bob")
algo.all_shortest_paths(G, "Alice", "Bob")

# Structural
algo.triangle_count(G)
algo.clustering_coefficient(G)

# Helpers
algo.top_n(scores, n=10)                    # top N (node, score) tuples
algo.scores_df(scores, node_col="actor")    # scores as DataFrame
algo.write_scores(G, scores, "pagerank")    # write scores back to graph attrs
```

---

## Instance Management

### Delete all active instances

```bash
make clean-instances
```

### Delete instances older than N hours

```bash
make clean-old-instances          # default: older than 2 hours
make clean-old-instances HOURS=4  # older than 4 hours
```

### Bulk delete from Jupyter (with filters)

Use `cleanup.ipynb` or the SDK directly:

```python
# Preview (dry run)
client.instances.bulk_delete(older_than_hours=2, dry_run=True)

# Delete all instances older than 2 hours
client.instances.bulk_delete(older_than_hours=2)

# Delete only instances owned by a specific user
client.instances.bulk_delete(owner="alice@example.com")

# Combine filters
client.instances.bulk_delete(older_than_hours=1, owner="alice@example.com", dry_run=True)
```

### Memory guidance

Each wrapper pod requests **1Gi RAM**. On a 12GB node, safely run 4–5 pods in parallel.
If pods fail to start with `OOMKilled`, run `make clean-instances` to free memory.

---

## Common Commands

```bash
make build                       # Build all images
make build SVC=control-plane     # Build one image

make deploy                      # Deploy / re-deploy full stack
make status                      # Show pod health
make logs SVC=control-plane      # Tail logs for a service
make logs SVC=export-worker
make logs SVC=jupyter-labs

make teardown                    # Delete everything (namespace)
```

### Rebuilding After Code Changes

```bash
make build SVC=control-plane     # Rebuild the changed service
make deploy                      # Re-deploy (Helm picks up the new image)
```

---

## Kubernetes Dashboard (Web UI)

A web-based dashboard for monitoring pods, logs, and resources in your browser.

### Install and open

```bash
make dashboard
```

This installs the dashboard, prints a login token, starts a local proxy, and gives you the URL.

### Open in browser

```
http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

Select **Token** on the login screen and paste the token printed by `make dashboard`.

Then switch the namespace to **graph-olap-local** in the left sidebar to see your pods.

### Useful views

| Sidebar item | What to look for |
| --- | --- |
| **Workloads → Pods** | All running pods including wrapper pods spawned per graph instance |
| **Workloads → Deployments** | control-plane, export-worker, jupyter-labs health |
| **Config → Config Maps** | Inspect GCS bucket and storage emulator settings |
| **Storage → Persistent Volume Claims** | Jupyter notebook storage |

### Refresh token (expires after 1 hour)

```bash
make dashboard-token
```

### Stop the proxy

```bash
make dashboard-stop
```

---

## Troubleshooting

### Pods stuck in `CrashLoopBackOff`

```bash
make logs SVC=control-plane
kubectl describe pod -n graph-olap-local -l app=graph-olap-control-plane
```

### `ErrImageNeverPull`

Images were not built or not loaded into your K8s daemon:

```bash
make build
```

### Port 30081 not responding after deploy

Services may still be starting — wait 60 seconds and retry. Then:

```bash
make status   # check pod readiness
```

On **minikube**, NodePorts are not on `localhost` — run:

```bash
minikube service -n graph-olap-local graph-olap-control-plane --url
```

### Helm dependency errors

```bash
helm dependency update helm/charts/graph-olap
helm dependency update helm/charts/local-infra
```

### Reset everything and start fresh

```bash
make teardown
source .env
make deploy
```

---

## Loading Data Without Starburst

If you don't have Starburst credentials, you can load your own data directly by uploading Parquet files to GCS in the correct folder structure. The wrapper pod will load them automatically — it never talks to Starburst, only to GCS.

### How It Works

The wrapper pod expects Parquet files at this exact GCS path layout:

```
gs://your-bucket/{owner}/{mapping_id}/v1/{snapshot_id}/
    ├── nodes/
    │   ├── {NodeLabel}/        e.g. nodes/Customer/data.parquet
    │   └── {NodeLabel}/        e.g. nodes/Nation/data.parquet
    └── edges/
        └── {EdgeType}/         e.g. edges/BELONGS_TO/data.parquet
```

Where `owner` is the `X-Username` header value used when creating the instance (e.g. `demo@example.com`).

### Step-by-Step

#### Step 1 — Create your Parquet files

In Python (using pandas or polars):

```python
import pandas as pd

# --- Nodes ---
customers = pd.DataFrame({
    "custkey": [1, 2, 3],
    "name":    ["Alice Corp", "Bob Ltd", "Carol Inc"],
    "acctbal": [1200.50, 850.00, 3400.75],
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

# Save as Parquet files
import os
os.makedirs("nodes/Customer", exist_ok=True)
os.makedirs("nodes/Nation",   exist_ok=True)
os.makedirs("edges/BELONGS_TO", exist_ok=True)

customers.to_parquet("nodes/Customer/data.parquet",     index=False)
nations.to_parquet("nodes/Nation/data.parquet",         index=False)
belongs_to.to_parquet("edges/BELONGS_TO/data.parquet",  index=False)
```

#### Step 2 — Create a Mapping via the API

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

Note the `mapping_id` and `snapshot_id` from the response.

#### Step 3 — Create an Instance to get the snapshot_id

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

Note the `snapshot_id` from the response. The instance will be stuck in `waiting_for_snapshot` — that is expected at this point.

#### Step 4 — Upload Parquet files to GCS

Upload via the fake-gcs HTTP API (works from inside the Jupyter pod or any pod in the cluster):

```python
import requests

BUCKET   = "graph-olap-local-dev"
GCS      = "http://fake-gcs-local:4443"
OWNER    = "you@example.com"   # must match X-Username used when creating the instance
MAPPING_ID  = "<mapping_id>"
SNAPSHOT_ID = "<snapshot_id>"
PREFIX   = f"{OWNER}/{MAPPING_ID}/v1/{SNAPSHOT_ID}"

files = [
    ("nodes/Customer/data.parquet",   f"{PREFIX}/nodes/Customer/data.parquet"),
    ("nodes/Nation/data.parquet",     f"{PREFIX}/nodes/Nation/data.parquet"),
    ("edges/BELONGS_TO/data.parquet", f"{PREFIX}/edges/BELONGS_TO/data.parquet"),
]

for local, remote in files:
    with open(local, "rb") as f:
        data = f.read()
    url = f"{GCS}/upload/storage/v1/b/{BUCKET}/o?uploadType=media&name={remote}"
    resp = requests.post(url, data=data, headers={"Content-Type": "application/octet-stream"})
    print(f"{'✅' if resp.status_code in (200,201) else '❌'} {remote}: {resp.status_code}")
```

#### Step 5 — Bypass the export worker and mark the snapshot as ready

The export worker normally handles this via Starburst. Since we're loading Parquet directly, bypass it via psycopg2:

```python
import psycopg2

conn = psycopg2.connect(
    host="postgres", port=5432,
    dbname="control_plane", user="control_plane", password="control_plane"
)
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute(
        "UPDATE export_jobs SET status='failed' WHERE snapshot_id=%s AND status='pending'",
        (snapshot_id,)
    )
    cur.execute(
        "UPDATE snapshots SET status='ready' WHERE id=%s",
        (snapshot_id,)
    )
conn.close()
```

Within ~10 seconds the reconciliation job will detect the ready snapshot and start the wrapper pod. The instance will progress from `waiting_for_snapshot` → `starting` → `running`.

#### Step 6 — Query your graph

```python
import requests, time

# Poll until running
while True:
    status = requests.get(
        f"http://graph-olap-control-plane:8080/api/instances/{instance_id}",
        headers={"X-Username": "you@example.com", "X-User-Role": "admin"}
    ).json()["data"]["status"]
    print(status)
    if status == "running": break
    time.sleep(10)

# Get wrapper pod name and query directly
inst = requests.get(
    f"http://graph-olap-control-plane:8080/api/instances/{instance_id}",
    headers={"X-Username": "you@example.com", "X-User-Role": "admin"}
).json()["data"]
pod_name = inst["pod_name"]

result = requests.post(
    f"http://{pod_name}:8000/query",
    json={"query": "MATCH (n:Customer) RETURN n.name, n.acctbal"}
)
print(result.json()["rows"])
```

> Note: query the wrapper pod directly at `http://{pod_name}:8000/query` — not via the control plane API.

### Column Requirements

The Parquet file columns must exactly match what you declared in the Mapping:

| Mapping field | Required Parquet column |
|---|---|
| `primary_key.name` | Must be present (used as graph node ID) |
| `properties[].name` | Must be present |
| `from_key` (edge) | Must be present (foreign key to source node's primary_key) |
| `to_key` (edge) | Must be present (foreign key to target node's primary_key) |

Extra columns in the Parquet file are ignored.

---

## Known Issues

### Export worker claims and fails jobs (local demo bypass)

In the local setup there is no Starburst Galaxy connection, so the export worker will claim and fail any `pending` export jobs. This causes instances to get stuck.

**Workaround** (already included in all demo notebooks):

After creating an instance, immediately fail the pending export jobs and mark the snapshot ready via psycopg2:

```python
import psycopg2
conn = psycopg2.connect(
    host="postgres", port=5432, dbname="control_plane",
    user="control_plane", password="control_plane"
)
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute(
        "UPDATE export_jobs SET status='failed' WHERE snapshot_id=%s AND status='pending'",
        (snapshot_id,)
    )
    cur.execute(
        "UPDATE snapshots SET status='ready' WHERE id=%s",
        (snapshot_id,)
    )
conn.close()
```

> `status='failed'` is required — the DB check constraint only allows: `pending`, `running`, `failed`, `cancelled_by_user`.

---

## Architecture Reference

```
http://localhost:30081
        │
        ▼
nginx Ingress Controller (NodePort 30081)
        │
        ├── /              → Documentation (MkDocs)
        ├── /api/*         → Control Plane (FastAPI) — auth: X-Username + X-User-Role headers
        ├── /jupyter       → Jupyter Labs
        ├── /health        → Control Plane health
        └── /{instance}/*  → Wrapper pods (spawned dynamically per graph instance)

Control Plane
        ├── PostgreSQL      — stores mappings, snapshots, instances, users
        ├── Extension Server — graph algorithm extensions
        └── Kubernetes API  — spawns/deletes wrapper pods on demand

Export Worker
        ├── Starburst Galaxy — runs UNLOAD queries (requires STARBURST_USER + PASSWORD)
        └── GCS             — writes Parquet files (requires GCP_SA_KEY_JSON)

Wrapper Pod (created per instance)
        ├── FalkorDB or Ryugraph — in-memory graph database
        └── GCS             — downloads Parquet files on startup
```

---

## What Each Service Does

| Service | Image | Description |
|---|---|---|
| **control-plane** | `control-plane:latest` | FastAPI REST API — manages mappings, instances, users |
| **export-worker** | `export-worker:latest` | Polls for export jobs, runs UNLOAD on Starburst, writes to GCS |
| **falkordb-wrapper** | `falkordb-wrapper:local` | Graph pod (FalkorDB engine) — spawned per instance |
| **ryugraph-wrapper** | `ryugraph-wrapper:local` | Graph pod (KuzuDB engine) — spawned per instance |
| **documentation** | `documentation:latest` | MkDocs Material docs site |
| **jupyter-labs** | `jupyter-labs:latest` | Jupyter environment with graph-olap SDK pre-installed |
| **PostgreSQL** | `postgres:15-alpine` | Control plane database |
| **Extension Server** | `ghcr.io/predictable-labs/extension-repo` | Graph algorithm extensions for Ryugraph |
| **fake-gcs-local** | `fsouza/fake-gcs-server` | Local GCS emulator (used by export-worker only) |
