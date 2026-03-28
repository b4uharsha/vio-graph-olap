# KEDA Autoscaling (Export Worker)

KEDA (Kubernetes Event-Driven Autoscaling) scales the export worker from zero to N based on pending export jobs. This means **zero cost when idle** — no export worker pods run until a mapping creates a snapshot.

## Architecture

```
Control Plane creates export job
    │
    ▼
KEDA ScaledObject watches job queue
    │
    ▼
KEDA scales export-worker 0 → 1 (or more)
    │
    ▼
Export Worker processes job:
    Starburst SQL → Parquet → GCS
    │
    ▼
Job completes → KEDA scales back to 0
```

## 1. Install KEDA

```bash
# Add KEDA Helm repo
helm repo add kedacore https://kedacore.github.io/charts
helm repo update

# Install KEDA in keda namespace
helm install keda kedacore/keda \
    --namespace keda \
    --create-namespace \
    --version 2.16.0
```

Verify:

```bash
kubectl get pods -n keda
# Should see: keda-operator, keda-metrics-apiserver
```

## 2. Configure ScaledObject

```yaml
# export-worker-scaledobject.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: export-worker
  namespace: graph-olap
spec:
  scaleTargetRef:
    name: export-worker
  minReplicaCount: 0          # Scale to zero when idle
  maxReplicaCount: 5          # Max concurrent exports
  cooldownPeriod: 60          # Seconds before scaling down
  pollingInterval: 5          # How often KEDA checks for work
  triggers:
    - type: postgresql
      metadata:
        connectionFromEnv: GRAPH_OLAP_DATABASE_URL
        query: "SELECT COUNT(*) FROM export_jobs WHERE status = 'pending'"
        targetQueryValue: "1"  # Scale up when >= 1 pending job
        activationTargetQueryValue: "1"
```

```bash
kubectl apply -f export-worker-scaledobject.yaml
```

## 3. Export Worker Deployment

The export worker deployment must allow scaling to zero:

```yaml
# export-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: export-worker
  namespace: graph-olap
spec:
  replicas: 0  # KEDA manages replica count
  selector:
    matchLabels:
      app: export-worker
  template:
    metadata:
      labels:
        app: export-worker
    spec:
      serviceAccountName: export-worker
      containers:
        - name: export-worker
          image: export-worker:latest  # Replace with your registry image
          env:
            - name: GRAPH_OLAP_DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: graph-olap-secrets
                  key: database-url
            - name: GRAPH_OLAP_GCS_BUCKET
              value: "<your-gcs-bucket>"
            - name: GRAPH_OLAP_STARBURST_URL
              value: "<your-starburst-url>"
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1"
```

## 4. Verify KEDA

```bash
# Check ScaledObject status
kubectl get scaledobject -n graph-olap

# Check current replicas (should be 0 when idle)
kubectl get deployment export-worker -n graph-olap

# Watch scaling in action (create a mapping to trigger)
kubectl get pods -n graph-olap -l app=export-worker -w
```

## How It Saves Cost

| State | Export Worker Pods | Cost |
|-------|-------------------|------|
| Idle (no exports) | 0 | $0 |
| 1 export running | 1 | ~$0.05/hr |
| 5 concurrent exports | 5 | ~$0.25/hr |
| Export complete | Back to 0 | $0 |
