# Control Plane Gap Analysis

## Summary

| Category | Documented | Implemented | Coverage |
|----------|------------|-------------|----------|
| Mappings API | 12 endpoints | 5 endpoints | 42% |
| Snapshots API | 8 endpoints | 6 endpoints | 75% |
| Instances API | 9 endpoints | 6 endpoints | 67% |
| Favorites API | 3 endpoints | 3 endpoints | 100% |
| Internal API | 10 endpoints | 2 endpoints | 20% |
| Admin/Ops API | 17 endpoints | 0 endpoints | 0% |
| **Total** | **59 endpoints** | **22 endpoints** | **37%** |

---

## Detailed Gap Analysis

### Mappings API (`api.mappings.spec.md`)

| Endpoint | Status | Priority |
|----------|--------|----------|
| `GET /mappings` | ✅ Implemented | - |
| `GET /mappings/:id` | ✅ Implemented | - |
| `POST /mappings` | ✅ Implemented | - |
| `PUT /mappings/:id` | ✅ Implemented | - |
| `DELETE /mappings/:id` | ✅ Implemented | - |
| `POST /mappings/:id/copy` | ❌ Missing | Medium |
| `PUT /mappings/:id/lifecycle` | ❌ Missing | Medium |
| `GET /mappings/:id/versions` | ❌ Missing | Medium |
| `GET /mappings/:id/versions/:version` | ❌ Missing | Medium |
| `GET /mappings/:id/versions/:v1/diff/:v2` | ❌ Missing | Low |
| `GET /mappings/:id/tree` | ❌ Missing | Low |
| `GET /mappings/:id/snapshots` | ❌ Missing | Medium |

### Snapshots API (`api.snapshots.spec.md`)

| Endpoint | Status | Priority |
|----------|--------|----------|
| `GET /snapshots` | ✅ Implemented | - |
| `GET /snapshots/:id` | ✅ Implemented | - |
| `POST /snapshots` | ✅ Implemented | - |
| `PUT /snapshots/:id` | ❌ Missing | Medium |
| `DELETE /snapshots/:id` | ✅ Implemented | - |
| `PUT /snapshots/:id/lifecycle` | ❌ Missing | Medium |
| `POST /snapshots/:id/retry` | ✅ Implemented | - |
| `GET /snapshots/:id/progress` | ✅ Implemented | - |

### Instances API (`api.instances.spec.md`)

| Endpoint | Status | Priority |
|----------|--------|----------|
| `GET /instances` | ✅ Implemented | - |
| `GET /instances/:id` | ✅ Implemented | - |
| `POST /instances` | ✅ Implemented | - |
| `PUT /instances/:id` | ❌ Missing | Medium |
| `DELETE /instances/:id` | ✅ Implemented | - |
| `POST /instances/:id/terminate` | ✅ Implemented | - |
| `POST /instances/:id/force-terminate` | ❌ Missing | Low (Ops only) |
| `PUT /instances/:id/lifecycle` | ❌ Missing | Medium |
| `GET /instances/:id/progress` | ❌ Missing | Medium |

### Favorites API (`api.favorites.spec.md`)

| Endpoint | Status | Priority |
|----------|--------|----------|
| `GET /favorites` | ✅ Implemented | - |
| `POST /favorites` | ✅ Implemented | - |
| `DELETE /favorites/:type/:id` | ✅ Implemented | - |

### Internal API (`api.internal.spec.md`)

| Endpoint | Status | Priority | Needed By |
|----------|--------|----------|-----------|
| `PUT /snapshots/:id/status` | ✅ Implemented | - | - |
| `POST /snapshots/:id/export-jobs` | ❌ Missing | **HIGH** | Export Submitter |
| `GET /snapshots/:id/export-jobs` | ❌ Missing | **HIGH** | Export Poller |
| `PATCH /export-jobs/:id` | ❌ Missing | **HIGH** | Export Poller |
| `PUT /instances/:id/status` | ✅ Implemented | - | - |
| `PUT /instances/:id/metrics` | ❌ Missing | **HIGH** | Wrapper Pod |
| `PUT /instances/:id/progress` | ❌ Missing | **HIGH** | Wrapper Pod |
| `GET /starburst/catalogs` | ❌ Missing | Low | Schema Browser |
| `GET /starburst/schemas` | ❌ Missing | Low | Schema Browser |
| `GET /starburst/tables` | ❌ Missing | Low | Schema Browser |
| `GET /starburst/columns` | ❌ Missing | Low | Schema Browser |
| `POST /starburst/parse-sql` | ❌ Missing | Low | Mapping Editor |
| `POST /starburst/validate` | ❌ Missing | Low | Mapping Editor |

