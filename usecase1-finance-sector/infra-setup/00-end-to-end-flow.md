# End-to-End Platform Flow

This document describes the complete data flow through the Graph OLAP platform - from user request to query execution.

## Complete Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    ENTERPRISE NETWORK                                            │
│                                                                                                  │
│  ┌──────────────┐                                                                               │
│  │    Client    │                                                                               │
│  │  (Browser/   │                                                                               │
│  │   SDK/CLI)   │                                                                               │
│  └──────┬───────┘                                                                               │
│         │                                                                                        │
│         │ HTTPS + JWT Token                                                                      │
│         ▼                                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              GKE CLUSTER (Private)                                        │   │
│  │                                                                                           │   │
│  │   ┌─────────────────────────────────────────────────────────────────────────────────┐    │   │
│  │   │                        INTERNAL LOAD BALANCER                                    │    │   │
│  │   │                    (GCE Internal / NEG-based)                                    │    │   │
│  │   └────────────────────────────────┬────────────────────────────────────────────────┘    │   │
│  │                                    │                                                      │   │
│  │                                    ▼                                                      │   │
│  │   ┌────────────────────────────────────────────────────────────────┐                     │   │
│  │   │                      CONTROL PLANE POD                          │                     │   │
│  │   │  ┌──────────────────┐    ┌─────────────────────────────────┐   │                     │   │
│  │   │  │   FastAPI App    │    │     Cloud SQL Proxy Sidecar     │   │                     │   │
│  │   │  │                  │    │                                 │   │                     │   │
│  │   │  │  • JWT Validation│    │  • IAM Auth to Cloud SQL        │   │                     │   │
│  │   │  │  • API Endpoints │    │  • Encrypted Connection         │   │                     │   │
│  │   │  │  • K8s Pod Mgmt  │    │  • localhost:5432               │   │                     │   │
│  │   │  │  • Schema Cache  │────│                                 │   │                     │   │
│  │   │  └──────────────────┘    └─────────────────────────────────┘   │                     │   │
│  │   └─────────────┬──────────────────────────────────────────────────┘                     │   │
│  │                 │                                                                         │   │
│  │    ┌────────────┼────────────────────────────────────────────────────────────┐           │   │
│  │    │            │                                                             │           │   │
│  │    ▼            ▼                                                             ▼           │   │
│  │   ┌────────────────────┐    ┌─────────────────────┐    ┌─────────────────────────────┐   │   │
│  │   │   EXPORT WORKER    │    │   WRAPPER PODS      │    │   KUBERNETES API            │   │   │
│  │   │                    │    │   (Dynamic)         │    │                             │   │   │
│  │   │  • Poll for jobs   │    │  ┌───────┐ ┌───────┐│    │  • Create/Delete Pods       │   │   │
│  │   │  • Query Starburst │    │  │Ryugraph│ │FalkorDB│    │  • Create/Delete Services   │   │   │
│  │   │  • Export to GCS   │    │  │Wrapper │ │Wrapper ││    │  • Watch Pod Status         │   │   │
│  │   │  • Update status   │    │  └───────┘ └───────┘│    │                             │   │   │
│  │   └─────────┬──────────┘    └──────────┬──────────┘    └─────────────────────────────┘   │   │
│  │             │                          │                                                  │   │
│  └─────────────┼──────────────────────────┼──────────────────────────────────────────────────┘   │
│                │                          │                                                      │
└────────────────┼──────────────────────────┼──────────────────────────────────────────────────────┘
                 │                          │
     ┌───────────┼──────────────────────────┼───────────────────────────────────────┐
     │           │                          │                                        │
     │           ▼                          ▼                                        │
     │  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐   │
     │  │    STARBURST    │        │  CLOUD STORAGE  │        │    CLOUD SQL    │   │
     │  │    (Trino)      │        │     (GCS)       │        │   (PostgreSQL)  │   │
     │  │                 │        │                 │        │                 │   │
     │  │ • Query Engine  │───────▶│ • Snapshots     │◀───────│ • Instance State│   │
     │  │ • BigQuery Conn │        │ • Parquet Files │        │ • Mappings      │   │
     │  │ • Role-Based    │        │ • Export Data   │        │ • Export Jobs   │   │
     │  │   Access        │        │                 │        │ • User Data     │   │
     │  └─────────────────┘        └─────────────────┘        └─────────────────┘   │
     │                                                                               │
     │                           GCP SERVICES                                        │
     └───────────────────────────────────────────────────────────────────────────────┘
