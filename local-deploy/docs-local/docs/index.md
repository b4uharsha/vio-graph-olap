<div class="hero">
  <h1>Graph OLAP Platform</h1>
  <p>Self-service graph analytics on top of your data warehouse.<br>
  Every analyst gets their own isolated, in-memory graph — spun up in seconds.</p>
  <div class="hero-buttons">
    <a href="setup/" class="hero-btn hero-btn-primary">Get Started →</a>
    <a href="flow/" class="hero-btn hero-btn-secondary">See How It Works</a>
  </div>
</div>

<div class="stat-bar">
  <div class="stat-card">
    <span class="stat-number">~10s</span>
    <span class="stat-label">Instance startup</span>
  </div>
  <div class="stat-card">
    <span class="stat-number">200k</span>
    <span class="stat-label">Rows/sec load speed</span>
  </div>
  <div class="stat-card">
    <span class="stat-number">2</span>
    <span class="stat-label">Graph engines (FalkorDB / KuzuDB)</span>
  </div>
  <div class="stat-card">
    <span class="stat-number">1</span>
    <span class="stat-label">API call to create a graph</span>
  </div>
</div>

---

## What Problem Are We Solving?

Modern data warehouses are brilliant at aggregating numbers — but they treat everything as **flat tables**. The moment you need to ask *relationship questions*, they struggle badly.

| What analysts need | What the industry offers today | The gap |
| --- | --- | --- |
| "Which customers share 3+ common suppliers?" | Complex recursive SQL or custom ETL pipelines | Hours to days of engineering |
| "Find all accounts within 2 hops of a flagged entity" | Separate graph DB requiring its own team to maintain | High operational overhead |
| "Detect circular payment chains" | Near-impossible with SQL CTEs at scale | Not feasible for most teams |
| "Run PageRank on my customer network" | Neo4j/TigerGraph — disconnected from the warehouse | Stale data, duplication, bespoke pipelines |

**The core problem:** Graph databases exist, but they're siloed from the data warehouse. Loading data into them requires custom ETL, dedicated engineers, and produces stale copies. Most organisations give up and write painful SQL instead.

---

## What's Missing in the Industry

=== ":material-clock-alert: Data Freshness"

    Existing graph tools (Neo4j, TigerGraph, Amazon Neptune) require data to be loaded via bulk import or CDC pipelines. By the time an analyst queries, the graph is hours or days out of date.

    **Graph OLAP:** Every instance is a fresh point-in-time export from the warehouse — always consistent with the source.

=== ":material-account-off: No Self-Service"

    Standing up a graph DB today means provisioning VMs, installing software, configuring auth, and writing a loader. A data analyst cannot do this themselves.

    **Graph OLAP:** An analyst creates a graph instance via a single API call or notebook cell. The platform handles everything.

=== ":material-share-variant: No Isolation"

    Shared graph databases mean one analyst's expensive traversal query degrades performance for everyone else.

    **Graph OLAP:** Each analyst gets their own dedicated pod with complete compute isolation. Pods auto-expire when done.

=== ":material-cash-remove: Always-On Cost"

    Traditional graph databases are always-on — always paying for compute even when no one is querying.

    **Graph OLAP:** Pods are ephemeral — created on demand, destroyed after TTL or inactivity. Pay only for what you use.

---

!!! tip "Where to go next"
    - **[Architecture](architecture.md)** — how the platform is built, all services explained
    - **[Flow](flow.md)** — step-by-step walkthrough from analyst to query result
    - **[Setup Guide](setup.md)** — get the full stack running in under 30 minutes
    - **[Loading Data](data.md)** — Starburst export or direct Parquet upload
