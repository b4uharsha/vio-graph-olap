# Use Cases

Real-world scenarios where Graph OLAP delivers value that SQL and traditional data warehouses cannot.

---

## Financial Services

=== ":material-alert-circle: Fraud Ring Detection"

    **The problem:** Fraudsters operate in rings — multiple accounts, shared addresses, phone numbers, or devices that are individually clean but collectively suspicious. SQL cannot efficiently find these clusters.

    **With Graph OLAP:**

    ```cypher
    -- Find accounts sharing the same device fingerprint
    MATCH (a1:Account)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(a2:Account)
    WHERE a1.id <> a2.id
    WITH d, collect(DISTINCT a1) + collect(DISTINCT a2) AS ring
    WHERE size(ring) > 3
    RETURN d.device_id, size(ring) AS ring_size, ring
    ORDER BY ring_size DESC

    -- Detect accounts within 2 hops of a known fraudulent account
    MATCH path = (fraud:Account {flagged: true})-[*1..2]-(suspect:Account)
    WHERE suspect.flagged = false
    RETURN suspect.id, suspect.name, length(path) AS hops
    ```

    **Business value:** Analysts can run these queries interactively in Jupyter, on a fresh snapshot of their warehouse data, without any ETL pipeline or dedicated graph DB team.

=== ":material-bank: AML — Anti-Money Laundering"

    **The problem:** Money laundering involves circular transaction chains — money that flows through multiple intermediaries and eventually returns to the origin. Circular CTEs in SQL are extremely slow at scale.

    **With Graph OLAP:**

    ```cypher
    -- Find circular payment chains
    MATCH path = (origin:Account)-[:TRANSFERRED_TO*2..6]->(origin)
    WHERE all(r IN relationships(path) WHERE r.amount > 10000)
    RETURN [n IN nodes(path) | n.account_id] AS chain,
           [r IN relationships(path) | r.amount] AS amounts

    -- High-velocity fan-out (potential layering)
    MATCH (a:Account)-[t:TRANSFERRED_TO]->(b:Account)
    WHERE t.date >= date('2024-01-01')
    WITH a, count(DISTINCT b) AS recipients, sum(t.amount) AS total
    WHERE recipients > 10 AND total > 1000000
    RETURN a.account_id, recipients, total
    ORDER BY total DESC
    ```

    **Business value:** Compliance teams get fresh, on-demand graph snapshots for investigation — no waiting for nightly batch jobs.

=== ":material-domain: Counterparty Exposure"

    **The problem:** How exposed is a bank to a given counterparty — directly and through chains of connected entities? Regulators increasingly require this analysis.

    **With Graph OLAP:**

    ```cypher
    -- Total exposure within 3 hops of a counterparty
    MATCH path = (target:Entity {name: "Risky Corp"})-[*1..3]-(connected:Entity)
    WITH connected, min(length(path)) AS distance
    MATCH (connected)-[e:HAS_EXPOSURE]->(b:Book)
    RETURN connected.name, distance, sum(e.notional) AS total_exposure
    ORDER BY total_exposure DESC

    -- Concentration risk — entities that appear in many portfolios
    MATCH (e:Entity)<-[:COUNTERPARTY_TO]-(t:Trade)
    WITH e, count(DISTINCT t.portfolio_id) AS portfolios, sum(t.notional) AS total
    WHERE portfolios > 5
    RETURN e.name, portfolios, total
    ORDER BY total DESC
    ```

=== ":material-account-group: Customer 360"

    **The problem:** A complete picture of a customer — their products, relationships, events, and connections to other customers — requires dozens of JOIN-heavy queries that are slow and hard to maintain.

    **With Graph OLAP:**

    ```cypher
    -- Full customer graph neighbourhood
    MATCH (c:Customer {id: 12345})-[r]-(connected)
    RETURN type(r) AS relationship, labels(connected)[0] AS entity_type,
           connected.name AS name

    -- Customers likely to churn based on network effects
    MATCH (c:Customer)-[:FRIEND_OF]->(churned:Customer {churned: true})
    WHERE c.churned = false
    WITH c, count(churned) AS churned_friends
    WHERE churned_friends >= 2
    RETURN c.id, c.name, churned_friends
    ORDER BY churned_friends DESC
    ```

---

## Supply Chain

