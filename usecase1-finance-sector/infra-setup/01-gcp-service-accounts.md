# GCP Service Accounts Setup

This guide covers the service account configuration required for deploying the Graph OLAP platform on GKE.

## Overview

The platform requires multiple service accounts with specific IAM roles:

| Service Account | Purpose | Key Permissions |
|----------------|---------|-----------------|
| `gke-node-sa` | GKE node pool identity | Container Registry, Logging, Monitoring |
| `control-plane-sa` | Control Plane workload | GCS read/write, Cloud SQL client |
| `wrapper-sa` | Wrapper pods workload | GCS read-only |
| `export-worker-sa` | Export worker workload | GCS read/write |

## 1. Set Environment Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export NAMESPACE="graph-olap"
```

## 2. Create Service Accounts

```bash
# GKE Node Service Account
gcloud iam service-accounts create gke-node-sa \
    --display-name="GKE Node Service Account" \
    --project=$PROJECT_ID

# Control Plane Service Account
gcloud iam service-accounts create control-plane-sa \
    --display-name="Graph OLAP Control Plane" \
    --project=$PROJECT_ID

# Wrapper Pods Service Account
gcloud iam service-accounts create wrapper-sa \
    --display-name="Graph OLAP Wrapper Pods" \
    --project=$PROJECT_ID

# Export Worker Service Account
gcloud iam service-accounts create export-worker-sa \
    --display-name="Graph OLAP Export Worker" \
    --project=$PROJECT_ID
```

## 3. Assign IAM Roles

### GKE Node Service Account

```bash
# Required for pulling images from Container Registry / Artifact Registry
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:gke-node-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.reader"

# Logging and monitoring
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:gke-node-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:gke-node-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:gke-node-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/monitoring.viewer"
```

### Control Plane Service Account

```bash
# GCS access for snapshots
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:control-plane-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Cloud SQL client (for Cloud SQL Auth Proxy)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:control-plane-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"
```

### Wrapper Service Account

```bash
# Read-only GCS access for loading snapshot data
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:wrapper-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
```

### Export Worker Service Account

```bash
# GCS access for writing export results
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:export-worker-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

## 4. Configure Workload Identity

Workload Identity allows Kubernetes service accounts to act as GCP service accounts without managing keys.

### Enable Workload Identity on Cluster

```bash
gcloud container clusters update YOUR_CLUSTER_NAME \
    --region=$REGION \
    --workload-pool="${PROJECT_ID}.svc.id.goog"
```

### Bind Kubernetes Service Accounts to GCP Service Accounts

```bash
# Control Plane
gcloud iam service-accounts add-iam-policy-binding \
    control-plane-sa@${PROJECT_ID}.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[${NAMESPACE}/control-plane]"

# Wrapper pods
gcloud iam service-accounts add-iam-policy-binding \
    wrapper-sa@${PROJECT_ID}.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[${NAMESPACE}/wrapper]"

# Export Worker
gcloud iam service-accounts add-iam-policy-binding \
    export-worker-sa@${PROJECT_ID}.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[${NAMESPACE}/export-worker]"
```

## 5. Create Kubernetes Service Accounts with Annotations

```yaml
# control-plane-sa.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: control-plane
  namespace: graph-olap
  annotations:
    iam.gke.io/gcp-service-account: control-plane-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
---
# wrapper-sa.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: wrapper
  namespace: graph-olap
  annotations:
    iam.gke.io/gcp-service-account: wrapper-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
---
# export-worker-sa.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: export-worker
  namespace: graph-olap
  annotations:
    iam.gke.io/gcp-service-account: export-worker-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

Apply:

```bash
kubectl apply -f control-plane-sa.yaml
kubectl apply -f wrapper-sa.yaml
kubectl apply -f export-worker-sa.yaml
```

## 6. Verify Workload Identity

```bash
# Test from a pod using the service account
kubectl run test-wi --rm -it \
    --image=google/cloud-sdk:slim \
    --serviceaccount=control-plane \
    --namespace=$NAMESPACE \
    -- gcloud auth list

# Expected output should show the GCP service account
```

## Next Steps

- [02-gke-cluster-setup.md](02-gke-cluster-setup.md) - GKE cluster configuration
