# graph-olap-sdk

Python SDK for Graph OLAP Platform - Jupyter notebook integration for graph analytics.

## Installation

```bash
pip install graph-olap-sdk
```

With optional features:

```bash
pip install "graph-olap-sdk[dataframe]"    # Polars + Pandas support
pip install "graph-olap-sdk[viz]"          # NetworkX, PyVis, Plotly
pip install "graph-olap-sdk[interactive]"  # iTables, ipywidgets
pip install "graph-olap-sdk[all]"          # All features
```

## Quick Start

```python
from graph_olap import GraphOLAPClient

client = GraphOLAPClient(base_url="https://api.example.com", api_key="your-key")

# List instances
instances = client.instances.list()

# Connect and query
conn = client.instances.connect("my-instance")
result = conn.query("MATCH (n) RETURN n LIMIT 10")
```

## Development

```bash
make install    # Install in editable mode with dev dependencies
make test       # Run tests
make lint       # Run linter
make build      # Build wheel
```

## License

MIT
