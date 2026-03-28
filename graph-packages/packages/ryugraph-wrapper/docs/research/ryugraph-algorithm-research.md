# Ryugraph/KuzuDB Research Report

## Executive Summary

This report analyzes Ryugraph (a fork of KuzuDB) capabilities, current implementation gaps, and recommendations for making the E2E tests pass for data loading, Cypher queries, and graph algorithms.

## 1. Ryugraph/KuzuDB Architecture

### 1.1 Background

[Ryugraph](https://ryugraph.io/) is a community fork of [KuzuDB](https://kuzudb.com/), an embedded property graph database. KuzuDB was archived in October 2025, and Ryugraph continues development under Predictable Labs. The database:

- **Implements Cypher** query language
- **Is embedded** - runs in-process without external server
- **Uses columnar storage** with disk-based execution
- **Supports Parquet, Arrow, DuckDB** interoperability
- **Provides algo extension** for native graph algorithms

### 1.2 Key Differences from Neo4j

| Feature | KuzuDB/Ryugraph | Neo4j |
|---------|-----------------|-------|
| Schema | **Required** (CREATE NODE/REL TABLE) | Optional |
| Primary Keys | **Required** on node tables | Optional |
| Multi-labels | Not supported | Supported |
| Path Semantics | Walk (allows edge repetition) | Trail (no repetition) |
| Variable-length upper bound | Required (default 30) | Optional |
| List indexing | **1-based** | 0-based |
| Aggregate in SET | **Not supported** | Supported |
| REMOVE property | **Not supported** | Supported |

---

## 2. Data Loading from Parquet

### 2.1 Official KuzuDB Approach

```sql
-- Create schema first
CREATE NODE TABLE Person(id STRING PRIMARY KEY, name STRING, age INT64);
CREATE REL TABLE KNOWS(FROM Person TO Person, since INT64);

-- Load data (nodes first, then edges)
COPY Person FROM 'person.parquet';
COPY KNOWS FROM 'knows.parquet';
```

**Rules:**
1. Parquet column order must match table property order
2. Nodes must exist before loading edges that reference them
3. Relationship parquet must have FROM/TO columns as first two columns

### 2.2 Current Implementation Analysis

The current `database.py` implementation:
- Downloads Parquet from GCS to temp directory
- Executes `COPY FROM '*.parquet'` for each table
- Handles both nodes and edges with proper ordering

**Issue Found:** The E2E tests fail during k3d cluster setup, not during data loading itself. Data loading code is correct.

---

## 3. Cypher Query Execution

### 3.1 KuzuDB Cypher Dialect

KuzuDB implements Cypher with these specifics:

```cypher
-- Standard queries work
MATCH (p:Person) WHERE p.age > 30 RETURN p.name ORDER BY p.name

-- Parameterized queries
MATCH (p:Person {name: $name}) RETURN p.age

-- Variable-length paths (requires upper bound)
MATCH (a)-[:KNOWS*1..5]->(b) RETURN a, b

-- Aggregations
MATCH (p:Person) RETURN avg(p.age), count(p)
```

### 3.2 Current Implementation Status

The wrapper correctly:
- Executes queries via thread pool (async-over-sync pattern)
- Extracts results using `has_next()/get_next()` (avoids broken `get_as_pl()`)
- Handles timeouts and parameters
- Blocks mutation operations in read-only mode

**Status:** ✅ Query execution tests pass when cluster is available.

---

## 4. Native Algorithm Implementation

### 4.1 KuzuDB Algo Extension (Preferred Approach)

KuzuDB provides a native `algo` extension with disk-based algorithms:

```sql
-- Install and load extension (pre-loaded in v0.11.3+)
INSTALL algo;
LOAD algo;

-- Create projected graph
CALL project_graph('MyGraph', ['Person'], ['KNOWS']);

-- Run algorithms
CALL page_rank('MyGraph') RETURN node, rank;
CALL weakly_connected_components('MyGraph') RETURN node, component;
CALL louvain('MyGraph') RETURN node, community;
CALL strongly_connected_components('MyGraph') RETURN node, component;
```

**Available Algorithms:**
- PageRank
- Weakly Connected Components (WCC)
- Strongly Connected Components (SCC)
- Louvain (community detection)
- K-Core decomposition

### 4.2 Current Implementation Analysis

The current `native.py` implements algorithms **using iterative Cypher queries**, NOT the algo extension:

```python
# Current approach (problematic)
async def execute(self, ...):
    init_query = f"MATCH (n:{node_label}) SET n.{result_property} = {init_value}"
    for i in range(max_iter):
        update_query = f"MATCH (n)... SET n.{prop}_new = ..."
```

**Problems:**
1. **Cannot use aggregates in SET clauses** - Kuzu limitation
2. **CASE WHEN syntax issues** - Different from Neo4j
3. **No REMOVE support** - Cannot clean up temp properties
4. **Performance** - Iterative queries are much slower than native algo extension

### 4.3 Recommendation: Use Algo Extension

**Replace iterative Cypher with algo extension calls:**

```python
async def execute_pagerank(self, db_service, node_label, edge_type, result_property, parameters):
    # Create projected graph
    await db_service.execute_query(
        f"CALL project_graph('TempGraph', ['{node_label}'], ['{edge_type}'])"
    )

    # Run PageRank
    damping = parameters.get('damping_factor', 0.85)
    max_iter = parameters.get('max_iterations', 20)
    tolerance = parameters.get('tolerance', 1e-6)

    result = await db_service.execute_query(
        f"""
        CALL page_rank('TempGraph', {{
            dampingFactor: {damping},
            maxIterations: {max_iter},
            tolerance: {tolerance}
        }})
        RETURN node, rank
        """
    )

    # Write results back to nodes
    await self._write_results(db_service, result, node_label, result_property)

    # Drop projected graph
    await db_service.execute_query("CALL drop_projected_graph('TempGraph')")
```

---

## 5. NetworkX Algorithm Integration

### 5.1 KuzuDB to NetworkX Conversion

KuzuDB provides `get_as_networkx()` for direct conversion:

```python
# Official approach
result = conn.execute("MATCH (n)-[r]->(m) RETURN *")
G = result.get_as_networkx(directed=True)
```

### 5.2 Current Implementation Analysis

The current `networkx.py`:
1. **Extracts graph manually** using `offset(id(n))` queries
2. **Runs NetworkX algorithms** on extracted graph
3. **Writes results back** using batch UNWIND queries

**Issues Found:**
- Uses `offset(id(n))` which returns integer offsets - this is correct
- Uses `update[1]` and `update[2]` for 1-based indexing - this is correct
- The error `"unhashable type: 'dict'"` occurred when using `id(n)` instead of `offset(id(n))` - now fixed

### 5.3 Static vs Dynamic NetworkX APIs

**Static Algorithms** (pre-registered, called by name):
```python
# Current implementation - works
POST /networkx/betweenness_centrality
{"node_label": "Person", "edge_type": "KNOWS", "result_property": "bc"}
```

**Dynamic Algorithms** (discovered at runtime):
```python
# Current implementation - list_algorithms()
GET /networkx/algorithms?category=centrality
# Returns available algorithms discovered via introspection
```

The wrapper supports both through the algorithm registry:
- 16+ common algorithms pre-registered at startup
- Dynamic discovery via `discover_algorithm(name)` introspection

---

## 6. Test Failure Analysis

### 6.1 E2E Test Results Summary

| Category | Passing | Failing | Root Cause |
|----------|---------|---------|------------|
| Health/Ready | 3 | 0 | ✅ Working |
| Cypher Queries | 7 | 0 | ✅ Working |
| Schema | 1 | 0 | ✅ Working |
| Native Algorithms | 0 | 3 | Cypher syntax incompatibility |
| NetworkX Algorithms | 0 | 5 | Query syntax issues |
| Locking | 0 | 2 | Depends on algorithm execution |
| Persistence | 0 | 2 | Depends on algorithm execution |

### 6.2 Specific Errors

**Native PageRank:**
```
Cannot evaluate expression with type AGGREGATE_FUNCTION
```
- Cause: `SET n.prop = 1.0 / count(n)` not allowed in Kuzu

**Native WCC:**
```
Function GREATEST did not receive correct arguments
```
- Cause: `greatest(INT64, INT64)` not supported

**NetworkX Betweenness:**
```
List extract takes 1-based position
```
- Cause: Using `update[0]` instead of `update[1]`

---

## 7. Recommendations

### 7.1 Priority 1: Use Algo Extension for Native Algorithms

Replace iterative Cypher with native algo extension:

```python
# PageRank
CALL project_graph('G', ['Person'], ['KNOWS']);
CALL page_rank('G') RETURN node, rank;

# WCC
CALL weakly_connected_components('G') RETURN node, component;

# Louvain (Label Propagation replacement)
CALL louvain('G') RETURN node, community;
```

### 7.2 Priority 2: Fix NetworkX Graph Extraction

Use `get_as_networkx()` instead of manual query:

```python
async def _extract_graph(self, db_service, node_label, edge_type, subgraph_query):
    if subgraph_query:
        result = await db_service.execute_query(subgraph_query)
    else:
        query = f"MATCH (n:{node_label})-[r:{edge_type}]->(m:{node_label}) RETURN *"
        result = await db_service.execute_query(query)

    # Use native conversion if available
    if hasattr(result, 'get_as_networkx'):
        return result.get_as_networkx(directed=True)

    # Fallback to manual construction
    ...
```

### 7.3 Priority 3: Simplify Result Writeback

Use ALTER TABLE + LOAD FROM for bulk updates:

```python
async def _write_results(self, db_service, results, node_label, result_property):
    # Ensure property exists
    await db_service.execute_query(
        f"ALTER TABLE {node_label} ADD IF NOT EXISTS {result_property} DOUBLE DEFAULT 0.0"
    )

    # Convert to DataFrame
    df = pd.DataFrame(list(results.items()), columns=['_node_id', result_property])

    # Use LOAD FROM to update
    await db_service.execute_query(
        f"""
        LOAD FROM df
        WITH * MATCH (n:{node_label})
        WHERE offset(id(n)) = _node_id
        SET n.{result_property} = {result_property}
        """
    )
```

---

## 8. Sources

- [KuzuDB Python API](https://docs.kuzudb.com/client-apis/python/)
- [KuzuDB Import Parquet](https://docs.kuzudb.com/import/parquet/)
- [KuzuDB Create Table](https://docs.kuzudb.com/cypher/data-definition/create-table/)
- [KuzuDB Algo Extension](https://docs.kuzudb.com/extensions/algo/)
- [KuzuDB PageRank](https://docs.kuzudb.com/extensions/algo/pagerank/)
- [KuzuDB WCC](https://docs.kuzudb.com/extensions/algo/wcc/)
- [KuzuDB Louvain](https://docs.kuzudb.com/extensions/algo/louvain/)
- [KuzuDB ALTER TABLE](https://docs.kuzudb.com/cypher/data-definition/alter/)
- [Ryugraph GitHub](https://github.com/predictable-labs/ryugraph)
- [NetworkX Centrality](https://networkx.org/documentation/stable/reference/algorithms/centrality.html)
