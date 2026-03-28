# Cloud SQL Auth Proxy Configuration

This guide covers configuring Cloud SQL Auth Proxy for secure database connectivity.

## Overview

Cloud SQL Auth Proxy provides:
- Secure, encrypted connections to Cloud SQL
- IAM-based authentication (no passwords in connection strings)
- Automatic certificate management
- Connection pooling

## 1. Create Cloud SQL Instance

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export INSTANCE_NAME="graph-olap-db"

# Create PostgreSQL instance
gcloud sql instances create $INSTANCE_NAME \
    --database-version=POSTGRES_15 \
    --tier=db-custom-4-16384 \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=100GB \
    --storage-auto-increase \
    --availability-type=REGIONAL \
    --backup-start-time=02:00 \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=03 \
    --database-flags=max_connections=200 \
    --network=projects/$PROJECT_ID/global/networks/your-vpc \
    --no-assign-ip \
    --enable-google-private-path
```

## 2. Create Database and User

```bash
# Create database
gcloud sql databases create your_database \
    --instance=$INSTANCE_NAME

# Create user (for bootstrap - prefer IAM auth)
gcloud sql users create your_database_user \
    --instance=$INSTANCE_NAME \
    --password="your-secure-password"
```

## 3. IAM Database Authentication (Recommended)

```bash
# Enable IAM database authentication
gcloud sql instances patch $INSTANCE_NAME \
    --database-flags=cloudsql.iam_authentication=on

# Grant IAM user access
gcloud sql users create control-plane-sa@${PROJECT_ID}.iam \
    --instance=$INSTANCE_NAME \
    --type=CLOUD_IAM_SERVICE_ACCOUNT
```

Grant database permissions:

```sql
-- Connect to the database and run:
GRANT ALL PRIVILEGES ON DATABASE your_database TO "control-plane-sa@YOUR_PROJECT_ID.iam";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "control-plane-sa@YOUR_PROJECT_ID.iam";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "control-plane-sa@YOUR_PROJECT_ID.iam";
```

## 4. Cloud SQL Proxy Sidecar Configuration

### Deployment with Sidecar

```yaml
# control-plane-with-proxy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: control-plane
  namespace: graph-olap
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

      containers:
        # Cloud SQL Auth Proxy sidecar
        - name: cloud-sql-proxy
          image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8.0
          args:
            - "--structured-logs"
            - "--port=5432"
            # Connection string format: PROJECT:REGION:INSTANCE
            - "YOUR_PROJECT:us-central1:graph-olap-db"
            # For IAM authentication:
            - "--auto-iam-authn"

          securityContext:
            runAsNonRoot: true
            runAsUser: 65532
            allowPrivilegeEscalation: false

          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "256Mi"
              cpu: "500m"

          # Health check for the proxy
          livenessProbe:
            exec:
              command:
                - /cloud-sql-proxy
                - --version
            initialDelaySeconds: 5
            periodSeconds: 30

        # Main application container
        - name: control-plane
          image: gcr.io/YOUR_PROJECT/control-plane:v1.0.0

          env:
            # Database URL points to localhost (proxy)
            # For IAM auth, password is empty
            - name: DATABASE_URL
              value: "postgresql://control-plane-sa@YOUR_PROJECT_ID.iam@127.0.0.1:5432/your_database"

            # For password auth (alternative)
            # - name: DATABASE_URL
            #   valueFrom:
            #     secretKeyRef:
            #       name: control-plane-secrets
            #       key: database-url

          # ... rest of container spec
```

## 5. Connection String Formats

### IAM Authentication (Recommended)

```
postgresql://SA_NAME@PROJECT_ID.iam@127.0.0.1:5432/DATABASE
```

Example:
```
postgresql://control-plane-sa@my-project.iam@127.0.0.1:5432/your_database
```

### Password Authentication

```
postgresql://USERNAME:PASSWORD@127.0.0.1:5432/DATABASE
```

## 6. SSL Configuration

When connecting via Cloud SQL Proxy, SSL is handled by the proxy. The application connects to localhost without SSL:

```python
# Python SQLAlchemy configuration
from sqlalchemy import create_engine

# SSL disabled for localhost (proxy handles encryption)
engine = create_engine(
    "postgresql://user@127.0.0.1:5432/your_database",
    connect_args={"sslmode": "disable"}  # Proxy handles SSL
)
```

Code implementation in `database.py`:

```python
def get_connect_args(database_url: str) -> dict:
    """Get connection arguments based on host."""
    parsed = urlparse(database_url)

    # Disable SSL for localhost connections (Cloud SQL Proxy)
    if parsed.hostname in ("127.0.0.1", "localhost"):
        return {"ssl": False}

    # Enable SSL for direct connections
    return {"ssl": "require"}
```

## 7. Connection Pooling

The proxy handles connection pooling efficiently:

```yaml
# proxy-with-pooling.yaml
containers:
  - name: cloud-sql-proxy
    image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8.0
    args:
      - "--structured-logs"
      - "--port=5432"
      - "--max-connections=100"        # Max connections to Cloud SQL
      - "--max-sigterm-delay=30s"      # Graceful shutdown
      - "--lazy-refresh"               # Refresh certs lazily
      - "YOUR_PROJECT:REGION:INSTANCE"
```

## 8. Troubleshooting

### Check Proxy Logs

```bash
kubectl logs -n graph-olap -l app=control-plane -c cloud-sql-proxy
```

### Test Connection

```bash
# Exec into the pod
kubectl exec -n graph-olap -it deployment/control-plane -c control-plane -- sh

# Test connection
psql "postgresql://user@127.0.0.1:5432/your_database" -c "SELECT 1"
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | Proxy not running | Check proxy container logs |
| Permission denied | Missing IAM role | Add `roles/cloudsql.client` to SA |
| Certificate error | Old proxy version | Update to latest proxy image |
| Too many connections | Pool exhausted | Increase `--max-connections` |

## 9. High Availability Setup

```yaml
# For HA, ensure proxy runs on all pods
spec:
  replicas: 2
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: control-plane
              topologyKey: kubernetes.io/hostname
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Control Plane Pod                            │
│                                                                      │
│   ┌─────────────────────────┐     ┌──────────────────────────────┐  │
│   │     control-plane       │     │     cloud-sql-proxy          │  │
│   │     container           │     │     sidecar                  │  │
│   │                         │     │                              │  │
│   │  DATABASE_URL=          │────▶│  Listens on 127.0.0.1:5432   │  │
│   │  postgresql://...       │     │                              │  │
│   │  @127.0.0.1:5432        │     │  Encrypts connection         │  │
│   │                         │     │  Uses Workload Identity      │  │
│   └─────────────────────────┘     └──────────────────────────────┘  │
│                                               │                      │
└───────────────────────────────────────────────┼──────────────────────┘
                                                │
                                    Encrypted Connection
                                    (TLS 1.3, IAM Auth)
                                                │
                                                ▼
                                   ┌──────────────────────┐
                                   │     Cloud SQL        │
                                   │     PostgreSQL       │
                                   │                      │
                                   │  Private IP only     │
                                   │  Regional HA         │
                                   └──────────────────────┘
```

## Next Steps

- [08-jwt-authentication.md](08-jwt-authentication.md) - JWT authentication flow
