# Use Case 1: Finance Sector — Graph Analytics on Banking Data

End-to-end deployment and testing of the Graph OLAP platform for a finance sector use case.

## Overview

This use case demonstrates how a financial institution can use Graph OLAP to:
- Model **Customer -> Account -> Transaction** relationships as a graph
- Map relational data from Starburst/Trino into graph nodes and edges
- Run Cypher queries and graph algorithms for fraud detection, network analysis, and KYC
- Integrate via Python SDK or raw REST API

## Repository Structure

```
usecase1-finance-sector/
├── README.md                  # This file — architecture, data model, results
├── config/
│   └── env.example            # Environment template — fill in your values
├── scripts/
│   ├── api-onego.md           # One-cell API test (httpx, no SDK needed)
│   ├── sdk-onego.md           # One-cell SDK test (graph-olap-sdk)
│   └── run-all-e2e.md         # Run all 17 test notebooks via papermill
└── infra-setup/               # 14 GKE deployment guides
    ├── 00-end-to-end-flow.md
    ├── 01-gcp-service-accounts.md
    ├── 02-gke-cluster-setup.md
    ├── 03-kubernetes-resources.md
    ├── 04-control-plane-deployment.md
    ├── 05-wrapper-pod-architecture.md
    ├── 06-internal-load-balancer.md
    ├── 07-cloud-sql-proxy.md
    ├── 08-jwt-authentication.md
    ├── 09-testing-validation.md
    ├── 10-smoke-tests-curl.md
    ├── 11-starburst-connectivity.md
    └── 12-deployment-notes.md
```

## Platform Packages Used

All packages come from [`graph-packages/`](../graph-packages/) — the standard platform.
No custom code required for this use case, only configuration.

| Package | Version | Purpose |
|---------|---------|---------|
| `control-plane` | 0.1.0 | FastAPI control plane — mappings, instances, schema, RBAC |
| `graph-olap-sdk` | 0.5.0 | Python SDK — `GraphOLAPClient`, `notebook.test()`, `TestPersona` |
| `graph-olap-schemas` | 1.0.1 | Shared Pydantic models |
| `falkordb-wrapper` | 0.1.0 | FalkorDB graph database wrapper pod |
| `ryugraph-wrapper` | 0.1.0 | Ryugraph graph database wrapper pod |
| `export-worker` | 0.1.0 | Starburst -> GCS Parquet export worker (KEDA-scaled) |
| `lib-auth` | 1.0.0 | JWT authentication utilities |

## Configuration

Copy and fill in your environment values:

```bash
cp config/env.example config/.env
```

Key variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `GRAPH_OLAP_API_URL` | Control plane endpoint | `https://control-plane.your-domain.com` |
| `GRAPH_OLAP_USE_CASE_ID` | Use case identifier | `uc_finance_dev` |
| `STARBURST_CATALOG` | Starburst catalog | `your-data-catalog` |
| `STARBURST_SCHEMA` | Schema with banking tables | `banking_data_views` |
| `https_proxy` | Corporate proxy (if applicable) | `http://proxy:3128` |

## Data Model

```
Customer ──HAS_ACCOUNT──> Account ──HAS_TRANSACTION──> Transaction
```

### Tables

| Table | Description | Keys | Rows |
|-------|-------------|------|------|
| customer_demographics | Customer master data | customer_id | ~6 |
| account_master | Account dimension | customer_id, account_no | ~2 |
| account_daily_history | Account daily snapshots | customer_id, account_no | ~540 |
| transaction_monthly | Monthly transaction history | customer_id, account_no | ~499 |
| transaction_daily | Daily transaction history | customer_id, account_no | ~612 |

**Total: ~1,659 rows** (test dataset)

## Quick Start

### 1. Deploy the Platform

Follow the guides in [infra-setup/](infra-setup/) to deploy on GKE:

```
01 → GCP service accounts
02 → GKE cluster setup
03 → Kubernetes resources
04 → Control plane deployment
05 → Wrapper pod architecture
...
```

### 2. API One-Go Test

Single Jupyter cell — tests the full lifecycle using raw HTTP (no SDK needed):

```
Health check → Create mapping → Create instance → Query graph → Visualize → Cleanup
```

See: [scripts/api-onego.md](scripts/api-onego.md)

### 3. SDK One-Go Test

Single Jupyter cell — same test using the Python SDK:

```python
client = GraphOLAPClient(api_url=API_URL, ...)
mapping = client.mappings.create(...)
instance = client.instances.create_and_wait(...)
conn = client.instances.connect(instance.id)
result = conn.query("MATCH (c:Customer) RETURN c")
```

See: [scripts/sdk-onego.md](scripts/sdk-onego.md)

### 4. Full E2E Test Suite

Run all 17 test notebooks sequentially via papermill:

See: [scripts/run-all-e2e.md](scripts/run-all-e2e.md)

