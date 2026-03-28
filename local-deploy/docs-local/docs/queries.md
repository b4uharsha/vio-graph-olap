# Query Cookbook

Ready-to-run Cypher queries organised by category. All examples use the TPC-H demo dataset but apply to any graph with similar structure.

!!! info "Running queries"
    Queries go directly to the wrapper pod. The easiest way is via the SDK inside Jupyter Labs:

    ```python
    conn = client.instances.connect(instance_id)
    conn.query("<paste query here>").df()
    ```

    Or port-forward the wrapper pod and use curl from your laptop:

    ```bash
    kubectl port-forward -n graph-olap-local pod/<wrapper-pod-name> 8000:8000
    curl -s -X POST http://localhost:8000/query \
      -H "Content-Type: application/json" \
      -d '{"query": "<paste query here>"}'
    ```

---

## Basic Lookups

=== "Count all nodes by label"

    ```cypher
    MATCH (n)
    RETURN labels(n)[0] AS label, count(n) AS total
    ORDER BY total DESC
    ```

=== "Find a node by property"

    ```cypher
    MATCH (c:Customer {name: "Alice Corp"})
    RETURN c
    ```

=== "Get all neighbours of a node"

    ```cypher
    MATCH (c:Customer {custkey: 1})-[r]-(neighbour)
    RETURN type(r) AS relationship,
           labels(neighbour)[0] AS type,
           neighbour.name AS name
    ```

=== "List all relationship types"

    ```cypher
    MATCH ()-[r]->()
    RETURN DISTINCT type(r) AS relationship, count(r) AS count
    ORDER BY count DESC
    ```

---

## Aggregations

=== "Customers per nation"

    ```cypher
    MATCH (c:Customer)-[:BELONGS_TO]->(n:Nation)
    RETURN n.name, count(c) AS customers
    ORDER BY customers DESC
    ```

=== "Revenue by market segment"

    ```cypher
    MATCH (c:Customer)-[:PLACED]->(o:SalesOrder)
    RETURN c.mktsegment, sum(o.totalprice) AS revenue, count(o) AS orders
    ORDER BY revenue DESC
    ```

=== "Top 10 customers by spend"

    ```cypher
    MATCH (c:Customer)-[:PLACED]->(o:SalesOrder)
    RETURN c.name, c.mktsegment, sum(o.totalprice) AS total_spend
    ORDER BY total_spend DESC
    LIMIT 10
    ```

=== "Average account balance per nation"

    ```cypher
    MATCH (c:Customer)-[:BELONGS_TO]->(n:Nation)
    RETURN n.name,
           round(avg(c.acctbal) * 100) / 100 AS avg_balance,
           min(c.acctbal) AS min_balance,
           max(c.acctbal) AS max_balance
    ORDER BY avg_balance DESC
    ```

---

## Relationship Queries

=== "Customers sharing the same nation"

    ```cypher
    MATCH (c1:Customer)-[:BELONGS_TO]->(n:Nation)<-[:BELONGS_TO]-(c2:Customer)
    WHERE c1.custkey < c2.custkey
      AND c1.mktsegment = c2.mktsegment
    RETURN n.name, c1.name, c2.name, c1.mktsegment AS segment
    LIMIT 20
    ```

=== "Nations with customers in multiple segments"

    ```cypher
    MATCH (c:Customer)-[:BELONGS_TO]->(n:Nation)
    WITH n, collect(DISTINCT c.mktsegment) AS segments
    WHERE size(segments) > 3
    RETURN n.name, size(segments) AS segment_count, segments
    ORDER BY segment_count DESC
    ```

=== "Customers with no orders"

    ```cypher
    MATCH (c:Customer)
    WHERE NOT (c)-[:PLACED]->(:SalesOrder)
    RETURN c.name, c.acctbal, c.mktsegment
    ORDER BY c.acctbal DESC
    ```

---

## Path Queries

=== "Shortest path between two customers"

    ```cypher
    MATCH (a:Customer {custkey: 1}), (b:Customer {custkey: 100})
    MATCH path = shortestPath((a)-[*]-(b))
    RETURN [n IN nodes(path) | coalesce(n.name, labels(n)[0])] AS path,
           length(path) AS hops
    ```

