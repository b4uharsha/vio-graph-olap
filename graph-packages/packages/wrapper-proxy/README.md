# wrapper-proxy

NGINX reverse proxy for graph wrapper pod routing.

## Architecture

```
Analyst Browser/SDK
    |
    v
nginx Wrapper Proxy (this service)
    |
    |-- /wrapper/falkordb/*   -> falkordb-wrapper:8000
    |-- /wrapper/ryugraph/*   -> ryugraph-wrapper:8000
    |-- /wrapper/{slug}/*     -> wrapper-{slug}:8000 (dynamic)
    |
    v
Graph Database Pod (FalkorDB / KuzuDB)
```

## Quick Start

```bash
make build
make push TAG=v1.0
```

## API

| Action | Method | URL |
|--------|--------|-----|
| Health check | GET | `/healthz` |
| Run Cypher query | POST | `/wrapper/{slug}/query` |
| Get schema | GET | `/wrapper/{slug}/schema` |
| Graph algorithms | POST | `/wrapper/{slug}/algo/{algorithm}` |
