# Jupyter Labs - Local Build
# Provides JupyterHub + graph-olap-sdk for interactive graph analytics.
# BUILD FROM MONOREPO ROOT:
#   docker build -t jupyter-labs:latest -f local-deploy/docker/jupyter-labs.Dockerfile .

FROM quay.io/jupyter/minimal-notebook:python-3.11

USER root

# graph-olap-schemas and graph-olap-sdk are local packages (not on PyPI).
COPY --chown=jovyan:users packages/graph-olap-schemas/ /tmp/graph-olap-schemas/
COPY --chown=jovyan:users packages/graph-olap-sdk/ /tmp/graph-olap-sdk/

USER jovyan

# Install local packages then the SDK with all optional extras.
# graph-olap-schemas must be installed first (graph-olap-sdk depends on it).
RUN pip install --no-cache-dir \
        /tmp/graph-olap-schemas \
        "/tmp/graph-olap-sdk[all]" && \
    rm -rf /tmp/graph-olap-schemas /tmp/graph-olap-sdk

# Extra packages needed by local demo notebooks
RUN pip install --no-cache-dir \
        psycopg2-binary \
        networkx \
        scipy \
        pyvis \
        python-louvain \
        pyarrow

ENV JUPYTER_ENABLE_LAB=yes \
    GRAPH_OLAP_URL="http://control-plane:8080"

EXPOSE 8888

ENTRYPOINT ["start-notebook.py", "--NotebookApp.token=''", "--NotebookApp.password=''"]
