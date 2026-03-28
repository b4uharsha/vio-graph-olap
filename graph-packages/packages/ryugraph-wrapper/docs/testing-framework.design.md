# Test Framework Design

## Overview

This document defines a simplified, industry-standard testing strategy for the Graph OLAP Platform. The framework consolidates the previous multi-level approach into three clear tiers aligned with Google's testing best practices.

## Test Pyramid

```
          ┌─────────────┐
          │    E2E      │  ~10% of tests
          │  (k3d/GKE)  │  Real K8s cluster
          ├─────────────┤
          │ Integration │  ~20% of tests
          │  (Docker)   │  Real services, containers
          ├─────────────┤
          │    Unit     │  ~70% of tests
          │   (Mocks)   │  Fast, isolated
          └─────────────┘
```

## Test Tiers

### Tier 1: Unit Tests

**Purpose:** Verify individual functions, classes, and modules in isolation.

| Aspect | Specification |
|--------|---------------|
| **Scope** | Single function/class |
| **Dependencies** | All mocked |
| **Database** | Mocked |
| **External Services** | Mocked |
| **Docker Required** | No |
| **Target Duration** | < 20 seconds total |
| **Parallelization** | Full (`pytest -n auto`) |

**Characteristics:**
- No I/O operations (disk, network)
- No real database connections
- All external calls mocked with `unittest.mock` or `respx`
- Deterministic and reproducible
- Can run on any machine without setup

**Directory:** `tests/unit/`

**Run Command:**
```bash
pytest tests/unit/ -n auto --timeout=30
```

### Tier 2: Integration Tests

**Purpose:** Verify component interactions with real services in Docker containers.

| Aspect | Specification |
|--------|---------------|
| **Scope** | Component + real dependencies |
| **Dependencies** | Testcontainers |
| **Database** | Real Ryugraph |
| **External Services** | fake-gcs-server, in-process Control Plane |
| **Docker Required** | Yes |
| **Target Duration** | < 60 seconds total |
| **Parallelization** | Per-file (`pytest -n 4`) |

**Characteristics:**
- Uses testcontainers for GCS emulation
- Real Ryugraph database with test data
- In-process Control Plane (ASGI transport) for fast API testing
- Tests actual SQL/Cypher execution
- Tests data loading pipelines
- Tests service interactions

**Directory:** `tests/integration/`

**Run Command:**
```bash
pytest tests/integration/ -n 4 --timeout=120
```

### Tier 3: End-to-End Tests (Kubernetes)

**Purpose:** Verify the complete system deployed on Kubernetes.

| Aspect | Specification |
|--------|---------------|
| **Scope** | Full system on K8s |
| **Dependencies** | k3d cluster |
| **Database** | Real Ryugraph in Pod |
| **External Services** | All containerized in K8s |
| **Docker Required** | Yes |
| **Kubernetes Required** | Yes (k3d) |
| **Target Duration** | < 180 seconds total |
| **Parallelization** | Limited (shared cluster) |

**Characteristics:**
- Tests actual Kubernetes deployment manifests
- Validates ConfigMaps, Secrets, Services, Deployments
- Tests pod-to-pod communication
- Tests ingress and networking
- Tests resource limits and health checks
- Tests startup sequences and failure scenarios

**Directory:** `tests/e2e/`

**Run Command:**
```bash
pytest tests/e2e/ --k3d-cluster-name=test --timeout=300
```

## Kubernetes E2E Framework: k3d

### Why k3d?

Based on industry benchmarks and Google Cloud best practices:

| Criterion | k3d | kind | minikube |
|-----------|-----|------|----------|
| Startup Time | ~5s | ~20s | ~60s |
| Memory Usage | ~500MB | ~800MB | ~2GB |
| Multi-node | Yes | Yes | Limited |
| CI/CD Friendly | Excellent | Good | Poor |
| K8s Conformance | k3s-based | Full | Full |

**k3d advantages:**
- Fastest startup time (critical for local dev iteration)
- Lower memory footprint
- Built-in LoadBalancer support
- Easy local registry integration
- Excellent for CI/CD pipelines

