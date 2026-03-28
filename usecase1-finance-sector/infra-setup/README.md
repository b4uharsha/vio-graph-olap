# Graph OLAP Platform - GKE Deployment Guide

Complete deployment guide for running the Graph OLAP platform on Google Kubernetes Engine (GKE).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GCP Project                                     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                           VPC Network                                   │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │                        GKE Cluster                               │   │ │
│  │  │                                                                  │   │ │
│  │  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │ │
│  │  │   │ Control Plane│  │Export Worker │  │   Wrapper Pods       │  │   │ │
│  │  │   │              │  │              │  │   (dynamic)          │  │   │ │
│  │  │   │ + Cloud SQL  │  │              │  │  ┌────┐ ┌────┐       │  │   │ │
│  │  │   │   Proxy      │  │              │  │  │ W1 │ │ W2 │ ...   │  │   │ │
│  │  │   └──────────────┘  └──────────────┘  │  └────┘ └────┘       │  │   │ │
│  │  │                                       └──────────────────────┘  │   │ │
│  │  │                                                                  │   │ │
│  │  │   ┌──────────────────────────────────────────────────────────┐  │   │ │
│  │  │   │            Internal Load Balancer (GCE)                   │  │   │ │
│  │  │   └──────────────────────────────────────────────────────────┘  │   │ │
│  │  │                                                                  │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  │                                │                                        │ │
│  │                                ▼                                        │ │
│  │                   ┌──────────────────────┐                              │ │
│  │                   │      Cloud SQL       │                              │ │
│  │                   │     (PostgreSQL)     │                              │ │
│  │                   └──────────────────────┘                              │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │  Cloud Storage   │  │  Artifact Reg.   │  │   Secret Mgr     │           │
│  │  (Snapshots)     │  │  (Images)        │  │  (Credentials)   │           │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

Before starting, ensure you have:

- GCP Project with billing enabled
- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- `kubectl` installed (`gcloud components install kubectl`)
- `helm` v3 installed
- Docker (for building images)
- Access to a container registry (GCR, Artifact Registry, or private)
- Starburst Galaxy account (or other Trino-compatible engine)

## Deployment Order

Follow these guides **in order** — each step builds on the previous:

### Phase 1: Infrastructure

| # | Guide | What You Get |
|---|-------|-------------|
| 00 | [End-to-End Flow](00-end-to-end-flow.md) | **Read first** — understand the full architecture |
| 01 | [GCP Service Accounts](01-gcp-service-accounts.md) | IAM service accounts + Workload Identity bindings |
| 02 | [GKE Cluster Setup](02-gke-cluster-setup.md) | Running Kubernetes cluster with node pools |
| 03 | [Kubernetes Resources](03-kubernetes-resources.md) | Namespace, RBAC, secrets, ConfigMaps |

### Phase 2: Core Services

| # | Guide | What You Get |
|---|-------|-------------|
| 04 | [Control Plane Deployment](04-control-plane-deployment.md) | Running control plane (FastAPI + PostgreSQL) |
| 05 | [Wrapper Pod Architecture](05-wrapper-pod-architecture.md) | Understanding of dynamic wrapper pod lifecycle |
| 06 | [Internal Load Balancer](06-internal-load-balancer.md) | GCE internal ingress + NEG configuration |
| 06a | [Wrapper Proxy](06a-wrapper-proxy.md) | NGINX reverse proxy for wrapper pod routing |
| 06b | [KEDA Autoscaling](06b-keda-autoscaling.md) | Export worker scales 0 to N based on job queue |
| 06c | [Corporate Proxy](06c-corporate-proxy.md) | Proxy config for enterprise/air-gapped networks |

### Phase 3: Connectivity & Auth

| # | Guide | What You Get |
|---|-------|-------------|
| 07 | [Cloud SQL Proxy](07-cloud-sql-proxy.md) | Database connectivity via Cloud SQL Auth Proxy |
| 08 | [JWT Authentication](08-jwt-authentication.md) | OAuth2/OIDC authentication (Auth0 / oauth2-proxy) |
| 11 | [Starburst Connectivity](11-starburst-connectivity.md) | Starburst/Trino connection, auth, roles, exports |

### Phase 4: Validate & Ship

| # | Guide | What You Get |
|---|-------|-------------|
| 09 | [Testing & Validation](09-testing-validation.md) | API + SDK one-go tests, full E2E suite |
| 10 | [Smoke Tests](10-smoke-tests-curl.md) | Quick curl commands to verify each component |
| 12 | [Deployment Notes](12-deployment-notes.md) | Required vs optional components, troubleshooting |

## Quick Start

### Prerequisites

- GCP Project with billing enabled
- `gcloud` CLI installed and authenticated
- `kubectl` installed
- `helm` v3 installed

### 1. Set Environment Variables

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export CLUSTER_NAME="graph-olap-cluster"
export NAMESPACE="graph-olap"
```

### 2. Create Service Accounts

```bash
# See 01-gcp-service-accounts.md for full details
gcloud iam service-accounts create control-plane-sa \
    --display-name="Graph OLAP Control Plane"
```

### 3. Create GKE Cluster

```bash
# See 02-gke-cluster-setup.md for full details
gcloud container clusters create $CLUSTER_NAME \
    --region=$REGION \
    --workload-pool="${PROJECT_ID}.svc.id.goog"
```

### 4. Deploy Platform

```bash
# Apply Kubernetes resources
kubectl apply -f namespace.yaml
kubectl apply -f rbac.yaml
kubectl apply -f secrets.yaml
kubectl apply -f configmaps.yaml
kubectl apply -f deployments/

# Verify
kubectl get pods -n graph-olap
```

### 5. Test Deployment

```bash
# Health check
kubectl run test --rm -it --image=curlimages/curl -- \
    curl -s http://control-plane.graph-olap.svc.cluster.local:8080/health
```

## Key Components

### Control Plane

- FastAPI application managing instance lifecycle
- Connects to Cloud SQL via Auth Proxy sidecar
- Creates/deletes wrapper pods dynamically
- Handles JWT authentication

### Wrapper Pods

- Ephemeral pods serving graph queries
- Load data from GCS on startup
- Two types: Ryugraph (high-performance) and FalkorDB (Redis-based)
- Accessed via in-cluster service DNS

### Export Worker

- Background job processor
- Exports data from Starburst to GCS
- Creates snapshots for wrapper consumption

## Authentication Modes

| Mode | Header | Use Case |
|------|--------|----------|
| External | `Authorization: Bearer <JWT>` | API Gateway |
| In-Cluster | `X-Username`, `X-User-Role` | Internal services |

## Networking

- **Internal Load Balancer**: GCE internal for VPC-only access
- **Wrapper Access**: In-cluster service DNS (no wildcard DNS required)
- **Container-Native LB**: NEG-based direct pod routing

## Security Features

- Workload Identity (no service account keys)
- Cloud SQL Auth Proxy (encrypted connections)
- JWT validation via JWKS
- RBAC for pod management permissions
- Private cluster (no public IPs)

## Monitoring

- Structured JSON logging
- Health endpoints: `/health`, `/ready`
- Kubernetes probes: startup, liveness, readiness
- Pod labels for filtering and cleanup

## Troubleshooting

```bash
# Check all resources
kubectl get all -n graph-olap

# Check events
kubectl get events -n graph-olap --sort-by='.lastTimestamp'

# Check logs
kubectl logs -n graph-olap -l app=control-plane -c control-plane

# Debug pod
kubectl describe pod -n graph-olap <pod-name>
```

## Support

For issues and feature requests, please contact the platform team.
