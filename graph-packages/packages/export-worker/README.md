# Export Worker

Cloud Function for Graph OLAP snapshot export.

## Overview

This Cloud Function handles snapshot export requests by:

1. Receiving Pub/Sub messages with snapshot definitions
2. Executing Starburst UNLOAD queries to export data to GCS as Parquet
3. Counting exported rows and calculating total size
4. Reporting status updates to the Control Plane

## Development

### Prerequisites

- Python 3.11+
- GCP credentials configured

### Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run unit tests only
pytest tests/unit

# Run integration tests only
pytest tests/integration
```

### Local Development

```bash
# Set environment variables
export STARBURST_URL=http://localhost:8080
export STARBURST_USER=admin
export STARBURST_PASSWORD=admin
export GCP_PROJECT=dev-project
export CONTROL_PLANE_URL=http://localhost:8081

# Run local server
functions-framework --target=process_snapshot --debug
```

## Architecture

The worker follows a clean architecture pattern:

- `main.py` - Cloud Function entry point with error handling
- `processor.py` - Orchestrates the export workflow
- `clients/` - External service clients (Starburst, GCS, Control Plane)
- `models.py` - Pydantic models for data validation
- `exceptions.py` - Custom exception hierarchy for error handling