### Admin/Ops API (`api.admin-ops.spec.md`)

| Endpoint | Status | Priority |
|----------|--------|----------|
| `GET /config/lifecycle` | ❌ Missing | Medium |
| `PUT /config/lifecycle` | ❌ Missing | Medium |
| `GET /config/concurrency` | ❌ Missing | Medium |
| `PUT /config/concurrency` | ❌ Missing | Medium |
| `GET /config/schemas` | ❌ Missing | Low |
| `PUT /config/schemas` | ❌ Missing | Low |
| `GET /config/schemas/cache` | ❌ Missing | Low |
| `POST /config/schemas/cache/refresh` | ❌ Missing | Low |
| `GET /config/maintenance` | ❌ Missing | Medium |
| `PUT /config/maintenance` | ❌ Missing | Medium |
| `GET /cluster/health` | ❌ Missing | Medium |
| `GET /cluster/instances` | ❌ Missing | Medium |
| `GET /cluster/metrics` | ❌ Missing | Low |
| `GET /exports` | ❌ Missing | Low |
| `GET /exports/stats` | ❌ Missing | Low |
| `POST /exports/:id/retry` | ❌ Missing | Low |
| `POST /exports/:id/cancel` | ❌ Missing | Low |

---

## Missing Repositories

| Repository | Status | Needed For |
|------------|--------|------------|
| `allowed_catalogs` | ❌ Missing | Schema browser whitelist |
| `allowed_schemas` | ❌ Missing | Schema browser whitelist |
| `schema_metadata_cache` | ❌ Missing | Schema browser cache |

---

## Prioritized Implementation Plan

### Phase 1: Critical (Export Worker + Wrapper Pod Dependencies)
**These endpoints are required for other components to function.**

1. Export Jobs Internal Router:
   - `POST /api/internal/snapshots/:id/export-jobs`
   - `GET /api/internal/snapshots/:id/export-jobs`
   - `PATCH /api/internal/export-jobs/:id`

2. Instance Metrics/Progress Internal Endpoints:
   - `PUT /api/internal/instances/:id/metrics`
   - `PUT /api/internal/instances/:id/progress`

### Phase 2: Core API Completeness
**Complete the public API to match documentation.**

3. Mapping Extensions:
   - `POST /mappings/:id/copy`
   - `PUT /mappings/:id/lifecycle`
   - `GET /mappings/:id/versions`
   - `GET /mappings/:id/versions/:version`
   - `GET /mappings/:id/snapshots`

4. Snapshot/Instance Extensions:
   - `PUT /snapshots/:id` (update name/description)
   - `PUT /snapshots/:id/lifecycle`
   - `PUT /instances/:id` (update name/description)
   - `PUT /instances/:id/lifecycle`
   - `GET /instances/:id/progress`

### Phase 3: Admin/Ops Features
**Operational management capabilities.**

5. Config Endpoints:
   - `GET/PUT /config/lifecycle`
   - `GET/PUT /config/concurrency`
   - `GET/PUT /config/maintenance`

6. Cluster Status:
   - `GET /cluster/health`
   - `GET /cluster/instances`

### Phase 4: Advanced Features
**Lower priority, can defer.**

7. Version Diff:
   - `GET /mappings/:id/versions/:v1/diff/:v2`
   - `GET /mappings/:id/tree`

8. Starburst Integration:
   - All `/starburst/*` endpoints (requires Starburst connection)

9. Schema Browser:
   - `GET/PUT /config/schemas`
   - Schema cache management

10. Export Queue Management:
    - `GET /exports`
    - `GET /exports/stats`
    - `POST /exports/:id/retry`
    - `POST /exports/:id/cancel`

---

## Recommendation

**Immediate action:** Implement Phase 1 (5 endpoints) - the export-worker and wrapper-pod cannot communicate with control-plane without these.

**Estimated effort:**
- Phase 1: ~2 hours (critical)
- Phase 2: ~4 hours (core completeness)
- Phase 3: ~3 hours (ops features)
- Phase 4: ~6 hours (advanced features)
