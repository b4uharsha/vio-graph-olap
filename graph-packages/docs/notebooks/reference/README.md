# Reference Documentation

API and algorithm reference for Graph OLAP.

## SDK Reference

Complete documentation for SDK classes:

| Class | Description |
|-------|-------------|
| `GraphOLAPClient` | Main client entry point |
| `InstanceConnection` | Query and algorithm execution |
| `MappingResource` | Graph schema definitions |
| `SnapshotResource` | Point-in-time data exports |
| `InstanceResource` | Running graph instances |

## Algorithm Reference

Graph algorithms organized by category:

| Category | Algorithms | Use Case |
|----------|------------|----------|
| **centrality/** | PageRank, Betweenness, Closeness, Degree, Eigenvector | Find important nodes |
| **community/** | Louvain, Leiden, Label Propagation, Girvan-Newman | Detect communities |
| **pathfinding/** | Shortest Path, Dijkstra, BFS, A*, Spanning Tree | Find routes |
| **similarity/** | Jaccard, Adamic-Adar, Common Neighbors | Compare nodes |
| **structural/** | K-Core, Triangle Count, Connected Components | Network structure |
| **embeddings/** | Node2Vec | Vector representations |

## Using Reference Docs

Each reference notebook includes:
- Method signatures and parameters
- Return types
- Code examples
- Performance notes
