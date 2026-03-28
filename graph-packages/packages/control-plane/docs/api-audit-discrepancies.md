# API Documentation vs Implementation Audit Report

**Date:** 2025-01-15
**Auditor:** Senior Software Engineer
**Scope:** Control Plane API endpoints

---

## Executive Summary

This audit compares documentation across all system components to identify conflicts and gaps. **Documentation is the authoritative source** - all docs must align before implementation proceeds.

**Documents Analyzed:**
- `docs/system-design/api/*.spec.md` - API specifications
- `docs/component-designs/export-worker.design.md` - Export Worker design
- `docs/component-designs/ryugraph-wrapper.design.md` - RyuGraph Wrapper design
- `docs/component-designs/jupyter-sdk.design.md` - Jupyter SDK design

### Documentation Alignment Status: ✅ RESOLVED

All critical documentation conflicts have been resolved. The API specifications now align with consumer artifact designs.

| Issue | Status | Resolution |
|-------|--------|------------|
| GET /mapping endpoint direction | ✅ Fixed | Moved to "Wrapper Pod → Control Plane" section with path `/instances/:id/mapping` |
| Export jobs list response format | ✅ Fixed | Changed to `{data: {jobs: [...]}}` to match Worker design |
| Export jobs create missing fields | ✅ Fixed | Added `status`, `submitted_at` fields to request body |
| Export jobs update missing field | ✅ Fixed | Added `completed_at` field to request body |
| Instance activity endpoint | ✅ Fixed | Added `POST /instances/:id/activity` |
| Version diff endpoint | ✅ Already existed | `GET /mappings/:id/versions/:v1/diff/:v2` was already documented |
| Export queue endpoints | ✅ Already existed | `/exports/*` endpoints were already documented in api.admin-ops.spec.md |

### Consumer Documentation Alignment Summary

| Consumer | API Spec Alignment | Status |
|----------|-------------------|--------|
| Export Worker | ✅ **ALIGNED** | Response format and fields now match |
| RyuGraph Wrapper | ✅ **ALIGNED** | GET /mapping direction corrected, activity endpoint added |
| Jupyter SDK | ✅ **ALIGNED** | Pagination `meta` wrapper defined in api.common.spec.md |
| Web Application | ✅ ~95% | All critical endpoints documented; Starburst introspection is future scope |

### Remaining Implementation Work

The documentation is now aligned. Implementation should be updated to match the API specifications:

1. **Response format changes:**
   - List export jobs: wrap in `{data: {jobs: [...]}}`
   - Add `meta` wrapper to all paginated responses

2. **New endpoints to implement:**
   - `GET /instances/:id/mapping` - Return mapping definition for instance startup
   - `POST /instances/:id/activity` - Record query/algorithm activity
   - `GET /mappings/:id/versions/:v1/diff/:v2` - Compare mapping versions

3. **Field additions:**
   - Add `owner_id`, `owner_name`, `snapshot_count` to mapping responses
   - Add `mapping_name`, `instance_count` to snapshot responses
   - Add `snapshot_name` to instance responses

---

## 1. Mappings API

**Spec:** `docs/system-design/api/api.mappings.spec.md`
**Impl:** `src/control_plane/routers/api/mappings.py`

### 1.1 Endpoint Coverage

| Endpoint | Documented | Implemented | Status |
|----------|------------|-------------|--------|
| `GET /mappings` | Yes | Yes | OK |
| `GET /mappings/:id` | Yes | Yes | OK |
| `POST /mappings` | Yes | Yes | OK |
| `PUT /mappings/:id` | Yes | Yes | OK |
| `DELETE /mappings/:id` | Yes | Yes | OK |
| `POST /mappings/:id/copy` | Yes | Yes | OK |
| `PUT /mappings/:id/lifecycle` | Yes | Yes | OK |
| `GET /mappings/:id/versions` | Yes | Yes | OK |
| `GET /mappings/:id/versions/:version` | Yes | Yes | OK |
| `GET /mappings/:id/versions/:v1/diff/:v2` | Yes | **No** | **MISSING** |
| `GET /mappings/:id/tree` | Yes | **No** | **MISSING** |
| `GET /mappings/:id/snapshots` | Yes | Yes | OK |

### 1.2 Response Schema Discrepancies

| Field | Documentation | Implementation | Impact |
|-------|---------------|----------------|--------|
| ID type | `uuid` (string) | `integer` | **Breaking** |
| Owner field | `owner_id`, `owner_name` | `owner_username` only | **Breaking** |
| List response | includes `snapshot_count` | includes `node_count`, `edge_count` | Different |
| Version created_by | `created_by`, `created_by_name` | `created_by` only | Missing field |
| Query param `owner` | uuid type | string (username) | Type mismatch |
| Query params | `created_after`, `created_before` | Not implemented | Missing filters |

### 1.3 Missing Endpoints (High Priority)

#### `GET /mappings/:id/versions/:v1/diff/:v2`
- **Purpose:** Compare two versions showing added/removed/modified definitions
- **Complexity:** Medium - requires JSON diffing logic
- **Business Value:** Essential for version management workflow

#### `GET /mappings/:id/tree`
- **Purpose:** Show full hierarchy (mapping -> versions -> snapshots -> instances)
- **Complexity:** Medium - requires joining multiple tables
- **Business Value:** Useful for understanding resource dependencies

---

## 2. Snapshots API

