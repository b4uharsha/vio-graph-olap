# Debug Guide

## Common Issues

### Pod not starting

```bash
kubectl describe pod -n graph-olap-platform -l app=control-plane
kubectl logs -n graph-olap-platform -l app=control-plane --previous
```

### Cloud SQL Proxy connection failure

```bash
kubectl logs -n graph-olap-platform -l app=control-plane -c cloud-sql-proxy
```

### Wrapper proxy returning 502

```bash
kubectl logs -n graph-olap-platform -l app=wrapper-proxy
kubectl exec -n graph-olap-platform deploy/wrapper-proxy -- curl -v http://falkordb-wrapper:8080/health
```

### Checking request headers

```bash
kubectl exec -n graph-olap-platform deploy/control-plane -- \
    curl -v -H "X-Username: testuser" http://localhost:8080/api/v1/health
```

---

## Wrapper Image Management

### Check current wrapper images

```bash
# Static deployment images (templates — 0/0 pods is normal)
kubectl get deployment ryugraph-wrapper -n graph-olap-platform -o jsonpath='{.spec.template.spec.containers[0].image}' && echo
kubectl get deployment falkordb-wrapper -n graph-olap-platform -o jsonpath='{.spec.template.spec.containers[0].image}' && echo

# Control-plane configmap (used when spawning dynamic wrapper pods)
kubectl get configmap control-plane-config -n graph-olap-platform -o jsonpath='{.data.GRAPH_OLAP_WRAPPER_IMAGE}' && echo
kubectl get configmap control-plane-config -n graph-olap-platform -o jsonpath='{.data.GRAPH_OLAP_FALKORDB_WRAPPER_IMAGE}' && echo

# All images currently running in the namespace
kubectl get pods -n graph-olap-platform -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
```

### Kill stale dynamic wrapper pods

```bash
# Kill all running ryugraph wrapper instances
kubectl delete pods -n graph-olap-platform -l wrapper-type=ryugraph

# Kill all running falkordb wrapper instances
kubectl delete pods -n graph-olap-platform -l wrapper-type=falkordb

# Kill ALL dynamic wrapper pods at once
kubectl delete pods -n graph-olap-platform -l wrapper-type
```

### Restart control-plane (picks up configmap changes)

```bash
kubectl rollout restart deployment graph-olap-control-plane -n graph-olap-platform
kubectl rollout status deployment graph-olap-control-plane -n graph-olap-platform --timeout=120s
```

### Update wrapper image tag (bypasses ArgoCD — temporary)

```bash
# Ryugraph
kubectl patch configmap control-plane-config -n graph-olap-platform \
    --type merge -p '{"data":{"GRAPH_OLAP_WRAPPER_IMAGE":"gcr.io/hsbc-12636856-udlhk-dev/com/hsbc/wholesale/data/ryugraph-wrapper:NEW_TAG"}}'

# FalkorDB
kubectl patch configmap control-plane-config -n graph-olap-platform \
    --type merge -p '{"data":{"GRAPH_OLAP_FALKORDB_WRAPPER_IMAGE":"gcr.io/hsbc-12636856-udlhk-dev/com/hsbc/wholesale/data/falkordb-wrapper:NEW_TAG"}}'

# Then restart control-plane to pick up changes
kubectl rollout restart deployment graph-olap-control-plane -n graph-olap-platform
```

---

## Service Health Checks

### Check all workload status

```bash
kubectl get deployments -n graph-olap-platform
kubectl get pods -n graph-olap-platform
kubectl get cronjobs -n graph-olap-platform
```

### Control-plane health

```bash
kubectl exec -n graph-olap-platform deploy/graph-olap-control-plane -- \
    curl -s http://localhost:8080/api/v1/health | python3 -m json.tool
```

### Export worker logs

```bash
kubectl logs -n graph-olap-platform deploy/graph-olap-export-worker --tail=100
```

### Cloud SQL connectivity

