# Architecture

How the Graph OLAP platform is built — all services, their roles, and how they connect.

---

## System Diagram

```text
http://localhost:30081
        │
        ▼
nginx Ingress Controller (NodePort 30081)
        │
        ├── /api/*       → Control Plane (FastAPI)
        ├── /jupyter     → Jupyter Labs
        ├── /health      → Control Plane health
        └── /{instance}/ → Wrapper pods (spawned per graph instance)

Control Plane
        ├── PostgreSQL      — mappings, snapshots, instances, users
        ├── Extension Server — graph algorithm extensions
        └── Kubernetes API  — spawns/deletes wrapper pods on demand

Export Worker
        ├── Starburst Galaxy — runs UNLOAD queries
        └── GCS             — writes Parquet files

Wrapper Pod (one per instance)
        ├── FalkorDB or KuzuDB — in-memory graph database
        └── GCS               — downloads Parquet on startup
```

---

## Platform Services

<div class="service-grid">

  <div class="service-card">
    <span class="service-icon">🧠</span>
    <h4>Control Plane</h4>
    <p>FastAPI REST API — the brain. Manages mappings, instances, users, and orchestrates everything via the Kubernetes API.</p>
    <code>control-plane:latest</code>
  </div>

  <div class="service-card">
    <span class="service-icon">📦</span>
    <h4>Export Worker</h4>
    <p>Polls for export jobs, connects to Starburst Galaxy, runs UNLOAD queries, and writes Parquet files to GCS.</p>
    <code>export-worker:latest</code>
  </div>

  <div class="service-card">
    <span class="service-icon">⚡</span>
    <h4>FalkorDB Wrapper</h4>
    <p>Graph pod using FalkorDB (Redis-based in-memory graph). Fast lookups, low latency. Spawned per analyst instance.</p>
    <code>falkordb-wrapper:local</code>
  </div>

  <div class="service-card">
    <span class="service-icon">🔬</span>
    <h4>Ryugraph Wrapper</h4>
    <p>Graph pod using KuzuDB (columnar graph engine). Better for large analytical scans and algorithm workloads.</p>
    <code>ryugraph-wrapper:local</code>
  </div>

  <div class="service-card">
    <span class="service-icon">📓</span>
    <h4>Jupyter Labs</h4>
    <p>Pre-configured notebook environment with the Graph OLAP Python SDK installed. Six demo notebooks pre-loaded — no credentials needed.</p>
    <code>jupyter-labs:latest</code>
  </div>

  <div class="service-card">
    <span class="service-icon">🗄️</span>
    <h4>PostgreSQL</h4>
    <p>Control plane database — stores mappings, snapshots, instances, and users. Standard postgres:15-alpine.</p>
    <code>postgres:15-alpine</code>
  </div>

  <div class="service-card">
    <span class="service-icon">🔧</span>
    <h4>Extension Server</h4>
    <p>Provides graph algorithm extensions — PageRank, BFS, community detection — for Ryugraph/KuzuDB instances.</p>
    <code>extension-repo</code>
  </div>

  <div class="service-card">
    <span class="service-icon">☁️</span>
    <h4>Fake GCS Server</h4>
    <p>Local GCS emulator used by the export worker during local development. Not needed if using a real GCS bucket.</p>
    <code>fake-gcs-server</code>
  </div>

</div>

---

## Why Per-Instance Pods?

!!! success "No contention"
    One analyst's heavy traversal query cannot slow down another's. Complete compute isolation at the pod level.

!!! success "Snapshot isolation"
    Each instance is a point-in-time export of the warehouse. No shared mutable state between analysts.

!!! success "Engine choice per instance"
    Choose **FalkorDB** for low-latency lookups, or **KuzuDB** for large analytical scans — decided per instance.

!!! success "Zero idle cost"
    Pods are ephemeral. They expire after a configured TTL or period of inactivity.

---

## FalkorDB vs KuzuDB — Which to Pick?

| | FalkorDB | KuzuDB (Ryugraph) |
| --- | --- | --- |
| Engine type | Redis-based in-memory graph | Columnar graph DB |
| Best for | Low-latency point lookups, small-medium graphs | Large analytical scans, graph algorithms |
| PageRank / BFS | Via extension server | Native |
| Memory model | Node/edge store in Redis structures | Column-oriented |
| Choose when | You need fast traversal with minimal overhead | You need graph algorithms at scale |

---

## Local vs Production

This local deployment is a **faithful replica** of the production architecture — same services, same APIs, same Helm charts.

| | Local | Production |
| --- | --- | --- |
| Auth | `X-Username` / `X-User-Role` headers | JWT via Auth0 / OAuth2 Proxy |
| Ingress | NodePort 30081 | Cloud load balancer + custom domain |
| GCS | All services → fake-gcs-local (in-cluster emulator, auto-configured). Run `make secrets` with a real SA key to switch to real GCS. | Shared managed GCS bucket |
| Kubernetes | OrbStack / minikube / kind | GKE / EKS / AKS |
| Starburst | Optional — bypass via direct Parquet | Required for full export pipeline |

---

## Data Flow Diagram

![Data Flow Architecture](assets/diagrams/data-flow-architecture.svg)