=== "All paths up to 3 hops"

    ```cypher
    MATCH (c:Customer {custkey: 1}),
          path = (c)-[*1..3]-(other)
    RETURN DISTINCT other.name, labels(other)[0] AS type,
           length(path) AS distance
    ORDER BY distance, other.name
    ```

=== "Check if two nodes are connected"

    ```cypher
    MATCH (a:Customer {custkey: 1}), (b:Nation {nationkey: 5})
    RETURN exists((a)-[*1..5]-(b)) AS connected
    ```

---

## Graph Algorithms *(Ryugraph / KuzuDB only)*

=== "PageRank — most influential nodes"

    ```cypher
    CALL algo.pageRank({
      nodeLabel: "Customer",
      relationshipType: "BELONGS_TO",
      dampingFactor: 0.85,
      iterations: 20
    })
    YIELD nodeId, score
    MATCH (c:Customer) WHERE id(c) = nodeId
    RETURN c.name, c.mktsegment, round(score * 1000) / 1000 AS pagerank
    ORDER BY pagerank DESC
    LIMIT 20
    ```

=== "BFS — breadth-first search"

    ```cypher
    CALL algo.bfs({
      startNodeId: 1,
      nodeLabel: "Customer",
      relationshipType: "BELONGS_TO"
    })
    YIELD nodeId, distance
    MATCH (c:Customer) WHERE id(c) = nodeId
    RETURN c.name, distance
    ORDER BY distance, c.name
    ```

=== "Community Detection (Louvain)"

    ```cypher
    CALL algo.louvain({
      nodeLabel: "Customer",
      relationshipType: "BELONGS_TO"
    })
    YIELD nodeId, communityId
    WITH communityId, count(*) AS members
    WHERE members > 5
    RETURN communityId, members
    ORDER BY members DESC
    ```

---

## Filtering & Conditions

=== "Nodes matching a range condition"

    ```cypher
    MATCH (c:Customer)
    WHERE c.acctbal > 5000 AND c.mktsegment = "FINANCE"
    RETURN c.name, c.acctbal
    ORDER BY c.acctbal DESC
    LIMIT 20
    ```

=== "String pattern matching"

    ```cypher
    MATCH (c:Customer)
    WHERE c.name STARTS WITH "A" OR c.name CONTAINS "Corp"
    RETURN c.name, c.mktsegment
    ORDER BY c.name
    ```

=== "Nodes with multiple relationship types"

    ```cypher
    MATCH (c:Customer)
    WHERE (c)-[:PLACED]->(:SalesOrder)
      AND (c)-[:BELONGS_TO]->(:Nation {name: "UNITED KINGDOM"})
    RETURN c.name, c.acctbal
    ORDER BY c.acctbal DESC
    ```

---

## Useful Patterns

=== "Parameterised query (Python SDK)"

    ```python
    from graph_olap import GraphOLAPClient

    client = GraphOLAPClient(base_url="http://localhost:30081", username="you@example.com", role="analyst")

    results = client.query(
        instance_id=7,
        query="MATCH (c:Customer) WHERE c.acctbal > $min_balance RETURN c.name, c.acctbal",
        parameters={"min_balance": 5000}
    )
    ```

=== "Pagination"

    ```cypher
    -- Page 2 of customers (20 per page)
    MATCH (c:Customer)
    RETURN c.name, c.acctbal
    ORDER BY c.custkey
    SKIP 20 LIMIT 20
    ```

=== "Collecting results into a list"

    ```cypher
    MATCH (n:Nation)<-[:BELONGS_TO]-(c:Customer)
    WITH n, collect(c.name)[..5] AS sample_customers, count(c) AS total
    RETURN n.name, total, sample_customers
    ORDER BY total DESC
    ```

=== "Conditional return with CASE"

    ```cypher
    MATCH (c:Customer)
    RETURN c.name,
           CASE
             WHEN c.acctbal > 8000 THEN "High value"
             WHEN c.acctbal > 4000 THEN "Mid value"
             ELSE "Low value"
           END AS tier
    ORDER BY c.acctbal DESC
    ```