```bash
kubectl logs -n graph-olap-platform deploy/graph-olap-control-plane -c cloud-sql-proxy --tail=50
```

---

## Starburst / Snapshot Debugging

### Check export worker snapshot progress

```bash
kubectl logs -n graph-olap-platform deploy/graph-olap-export-worker --tail=200 | grep -i "snapshot\|export\|claim"
```

### Check if Starburst is reachable

```bash
kubectl exec -n graph-olap-platform deploy/graph-olap-export-worker -- \
    curl -sk https://wsdv-hk-dev.hk.hsbc:8443/v1/info
```

---

## Cleanup

### Terminate all user instances (via API)

```bash
kubectl exec -n graph-olap-platform deploy/graph-olap-control-plane -- \
    curl -s http://localhost:8080/api/v1/instances?status=running | python3 -m json.tool
```

### Delete orphaned wrapper pods

```bash
# List wrapper pods with their instance labels
kubectl get pods -n graph-olap-platform -l wrapper-type -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,INSTANCE:.metadata.labels.instance-id,OWNER:.metadata.labels.owner-email'

# Delete a specific wrapper pod
kubectl delete pod <pod-name> -n graph-olap-platform
```

### Force-clean all wrapper pods and services

```bash
kubectl delete pods -n graph-olap-platform -l wrapper-type
kubectl delete services -n graph-olap-platform -l wrapper-type
```

---

## View All Images (Single Command)

