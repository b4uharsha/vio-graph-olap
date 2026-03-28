# Local Setup Documentation Site
# Standalone MkDocs Material site — no monorepo required.
# BUILD CONTEXT: local-deploy/ directory
#   docker build -t local-docs:latest -f docker/local-docs.Dockerfile .

FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir \
    mkdocs-material==9.5.18 \
    mkdocs>=1.5

COPY docs-local/mkdocs.yml .
COPY docs-local/docs/ docs/

RUN mkdocs build --site-dir /site

# ---------------------------------------------------------------------------
FROM nginx:alpine AS runtime

RUN rm -rf /usr/share/nginx/html/*
COPY --from=builder /site/ /usr/share/nginx/html/

RUN printf 'server {\n\
    listen 3001;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ $uri.html =404;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 3001
