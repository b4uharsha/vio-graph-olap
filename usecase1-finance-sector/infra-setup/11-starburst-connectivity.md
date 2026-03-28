# Starburst/Trino Connectivity Guide

This guide covers how the Graph OLAP platform connects to Starburst (Trino) for data export and query execution.

## Overview

The platform connects to Starburst for:
- **Data Export**: Querying source data and exporting to GCS as Parquet files
- **Schema Validation**: Validating mapping SQL queries via DESCRIBE
- **Role-Based Access**: Setting user roles before query execution

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Graph OLAP Platform                               │
│                                                                              │
│  ┌──────────────────┐              ┌──────────────────────────────────────┐ │
│  │  Control Plane   │              │           Export Worker              │ │
│  │                  │              │                                      │ │
│  │  - Schema cache  │              │  - UNLOAD queries (system.unload)   │ │
│  │  - Query valid.  │              │  - Direct export (PyArrow fallback) │ │
│  │  - Starburst URL │              │  - Polling for completion           │ │
│  └────────┬─────────┘              └──────────────────┬───────────────────┘ │
│           │                                           │                      │
│           │         Starburst REST API               │                      │
│           │         (HTTPS :443)                     │                      │
│           └───────────────────┬──────────────────────┘                      │
│                               │                                              │
└───────────────────────────────┼──────────────────────────────────────────────┘
                                │
                                ▼
                   ┌─────────────────────────────┐
                   │        Starburst            │
                   │    (Trino / Galaxy)         │
                   │                             │
                   │  - BigQuery connector       │
                   │  - GCS connector            │
                   │  - Role-based access        │
                   │  - Resource groups          │
                   └─────────────────────────────┘
```

## 1. Connection Configuration

### Environment Variables

```bash
# Starburst connection
export STARBURST_URL="https://your-cluster.trino.galaxy.starburst.io:443"
export STARBURST_USER="service-account@your-org/accountadmin"
export STARBURST_PASSWORD="your-password"          # Optional for header-only auth
export STARBURST_CATALOG="bigquery"
export STARBURST_SCHEMA="your_schema"

# Role-based access (enterprise)
export STARBURST_ROLE="data_analyst_role"

# Resource group routing
export STARBURST_CLIENT_TAGS="graph-olap-export"
export STARBURST_SOURCE="graph-olap-export-worker"

# SSL verification (set false for self-signed certs)
export STARBURST_SSL_VERIFY="true"

# Request timeout
export STARBURST_REQUEST_TIMEOUT_SECONDS="30"
```

### Kubernetes Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: starburst-credentials
  namespace: graph-olap
type: Opaque
stringData:
  STARBURST_URL: "https://your-cluster.trino.galaxy.starburst.io:443"
  STARBURST_USER: "service-account@your-org/accountadmin"
  STARBURST_PASSWORD: "your-password"
  STARBURST_ROLE: "data_analyst_role"
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: starburst-config
  namespace: graph-olap
data:
  STARBURST_CATALOG: "bigquery"
  STARBURST_SCHEMA: "your_schema"
  STARBURST_CLIENT_TAGS: "graph-olap-export"
  STARBURST_SOURCE: "graph-olap-export-worker"
  STARBURST_SSL_VERIFY: "true"
  STARBURST_REQUEST_TIMEOUT_SECONDS: "30"
```

## 2. Authentication Methods

### Method 1: Basic Auth (Username + Password)

```python
# HTTP Basic Authentication
client = httpx.Client(
    auth=(username, password),
    timeout=30,
)
```

Headers sent:
```
Authorization: Basic <base64(user:pass)>
X-Trino-User: service-account@your-org/accountadmin
```

### Method 2: Header-Only Auth (No Password)

For environments using external auth (SSO, IAM):

```python
# No auth tuple, just headers
client = httpx.Client(timeout=30)
headers = {
    "X-Trino-User": "service-account@your-org/accountadmin",
    "X-Trino-Catalog": "bigquery",
    "X-Trino-Schema": "your_schema",
}
```

### Method 3: Role-Based Auth with SET ROLE

For enterprise Starburst with fine-grained access control:

```python
# Step 1: Set role via SQL (before queries)
session.execute("SET ROLE data_analyst_role")

# Step 2: Execute actual query
session.execute("SELECT * FROM table")
```

The platform implements this as:

```python
def _set_role_sync(self, client, catalog):
    """Send SET ROLE statement before queries."""
    if self.role:
        client.post(
            f"{self.url}/v1/statement",
            content=f"SET ROLE {self.role}",
            headers=self._get_headers(catalog),
        )
```

