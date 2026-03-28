# Testing and Validation

This guide covers testing the deployed platform using proven scripts. Two approaches:

1. **API One-Go Test** — single Jupyter cell, raw HTTP, tests full lifecycle
2. **SDK One-Go Test** — single Jupyter cell, Python SDK, tests full lifecycle

Both scripts are self-contained and run from a Jupyter notebook on a connected cluster (e.g., Dataproc, JupyterHub).

## 1. Pre-Deployment Checks

Before running E2E tests, verify infrastructure is healthy:

```bash
# Verify all pods are running
kubectl get pods -n graph-olap

# Check control plane health
kubectl run test-health --rm -it --image=curlimages/curl --restart=Never -- \
    curl -s http://control-plane.graph-olap.svc.cluster.local:8080/health

# Check database connectivity
kubectl logs -n graph-olap -l app=control-plane -c control-plane --tail=20 | grep -i "database"

# Check export worker
kubectl get deployment export-worker -n graph-olap

# Verify GCS access
kubectl run test-gcs --rm -it \
    --image=google/cloud-sdk:slim \
    --serviceaccount=control-plane \
    --namespace=graph-olap \
    -- gsutil ls gs://<your-bucket>/
```

## 2. API One-Go Test (Recommended First Test)

Paste into a single Jupyter cell. Tests: health, mapping creation, instance creation, Cypher queries, visualization, cleanup.

**No SDK installation required** — uses `httpx` only.

```python
import os, time, json, subprocess

# Install httpx (proxy stripped so pip can reach PyPI)
clean_env = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower()}
subprocess.run(["pip", "install", "--no-cache-dir", "httpx", "-q"], capture_output=True, env=clean_env)

# === CONFIGURATION — UPDATE THESE ===
API_URL = "https://<your-control-plane-url>"
PROXY = "http://<proxy-host>:<port>"       # Remove if no proxy
USE_CASE_ID = "<your-use-case-id>"
CATALOG = "<your-catalog>"
SCHEMA = "<your-schema>"
TABLE = "<your-customer-table>"

os.environ['http_proxy'] = PROXY
os.environ['https_proxy'] = PROXY

import httpx
HEADERS = {"Content-Type": "application/json", "X-Username": "test-user", "X-User-Role": "admin", "X-Use-Case-Id": USE_CASE_ID}
client = httpx.Client(base_url=API_URL, headers=HEADERS, verify=False, timeout=30, proxy=PROXY)

# === HEALTH ===
print("1. Health:", client.get("/health").json())

# === CREATE MAPPING ===
r = client.post("/api/mappings", json={
    "name": "validation-test",
    "description": "Deployment validation test",
    "node_definitions": [{
        "label": "Customer",
        "sql": f'SELECT DISTINCT customer_id, customer_name, sector FROM "{CATALOG}"."{SCHEMA}"."{TABLE}" LIMIT 10',
        "primary_key": {"name": "customer_id", "type": "INT64"},
        "properties": [
            {"name": "customer_name", "type": "STRING"},
            {"name": "sector", "type": "STRING"}
        ]
    }],
    "edge_definitions": []
})
MAPPING_ID = r.json()["data"]["id"]
print(f"2. Mapping created: id={MAPPING_ID}")

# === CREATE INSTANCE ===
r = client.post("/api/instances", json={"mapping_id": MAPPING_ID, "name": "validation-instance", "wrapper_type": "falkordb"})
INSTANCE_ID = r.json()["data"]["id"]
print(f"3. Instance created: id={INSTANCE_ID}")

# === POLL UNTIL RUNNING ===
status = "unknown"
SLUG = ""
for i in range(30):
    r = client.get(f"/api/instances/{INSTANCE_ID}")
    inst = r.json()["data"]
    status = inst["status"]
    print(f"   [{i}] {status}")
    if status == "running":
        SLUG = inst["instance_url"].split("/wrapper/")[-1]
        print(f"   Running! Waiting 45s for wrapper...")
        time.sleep(45)
        break
    elif status == "failed":
        print(f"   FAILED: {inst.get('error_message')}")
        break
    time.sleep(3)

# === QUERY ===
if status == "running":
    r = client.post(f"/wrapper/{SLUG}/query", json={"query": "MATCH (n:Customer) RETURN count(n) as total"})
    if r.status_code == 200:
        print(f"4. Customer count: {r.json()['rows'][0][0]}")

        r = client.post(f"/wrapper/{SLUG}/query", json={"query": "MATCH (n:Customer) RETURN n.customer_name, n.sector LIMIT 10"})
        print(f"5. Sample data:")
        for row in r.json()["rows"]:
            print(f"   {row}")

        print(f"6. Schema:")
        print(json.dumps(client.get(f"/wrapper/{SLUG}/schema").json(), indent=2))

    # === CLEANUP ===
    client.delete(f"/api/instances/{INSTANCE_ID}")
    client.delete(f"/api/mappings/{MAPPING_ID}")
    print(f"\n7. Cleaned up: instance {INSTANCE_ID}, mapping {MAPPING_ID}")

print("\n" + "=" * 50)
print("VALIDATION: PASS" if status == "running" else "VALIDATION: FAIL")
print("=" * 50)
```

## 3. SDK One-Go Test

Same test using the Python SDK. Requires `graph-olap-sdk` installed.

See: [../scripts/sdk-onego.md](../scripts/sdk-onego.md)

## 4. Full E2E Test Suite

Run all 17 test notebooks via papermill for comprehensive validation.

See: [../scripts/run-all-e2e.md](../scripts/run-all-e2e.md)

## 5. Post-Test Verification

After running tests, verify cleanup:

```bash
# Check no orphaned wrapper pods
kubectl get pods -n graph-olap -l wrapper-type

# Check no orphaned services
kubectl get svc -n graph-olap | grep wrapper

# Check instance count in control plane
curl -s "$API_URL/api/instances" \
    -H "X-Username: test-user" \
    -H "X-User-Role: admin" | jq '.data | length'
```

## Validation Checklist

```
[ ] Control plane /health returns healthy
[ ] Mapping creation succeeds
[ ] Instance creation succeeds (status -> running)
[ ] Wrapper pod spawns and becomes ready
[ ] Cypher query returns data
[ ] Schema endpoint returns node/edge info
[ ] Instance deletion cleans up pod
[ ] Mapping deletion succeeds
[ ] No orphaned resources after cleanup
```
