# Changelog

All notable changes to the Graph OLAP Python SDK are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.5.0] - 2026-01-28

### Added

- Dynamic resource sizing with CPU override support for instance creation
- Resource monitoring capabilities for tracking instance CPU and memory usage
- `create_from_mapping()` convenience method to create instances directly from mappings
- Instance resource configuration options (cpu_cores, memory_gb parameters)

### Changed

- Updated test suite for dynamic resource sizing features
- Improved instance creation workflow with resource specification

---

## [0.4.0] - 2026-01-20

### Added

- `wake_starburst()` method to handle Starburst Galaxy cluster auto-suspend
- Automatic cluster wake detection during snapshot creation
- Card-based navigation component for notebooks
- Improved table styling with Airbnb DLS compliance

### Fixed

- Unit and integration test failures
- Notebook table container left alignment
- Jupyter CSS styling now loads automatically without running cells

### Changed

- Restructured curriculum to docs/notebooks with three-tier hierarchy
- Stronger table borders and larger font in notebook styling

---

## [0.3.0] - 2026-01-07

### Added

- Python 3.13 support across all platform components
- Standardized API schemas across wrappers and SDK
- Cloud E2E testing with optimized wrapper resources

### Fixed

- Handle empty `column_types` array from wrappers gracefully
- Python 3.11+ compatibility for jupyter-labs cross-package usage

### Changed

- Migrated all container images to Chainguard with zero CVEs
- Standardized Python versions across platform (3.11 minimum, 3.13 default)
- Comprehensive Helm chart and API infrastructure updates

---

## [0.2.0] - 2025-12-28

### Added

- FalkorDB wrapper support with multi-wrapper architecture
- `WrapperType` enum (RYUGRAPH, FALKORDB) for instance creation
- Async algorithm execution with property writeback
- Comprehensive unit and integration tests for FalkorDB, SDK, and Control Plane
- Jupyter Labs deployment in Kubernetes with environment-aware SDK
- Mapping version diff with semantic change tracking
- Parallel E2E test execution with resource pooling

### Fixed

- All E2E test failures resolved (18/18 tests passing)
- Orphaned resource cleanup in E2E tests
- Production bug fixes for instance lifecycle

### Changed

- REST-compliant DELETE endpoint for instance deletion
- Simplified instance lifecycle: terminate now immediately deletes
- Added json parameter support to HTTP DELETE method

---

## [0.1.0] - 2025-12-21

### Added

- Initial SDK release with core functionality
- `GraphOLAPClient` main entry point with typed resource managers
- `MappingResource` for graph mapping CRUD operations
- `SnapshotResource` for data snapshot management
- `InstanceResource` for graph instance lifecycle
- `InstanceConnection` for Cypher queries and algorithms
- `QueryResult` with DataFrame, dict, and visualization exports
- `FavoriteResource` for user bookmarks
- `HealthResource` for platform health checks
- `OpsResource` for operations configuration (Ops role)
- `AdminResource` for admin operations (Admin role)
- `SchemaResource` for Starburst schema browsing
- Native algorithm support (PageRank, WCC, Louvain, SCC, k-core, etc.)
- NetworkX algorithm integration
- Polars and Pandas DataFrame conversion
- PyVis and ipycytoscape visualization support
- Type coercion for Ryugraph data types
- Context manager support for client and connections
- Comprehensive exception hierarchy
- Modern Python packaging with hatchling

### Dependencies

- httpx >= 0.28.1
- pydantic >= 2.12.5
- tenacity >= 9.1.2
- graph-olap-schemas >= 1.0.0

### Optional Dependencies

- DataFrame: polars, pandas
- Visualization: networkx, pyvis, plotly
- Interactive: itables, ipywidgets

---

## Unreleased

### Planned

- Async client support (`GraphOLAPAsyncClient`)
- Batch operations for bulk resource management
- Enhanced progress tracking with ETA estimation
- Additional graph algorithms (community detection, centrality variants)
- Graph schema validation utilities
- Export to additional formats (Arrow, Avro)

---

[0.5.0]: https://github.com/internal/graph-olap-sdk/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/internal/graph-olap-sdk/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/internal/graph-olap-sdk/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/internal/graph-olap-sdk/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/internal/graph-olap-sdk/releases/tag/v0.1.0
