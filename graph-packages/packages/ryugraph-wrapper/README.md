# Ryugraph Wrapper

FastAPI service providing a REST API for embedded Ryugraph (KuzuDB fork) graph database instances.

## Features

- **Cypher Query Execution**: Execute read-only Cypher queries against the graph
- **Native Algorithms**: Run built-in graph algorithms (PageRank, WCC, etc.)
- **NetworkX Algorithms**: Dynamic discovery and execution of NetworkX algorithms
- **Lock Management**: Implicit locking for algorithm execution concurrency
- **Health Monitoring**: Kubernetes-compatible health and readiness probes

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start the server
uvicorn wrapper.main:app --reload
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/ready` | GET | Readiness probe |
| `/status` | GET | Detailed instance status |
| `/query` | POST | Execute Cypher query |
| `/schema` | GET | Get graph schema |
| `/lock` | GET | Get lock status |
| `/algo/{name}` | POST | Run native algorithm |
| `/algo/algorithms` | GET | List native algorithms |
| `/networkx/{name}` | POST | Run NetworkX algorithm |
| `/networkx/algorithms` | GET | List NetworkX algorithms |

## Configuration

Configuration via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `WRAPPER_INSTANCE_ID` | Instance identifier | Required |
| `WRAPPER_SNAPSHOT_ID` | Snapshot identifier | Required |
| `WRAPPER_CONTROL_PLANE_URL` | Control Plane API URL | Required |
| `RYUGRAPH_DATABASE_PATH` | Database directory path | `/data/db` |
| `RYUGRAPH_BUFFER_POOL_SIZE` | Buffer pool size bytes | 2GB |
| `LOG_LEVEL` | Logging level | `INFO` |

## Development

```bash
# Run linting
ruff check src tests

# Run type checking
mypy src

# Run tests with coverage
pytest --cov=wrapper --cov-report=html
```

## License

MIT
