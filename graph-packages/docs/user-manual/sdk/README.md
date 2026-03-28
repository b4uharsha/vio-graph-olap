# SDK User Manual

Welcome to the Graph OLAP SDK User Manual. This comprehensive guide covers everything you need to know to effectively use the Graph OLAP Python SDK for graph analytics.

## Overview

The Graph OLAP SDK is the **sole user interface** for the Graph OLAP Platform. All platform operations - from creating graph mappings to running algorithms - are performed through this Python SDK in Jupyter notebooks. There is no separate web console or GUI.

The SDK provides complete capabilities for:

- **Schema Discovery** - Browse Starburst catalogs, schemas, tables, and columns
- **Mapping Management** - Full CRUD for graph mappings (create, read, update, delete, copy, list)
- **Instance Lifecycle** - Create instances from mappings, terminate, update CPU, monitor status
- **Graph Queries** - Execute Cypher queries with DataFrame results (Polars/Pandas)
- **Graph Algorithms** - Run native algorithms and 500+ NetworkX algorithms
- **Administration** - Cluster health, configuration, and bulk operations (role-based)
- **Favorites** - Bookmark frequently used mappings, snapshots, and instances

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Getting Started](01-getting-started.manual.md) | Installation, configuration, and first steps |
| [Core Concepts](02-core-concepts.manual.md) | Understanding resources, connections, and the SDK architecture |
| [API Reference](03-api-reference.manual.md) | Complete API documentation with examples |
| [Graph Algorithms](04-graph-algorithms.manual.md) | Guide to all available graph algorithms |
| [Advanced Topics](05-advanced-topics.manual.md) | Performance optimization, error handling, and best practices |
| [Examples](06-examples.manual.md) | Real-world use cases and code examples |

## Appendices

| Appendix | Description |
|----------|-------------|
| [Environment Variables](appendices/a-environment-variables.manual.md) | Configuration via environment variables |
| [Error Codes](appendices/b-error-codes.manual.md) | Complete error code reference |
| [Cypher Reference](appendices/c-cypher-reference.manual.md) | Cypher query language quick reference |
| [Algorithm Reference](appendices/d-algorithm-reference.manual.md) | Algorithm parameters and complexity |

## Prerequisites

Before using this manual, you should have:

- Python 3.10 or later
- Access to a Graph OLAP platform instance
- Basic familiarity with Python and graph concepts

## Getting Help

- **Tutorials**: Interactive Jupyter notebooks in the [Notebooks](../notebooks/README.md) section
- **API Docs**: Detailed API reference in the [Component Designs](../../component-designs/jupyter-sdk.design.md) section
- **Examples**: Working code examples throughout this manual

## Version Information

This manual covers SDK version 0.1.x and is compatible with Graph OLAP Platform version 1.x.
