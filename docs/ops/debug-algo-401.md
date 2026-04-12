# Debug: Algorithm Errors — Extension Not Loaded

The 401 auth issue (AlgorithmPermissionDep) is **resolved**. The current issue is:

```
Catalog exception: function page_rank is not defined. This function exists in the ALGO extension.
You can install and load the extension by running 'INSTALL ALGO; LOAD EXTENSION ALGO;'.
```

**Root cause:** The ALGO extension binary is not loaded in the running wrapper pod. The wrapper
code (`LOAD algo` at startup) failed silently, so native algorithms (`page_rank`, `wcc`, `scc`,
`louvain`, `kcore`) are unavailable.

**Key observation from GKE Console (2026-04-09):**
- `ryugraph-wrapper` Deployment = **0/0 pods**
- `falkordb-wrapper` Deployment = **0/0 pods**
- Actual running wrapper = standalone Pod `wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93`
- This standalone Pod is likely running an **old image** without the baked algo extension (ADR-138)

---

## Step 1 — What image is the wrapper pod running?

```bash
kubectl get pod wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform -o jsonpath='{.spec.containers[0].image}' && echo
```

Expected (ADR-138 fix): image tag should be `hash-16c3e98295fe` or newer.
If the tag is older, the algo extension binary is not baked in.

## Step 2 — Did LOAD algo succeed at startup?

```bash
kubectl logs wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform | grep -i "algo extension"
```

If grep doesn't work or returns nothing, try these alternatives:

```bash
kubectl logs wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform | grep algo
```

```bash
kubectl logs wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform | head -50
```

```bash
kubectl logs wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform
```

Look for these log lines near the top (startup):

- `"Loading algo extension from local cache"` → code has ADR-138 changes
- `"Algo extension loaded successfully"` → extension is loaded, problem is elsewhere (unlikely)
- `"Failed to load algo extension"` → binary not at expected path, confirms old image
- No "algo" lines at all → pod is running code that predates ADR-138 entirely

## Step 3 — Check if the extension binary exists in the pod

```bash
kubectl exec wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform -- ls -la /root/.ryu/extension/25.9.0/linux_amd64/algo/libalgo.ryu_extension 2>&1
```

- File exists → extension should load; check startup logs for why `LOAD algo` failed
- `No such file or directory` → image does not have the baked extension (needs rebuild/redeploy)

## Step 4 — Check if it's at the wrong version path

```bash
kubectl exec wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform -- find /root/.ryu -name "*.ryu_extension" 2>/dev/null
```

If the binary is under `25.9.2/` instead of `25.9.0/`, the Earthfile used `ryugraph.__version__`
instead of the hardcoded native library version. See ADR-138 for details.

## Step 5 — Health check (should return 200)

```bash
kubectl exec wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform -- python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/healthz').read().decode())"
```

## Step 6 — Test Cypher query (should work)

```bash
kubectl exec wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform -- python3 -c "
import urllib.request, json
req = urllib.request.Request('http://localhost:8000/query', method='POST',
    headers={'Content-Type': 'application/json', 'X-User-ID': 'analyst@e2e.h.local', 'X-Username': 'analyst@e2e.h.local'},
    data=json.dumps({'query': 'MATCH (n) RETURN count(n) AS total'}).encode())
try:
    print(urllib.request.urlopen(req).read().decode())
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()}')
"
```

## Step 7 — Test algo PageRank call

