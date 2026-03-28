# Smoke Tests

Quick validation commands to verify each component is working after deployment.

## 1. Health Checks

```bash
# Control plane health
curl -s https://<your-control-plane-url>/health | jq .
# Expected: {"status": "healthy"}

# Control plane readiness
curl -s https://<your-control-plane-url>/ready | jq .
# Expected: {"status": "ready", "database": "connected"}
```

## 2. API Smoke Test

```bash
API_URL="https://<your-control-plane-url>"

# List mappings (should return empty or existing)
curl -s "$API_URL/api/mappings" \
    -H "X-Username: test-user" \
    -H "X-User-Role: admin" \
    -H "X-Use-Case-Id: <your-use-case-id>" | jq '.data | length'

# List instances
curl -s "$API_URL/api/instances" \
    -H "X-Username: test-user" \
    -H "X-User-Role: admin" \
    -H "X-Use-Case-Id: <your-use-case-id>" | jq '.data | length'
```

## 3. Create Mapping + Instance (Full Lifecycle)

```bash
API_URL="https://<your-control-plane-url>"
HEADERS='-H "Content-Type: application/json" -H "X-Username: test-user" -H "X-User-Role: admin" -H "X-Use-Case-Id: <your-use-case-id>"'

# Create mapping
MAPPING_ID=$(curl -s -X POST "$API_URL/api/mappings" $HEADERS \
    -d '{
        "name": "smoke-test",
        "description": "Smoke test",
        "node_definitions": [{
            "label": "TestNode",
            "sql": "SELECT 1 as id, '\''test'\'' as name",
            "primary_key": {"name": "id", "type": "INT64"},
            "properties": [{"name": "name", "type": "STRING"}]
        }],
        "edge_definitions": []
    }' | jq -r '.data.id')
echo "Mapping: $MAPPING_ID"

# Create instance
INSTANCE_ID=$(curl -s -X POST "$API_URL/api/instances" $HEADERS \
    -d "{\"mapping_id\": $MAPPING_ID, \"name\": \"smoke-test\", \"wrapper_type\": \"falkordb\"}" \
    | jq -r '.data.id')
echo "Instance: $INSTANCE_ID"

# Poll until running
for i in $(seq 1 30); do
    STATUS=$(curl -s "$API_URL/api/instances/$INSTANCE_ID" $HEADERS | jq -r '.data.status')
    echo "[$i] $STATUS"
    [ "$STATUS" = "running" ] && break
    sleep 3
done

# Cleanup
curl -s -X DELETE "$API_URL/api/instances/$INSTANCE_ID" $HEADERS
curl -s -X DELETE "$API_URL/api/mappings/$MAPPING_ID" $HEADERS
echo "Cleaned up"
```

## 4. Kubernetes Health

```bash
# All pods running
kubectl get pods -n graph-olap

# Control plane logs (last 20 lines)
kubectl logs -n graph-olap -l app=control-plane -c control-plane --tail=20

# Check for errors
kubectl logs -n graph-olap -l app=control-plane -c control-plane | grep -i error | tail -5

# Export worker status
kubectl get deployment export-worker -n graph-olap

# Ingress status
kubectl get ingress -n graph-olap
```

## 5. Wrapper Pod Verification

```bash
# Watch wrapper pods spawn/terminate
kubectl get pods -n graph-olap -l wrapper-type -w

# Check wrapper logs
kubectl logs -n graph-olap -l wrapper-type --tail=50

# Check wrapper services
kubectl get svc -n graph-olap | grep wrapper
```

## Quick Pass/Fail Checklist

```
[ ] /health returns 200
[ ] /api/mappings returns 200
[ ] Mapping creation returns ID
[ ] Instance reaches "running" status
[ ] Wrapper pod appears in kubectl
[ ] Cleanup deletes instance and mapping
[ ] No error logs in control plane
```
