# Internal Load Balancer and Ingress Setup

This guide covers configuring GCE Internal Ingress for private network access to the Graph OLAP platform.

## Overview

For enterprise deployments, the platform uses GCE Internal Load Balancer instead of external ingress:
- Traffic stays within the VPC
- No public IP exposure
- Integrates with private DNS
- Uses container-native load balancing (NEGs) for direct pod routing

## 1. Ingress Class Configuration

```yaml
# ingress-class.yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: gce-internal
  annotations:
    ingressclass.kubernetes.io/is-default-class: "false"
spec:
  controller: ingress.gce.io/internal
```

## 2. Control Plane Ingress

```yaml
# control-plane-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: control-plane-ingress
  namespace: graph-olap
  annotations:
    kubernetes.io/ingress.class: "gce-internal"
    # Reserve static internal IP (optional)
    kubernetes.io/ingress.regional-static-ip-name: "graph-olap-internal-ip"
spec:
  ingressClassName: gce-internal
  rules:
    - host: graph-olap.internal.your-domain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: control-plane
                port:
                  number: 8080
```

## 3. Wrapper Access Strategy

Since GCE Internal doesn't support wildcard DNS, wrappers use in-cluster service DNS:

### In-Cluster URL Pattern

```
http://wrapper-{url-slug}.graph-olap.svc.cluster.local:8000
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GKE Cluster                                   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   Internal Load Balancer                     │    │
│  │               (graph-olap.internal.domain.com)               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                     Control Plane                            │    │
│  │                                                              │    │
│  │   /api/instances     → Instance management                   │    │
│  │   /api/mappings      → Schema mappings                       │    │
│  │   /api/snapshots     → Snapshot management                   │    │
│  │   /health            → Health check                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ wrapper-abc123   │  │ wrapper-def456   │  │ wrapper-ghi789   │   │
│  │ (ClusterIP Svc)  │  │ (ClusterIP Svc)  │  │ (ClusterIP Svc)  │   │
│  │                  │  │                  │  │                  │   │
│  │ In-cluster only  │  │ In-cluster only  │  │ In-cluster only  │   │
│  │ via service DNS  │  │ via service DNS  │  │ via service DNS  │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Client Access Pattern

1. Client calls Control Plane API to create instance
2. Control Plane returns instance URL (in-cluster DNS)
3. Client (running in-cluster) uses the wrapper URL directly

```bash
# Example from in-cluster client
curl http://wrapper-abc123.graph-olap.svc.cluster.local:8000/query \
    -H "Content-Type: application/json" \
    -H "X-Username: user@example.com" \
    -H "X-User-Role: analyst" \
    -d '{"query": "MATCH (n) RETURN count(n)"}'
```

## 4. NEG (Network Endpoint Groups) Configuration

Container-native load balancing uses NEGs for efficient routing:

### Service Annotation

```yaml
# wrapper-service-neg.yaml
apiVersion: v1
kind: Service
metadata:
  name: wrapper-abc123
  namespace: graph-olap
  annotations:
    # Enable container-native load balancing
    cloud.google.com/neg: '{"ingress": true}'
spec:
  selector:
    app: ryugraph-wrapper
    url-slug: abc123
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

### Benefits of NEGs

| Traditional (iptables) | Container-Native (NEG) |
|----------------------|------------------------|
| LB → Node → iptables → Pod | LB → Pod directly |
| Extra network hop | Direct routing |
| NodePort required | ClusterIP works |
| Less efficient | More efficient |

## 5. Static Internal IP (Optional)

Reserve a static internal IP for consistent DNS:

```bash
# Reserve internal IP
gcloud compute addresses create graph-olap-internal-ip \
    --region=us-central1 \
    --subnet=your-subnet \
    --purpose=SHARED_LOADBALANCER_VIP

# Get the IP
gcloud compute addresses describe graph-olap-internal-ip \
    --region=us-central1 \
    --format="value(address)"
```

## 6. Private DNS Configuration

Configure Cloud DNS for internal access:

```bash
# Create private DNS zone
gcloud dns managed-zones create graph-olap-internal \
    --dns-name="internal.your-domain.com." \
    --visibility=private \
    --networks=your-vpc-network

# Add A record pointing to internal LB IP
gcloud dns record-sets create graph-olap.internal.your-domain.com. \
    --zone=graph-olap-internal \
    --type=A \
    --ttl=300 \
    --rrdatas="10.128.0.100"  # Your internal LB IP
```

## 7. Health Checks

GCE automatically creates health checks for the backend:

```yaml
# Custom health check (optional)
apiVersion: cloud.google.com/v1
kind: BackendConfig
metadata:
  name: control-plane-backend-config
  namespace: graph-olap
spec:
  healthCheck:
    checkIntervalSec: 10
    timeoutSec: 5
    healthyThreshold: 2
    unhealthyThreshold: 3
    type: HTTP
    requestPath: /health
    port: 8080
```

Link to service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: control-plane
  namespace: graph-olap
  annotations:
    cloud.google.com/backend-config: '{"default": "control-plane-backend-config"}'
```

## 8. Firewall Rules

Ensure firewall allows internal LB health checks:

```bash
# Allow health check probes from GCP ranges
gcloud compute firewall-rules create allow-health-checks \
    --network=your-vpc-network \
    --allow=tcp:8080,tcp:8000 \
    --source-ranges=35.191.0.0/16,130.211.0.0/22 \
    --target-tags=gke-node
```

## 9. Testing Internal Access

```bash
# From a pod in the cluster
kubectl run test-curl --rm -it --image=curlimages/curl -- \
    curl -v http://control-plane.graph-olap.svc.cluster.local:8080/health

# From a VM in the same VPC
curl -v http://graph-olap.internal.your-domain.com/health

# Test wrapper access (from in-cluster)
kubectl run test-curl --rm -it --image=curlimages/curl -- \
    curl -v http://wrapper-abc123.graph-olap.svc.cluster.local:8000/ready
```

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                           VPC Network                                │
│                                                                      │
│    ┌──────────────┐                                                 │
│    │   Client VM  │                                                 │
│    │   or Pod     │                                                 │
│    └──────┬───────┘                                                 │
│           │                                                          │
│           │ graph-olap.internal.your-domain.com                     │
│           ▼                                                          │
│    ┌──────────────────────────────────────────────────────────┐     │
│    │           GCE Internal Load Balancer                      │     │
│    │                  (10.128.0.100)                           │     │
│    └──────────────────────────┬───────────────────────────────┘     │
│                               │                                      │
│                               ▼                                      │
│    ┌──────────────────────────────────────────────────────────┐     │
│    │                     GKE Cluster                           │     │
│    │                                                           │     │
│    │   ┌─────────────────┐      ┌─────────────────────────┐   │     │
│    │   │  Control Plane  │      │  Wrapper Pods           │   │     │
│    │   │  (via Ingress)  │      │  (ClusterIP services)   │   │     │
│    │   │                 │      │                         │   │     │
│    │   │  NEG backend    │      │  In-cluster DNS only    │   │     │
│    │   └─────────────────┘      └─────────────────────────┘   │     │
│    │                                                           │     │
│    └──────────────────────────────────────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Next Steps

- [07-cloud-sql-proxy.md](07-cloud-sql-proxy.md) - Cloud SQL Auth Proxy configuration