### pytest-kind Integration

Despite the name, `pytest-kind` principles apply to k3d. We use `kubetest` for the pytest integration:

```python
# tests/e2e/conftest.py
import pytest
from kubernetes import client, config

@pytest.fixture(scope="session")
def k3d_cluster():
    """Create k3d cluster for E2E tests."""
    import subprocess

    cluster_name = "graph-olap-test"

    # Create cluster if not exists
    subprocess.run([
        "k3d", "cluster", "create", cluster_name,
        "--servers", "1",
        "--agents", "2",
        "--port", "8080:80@loadbalancer",
        "--wait",
    ], check=True)

    # Configure kubectl
    subprocess.run([
        "k3d", "kubeconfig", "merge", cluster_name,
        "--kubeconfig-merge-default",
    ], check=True)

    config.load_kube_config()
    yield client.CoreV1Api()

    # Cleanup handled by --keep-cluster flag or explicit delete

@pytest.fixture(scope="session")
def deployed_stack(k3d_cluster):
    """Deploy the full stack to k3d."""
    import subprocess

    # Apply Kubernetes manifests
    subprocess.run([
        "kubectl", "apply", "-k", "deploy/overlays/test"
    ], check=True)

    # Wait for deployments
    subprocess.run([
        "kubectl", "wait", "--for=condition=available",
        "deployment/control-plane", "deployment/ryugraph-wrapper",
        "--timeout=120s"
    ], check=True)

    yield

    # Cleanup
    subprocess.run([
        "kubectl", "delete", "-k", "deploy/overlays/test"
    ], check=False)
```

## Directory Structure

```
tests/
├── conftest.py              # Shared fixtures (mocks, data)
├── unit/                    # Tier 1: Unit tests
│   ├── __init__.py
│   ├── conftest.py          # Unit-specific fixtures
│   ├── test_database_service.py
│   ├── test_algorithm_service.py
│   ├── test_control_plane_client.py
│   └── test_routers.py
├── integration/             # Tier 2: Integration tests
│   ├── __init__.py
│   ├── conftest.py          # Docker fixtures (testcontainers)
│   ├── test_data_loading.py
│   ├── test_query_execution.py
│   ├── test_api_integration.py
│   └── test_control_plane_integration.py
├── e2e/                     # Tier 3: Kubernetes E2E tests
│   ├── __init__.py
│   ├── conftest.py          # k3d cluster fixtures
│   ├── test_deployment.py   # K8s manifest validation
│   ├── test_startup_flow.py # Pod startup sequence
│   ├── test_api_e2e.py      # Full API through ingress
│   └── test_failure_scenarios.py
├── fixtures/                # Shared test data
│   ├── __init__.py
│   └── parquet_data.py
└── containers/              # Container helpers (for integration)
    ├── __init__.py
    └── gcs.py
```

## pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
]
markers = [
    "unit: Fast unit tests with mocks (no Docker)",
    "integration: Tests with Docker containers",
    "e2e: End-to-end tests on Kubernetes (requires k3d)",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]
timeout = 60  # Default timeout per test
```

## Running Tests

### Local Development

```bash
# Quick feedback loop - unit tests only
pytest tests/unit/ -n auto -q

# Full local validation (unit + integration)
pytest tests/unit/ tests/integration/ -n 4

# Full E2E with Kubernetes (requires k3d)
k3d cluster create test-cluster --wait
pytest tests/e2e/ --k3d-cluster-name=test-cluster
k3d cluster delete test-cluster
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yaml
name: Test Suite

