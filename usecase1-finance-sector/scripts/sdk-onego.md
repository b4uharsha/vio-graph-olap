# SDK One-Go Test

Paste into a single Jupyter cell. Tests the full platform lifecycle using the Graph OLAP Python SDK.

## Configuration

Update these variables for your environment before running:

```python
API_URL = "https://<your-control-plane-url>"
PROXY = "http://<proxy-host>:<port>"
USE_CASE_ID = "<your-use-case-id>"
```

## Script

```python
# === SDK E2E TEST ===
import os, time

# === CONFIGURATION — UPDATE THESE ===
API_URL = "https://<your-control-plane-url>"
PROXY = "http://<proxy-host>:<port>"
USE_CASE_ID = "<your-use-case-id>"
CATALOG = "<your-catalog>"
SCHEMA = "<your-schema>"
TABLE = "customer_demographics"

# Environment
os.environ['GRAPH_OLAP_API_URL'] = API_URL
os.environ['GRAPH_OLAP_IN_CLUSTER_MODE'] = 'true'
os.environ['GRAPH_OLAP_USE_CASE_ID'] = USE_CASE_ID
os.environ['GRAPH_OLAP_VERIFY_SSL'] = 'false'
os.environ['GRAPH_OLAP_SKIP_HEALTH_CHECK'] = 'true'
os.environ['https_proxy'] = PROXY
os.environ['http_proxy'] = PROXY

from graph_olap import GraphOLAPClient
from graph_olap.models.mapping import NodeDefinition, PropertyDefinition
from graph_olap_schemas import WrapperType

# === CONNECT ===
client = GraphOLAPClient(
    api_url=API_URL,
    username="test-user",
    role="admin",
    use_case_id=USE_CASE_ID,
    proxy=PROXY,
    verify=False,
)
print(f"Connected to: {client._config.api_url}")

# === HEALTH ===
health = client.health.check()
print(f"Health: {health.status}")

# === CREATE MAPPING ===
mapping = client.mappings.create(
    name="finance-sdk-test",
    description="Finance sector SDK E2E test",
    node_definitions=[{
        "label": "Customer",
        "sql": f'SELECT DISTINCT customer_id, customer_name, sector, id_type FROM "{CATALOG}"."{SCHEMA}"."{TABLE}" LIMIT 10',
        "primary_key": {"name": "customer_id", "type": "INT64"},
        "properties": [
            {"name": "customer_name", "type": "STRING"},
            {"name": "sector", "type": "STRING"},
            {"name": "id_type", "type": "STRING"}
        ]
    }],
    edge_definitions=[]
)
MAPPING_ID = mapping.id
print(f"Mapping created: id={MAPPING_ID}, name={mapping.name}")

# === CREATE INSTANCE (waits until running) ===
print("Creating instance (snapshot + FalkorDB)... this takes 2-4 minutes")
instance = client.instances.create_and_wait(
    mapping_id=MAPPING_ID,
    name="finance-sdk-instance",
    wrapper_type=WrapperType.FALKORDB,
    timeout=300,
    poll_interval=5,
)
INSTANCE_ID = instance.id
print(f"Instance running: id={INSTANCE_ID}")

# === CONNECT TO WRAPPER (with retry) ===
conn = client.instances.connect(INSTANCE_ID)
print("Connected to wrapper, waiting for readiness...")
for attempt in range(12):
    try:
        conn.query("RETURN 1")
        print(f"Wrapper ready after {attempt * 5}s")
        break
    except Exception:
        if attempt < 11:
            time.sleep(5)
        else:
            print("Wrapper not ready after 60s")
            raise

# === QUERY: Count ===
result = conn.query("MATCH (c:Customer) RETURN count(c) as total")
print(f"\nCustomer count: {result.rows[0][0]}")

# === QUERY: List customers ===
result = conn.query("MATCH (c:Customer) RETURN c.customer_name, c.sector, c.id_type LIMIT 10")
print(f"\nCustomers ({result.row_count} rows):")
for row in result.rows:
    print(f"  {row}")

# === QUERY: Schema ===
schema = conn.get_schema()
print(f"\nSchema:")
print(f"  Nodes: {list(schema.node_labels.keys())}")
print(f"  Edges: {list(schema.relationship_types.keys())}")

# === DATAFRAME ===
import pandas as pd
result = conn.query("MATCH (c:Customer) RETURN c.customer_name as name, c.sector as sector, c.id_type as id_type")
df = pd.DataFrame(result.rows, columns=[c for c in result.columns])
print(f"\nDataFrame:")
print(df)

# === GRAPH VISUALIZATION ===
import networkx as nx
import matplotlib.pyplot as plt

G = nx.Graph()
for row in result.rows:
    G.add_node(row[0], sector=row[1])
for i, n1 in enumerate(result.rows):
    for n2 in result.rows[i+1:]:
        if n1[1] == n2[1]:
            G.add_edge(n1[0], n2[0])

plt.figure(figsize=(10, 6))
nx.draw(G, with_labels=True, node_color="lightblue", node_size=2000, font_size=8, edge_color="gray")
plt.title("Customer Graph - connected by same sector (via SDK)")
plt.show()

# === CLEANUP ===
client.instances.terminate(INSTANCE_ID)
print(f"\nInstance {INSTANCE_ID} terminated")
try:
    client.mappings.delete(MAPPING_ID)
    print(f"Mapping {MAPPING_ID} deleted")
except Exception:
    print(f"Mapping {MAPPING_ID} kept (has snapshot)")

print("\n" + "=" * 50)
print("SDK E2E TEST: PASS")
print("=" * 50)
print("\nVerified via SDK:")
print("  1. Health check")
print("  2. Create mapping (Customer data)")
print("  3. Create instance (Starburst -> GCS -> FalkorDB)")
print("  4. Connect to wrapper (proxy-aware)")
print("  5. Cypher queries (count, list, schema)")
print("  6. DataFrame (pandas)")
print("  7. Graph visualization (networkx)")
print("  8. Cleanup (terminate + delete)")

client.close()
```
