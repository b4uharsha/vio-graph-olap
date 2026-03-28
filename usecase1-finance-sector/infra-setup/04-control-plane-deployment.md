# Control Plane Deployment

This guide covers deploying the Control Plane service, which orchestrates wrapper pod lifecycle and handles API requests.

## Overview

The Control Plane is the central coordinator that:
- Manages wrapper instance lifecycle (create, delete, status)
- Handles user authentication via JWT
- Coordinates with Cloud SQL for state persistence
- Dynamically creates/destroys Kubernetes pods for graph instances

## 1. Deployment Manifest

```yaml
# control-plane-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: control-plane
  namespace: graph-olap
  labels:
    app: control-plane
spec:
  replicas: 2
  selector:
    matchLabels:
      app: control-plane
  template:
    metadata:
      labels:
        app: control-plane
    spec:
      serviceAccountName: control-plane

      # Node selector for control-plane pool
      nodeSelector:
        workload: control-plane
      tolerations:
        - key: "workload"
          operator: "Equal"
          value: "control-plane"
          effect: "NoSchedule"

      # Cloud SQL Auth Proxy sidecar
      containers:
        - name: cloud-sql-proxy
          image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8.0
          args:
            - "--structured-logs"
            - "--port=5432"
            - "YOUR_PROJECT:YOUR_REGION:YOUR_INSTANCE"
          securityContext:
            runAsNonRoot: true
          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "128Mi"
              cpu: "100m"

        - name: control-plane
          image: gcr.io/YOUR_PROJECT/control-plane:v1.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
              name: http

          envFrom:
            - configMapRef:
                name: control-plane-config

          env:
            # Database URL points to localhost (Cloud SQL Proxy)
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: control-plane-secrets
                  key: database-url
            - name: GRAPH_OLAP_INTERNAL_API_KEY
              valueFrom:
                secretKeyRef:
                  name: control-plane-secrets
                  key: api-internal-token
            - name: STARBURST_USER
              valueFrom:
                secretKeyRef:
                  name: starburst-credentials
                  key: STARBURST_USER
            - name: STARBURST_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: starburst-credentials
                  key: STARBURST_PASSWORD

          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "2000m"

          # Startup probe - allow time for database migrations
          startupProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 30  # 150s max startup

          # Readiness probe
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3

          # Liveness probe
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3

          securityContext:
            runAsNonRoot: true
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            capabilities:
              drop:
                - ALL

      # Pod anti-affinity for HA
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: control-plane
                topologyKey: kubernetes.io/hostname
```

## 2. Service

```yaml
# control-plane-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: control-plane
  namespace: graph-olap
  labels:
    app: control-plane
spec:
  selector:
    app: control-plane
  ports:
    - port: 8080
      targetPort: 8080
      name: http
  type: ClusterIP
```

## 3. Pod Disruption Budget

```yaml
# control-plane-pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: control-plane-pdb
  namespace: graph-olap
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: control-plane
```

## 4. Horizontal Pod Autoscaler

```yaml
# control-plane-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: control-plane-hpa
  namespace: graph-olap
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: control-plane
  minReplicas: 2
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

## 5. Deploy

```bash
kubectl apply -f control-plane-deployment.yaml
kubectl apply -f control-plane-service.yaml
kubectl apply -f control-plane-pdb.yaml
kubectl apply -f control-plane-hpa.yaml
```

## 6. Verify Deployment

```bash
# Check deployment status
kubectl get deployment control-plane -n graph-olap

# Check pods
kubectl get pods -n graph-olap -l app=control-plane

# Check logs
kubectl logs -n graph-olap -l app=control-plane -c control-plane --tail=100

# Check Cloud SQL Proxy logs
kubectl logs -n graph-olap -l app=control-plane -c cloud-sql-proxy --tail=50

# Test health endpoint (from within cluster)
kubectl run test-curl --rm -it --image=curlimages/curl -- \
    curl -s http://control-plane.graph-olap.svc.cluster.local:8080/health
```

## 7. Database Migrations

The control plane runs migrations on startup. Verify:

```bash
# Check migration logs
kubectl logs -n graph-olap -l app=control-plane -c control-plane | grep -i migration
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Plane Pod                         │
│                                                              │
│  ┌──────────────────────┐    ┌─────────────────────────┐    │
│  │   control-plane      │    │   cloud-sql-proxy       │    │
│  │   container          │    │   sidecar               │    │
│  │                      │    │                         │    │
│  │  - FastAPI app       │───▶│  - Connects to Cloud SQL│    │
│  │  - JWT auth          │    │  - localhost:5432       │    │
│  │  - K8s API calls     │    │  - IAM authentication   │    │
│  │  - Starburst client  │    │                         │    │
│  └──────────────────────┘    └─────────────────────────┘    │
│            │                            │                    │
└────────────┼────────────────────────────┼────────────────────┘
             │                            │
             ▼                            ▼
    ┌─────────────────┐          ┌─────────────────┐
    │  Kubernetes API │          │   Cloud SQL     │
    │  (create pods)  │          │   (PostgreSQL)  │
    └─────────────────┘          └─────────────────┘
```

## Next Steps

- [05-wrapper-pod-architecture.md](05-wrapper-pod-architecture.md) - Wrapper pod architecture