```

## Flow 1: Create Mapping (Schema Definition)

User defines how to map relational data to graph structure.

```
┌─────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Client │────▶│ Control Plane │────▶│   Starburst   │────▶│   Cloud SQL   │
└─────────┘     └───────────────┘     └───────────────┘     └───────────────┘
     │                 │                     │                     │
     │  POST /api/mappings                   │                     │
     │  {                                    │                     │
     │    "name": "movie_graph",             │                     │
     │    "nodes": [...],                    │                     │
     │    "edges": [...]                     │                     │
     │  }                                    │                     │
     │                 │                     │                     │
     │                 │  Validate SQL       │                     │
     │                 │  DESCRIBE (query)   │                     │
     │                 │────────────────────▶│                     │
     │                 │                     │                     │
     │                 │  Column metadata    │                     │
     │                 │◀────────────────────│                     │
     │                 │                     │                     │
     │                 │  Store mapping      │                     │
     │                 │─────────────────────────────────────────▶│
     │                 │                     │                     │
     │  201 Created    │                     │                     │
     │  {"id": 1}      │                     │                     │
     │◀────────────────│                     │                     │
```

### Curl Example

```bash
# Create a mapping
curl -X POST "http://control-plane:8080/api/mappings" \
    -H "Content-Type: application/json" \
    -H "X-Username: analyst@example.com" \
    -H "X-User-Role: analyst" \
    -d '{
        "name": "movie_graph",
        "starburst_catalog": "bigquery",
        "starburst_schema": "movies",
        "nodes": [
            {
                "label": "Movie",
                "sql": "SELECT id, title, year FROM movies",
                "id_column": "id"
            },
            {
                "label": "Actor",
                "sql": "SELECT id, name FROM actors",
                "id_column": "id"
            }
        ],
        "edges": [
            {
                "type": "ACTED_IN",
                "sql": "SELECT actor_id, movie_id FROM cast",
                "source_column": "actor_id",
                "target_column": "movie_id",
                "source_label": "Actor",
                "target_label": "Movie"
            }
        ]
    }'
```

---

## Flow 2: Create Snapshot (Data Export)

Export data from Starburst to GCS as Parquet files.

```
┌─────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌─────────────┐
│  Client │──▶│ Control Plane │──▶│   Cloud SQL   │   │ Export Worker │──▶│  Starburst  │
└─────────┘   └───────────────┘   └───────────────┘   └───────────────┘   └─────────────┘
     │               │                    │                   │                   │
     │  POST /api/snapshots               │                   │                   │
     │  {"mapping_id": 1}                 │                   │                   │
     │               │                    │                   │                   │
     │               │  Create snapshot   │                   │                   │
     │               │  Create export job │                   │                   │
     │               │───────────────────▶│                   │                   │
     │               │                    │                   │                   │
     │  202 Accepted │                    │                   │                   │
     │◀──────────────│                    │                   │                   │
     │               │                    │                   │                   │
     │               │                    │  Poll for jobs    │                   │
     │               │                    │◀──────────────────│                   │
     │               │                    │                   │                   │
     │               │                    │  Claim job        │                   │
     │               │                    │──────────────────▶│                   │
     │               │                    │                   │                   │
     │               │                    │                   │  SET ROLE         │
     │               │                    │                   │─────────────────▶│
     │               │                    │                   │                   │
     │               │                    │                   │  UNLOAD query     │
     │               │                    │                   │  (or direct       │
     │               │                    │                   │   PyArrow export) │
     │               │                    │                   │─────────────────▶│
     │               │                    │                   │                   │
     │               │                    │                   │  Write Parquet    │
     │               │                    │                   │  to GCS           │
     │               │                    │                   │───────┐           │
     │               │                    │                   │       │           │
     │               │                    │                   │       ▼           │
     │               │                    │                   │  ┌─────────┐      │
     │               │                    │                   │  │   GCS   │      │
     │               │                    │                   │  └─────────┘      │
     │               │                    │                   │                   │
     │               │                    │  Update job       │                   │
     │               │                    │  status=completed │                   │
     │               │                    │◀──────────────────│                   │
     │               │                    │                   │                   │
     │               │                    │  Update snapshot  │                   │
     │               │                    │  status=ready     │                   │
