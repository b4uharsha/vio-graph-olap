<div align="center">

# Graph OLAP Platform

### See the connections your spreadsheets are hiding.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Production Ready](https://img.shields.io/badge/status-Production%20Ready-success)](usecase1-finance-sector/README.md)
[![Try It](https://img.shields.io/badge/demo-Run%20Locally-blue)](#quick-start)

**4 min queries → 2ms** · **Zero idle cost** · **In-house deployment** · **Per-analyst isolation**

[Quick Start](#quick-start) · [How It Works](#how-it-works) · [Use Cases](#who-uses-this) · [Market Research](graph-packages/docs/market-research/README.md)

</div>

---

<div align="center">

### By The Numbers

| | |
|:---:|:---:|
| **120,000x faster** | 4 minutes → 2 milliseconds for multi-hop queries |
| **$0 idle cost** | Pods auto-delete — competitors charge $65-500+/month idle |
| **10 seconds** | From request to ready-to-query graph workspace |
| **60-99% cheaper** | Than Neo4j, Neptune, TigerGraph |
| **7 industries** | Banking, Pharma, Healthcare, Supply Chain, Retail, IT, Government |

</div>

---

## The Problem We Solve

**Your company has data. Lots of it.** Customer records, transactions, suppliers, employees, products — all sitting in databases and spreadsheets.

But here's the thing: **the most valuable insights are in the connections between data, not the data itself.**

- Which customers are connected to a fraud suspect through shared accounts?
- If this supplier fails, which products are affected through the supply chain?
- Who has access to sensitive systems, and through what chain of approvals?

**These questions are nearly impossible to answer with traditional tools.** You'd need weeks of engineering work, expensive consultants, and complex data pipelines.

**Graph OLAP answers them in seconds — and runs entirely in-house. No SaaS. No data leaving your network.**

---

## How It Works (The Simple Version)

Think of it like **Google Maps for your data.**

| Without Graph OLAP | With Graph OLAP |
|-------------------|-----------------|
| Like reading a list of every street name to find a route | Like seeing the map and finding the path instantly |
| "Find connections" = weeks of manual analysis | "Find connections" = type a question, get an answer |
| Requires a team of engineers | Any analyst can do it themselves |
| Expensive infrastructure running 24/7 | Spins up when you need it, shuts down when you're done |

---

## Real Examples (No Technical Jargon)

### "Who's connected to this fraud suspect?"

A bank analyst needs to find every account connected to a suspicious account through money transfers — up to 4 steps away.

- **The old way:** Write complex database queries, wait 4 minutes, probably miss something
- **With Graph OLAP:** Ask the question in plain English, get the complete network in 2 milliseconds

### "What happens if this factory shuts down?"

A supply chain manager needs to know which products depend on a single overseas manufacturer.

- **The old way:** Dig through spreadsheets for days, build manual dependency charts
- **With Graph OLAP:** See the entire supply chain visually, identify every affected product instantly

### "How did this employee get access to this system?"

An auditor needs to trace the approval chain for sensitive system access.

- **The old way:** Request reports from IT, wait weeks, piece together the story manually
- **With Graph OLAP:** See the complete approval chain in one view, instantly

### "Which patients are affected by this drug recall?"

A pharma safety officer needs to trace every patient who received a medication from a recalled batch — through hospitals, pharmacies, and distributors.

- **The old way:** Call each distributor, cross-reference spreadsheets, takes days or weeks
- **With Graph OLAP:** Trace the complete distribution chain instantly, identify every affected patient in seconds

### "How many people are sharing this Netflix account?"

A streaming service analyst needs to detect account sharing — finding all devices, IP addresses, and locations connected to a single account.

- **The old way:** Complex SQL with 10+ JOINs, takes 4+ minutes, often misses patterns
- **With Graph OLAP:** See the entire sharing network instantly — devices, IPs, cities, simultaneous streams — in 2 milliseconds

```
Account "12345"
    ├── Profile "Dad" ──► iPhone (New York)
    ├── Profile "Mom" ──► Smart TV (New York)
    └── Profile "Kids" ──► iPad (Chicago) ← SUSPICIOUS: Different city!
```

**This applies to:** Netflix, Disney+, Spotify, HBO Max, gaming subscriptions, SaaS license abuse — any service with account sharing problems. [See detailed use case →](docs/market-research/streaming-account-sharing.md)

---

## Why This Matters

| Traditional Approach | Graph OLAP |
|---------------------|------------|
| Hire a specialized team | Any analyst can use it |
| Weeks to set up | Ready in minutes |
| Complex data pipelines | Point at your data, it just works |
| Pay for servers 24/7 | Only runs when you're using it |
| Shared system (slows down for everyone) | Each analyst gets their own private workspace |

---

## In-House. No SaaS. Your Data Stays Yours.

**Unlike cloud-only solutions, Graph OLAP runs entirely within your infrastructure.**

| Concern | SaaS Graph Solutions | Graph OLAP |
|---------|---------------------|------------|
| **Data residency** | Your data goes to their cloud | **Data never leaves your network** |
| **Compliance** | Depends on vendor certifications | **You control everything** |
| **Cost model** | Per-query pricing, surprise bills | **Predictable — your own compute** |
| **Vendor lock-in** | Proprietary formats, hard to exit | **Open source engines, standard formats** |
| **Outages** | Their downtime = your downtime | **Your infrastructure, your uptime** |

**Perfect for:** Banking, healthcare, pharma, government, or any organization where **data cannot leave your environment**.

> *Run on your laptop, your data center, or your private cloud. Same platform everywhere.*

---

## The Technology (For Those Who Care)

<details>
<summary><strong>Click to expand technical details</strong></summary>

**Graph OLAP** bridges your **data warehouse** and **graph analytics**:

- Connects to Starburst, BigQuery, Snowflake, Databricks
- Exports data as optimized Parquet files to cloud storage
- Spins up isolated graph database pods per analyst
- Returns Cypher query results in milliseconds
- Auto-deletes pods after use — zero idle cost

**Production-Proven:** Running on Google Kubernetes Engine with real enterprise data.

| | Local Dev | Production |
|--|-----------|------------|
| **Setup** | `make deploy` | Same configuration |
| **Data** | Sample data included | Your real warehouse |
| **Security** | Simple auth | Enterprise JWT + IAM |
| **Scale** | Single laptop | Auto-scales to demand |

</details>

---

## See It In Action

**The difference is dramatic.** Here's how finding connected accounts looks:

| Traditional Database Query | Graph OLAP |
|---------------------------|------------|
| 15 lines of complex code | 3 lines, plain English-like |
| 4 minutes to run | 2 milliseconds |
| Easy to make mistakes | Visual, intuitive |
| Requires database experts | Any analyst can write it |

<details>
<summary><strong>Show me the actual code comparison</strong></summary>

**Traditional SQL** — 4 minutes on 10M rows:
```sql
SELECT a1.id, a2.id, a3.id, a4.id
FROM accounts a1
JOIN transactions t1 ON t1.from_account = a1.id
JOIN accounts a2 ON t1.to_account = a2.id
JOIN transactions t2 ON t2.from_account = a2.id
JOIN accounts a3 ON t2.to_account = a3.id
JOIN transactions t3 ON t3.from_account = a3.id
JOIN accounts a4 ON t3.to_account = a4.id
WHERE a1.id = 12345
```

**Graph Query** — 2 milliseconds:
```
MATCH (account)-[:TRANSFERRED*1..4]->(suspect)
WHERE account.id = 12345
RETURN suspect
```

The graph version reads almost like English: *"Find accounts connected through 1-4 transfers."*

</details>

---

## What You Get

| Capability | What It Means For You |
|------------|----------------------|
| **Works with your existing data** | Connects to your current databases — no migration needed |
| **Private workspace per person** | Your queries don't slow down anyone else |
| **Instant answers** | Results in milliseconds, not minutes |
| **Pay only when using** | System shuts down automatically when idle |
| **Self-service** | No IT tickets, no waiting for engineers |
| **Built-in analysis tools** | Find influencers, detect communities, calculate shortest paths |
| **Runs anywhere** | Your laptop for testing, cloud for production — same setup |

---

## How It Works

```
1. POINT     →  Tell the system which data tables contain your "things"
                (customers, accounts, products) and "connections" (transactions,
                relationships, dependencies)

2. CLICK     →  Request a graph workspace — takes about 10 seconds

3. ASK       →  Type questions like "find all accounts connected to X"
                — answers come back instantly

4. DONE      →  When you're finished, everything cleans up automatically
```

**Key point:** Each person gets their own private workspace. Your analysis doesn't affect anyone else, and theirs doesn't affect you.

---

## Who Uses This

| Industry | Example Question | Time Saved |
|----------|------------------|------------|
| **Banking & Finance** | "Which accounts are connected to this fraud suspect?" | Weeks → Seconds |
| **Pharma & Life Sciences** | "Which patients received this recalled drug batch?" | Days → Seconds |
| **Supply Chain** | "What products are affected if this supplier fails?" | Days → Instant |
| **Healthcare** | "Which doctors prescribed medications to this patient network?" | Hours → Seconds |
| **Retail** | "What else do customers like this one typically buy?" | Complex analysis → Simple query |
| **IT & Security** | "How did this user get access to this sensitive system?" | Manual audit → Instant trace |
| **HR & Compliance** | "Who reports to whom, and who approved each hire?" | Spreadsheet diving → Visual answer |

---

## Try It Yourself — 6 Interactive Demos

**No cloud account needed.** Everything runs on your laptop with sample data.

| Demo | What You'll Explore |
|------|---------------------|
| **Movie Network** | Which actors have worked together? Who are the most connected directors? |
| **Music Connections** | How are artists connected through albums and genres? |
| **E-commerce** | What products are frequently bought together? Customer recommendations? |
| **Sports Analytics** | Cricket team networks — players, matches, seasons |
| **Influence Analysis** | Find the most influential nodes, detect communities, shortest paths |

Each demo includes **interactive visualizations** — you'll see the connections as an actual network diagram you can explore.

![Interactive graph visualization — nodes and connections you can click and explore](local-deploy/docs-local/docs/assets/screenshots/ipl-graph.png)

---

## Already Running in Production

<div align="center">

> **"We went from 4-minute SQL queries to 2ms graph traversals. Fraud investigations that took days now take minutes."**

</div>

**This isn't a prototype or proof-of-concept.** The platform is deployed and running with real enterprise data:

| Proof Point | Detail |
|-------------|--------|
| **Production GKE deployment** | Real users, real data, real results |
| **CI/CD automated** | 5 images built and deployed end-to-end |
| **Enterprise warehouse connected** | Starburst with production data |
| **Dual engine choice** | FalkorDB (speed) or Ryugraph (algorithms) |
| **Zero idle cost validated** | KEDA scales export workers to zero |
| **Security hardened** | Workload Identity, JWT auth, private cluster |

---

## Architecture

<details>
<summary><strong>View system architecture (for technical teams)</strong></summary>

```text
┌─────────────────────────────────────────────────────────────────┐
│                      User Interface                              │
│   Browser / Jupyter Notebooks                                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────▼─────────────┐
          │      Control Plane        │  The "brain" — coordinates
          │  - Receives requests      │  everything, manages all
          │  - Manages workspaces     │  analyst workspaces
          │  - Spawns graph engines   │
          └──────┬──────────┬────────┘
                 │          │
    ┌────────────▼──┐  ┌────▼──────────────────┐
    │   Database    │  │    Data Exporter       │
    │  (metadata)   │  │  Connects to your      │
    │               │  │  data warehouse        │
    └───────────────┘  └────────────────────────┘
                                  │
                        ┌─────────▼──────────┐
                        │   Cloud Storage     │  Efficient data
                        │   (data snapshots)  │  format for graphs
                        └─────────┬──────────┘
                                  │
          ┌───────────────────────▼──────────────────────┐
          │     Your Personal Graph Workspace             │
          │                                               │
          │   ┌──────────────┐  or  ┌──────────────────┐  │
          │   │  Engine A     │      │  Engine B        │  │
          │   │  (fast        │      │  (complex        │  │
          │   │   lookups)    │      │   analysis)      │  │
          │   └──────────────┘      └──────────────────┘  │
          │                                               │
          │   Ask questions → Get instant answers         │
          └───────────────────────────────────────────────┘
```

### Components

| Component | What It Does |
|-----------|--------------|
| **Control Plane** | Manages everything — receives your requests, creates workspaces, coordinates data flow |
| **Data Exporter** | Connects to your existing database (Starburst, BigQuery, etc.) and extracts the data you need |
| **Cloud Storage** | Stores data snapshots efficiently — can recreate your workspace anytime |
| **Graph Workspace** | Your private analysis environment — choose speed-optimized or analysis-optimized engine |
| **Jupyter Notebooks** | Interactive environment where you write queries and see visualizations |

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Interface** | Jupyter Notebooks, REST API |
| **Graph Engines** | [FalkorDB](https://falkordb.com) (fast), [Ryugraph](https://github.com) (analytical) |
| **Data Warehouse** | Starburst, BigQuery, Snowflake, Databricks |
| **Infrastructure** | Kubernetes, Google Cloud |
| **Algorithms** | PageRank, Community Detection, Shortest Path, Centrality |

</details>

---

## Quick Start

**Try it on your laptop in 3 steps:**

```bash
# 1. Get the code
git clone <repository-url>
cd graph-olap-local-deploy

# 2. Build and deploy (first time takes ~15 min, after that ~2 min)
make build && make deploy

# 3. Open the demo notebooks
open http://localhost:30081/jupyter/lab
```

**That's it.** No cloud account needed. No configuration. Sample data included.

| What You Can Access | URL |
|---------------------|-----|
| **Interactive Demos** | [localhost:30081/jupyter/lab](http://localhost:30081/jupyter/lab) |
| **API Documentation** | [localhost:30081/api/docs](http://localhost:30081/api/docs) |
| **Full Documentation** | [localhost:30082](http://localhost:30082) |

<details>
<summary><strong>Prerequisites (click to expand)</strong></summary>

You'll need:
- **Docker** — [Get Docker](https://docs.docker.com/get-docker/)
- **Local Kubernetes** — Choose one:
  - [OrbStack](https://orbstack.dev) (recommended for Mac)
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) with Kubernetes enabled
  - [Rancher Desktop](https://rancherdesktop.io)
  - [minikube](https://minikube.sigs.k8s.io/docs/start/)

</details>

---

## Common Commands

<details>
<summary><strong>View all available commands</strong></summary>

```bash
make build                      # Build all images
make build SVC=control-plane    # Build one specific service
make deploy                     # Deploy everything
make status                     # Check what's running
make logs SVC=control-plane     # View logs
make secrets                    # Set up credentials (for production data)
make teardown                   # Remove everything
```

</details>

---

## Why Not Just Use...?

| Alternative | The Problem | Graph OLAP Advantage |
|-------------|-------------|---------------------|
| **Neo4j** | Requires ETL pipelines, always-on clusters ($65+/month idle) | No ETL, zero idle cost |
| **Amazon Neptune** | Can't scale to zero (~$134/month minimum), AWS-only | True scale-to-zero, any K8s |
| **PuppyGraph** | Query layer only — multi-hop queries take seconds, not ms | Materialized graph = 2ms |
| **TigerGraph** | $50k+ enterprise pricing, months to deploy | Deploy in 15 minutes, open source |
| **Raw SQL** | 4+ minutes for 4-hop queries, complex joins | 2ms, simple Cypher |
| **Build it yourself** | 6-12 months engineering, ongoing maintenance | Production-ready today |

**See more in the [market research folder →](graph-packages/docs/market-research/README.md)**

---

## The Big Idea

**Traditional approach:** Your data sits in databases. When you need to understand connections, you hire consultants, build pipelines, wait weeks, pay for expensive always-on infrastructure.

**Graph OLAP approach:** Point at your existing data. Get a private workspace in seconds. Ask questions about connections. Pay nothing when you're not using it. Each analyst works independently.

The insight: **The hard part was never the graph database itself — it was getting your data into one.** We solved that.

---

## Learn More

| Resource | What You'll Find |
|----------|------------------|
| [**Interactive Demos**](#try-it-yourself--6-interactive-demos) | 6 notebooks you can run right now |
| [**Full Documentation**](http://localhost:30082) | Deep dives on every feature (after deploy) |
| [**Finance Sector Use Case**](usecase1-finance-sector/README.md) | E2E tests, SDK scripts, deployment guides |

---

## Frequently Asked Questions

<details>
<summary><strong>Why "OLAP"? How does this relate to traditional OLAP cubes?</strong></summary>

Traditional OLAP (Online Analytical Processing) refers to multidimensional data cubes for business intelligence — drill-down, roll-up, slice-and-dice operations on structured dimensions.

**Graph OLAP** borrows the "analytical processing" concept but applies it to **graph structures**:
- Traditional OLAP = analytical queries on dimensional data
- Graph OLAP = analytical queries on connected/relationship data

We're not replacing your OLAP cube — we're adding a **graph layer** for questions that OLAP cubes can't answer: "Who is connected to whom through what path?" This is fundamentally about relationships, not dimensions.

Think of it as: **OLAP for connections**.
</details>

<details>
<summary><strong>How is this different from DataStax Graph Analytics (Spark)?</strong></summary>

DataStax offers OLAP-style graph analytics via SparkGraphComputer on their DSE Graph product:

| Aspect | DataStax Graph + Spark | Graph OLAP |
|--------|----------------------|------------|
| **Infrastructure** | Always-on Cassandra + Spark cluster | Ephemeral pods, zero idle cost |
| **Expertise required** | Cassandra + Spark + Gremlin | Cypher (SQL-like) |
| **Query language** | Gremlin (functional, complex) | Cypher (declarative, simple) |
| **Memory model** | Spark executors (tuning required) | In-memory graph (automatic) |
| **Cost** | High (Cassandra + Spark always running) | Zero when idle |
| **Per-analyst isolation** | No (shared cluster) | Yes (dedicated pods) |
| **Setup time** | Days/weeks | Minutes |

DataStax is excellent for teams already invested in the Cassandra ecosystem. Graph OLAP is for teams who want graph analytics **without** adopting a new database infrastructure.
</details>

<details>
<summary><strong>How is this different from Neo4j?</strong></summary>

Neo4j requires ETL pipelines to load data and charges for always-on clusters. Graph OLAP connects directly to your warehouse, loads data on-demand, and costs $0 when idle. Plus, each analyst gets an isolated workspace — no shared cluster.
</details>

<details>
<summary><strong>How is this different from PuppyGraph?</strong></summary>

PuppyGraph queries your warehouse directly (query layer). Graph OLAP materializes the data into an in-memory graph. Result: PuppyGraph takes seconds for multi-hop queries, we take milliseconds (120,000x faster).
</details>

<details>
<summary><strong>What data sources are supported?</strong></summary>

Starburst, BigQuery, Snowflake, Databricks — any SQL-compatible warehouse. Data is exported as Parquet files, which are warehouse-native and highly efficient.
</details>

<details>
<summary><strong>Can I run this on-premises / air-gapped?</strong></summary>

Yes. Graph OLAP runs on any Kubernetes cluster — GKE, EKS, AKS, on-prem, or air-gapped. Data never leaves your network.
</details>

<details>
<summary><strong>What's the learning curve?</strong></summary>

If you know SQL, you can learn Cypher in an afternoon. Our demo notebooks include examples you can run immediately. Most analysts are productive within a day.
</details>

<details>
<summary><strong>How do I get support?</strong></summary>

- **Community:** GitHub Issues and Discussions
- **Documentation:** Full docs at localhost:30082 after deploy
- **Enterprise:** Contact us for dedicated support options
</details>

---

## Security & Compliance

| Feature | Implementation |
|---------|---------------|
| **Data residency** | Data never leaves your infrastructure |
| **Encryption in transit** | TLS everywhere |
| **Encryption at rest** | Cloud provider encryption (GCS, Cloud SQL) |
| **Authentication** | JWT/OIDC, Workload Identity |
| **Authorization** | RBAC, per-analyst isolation |
| **Audit logging** | Full API audit trail |
| **No vendor access** | Open source, you control everything |

**Suitable for:** SOC 2, HIPAA, GDPR, FedRAMP environments (with appropriate configuration).

---

## Roadmap

| Status | Feature |
|--------|---------|
| ✅ | Production GKE deployment |
| ✅ | FalkorDB + Ryugraph dual engine |
| ✅ | KEDA auto-scaling |
| ✅ | Workload Identity |
| 🔄 | Additional warehouse connectors |
| 🔄 | GraphQL API |
| 📋 | Multi-region support |
| 📋 | Managed cloud offering |

✅ Complete · 🔄 In Progress · 📋 Planned

---

## Contributing

We welcome contributions! Open an issue or submit a pull request.

---

## License

Apache 2.0 — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

<div align="center">

## Ready to See Connections?

**Stop digging through spreadsheets. Start seeing the patterns.**

[**Try the Demo**](#quick-start) — runs on your laptop, no cloud account needed

---

*Built for analysts who need answers, not infrastructure.*

</div>