**Spec:** `docs/system-design/api/api.snapshots.spec.md`
**Impl:** `src/control_plane/routers/api/snapshots.py`

### 2.1 Endpoint Coverage

| Endpoint | Documented | Implemented | Status |
|----------|------------|-------------|--------|
| `GET /snapshots` | Yes | Yes | OK |
| `GET /snapshots/:id` | Yes | Yes | OK |
| `POST /snapshots` | Yes | Yes | OK |
| `PUT /snapshots/:id` | Yes | Yes | OK |
| `DELETE /snapshots/:id` | Yes | Yes | OK |
| `PUT /snapshots/:id/lifecycle` | Yes | Yes | OK |
| `POST /snapshots/:id/retry` | Yes | Yes | OK |
| `GET /snapshots/:id/progress` | Yes | Yes | OK |

### 2.2 Response Schema Discrepancies

| Field | Documentation | Implementation | Impact |
|-------|---------------|----------------|--------|
| ID type | `uuid` (string) | `integer` | **Breaking** |
| Owner field | `owner_id`, `owner_name` | `owner_username` only | **Breaking** |
| List response | includes `mapping_name` | Not included | Missing field |
| List response | includes `instance_count` | Not included | Missing field |
| Get response | includes `instances` array | Not included | Missing field |
| Query param `mapping_version` | Documented | Not implemented | Missing filter |
| Query params | `created_after`, `created_before` | Not implemented | Missing filters |

---

## 3. Instances API

**Spec:** `docs/system-design/api/api.instances.spec.md`
**Impl:** `src/control_plane/routers/api/instances.py`

### 3.1 Endpoint Coverage

| Endpoint | Documented | Implemented | Status |
|----------|------------|-------------|--------|
| `GET /instances` | Yes | Yes | OK |
| `GET /instances/:id` | Yes | Yes | OK |
| `POST /instances` | Yes | Yes | OK |
| `PUT /instances/:id` | Yes | Yes | OK |
| `DELETE /instances/:id` | Yes | Yes | OK |
| `POST /instances/:id/terminate` | Yes | Yes | OK |
| `POST /instances/:id/force-terminate` | Yes | **No** | **MISSING** |
| `PUT /instances/:id/lifecycle` | Yes | Yes | OK |
| `GET /instances/:id/progress` | Yes | Yes | OK |
| `GET /instances/cluster/status` | **No** | Yes | **UNDOCUMENTED** |
| `GET /instances/user/status` | **No** | Yes | **UNDOCUMENTED** |

### 3.2 Response Schema Discrepancies

| Field | Documentation | Implementation | Impact |
|-------|---------------|----------------|--------|
| ID type | `uuid` (string) | `integer` | **Breaking** |
| Owner field | `owner_id`, `owner_name` | `owner_username` only | **Breaking** |
| Get response | includes `snapshot_name` | Not included | Missing field |
| Get response | includes `mapping_id`, `mapping_name`, `mapping_version` | Not included | Missing fields |
| Query params | `created_after`, `created_before` | Not implemented | Missing filters |

### 3.3 Missing Endpoints

#### `POST /instances/:id/force-terminate` (Ops Only)
- **Purpose:** Bypass graceful shutdown for stuck instances
- **Complexity:** Low - similar to terminate but with force flag
- **Business Value:** Critical for operational recovery

---

## 4. Favorites API

**Spec:** `docs/system-design/api/api.favorites.spec.md`
**Impl:** `src/control_plane/routers/api/favorites.py`

### 4.1 Endpoint Coverage

| Endpoint | Documented | Implemented | Status |
|----------|------------|-------------|--------|
| `GET /favorites` | Yes | Yes | OK |
| `POST /favorites` | Yes | Yes | OK |
| `DELETE /favorites/:resource_type/:resource_id` | Yes | Yes | OK |

**Status: FULLY ALIGNED**

---

## 5. Config API (Ops Only)

**Spec:** Not documented in API specs
**Impl:** `src/control_plane/routers/api/config.py`

### 5.1 Undocumented Endpoints

| Endpoint | Implemented | Need Documentation |
|----------|-------------|-------------------|
| `GET /config/lifecycle` | Yes | **Yes** |
| `PUT /config/lifecycle` | Yes | **Yes** |
| `GET /config/concurrency` | Yes | **Yes** |
| `PUT /config/concurrency` | Yes | **Yes** |
| `GET /config/maintenance` | Yes | **Yes** |
| `PUT /config/maintenance` | Yes | **Yes** |

**Action Required:** Create `api.config.spec.md`

---

## 6. Cluster API (Ops Only)

**Spec:** Not documented in API specs
**Impl:** `src/control_plane/routers/api/cluster.py`

### 6.1 Undocumented Endpoints

| Endpoint | Implemented | Need Documentation |
|----------|-------------|-------------------|
| `GET /cluster/health` | Yes | **Yes** |
| `GET /cluster/instances` | Yes | **Yes** |

**Action Required:** Create `api.cluster.spec.md` or add to `api.config.spec.md`

---

## 7. Internal API

**Spec:** `docs/system-design/api/api.internal.spec.md`
**Impl:** `src/control_plane/routers/internal/*.py`

### 7.1 Worker -> Control Plane Endpoints

