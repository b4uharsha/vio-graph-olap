# Export Worker - Local Build
# BUILD FROM MONOREPO ROOT:
#   docker build -t export-worker:latest -f local-deploy/docker/export-worker.Dockerfile .

FROM cgr.dev/chainguard/python:latest-dev AS builder

WORKDIR /build

RUN python -m venv /build/venv
ENV PATH="/build/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip build hatchling

COPY packages/graph-olap-schemas/ ./graph-olap-schemas/
COPY packages/export-worker/pyproject.toml ./

RUN pip install --no-cache-dir ./graph-olap-schemas && \
    pip install --no-cache-dir \
        "google-cloud-storage>=2.14.0" \
        "google-auth>=2.27.0" \
        "httpx>=0.27.0" \
        "tenacity>=8.2.0" \
        "structlog>=24.1.0" \
        "pydantic>=2.6.0" \
        "pydantic-settings>=2.1.0" \
        "pyarrow>=15.0.0" \
        "trino>=0.328.0"

# Runtime stage
FROM cgr.dev/chainguard/python:latest AS production

WORKDIR /app

COPY --from=builder --chown=nonroot:nonroot /build/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY --chown=nonroot:nonroot packages/export-worker/src/export_worker /app/export_worker

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO

ENTRYPOINT ["python", "-m", "export_worker.worker"]
