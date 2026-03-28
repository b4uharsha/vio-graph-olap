# Graph OLAP — Local Deployment

Self-contained tooling to build and run the full Graph OLAP stack on any developer machine. No internal tools, no private registries, no Earthly.

---

## What You Get

| Endpoint | What it is |
|----------|-----------|
| `http://localhost:30081/jupyter/lab` | Jupyter Labs — 6 demo notebooks pre-loaded |
| `http://localhost:30081/api/...` | Control Plane REST API |
| `http://localhost:30081/health` | Health check |
| `http://localhost:30082` | Local setup guide (docs) |

Six notebooks are ready to run immediately — no Starburst or GCP credentials required for any of them:

| # | Notebook | What it shows |
|---|----------|--------------|
| `01` | Movie Graph | Movies, actors, directors, genres — PyVis interactive graph |
| `02` | Music Graph | Artists, albums, tracks, collaborations |
| `03` | E-commerce Graph | Customers, products, orders, recommendations |
| `04` | IPL T20 Graph | Cricket players, teams, matches — PyVis interactive graph |
| `05` | Algorithms Demo | PageRank, Betweenness, Louvain communities, Shortest Path on a co-actor network |
| `00` | Cleanup | Utility to terminate running instances |

All notebooks generate their own synthetic data and upload it to the local GCS emulator (fake-gcs-local). The export worker is bypassed entirely — wrapper pods start from GCS directly.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker | 24+ | https://docs.docker.com/get-docker/ |
| kubectl | any | https://kubernetes.io/docs/tasks/tools/ |
| Helm | 3+ | `brew install helm` |
| Local Kubernetes | any | see below |

**Local Kubernetes options (pick one):**
- **OrbStack** (macOS, recommended): `brew install orbstack` → enable K8s in settings
- **Rancher Desktop** (macOS/Windows/Linux): https://rancherdesktop.io
- **Docker Desktop**: enable Kubernetes in preferences
- **minikube**: `brew install minikube && minikube start`
- **kind**: `brew install kind && kind create cluster`

**Source code** — this folder must be a sibling of the `graph-olap` monorepo:
```
parent-dir/
├── graph-olap/                  ← source code (monorepo)
└── graph-olap-local-deploy/     ← this folder
```

If your layout differs, set `MONOREPO_ROOT`:
```bash
export MONOREPO_ROOT=/path/to/graph-olap
```

---

## Quick Start

```bash
# 1. Check prerequisites
make prereqs

# 2. Build all Docker images (~10-20 min first time)
make build

# 3. Deploy to local Kubernetes
make deploy

# 4. Verify
make status
curl http://localhost:30081/health

# 5. Open Jupyter Labs
open http://localhost:30081/jupyter/lab
```

---

## Credentials (Optional)

The demo notebooks work without any credentials — they use a local GCS emulator and synthetic data.

Credentials are only needed if you want to run the full export pipeline against a real Starburst Galaxy cluster and a real GCS bucket.

```bash
make secrets
```

This runs an interactive setup that prompts for each value with instructions showing exactly where to find it, then writes `.env` and `helm/values-local.yaml`.

Required for full pipeline:

| Credential | Where to get it |
|-----------|----------------|
| Starburst Galaxy URL + service account | Galaxy UI → Clusters → Connection info; Settings → Service Accounts |
| GCP service account key (JSON) | GCP Console → IAM → Service Accounts → Keys → Create JSON key |

---

## What Gets Deployed

| Component | Image | Description |
|-----------|-------|-------------|
| PostgreSQL | `postgres:15-alpine` (public) | Control-plane database |
| Extension Server | `ghcr.io/predictable-labs/extension-repo` (public) | Graph algorithm extensions |
| Control Plane | `control-plane:latest` (local build) | FastAPI REST API |
| Export Worker | `export-worker:latest` (local build) | Background export job processor |
| Jupyter Labs | `jupyter-labs:latest` (local build) | Jupyter environment with graph-olap SDK |
| fake-gcs-local | `fsouza/fake-gcs-server` (public) | Local GCS emulator for demo notebooks |
| nginx Ingress | installed via Helm (public) | Routes traffic into the cluster |

**Wrapper pods** (`falkordb-wrapper`, `ryugraph-wrapper`) are built locally and stored in Docker. The control-plane spawns them dynamically when graph instances are created — they are not pre-deployed. Multiple wrapper pods can run simultaneously (one per active instance).

---

## Common Commands

