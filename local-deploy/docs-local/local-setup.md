# Graph OLAP — Local Setup Guide

Complete step-by-step guide to get the full Graph OLAP stack running on your machine.

---

## What You Will End Up With

| Endpoint | What it is |
|---|---|
| `http://localhost:30082` | This setup guide |
| `http://localhost:30081/api/...` | Control Plane REST API |
| `http://localhost:30081/jupyter/lab` | Jupyter Labs (demo notebook included) |
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

### 2. Required Credentials

You need **both** of the following to run the full export pipeline:

| Credential | What it's for | Where to get it |
|---|---|---|
| **Starburst Galaxy** username + password | Exporting data from the warehouse | Galaxy UI → Settings → Service Accounts → Create |
| **GCP Service Account key** (JSON file) | Reading/writing Parquet files on GCS | GCP Console → IAM → Service Accounts → Create Key |

> Without these, the core API, documentation, and Jupyter still work — but creating graph instances (which require data export) will fail.

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

Copy the example environment file and fill in your values:

```bash
cd graph-olap-local-deploy
cp .env.example .env
```

Edit `.env`:

```bash
# Path to source code (only needed if repos are not siblings)
# export MONOREPO_ROOT=../graph-olap

# Starburst Galaxy credentials
export STARBURST_USER=your-service-account@your-org/accountadmin
export STARBURST_PASSWORD=your-galaxy-password

# GCP service account key for GCS access
export GCP_SA_KEY_JSON=$(cat /path/to/your-sa-key.json)
```

Then source it:

```bash
source .env
```

### Also update `helm/values-local.yaml`

Open `helm/values-local.yaml` and fill in these placeholders:

| Line | Placeholder | Replace with |
|---|---|---|
| `gcpProject` | `your-gcp-project-id` | Your GCP project ID |
| `gcs.bucket` | `your-gcs-bucket` | Your GCS bucket name |
| `starburst.url` | `your-cluster.trino.galaxy.starburst.io:443` | Your Starburst Galaxy cluster URL |
| `starburst.user` | `your-starburst-user@your-org/accountadmin` | Your Starburst service account |
| `GCS_BUCKET` (export-worker extraEnv) | `your-gcs-bucket` | Same GCS bucket name |

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

Available services: `control-plane`, `export-worker`, `falkordb-wrapper`, `ryugraph-wrapper`, `jupyter-labs`

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
5. **demo notebook** — copies the demo notebook into the Jupyter pod

When complete you will see:

```
================================================
[OK]    Deployment complete!
================================================

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
jupyter-labs-xxx                        1/1     Running
fake-gcs-local-xxx                      1/1     Running
local-infra-postgres-xxx                1/1     Running
local-infra-extension-server-xxx        1/1     Running
```

Check the API health:

```bash
curl http://localhost:30081/health
```

Expected response:
```json
{"status": "healthy"}
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

## Step 8 — Run the Demo Notebook (End-to-End)

Open Jupyter Labs:

```
http://localhost:30081/jupyter/lab
```

Open **`graph-olap-demo.ipynb`** — it is already in the file browser.

The notebook walks through the full pipeline:

1. **Create a Mapping** — Customer / Nation / SalesOrder from TPC-H dataset
2. **Create an Instance** — triggers the export pipeline
3. **Fix the catalog bug** — patches the DB so the export worker uses the correct Starburst catalog (see Known Issues below)
4. **Monitor export progress** — polls until all Parquet files land in GCS
5. **Run Cypher queries** — customers per nation, top spenders, market segments
6. **Visualise the graph** — interactive PyVis graph in the notebook

> The notebook uses `http://graph-olap-control-plane:8080` (direct in-cluster URL, no auth needed) and includes the DB patch automatically.

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
gs://your-bucket/snapshot-{snapshot_id}/
    ├── nodes/
    │   ├── {NodeLabel}/        e.g. nodes/Customer/data.parquet
    │   └── {NodeLabel}/        e.g. nodes/Nation/data.parquet
    └── edges/
        └── {EdgeType}/         e.g. edges/BELONGS_TO/data.parquet
```

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

```bash
SNAPSHOT_ID=<snapshot_id>
BUCKET=your-gcs-bucket

gsutil cp nodes/Customer/data.parquet   gs://$BUCKET/snapshot-$SNAPSHOT_ID/nodes/Customer/data.parquet
gsutil cp nodes/Nation/data.parquet     gs://$BUCKET/snapshot-$SNAPSHOT_ID/nodes/Nation/data.parquet
gsutil cp edges/BELONGS_TO/data.parquet gs://$BUCKET/snapshot-$SNAPSHOT_ID/edges/BELONGS_TO/data.parquet
```

#### Step 5 — Mark the snapshot as ready

The export worker normally does this automatically. Since you're bypassing it, patch the database directly:

```bash
kubectl exec -n graph-olap-local deploy/local-infra-postgres -- \
  psql -U control_plane -d control_plane -c \
  "UPDATE snapshots SET status='ready' WHERE id=$SNAPSHOT_ID;"
```

Within ~10 seconds the reconciliation job will detect the ready snapshot and start the wrapper pod. The instance will progress from `waiting_for_snapshot` → `starting` → `running`.

#### Step 6 — Query your graph

```bash
# Check instance status
curl -s http://localhost:30081/api/instances/<instance_id> \
  -H "X-Username: you@example.com" \
  -H "X-User-Role: admin" | jq '.data.status'

# Once running, query it
curl -s http://localhost:30081/api/instances/<instance_id>/query \
  -H "Content-Type: application/json" \
  -H "X-Username: you@example.com" \
  -H "X-User-Role: admin" \
  -d '{"query": "MATCH (n:Customer) RETURN n.name, n.acctbal"}'
```

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

### Export jobs fail with "table not found" (starburst_catalog bug)

The control-plane hardcodes `starburst_catalog = 'bigquery'` when creating export jobs, regardless of your config. This causes every export to fail silently.

**Workaround** (already included in the demo notebook):

After creating an instance, immediately run this in a notebook cell:

```python
import psycopg2
conn = psycopg2.connect(
    host="postgres", port=5432, dbname="control_plane",
    user="control_plane", password="control_plane"
)
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute(
        "UPDATE export_jobs SET starburst_catalog = 'tpch' WHERE snapshot_id = %s AND starburst_catalog = 'bigquery'",
        (snapshot_id,)
    )
    print(f"Patched {cur.rowcount} export jobs")
conn.close()
```

Replace `'tpch'` with your actual Starburst catalog name if different.

---

## Architecture Reference

```
http://localhost:30081
        │
        ▼
nginx Ingress Controller (NodePort 30081)
        │
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
| **jupyter-labs** | `jupyter-labs:latest` | Jupyter environment with graph-olap SDK pre-installed |
| **PostgreSQL** | `postgres:15-alpine` | Control plane database |
| **Extension Server** | `ghcr.io/predictable-labs/extension-repo` | Graph algorithm extensions for Ryugraph |
| **fake-gcs-local** | `fsouza/fake-gcs-server` | Local GCS emulator (used by export-worker only) |
