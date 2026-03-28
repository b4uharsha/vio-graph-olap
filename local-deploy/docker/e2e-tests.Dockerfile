# E2E Tests - Local Build
# Runs the Graph OLAP end-to-end pytest suite inside the cluster.
# BUILD FROM MONOREPO ROOT:
#   docker build -t e2e-tests:latest -f local-deploy/docker/e2e-tests.Dockerfile .

FROM python:3.11-slim

WORKDIR /e2e

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install local packages first (SDK depends on schemas)
COPY packages/graph-olap-schemas/ /tmp/graph-olap-schemas/
COPY packages/graph-olap-sdk/ /tmp/graph-olap-sdk/

RUN pip install --no-cache-dir \
        /tmp/graph-olap-schemas \
        "/tmp/graph-olap-sdk[all]" && \
    rm -rf /tmp/graph-olap-schemas /tmp/graph-olap-sdk

# Copy e2e test suite
COPY tests/e2e/ /e2e/

# Install e2e test dependencies (excluding local workspace packages already installed)
RUN pip install --no-cache-dir \
        "pytest>=9.0.2" \
        "pytest-asyncio>=1.3.0" \
        "pytest-timeout>=2.4.0" \
        "pytest-xdist>=3.8.0" \
        "pytest-order>=1.3.0" \
        "httpx>=0.28.1" \
        "polars>=1.36.1" \
        "pandas>=2.0.0" \
        "papermill>=2.6.0" \
        "jupyter>=1.1.1" \
        "ipykernel>=7.1.0"

ENV PYTHONUNBUFFERED=1

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