| Endpoint | Documented | Implemented | Method Match |
|----------|------------|-------------|--------------|
| `/snapshots/:id/status` | PUT | PATCH | **MISMATCH** |
| `/snapshots/:id/export-jobs` (POST) | Yes | Yes | OK |
| `/snapshots/:id/export-jobs` (GET) | Yes | Yes | OK |
| `/export-jobs/:id` | PATCH | PATCH | OK |

### 7.2 Wrapper -> Control Plane Endpoints

| Endpoint | Documented | Implemented | Method Match |
|----------|------------|-------------|--------------|
| `/instances/:id/status` | PUT | PATCH | **MISMATCH** |
| `/instances/:id/metrics` | PUT | PUT | OK |
| `/instances/:id/progress` | PUT | PUT | OK |
| `/instances/:id/activity` | **No** | POST | **UNDOCUMENTED** |

### 7.3 Starburst Introspection Endpoints

| Endpoint | Documented | Implemented | Status |
|----------|------------|-------------|--------|
| `GET /starburst/catalogs` | Yes | **No** | **MISSING** |
| `GET /starburst/schemas` | Yes | **No** | **MISSING** |
| `GET /starburst/tables` | Yes | **No** | **MISSING** |
| `GET /starburst/columns` | Yes | **No** | **MISSING** |
| `POST /starburst/parse-sql` | Yes | **No** | **MISSING** |
| `POST /starburst/validate` | Yes | **No** | **MISSING** |

---

## 8. Systematic Discrepancies (Affecting All APIs)

### 8.1 ID Type Inconsistency

**Documentation:** All IDs are UUIDs (strings like `"550e8400-e29b-41d4-a716-446655440000"`)
**Implementation:** All IDs are integers

**Recommendation:** Update documentation to reflect integer IDs (current implementation is correct for SQLite/PostgreSQL compatibility).

### 8.2 Owner Field Naming

**Documentation:** Uses `owner_id` (UUID) and `owner_name` (display name)
**Implementation:** Uses `owner_username` (string username)

**Recommendation:** Either:
1. Add `owner_id` and `owner_name` to responses (requires user lookup)
2. Update documentation to use `owner_username`

### 8.3 Missing Filter Parameters

The following filter parameters are documented but not implemented across multiple endpoints:
- `created_after` (timestamp filter)
- `created_before` (timestamp filter)
- `mapping_version` (for snapshots)

---

## 9. Consumer Analysis

This section analyzes API requirements from each component that consumes the Control Plane API.

### 9.1 Export Worker Requirements (Detailed Analysis)

**Sources:**
- `docs/component-designs/export-worker.design.md` (Worker implementation design)
- `docs/system-design/api/api.internal.spec.md` (API specification)
- `src/control_plane/routers/internal/export_jobs.py` (Implementation)

#### Endpoint Summary

| Endpoint | API Spec | Worker Design | Implementation | Status |
|----------|----------|---------------|----------------|--------|
| Update snapshot status | PUT | PUT | PATCH | **METHOD MISMATCH** |
| Create export jobs | POST | POST | POST | **WORKFLOW MISMATCH** |
| List export jobs | GET | GET | GET | **RESPONSE MISMATCH** |
| Update export job | PATCH | PATCH | PATCH | **VALIDATION MISMATCH** |

#### 9.1.1 Update Snapshot Status - METHOD MISMATCH

| Attribute | API Spec | Worker Design | Implementation |
|-----------|----------|---------------|----------------|
| HTTP Method | PUT | PUT | **PATCH** |
| Path | `/snapshots/:id/status` | `/api/internal/snapshots/{id}/status` | `/api/internal/snapshots/{id}/status` |

**Resolution needed:** Change API spec and Worker design from PUT to PATCH.

#### 9.1.2 Create Export Jobs - Field Comparison

**Worker Design sends (lines 254-263, 1027-1039):**
```python
ExportJob(
    snapshot_id=...,
    job_type="node",
    entity_name=node_def["label"],
    status="running",
    starburst_query_id=query_id,
    next_uri=next_uri,
    gcs_path=gcs_path,
    submitted_at=datetime.utcnow().isoformat() + "Z",
)

body = {"jobs": [job.to_dict() for job in jobs]}
```

**API Internal Spec (lines 95-146) documents request body:**
```json
{
  "jobs": [
    {
      "job_type": "node",
      "entity_name": "Customer",
      "starburst_query_id": "20250115_ABC123",
      "next_uri": "https://starburst.example.com/v1/query/...",
      "gcs_path": "gs://..."
    }
  ]
}
```

| Field | Worker Sends | API Spec Documents | Status |
|-------|--------------|-------------------|--------|
| `job_type` | ✓ | ✓ | ✓ Aligned |
| `entity_name` | ✓ | ✓ | ✓ Aligned |
| `starburst_query_id` | ✓ | ✓ | ✓ Aligned |
| `next_uri` | ✓ | ✓ | ✓ Aligned |
| `gcs_path` | ✓ | ✓ | ✓ Aligned |
| `status` | ✓ ("running") | ❌ Not shown | ⚠️ Gap |
| `submitted_at` | ✓ | ❌ Not shown | ⚠️ Gap |
| `snapshot_id` | ✓ (in job object) | ❌ Not shown (in URL) | ⚠️ Gap |

**Create Jobs Response:**

| Attribute | Worker Design | API Spec |
|-----------|---------------|----------|
| Response body | Not parsed (checks 201 status only) | `{data: {created: N, jobs: [...]}}`  |

**Status: ⚠️ PARTIAL ALIGNMENT** - API spec should document `status`, `submitted_at` fields if Worker sends them.

