# Kubernetes Resources Configuration

This guide covers namespace, RBAC, secrets, and ConfigMap setup for the Graph OLAP platform.

## 1. Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: graph-olap
  labels:
    name: graph-olap
    environment: production
```

```bash
kubectl apply -f namespace.yaml
```

## 2. Service Accounts

```yaml
# service-accounts.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: control-plane
  namespace: graph-olap
  annotations:
    iam.gke.io/gcp-service-account: control-plane-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: wrapper
  namespace: graph-olap
  annotations:
    iam.gke.io/gcp-service-account: wrapper-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: export-worker
  namespace: graph-olap
  annotations:
    iam.gke.io/gcp-service-account: export-worker-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## 3. RBAC - Control Plane Pod Management

The control plane needs permissions to create/delete wrapper pods dynamically:

```yaml
# rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: control-plane-role
  namespace: graph-olap
rules:
  # Pod management for wrapper instances
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch", "create", "delete"]
  # Service management for wrapper routing
  - apiGroups: [""]
    resources: ["services"]
    verbs: ["get", "list", "watch", "create", "delete"]
  # Ingress management for external access
  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses"]
    verbs: ["get", "list", "watch", "create", "delete"]
  # Pod status for health checks
  - apiGroups: [""]
    resources: ["pods/status"]
    verbs: ["get"]
  # Pod logs for debugging
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: control-plane-rolebinding
  namespace: graph-olap
subjects:
  - kind: ServiceAccount
    name: control-plane
    namespace: graph-olap
roleRef:
  kind: Role
  name: control-plane-role
  apiGroup: rbac.authorization.k8s.io
```

## 4. Secrets

### Database Connection Secret

```bash
# Create database URL secret
kubectl create secret generic control-plane-secrets \
    --namespace=graph-olap \
    --from-literal=database-url="postgresql://user:password@127.0.0.1:5432/your_database" \
    --from-literal=api-internal-token="$(openssl rand -hex 32)"
```

Or declaratively:

```yaml
# secrets.yaml (use external secrets manager in production)
apiVersion: v1
kind: Secret
metadata:
  name: control-plane-secrets
  namespace: graph-olap
type: Opaque
stringData:
  database-url: "postgresql://user:password@127.0.0.1:5432/your_database"
  api-internal-token: "your-internal-api-token"
---
apiVersion: v1
kind: Secret
metadata:
  name: export-worker-secrets
  namespace: graph-olap
type: Opaque
stringData:
  STARBURST_PASSWORD: "your-starburst-password"
  GRAPH_OLAP_INTERNAL_API_KEY: "your-internal-api-token"
```

### Starburst Credentials

```bash
kubectl create secret generic starburst-credentials \
    --namespace=graph-olap \
    --from-literal=STARBURST_USER="service-account@your-org/accountadmin" \
    --from-literal=STARBURST_PASSWORD="your-password"
```

## 5. ConfigMaps

### Control Plane Configuration

```yaml
# control-plane-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: control-plane-config
  namespace: graph-olap
data:
  # Server
  HOST: "0.0.0.0"
  PORT: "8080"
  DEBUG: "false"
  ENVIRONMENT: "production"

  # GCP
  GCP_PROJECT: "your-project-id"
  GCS_BUCKET: "your-gcs-bucket"

  # Kubernetes
  K8S_NAMESPACE: "graph-olap"
  K8S_IN_CLUSTER: "true"

  # Wrapper configuration
  WRAPPER_IMAGE: "gcr.io/your-project/ryugraph-wrapper:v1.0.0"
  FALKORDB_WRAPPER_IMAGE: "gcr.io/your-project/falkordb-wrapper:v1.0.0"
  WRAPPER_IMAGE_PULL_POLICY: "IfNotPresent"
  WRAPPER_SERVICE_ACCOUNT: "wrapper"
  WRAPPER_EXTERNAL_BASE_URL: "https://graph-olap.your-domain.com"
  WRAPPER_INGRESS_CLASS: "gce-internal"

  # Starburst
  STARBURST_URL: "https://your-cluster.trino.galaxy.starburst.io:443"
  STARBURST_CATALOG: "your_catalog"
  STARBURST_TIMEOUT_SECONDS: "120"

  # Extension Server
  EXTENSION_SERVER_URL: "http://extension-server:8080"

  # Resource defaults
  RYUGRAPH_MEMORY_REQUEST: "2Gi"
  RYUGRAPH_MEMORY_LIMIT: "4Gi"
  RYUGRAPH_CPU_REQUEST: "1"
  RYUGRAPH_CPU_LIMIT: "2"

  FALKORDB_MEMORY_REQUEST: "2Gi"
  FALKORDB_MEMORY_LIMIT: "4Gi"
  FALKORDB_CPU_REQUEST: "500m"
  FALKORDB_CPU_LIMIT: "1"

  # Jobs
  RECONCILIATION_INTERVAL_SECONDS: "30"
  LIFECYCLE_INTERVAL_SECONDS: "30"

  # JWT Authentication
  JWT_EMAIL_CLAIM_URL: "https://api.your-domain.com/email"
  JWT_ROLES_CLAIM_URL: "https://api.your-domain.com/roles"
  AUTH0_JWKS_URL: "https://your-tenant.auth0.com/.well-known/jwks.json"
  AUTH0_AUDIENCE: "https://api.your-domain.com"
  AUTH0_ISSUER: "https://your-tenant.auth0.com/"
```

### Export Worker Configuration

```yaml
# export-worker-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: export-worker-config
  namespace: graph-olap
data:
  GCP_PROJECT: "your-project-id"
  GCS_BUCKET: "your-gcs-bucket"

  STARBURST_URL: "https://your-cluster.trino.galaxy.starburst.io:443"
  STARBURST_CATALOG: "your_catalog"
  STARBURST_SCHEMA: "your_schema"
  STARBURST_REQUEST_TIMEOUT_SECONDS: "30"
  STARBURST_CLIENT_TAGS: "graph-olap-export"
  STARBURST_SOURCE: "graph-olap-export-worker"

  CONTROL_PLANE_URL: "http://control-plane:8080"
  CONTROL_PLANE_TIMEOUT_SECONDS: "30"

  WORKER_POLL_INTERVAL_SECONDS: "5"
  WORKER_EMPTY_POLL_BACKOFF_SECONDS: "10"
  WORKER_CLAIM_LIMIT: "10"

  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
```

## 6. Apply All Resources

```bash
# Apply in order
kubectl apply -f namespace.yaml
kubectl apply -f service-accounts.yaml
kubectl apply -f rbac.yaml
kubectl apply -f secrets.yaml
kubectl apply -f control-plane-config.yaml
kubectl apply -f export-worker-config.yaml
```

## 7. Verify Resources

```bash
# Check namespace
kubectl get namespace graph-olap

# Check service accounts
kubectl get serviceaccounts -n graph-olap

# Check RBAC
kubectl get roles,rolebindings -n graph-olap

# Check secrets (names only)
kubectl get secrets -n graph-olap

# Check configmaps
kubectl get configmaps -n graph-olap
```

## Using External Secrets Manager (Recommended)

For production, use GCP Secret Manager with External Secrets Operator:

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: control-plane-secrets
  namespace: graph-olap
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: gcp-secret-manager
  target:
    name: control-plane-secrets
    creationPolicy: Owner
  data:
    - secretKey: database-url
      remoteRef:
        key: graph-olap-database-url
    - secretKey: api-internal-token
      remoteRef:
        key: graph-olap-internal-token
```

## Next Steps

- [04-control-plane-deployment.md](04-control-plane-deployment.md) - Control Plane deployment