=== ":material-truck: Supply Chain Risk"

    **The problem:** A tier-1 supplier going down is visible. But what if a tier-3 supplier is the single source of a critical component used by multiple tier-1 suppliers? This hidden concentration risk is invisible to SQL.

    **With Graph OLAP:**

    ```cypher
    -- Find single-source dependencies buried in the supply chain
    MATCH (component:Component)<-[:SUPPLIES*1..4]-(supplier:Supplier)
    WITH component, collect(DISTINCT supplier) AS suppliers
    WHERE size(suppliers) = 1
    MATCH (component)<-[:USES]-(product:Product)
    RETURN component.name, suppliers[0].name AS sole_supplier,
           count(product) AS products_at_risk

    -- Impact radius if a specific supplier fails
    MATCH path = (failed:Supplier {name: "Acme Corp"})-[:SUPPLIES*1..5]->(impact)
    RETURN DISTINCT labels(impact)[0] AS type, impact.name,
           length(path) AS hops_from_failure
    ORDER BY hops_from_failure
    ```

=== ":material-recycle: Circular Economy Tracking"

    **The problem:** Track materials through multiple recycling and remanufacturing steps — a naturally graph-shaped problem.

    ```cypher
    -- Trace a material from source to end-of-life
    MATCH path = (source:RawMaterial)-[:PROCESSED_INTO|ASSEMBLED_INTO|RECYCLED_INTO*1..10]->(end)
    WHERE end:Waste OR end:RecycledMaterial
    RETURN [n IN nodes(path) | n.name] AS lifecycle,
           length(path) AS steps

    -- Find materials never reaching recycling
    MATCH (m:RawMaterial)
    WHERE NOT (m)-[:PROCESSED_INTO|ASSEMBLED_INTO*]-(:RecycledMaterial)
    RETURN m.name, m.category, m.annual_tonnes
    ORDER BY m.annual_tonnes DESC
    ```

---

## Retail & Telco

=== ":material-account-multiple: Social Network Analysis"

    **The problem:** Who are the most influential customers? Which communities exist in your customer base? These questions require graph centrality and community algorithms that are impractical in SQL.

    ```cypher
    -- PageRank — most influential customers (Ryugraph only)
    CALL algo.pageRank({nodeLabel: "Customer", relationshipType: "REFERRED"})
    YIELD nodeId, score
    MATCH (c:Customer) WHERE id(c) = nodeId
    RETURN c.name, c.segment, score
    ORDER BY score DESC LIMIT 20

    -- Community detection — customer clusters (Ryugraph only)
    CALL algo.louvain({nodeLabel: "Customer", relationshipType: "CONNECTED_TO"})
    YIELD nodeId, communityId
    WITH communityId, count(*) AS size
    WHERE size > 50
    RETURN communityId, size
    ORDER BY size DESC
    ```

=== ":material-wifi: Network Topology"

    **The problem:** Telcos need to understand blast radius (if this node fails, what's affected?) and optimal routing — classic graph problems.

    ```cypher
    -- Blast radius of a node failure
    MATCH path = (failed:Node {id: "core-router-1"})-[:CONNECTED_TO*1..5]->(affected:Node)
    WHERE affected.type = "EndPoint"
    RETURN count(DISTINCT affected) AS endpoints_affected,
           max(length(path)) AS max_hops

    -- Shortest path between two endpoints
    MATCH (src:Node {id: "A"}), (dst:Node {id: "Z"})
    MATCH path = shortestPath((src)-[:CONNECTED_TO*]-(dst))
    RETURN [n IN nodes(path) | n.id] AS route, length(path) AS hops
    ```

---

## Why Not Just Use Neo4j?

| | Neo4j / TigerGraph | Graph OLAP |
| --- | --- | --- |
| Data freshness | Batch import or CDC — hours/days stale | Fresh warehouse export per instance |
| Self-service | Requires DBA/DevOps to provision | Analyst creates instance via API call |
| Isolation | Shared cluster | Dedicated pod per analyst |
| Cost model | Always-on licence + infra | Ephemeral pods — pay only when running |
| Data source | Separate from warehouse | Directly from Starburst / BigQuery |
| Setup time | Days to weeks | Under 30 minutes (local) |
| Analyst workflow | Export → load → query (separate tools) | Define mapping → create instance → query (one platform) |
