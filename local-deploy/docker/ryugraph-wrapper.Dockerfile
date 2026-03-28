# Ryugraph Wrapper - Local Build
# Uses python:3.12-slim because ryugraph does not publish wheels for Python 3.13+
# BUILD FROM MONOREPO ROOT:
#   docker build -t ryugraph-wrapper:latest -f local-deploy/docker/ryugraph-wrapper.Dockerfile .

FROM python:3.12-slim AS builder

WORKDIR /app

RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Local packages: graph-olap-schemas and lib-auth (not on PyPI)
COPY packages/graph-olap-schemas/ ./graph-olap-schemas/
COPY packages/graph-olap/lib/auth/ ./lib-auth/

COPY packages/ryugraph-wrapper/pyproject.toml packages/ryugraph-wrapper/README.md ./
COPY packages/ryugraph-wrapper/requirements.lock* ./
COPY packages/ryugraph-wrapper/src/ ./src/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ./graph-olap-schemas ./lib-auth && \
    if [ -f requirements.lock ]; then \
        pip install --no-cache-dir -r requirements.lock; \
    else \
        pip install --no-cache-dir .; \
    fi

# Runtime stage
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY packages/ryugraph-wrapper/src/ ./src/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WRAPPER_INSTANCE_ID="" \
    WRAPPER_SNAPSHOT_ID="" \
    WRAPPER_MAPPING_ID="" \
    WRAPPER_OWNER_ID="" \
    WRAPPER_CONTROL_PLANE_URL="" \
    WRAPPER_GCS_BASE_PATH="" \
    RYUGRAPH_DATABASE_PATH="/data/db" \
    RYUGRAPH_BUFFER_POOL_SIZE=2147483648 \
    RYUGRAPH_MAX_THREADS=16 \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    ENVIRONMENT=production

EXPOSE 8000

ENTRYPOINT ["python", "-m", "uvicorn", "wrapper.main:app", "--host", "0.0.0.0", "--port", "8000"]