## 3. HTTP Headers

### Required Headers

```python
headers = {
    # User identification
    "X-Trino-User": "service-account@your-org",

    # Catalog and schema context
    "X-Trino-Catalog": "bigquery",
    "X-Trino-Schema": "your_schema",

    # Content type for SQL queries
    "Content-Type": "text/plain",
}
```

### Optional Headers

```python
headers.update({
    # Role for fine-grained access (enterprise)
    "X-Trino-Role": "data_analyst_role",

    # Resource group routing (for query prioritization)
    "X-Trino-Client-Tags": "graph-olap-export,batch",

    # Source identification (for logging/monitoring)
    "X-Trino-Source": "graph-olap-export-worker",
})
```

## 4. Query Execution Flow

### Submit Query

```bash
# Submit query to Starburst
curl -X POST "https://your-cluster.trino.galaxy.starburst.io:443/v1/statement" \
    -H "X-Trino-User: $STARBURST_USER" \
    -H "X-Trino-Catalog: bigquery" \
    -H "X-Trino-Schema: your_schema" \
    -H "X-Trino-Role: $STARBURST_ROLE" \
    -H "X-Trino-Client-Tags: graph-olap-export" \
    -H "X-Trino-Source: graph-olap-export-worker" \
    -H "Content-Type: text/plain" \
    -u "$STARBURST_USER:$STARBURST_PASSWORD" \
    -d "SELECT * FROM your_table LIMIT 10"
```

### Response

```json
{
  "id": "20240315_123456_00001_xxxxx",
  "infoUri": "https://cluster/ui/query/20240315_123456_00001_xxxxx",
  "nextUri": "https://cluster/v1/statement/queued/20240315_123456_00001_xxxxx/1",
  "stats": {
    "state": "QUEUED",
    "queued": true,
    "scheduled": false,
    "nodes": 0,
    "totalSplits": 0
  }
}
```

### Poll for Results

```bash
# Poll using nextUri from response
curl -X GET "https://cluster/v1/statement/queued/20240315_123456_00001_xxxxx/1" \
    -H "X-Trino-User: $STARBURST_USER" \
    -u "$STARBURST_USER:$STARBURST_PASSWORD"
```

### Query States

| State | Description |
|-------|-------------|
| `QUEUED` | Query waiting in queue |
| `PLANNING` | Query being planned |
| `STARTING` | Query starting execution |
| `RUNNING` | Query executing |
| `FINISHING` | Query finishing |
| `FINISHED` | Query completed successfully |
| `FAILED` | Query failed |

## 5. Export Methods

### Method 1: UNLOAD to GCS (Preferred)

Uses Starburst's `system.unload` table function:

```sql
SELECT * FROM TABLE(
    system.unload(
        input => TABLE(
            SELECT column1, column2, column3
            FROM (your_source_query)
        ),
        location => 'gs://your-bucket/exports/snapshot-123/',
        format => 'PARQUET',
        compression => 'SNAPPY'
    )
)
```

**Advantages:**
- Server-side export (no data transfer through client)
- Efficient for large datasets
- Supports partitioning

**Requirements:**
- GCS catalog configured in Starburst
- `system.unload` function available

### Method 2: Direct Export via PyArrow (Fallback)

For environments without `system.unload`:

```python
# 1. Execute query and collect results
response = client.post("/v1/statement", content=sql)
all_data = []

while next_uri:
    response = client.get(next_uri)
    if "data" in response:
        all_data.extend(response["data"])
    next_uri = response.get("nextUri")

# 2. Build PyArrow table
table = pa.table({col: [row[i] for row in data] for i, col in enumerate(columns)})

# 3. Write to GCS
pq.write_table(table, "data.parquet", compression="snappy")
gcs_client.upload_from_filename("data.parquet", "gs://bucket/path/")
```

**Advantages:**
- Works without GCS catalog in Starburst
- Full control over Parquet schema

**Disadvantages:**
- Data transfers through export worker
- Higher memory usage for large datasets

## 6. Role-Based Access Control

### Enterprise Starburst Roles

```sql
-- Set role before executing queries
SET ROLE data_analyst_role;

-- Query now runs with role permissions
SELECT * FROM protected_schema.sensitive_table;
```

### Implementation Pattern

```python
class StarburstClient:
    def __init__(self, role: str | None = None):
        self.role = role

    def execute_query(self, sql: str):
        with httpx.Client(auth=self.auth) as client:
            # Step 1: Set role if configured
            if self.role:
                client.post(
                    f"{self.url}/v1/statement",
                    content=f"SET ROLE {self.role}",
                    headers=self._get_headers(),
                )

            # Step 2: Execute actual query
            return client.post(
                f"{self.url}/v1/statement",
                content=sql,
                headers=self._get_headers(),
            )
```

