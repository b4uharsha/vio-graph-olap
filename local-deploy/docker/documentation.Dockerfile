# Documentation Site - Local Build (MkDocs Material)
# BUILD FROM MONOREPO ROOT:
#   docker build -t documentation:latest -f local-deploy/docker/documentation.Dockerfile .

# ---------------------------------------------------------------------------
# Stage 1: Build static site with MkDocs
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install MkDocs and plugins
COPY packages/documentation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MkDocs config and theme overrides
COPY packages/documentation/mkdocs.yml .
COPY packages/documentation/overrides/ overrides/

# Assemble docs_dir (mkdocs.yml: docs_dir: build)
# The Earthfile gathers content from packages/ and docs/ into this directory.
RUN mkdir -p build/javascripts build/stylesheets

COPY packages/documentation/javascripts/ build/javascripts/
COPY packages/documentation/stylesheets/ build/stylesheets/

# SDK notebook stylesheet
COPY packages/graph-olap-sdk/src/graph_olap/styles/notebook.css build/stylesheets/

# All docs content (markdown, notebooks, images, assets)
COPY docs/ build/

# Build the static site
RUN mkdocs build --site-dir /site

# ---------------------------------------------------------------------------
# Stage 2: Serve with nginx on port 3000
# ---------------------------------------------------------------------------
FROM nginx:alpine AS runtime

COPY --from=builder /site /usr/share/nginx/html

# Port 3000 to match the Earthfile convention
RUN printf 'server {\n\
    listen 3000;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ $uri.html =404;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 3000