```bash
echo "--- Deployment images ---" && \
kubectl get deployment ryugraph-wrapper -n graph-olap-platform -o jsonpath='ryugraph: {.spec.template.spec.containers[0].image}{"\n"}' && \
kubectl get deployment falkordb-wrapper -n graph-olap-platform -o jsonpath='falkordb: {.spec.template.spec.containers[0].image}{"\n"}' && \
echo "--- Configmap images (used for dynamic pods) ---" && \
kubectl get configmap control-plane-config -n graph-olap-platform -o jsonpath='ryugraph: {.data.GRAPH_OLAP_WRAPPER_IMAGE}{"\n"}falkordb: {.data.GRAPH_OLAP_FALKORDB_WRAPPER_IMAGE}{"\n"}' && \
echo "--- Control-plane image ---" && \
kubectl get deployment graph-olap-control-plane -n graph-olap-platform -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}' && \
echo "--- Export worker image ---" && \
kubectl get deployment graph-olap-export-worker -n graph-olap-platform -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}' && \
echo "--- Wrapper proxy image ---" && \
kubectl get deployment nginx-wrapper-proxy -n graph-olap-platform -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}' && \
echo "--- Documentation image ---" && \
kubectl get deployment graph-olap-documentation -n graph-olap-platform -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

---

## Restart Components

### What needs restart and when

| Component | Restart when... | Command |
|---|---|---|
| **control-plane** | Configmap changed, new wrapper image tags, DB schema change | `kubectl rollout restart deployment graph-olap-control-plane -n graph-olap-platform` |
| **export-worker** | Starburst config changed, export bug fix | `kubectl rollout restart deployment graph-olap-export-worker -n graph-olap-platform` |
| **wrapper-proxy** | Nginx config changed (rare) | `kubectl rollout restart deployment nginx-wrapper-proxy -n graph-olap-platform` |
| **documentation** | Docs site updated | `kubectl rollout restart deployment graph-olap-documentation -n graph-olap-platform` |
| **wrapper pods** | Stale image, algo bug, stuck instance | `kubectl delete pods -n graph-olap-platform -l wrapper-type` |

### Restart control-plane (most common)

```bash
kubectl rollout restart deployment graph-olap-control-plane -n graph-olap-platform
kubectl rollout status deployment graph-olap-control-plane -n graph-olap-platform --timeout=120s
```

### Restart everything (nuclear option)

```bash
kubectl rollout restart deployment -n graph-olap-platform
kubectl rollout status deployment -n graph-olap-platform --timeout=180s
```

---

## Known Issues

### Algorithm execution denied: role claim missing from token

**Symptom**: Cypher queries work, but PageRank/algo calls fail with `AuthenticationError`.

**Wrapper log**: `"Algorithm execution denied: role claim missing from token"`

**Cause**: Wrapper image was built before the `AlgorithmPermissionDep` removal fix.

**Fix**: Rebuild wrapper images from latest source (which removes `AlgorithmPermissionDep` from `routers/algo.py` and `routers/networkx.py`), push to GCR, update configmap tags, restart control-plane, kill stale wrapper pods.

**Verify**: Check that these files do NOT contain `AlgorithmPermissionDep`:
- `ryugraph-wrapper/src/wrapper/routers/algo.py` (line ~20)
- `ryugraph-wrapper/src/wrapper/routers/networkx.py` (line ~18)
- `falkordb-wrapper/src/wrapper/routers/algo.py` (line ~22)

### Instance timeout (did not start within Ns)

**Symptom**: `provision()` hangs then raises `TimeoutError`.

**Possible causes**:
1. Wrapper image can't pull — check `kubectl describe pod <wrapper-pod> -n graph-olap-platform` for `ImagePullBackOff`
2. Snapshot still building — check export-worker logs: `kubectl logs deploy/graph-olap-export-worker -n graph-olap-platform --tail=200`
3. Starburst down — snapshot SQL can't execute
4. Concurrency limit hit — max wrapper pods reached

### Snapshot failed: BigQuery partition filter

**Symptom**: `Query failed: com.google.cloud.bigquery.BigQueryException` mentioning `image_dt`.

**Cause**: `bis_acct_dh` requires partition filter `WHERE image_dt >= DATE '2020-01-01'`.

**Fix**: Ensure `notebook_setup.py` uses `DATE '2020-01-01'` (ANSI DATE literal, not string `'2020-01-01'`).

### SSL certificate verification failed

**Symptom**: `CERTIFICATE_VERIFY_FAILED` from SDK calls.

**Cause**: HSBC uses self-signed cert via `graph-olap-issuer`.

**Fix**: Set `GRAPH_OLAP_SSL_VERIFY=false` in environment or `notebook_setup.py`.

### polars not installed

**Symptom**: `ImportError: polars is required for to_polars()`.

**Cause**: SDK `query_df()` defaults to polars backend which isn't installed on Dataproc.

**Fix**: `pip install polars` or use `conn.query_df("...", backend="pandas")`.

---

## Nginx Wrapper Proxy Debugging

### Check nginx config

```bash
kubectl exec -n graph-olap-platform deploy/nginx-wrapper-proxy -- cat /etc/nginx/nginx.conf
```

### Nginx access logs (exclude health checks)

```bash
kubectl logs deploy/nginx-wrapper-proxy -n graph-olap-platform --tail=100 | grep -v healthz
```

### Nginx error logs

```bash
kubectl logs deploy/nginx-wrapper-proxy -n graph-olap-platform --tail=100 | grep -iE "error|warn|502|503|504"
```

### Check if nginx can reach a wrapper pod

```bash
# List all running wrapper pods with their slugs
kubectl get pods -n graph-olap-platform -l wrapper-type -o custom-columns='NAME:.metadata.name,SLUG:.metadata.labels.url-slug,STATUS:.status.phase,AGE:.metadata.creationTimestamp'

# Get slug of first wrapper pod
kubectl get pods -n graph-olap-platform -l wrapper-type -o jsonpath='{range .items[0]}{.metadata.labels.url-slug}{"\n"}{end}'