### Role Header (Alternative)

Some Starburst configurations accept role via header:

```python
headers["X-Trino-Role"] = "data_analyst_role"
```

**Note:** Both SET ROLE SQL and X-Trino-Role header may be needed depending on Starburst configuration.

## 7. Resource Group Routing

Starburst resource groups manage query concurrency and prioritization:

### Client Tags

```python
# Tag queries for resource group routing
headers["X-Trino-Client-Tags"] = "graph-olap-export,batch,low-priority"
```

### Starburst Resource Group Config

```json
{
  "resourceGroups": [
    {
      "name": "graph-olap-export",
      "maxRunning": 10,
      "maxQueued": 100,
      "selectors": [
        {
          "clientTags": ["graph-olap-export"]
        }
      ]
    }
  ]
}
```

## 8. Error Handling

### Common Errors

| Error Code | Cause | Solution |
|------------|-------|----------|
| `PERMISSION_DENIED` | Missing role or privileges | Check role and SET ROLE |
| `CATALOG_NOT_FOUND` | Invalid catalog | Verify catalog name |
| `SCHEMA_NOT_FOUND` | Invalid schema | Verify schema name |
| `TABLE_NOT_FOUND` | Table doesn't exist | Check table name |
| `QUERY_REJECTED` | Resource limits exceeded | Check resource groups |

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
)
def submit_query(sql: str):
    response = client.post(f"{url}/v1/statement", content=sql)
    response.raise_for_status()
    return response.json()
```

## 9. Testing Connectivity

### Basic Connectivity Test

```bash
# Test connection
curl -sf "https://your-cluster.trino.galaxy.starburst.io:443/v1/info" | jq .

# Expected response:
# {"nodeVersion": {"version": "..."}, "environment": "production"}
```

### Query Test

```bash
# Test simple query
curl -X POST "https://your-cluster.trino.galaxy.starburst.io:443/v1/statement" \
    -H "X-Trino-User: $STARBURST_USER" \
    -H "X-Trino-Catalog: system" \
    -H "Content-Type: text/plain" \
    -u "$STARBURST_USER:$STARBURST_PASSWORD" \
    -d "SELECT 1 as test" | jq .
```

### Role Test

```bash
# Test SET ROLE
curl -X POST "https://your-cluster.trino.galaxy.starburst.io:443/v1/statement" \
    -H "X-Trino-User: $STARBURST_USER" \
    -H "X-Trino-Catalog: $STARBURST_CATALOG" \
    -H "Content-Type: text/plain" \
    -u "$STARBURST_USER:$STARBURST_PASSWORD" \
    -d "SET ROLE $STARBURST_ROLE" | jq .
```

### Catalog Access Test

```bash
# List schemas in catalog
curl -X POST "https://your-cluster.trino.galaxy.starburst.io:443/v1/statement" \
    -H "X-Trino-User: $STARBURST_USER" \
    -H "X-Trino-Catalog: $STARBURST_CATALOG" \
    -H "Content-Type: text/plain" \
    -u "$STARBURST_USER:$STARBURST_PASSWORD" \
    -d "SHOW SCHEMAS" | jq .
```

## 10. Smoke Test Script

```bash
#!/bin/bash
# smoke-starburst.sh - Starburst connectivity smoke test

set -e

STARBURST_URL="${STARBURST_URL:-https://your-cluster.trino.galaxy.starburst.io:443}"
STARBURST_USER="${STARBURST_USER:-your-user}"
STARBURST_PASSWORD="${STARBURST_PASSWORD:-}"
STARBURST_CATALOG="${STARBURST_CATALOG:-bigquery}"
STARBURST_ROLE="${STARBURST_ROLE:-}"

echo "=== Starburst Connectivity Smoke Test ==="
echo "URL: $STARBURST_URL"
echo "User: $STARBURST_USER"
echo "Catalog: $STARBURST_CATALOG"
echo ""

# Build auth option
if [ -n "$STARBURST_PASSWORD" ]; then
    AUTH_OPT="-u $STARBURST_USER:$STARBURST_PASSWORD"
else
    AUTH_OPT=""
fi

