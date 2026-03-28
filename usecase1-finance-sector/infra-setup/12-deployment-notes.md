# Deployment Notes and Optional Components

This document clarifies which components are required vs optional, and documents key configuration decisions for GKE deployment.

## Component Requirements Summary

| Component | Required | Notes |
|-----------|----------|-------|
| Control Plane | **Yes** | Core API service |
| Cloud SQL (PostgreSQL) | **Yes** | State persistence |
| Cloud SQL Proxy | **Yes** | Secure DB connectivity |
| Export Worker | **Yes** | Data export to GCS |
| GCS Bucket | **Yes** | Snapshot storage |
| Starburst/Trino | **Yes** | Source data queries |
| Internal Load Balancer | **Yes** | API access |
| Extension Server | **No** | Optional - for graph algorithms |
| OAuth2 Proxy | **No** | Optional - for external JWT auth |
| KEDA | **No** | Optional - for auto-scaling export workers |

## Extension Server - Not Required

The Extension Server is an **optional** component that provides additional graph algorithms via a NetworkX-based service.

### When You DON'T Need It:
- Basic graph queries (MATCH, CREATE, MERGE, etc.)
- Standard Cypher operations
- Most common use cases

### When You Might Need It:
- Advanced graph algorithms (PageRank, community detection, etc.)
- NetworkX-specific functions
- Custom algorithm extensions

### Configuration Without Extension Server

Simply omit or leave empty the extension server URL:

```yaml
# In control-plane config
env:
  EXTENSION_SERVER_URL: ""  # Leave empty if not using
```

Or in Helm values:

```yaml
control-plane:
  config:
    extensionServer:
      url: ""  # Not required for basic deployment
```

The wrapper pods will function normally without the extension server - they just won't have access to advanced algorithms.

## Key Code Changes for GKE Deployment

The following adaptations were made for enterprise GKE deployment:

### 1. Internal Load Balancer (GCE Internal Ingress)

**File:** `k8s_service.py`

Instead of nginx path-based routing, uses GCE internal ingress with host-based routing:

```python
# GCE internal load balancer configuration
if self._ingress_class == "gce-internal":
    # Host-based routing: wrapper-{slug}.{domain}
    annotations = {}
    domain = self._get_wrapper_domain()
    ingress_host = f"wrapper-{url_slug}.{domain}"
    path = "/"
    path_type = "Prefix"
```

**Why:** Enterprise environments often don't support wildcard DNS, so we use in-cluster service DNS instead.

### 2. In-Cluster Service DNS for Wrappers

**File:** `k8s_service.py`

```python
def get_external_instance_url(self, url_slug: str) -> str | None:
    if self._ingress_class == "gce-internal":
        # Use in-cluster service DNS - works for kubectl exec clients
        return f"http://wrapper-{url_slug}.{self._namespace}.svc.cluster.local:8000"
```

**Why:** Without wildcard DNS, wrappers are accessed via Kubernetes service DNS from within the cluster.

### 3. Container-Native Load Balancing (NEG)

**File:** `k8s_service.py`

```python
# For GCE internal ingress, enable container-native load balancing
service_annotations = {}
if self._ingress_class == "gce-internal":
    service_annotations["cloud.google.com/neg"] = '{"ingress": true}'
```

**Why:** NEG provides direct pod routing, more efficient than iptables-based NodePort.

### 4. Cloud SQL Proxy SSL Handling

**File:** `database.py`

```python
# Disable SSL for localhost connections (Cloud SQL Proxy handles encryption)
if parsed.hostname in ("127.0.0.1", "localhost"):
    connect_args["ssl"] = False
```

**Why:** Cloud SQL Proxy already encrypts the connection; double SSL causes issues.

### 5. Starburst Role-Based Access

**File:** `starburst.py`

```python
def _set_role_sync(self, client, catalog):
    """Send SET ROLE statement before queries."""
    if self.role:
        client.post(
            f"{self.url}/v1/statement",
            content=f"SET ROLE {self.role}",
            headers=self._get_headers(catalog),
        )
```

**Why:** Enterprise Starburst often requires explicit role setting for fine-grained access control.

### 6. In-Cluster Authentication Mode

**File:** `testing.py`

```python
# In-cluster mode uses X-Username/X-User-Role headers
if os.environ.get("GRAPH_OLAP_IN_CLUSTER_MODE"):
    return {
        "X-Username": persona["email"],
        "X-User-Role": persona["role"],
    }
```

**Why:** For in-cluster testing/access, use simple header-based auth instead of JWT.

### 7. Standalone/Canary Mode for Wrappers

**Files:** `ryugraph-wrapper/config.py`, `falkordb-wrapper/config.py`, `lifespan.py`

```python
# Instance identification (empty = standalone/canary mode — no control-plane registration)
instance_id: str = Field(default="", description="Unique instance identifier (UUID)")
gcs_base_path: str = Field(default="", description="GCS path to snapshot Parquet files")

# In lifespan.py
standalone = not settings.wrapper.instance_id
if standalone:
    logger.info("Running in standalone/canary mode — health endpoint only")
    yield
    return
```

**Why:** Allows deploying wrapper pods for image/config validation without a full control plane setup. Useful for:
- Testing new container images before production
- Validating Kubernetes configurations
- Canary deployments to verify pod startup
- Development environments without full infrastructure

### 8. Starburst Optional Password and SSL Configuration

**File:** `export_worker/config.py`, `starburst.py`

```python
# Password is optional for header-only auth
password: SecretStr | None = Field(default=None, description="Optional password")
role: str | None = Field(default=None, description="Starburst role for X-Trino-Role header")
ssl_verify: bool = Field(default=True, description="Verify SSL certificates")

# In client initialization
self.auth = (user, password) if password else None
```