```

### Curl Example

```bash
# Create snapshot from mapping
curl -X POST "http://control-plane:8080/api/snapshots" \
    -H "Content-Type: application/json" \
    -H "X-Username: analyst@example.com" \
    -H "X-User-Role: analyst" \
    -d '{"mapping_id": 1}'

# Response: {"id": 100, "status": "pending"}

# Poll for snapshot status
curl "http://control-plane:8080/api/snapshots/100" \
    -H "X-Username: analyst@example.com" \
    -H "X-User-Role: analyst"

# Response when ready: {"id": 100, "status": "ready", "gcs_path": "gs://bucket/snapshots/100/"}
```

### What Happens in Starburst

```sql
-- 1. Export Worker sets role
SET ROLE data_analyst_role;

-- 2. Export Worker runs UNLOAD query (or direct SELECT with PyArrow)
SELECT * FROM TABLE(
    system.unload(
        input => TABLE(
            SELECT id, title, year FROM movies
        ),
        location => 'gs://bucket/snapshots/100/nodes/Movie/',
        format => 'PARQUET',
        compression => 'SNAPPY'
    )
);

-- 3. Repeat for each node type and edge type
```

### GCS Output Structure

```
gs://bucket/snapshots/100/
├── nodes/
│   ├── Movie/
│   │   └── data.parquet
│   └── Actor/
│       └── data.parquet
├── edges/
│   └── ACTED_IN/
│       └── data.parquet
└── metadata.json
```

---

## Flow 3: Create Instance (Spawn Wrapper Pod)

Create a running graph instance from a snapshot.

```
┌─────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌─────────────┐
│  Client │──▶│ Control Plane │──▶│ Kubernetes API│──▶│  Wrapper Pod  │──▶│     GCS     │
└─────────┘   └───────────────┘   └───────────────┘   └───────────────┘   └─────────────┘
     │               │                    │                   │                   │
     │  POST /api/instances               │                   │                   │
     │  {"snapshot_id": 100}              │                   │                   │
     │               │                    │                   │                   │
     │               │  Create Pod spec   │                   │                   │
     │               │  with env vars:    │                   │                   │
     │               │  - SNAPSHOT_ID     │                   │                   │
     │               │  - GCS_PATH        │                   │                   │
     │               │  - INSTANCE_URL    │                   │                   │
     │               │───────────────────▶│                   │                   │
     │               │                    │                   │                   │
     │               │  Create Service    │                   │                   │
     │               │───────────────────▶│                   │                   │
     │               │                    │                   │                   │
     │  202 Accepted │                    │                   │                   │
     │  {                                 │                   │                   │
     │    "id": 42,                       │                   │                   │
     │    "status": "pending"             │                   │                   │
     │  }                                 │                   │                   │
     │◀──────────────│                    │                   │                   │
     │               │                    │                   │                   │
     │               │                    │  Pod starts       │                   │
     │               │                    │──────────────────▶│                   │
     │               │                    │                   │                   │
     │               │                    │                   │  Download Parquet │
     │               │                    │                   │─────────────────▶│
     │               │                    │                   │                   │
     │               │                    │                   │  nodes/Movie/     │
     │               │                    │                   │◀─────────────────│
     │               │                    │                   │                   │
     │               │                    │                   │  nodes/Actor/     │
     │               │                    │                   │◀─────────────────│
     │               │                    │                   │                   │
     │               │                    │                   │  edges/ACTED_IN/  │
     │               │                    │                   │◀─────────────────│
     │               │                    │                   │                   │
     │               │                    │                   │  Load into        │
     │               │                    │                   │  graph engine     │
     │               │                    │                   │  (Ryugraph/       │
     │               │                    │                   │   FalkorDB)       │
     │               │                    │                   │                   │
     │               │                    │  Pod Ready=True   │                   │
     │               │                    │◀──────────────────│                   │
     │               │                    │                   │                   │
     │  GET /instances/42                 │                   │                   │
     │               │                    │                   │                   │
     │  {                                 │                   │                   │
     │    "id": 42,                       │                   │                   │
     │    "status": "running",            │                   │                   │
     │    "url": "http://wrapper-xyz..."  │                   │                   │
     │  }                                 │                   │                   │
     │◀──────────────│                    │                   │                   │
