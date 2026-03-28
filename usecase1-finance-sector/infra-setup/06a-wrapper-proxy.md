# Wrapper Proxy (NGINX Reverse Proxy)

The wrapper proxy routes analyst requests from the control plane to the correct graph wrapper pod. Each analyst instance gets its own wrapper pod, and the proxy handles routing by instance slug.

## Architecture

```
Analyst Request
    │
    ▼
NGINX Ingress
    │
    ├── /api/*         ──▶ Control Plane
    │
    └── /wrapper/{slug} ──▶ Wrapper Proxy (NGINX) ──▶ Wrapper Pod (FalkorDB)
                                                          │
                                                          └── port 8000
```

## How It Works

1. Analyst creates an instance via `/api/instances`
2. Control plane spawns a wrapper pod + ClusterIP service
3. The instance URL is returned as `/wrapper/{slug}`
4. Analyst queries via `/wrapper/{slug}/query`
5. NGINX ingress (or wrapper proxy) routes to the correct pod service

## Configuration

The control plane handles wrapper routing internally via the `/wrapper/{slug}` proxy endpoint. No separate wrapper-proxy deployment is needed if using the built-in control plane proxy.

For high-traffic deployments, a dedicated NGINX reverse proxy can be deployed:

```yaml
# wrapper-proxy-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: wrapper-proxy-config
  namespace: graph-olap
data:
  nginx.conf: |
    worker_processes auto;
    events { worker_connections 1024; }

    http {
      resolver kube-dns.kube-system.svc.cluster.local valid=5s;

      server {
        listen 8080;

        # Health check
        location /health {
          return 200 '{"status": "healthy"}';
          add_header Content-Type application/json;
        }

        # Dynamic routing to wrapper pods by slug
        location ~ ^/wrapper/(?<slug>[^/]+)(?<path>/.*)$ {
          proxy_pass http://wrapper-$slug.graph-olap.svc.cluster.local:8000$path;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_read_timeout 300s;
        }
      }
    }
```

```yaml
# wrapper-proxy-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wrapper-proxy
  namespace: graph-olap
spec:
  replicas: 2
  selector:
    matchLabels:
      app: wrapper-proxy
  template:
    metadata:
      labels:
        app: wrapper-proxy
    spec:
      containers:
        - name: nginx
          image: nginx:1.27-alpine
          ports:
            - containerPort: 8080
          volumeMounts:
            - name: config
              mountPath: /etc/nginx/nginx.conf
              subPath: nginx.conf
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
      volumes:
        - name: config
          configMap:
            name: wrapper-proxy-config
---
apiVersion: v1
kind: Service
metadata:
  name: wrapper-proxy
  namespace: graph-olap
spec:
  selector:
    app: wrapper-proxy
  ports:
    - port: 8080
      targetPort: 8080
```

## When to Use

| Approach | When |
|----------|------|
| Built-in control plane proxy | Default — works for most deployments |
| Dedicated wrapper proxy | High traffic, need separate scaling for proxy vs control plane |

## Verification

```bash
# Check wrapper proxy pods
kubectl get pods -n graph-olap -l app=wrapper-proxy

# Test routing (replace SLUG with actual instance slug)
curl -s http://wrapper-proxy.graph-olap.svc.cluster.local:8080/wrapper/SLUG/health
```