**Why:** Some enterprise Starburst deployments use header-only authentication (X-Trino-User) without password, and may have self-signed certificates.

### 9. Direct Export Mode (PyArrow Fallback)

**File:** `export_worker/config.py`

```python
direct_export: bool = Field(
    default=True,
    validation_alias="DIRECT_EXPORT",
    description="Use direct PyArrow export instead of Starburst system.unload",
)
```

**Why:** When Starburst `system.unload` is not available (e.g., missing GCS catalog), falls back to PyArrow-based direct export.

## Environment Variables Reference

### Required Variables

```bash
# Database
GRAPH_OLAP_DATABASE_URL="postgresql://user:pass@127.0.0.1:5432/database"

# GCP
GCP_PROJECT="your-project-id"
GCS_BUCKET="your-bucket-name"

# Kubernetes
K8S_NAMESPACE="graph-olap"
K8S_IN_CLUSTER="true"
WRAPPER_SERVICE_ACCOUNT="wrapper"
WRAPPER_INGRESS_CLASS="gce-internal"

# Starburst
STARBURST_URL="https://your-cluster.trino.galaxy.starburst.io:443"
STARBURST_USER="your-service-account"
STARBURST_PASSWORD="your-password"  # Optional for header-only auth
STARBURST_CATALOG="your_catalog"
STARBURST_ROLE="your_role"  # Optional but recommended for enterprise RBAC
STARBURST_SSL_VERIFY="true"  # Set false for self-signed certs

# Export Worker
DIRECT_EXPORT="true"  # Use PyArrow export (default), set false for system.unload
```

### Optional Variables

```bash
# Extension Server (not required for basic deployment)
EXTENSION_SERVER_URL=""  # Leave empty

# OAuth2/JWT (only if using external auth)
AUTH0_JWKS_URL=""
AUTH0_AUDIENCE=""
AUTH0_ISSUER=""

# Auto-scaling (only if using KEDA)
KEDA_ENABLED="false"
```

## Deployment Checklist

### Pre-Deployment

- [ ] GCP Service Accounts created with IAM roles
- [ ] Workload Identity bindings configured
- [ ] GKE cluster running with correct node pools
- [ ] Cloud SQL instance created
- [ ] GCS bucket created
- [ ] Starburst credentials obtained
- [ ] Container images pushed to Artifact Registry

### Kubernetes Resources

- [ ] Namespace created
- [ ] Service accounts with Workload Identity annotations
- [ ] RBAC roles and bindings applied
- [ ] Secrets created (database URL, Starburst credentials)
- [ ] ConfigMaps created

### Deployments

- [ ] Control Plane deployed with Cloud SQL Proxy sidecar
- [ ] Export Worker deployed
- [ ] Internal Load Balancer provisioned
- [ ] NEGs created for services

### Post-Deployment Validation

- [ ] Control Plane health check passing
- [ ] Database migrations completed
- [ ] Export Worker polling for jobs
- [ ] Can create mapping (validates Starburst connectivity)
- [ ] Can create snapshot (validates GCS access)
- [ ] Can create instance (validates K8s pod creation)
- [ ] Can execute query (validates wrapper functionality)

## Common Issues and Solutions

### Issue: Wrapper pods can't access GCS

**Cause:** Workload Identity not configured correctly

**Solution:**
```bash
# Verify annotation on K8s service account
kubectl get sa wrapper -n graph-olap -o yaml | grep gcp-service-account

# Verify IAM binding
gcloud iam service-accounts get-iam-policy wrapper-sa@PROJECT.iam.gserviceaccount.com
```

### Issue: Control Plane can't connect to Cloud SQL

**Cause:** Cloud SQL Proxy not running or IAM role missing

**Solution:**
```bash
# Check proxy logs
kubectl logs -n graph-olap -l app=control-plane -c cloud-sql-proxy

# Verify IAM role
gcloud projects get-iam-policy PROJECT_ID | grep cloudsql.client
```

### Issue: Starburst queries fail with permission denied

**Cause:** Role not set or user doesn't have access

**Solution:**
```bash
# Verify SET ROLE is working
curl -X POST "$STARBURST_URL/v1/statement" \
    -H "X-Trino-User: $STARBURST_USER" \
    -d "SET ROLE $STARBURST_ROLE"

# List available roles
curl -X POST "$STARBURST_URL/v1/statement" \
    -H "X-Trino-User: $STARBURST_USER" \
    -d "SHOW ROLES"
```

### Issue: Internal Load Balancer not provisioning

**Cause:** Missing firewall rules or incorrect ingress class

**Solution:**
```bash
# Check ingress status
kubectl describe ingress control-plane-ingress -n graph-olap

# Verify firewall allows health checks
gcloud compute firewall-rules list | grep health
```

## Architecture Decision Records

Key decisions made for this deployment:

1. **GCE Internal vs nginx ingress** - Chose GCE Internal for native GCP integration and no external exposure

2. **In-cluster service DNS vs wildcard DNS** - Chose in-cluster DNS since enterprise environments often don't support wildcard DNS

3. **Container-native LB (NEG) vs NodePort** - Chose NEG for better performance and direct pod routing

4. **Cloud SQL Proxy vs direct connection** - Chose proxy for IAM-based auth and encrypted connections without managing SSL certificates

5. **SET ROLE + X-Trino-Role header** - Use both for maximum compatibility with different Starburst configurations

6. **Workload Identity vs service account keys** - Chose Workload Identity for keyless authentication (more secure)