```

### Curl Example

```bash
# Create instance
curl -X POST "http://control-plane:8080/api/instances" \
    -H "Content-Type: application/json" \
    -H "X-Username: analyst@example.com" \
    -H "X-User-Role: analyst" \
    -d '{"snapshot_id": 100, "wrapper_type": "ryugraph"}'

# Response: {"id": 42, "status": "pending", "url": null}

# Poll until running
while true; do
    RESPONSE=$(curl -s "http://control-plane:8080/api/instances/42" \
        -H "X-Username: analyst@example.com" \
        -H "X-User-Role: analyst")

    STATUS=$(echo "$RESPONSE" | jq -r '.status')
    echo "Status: $STATUS"

    if [ "$STATUS" == "running" ]; then
        URL=$(echo "$RESPONSE" | jq -r '.url')
        echo "Instance ready at: $URL"
        break
    fi

    sleep 5
done
```

### What Kubernetes Creates

```yaml
# Pod
apiVersion: v1
kind: Pod
metadata:
  name: wrapper-abc123def
  labels:
    app: ryugraph-wrapper
    instance-id: "42"
    snapshot-id: "100"
spec:
  serviceAccountName: wrapper  # Workload Identity → GCS access
  containers:
    - name: wrapper
      image: gcr.io/project/ryugraph-wrapper:v1.0.0
      env:
        - name: WRAPPER_SNAPSHOT_ID
          value: "100"
        - name: WRAPPER_GCS_BASE_PATH
          value: "gs://bucket/snapshots/100"
        - name: WRAPPER_INSTANCE_URL
          value: "http://wrapper-abc123def.graph-olap.svc.cluster.local:8000"
---
# Service
apiVersion: v1
kind: Service
metadata:
  name: wrapper-abc123def
  annotations:
    cloud.google.com/neg: '{"ingress": true}'  # Container-native LB
spec:
  selector:
    app: ryugraph-wrapper
    url-slug: abc123def
  ports:
    - port: 8000
```

---

## Flow 4: Execute Query

Run Cypher/GQL queries against the graph instance.

```
┌─────────┐                              ┌─────────────────┐
│  Client │─────────────────────────────▶│   Wrapper Pod   │
└─────────┘                              └─────────────────┘
     │                                           │
     │  POST /query                              │
     │  {                                        │
     │    "query": "MATCH (m:Movie)              │
     │              WHERE m.year > 2000          │
     │              RETURN m.title, m.year       │
     │              LIMIT 10"                    │
     │  }                                        │
     │  Headers:                                 │
     │    X-Username: analyst@example.com        │
     │    X-User-Role: analyst                   │
     │                                           │
     │                                           │  Validate user
     │                                           │  Parse Cypher
     │                                           │  Execute on
     │                                           │  in-memory graph
     │                                           │
     │  200 OK                                   │
     │  {                                        │
     │    "results": [                           │
     │      {"m.title": "Inception",             │
     │       "m.year": 2010},                    │
     │      {"m.title": "Interstellar",          │
     │       "m.year": 2014}                     │
     │    ],                                     │
     │    "metadata": {                          │
     │      "execution_time_ms": 12,             │
     │      "rows_returned": 2                   │
     │    }                                      │
     │  }                                        │
     │◀──────────────────────────────────────────│
```

### Curl Example

```bash
# Get instance URL
INSTANCE=$(curl -s "http://control-plane:8080/api/instances/42" \
    -H "X-Username: analyst@example.com" \
    -H "X-User-Role: analyst")

WRAPPER_URL=$(echo "$INSTANCE" | jq -r '.url')

# Execute query
curl -X POST "$WRAPPER_URL/query" \
    -H "Content-Type: application/json" \
    -H "X-Username: analyst@example.com" \
    -H "X-User-Role: analyst" \
    -d '{
        "query": "MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) WHERE m.year > 2000 RETURN a.name, m.title LIMIT 10"
    }'