# Test from inside nginx
kubectl exec -n graph-olap-platform deploy/nginx-wrapper-proxy -- curl -v http://wrapper-<URL_SLUG>:8000/healthz
```

### Reading nginx access logs

```
192.168.228.131 - [09/Apr/2026:11:11:45] "POST /wrapper/<slug>/algo/pagerank HTTP/1.1" 401 73 "192.168.212.230:8000" 0.003
│                                          │                                              │   │   │                      │
│                                          │                                              │   │   │                      └─ response time
│                                          │                                              │   │   └─ upstream (wrapper pod IP)
│                                          │                                              │   └─ response body size
│                                          │                                              └─ HTTP status (from wrapper, not nginx)
└─ client IP                               └─ request path
```

- **401 with upstream IP shown** = nginx forwarded correctly, wrapper rejected the request
- **502 Bad Gateway** = nginx can't reach the wrapper pod (pod crashed, not ready, wrong DNS)
- **504 Gateway Timeout** = wrapper pod is alive but not responding in time
- **No upstream IP** = nginx rejected before forwarding (config issue)

### Common nginx issues

| Status | Meaning | Fix |
|---|---|---|
| 401 | Wrapper rejected (auth) — nginx is fine | Fix wrapper image (AlgorithmPermissionDep) |
| 502 | Wrapper pod unreachable | Check pod status: `kubectl get pods -n graph-olap-platform -l wrapper-type` |
| 503 | No upstream available | Wrapper pod hasn't started yet, or DNS not ready |
| 504 | Wrapper timeout | Check wrapper logs for slow queries or stuck operations |

### Reload nginx config without restart

```bash
kubectl exec -n graph-olap-platform deploy/nginx-wrapper-proxy -- nginx -s reload
```

### Full nginx restart

```bash
kubectl rollout restart deployment nginx-wrapper-proxy -n graph-olap-platform
kubectl rollout status deployment nginx-wrapper-proxy -n graph-olap-platform --timeout=60s
```

### Validate nginx config syntax

```bash
# Check for underscore header handling (underscores_in_headers)
kubectl exec -n graph-olap-platform deploy/nginx-wrapper-proxy -- nginx -T | grep underscores

# Full config syntax test
kubectl exec -n graph-olap-platform deploy/nginx-wrapper-proxy -- nginx -T
```

> **Note**: By default nginx silently drops headers with underscores (e.g. `X_Username`).
> If headers use underscores, add `underscores_in_headers on;` in the `http` block.
> Graph OLAP uses hyphens (`X-Username`, `X-User-ID`) so this is normally not an issue.

### Check what headers reach the control-plane

Open in browser:
```
https://control-plane-graph-olap-platform.hsbc-12636856-udlhk-dev.dev.gcp.cloud.hk.hsbc/api/debug/headers
```

**What to look for:**
- `X-Username` / `X-User-ID` — should be present if SDK is calling (absent from browser = normal)
- `cookie: AMToken=...` — HSBC Access Manager token (means request went through AM proxy)
- `x-forwarded-for` — shows client IP chain
- `via: 1.1 google` — confirms GCE ILB is in the path

> **Key insight**: Browser requests carry `AMToken` cookie (HSBC AM auth).
> SDK requests carry `X-Username` header (ADR-104 trust model).
> If `lib-auth` in the wrapper validates AMToken role claims instead of trusting X-Username,
> provisioned personas (e.g. `analyst@e2e.h.local`) will fail because they don't exist in HSBC AM.

### Check headers reaching the wrapper pod

```bash
# See what headers the wrapper receives on algo calls (check wrapper logs)
kubectl logs wrapper-<SLUG> -n graph-olap-platform --tail=50 | grep -i "header\|x-username\|x-user\|authorization\|cookie\|AMToken"
```

---

## Wrapper Pod Inspection

### Check image of a running wrapper pod

```bash
# Replace <SLUG> with the actual slug (e.g. bb05bf48-1e80-4b44-8cdb-5897c6f3fd85)
kubectl get pod wrapper-<SLUG> -n graph-olap-platform -o jsonpath='{.spec.containers[0].image}' && echo
```

### Check if wrapper pod has the AlgorithmPermissionDep bug

```bash
# If this returns lines, the pod has the OLD code (bug)
# If empty, the fix is deployed
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- grep -n "AlgorithmPermissionDep" /app/src/wrapper/routers/algo.py

