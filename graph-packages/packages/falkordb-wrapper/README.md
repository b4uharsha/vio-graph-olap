# FalkorDB Wrapper

FastAPI wrapper for embedded FalkorDB graph database instances.

## Overview

This wrapper provides a REST API for FalkorDB graph databases, enabling:
- Cypher query execution
- Algorithm REST API infrastructure (see limitations below)
- Schema introspection
- Health and readiness probes
- Automatic data loading from GCS Parquet snapshots

## Requirements

- Python 3.12+ (FalkorDBLite requires Python 3.12)
- FalkorDBLite package
- Google Cloud Storage access (for snapshot data)

## Key Differences from Ryugraph Wrapper

- **No NetworkX support**: FalkorDB algorithms are invoked via Cypher procedures (`CALL algo.xxx()`)
- **No bulk import**: Data loaded via UNWIND batches from Parquet files
- **In-memory only**: All graph data must fit in RAM (no disk-based buffer pool)
- **Algorithm result mode**: Results returned as query results, not property writeback

## Algorithm Availability (Important)

**FalkorDBLite (embedded) does NOT include graph algorithms.**

The Algorithm REST API (`/algo/*` endpoints) is implemented and functional, but the underlying
Cypher procedures (e.g., `pagerank.stream()`, `algo.betweenness()`, `algo.WCC()`) are only
available in **FalkorDB server**, not in the embedded FalkorDBLite package.

| Feature | FalkorDBLite (Embedded) | FalkorDB Server |
|---------|-------------------------|-----------------|
| Cypher queries | Yes | Yes |
| Algorithm REST API | Yes (infrastructure) | Yes (fully functional) |
| PageRank | **No** | Yes |
| Betweenness Centrality | **No** | Yes |
| WCC (Connected Components) | **No** | Yes |
| CDLP (Community Detection) | **No** | Yes |
| BFS/Shortest Path | **No** | Yes |

For production use with graph algorithms, deploy FalkorDB server instead of FalkorDBLite.

The E2E tests detect algorithm availability and skip algorithm execution tests when running
against FalkorDBLite, while still testing the REST API infrastructure

## Installation

```bash
pip install -e .
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Environment Variables

See `wrapper/config.py` for configuration options.
