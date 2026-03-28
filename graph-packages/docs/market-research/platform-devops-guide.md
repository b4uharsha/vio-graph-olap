# Platform & DevOps Teams Guide

> How to deploy Graph OLAP as an internal platform service for your organization.

---

## The Opportunity for Platform Teams

**Your analysts need graph analytics. You have two choices:**

| Option | Effort | Cost | Control |
|--------|--------|------|---------|
| Buy SaaS (Neo4j Aura, PuppyGraph) | Low | High ($$$) | None — data leaves network |
| Build custom solution | Very High | Medium | Full — but years of work |
| **Deploy Graph OLAP** | **Low** | **Low** | **Full — runs on your K8s** |

**Graph OLAP is designed to be operated by platform teams** — same patterns you already use for other internal services.

---

## Architecture for Platform Teams

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Your Kubernetes Cluster                           │
│                                                                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │  Control Plane  │    │  Export Worker  │    │   PostgreSQL    │      │
│  │  (always-on)    │    │  (KEDA scaled)  │    │   (metadata)    │      │
│  │  - REST API     │    │  - Scales to 0  │    │                 │      │
│  │  - K8s operator │    │  - Scales up    │    │                 │      │
│  └────────┬────────┘    └─────────────────┘    └─────────────────┘      │
│           │                                                              │
│           │ Spawns/deletes dynamically                                   │
│           ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Analyst Workspace Pods                        │    │
│  │                                                                  │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │    │
│  │  │ Alice's  │  │  Bob's   │  │ Carol's  │  │  Dave's  │  ...   │    │
│  │  │ FalkorDB │  │ RyuGraph │  │ FalkorDB │  │ RyuGraph │        │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │    │
│  │                                                                  │    │
│  │  Auto-delete after TTL (configurable: 1hr, 4hr, 24hr, etc.)     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐            ┌─────────────────┐
│  Your Warehouse │            │   Your GCS/S3   │
│  (Starburst,    │            │   (Parquet      │
│   BigQuery)     │            │    snapshots)   │
└─────────────────┘            └─────────────────┘
```

---

## What Platform Teams Manage

### Always-On Components (Minimal Resources)

| Component | Resources | Purpose |
|-----------|-----------|---------|
| Control Plane | 1 pod, 512MB RAM | API, orchestration |
| PostgreSQL | 1 pod, 1GB RAM | Metadata storage |
| Extension Server | 1 pod, 256MB RAM | Graph algorithms |

**Total always-on footprint: ~2GB RAM, 1 CPU**

### Auto-Scaled Components

| Component | Scaling | Purpose |
|-----------|---------|---------|
| Export Worker | KEDA (0→N based on queue) | Data extraction |
| Wrapper Pods | On-demand per analyst | Graph workspaces |

**These scale to zero when not in use.**

---

## Deployment Options

### Option 1: Dedicated Namespace

```yaml
# Isolated namespace for graph-olap
apiVersion: v1
kind: Namespace
metadata:
  name: graph-olap
  labels:
    team: platform
    service: graph-analytics
```

**Best for:** Strict resource isolation, chargeback by namespace.

### Option 2: Shared Platform Namespace

Deploy alongside other data platform services.

**Best for:** Simpler management, shared infrastructure.

### Option 3: Multi-Tenant with Namespace per Team

```
graph-olap-finance/     # Finance team's workspaces
graph-olap-risk/        # Risk team's workspaces
graph-olap-compliance/  # Compliance team's workspaces
```

**Best for:** Large organizations with team-level isolation requirements.

---

## Integration with Existing Infrastructure

### 1. Authentication (SSO/OIDC)

```yaml
# values.yaml
auth:
  provider: oidc
  issuer: https://your-idp.company.com
  clientId: graph-olap
  # Maps OIDC groups to Graph OLAP roles
  groupMappings:
    analysts: analyst
    admins: admin
```

**Supports:** Okta, Azure AD, Google Workspace, Keycloak, any OIDC provider.

### 2. Secrets Management

```yaml
# Integration with external secrets
externalSecrets:
  enabled: true
  secretStore: vault  # or aws-secrets-manager, gcp-secret-manager
  keys:
    - name: starburst-password
      remoteRef: graph-olap/starburst
    - name: gcs-credentials
      remoteRef: graph-olap/gcs
```

**Supports:** HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault.

### 3. Observability Stack

```yaml
# Prometheus/Grafana integration
monitoring:
  prometheus:
    enabled: true
    serviceMonitor: true
  grafana:
    dashboards: true
```

**Exports:** Request latency, pod lifecycle, query metrics, resource usage.

### 4. Logging

```yaml
# Structured logging to your stack
logging:
  format: json
  level: info
  # Ships to your existing log aggregator
```

**Compatible with:** ELK, Loki, Splunk, Datadog, CloudWatch.

### 5. Network Policies

```yaml
# Restrict traffic to required services only
networkPolicy:
  enabled: true
  ingress:
    - from: [ingress-controller]
  egress:
    - to: [starburst, gcs, postgres]
```

---

## Resource Management

### Resource Quotas per Team

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: finance-team-quota
  namespace: graph-olap
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "20"
```

### Pod Limits for Wrapper Instances

```yaml
# values.yaml
wrapper:
  resources:
    requests:
      memory: "2Gi"
      cpu: "500m"
    limits:
      memory: "8Gi"
      cpu: "2"
  # Maximum concurrent pods per user
  maxPodsPerUser: 3
  # Default TTL before auto-delete
  defaultTTL: 4h
```

### Cost Control

