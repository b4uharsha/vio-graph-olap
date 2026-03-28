# FalkorDB Wrapper - Local Build
# BUILD FROM MONOREPO ROOT:
#   docker build -t falkordb-wrapper:latest -f local-deploy/docker/falkordb-wrapper.Dockerfile .

FROM cgr.dev/chainguard/python:latest-dev AS builder

WORKDIR /app

RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Local packages: graph-olap-schemas and lib-auth (not on PyPI)
# --chown required: Chainguard builder runs as nonroot; setuptools writes egg-info into source dirs
COPY --chown=nonroot:nonroot packages/graph-olap-schemas/ ./graph-olap-schemas/
COPY --chown=nonroot:nonroot packages/graph-olap/lib/auth/ ./lib-auth/

COPY --chown=nonroot:nonroot packages/falkordb-wrapper/pyproject.toml packages/falkordb-wrapper/README.md ./
COPY --chown=nonroot:nonroot packages/falkordb-wrapper/requirements.lock* ./
COPY --chown=nonroot:nonroot packages/falkordb-wrapper/src/ ./src/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ./graph-olap-schemas ./lib-auth

# FalkorDBLite architecture fix: delete the pre-built x86_64 binary so the
# correct architecture binary is downloaded for the current platform.
ARG FALKORDBLITE_VERSION=0.6.0
RUN pip download --no-binary :all: falkordblite==${FALKORDBLITE_VERSION} -d /tmp/falkordblite && \
    cd /tmp/falkordblite && \
    tar xzf falkordblite-${FALKORDBLITE_VERSION}.tar.gz && \
    rm -f falkordblite-${FALKORDBLITE_VERSION}/falkordb.so && \
    pip install --no-cache-dir /tmp/falkordblite/falkordblite-${FALKORDBLITE_VERSION} && \
    rm -rf /tmp/falkordblite

RUN if [ -f requirements.lock ]; then \
        grep -v "^falkordblite" requirements.lock > requirements-filtered.lock && \
        pip install --no-cache-dir -r requirements-filtered.lock && \
        rm requirements-filtered.lock; \
    else \
        pip install --no-cache-dir .; \
    fi

# Remove the CLI launcher (not needed in wrapper pod)
RUN rm -f /app/venv/bin/falkordb.so

# Runtime stage
FROM cgr.dev/chainguard/python:latest AS runtime

WORKDIR /app

COPY --from=builder /usr/lib/libgomp.so.1 /usr/lib/libgomp.so.1
COPY --from=builder --chown=nonroot:nonroot /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY --chown=nonroot:nonroot packages/falkordb-wrapper/src/ ./src/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WRAPPER_INSTANCE_ID="" \
    WRAPPER_SNAPSHOT_ID="" \
    WRAPPER_MAPPING_ID="" \
    WRAPPER_OWNER_ID="" \
    WRAPPER_CONTROL_PLANE_URL="" \
    WRAPPER_GCS_BASE_PATH="" \
    DATABASE_PATH="/data/db" \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    ENVIRONMENT=production

EXPOSE 8000

ENTRYPOINT ["python", "-m", "uvicorn", "wrapper.main:app", "--host", "0.0.0.0", "--port", "8000"]