# Also check networkx router
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- grep -n "AlgorithmPermissionDep" /app/src/wrapper/routers/networkx.py
```

### Check wrapper pod env vars

```bash
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- env | sort
```

### Check wrapper pod logs

```bash
kubectl logs wrapper-<SLUG> -n graph-olap-platform --tail=100
```

### Check wrapper pod labels

```bash
kubectl get pod wrapper-<SLUG> -n graph-olap-platform --show-labels
```

### Check if lib-auth is intercepting requests

```bash
# List auth-related files inside the wrapper pod
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- find /app -path "*auth*" -name "*.py" 2>/dev/null

# Search for "role claim" message (if it exists in lib-auth, not in main source)
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- grep -rn "role claim" /app/ 2>/dev/null
```

### Test wrapper endpoints directly (using python — wrapper pods don't have curl)

```bash
# Health check
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/healthz').read().decode())"

# Cypher query (should work)
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- python3 -c "
import urllib.request, json
req = urllib.request.Request('http://localhost:8000/query', method='POST',
    headers={'Content-Type': 'application/json', 'X-User-ID': 'analyst@e2e.h.local', 'X-Username': 'analyst@e2e.h.local'},
    data=json.dumps({'query': 'MATCH (n) RETURN count(n) AS total'}).encode())
try:
    print(urllib.request.urlopen(req).read().decode())
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()}')
"

# Algo call (this is what fails with 401)
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- python3 -c "
import urllib.request, json
req = urllib.request.Request('http://localhost:8000/algo/pagerank', method='POST',
    headers={'Content-Type': 'application/json', 'X-User-ID': 'analyst@e2e.h.local', 'X-Username': 'analyst@e2e.h.local'},
    data=json.dumps({'node_label': 'Customer', 'property_name': 'test_pr', 'edge_type': 'SHARES_ACCOUNT'}).encode())
try:
    print(urllib.request.urlopen(req).read().decode())
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()}')
"
```

> **Note**: Wrapper pods are distroless/minimal — no `curl`, `wget`, or shell utilities.
> Use `python3` with `urllib` for all HTTP testing from inside wrapper pods.

---

## Full Debug Sequence (copy-paste ready)

Replace `<SLUG>` with the actual slug (e.g. `bb05bf48-1e80-4b44-8cdb-5897c6f3fd85`).

```bash
# 1. What image is running?
kubectl get pod wrapper-<SLUG> -n graph-olap-platform -o jsonpath='{.spec.containers[0].image}' && echo

# 2. Is AlgorithmPermissionDep in the running code? (empty = fixed, lines = bug)
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- grep -n "AlgorithmPermissionDep" /app/src/wrapper/routers/algo.py

# 3. Where does "role claim" error come from?
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- grep -rn "role claim" /app/

# 4. Health check (should return {"status":"healthy"})
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/healthz').read().decode())"

# 5. Test Cypher query (should work)
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- python3 -c "
import urllib.request, json
req = urllib.request.Request('http://localhost:8000/query', method='POST',
    headers={'Content-Type': 'application/json', 'X-User-ID': 'analyst@e2e.h.local', 'X-Username': 'analyst@e2e.h.local'},
    data=json.dumps({'query': 'MATCH (n) RETURN count(n) AS total'}).encode())
try:
    print(urllib.request.urlopen(req).read().decode())
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()}')
"

# 6. Test algo call (this is what fails with 401)
kubectl exec wrapper-<SLUG> -n graph-olap-platform -- python3 -c "
import urllib.request, json
req = urllib.request.Request('http://localhost:8000/algo/pagerank', method='POST',
    headers={'Content-Type': 'application/json', 'X-User-ID': 'analyst@e2e.h.local', 'X-Username': 'analyst@e2e.h.local'},
    data=json.dumps({'node_label': 'Customer', 'property_name': 'test_pr', 'edge_type': 'SHARES_ACCOUNT'}).encode())
try:
    print(urllib.request.urlopen(req).read().decode())
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()}')
"
```
