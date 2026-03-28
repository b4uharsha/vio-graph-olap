# GKE Cluster Setup

This guide covers creating and configuring a GKE cluster for the Graph OLAP platform.

## Overview

The platform requires a private GKE cluster with:
- Workload Identity enabled
- Internal load balancing support
- VPC-native networking (alias IPs)
- Container-native load balancing (NEG)

## 1. Prerequisites

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"
export CLUSTER_NAME="graph-olap-cluster"
export NETWORK="your-vpc-network"
export SUBNET="your-subnet"
export PODS_RANGE="pods-range"
export SERVICES_RANGE="services-range"
```

## 2. Create GKE Cluster

```bash
gcloud container clusters create $CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --network=$NETWORK \
    --subnetwork=$SUBNET \
    --cluster-secondary-range-name=$PODS_RANGE \
    --services-secondary-range-name=$SERVICES_RANGE \
    --enable-private-nodes \
    --enable-private-endpoint \
    --master-ipv4-cidr="172.16.0.0/28" \
    --enable-ip-alias \
    --enable-master-authorized-networks \
    --master-authorized-networks="10.0.0.0/8" \
    --workload-pool="${PROJECT_ID}.svc.id.goog" \
    --enable-shielded-nodes \
    --service-account="gke-node-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --num-nodes=3 \
    --machine-type="e2-standard-4" \
    --disk-size="100GB" \
    --disk-type="pd-ssd" \
    --enable-autorepair \
    --enable-autoupgrade \
    --release-channel="regular" \
    --addons=HttpLoadBalancing,HorizontalPodAutoscaling
```

## 3. Create Node Pools

### Control Plane Node Pool

```bash
gcloud container node-pools create control-plane-pool \
    --cluster=$CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --machine-type="e2-standard-4" \
    --num-nodes=2 \
    --disk-size="50GB" \
    --disk-type="pd-ssd" \
    --service-account="gke-node-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --node-labels="workload=control-plane" \
    --node-taints="workload=control-plane:NoSchedule" \
    --enable-autorepair \
    --enable-autoupgrade
```

### Wrapper Node Pool (High Memory)

Wrapper pods load graph data into memory, requiring high-memory nodes:

```bash
gcloud container node-pools create wrapper-pool \
    --cluster=$CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --machine-type="e2-highmem-8" \
    --num-nodes=3 \
    --min-nodes=1 \
    --max-nodes=10 \
    --enable-autoscaling \
    --disk-size="100GB" \
    --disk-type="pd-ssd" \
    --service-account="gke-node-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --node-labels="workload=wrapper" \
    --enable-autorepair \
    --enable-autoupgrade
```

## 4. Configure kubectl Access

```bash
gcloud container clusters get-credentials $CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID
```

## 5. Verify Cluster

```bash
# Check nodes
kubectl get nodes -o wide

# Check system pods
kubectl get pods -n kube-system

# Verify Workload Identity
kubectl describe configmap -n kube-system gke-metadata-server
```

## 6. Install Required Components

### GCE Internal Ingress Controller

For internal load balancing, the cluster uses GCE's native internal load balancer:

```yaml
# internal-ingress-class.yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: gce-internal
  annotations:
    ingressclass.kubernetes.io/is-default-class: "false"
spec:
  controller: ingress.gce.io/internal
```

```bash
kubectl apply -f internal-ingress-class.yaml
```

### Enable Container-Native Load Balancing

Container-native load balancing uses Network Endpoint Groups (NEGs) for direct pod-to-load-balancer communication:

```bash
# Verify NEG controller is running
kubectl get pods -n kube-system | grep neg
```

## 7. Network Policies (Optional)

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: graph-olap-network-policy
  namespace: graph-olap
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: graph-olap
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: graph-olap
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443  # External APIs (Starburst, etc.)
        - protocol: TCP
          port: 5432 # Cloud SQL
```

## 8. Resource Quotas

```yaml
# resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: graph-olap-quota
  namespace: graph-olap
spec:
  hard:
    requests.cpu: "50"
    requests.memory: "200Gi"
    limits.cpu: "100"
    limits.memory: "400Gi"
    pods: "100"
```

## Cluster Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GKE Cluster                                  │
│                                                                      │
│  ┌─────────────────────┐  ┌─────────────────────────────────────┐   │
│  │ control-plane-pool  │  │         wrapper-pool                │   │
│  │  (e2-standard-4)    │  │       (e2-highmem-8)                │   │
│  │                     │  │                                      │   │
│  │  ┌───────────────┐  │  │  ┌───────────┐  ┌───────────┐       │   │
│  │  │ control-plane │  │  │  │ wrapper-1 │  │ wrapper-2 │  ...  │   │
│  │  │     pod       │  │  │  │   pod     │  │   pod     │       │   │
│  │  └───────────────┘  │  │  └───────────┘  └───────────┘       │   │
│  │  ┌───────────────┐  │  │                                      │   │
│  │  │ export-worker │  │  │                                      │   │
│  │  │     pod       │  │  │                                      │   │
│  │  └───────────────┘  │  │                                      │   │
│  └─────────────────────┘  └─────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Internal Load Balancer                       │ │
│  │                    (GCE Internal Ingress)                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────┐
                        │   Cloud SQL       │
                        │   (PostgreSQL)    │
                        └───────────────────┘
```

## Next Steps

- [03-kubernetes-resources.md](03-kubernetes-resources.md) - Namespace, RBAC, and secrets configuration