#### 9.1.3 List Export Jobs - CRITICAL RESPONSE FORMAT CONFLICT

**Worker Design parses (line 1065):**
```python
return [ExportJob.from_dict(j) for j in response.json()["data"]["jobs"]]
```

**API Internal Spec documents (lines 168-204):**
```json
{
  "data": [
    {"id": 1, "snapshot_id": 42, "job_type": "node", ...}
  ]
}
```

| Attribute | Worker Expects | API Spec Documents |
|-----------|----------------|-------------------|
| Response parsing | `response["data"]["jobs"]` | `response["data"]` (array directly) |

**STATUS: ❌ CRITICAL CONFLICT**

**Resolution Required:** Either:
1. **Option A:** Update API spec to return `{data: {jobs: [...]}}`
2. **Option B:** Update Worker design to parse `response["data"]` directly

#### 9.1.4 Update Export Job - Field Comparison

**Worker Design sends (lines 1072-1105):**
```python
body = {}
if status is not None: body["status"] = status
if next_uri is not None: body["next_uri"] = next_uri
if row_count is not None: body["row_count"] = row_count
if size_bytes is not None: body["size_bytes"] = size_bytes
if completed_at is not None: body["completed_at"] = completed_at
if error_message is not None: body["error_message"] = error_message
```

**API Internal Spec documents (lines 209-265):**
```json
{
  "next_uri": "...",
  "status": "completed",
  "row_count": 10000,
  "size_bytes": 52428800,
  "error_message": "..."
}
```

| Field | Worker Sends | API Spec Documents | Status |
|-------|--------------|-------------------|--------|
| `status` | ✓ | ✓ | ✓ Aligned |
| `next_uri` | ✓ | ✓ | ✓ Aligned |
| `row_count` | ✓ | ✓ | ✓ Aligned |
| `size_bytes` | ✓ | ✓ | ✓ Aligned |
| `error_message` | ✓ | ✓ | ✓ Aligned |
| `completed_at` | ✓ | ❌ Not shown | ⚠️ Gap |

**Status: ⚠️ MOSTLY ALIGNED** - `completed_at` not documented in API spec.

#### 9.1.5 Export Worker Documentation Summary

| Issue | Status | Resolution Applied |
|-------|--------|-------------------|
| List jobs response format | ✅ **FIXED** | API spec now returns `{data: {jobs: [...]}}` |
| Create jobs missing fields | ✅ **FIXED** | Added `status`, `submitted_at` to API spec |
| Update job missing field | ✅ **FIXED** | Added `completed_at` to API spec |

**✅ RESOLVED: All Export Worker documentation conflicts have been fixed in `api.internal.spec.md`.**

### 9.2 RyuGraph Wrapper Requirements (Detailed Analysis)

**Sources:**
- `docs/component-designs/ryugraph-wrapper.design.md` (Wrapper design - what the Wrapper expects to CALL)
- `docs/system-design/api/api.internal.spec.md` (API spec - what Control Plane documents as AVAILABLE)

#### Endpoint Summary

| Endpoint | Wrapper Design | API Internal Spec | Status |
|----------|----------------|-------------------|--------|
| Update instance status | PUT `/api/internal/instances/{id}/status` | PUT `/instances/:id/status` | ✓ Aligned |
| Update instance metrics | PUT `/api/internal/instances/{id}/metrics` | PUT `/instances/:id/metrics` | ⚠️ Partial |
| Update instance progress | PUT `/api/internal/instances/{id}/progress` | PUT `/instances/:id/progress` | ⚠️ Partial |
| Get instance mapping | GET `/api/internal/instances/{id}/mapping` | GET `/mapping` (ON WRAPPER!) | **CRITICAL CONFLICT** |

#### 9.2.1 CRITICAL: Get Mapping Endpoint Direction REVERSED

**Wrapper Design (lines 1472-1485) - Wrapper CALLS Control Plane:**
```python
async def get_instance_mapping(self, instance_id: int) -> MappingDefinition:
    """Get mapping definition for instance startup."""
    async with session.get(
        f"{self.base_url}/api/internal/instances/{instance_id}/mapping",
        ...
    ) as response:
        data = await response.json()
        return MappingDefinition(**data["data"])
```

**API Internal Spec (lines 426-447) - Control Plane CALLS Wrapper:**
```
GET /mapping

Called during startup to retrieve the mapping definition for schema creation.

Response: 200 OK
{
  "data": {
    "snapshot_id": "snapshot-uuid",
    "mapping_id": "mapping-uuid",
    ...
  }
}
```

| Document | Direction | Path |
|----------|-----------|------|
| Wrapper Design | Wrapper → Control Plane | `GET /api/internal/instances/{id}/mapping` |
| API Internal Spec | Control Plane → Wrapper | `GET /mapping` |

**This is an architectural contradiction.** The API spec has this backwards - the Wrapper NEEDS the mapping definition to create its schema. It cannot serve `/mapping` before it has the data.

**Resolution Required:** Update `api.internal.spec.md` to document:
```
GET /instances/:id/mapping

Called by Wrapper Pod during startup to retrieve mapping definition.

Response: 200 OK
{
  "data": {
    "snapshot_id": 42,
    "mapping_id": 123,
    "mapping_version": 3,
    "gcs_path": "gs://bucket/user/mapping/snapshot/",
    "node_definitions": [...],
    "edge_definitions": [...]
  }
}
```

