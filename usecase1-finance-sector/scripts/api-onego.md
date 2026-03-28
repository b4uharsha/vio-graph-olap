# API One-Go Test

Paste into a single Jupyter cell. Tests the full platform lifecycle using raw HTTP API.

## Configuration

Update these variables for your environment before running:

```python
API_URL = "https://<your-control-plane-url>"       # Control plane endpoint
PROXY = "http://<proxy-host>:<port>"                # Corporate proxy (or None)
USE_CASE_ID = "<your-use-case-id>"                  # Use case identifier
CATALOG = "<your-catalog>"                          # Starburst catalog name
SCHEMA = "<your-schema>"                            # Schema containing tables
TABLE = "<your-customer-table>"                     # Customer demographics table
```

## Script

```python
# === SETUP ===
import os, time, json, subprocess

# Install httpx (proxy stripped from env so pip can reach PyPI)
clean_env = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower()}
subprocess.run(["pip", "install", "--no-cache-dir", "httpx", "-q"], capture_output=True, env=clean_env)

# === CONFIGURATION — UPDATE THESE ===
API_URL = "https://<your-control-plane-url>"
PROXY = "http://<proxy-host>:<port>"
USE_CASE_ID = "<your-use-case-id>"
CATALOG = "<your-catalog>"
SCHEMA = "<your-schema>"
TABLE = "customer_demographics"

# Proxy on for API calls
os.environ['http_proxy'] = PROXY
os.environ['https_proxy'] = PROXY

import httpx
HEADERS = {"Content-Type": "application/json", "X-Username": "test-user", "X-User-Role": "admin", "X-Use-Case-Id": USE_CASE_ID}
client = httpx.Client(base_url=API_URL, headers=HEADERS, verify=False, timeout=30, proxy=PROXY)

# === HEALTH ===
print("Health:", client.get("/health").json())

# === CREATE MAPPING ===
r = client.post("/api/mappings", json={
    "name": "finance-e2e-test",
    "description": "Finance sector E2E test",
    "node_definitions": [{
        "label": "Customer",
        "sql": f'SELECT DISTINCT customer_id, customer_name, sector, id_type FROM "{CATALOG}"."{SCHEMA}"."{TABLE}" LIMIT 10',
        "primary_key": {"name": "customer_id", "type": "INT64"},
        "properties": [
            {"name": "customer_name", "type": "STRING"},
            {"name": "sector", "type": "STRING"},
            {"name": "id_type", "type": "STRING"}
        ]
    }],
    "edge_definitions": []
})
MAPPING_ID = r.json()["data"]["id"]
print(f"Mapping created: id={MAPPING_ID}")

# === CREATE INSTANCE ===
r = client.post("/api/instances", json={"mapping_id": MAPPING_ID, "name": "finance-e2e-instance", "wrapper_type": "falkordb"})
INSTANCE_ID = r.json()["data"]["id"]
print(f"Instance created: id={INSTANCE_ID}")

# === POLL UNTIL RUNNING ===
status = "unknown"
SLUG = ""
for i in range(30):
    r = client.get(f"/api/instances/{INSTANCE_ID}")
    inst = r.json()["data"]
    status = inst["status"]
    print(f"  [{i}] {status}")
    if status == "running":
        SLUG = inst["instance_url"].split("/wrapper/")[-1]
        print(f"\nRunning! slug={SLUG}")
        print("Waiting 45s for wrapper pod to be ready...")
        time.sleep(45)
        break
    elif status == "failed":
        print(f"\nFailed: {inst.get('error_message')}")
        break
    time.sleep(3)

# === HEALTH + QUERY ===
if status == "running":
    r = client.get(f"/wrapper/{SLUG}/health")
    print(f"\nHealth: {r.status_code}", r.json() if r.status_code == 200 else r.text[:200])

    r = client.get(f"/wrapper/{SLUG}/ready")
    print(f"Ready: {r.status_code}", r.json() if r.status_code == 200 else r.text[:200])

    r = client.post(f"/wrapper/{SLUG}/query", json={"query": "MATCH (n:Customer) RETURN count(n) as total"})
    if r.status_code == 200:
        print(f"\nCustomer count: {r.json()['rows'][0][0]}")

        r = client.post(f"/wrapper/{SLUG}/query", json={"query": "MATCH (n:Customer) RETURN n.customer_name, n.sector, n.id_type LIMIT 10"})
        result = r.json()
        print(f"\nCustomers:")
        for row in result["rows"]:
            print(f"  {row}")

        print(f"\nSchema:")
        print(json.dumps(client.get(f"/wrapper/{SLUG}/schema").json(), indent=2))

        # === DATAFRAME ===
        import pandas as pd
        r = client.post(f"/wrapper/{SLUG}/query", json={"query": "MATCH (n:Customer) RETURN n.customer_name as name, n.sector as sector, n.id_type as id_type"})
        result = r.json()
        df = pd.DataFrame(result["rows"], columns=result["columns"])
        print("\nDataFrame:")
        print(df)

        # === GRAPH VISUALIZATION ===
        import networkx as nx
        import matplotlib.pyplot as plt

        G = nx.Graph()
        for row in result["rows"]:
            G.add_node(row[0], sector=row[1])
        for i, n1 in enumerate(result["rows"]):
            for n2 in result["rows"][i+1:]:
                if n1[1] == n2[1]:
                    G.add_edge(n1[0], n2[0])

        plt.figure(figsize=(10, 6))
        nx.draw(G, with_labels=True, node_color="lightblue", node_size=2000, font_size=8, edge_color="gray")
        plt.title("Customer Graph - connected by same sector")
        plt.show()

        # === CLEANUP ===
        client.delete(f"/api/instances/{INSTANCE_ID}")
        client.delete(f"/api/mappings/{MAPPING_ID}")
        print(f"\nCleaned up: instance {INSTANCE_ID}, mapping {MAPPING_ID}")
    else:
        print("Query failed:", r.text[:500])
        print(f"\nClean up manually:")
        print(f'  client.delete("/api/instances/{INSTANCE_ID}")')
        print(f'  client.delete("/api/mappings/{MAPPING_ID}")')
```
