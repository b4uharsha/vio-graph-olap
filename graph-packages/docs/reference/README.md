# External Technology Reference (Tier 6)

Technical reference for external systems and integration patterns.

**Purpose:** Document HOW external technologies work (not how WE build things)

## Upstream Documentation Snapshots

Read-only snapshots of upstream documentation for offline reference and AI consumption.

| Directory | Source | Notes |
|-----------|--------|-------|
| [ryugraph-v25.9/](ryugraph-v25.9/) | [predictable-labs/ryugraph-docs](https://github.com/predictable-labs/ryugraph-docs) | Active - Ryugraph v25.x |
| [kuzudb-v0.11.3/](kuzudb-v0.11.3/) | [kuzudb/kuzu-docs](https://github.com/kuzudb/kuzu-docs) | Archived - for historical reference |

**Rules for snapshots:**
- DO NOT MODIFY - keep identical to upstream GitHub
- Custom docs belong in `../platform/`
- Update by re-downloading from GitHub, not editing

## Reference Documents

| Document | Purpose |
|----------|---------|
| [data-pipeline.reference.md](data-pipeline.reference.md) | Starburst UNLOAD, Parquet format, Ryugraph import, type mapping |
| [ryugraph-networkx.reference.md](ryugraph-networkx.reference.md) | Ryugraph Python API, NetworkX integration, algorithm patterns |
| [ryugraph-performance.reference.md](ryugraph-performance.reference.md) | Threading, buffer pool, I/O characteristics, pod memory configuration |
| [gke-configuration.reference.md](gke-configuration.reference.md) | GKE cluster setup, node pools, networking, Workload Identity, storage, observability |

## When to Use Reference Docs

| Aspect | Reference Doc | Component Design |
|--------|---------------|------------------|
| Subject | External system | Our code |
| Changes when | Vendor releases update | We redesign |
| Example | "Ryugraph COPY FROM syntax" | "How our wrapper invokes COPY FROM" |

## Referenced By

- [component-designs/export-worker.design.md](../component-designs/export-worker.design.md)
- [component-designs/ryugraph-wrapper.design.md](../component-designs/ryugraph-wrapper.design.md)
- [component-designs/control-plane.design.md#mapping-generator-subsystem](../component-designs/control-plane.design.md#mapping-generator-subsystem)
- [system-design/system.architecture.design.md](../system-design/system.architecture.design.md)
- [foundation/requirements.md](../foundation/requirements.md)