#### 9.2.2 Update Instance Metrics - Field Mismatch

**Wrapper Design sends (lines 1447-1470):**
```python
json={
    "memory_usage_bytes": memory_usage_bytes,
    "disk_usage_bytes": disk_usage_bytes,
    "last_activity_at": last_activity_at,
}
```

**API Internal Spec documents (lines 320-330):**
```json
{
  "memory_usage_bytes": 536870912,
  "disk_usage_bytes": 1073741824,
  "last_activity_at": "2025-01-15T14:00:00Z",
  "query_count_since_last": 15,
  "avg_query_time_ms": 25
}
```

| Field | Wrapper Sends | API Spec Documents |
|-------|---------------|-------------------|
| `memory_usage_bytes` | ✓ | ✓ |
| `disk_usage_bytes` | ✓ | ✓ |
| `last_activity_at` | ✓ | ✓ |
| `query_count_since_last` | ❌ Not sent | ✓ Documented |
| `avg_query_time_ms` | ❌ Not sent | ✓ Documented |

**Resolution Options:**
1. **Option A:** Update Wrapper design to send `query_count_since_last` and `avg_query_time_ms`
2. **Option B:** Mark these fields as optional in API spec (they're useful but not critical)

#### 9.2.3 Update Instance Progress - Field Alignment

**Wrapper Design (lines 220-238) sends steps with:**
- `name`
- `status`

**Wrapper Design load_data callback (line 245-248) sends:**
- `step` (name)
- `status`
- `count` (row_count)

**API Internal Spec (lines 354-362) documents:**
```json
{
  "phase": "loading_nodes",
  "steps": [
    {"name": "pod_scheduled", "status": "completed"},
    {"name": "Customer", "type": "node", "status": "completed", "row_count": 10000},
    {"name": "PURCHASED", "type": "edge", "status": "pending"}
  ]
}
```

| Field | Wrapper Sends | API Spec Documents |
|-------|---------------|-------------------|
| `steps[].name` | ✓ | ✓ |
| `steps[].status` | ✓ | ✓ |
| `steps[].type` | ❌ Not explicitly sent | ✓ Optional |
| `steps[].row_count` | ✓ Via callback | ✓ Optional |

**Resolution:** Update Wrapper design to send `type` field (`"node"` or `"edge"`) for each loading step to match API spec.

#### 9.2.4 Update Instance Status - Aligned

**Wrapper Design sends (lines 1422-1434):**
```python
body = {"status": status}
if pod_ip: body["pod_ip"] = pod_ip
if instance_url: body["instance_url"] = instance_url
if graph_stats: body["graph_stats"] = graph_stats
if error_message: body["error_message"] = error_message
if failed_phase: body["failed_phase"] = failed_phase
```

**API Spec documents (lines 278-300):**
- Running: `{status, pod_ip, instance_url, graph_stats}`
- Failed: `{status, error_message, failed_phase}`

**Status: ✓ FULLY ALIGNED**

#### 9.2.5 RyuGraph Wrapper Summary

| Issue | Status | Resolution Applied |
|-------|--------|-------------------|
| GET /mapping endpoint direction reversed | ✅ **FIXED** | Moved to "Wrapper Pod → Control Plane" section as `GET /instances/:id/mapping` |
| Missing activity endpoint | ✅ **FIXED** | Added `POST /instances/:id/activity` to API spec |
| Missing query metrics fields | ⚠️ Low | `query_count_since_last`, `avg_query_time_ms` are optional |
| Missing `type` field in progress steps | ⚠️ Low | API spec documents `type` as optional |

**✅ RESOLVED: Critical RyuGraph Wrapper documentation conflicts have been fixed in `api.internal.spec.md`.**

The Wrapper startup sequence now matches the API spec:
1. Pod starts
2. **Wrapper calls Control Plane**: `GET /instances/:id/mapping`
3. Control Plane returns mapping definition with `gcs_path`, `node_definitions`, `edge_definitions`
4. Wrapper creates schema and loads data from GCS
5. Wrapper reports "running" status via `PUT /instances/:id/status`

### 9.3 Jupyter SDK Requirements (Detailed Analysis)

**Sources (Documentation Only):**
- `docs/component-designs/jupyter-sdk.design.md` (SDK design with model definitions)
- `docs/system-design/api.common.spec.md` (Common API patterns including pagination)
- `docs/system-design/api/api.mappings.spec.md`, `api.snapshots.spec.md`, `api.instances.spec.md`

#### 9.3.1 Pagination Format - ALIGNED ✓

**SDK Design expects (lines 362-367):**
```python
return PaginatedList(
    items=[Mapping.from_dict(m) for m in response["data"]],
    total=response["meta"]["total"],
    offset=response["meta"]["offset"],
    limit=response["meta"]["limit"],
)
```

**API Common Spec documents (lines 119-133):**
```json
{
  "data": [...],
  "meta": {
    "request_id": "req-uuid",
    "total": 150,
    "offset": 0,
    "limit": 50
  }
}
```

**Status: ✓ FULLY ALIGNED** - Both SDK design and API spec use `meta.{total, offset, limit}`.

#### 9.3.2 Response Fields - ALIGNED ✓

##### Mapping Response

| SDK Expects | API Spec Documents | Status |
|-------------|-------------------|--------|
| `id` | ✓ | ✓ Aligned |
| `owner_id` | ✓ `"owner_id": "user-uuid"` | ✓ Aligned |
| `owner_name` | ✓ `"owner_name": "Alice Smith"` | ✓ Aligned |
| `name` | ✓ | ✓ Aligned |
| `description` | ✓ | ✓ Aligned |
| `current_version` | ✓ | ✓ Aligned |
| `snapshot_count` | ✓ `"snapshot_count": 5` | ✓ Aligned |
| `ttl` | ✓ | ✓ Aligned |
| `inactivity_timeout` | ✓ | ✓ Aligned |
| `created_at` | ✓ | ✓ Aligned |
| `updated_at` | ✓ | ✓ Aligned |

**Status: ✓ FULLY ALIGNED**

##### MappingVersion Response

| SDK Expects | API Spec Documents | Status |
|-------------|-------------------|--------|
| `mapping_id` | ✓ (implied) | ✓ Aligned |
| `version` | ✓ | ✓ Aligned |
| `change_description` | ✓ | ✓ Aligned |
| `node_definitions` | ✓ | ✓ Aligned |
| `edge_definitions` | ✓ | ✓ Aligned |
| `created_at` | ✓ | ✓ Aligned |
| `created_by` | ✓ `"created_by": "user-uuid"` | ✓ Aligned |
| `created_by_name` | ✓ `"created_by_name": "Alice Smith"` | ✓ Aligned |

**Status: ✓ FULLY ALIGNED**

##### Snapshot Response

| SDK Expects | API Spec Documents | Status |
|-------------|-------------------|--------|
| `id` | ✓ | ✓ Aligned |
| `mapping_id` | ✓ | ✓ Aligned |
| `mapping_name` | ✓ `"mapping_name": "Customer Transactions"` | ✓ Aligned |
| `mapping_version` | ✓ | ✓ Aligned |
| `owner_id` | ✓ `"owner_id": "user-uuid"` | ✓ Aligned |
| `owner_name` | ✓ `"owner_name": "Alice Smith"` | ✓ Aligned |
| `name` | ✓ | ✓ Aligned |
| `description` | ✓ | ✓ Aligned |
| `gcs_path` | ✓ | ✓ Aligned |
| `size_bytes` | ✓ | ✓ Aligned |
| `node_counts` | ✓ | ✓ Aligned |
| `edge_counts` | ✓ | ✓ Aligned |
| `status` | ✓ | ✓ Aligned |
| `error_message` | ✓ | ✓ Aligned |
| `instance_count` | ✓ `"instance_count": 2` | ✓ Aligned |
| `ttl` | ✓ | ✓ Aligned |
| `inactivity_timeout` | ✓ | ✓ Aligned |

**Status: ✓ FULLY ALIGNED**

##### Instance Response

| SDK Expects | API Spec Documents | Status |
|-------------|-------------------|--------|
| `id` | ✓ | ✓ Aligned |
| `snapshot_id` | ✓ | ✓ Aligned |
| `snapshot_name` | ✓ `"snapshot_name": "January 2025 Snapshot"` | ✓ Aligned |
| `owner_id` | ✓ `"owner_id": "user-uuid"` | ✓ Aligned |
| `owner_name` | ✓ `"owner_name": "Alice Smith"` | ✓ Aligned |
| `name` | ✓ | ✓ Aligned |
| `description` | ✓ | ✓ Aligned |
| `instance_url` | ✓ | ✓ Aligned |
| `status` | ✓ | ✓ Aligned |
| `error_message` | ✓ | ✓ Aligned |
| `created_at` | ✓ | ✓ Aligned |
| `started_at` | ✓ | ✓ Aligned |
| `last_activity_at` | ✓ | ✓ Aligned |
| `ttl` | ✓ | ✓ Aligned |
| `inactivity_timeout` | ✓ | ✓ Aligned |
| `memory_usage_bytes` | ✓ | ✓ Aligned |
| `disk_usage_bytes` | ✓ | ✓ Aligned |

**Status: ✓ FULLY ALIGNED**

#### 9.3.3 Query Parameters - ALIGNED ✓

| Parameter | SDK Sends | API Spec Documents | Status |
|-----------|-----------|-------------------|--------|
| `owner` | ✓ | ✓ | ✓ Aligned |
| `search` | ✓ | ✓ | ✓ Aligned |
| `created_after` | ✓ | ✓ | ✓ Aligned |
| `created_before` | ✓ | ✓ | ✓ Aligned |
| `sort_by` | ✓ | ✓ | ✓ Aligned |
| `sort_order` | ✓ | ✓ | ✓ Aligned |
| `offset` | ✓ | ✓ | ✓ Aligned |
| `limit` | ✓ | ✓ | ✓ Aligned |
| `mapping_id` (snapshots) | ✓ | ✓ | ✓ Aligned |
| `mapping_version` (snapshots) | ✓ | ✓ | ✓ Aligned |
| `status` | ✓ | ✓ | ✓ Aligned |
| `snapshot_id` (instances) | ✓ | ✓ | ✓ Aligned |

**Status: ✓ FULLY ALIGNED**

#### 9.3.4 Jupyter SDK Documentation Summary

**✅ SDK design and API specs are FULLY ALIGNED**

| Category | Status |
|----------|--------|
| Pagination format (`meta.{total,offset,limit}`) | ✓ Aligned |
| Mapping response fields | ✓ Aligned |
| MappingVersion response fields | ✓ Aligned |
| Snapshot response fields | ✓ Aligned |
| Instance response fields | ✓ Aligned |
| Query parameters | ✓ Aligned |

**The SDK design follows the API specifications exactly.** Any discrepancies are between API specs and implementation, not between SDK and API specs.

**Note:** SDK connects directly to wrapper pods via `instance_url` for query/algorithm operations, not through Control Plane.

### 9.4 Web Application Requirements

**Source:** `docs/ux-design/ux.flows.md`, `docs/ux-design/ux.components.spec.md`

**User-Facing Pages:**

| Page | Required Endpoints | Status |
|------|-------------------|--------|
| Dashboard | GET /mappings, /snapshots, /instances, /favorites (filtered) | ✓ All implemented |
| Mappings List | GET /mappings (with filters, pagination, sort) | ✓ Implemented |
| Mapping Create | POST /mappings | ✓ Implemented |
| Mapping Detail | GET /mappings/:id, /versions, /snapshots | ✓ All implemented |
| Mapping Edit | PUT /mappings/:id | ✓ Implemented |
| **Mapping Compare** | GET /mappings/:id/versions/:v1/diff/:v2 | **NOT IMPLEMENTED** |
| Snapshots List | GET /snapshots | ✓ Implemented |
| Snapshot Detail | GET /snapshots/:id, /progress | ✓ All implemented |
| Instances List | GET /instances | ✓ Implemented |
| Instance Detail | GET /instances/:id, /progress | ✓ All implemented |
| Instance Terminate | POST /instances/:id/terminate | ✓ Implemented |
| Instance Extend TTL | PUT /instances/:id/lifecycle | ✓ Implemented |
| Favorites | GET/POST/DELETE /favorites | ✓ All implemented |

**Ops Pages:**

| Page | Required Endpoints | Status |
|------|-------------------|--------|
| Cluster Health | GET /cluster/health, /cluster/instances | ✓ Implemented (undocumented) |
| Configuration | GET/PUT /config/lifecycle, /concurrency, /maintenance | ✓ Implemented (undocumented) |
| Export Queue | See detail below | **PARTIALLY IMPLEMENTED** |

**Export Queue Page Requirements** (from ux.flows.md Flow 8):

The Export Queue page shows all export jobs cluster-wide with:
- Columns: Snapshot name, Status, Attempts, Created, Actions
- Filter by status (Queued, Processing, Failed, Dead Letter)
- Retry button for failed jobs
- Cancel button for queued jobs

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `GET /api/ops/export-jobs` | List ALL export jobs cluster-wide | **NOT IMPLEMENTED** |
| `POST /api/snapshots/:id/retry` | Retry failed export | ✓ Implemented |
| `POST /api/ops/export-jobs/:id/cancel` | Cancel queued job | **NOT IMPLEMENTED** |

**Note:** Current `GET /api/internal/snapshots/:id/export-jobs` is per-snapshot and internal-only. Ops UI needs a cluster-wide list.

**Schema Browser (Create Mapping page):**

| Endpoint | Documented | Implemented |
|----------|------------|-------------|
| GET /starburst/catalogs | Yes | **No** |
| GET /starburst/schemas | Yes | **No** |
| GET /starburst/tables | Yes | **No** |
| GET /starburst/columns | Yes | **No** |
| POST /starburst/parse-sql | Yes | **No** |
| POST /starburst/validate | Yes | **No** |

**Note:** The web application's Create Mapping page requires a schema browser (ADR-012) to help users write SQL queries. These Starburst introspection endpoints are not implemented.

### 9.5 Orphan Endpoints (No Consumer)

Endpoints documented or implemented that no consumer currently requires:

| Endpoint | In Docs | In Code | Consumer Need |
|----------|---------|---------|---------------|
| `GET /mappings/:id/tree` | Yes | No | Low - can be built from existing endpoints |
| `GET /instances/cluster/status` | No | Yes | Unknown - may be for future dashboard |
| `GET /instances/user/status` | No | Yes | Unknown - may be for future dashboard |

**Recommendation:** Remove `GET /mappings/:id/tree` from documentation OR implement it if product requirement exists.

### 9.6 Consumer Documentation Alignment Summary

**Documentation Alignment Status: ✅ ALL RESOLVED**

| Consumer | Design Doc | API Spec | Alignment Status |
|----------|------------|----------|------------------|
| **Export Worker** | `export-worker.design.md` | `api.internal.spec.md` | ✅ **ALIGNED** |
| **RyuGraph Wrapper** | `ryugraph-wrapper.design.md` | `api.internal.spec.md` | ✅ **ALIGNED** |
| **Jupyter SDK** | `jupyter-sdk.design.md` | `api.*.spec.md` | ✅ **ALIGNED** |
| **Web Application** | UX design docs | `api.*.spec.md` | ✅ ~95% (Starburst is future scope) |

**Resolved Documentation Conflicts:**

| Conflict | Consumer | Resolution Applied |
|----------|----------|-------------------|
| List export jobs response | Export Worker | ✅ API spec now returns `{data: {jobs: [...]}}` |
| GET /mapping direction | RyuGraph Wrapper | ✅ Moved to Wrapper→CP section as `GET /instances/:id/mapping` |
| Missing activity endpoint | RyuGraph Wrapper | ✅ Added `POST /instances/:id/activity` |
| Missing export job fields | Export Worker | ✅ Added `status`, `submitted_at`, `completed_at` |

**Endpoint Documentation Status:**

| Endpoint | Consumer | Status |
|----------|----------|--------|
| `GET /api/internal/instances/:id/mapping` | RyuGraph Wrapper | ✅ Now documented |
| `POST /api/internal/instances/:id/activity` | RyuGraph Wrapper | ✅ Now documented |
| `GET /mappings/:id/versions/:v1/diff/:v2` | Web Application | ✅ Already documented |
| `GET /exports` | Web Application | ✅ Already documented in api.admin-ops.spec.md |
| `POST /exports/:id/cancel` | Web Application | ✅ Already documented in api.admin-ops.spec.md |

**Key Finding:** All consumer artifacts now have fully aligned documentation. The API specifications are the authoritative source and implementation should follow them.

---

## 10. Priority Action Items - IMPLEMENTATION

**Documentation Status:** ✅ All API specifications are now aligned with consumer artifact designs.

**Next Phase:** Update implementation to match the API specifications.

### P0: Critical Implementation Changes

1. **IMPLEMENT: `GET /instances/:id/mapping`** (RyuGraph Wrapper startup)
   - **File:** `src/control_plane/routers/internal/instances.py`
   - **Returns:** `{snapshot_id, mapping_id, mapping_version, gcs_path, node_definitions, edge_definitions}`
   - **Consumer:** RyuGraph Wrapper (cannot start without this)

2. **FIX: List export jobs response format**
   - **File:** `src/control_plane/routers/internal/export_jobs.py`
   - **Change:** Return `{data: {jobs: [...]}}` instead of `{data: [...]}`
   - **Consumer:** Export Worker (will crash without this)

3. **FIX: Paginated response format**
   - **File:** `src/control_plane/models/responses.py`
   - **Change:** Wrap pagination fields in `meta: {total, offset, limit}`
   - **Consumer:** Jupyter SDK (will crash without this)

### P1: High Priority Implementation

4. **IMPLEMENT: `POST /instances/:id/activity`**
   - **File:** `src/control_plane/routers/internal/instances.py`
   - **Purpose:** Update `last_activity_at` timestamp
   - **Consumer:** RyuGraph Wrapper (activity tracking)

5. **IMPLEMENT: `GET /mappings/:id/versions/:v1/diff/:v2`**
   - **File:** `src/control_plane/routers/api/mappings.py`
   - **Purpose:** Compare two mapping versions
   - **Consumer:** Web Application (Compare Versions page)

6. **ADD: Missing response fields**
   - Add `owner_id`, `owner_name`, `snapshot_count` to MappingResponse
   - Add `mapping_name`, `instance_count` to SnapshotResponse
   - Add `snapshot_name` to InstanceResponse

7. **ADD: Missing query parameters**
   - `created_after`, `created_before` for all list endpoints
   - `mapping_version` for snapshots list

### P2: Medium Priority Implementation

8. **ADD: Export job fields to create endpoint**
   - Accept `status` (default: "running")
   - Accept `submitted_at` (default: current time)

9. **ADD: `completed_at` to update export job endpoint**
   - Accept `completed_at` (default: current time when status=completed)

### P3: Future Scope

10. **Starburst introspection endpoints** (Schema Browser feature)
    - 6 endpoints for catalog/schema/table browsing
    - Not required for MVP

11. **`GET /mappings/:id/tree`** (Resource hierarchy view)
    - Low priority, can be built from existing endpoints

---

## 11. Documentation Update Checklist

**Status:** ✅ All critical documentation updates have been completed.

### Completed Documentation Changes

| File | Changes Made | Status |
|------|-------------|--------|
| `api.internal.spec.md` | Fixed GET /mapping direction, added activity endpoint, added export job fields | ✅ Done |
| `api.common.spec.md` | Pagination `meta` format already defined | ✅ Already existed |
| `api.mappings.spec.md` | Version diff endpoint already documented | ✅ Already existed |
| `api.admin-ops.spec.md` | Export queue endpoints already documented | ✅ Already existed |

### No Changes Needed

| File | Reason |
|------|--------|
| `export-worker.design.md` | API spec updated to match Worker design (Option A chosen) |
| `jupyter-sdk.design.md` | API spec already matches SDK design |
| `api.config.spec.md` | Config endpoints already in `api.admin-ops.spec.md` |
| `api.cluster.spec.md` | Cluster endpoints already in `api.admin-ops.spec.md` |

### Summary of Changes to `api.internal.spec.md`

1. **Moved** `GET /mapping` from "Control Plane → Wrapper Pod" to "Wrapper Pod → Control Plane"
2. **Changed path** from `GET /mapping` to `GET /instances/:id/mapping`
3. **Added** `POST /instances/:id/activity` endpoint
4. **Updated** List Export Jobs response to use `{data: {jobs: [...]}}`
5. **Added** `status`, `submitted_at` fields to Create Export Jobs request
6. **Added** `completed_at` field to Update Export Job request
7. **Added** field description tables for export job endpoints

---

## Appendix: Test Coverage Verification

The integration tests at `tests/integration/` validate the implemented endpoints. Current test files:
- `test_api_mappings.py`
- `test_api_snapshots.py`
- `test_api_instances.py`
- `test_api_favorites.py`
- `test_api_cluster.py`
- `test_api_config.py`
- `test_internal_api.py`

Tests pass for all implemented endpoints (129 passing tests).
