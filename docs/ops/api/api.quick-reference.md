# Quick Reference Card

Single-page reference for Graph OLAP Platform implementation.

---

## Error Codes

| Code | HTTP | When |
|------|------|------|
| VALIDATION_FAILED | 400 | Invalid request body |
| INVALID_SQL | 400 | SQL syntax/validation error |
| AUTH_REQUIRED | 401 | Missing/invalid token |
| PERMISSION_DENIED | 403 | Role insufficient |
| RESOURCE_NOT_FOUND | 404 | Resource doesn't exist |
| MAPPING_NOT_FOUND | 404 | Mapping doesn't exist |
| SNAPSHOT_NOT_FOUND | 404 | Snapshot doesn't exist |
| INSTANCE_NOT_FOUND | 404 | Instance doesn't exist |
| QUERY_TIMEOUT | 408 | Query exceeded timeout |
| ALREADY_EXISTS | 409 | Duplicate resource |
| RESOURCE_LOCKED | 409 | Algorithm running |
| CONCURRENCY_LIMIT_EXCEEDED | 409 | Too many instances |
| RESOURCE_HAS_DEPENDENCIES | 409 | Cannot delete (children exist) |
| SNAPSHOT_NOT_READY | 409 | Snapshot not in 'ready' status |
| ALGORITHM_NOT_FOUND | 404 | Algorithm doesn't exist |
| EXECUTION_NOT_FOUND | 404 | Execution ID not found |

---

## Resource Status Values

| Resource | Statuses |
|----------|----------|
| Snapshot | `pending` → `creating` → `ready` / `failed` (managed internally) |
| Instance | `waiting_for_snapshot` → `starting` → `running` → `stopping` / `failed` |
| Algorithm | `running` → `completed` / `failed` |

> **Note:** Explicit snapshot APIs have been disabled. Snapshots are now managed
> internally when instances are created directly from mappings.

---

## Config Keys (global_config table)

| Key | Type | Example |
|-----|------|---------|
| `lifecycle.mapping.default_ttl` | Duration | `null` |
| `lifecycle.mapping.default_inactivity` | Duration | `P30D` |
| `lifecycle.mapping.max_ttl` | Duration | `P365D` |
| `lifecycle.snapshot.default_ttl` | Duration | `P7D` |
| `lifecycle.snapshot.default_inactivity` | Duration | `P3D` |
| `lifecycle.snapshot.max_ttl` | Duration | `P30D` |
| `lifecycle.instance.default_ttl` | Duration | `PT24H` |
| `lifecycle.instance.default_inactivity` | Duration | `PT4H` |
| `lifecycle.instance.max_ttl` | Duration | `P7D` |
| `concurrency.per_analyst` | Integer | `5` |
| `concurrency.cluster_total` | Integer | `50` |

---

## Ryugraph Types

| Type | Primary Key? | Description |
|------|--------------|-------------|
| STRING | ✓ | UTF-8 text |
| INT64 | ✓ | 64-bit integer |
| INT32 | | 32-bit integer |
| INT16 | | 16-bit integer |
| INT8 | | 8-bit integer |
| DOUBLE | | 64-bit float |
| FLOAT | | 32-bit float |
| DATE | ✓ | Calendar date |
| TIMESTAMP | | Date and time |
| BOOL | | Boolean |
| BLOB | | Binary data |
| UUID | ✓ | Universal identifier |
| LIST | | Array |
| MAP | | Key-value pairs |
| STRUCT | | Nested object |

---

## User Roles

| Role | Mappings/Snapshots/Instances | Config | Audit |
|------|------------------------------|--------|-------|
| Analyst | Own only | ❌ | ❌ |
| Admin | All users | ❌ | ✓ |
| Ops | All users | ✓ | ✓ |

---

## API Base URLs

| Component | URL |
|-----------|-----|
| Control Plane | `https://{domain}/api` |
| Wrapper Pod | `https://{domain}/{instance-id}` |
| Internal | `http://control-plane.graph-olap.svc.cluster.local/api/internal` |

---

## Authentication Headers

```
# Client sends:
Authorization: Bearer {api_key}

# Middleware injects:
X-Username: {username}
X-User-Role: {analyst|admin|ops}
```

---

## Deletion Rules

```
Instance ← can always terminate
Snapshot ← managed internally (no direct deletion)
Mapping  ← blocked if any instances exist
```

> **Note:** Snapshots are managed internally as part of instance lifecycle.

---

## Retry Configuration

| Operation | Max Retries | Backoff |
|-----------|-------------|---------|
| Snapshot export (Starburst) | 3 | Exponential (1s, 2s, 4s) |
| Status update to CP | 5 | Fixed (1s) |
| GCS operations | 3 | Exponential (500ms, 1s, 2s) |
| Instance startup | 0 | None (fail fast) |
| Pub/Sub ack | 3 | Pub/Sub default |

---

## GCS Path Structure

```
gs://{bucket}/{username}/{mapping_id}/{snapshot_id}/
├── nodes/
│   ├── {NodeLabel}/
│   │   └── *.parquet
└── edges/
    └── {EDGE_TYPE}/
        └── *.parquet
```

---

## Authoritative Sources

| Topic | Document |
|-------|----------|
| Error codes | `api.common.spec.md` |
| Anti-patterns | `architectural.guardrails.md` |
| Database schema | `data.model.spec.md` |
| API conventions | `api.common.spec.md` |
| Open questions | `decision.log.md` |
| JSON schemas | `data.model.spec.md` |