# Test 1: Server info
echo "[1/5] Testing server connectivity..."
INFO=$(curl -sf "$STARBURST_URL/v1/info" $AUTH_OPT)
if echo "$INFO" | jq -e '.nodeVersion' > /dev/null 2>&1; then
    VERSION=$(echo "$INFO" | jq -r '.nodeVersion.version')
    echo "✓ Connected to Starburst version: $VERSION"
else
    echo "✗ Failed to connect to Starburst"
    exit 1
fi

# Test 2: Simple query
echo "[2/5] Testing query execution..."
RESULT=$(curl -sf -X POST "$STARBURST_URL/v1/statement" \
    -H "X-Trino-User: $STARBURST_USER" \
    -H "X-Trino-Catalog: system" \
    -H "Content-Type: text/plain" \
    $AUTH_OPT \
    -d "SELECT 1 as test")

if echo "$RESULT" | jq -e '.id' > /dev/null 2>&1; then
    QUERY_ID=$(echo "$RESULT" | jq -r '.id')
    echo "✓ Query submitted: $QUERY_ID"
else
    echo "✗ Query submission failed"
    echo "$RESULT" | jq .
    exit 1
fi

# Test 3: SET ROLE (if configured)
if [ -n "$STARBURST_ROLE" ]; then
    echo "[3/5] Testing SET ROLE..."
    RESULT=$(curl -sf -X POST "$STARBURST_URL/v1/statement" \
        -H "X-Trino-User: $STARBURST_USER" \
        -H "X-Trino-Catalog: $STARBURST_CATALOG" \
        -H "Content-Type: text/plain" \
        $AUTH_OPT \
        -d "SET ROLE $STARBURST_ROLE")

    if echo "$RESULT" | jq -e '.id' > /dev/null 2>&1; then
        echo "✓ SET ROLE $STARBURST_ROLE succeeded"
    else
        echo "⚠ SET ROLE may have failed (check permissions)"
    fi
else
    echo "[3/5] Skipping SET ROLE test (no role configured)"
fi

# Test 4: Catalog access
echo "[4/5] Testing catalog access..."
RESULT=$(curl -sf -X POST "$STARBURST_URL/v1/statement" \
    -H "X-Trino-User: $STARBURST_USER" \
    -H "X-Trino-Catalog: $STARBURST_CATALOG" \
    -H "Content-Type: text/plain" \
    $AUTH_OPT \
    -d "SHOW SCHEMAS")

if echo "$RESULT" | jq -e '.id' > /dev/null 2>&1; then
    echo "✓ Catalog '$STARBURST_CATALOG' accessible"
else
    echo "✗ Failed to access catalog '$STARBURST_CATALOG'"
    exit 1
fi

# Test 5: Check for errors
echo "[5/5] Checking for query errors..."
NEXT_URI=$(echo "$RESULT" | jq -r '.nextUri // empty')
if [ -n "$NEXT_URI" ]; then
    # Poll once to check for errors
    POLL_RESULT=$(curl -sf "$NEXT_URI" $AUTH_OPT)
    if echo "$POLL_RESULT" | jq -e '.error' > /dev/null 2>&1; then
        ERROR_MSG=$(echo "$POLL_RESULT" | jq -r '.error.message')
        echo "✗ Query error: $ERROR_MSG"
        exit 1
    fi
    echo "✓ No errors detected"
fi

echo ""
echo "=== Starburst connectivity test passed! ==="
```

## 11. Troubleshooting

### Connection Refused

```bash
# Check network connectivity
curl -v https://your-cluster.trino.galaxy.starburst.io:443/v1/info

# Check DNS resolution
nslookup your-cluster.trino.galaxy.starburst.io
```

### SSL Certificate Error

```bash
# Test with SSL verification disabled (temporary)
curl -k https://your-cluster.trino.galaxy.starburst.io:443/v1/info

# Set in config for self-signed certs
export STARBURST_SSL_VERIFY="false"
```

### Permission Denied

```bash
# Check current role
curl -X POST "$STARBURST_URL/v1/statement" \
    -H "X-Trino-User: $STARBURST_USER" \
    -H "Content-Type: text/plain" \
    -u "$STARBURST_USER:$STARBURST_PASSWORD" \
    -d "SELECT current_role()"

# List available roles
curl -X POST "$STARBURST_URL/v1/statement" \
    -H "X-Trino-User: $STARBURST_USER" \
    -H "Content-Type: text/plain" \
    -u "$STARBURST_USER:$STARBURST_PASSWORD" \
    -d "SHOW ROLES"
```

### Query Timeout

```bash
# Increase request timeout
export STARBURST_REQUEST_TIMEOUT_SECONDS="120"

# Check resource group limits in Starburst admin
```
