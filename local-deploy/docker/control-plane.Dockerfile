# Control Plane - Local Build
# BUILD FROM MONOREPO ROOT:
#   docker build -t control-plane:latest -f local-deploy/docker/control-plane.Dockerfile .

FROM cgr.dev/chainguard/python:latest-dev AS builder

WORKDIR /build

RUN python -m venv /build/venv
ENV PATH="/build/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip build hatchling

# Local packages: graph-olap-schemas and lib-auth (not on PyPI)
# --chown required: Chainguard builder runs as nonroot; setuptools writes egg-info into source dirs
COPY --chown=nonroot:nonroot packages/graph-olap-schemas/ ./graph-olap-schemas/
COPY --chown=nonroot:nonroot packages/graph-olap/lib/auth/ ./lib-auth/

COPY --chown=nonroot:nonroot packages/control-plane/pyproject.toml ./
COPY --chown=nonroot:nonroot packages/control-plane/README.md* ./

RUN pip install --no-cache-dir ./graph-olap-schemas ./lib-auth && \
    pip install --no-cache-dir \
        fastapi \
        "uvicorn[standard]" \
        pydantic \
        pydantic-settings \
        pygtrie \
        "sqlalchemy[asyncio]" \
        asyncpg \
        alembic \
        structlog \
        httpx \
        google-cloud-storage \
        kubernetes \
        apscheduler \
        prometheus-client \
        tenacity \
        deepdiff \
        "PyJWT[crypto]"

# Runtime stage
FROM cgr.dev/chainguard/python:latest AS production

WORKDIR /app

COPY --from=builder --chown=nonroot:nonroot /build/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY --chown=nonroot:nonroot packages/control-plane/src/control_plane /app/control_plane

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV GRAPH_OLAP_HOST=0.0.0.0
ENV GRAPH_OLAP_PORT=8080
ENV GRAPH_OLAP_DEBUG=true
ENV GRAPH_OLAP_INTERNAL_API_KEY=test-internal-api-key

EXPOSE 8080

ENTRYPOINT ["python", "-m", "uvicorn", "control_plane.main:app", "--host", "0.0.0.0", "--port", "8080"]
