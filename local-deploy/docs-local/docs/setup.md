# Setup Guide

Get the full Graph OLAP stack running on your machine.

!!! success "What you'll have when done"
    | Endpoint | What it is |
    |---|---|
    | `http://localhost:30081/api/...` | Control Plane REST API |
    | `http://localhost:30081/jupyter/lab` | Jupyter Labs (pre-configured with the Python SDK + demo notebook) |
    | `http://localhost:30081/health` | Health check |

---

## Prerequisites

### Tools

Install all of the following before starting:

=== "macOS (Homebrew)"

    ```bash
    brew install kubectl helm
    ```

=== "Linux"

    ```bash
    # kubectl
    curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install kubectl /usr/local/bin/

    # helm
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    ```

| Tool | Min Version | Notes |
|---|---|---|
| Docker | 24+ | [Install](https://docs.docker.com/get-docker/) |
| kubectl | any | Kubernetes CLI |
| Helm | 3+ | Kubernetes package manager |
| Local Kubernetes | any | See below |

### Kubernetes — Pick One

!!! tip "Recommended on macOS: OrbStack"
    OrbStack is the fastest option on macOS — lightweight, low memory, and its K8s cluster shares the Docker daemon so images don't need to be manually loaded.

=== "OrbStack (macOS — recommended)"

    ```bash
    brew install orbstack
    # Open OrbStack → Settings → Kubernetes → Enable
    ```

=== "Rancher Desktop"

    Download from [rancherdesktop.io](https://rancherdesktop.io) and enable Kubernetes in preferences.

=== "Docker Desktop"

    Preferences → Kubernetes → Enable Kubernetes

=== "minikube"

    ```bash
    brew install minikube && minikube start
    ```

=== "kind"

    ```bash
    brew install kind && kind create cluster
    ```

### Credentials

You need **both** of the following to run the full export pipeline:

| Credential | What it's for | Where to get it |
|---|---|---|
| **Starburst Galaxy** username + password | Exporting data from the warehouse | Galaxy UI → Settings → Service Accounts → Create |
| **GCP Service Account key** (JSON file) | Reading/writing Parquet files on GCS | GCP Console → IAM → Service Accounts → Create Key |

!!! note "Running without credentials"
    Without these, the core API and Jupyter still work — but creating graph instances that require data export will fail. You can load data directly via Parquet instead — see [Loading Data](data.md).

---

## Step 1 — Clone Both Repositories

The local-deploy repo must be a **sibling** of the `graph-olap` source repo:

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

If they're in a different location, set `MONOREPO_ROOT`:

```bash
export MONOREPO_ROOT=/path/to/graph-olap
```

---

## Step 2 — Configure Credentials

!!! tip "Demo notebooks work without credentials"
    All 6 demo notebooks generate their own synthetic data and use a local GCS emulator. You can skip this step and go straight to `make build` if you just want to run the demos.

Run the interactive credential setup:

```bash
cd graph-olap-local-deploy
make secrets
```

This prompts for each value with inline instructions showing exactly where to find it in the Starburst Galaxy UI and GCP Console. It writes `.env` and updates `helm/values-local.yaml` automatically.

```
================================================
 Graph OLAP — Credential Setup
================================================

--- Starburst Galaxy ----------------------------------------

      ↳ Open https://galaxy.starburst.io → Clusters → your cluster
      ↳ Click 'Connection info' — copy the hostname
  Cluster host:
      ↳ Open https://galaxy.starburst.io → Settings → Service Accounts
  Service account email:
  Service account password:

--- Google Cloud Storage ------------------------------------

      ↳ GCP Console → your project ID (top-left dropdown)
  GCP project ID:
      ↳ GCP Console → Cloud Storage → Buckets
  GCS bucket name:
      ↳ GCP Console → IAM → Service Accounts → Keys → Add Key → JSON
  Path to SA key JSON file:
```

If the cluster namespace is already running, it will offer to apply secrets live and restart affected pods.

Then source the generated `.env`:

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

Builds all service images from source. Takes **10–20 minutes** the first time — fast on subsequent builds thanks to Docker layer caching.

```bash
make build
```

To build a single service:

```bash
make build SVC=control-plane
```

!!! info "Available services"
    `control-plane` · `export-worker` · `falkordb-wrapper` · `ryugraph-wrapper` · `jupyter-labs`

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

All pods should show `Running`:

![All pods running — watch kubectl get pods output](assets/screenshots/pods-running.png)

```
NAME                                    READY   STATUS
graph-olap-control-plane-xxx            1/1     Running
graph-olap-export-worker-xxx            1/1     Running
jupyter-labs-xxx                        1/1     Running
fake-gcs-local-xxx                      1/1     Running
postgres-xxx                            1/1     Running
local-infra-extension-server-xxx        1/1     Running
```

Check the API health:

```bash
curl http://localhost:30081/health
```

Expected:

```json
{"status": "healthy"}
```

---

## Step 7 — Make Your First API Call

No JWT or login required locally. Pass `X-Username` and `X-User-Role` headers directly:

```bash
# List all mappings (empty on fresh install)
curl http://localhost:30081/api/mappings \
  -H "X-Username: you@example.com" \
  -H "X-User-Role: admin"
```

Available roles: `analyst` · `admin` · `ops`

---

## Step 8 — Run the Demo Notebooks

Open Jupyter Labs:

```
http://localhost:30081/jupyter/lab
```

Six numbered notebooks are pre-loaded in the file browser. Run them in order:

| # | Notebook | What it demonstrates |
| --- | --- | --- |
| `00` | `00-cleanup.ipynb` | List + bulk-delete instances — run this after testing to free resources |
| `01` | `01-movie-graph-demo.ipynb` | Movie/actor/director graph — Cypher queries, PyVis visualisation |
| `02` | `02-music-graph-demo.ipynb` | Artist/album/track graph — multi-hop traversals, genre analysis |
| `03` | `03-ecommerce-graph-demo.ipynb` | Product/customer/order graph — recommendation queries |
| `04` | `04-ipl-t20-graph-demo.ipynb` | Cricket stats graph — player/team/match relationships |
| `05` | `05-algorithms-demo.ipynb` | Co-actor network — PageRank, Betweenness, Louvain communities, PyVis |

All notebooks:

- Generate synthetic data locally — **no Starburst credentials needed**
- Upload Parquet files to **fake-gcs-local** (the in-cluster GCS emulator)
- Bypass the export worker by marking the snapshot ready directly in PostgreSQL
- Use `graph_olap_sdk` — the local Python SDK pre-loaded at `/home/jovyan/work/graph_olap_sdk.py`

!!! tip "Each notebook is fully self-contained"
    Every notebook creates its own graph instance and cleans up after itself. Run `00-cleanup.ipynb` at the end to delete any leftover instances and free wrapper pods.

---

## Multiple Users & Multiple Instances

Yes — multiple analysts can use the platform simultaneously on the same machine. Each analyst gets a **completely isolated pod** with their own data. There is no shared state between instances.

### Add more users

```bash
# Add a second analyst
curl -s -X POST http://localhost:30081/api/users \
  -H "Content-Type: application/json" \
  -H "X-Username: admin@example.com" \
  -H "X-User-Role: admin" \
  -d '{"username": "analyst2@example.com", "role": "analyst"}'
```

### Each analyst creates their own instance

```bash
# Analyst 1 — Customer graph from TPC-H
POST /api/mappings  →  mapping_id=1
POST /api/instances { "mapping_id": 1, "name": "Customer Network", "ttl": "PT4H" }
# → gets their own pod: instance_id=1

# Analyst 2 — Supply chain graph (completely different data)
POST /api/mappings  →  mapping_id=2
POST /api/instances { "mapping_id": 2, "name": "Supply Chain", "ttl": "PT4H" }
# → gets their own pod: instance_id=2
```

Both instances run in parallel. Analyst 1's heavy query does not affect Analyst 2's pod.

### Resource limits on a laptop

Each instance pod consumes memory proportional to the loaded graph:

| Dataset | Approx. pod memory | Simultaneous instances (16GB laptop) |
| --- | --- | --- |
| TPC-H `tiny` (~16k rows) | ~150 MB | 10+ |
| TPC-H `sf1` (~1.6M rows) | ~1–2 GB | 4–6 |
| TPC-H `sf10` (~16M rows) | ~8–12 GB | 1–2 |

!!! tip "Check running instances"
    ```bash
    curl http://localhost:30081/api/instances \
      -H "X-Username: admin@example.com" \
      -H "X-User-Role: admin" | jq '.data[] | {id, name, status, expires_at}'
    ```

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

!!! warning "minikube users"
    NodePorts are not on `localhost` in minikube. Run:
    ```bash
    minikube service -n graph-olap-local graph-olap-control-plane --url
    ```

### Helm dependency errors

```bash
helm dependency update helm/charts/graph-olap
helm dependency update helm/charts/local-infra
```

### Reset and start fresh

```bash
make teardown
source .env
make deploy
```

---

## Known Issues

### Export jobs fail with "table not found" (if using real Starburst)

If you configure real Starburst credentials, the control-plane may hardcode `starburst_catalog = 'bigquery'` when creating export jobs, causing exports to fail silently.

!!! note "Not an issue for the demo notebooks"
    All 6 demo notebooks bypass the export worker entirely — they upload Parquet files directly to fake-gcs-local and mark the snapshot ready in PostgreSQL. This known issue only affects workflows that use real Starburst Galaxy export.

**Workaround** (if using real Starburst):

```python
import psycopg2
conn = psycopg2.connect(
    host="postgres", port=5432, dbname="graph_olap",
    user="graph_olap", password="graph_olap"
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

Replace `'tpch'` with your actual Starburst catalog name.

---

## What's Next?

Now that the stack is running, explore the rest of the documentation:

| Topic | Where to go | What you'll find |
| --- | --- | --- |
| **Demo notebooks** | [Notebooks](notebooks.md) | All 6 notebooks explained — schemas, sample queries, service map |
| **Load data** | [Loading Data](data.md) | Connect Starburst, upload Parquet files, TPC-H demo dataset |
| **REST API** | [API Reference](api.md) | All endpoints — mappings, instances, query, users, health |
| **Python SDK** | [Python SDK](sdk.md) | `graph_olap_sdk` — client, algorithms, QueryResult, bulk delete |
| **Cypher queries** | [Query Cookbook](queries.md) | ~20 ready-to-run queries — lookups, aggregations, paths, algorithms |
| **PostgreSQL tables** | [DB & Schema](db-schema.md) | `mappings`, `snapshots`, `export_jobs`, `instances`, `users` — with debug SQL |
| **Graph schema** | [DB & Schema → Graph Schema](db-schema.md#graph-schema--inside-the-wrapper-pod) | How Mapping node/edge definitions map to graph labels and relationship types |
| **How it all fits** | [Architecture](architecture.md) | Service overview, FalkorDB vs KuzuDB, local vs production |
| **Full platform flow** | [Flow](flow.md) | End-to-end flow diagram — from mapping definition to query results |
| **Use cases** | [Use Cases](use-cases.md) | Fraud detection, AML, supply chain, customer 360 — with Cypher examples |
