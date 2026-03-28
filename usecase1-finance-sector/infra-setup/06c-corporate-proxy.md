# Corporate Proxy Configuration

If deploying behind a corporate proxy (common in finance/enterprise environments), these settings are required for outbound connectivity.

## What Needs Proxy Access

| Component | Outbound To | Why |
|-----------|------------|-----|
| Export Worker | Starburst Galaxy | SQL queries for data export |
| Control Plane | Starburst (schema cache) | Schema metadata refresh |
| Jupyter/SDK | Control Plane | API calls from analyst notebooks |
| pip (install) | PyPI | Installing SDK / httpx packages |

## 1. Kubernetes Proxy Configuration

Set proxy environment variables on deployments that need outbound access:

```yaml
# Add to control-plane and export-worker deployments
env:
  - name: HTTP_PROXY
    value: "http://<proxy-host>:<port>"
  - name: HTTPS_PROXY
    value: "http://<proxy-host>:<port>"
  - name: NO_PROXY
    value: "localhost,127.0.0.1,.svc.cluster.local,.graph-olap,.internal"
```

`NO_PROXY` is critical — internal Kubernetes traffic (pod-to-pod, pod-to-service) must bypass the proxy.

## 2. Jupyter/Dataproc Notebook Proxy

When running tests from Jupyter notebooks on Dataproc or a connected VM:

```python
import os
os.environ['https_proxy'] = 'http://<proxy-host>:<port>'
os.environ['http_proxy'] = 'http://<proxy-host>:<port>'
```

For pip installs, strip the proxy (PyPI may need direct access or a different proxy):

```python
import subprocess
clean_env = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower()}
subprocess.run(["pip", "install", "--no-cache-dir", "httpx", "-q"], capture_output=True, env=clean_env)
```

## 3. Docker Build Proxy

If building images behind a proxy:

```bash
docker build \
    --build-arg HTTP_PROXY=http://<proxy-host>:<port> \
    --build-arg HTTPS_PROXY=http://<proxy-host>:<port> \
    --build-arg NO_PROXY=localhost,127.0.0.1 \
    -t control-plane:latest .
```

## 4. Helm Values Override

```yaml
# values-proxy.yaml
controlPlane:
  env:
    HTTP_PROXY: "http://<proxy-host>:<port>"
    HTTPS_PROXY: "http://<proxy-host>:<port>"
    NO_PROXY: "localhost,127.0.0.1,.svc.cluster.local"

exportWorker:
  env:
    HTTP_PROXY: "http://<proxy-host>:<port>"
    HTTPS_PROXY: "http://<proxy-host>:<port>"
    NO_PROXY: "localhost,127.0.0.1,.svc.cluster.local"
```

```bash
helm upgrade graph-olap ./helm -f values-proxy.yaml
```

## 5. Verification

```bash
# Test outbound connectivity from control plane pod
kubectl exec -n graph-olap deployment/control-plane -c control-plane -- \
    python -c "import httpx; print(httpx.get('https://httpbin.org/ip').json())"

# Test Starburst connectivity
kubectl exec -n graph-olap deployment/control-plane -c control-plane -- \
    python -c "import httpx; print(httpx.get('https://<your-starburst-url>/v1/info').status_code)"
```

## Common Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| `ConnectionError` from pods | Proxy not set on deployment | Add HTTP_PROXY/HTTPS_PROXY env vars |
| Internal services unreachable | Proxy intercepting cluster traffic | Add `.svc.cluster.local` to NO_PROXY |
| pip install fails | Proxy blocking PyPI | Strip proxy for pip or use private PyPI |
| SSL errors through proxy | Proxy doing TLS inspection | Set `GRAPH_OLAP_VERIFY_SSL=false` or add CA cert |