```bash
make build                      # Build all images
make build SVC=control-plane    # Build one image

make deploy                     # Deploy / re-deploy full stack
make status                     # Show pod and service health
make logs SVC=control-plane     # Tail logs
make logs SVC=export-worker
make logs SVC=jupyter-labs

make secrets                    # Interactive credential setup
make teardown                   # Delete everything (namespace)
```

```bash
# Watch pods live (requires: brew install watch)
watch kubectl get pods -n graph-olap-local
```

---

## Rebuilding After Code Changes

```bash
make build SVC=control-plane    # Rebuild one service
make deploy                     # Re-deploy (Helm detects the new image)
```

---

## Architecture

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

Export Worker (full pipeline only)
        ├── Starburst Galaxy — runs UNLOAD queries
        └── fake-gcs-local OR real GCS — writes Parquet files

Wrapper Pod (one per instance, spawned on demand)
        ├── FalkorDB or Ryugraph — in-memory graph database
        └── GCS (or fake-gcs-local) — downloads Parquet files on startup
```

The local deployment uses `fake-gcs-local` (a GCS emulator) by default. Demo notebooks upload Parquet files directly to the emulator — no real GCS required. When real GCP credentials are provided via `make secrets`, the emulator is disabled and real GCS is used.

---

## Troubleshooting

**Pods in CrashLoopBackOff:**
```bash
make logs SVC=control-plane
kubectl describe pod -n graph-olap-local -l app=graph-olap-control-plane
```

**Image not found (ErrImageNeverPull):**
```bash
make build          # Images were not built or need rebuilding
```

**Helm dependency errors:**
```bash
helm dependency update helm/charts/graph-olap
helm dependency update helm/charts/local-infra
```

**Port 30081 not responding after deploy:**
- Services may still be starting — wait 60 seconds and retry
- Check `make status` for pod readiness
- minikube: run `minikube service -n graph-olap-local graph-olap-control-plane --url`

**Reset everything:**
```bash
make teardown
make deploy
```

---

## Directory Structure

```
graph-olap-local-deploy/
├── Makefile                        # Entry point: make build / deploy / status / secrets
├── .env.example                    # Environment variable template
├── docker/
│   ├── control-plane.Dockerfile
│   ├── export-worker.Dockerfile
│   ├── falkordb-wrapper.Dockerfile
│   ├── ryugraph-wrapper.Dockerfile
│   └── jupyter-labs.Dockerfile     # Includes scipy, networkx, pyvis, pyarrow
├── helm/
│   ├── values-local.yaml           # Helm values (credentials injected here by make secrets)
│   └── charts/                     # Helm charts (graph-olap, local-infra, jupyter-labs)
├── k8s/
│   ├── control-plane-ingress.yaml
│   ├── control-plane-rbac.yaml     # RBAC for dynamic wrapper pod spawning
│   └── fake-gcs-server.yaml        # Local GCS emulator
├── notebooks/
│   ├── graph_olap_sdk.py           # Lightweight SDK used by all notebooks
│   ├── 00-cleanup.ipynb            # Instance management utility
│   ├── 01-movie-graph-demo.ipynb   # Movies + actors graph with PyVis
│   ├── 02-music-graph-demo.ipynb   # Artists + albums graph
│   ├── 03-ecommerce-graph-demo.ipynb # Products + customers graph
│   ├── 04-ipl-t20-graph-demo.ipynb # Cricket IPL graph with PyVis
│   └── 05-algorithms-demo.ipynb    # PageRank, Betweenness, Louvain, Shortest Path
├── scripts/
│   ├── prereqs.sh                  # Prerequisite checker
│   ├── build.sh                    # Docker build orchestration
│   ├── deploy.sh                   # Helm deploy orchestration
│   ├── teardown.sh                 # Cleanup
│   └── setup-secrets.sh            # Interactive credential setup (make secrets)
└── docs-local/                     # Local documentation site (http://localhost:30082)
```

---

## Image Build Notes

- All images use **public base images** — no internal registry needed
- `control-plane`, `falkordb-wrapper`, `ryugraph-wrapper`: Chainguard Python (`cgr.dev/chainguard/python`)
- `export-worker`: Chainguard Python
- `ryugraph-wrapper`: `python:3.12-slim` (ryugraph requires Python 3.12)
- `jupyter-labs`: `quay.io/jupyter/minimal-notebook:python-3.11`
- Builds run from the **monorepo root** as Docker context so all `packages/` are available
- On minikube/kind, the build script automatically loads images into the cluster