on: [push, pull_request]

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest tests/unit/ -n auto --cov --timeout=30

  integration:
    runs-on: ubuntu-latest
    needs: unit
    services:
      docker:
        image: docker:dind
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration/ -n 4 --timeout=120

  e2e:
    runs-on: ubuntu-latest
    needs: integration
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      # Install k3d
      - name: Install k3d
        run: |
          curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

      # Create cluster
      - name: Create k3d cluster
        run: |
          k3d cluster create ci-cluster \
            --servers 1 \
            --agents 1 \
            --wait

      # Build and load images
      - name: Build and load images
        run: |
          docker build -t control-plane:test -f control-plane/Dockerfile .
          docker build -t ryugraph-wrapper:test -f ryugraph-wrapper/Dockerfile .
          k3d image import control-plane:test ryugraph-wrapper:test -c ci-cluster

      # Run E2E tests
      - name: Run E2E tests
        run: |
          pip install -e ".[dev]"
          pytest tests/e2e/ --timeout=300

      # Cleanup
      - name: Cleanup
        if: always()
        run: k3d cluster delete ci-cluster
```

## Performance Optimization Strategies

### 1. Fixture Scoping

```python
# Session-scoped: Create once per test run
@pytest.fixture(scope="session")
def k3d_cluster():
    # Expensive setup - done once
    pass

# Module-scoped: Create once per test file
@pytest.fixture(scope="module")
def loaded_database():
    # Medium setup - per file
    pass

# Function-scoped: Create per test (default)
@pytest.fixture
def fresh_connection():
    # Cheap setup - per test
    pass
```

### 2. Parallel Execution

```bash
# Unit tests: Maximum parallelism
pytest tests/unit/ -n auto  # Uses all CPU cores

# Integration tests: Limited parallelism (Docker resources)
pytest tests/integration/ -n 4

# E2E tests: Sequential or limited (shared cluster)
pytest tests/e2e/ -n 2
```

### 3. Test Selection

```bash
# Run only tests matching pattern
pytest -k "test_query" tests/

# Run tests modified in current branch
pytest --lf  # Last failed
pytest --nf  # New files first

# Skip slow tests during development
pytest -m "not slow" tests/
```

### 4. Resource Reuse

```python
# Keep k3d cluster between runs (saves ~5s per run)
@pytest.fixture(scope="session")
def k3d_cluster(request):
    if request.config.getoption("--keep-cluster"):
        # Reuse existing cluster
        config.load_kube_config()
        return client.CoreV1Api()
    # Create new cluster
    ...
```

### 5. Image Caching

```bash
# Pre-pull images before tests
k3d image import \
    control-plane:test \
    ryugraph-wrapper:test \
    fsouza/fake-gcs-server:latest \
    -c test-cluster

# Use local registry for faster image access
k3d cluster create test --registry-create test-registry:5000
```

## Migration Plan

### Phase 1: Consolidate Existing Tests

1. Move `tests/integration/test_e2e.py` → `tests/integration/test_full_stack.py`
2. Remove redundant test levels (L1/L2/L3 distinction)
3. Update markers: `e2e` → `integration` for Docker-based tests

### Phase 2: Add Kubernetes E2E

1. Create `tests/e2e/` directory
2. Add k3d fixtures to `tests/e2e/conftest.py`
3. Create deployment validation tests
4. Create startup flow tests
5. Create failure scenario tests

### Phase 3: CI/CD Integration

1. Update GitHub Actions workflow
2. Add k3d cluster creation step
3. Configure image loading
4. Set appropriate timeouts

## Target Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Unit test duration | < 20s | ~15s |
| Integration test duration | < 60s | ~90s (needs optimization) |
| E2E test duration | < 180s | N/A (not implemented) |
| Unit test coverage | > 80% | 73% |
| Total test count | ~150 | 160 |

## References

- [k3d Documentation](https://k3d.io/)
- [kubetest - Kubernetes Integration Testing](https://github.com/vapor-ware/kubetest)
- [pytest-kind](https://codeberg.org/hjacobs/pytest-kind)
- [Google Cloud Build Integration Testing](https://github.com/GoogleCloudPlatform/cloudbuild-integration-testing)
- [Testkube - Kubernetes Native Testing](https://testkube.io/)
- [k3d vs kind vs minikube Comparison](https://sanj.dev/post/kind-vs-k3d-vs-k0s)