## E2E Test Results

All 17 notebooks passed on the deployed platform:

| # | Notebook | What it Tests | Status |
|---|----------|---------------|--------|
| 02 | Health Checks | Service health, persona verification | PASS |
| 03 | Managing Resources | Mapping/Snapshot/Instance CRUD | PASS |
| 04 | Cypher Basics | Query execution, parameters, schema | PASS |
| 05 | Exploring Schemas | Catalog/table/column browsing | PASS |
| 06 | Graph Algorithms | Centrality, community detection, paths | PASS |
| 07 | End-to-End Workflows | Full mapping->instance->query pipelines | PASS |
| 08 | Quick Start | One-call quick_start() workflow | PASS |
| 09 | Handling Errors | Error types, edge cases, mutations | PASS |
| 10 | Bookmarks | Favorites CRUD, filtering, cascade | PASS |
| 11 | Instance Lifecycle | TTL, health, progress, custom config | PASS |
| 13 | Advanced Mappings | Copy, hierarchy, multi-version | PASS |
| 14 | Version Diffing | Add/modify/remove diff, HTML render | PASS |
| 15 | Background Jobs | Scheduler, metrics, job execution | PASS |
| 16 | FalkorDB | Full API coverage, 10 test categories | PASS |
| 17 | Authorization | RBAC — analyst/admin/ops boundaries | PASS |
| 18 | Admin Operations | Bulk delete with safety validations | PASS |
| 19 | Ops Configuration | Config, cluster, job management | PASS |

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ANALYST LAYER                               │
│                                                                     │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐     │
│   │   Jupyter     │  │   Python     │  │   REST API Client    │     │
│   │   Notebook    │  │   SDK        │  │   (httpx / curl)     │     │
│   └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘     │
│          │                  │                      │                 │
└──────────┼──────────────────┼──────────────────────┼─────────────────┘
           │                  │                      │
           ▼                  ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PLATFORM LAYER (Kubernetes)                     │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    NGINX Ingress                             │   │
│   │              (routing + TLS + proxy)                         │   │
│   └──────────────────────┬──────────────────────────────────────┘   │
│                          │                                          │
│   ┌──────────────────────▼──────────────────────────────────────┐   │
│   │                 Control Plane (FastAPI)                      │   │
│   │                                                             │   │
│   │  /api/mappings   - Define node/edge SQL mappings            │   │
│   │  /api/instances  - Create/manage graph instances            │   │
│   │  /api/schema     - Browse data warehouse metadata           │   │
│   │  /wrapper/{slug} - Proxy to graph wrapper pods              │   │
│   │                                                             │   │
│   │  Auth: JWT/OIDC  |  RBAC: analyst / admin / ops roles       │   │
│   └────┬─────────────────────────────┬──────────────────────────┘   │
│        │                             │                              │
│        ▼                             ▼                              │
│   ┌────────────────┐    ┌────────────────────────────────────┐      │
│   │  Cloud SQL     │    │     Export Worker (KEDA)            │      │
│   │  (PostgreSQL)  │    │                                    │      │
│   │                │    │  1. Receives export job             │      │
│   │  - mappings    │    │  2. Queries Starburst/Trino        │      │
│   │  - snapshots   │    │  3. Writes Parquet to GCS          │      │
│   │  - instances   │    │  4. Scales to zero when idle       │      │
│   │  - jobs        │    │                                    │      │
│   └────────────────┘    └────────────────┬───────────────────┘      │
│                                          │                          │
└──────────────────────────────────────────┼──────────────────────────┘
                                           │
┌──────────────────────────────────────────┼──────────────────────────┐
│                     DATA LAYER                                      │
│                                          │                          │
│   ┌────────────────────┐    ┌────────────▼─────────────────────┐    │
│   │  Starburst Galaxy  │    │     Cloud Storage (GCS)          │    │
│   │  (Trino)           │    │                                  │    │
│   │                    │    │  /snapshots/                      │    │
│   │  SQL Catalogs:     │    │    ├── mapping_123/               │    │
│   │  - Banking data    │    │    │   ├── nodes_customer.parquet │    │
│   │  - Views / Tables  │    │    │   ├── nodes_account.parquet  │    │
│   │                    │    │    │   └── edges_has_acct.parquet  │    │
│   │  UNLOAD to Parquet │    │    └── ...                        │    │
│   └────────────────────┘    └────────────────┬─────────────────┘    │
│                                              │                      │
└──────────────────────────────────────────────┼──────────────────────┘
                                               │