| Lever | Configuration |
|-------|--------------|
| Max pods per user | `maxPodsPerUser: 3` |
| Default TTL | `defaultTTL: 4h` |
| Max TTL | `maxTTL: 24h` |
| Resource limits | Standard K8s limits |
| Namespace quotas | Standard K8s quotas |

---

## Operational Runbook

### Daily Operations

| Task | Automation |
|------|------------|
| Pod cleanup | Automatic (TTL-based) |
| Log rotation | Your existing stack |
| Metrics collection | Prometheus scrape |
| Health checks | K8s probes |

**Graph OLAP is designed to be low-ops** — most operations are automatic.

### Common Operations

```bash
# Check system health
kubectl get pods -n graph-olap

# View active analyst workspaces
kubectl get pods -n graph-olap -l app=wrapper

# Check control plane logs
kubectl logs -n graph-olap deployment/control-plane

# Force cleanup of stuck pod
kubectl delete pod -n graph-olap wrapper-<instance-id>

# Scale export workers manually (if needed)
kubectl scale deployment/export-worker -n graph-olap --replicas=5
```

### Upgrades

```bash
# Helm upgrade (zero-downtime for analysts)
helm upgrade graph-olap ./helm/charts/graph-olap \
  -n graph-olap \
  -f values.yaml \
  --set image.tag=v1.2.0
```

**Rolling updates:** Control plane updates without affecting running analyst workspaces.

---

## Security Checklist for Platform Teams

| Requirement | Graph OLAP Feature |
|-------------|-------------------|
| **No data exfiltration** | Runs in your cluster, no external calls |
| **Network isolation** | NetworkPolicy support |
| **Secrets management** | External secrets integration |
| **Audit logging** | All API calls logged |
| **RBAC** | K8s RBAC + application-level roles |
| **Pod security** | Non-root containers, read-only filesystem |
| **Image scanning** | Standard images, scan with your tools |

### Pod Security Standards

```yaml
# Pods run with restricted security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

---

## Capacity Planning

### Sizing Guide

| Team Size | Control Plane | Export Workers | Expected Pods |
|-----------|--------------|----------------|---------------|
| 5 analysts | 1 replica | 0-2 (KEDA) | 1-5 concurrent |
| 20 analysts | 2 replicas | 0-5 (KEDA) | 5-15 concurrent |
| 100 analysts | 3 replicas (HA) | 0-10 (KEDA) | 20-50 concurrent |

### Storage Requirements

| Data | Storage Type | Sizing |
|------|-------------|--------|
| Metadata (PostgreSQL) | Persistent | 10-50GB |
| Parquet snapshots | Object storage (GCS/S3) | Varies by data size |
| Wrapper pods | Ephemeral | 2-8GB per pod |

---

## Cost Model for Chargeback

### Option 1: Per-Pod-Hour

```
Cost = (pod_hours × resource_rate) + (storage_gb × storage_rate)
```

Track with: Prometheus metrics + Kubecost.

### Option 2: Per-Team Flat Rate

```
Team A: $500/month (up to 10 concurrent pods)
Team B: $200/month (up to 3 concurrent pods)
```

### Option 3: No Chargeback (Platform Absorbs)

For smaller deployments, just include in platform budget.

---

## Migration from SaaS Graph Solutions

### From Neo4j Aura

| Step | Action |
|------|--------|
| 1 | Export Cypher queries (they work in Graph OLAP) |
| 2 | Map data sources to SQL |
| 3 | Deploy Graph OLAP |
| 4 | Validate with test queries |
| 5 | Cut over analysts |

**Query compatibility:** Graph OLAP uses standard Cypher — most queries work unchanged.

### From PuppyGraph

| Step | Action |
|------|--------|
| 1 | Same warehouse connections |
| 2 | Map schema definitions |
| 3 | Deploy Graph OLAP |
| 4 | Enjoy 100x faster multi-hop queries |

---

## Support Model

### Self-Service (Analysts)

- Create/delete workspaces
- Run queries
- Export results

### Platform Team (You)

- Cluster management
- Upgrades
- Capacity planning
- Troubleshooting escalations

### What You Don't Need

- Graph database expertise
- Dedicated DBA
- 24/7 on-call (it's self-healing)

---

## Getting Started

### Step 1: Deploy to Dev/Test

```bash
# Clone repo
git clone https://github.com/your-org/graph-olap-local-deploy.git

# Deploy with defaults
make deploy

# Validate
make status
```

### Step 2: Configure for Your Environment

```bash
# Edit values for your cluster
vim helm/values-production.yaml

# Deploy to production namespace
helm install graph-olap ./helm/charts/graph-olap \
  -n graph-olap \
  -f helm/values-production.yaml
```

### Step 3: Integrate with SSO

```yaml
# Add to values-production.yaml
auth:
  provider: oidc
  issuer: https://your-idp.company.com
```

### Step 4: Onboard First Team

1. Create namespace/quotas
2. Add users to OIDC group
3. Share Jupyter URL
4. Run demo notebook together

---

## Summary: Why Platform Teams Love Graph OLAP

| Pain Point | Graph OLAP Solution |
|------------|---------------------|
| "Analysts want graph, I don't want another SaaS" | Runs on your K8s |
| "I can't send data to third parties" | Data never leaves your network |
| "I need cost control" | Zero idle cost + quotas |
| "I need to integrate with our stack" | Standard K8s patterns |
| "I don't want to be on-call for it" | Self-healing, auto-cleanup |
| "Analysts should self-serve" | They create their own workspaces |

**Graph OLAP is the internal platform service your analysts need — without the ops burden.**

---

## Resources

- [GKE Deployment Guide](../../usecase/README.md) — Full production deployment
- [Architecture Overview](../../README.md#architecture) — System design
- [API Documentation](http://localhost:30081/api/docs) — After deployment