```bash
kubectl exec wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform -- python3 -c "
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

## Step 8 — Check full startup logs

```bash
kubectl logs wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform | head -30
```

## Step 9 — Watch control-plane logs (live)

Follow logs to see wrapper spawning, orchestration, errors in real time:

```bash
kubectl logs -f deployment/graph-olap-control-plane -n graph-olap-platform -c control-plane --tail=50
```

Search for specific events:

```bash
kubectl logs deployment/graph-olap-control-plane -n graph-olap-platform -c control-plane --tail=200 | grep -i "spawn\|wrapper\|error\|failed\|image"
```

Check orchestration loop and GCS client status:

```bash
kubectl logs deployment/graph-olap-control-plane -n graph-olap-platform -c control-plane --tail=200 | grep -i "orchestration\|gcs\|lifecycle"
```

---

## Fix options

### Option A — Force control-plane to spawn wrapper with latest image (recommended)

The control-plane spawns wrapper pods using the image from its configmap
(`GRAPH_OLAP_WRAPPER_IMAGE`). If the configmap was updated but control-plane pods
are still running with the old cached value, restart them:

1. Check what image the configmap has vs what the wrapper pod is running:
   ```bash
   kubectl get configmap control-plane-config -n graph-olap-platform -o jsonpath='{.data.GRAPH_OLAP_WRAPPER_IMAGE}' && echo
   kubectl get pod wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform -o jsonpath='{.spec.containers[0].image}' && echo
   ```

2. If they differ, restart control-plane so it picks up the new configmap:
   ```bash
   kubectl rollout restart deployment graph-olap-control-plane -n graph-olap-platform
   ```

3. Delete the old wrapper pod so control-plane spawns a new one with the latest image:
   ```bash
   kubectl delete pod wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform
   ```

4. Wait for new wrapper pod to come up, then verify image and algo extension:
   ```bash
   kubectl get pods -n graph-olap-platform
   kubectl logs <new-wrapper-pod-name> -n graph-olap-platform | grep algo
   ```

### Option B — Manually load the extension in the running pod (temporary workaround)

If you need algo working immediately without redeploying, you can try loading from the
extension server (if it exists) by exec'ing into the pod. This is NOT a permanent fix.

### Note on image versions

The algo extension binary is only present in images built from the updated Dockerfile
that includes `COPY vendor/libalgo.ryu_extension`. If HSBC Jenkins has not yet rebuilt
from the updated graphsol Dockerfile, even the latest image tag will not have the binary.
HSBC must rebuild the ryugraph-wrapper image from the updated code before the fix works.

---

## What the results mean

| Step | Result | Meaning |
|------|--------|---------|
| 1 | Old image tag | Pod predates ADR-138. Extension not baked in. Redeploy. |
| 1 | `hash-16c3e98295fe` | Correct image. Check steps 2-4 for why LOAD failed. |
| 2 | "loaded successfully" | Extension is loaded — something else is wrong (check step 7). |
| 2 | "Failed to load" | Binary missing or wrong path. Check steps 3-4. |
| 3 | File exists | Binary is there but LOAD failed — check Ryugraph version mismatch. |
| 3 | No such file | Image doesn't have baked extension. Rebuild needed. |
| 4 | Under `25.9.2/` | Wrong path — Earthfile used `__version__` not native lib version. |
| 4 | Empty | No extension binary anywhere in the image. |
| 6 | Query works | Wrapper is alive, Cypher path is fine. |
| 7 | page_rank error | Confirms extension not loaded. |
| 7 | Works | Extension is loaded and algo works. |

---

## Debug: 503 "unconditional drop overload" on GET /api/mappings

**This is NOT our code.** The phrase "unconditional drop overload" does not appear anywhere in
our codebase. It is Envoy's overload manager terminology — something envoy-based in HSBC's
request path is shedding load before the request reaches our control-plane pod.

Likely culprits:
- Istio sidecar on the control-plane pod
- HSBC internal API gateway / WAF wrapping envoy
- Envoy-based ingress controller (Contour, Gloo, Emissary) instead of nginx-ingress

### Step 1 — Did the request reach our control-plane?

```bash
kubectl logs graph-olap-control-plane-6994b4f889-qvrdt -n graph-olap-platform --tail=100 | grep -i "mappings\|503\|error"
```

```bash
kubectl logs graph-olap-control-plane-6994b4f889-vlx2k -n graph-olap-platform --tail=100 | grep -i "mappings\|503\|error"
```

If `/api/mappings` does NOT appear in the logs around the error timestamp, the request was
dropped before it reached our pod. Confirms it's a proxy/mesh issue, not ours.

### Step 2 — What ingress/mesh is deployed?

```bash
kubectl get pods -A -l app.kubernetes.io/name=istio-proxy
```

```bash
kubectl get ing -A
```

If Istio or an envoy-based ingress is present, that's the source of the 503.

### Step 3 — Is control-plane actually overloaded?

```bash
kubectl top pod -n graph-olap-platform
```

If resource usage is high, the overload manager is doing its job — fix is raising replica
count or resource limits in the HSBC values file.

### Step 4 — Is it transient or persistent?

- Single 503 under load that succeeds on retry = transient pressure
- Persistent 503 = misconfigured threshold or stuck/unhealthy backend

**Action:** This is an HSBC infra issue. Share findings with HSBC operator team.

---

## Pre-deploy validation — verify control-plane service URL

Before deploying a new wrapper image, validate that the in-cluster URL
`http://control-plane-svc.graph-olap-platform.svc.cluster.local:8080`
is correct. Wrapper pods use this to talk back to control-plane.

### Step 1 — Check the service name exists

```bash
kubectl get svc -n graph-olap-platform | grep control-plane
```

Should show `control-plane-svc`. If the name is different, the URL in
`k8s_service.py` needs updating before deploying.

### Step 2 — Test DNS resolution from inside a pod

```bash
kubectl exec graph-olap-control-plane-6994b4f889-bjb8x -n graph-olap-platform -c control-plane -- python3 -c "import socket; print(socket.getaddrinfo('control-plane-svc.graph-olap-platform.svc.cluster.local', 8080)[0][4])"
```

If it resolves to an IP — URL is correct. If it fails — wrong service name.

### Step 3 — Check what the current wrapper pod has

```bash
kubectl exec wrapper-ee9e951d-d5c7-44f6-a667-3c1426398d93 -n graph-olap-platform -- env | grep CONTROL_PLANE
```

- `http://control-plane-svc.graph-olap-platform.svc.cluster.local:8080` = new code
- `http://graph-olap-control-plane:8080` = old code

---

## Background

- **ADR-138** (Bake Algo Extension Into Wrapper Image) eliminated the `extension-server` pod
  dependency by baking `libalgo.ryu_extension` into the wrapper Docker image at build time.
- The correct cache path is `/root/.ryu/extension/25.9.0/linux_amd64/algo/` — uses the native
  library version (25.9.0), NOT the Python wheel version (25.9.2).
- The `falkordb-wrapper` and `ryugraph-wrapper` Deployments at 0/0 replicas are likely leftover
  from before HSBC's control-plane started managing wrapper pods directly as standalone Pods.