┌──────────────────────────────────────────────┼──────────────────────┐
│                     GRAPH LAYER (per-analyst pods)                   │
│                                              │                      │
│   ┌──────────────────────────────────────────▼─────────────────┐    │
│   │              Wrapper Pod (FalkorDB)                         │    │
│   │                                                            │    │
│   │  1. Loads Parquet from GCS                                 │    │
│   │  2. Builds in-memory graph                                 │    │
│   │  3. Serves Cypher queries (~2ms)                           │    │
│   │  4. Runs graph algorithms (PageRank, centrality, etc.)     │    │
│   │  5. Auto-deletes after TTL                                 │    │
│   │                                                            │    │
│   │  Endpoints:                                                │    │
│   │    /health  /ready  /query  /schema  /algo/*               │    │
│   │                                                            │    │
│   │  Isolation: one pod per analyst per instance                │    │
│   └────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Step 1: DEFINE
  Analyst defines a mapping via SDK or API:
    - Node: Customer  (SELECT customer_id, name FROM customer_demographics)
    - Node: Account   (SELECT account_no, customer_id FROM account_master)
    - Edge: HAS_ACCOUNT (Customer.customer_id -> Account.customer_id)

Step 2: EXPORT
  Control Plane triggers Export Worker:
    Starburst ──SQL──▶ Query Results ──Parquet──▶ GCS Bucket

Step 3: LAUNCH
  Control Plane creates Wrapper Pod:
    GCS Parquet ──load──▶ FalkorDB In-Memory Graph

Step 4: QUERY
  Analyst connects and runs Cypher:
    MATCH (c:Customer)-[:HAS_ACCOUNT]->(a:Account)
    WHERE c.name = "John"
    RETURN a
    ──▶ Results in ~2ms

Step 5: CLEANUP
  Instance auto-deletes after TTL or manual termination.
  Wrapper pod removed. GCS snapshot retained for re-launch.
```

### Network Flow (Analyst to Pod)

```
Analyst (Jupyter / SDK / curl)
    │
    │  HTTPS (port 443)
    ▼
Corporate Proxy (if applicable)
    │
    │  HTTPS
    ▼
NGINX Ingress (Kubernetes)
    │
    ├──▶ /api/*        ──▶ Control Plane Service (ClusterIP)
    │                        │
    │                        ├──▶ Cloud SQL (PostgreSQL via Cloud SQL Proxy)
    │                        └──▶ Export Worker (KEDA-managed, scales 0→N)
    │                                  │
    │                                  └──▶ Starburst Galaxy (external, HTTPS)
    │
    └──▶ /wrapper/*    ──▶ Wrapper Pod Service (ClusterIP, per-instance)
                              │
                              └──▶ FalkorDB (in-pod, port 6379)
                                     │
                                     └──▶ GCS (Parquet load on startup)
```

## Infrastructure Setup

For step-by-step deployment guides, see [infra-setup/](infra-setup/):

**Phase 1: Infrastructure**

| Guide | Topic |
|-------|-------|
| [00 - End-to-End Flow](infra-setup/00-end-to-end-flow.md) | Read first — full architecture overview |
| [01 - GCP Service Accounts](infra-setup/01-gcp-service-accounts.md) | IAM + Workload Identity |
| [02 - GKE Cluster Setup](infra-setup/02-gke-cluster-setup.md) | Kubernetes cluster + node pools |
| [03 - Kubernetes Resources](infra-setup/03-kubernetes-resources.md) | Namespace, RBAC, secrets |

**Phase 2: Core Services**

| Guide | Topic |
|-------|-------|
| [04 - Control Plane](infra-setup/04-control-plane-deployment.md) | FastAPI control plane + PostgreSQL |
| [05 - Wrapper Pods](infra-setup/05-wrapper-pod-architecture.md) | Dynamic wrapper pod lifecycle |
| [06 - Load Balancer](infra-setup/06-internal-load-balancer.md) | GCE internal ingress + NEG |
| [06a - Wrapper Proxy](infra-setup/06a-wrapper-proxy.md) | NGINX reverse proxy for wrapper routing |
| [06b - KEDA Autoscaling](infra-setup/06b-keda-autoscaling.md) | Export worker scales 0→N |
| [06c - Corporate Proxy](infra-setup/06c-corporate-proxy.md) | Enterprise proxy configuration |

**Phase 3: Connectivity & Auth**

| Guide | Topic |
|-------|-------|
| [07 - Cloud SQL Proxy](infra-setup/07-cloud-sql-proxy.md) | Database via Cloud SQL Auth Proxy |
| [08 - JWT Authentication](infra-setup/08-jwt-authentication.md) | OAuth2/OIDC + oauth2-proxy |
| [11 - Starburst](infra-setup/11-starburst-connectivity.md) | Trino connection, auth, exports |

**Phase 4: Validate**

| Guide | Topic |
|-------|-------|
| [09 - Testing](infra-setup/09-testing-validation.md) | API + SDK one-go tests, full E2E |
| [10 - Smoke Tests](infra-setup/10-smoke-tests-curl.md) | Quick curl commands per component |
| [12 - Deployment Notes](infra-setup/12-deployment-notes.md) | Troubleshooting + notes |
