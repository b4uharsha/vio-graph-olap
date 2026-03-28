# API Reference

All requests require two headers — no JWT or login needed in local deployment:

```bash
-H "X-Username: you@example.com"
-H "X-User-Role: admin"    # admin | analyst | ops
```

Base URL: `http://localhost:30081`

---

## Mappings

A **Mapping** is a reusable blueprint — which warehouse tables become nodes and edges.

=== "List"

    ```bash
    GET /api/mappings
    ```

    ```json
    {
      "data": [
        { "id": 1, "name": "Customer Network", "created_at": "2025-01-01T00:00:00Z" }
      ]
    }
    ```

=== "Create"

    ```bash
    POST /api/mappings
    Content-Type: application/json

    {
      "name": "Customer Network",
      "description": "Customers connected to nations",
      "node_definitions": [
        {
          "label": "Customer",
          "sql": "SELECT custkey, name, acctbal, mktsegment FROM tpch.sf1.customer",
          "primary_key": { "name": "custkey", "type": "INT64" },
          "properties": [
            { "name": "name",        "type": "STRING" },
            { "name": "acctbal",     "type": "DOUBLE" },
            { "name": "mktsegment",  "type": "STRING" }
          ]
        },
        {
          "label": "Nation",
          "sql": "SELECT nationkey, name FROM tpch.sf1.nation",
          "primary_key": { "name": "nationkey", "type": "INT64" },
          "properties": [
            { "name": "name", "type": "STRING" }
          ]
        }
      ],
      "edge_definitions": [
        {
          "type": "BELONGS_TO",
          "from_node": "Customer",
          "to_node": "Nation",
          "sql": "SELECT custkey, nationkey FROM tpch.sf1.customer",
          "from_key": "custkey",
          "to_key": "nationkey",
          "properties": []
        }
      ]
    }
    ```

    Returns `{ "data": { "id": 42, ... } }`

=== "Get"

    ```bash
    GET /api/mappings/{mapping_id}
    ```

=== "Delete"

    ```bash
    DELETE /api/mappings/{mapping_id}
    ```

---

## Instances

An **Instance** is a running graph pod created from a Mapping.

=== "List"

    ```bash
    GET /api/instances
    ```

    ```json
    {
      "data": [
        {
          "id": 7,
          "name": "Q1 Analysis",
          "status": "running",
          "wrapper_type": "falkordb",
          "mapping_id": 42,
          "ttl": "PT4H",
          "created_at": "2025-01-01T10:00:00Z",
          "expires_at":  "2025-01-01T14:00:00Z"
        }
      ]
    }
    ```

=== "Create"

    ```bash
    POST /api/instances
    Content-Type: application/json

    {
      "mapping_id": 42,
      "wrapper_type": "falkordb",
      "name": "My Q1 Analysis",
      "ttl": "PT4H"
    }
    ```

    !!! info "wrapper_type options"
        - `falkordb` — FalkorDB (Redis-based). Fast lookups, low latency.
        - `ryugraph` — KuzuDB. Better for large scans and graph algorithms.

    !!! info "ttl format"
        ISO 8601 duration: `PT1H` · `PT4H` · `PT24H` · `P7D`

=== "Get"

    ```bash
    GET /api/instances/{instance_id}
    ```

    **Instance status lifecycle:**

    ```
    waiting_for_snapshot → starting → running → stopped
    ```

=== "Delete"

    ```bash
    DELETE /api/instances/{instance_id}
    ```

    Immediately deletes the pod and service. Parquet files in GCS are preserved.

---

## Querying

Queries go directly to the **wrapper pod**, not through the control-plane API.

=== "Via SDK (recommended — inside Jupyter)"

    ```python
    from graph_olap_sdk import GraphOLAPClient
    client = GraphOLAPClient("http://graph-olap-control-plane:8080", "you@example.com", "admin")
    conn   = client.instances.connect(instance_id)

    rows = conn.query(
        "MATCH (c:Customer)-[:BELONGS_TO]->(n:Nation) RETURN n.name, count(c) ORDER BY count(c) DESC"
    )
    print(rows.df())
    ```

=== "Via port-forward (from laptop)"

    ```bash
    # Find wrapper pod name
    kubectl get pods -n graph-olap-local | grep wrapper

    # Port-forward it
    kubectl port-forward -n graph-olap-local pod/<wrapper-pod-name> 8000:8000

    # Query directly
    curl -s -X POST http://localhost:8000/query \
      -H "Content-Type: application/json" \
      -d '{"query": "MATCH (c:Customer)-[:BELONGS_TO]->(n:Nation) RETURN n.name, count(c) ORDER BY count(c) DESC"}'
    ```

    Response format:

    ```json
    {
      "columns": ["n.name", "count(c)"],
      "rows": [["UNITED KINGDOM", 1823], ["GERMANY", 1654]],
      "row_count": 2,
      "execution_time_ms": 3
    }
    ```

    !!! warning "Only available when instance status is `running`"

=== "Check Schema"

    ```bash
    GET /api/instances/{instance_id}/schema
    ```

    Returns the node labels and relationship types loaded into the graph.

---

## Health

```bash
GET /health
```

```json
{ "status": "healthy" }
```

---

## Users

=== "List"

    ```bash
    GET /api/users
    ```

=== "Create"

    ```bash
    POST /api/users
    Content-Type: application/json

    {
      "username": "analyst@example.com",
      "role": "analyst"
    }
    ```

    **Available roles:**

    | Role | Permissions |
    | --- | --- |
    | `analyst` | Create instances, run queries |
    | `admin` | Full access — create/delete mappings, instances, users |
    | `ops` | View all instances, delete any instance |

---

## Property Types

| Type | Description |
| --- | --- |
| `STRING` | Text value |
| `INT64` | 64-bit integer |
| `DOUBLE` | Floating-point number |
| `BOOLEAN` | true / false |
| `DATE` | ISO 8601 date |
| `DATETIME` | ISO 8601 datetime |

---

## Error Responses

All errors return:

```json
{
  "error": {
    "code": "INSTANCE_NOT_FOUND",
    "message": "Instance 99 does not exist"
  }
}
```

| HTTP code | Meaning |
| --- | --- |
| `400` | Bad request — check your JSON body |
| `401` | Missing or invalid auth headers |
| `403` | Your role doesn't have permission |
| `404` | Resource not found |
| `409` | Conflict — e.g. mapping already has running instances |
| `500` | Internal server error — check control-plane logs |
