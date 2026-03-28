# Market Research & Competitive Analysis

> **Graph OLAP's unique position:** Ephemeral, per-analyst, warehouse-native, in-house graph analytics with zero idle cost.

## Why "OLAP"?

**Traditional OLAP** (Online Analytical Processing) = Multidimensional cubes for business intelligence (drill-down, roll-up, slice-and-dice on structured dimensions).

**Graph OLAP** = Analytical processing on **graph structures** — relationships and connections, not dimensions.

| Traditional OLAP | Graph OLAP |
|-----------------|------------|
| "What were sales by region and quarter?" | "Who is connected to this fraud suspect through 4 hops?" |
| Dimensional analysis | Relationship analysis |
| Cubes and hierarchies | Nodes and edges |
| Aggregations | Traversals |

**We're not replacing your OLAP cube.** We're adding a graph layer for questions that cubes can't answer — questions about **paths, connections, and networks**.

## Contents

| Document | Description |
|----------|-------------|
| [Public Sector Use Cases](public-sector-use-cases.md) | Government fraud detection, healthcare, tax |
| [Streaming Account Sharing](streaming-account-sharing.md) | Detect account sharing patterns |
| [Platform & DevOps Guide](platform-devops-guide.md) | How to deploy as an internal platform service |

---

## Executive Summary

### The Market Opportunity

The graph database market is projected to grow from **$3.3B (2025) → $11.4B (2030)** at **27.9% CAGR**. Large enterprises hold 59.5% of the market, but SMEs are the fastest-growing segment at 30.1% CAGR.

### What Makes Graph OLAP Unique

| Feature | Graph OLAP | Competitors |
|---------|------------|-------------|
| **Per-analyst isolation** | Dedicated pod per user | Shared clusters |
| **Zero idle cost** | Pods auto-delete | Always-on billing |
| **In-house deployment** | Your infrastructure | SaaS / cloud-only |
| **Materialized graph** | In-memory, sub-ms queries | Query layer over warehouse |
| **Self-service** | Analyst-driven | Requires engineering |

### Key Differentiators

1. **Ephemeral workspaces** — No one else offers true per-analyst isolated pods that auto-delete
2. **Zero idle cost** — Neptune/Neo4j can't scale to zero; we can
3. **In-house first** — Data never leaves your network (critical for regulated industries)
4. **Materialized + Warehouse-native** — Best of both worlds (unlike PuppyGraph which is query-only)

### Competitive Positioning Map

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    DEPLOYMENT MODEL                      │
                    │     SaaS-Only ◄─────────────────────► In-House First    │
                    │         │                                    │           │
    ┌───────────────┼─────────┼────────────────────────────────────┼───────────┤
    │               │         │                                    │           │
    │  Always-On    │  Neo4j Aura    TigerGraph      DataStax      │           │
    │               │  Neptune        (Cloud)                      │           │
    │               │         │                                    │           │
    │ COST MODEL    │─────────┼────────────────────────────────────┼───────────┤
    │               │         │                                    │           │
    │  Scale-to-    │  PuppyGraph                    ┌─────────────┴─────┐     │
    │  Zero         │  (partial)                     │   GRAPH OLAP      │     │
    │               │                                │   ★ Unique        │     │
    │               │                                │     Position      │     │
    │               │                                └───────────────────┘     │
    └───────────────┴──────────────────────────────────────────────────────────┘
                    │                                    │
                    │    Query Layer ◄────────────────► Materialized Graph     │
                    │                  ARCHITECTURE                             │
                    └───────────────────────────────────────────────────────────┘
```

**Graph OLAP occupies a unique position:** In-house deployment + Zero idle cost + Materialized graph. No competitor offers all three.

---

**[Public sector use cases →](public-sector-use-cases.md)**

---

## For Platform & DevOps Teams

**Graph OLAP is designed to be operated by platform teams** — same patterns you already use.

| Concern | How Graph OLAP Helps |
|---------|---------------------|
| "I don't want another SaaS" | Runs on your K8s |
| "Data can't leave our network" | Fully in-house |
| "I need cost control" | Zero idle cost + quotas |
| "Must integrate with our stack" | Standard K8s patterns (OIDC, Prometheus, etc.) |
| "I don't want to be on-call" | Self-healing, auto-cleanup |

**[Full Platform & DevOps Guide →](platform-devops-guide.md)**

---

## Quick Links

- [Public Sector Use Cases →](public-sector-use-cases.md)
- [Streaming Account Sharing →](streaming-account-sharing.md)
- [Platform & DevOps Guide →](platform-devops-guide.md)