```

---

## Flow 5: Delete Instance (Cleanup)

Terminate wrapper pod and release resources.

```
┌─────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Client │──▶│ Control Plane │──▶│ Kubernetes API│──▶│  Wrapper Pod  │
└─────────┘   └───────────────┘   └───────────────┘   └───────────────┘
     │               │                    │                   │
     │  DELETE /api/instances/42          │                   │
     │               │                    │                   │
     │               │  Delete Pod        │                   │
     │               │───────────────────▶│                   │
     │               │                    │  Terminate        │
     │               │                    │──────────────────▶│
     │               │                    │                   │ (deleted)
     │               │  Delete Service    │
     │               │───────────────────▶│
     │               │                    │
     │               │  Update DB status  │
     │               │  (terminated)      │
     │               │                    │
     │  204 No Content                    │
     │◀──────────────│                    │
```

### Curl Example

```bash
# Delete instance
curl -X DELETE "http://control-plane:8080/api/instances/42" \
    -H "X-Username: analyst@example.com" \
    -H "X-User-Role: analyst"

# Response: 204 No Content
```

---

## Complete End-to-End Smoke Test

```bash
#!/bin/bash
# e2e-smoke-test.sh - Complete platform flow test

set -e

API_URL="${API_URL:-http://control-plane.graph-olap.svc.cluster.local:8080}"
USER="smoketest@example.com"
ROLE="analyst"

AUTH="-H \"X-Username: $USER\" -H \"X-User-Role: $ROLE\""

echo "=== End-to-End Platform Smoke Test ==="
echo ""

# Step 1: Check health
echo "[1/7] Checking platform health..."
curl -sf "$API_URL/health" | jq .
echo "✓ Platform healthy"

# Step 2: List existing mappings
echo ""
echo "[2/7] Listing mappings..."
MAPPINGS=$(curl -sf "$API_URL/api/mappings" \
    -H "X-Username: $USER" -H "X-User-Role: $ROLE")
echo "$MAPPINGS" | jq '.[] | {id, name}'
MAPPING_ID=$(echo "$MAPPINGS" | jq -r '.[0].id // empty')

if [ -z "$MAPPING_ID" ]; then
    echo "⚠ No mappings found - create one first"
    exit 1
fi
echo "✓ Using mapping ID: $MAPPING_ID"

# Step 3: List snapshots for mapping
echo ""
echo "[3/7] Listing snapshots..."
SNAPSHOTS=$(curl -sf "$API_URL/api/snapshots?mapping_id=$MAPPING_ID" \
    -H "X-Username: $USER" -H "X-User-Role: $ROLE")
echo "$SNAPSHOTS" | jq '.[] | {id, status}'
SNAPSHOT_ID=$(echo "$SNAPSHOTS" | jq -r '[.[] | select(.status == "ready")] | .[0].id // empty')

if [ -z "$SNAPSHOT_ID" ]; then
    echo "⚠ No ready snapshots found - create one first"
    exit 1
fi
echo "✓ Using snapshot ID: $SNAPSHOT_ID"

# Step 4: Create instance
echo ""
echo "[4/7] Creating instance from snapshot..."
CREATE_RESPONSE=$(curl -sf -X POST "$API_URL/api/instances" \
    -H "Content-Type: application/json" \
    -H "X-Username: $USER" -H "X-User-Role: $ROLE" \
    -d "{\"snapshot_id\": $SNAPSHOT_ID, \"wrapper_type\": \"ryugraph\"}")
INSTANCE_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
echo "✓ Created instance: $INSTANCE_ID"

# Cleanup on exit
cleanup() {
    echo ""
    echo "Cleaning up instance $INSTANCE_ID..."
    curl -sf -X DELETE "$API_URL/api/instances/$INSTANCE_ID" \
        -H "X-Username: $USER" -H "X-User-Role: $ROLE" || true
}
trap cleanup EXIT

# Step 5: Wait for instance to be running
echo ""
echo "[5/7] Waiting for instance to be ready..."
for i in {1..60}; do
    INSTANCE=$(curl -sf "$API_URL/api/instances/$INSTANCE_ID" \
        -H "X-Username: $USER" -H "X-User-Role: $ROLE")
    STATUS=$(echo "$INSTANCE" | jq -r '.status')

    if [ "$STATUS" == "running" ]; then
        WRAPPER_URL=$(echo "$INSTANCE" | jq -r '.url')
        echo "✓ Instance running at: $WRAPPER_URL"
        break
    elif [ "$STATUS" == "failed" ]; then
        echo "✗ Instance failed to start"
        exit 1
    fi

    echo "  Status: $STATUS (${i}/60)"
    sleep 5
done

if [ "$STATUS" != "running" ]; then
    echo "✗ Timeout waiting for instance"
    exit 1
fi

# Step 6: Execute query
echo ""
echo "[6/7] Executing test query..."
QUERY_RESULT=$(curl -sf -X POST "$WRAPPER_URL/query" \
    -H "Content-Type: application/json" \
    -H "X-Username: $USER" -H "X-User-Role: $ROLE" \
    -d '{"query": "MATCH (n) RETURN count(n) as node_count"}')
NODE_COUNT=$(echo "$QUERY_RESULT" | jq -r '.results[0].node_count // .results[0][0] // "unknown"')
echo "✓ Query executed - Node count: $NODE_COUNT"

# Step 7: Test additional queries
echo ""
echo "[7/7] Running additional queries..."

# Get labels
LABELS_RESULT=$(curl -sf -X POST "$WRAPPER_URL/query" \
    -H "Content-Type: application/json" \
    -H "X-Username: $USER" -H "X-User-Role: $ROLE" \
    -d '{"query": "MATCH (n) RETURN DISTINCT labels(n)[0] as label, count(n) as count"}')
echo "Labels:"
echo "$LABELS_RESULT" | jq '.results'

# Get relationship types
RELS_RESULT=$(curl -sf -X POST "$WRAPPER_URL/query" \
    -H "Content-Type: application/json" \
    -H "X-Username: $USER" -H "X-User-Role: $ROLE" \
    -d '{"query": "MATCH ()-[r]->() RETURN DISTINCT type(r) as type, count(r) as count"}')
echo "Relationships:"
echo "$RELS_RESULT" | jq '.results'

echo ""
echo "=== End-to-End Smoke Test PASSED ==="
```

---

## Authentication Flow Summary

```
External Client                    In-Cluster Client
      │                                  │
      │ Authorization: Bearer JWT        │ X-Username: user@example.com
      │                                  │ X-User-Role: analyst
      ▼                                  ▼
┌─────────────────┐            ┌─────────────────┐
│  OAuth2 Proxy   │            │  Direct to Pod  │
│  (validates JWT │            │  (trusts headers│
│   extracts email)            │   from cluster) │
└────────┬────────┘            └────────┬────────┘
         │                              │
         │ X-Username: user@example.com │
         │ Authorization: Bearer JWT    │
         ▼                              ▼
    ┌─────────────────────────────────────────┐
    │              Control Plane              │
    │                                         │
    │  • Reads X-Username for user identity   │
    │  • Reads X-User-Role for authorization  │
    │  • Validates JWT claims if external     │
    └─────────────────────────────────────────┘
```

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   SOURCE DATA          EXPORT              STORAGE           QUERY       │
│                                                                          │
│   ┌──────────┐      ┌──────────┐       ┌──────────┐      ┌──────────┐   │
│   │Starburst │      │ Export   │       │   GCS    │      │ Wrapper  │   │
│   │(BigQuery,│─────▶│ Worker   │──────▶│(Parquet) │─────▶│  Pod     │   │
│   │ etc.)    │      │          │       │          │      │(In-Memory│   │
│   └──────────┘      └──────────┘       └──────────┘      │ Graph)   │   │
│        │                 │                  │            └──────────┘   │
│        │                 │                  │                  │        │
│        │  SQL Queries    │  UNLOAD or      │  Download        │ Cypher  │
│        │  SET ROLE       │  PyArrow        │  on startup      │ Queries │
│        │                 │  export         │                  │         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Integration Points

| Component | Connects To | Protocol | Authentication |
|-----------|-------------|----------|----------------|
| Client → Control Plane | Internal LB | HTTPS | JWT or X-Headers |
| Control Plane → Cloud SQL | Cloud SQL Proxy | PostgreSQL (localhost) | IAM via Workload Identity |
| Control Plane → K8s API | In-cluster | HTTPS | ServiceAccount RBAC |
| Export Worker → Starburst | REST API | HTTPS | Basic Auth + SET ROLE |
| Export Worker → GCS | GCS API | HTTPS | Workload Identity |
| Wrapper Pod → GCS | GCS API | HTTPS | Workload Identity |
| Client → Wrapper Pod | Service DNS | HTTP | X-Headers |
