# UI/UX Readiness Assessment

> **DEPRECATED** - This document is no longer maintained.
>
> The Graph OLAP Platform no longer includes a web interface. All user interaction
> is now through the Jupyter SDK. This document is retained for historical reference.
>
> See [jupyter-sdk.design.md](../component-designs/jupyter-sdk.design.md) for the current user interface design.

## Overview

Assessment of product engineering documentation completeness for informing UI/UX design work. This document identifies what's ready, what gaps exist, and what decisions are needed before or during UI/UX design.

**Assessment Date:** 2025-12-12
**Verdict:** 100% Ready - Product engineering complete for UI/UX handoff

---

## Executive Summary

The documentation is comprehensive for product engineering. All identified UX specification gaps have been resolved through ADRs 006-016.

**Key Strengths:**
- Complete domain model and data structures
- Fully specified API contracts (35+ endpoints)
- Clear user roles and permissions
- Detailed UX requirements in requirements.md (progress visibility, error messages, bulk operations)
- State machines for all async operations
- **11 ADRs** covering all UX design decisions
- **Internationalization** decided (ADR-015): English + Simplified Chinese with resource bundles
- **Ops section scope** clarified (ADR-016): Full UI, implementation method TBD

**Remaining Open Questions (not blocking UI/UX):**
- Infrastructure: Jupyter connectivity, domain config, CORS
- OQ-025: Ops implementation (Direct K8s vs GitOps) - does not affect UI scope

---

## What's Complete

### 1. Domain Model & Data Structures

| Document | Content | Status |
|----------|---------|--------|
| [requirements.md](../foundation/requirements.md) | Core resources (Mapping, Snapshot, Instance), field definitions, validation rules | Complete |
| [data.model.spec.md](../system-design/data.model.spec.md) | Database schema, JSON schemas for node/edge definitions, progress tracking schemas | Complete |

### 2. API Contracts

| Document | Content | Status |
|----------|---------|--------|
| [api.common.spec.md](../system-design/api.common.spec.md) | Request/response formats, pagination, filtering, sorting, error codes | Complete |
| [api/api.mappings.spec.md](../system-design/api/api.mappings.spec.md) | Mapping CRUD, versioning, lifecycle | Complete |
| [api/api.snapshots.spec.md](../system-design/api/api.snapshots.spec.md) | Snapshot CRUD, progress tracking | Complete |
| [api/api.instances.spec.md](../system-design/api/api.instances.spec.md) | Instance CRUD, lock status | Complete |
| [api/api.wrapper.spec.md](../system-design/api/api.wrapper.spec.md) | Graph queries, algorithms | Complete |

### 3. User Roles & Permissions

From [requirements.md](../foundation/requirements.md) and [architectural.guardrails.md](../foundation/architectural.guardrails.md):

| Role | Capabilities | UI Implications |
|------|--------------|-----------------|
| Analyst | CRUD own resources, view all, query any instance | Standard user views |
| Admin | CRUD any resource, force terminate | Same views + edit any + force terminate |
| Ops | All admin + cluster config, health monitoring | Separate ops section |

### 4. UX Requirements Already Specified

From [requirements.md:940-1062](../foundation/requirements.md):

- **Progress visibility:** Phases and details for snapshot creation, instance startup, algorithm execution
- **Auto-refresh intervals:** By state (pending: 5s, starting: 3s, algorithm: 2s)
- **Error message templates:** Plain language patterns for all error scenarios
- **Bulk operations:** Selection, confirmation, progress, partial failure handling
- **Empty states:** Guidance requirements
- **Timestamp display:** Relative (<24h) vs absolute (>24h), local timezone

### 5. State Machines

| Resource | States | Documented In |
|----------|--------|---------------|
| Snapshot | pending → creating → ready/failed | [requirements.md](../foundation/requirements.md), [system.architecture.design.md](../system-design/system.architecture.design.md) |
| Instance | starting → running → stopping/failed | [requirements.md](../foundation/requirements.md), [system.architecture.design.md](../system-design/system.architecture.design.md) |
| Algorithm | running → completed/failed | [requirements.md](../foundation/requirements.md) |

### 6. Business Rules

| Rule | Source |
|------|--------|
| Deletion dependency chain (Instance → Snapshot → Mapping) | [ADR-002](../process/decision.log.md) |
| Concurrency limits (per-analyst, cluster-wide) | [requirements.md](../foundation/requirements.md) |
| Lifecycle inheritance (child inherits from parent, can only be shorter) | [requirements.md](../foundation/requirements.md) |
| Immutable versions, mutable headers | [architectural.guardrails.md](../foundation/architectural.guardrails.md) |
| Implicit algorithm locking | [ADR-001](../process/decision.log.md) |

---

## Decisions Made During Assessment

### ADR-006: Authentication Mechanism (Resolved)

**Decision:** Authentication handled externally via OAuth 2.0 / OIDC with Active Directory. Headers (`X-Username`, `X-User-Role`) pre-set by upstream infrastructure.

**UI/UX Impact:**
- No login screen needed
- No session management UI
- Header displays username/role from trusted headers
- Application-level API token loaded into Jupyter context automatically

### ADR-007: Navigation Structure (Resolved)

**Decision:** Resource-centric navigation with Dashboard landing page.

<div style="font-family: system-ui, sans-serif; font-size: 13px; display: flex; gap: 16px; flex-wrap: wrap;">
  <div style="border: 1px solid #d1d5db; border-radius: 6px; overflow: hidden; min-width: 280px;">
    <div style="background: #dbeafe; padding: 8px 12px; border-bottom: 1px solid #93c5fd; font-weight: 600; color: #1d4ed8;">Primary Navigation (all users)</div>
    <div style="padding: 8px 0;">
      <div style="padding: 8px 16px; display: flex; justify-content: space-between; border-left: 3px solid #2563eb; background: #eff6ff;"><span style="font-weight: 500;">Dashboard</span> <span style="color: #6b7280; font-size: 12px;">Recent activity, quick stats</span></div>
      <div style="padding: 8px 16px; display: flex; justify-content: space-between;"><span>Mappings</span> <span style="color: #6b7280; font-size: 12px;">List, Create, Detail</span></div>
      <div style="padding: 8px 16px; display: flex; justify-content: space-between;"><span>Snapshots</span> <span style="color: #6b7280; font-size: 12px;">List, Detail</span></div>
      <div style="padding: 8px 16px; display: flex; justify-content: space-between;"><span>Instances</span> <span style="color: #6b7280; font-size: 12px;">List, Detail</span></div>
      <div style="padding: 8px 16px; display: flex; justify-content: space-between;"><span>Favorites</span> <span style="color: #6b7280; font-size: 12px;">Bookmarked resources</span></div>
      <div style="padding: 8px 16px; border-top: 1px solid #e5e7eb; margin-top: 4px;"><span style="color: #6b7280;">[User Menu]</span></div>
    </div>
  </div>
  <div style="border: 1px solid #d1d5db; border-radius: 6px; overflow: hidden; min-width: 240px;">
    <div style="background: #fef3c7; padding: 8px 12px; border-bottom: 1px solid #fcd34d; font-weight: 600; color: #b45309;">Admin Features</div>
    <div style="padding: 12px 16px; font-size: 12px; color: #6b7280;">
      <div style="padding: 4px 0;">Same views as Analyst</div>
      <div style="padding: 4px 0;">+ Edit/delete any resource</div>
      <div style="padding: 4px 0;">+ Force terminate any instance</div>
    </div>
  </div>
  <div style="border: 1px solid #d1d5db; border-radius: 6px; overflow: hidden; min-width: 260px;">
    <div style="background: #f3e8ff; padding: 8px 12px; border-bottom: 1px solid #d8b4fe; font-weight: 600; color: #7c3aed;">Ops Section (separate area)</div>
    <div style="padding: 8px 0;">
      <div style="padding: 6px 16px; display: flex; justify-content: space-between;"><span>Cluster Health</span> <span style="color: #6b7280; font-size: 12px;">Metrics, component status</span></div>
      <div style="padding: 6px 16px; display: flex; justify-content: space-between;"><span>Configuration</span> <span style="color: #6b7280; font-size: 12px;">Lifecycle, Concurrency, Schema, Maintenance</span></div>
      <div style="padding: 6px 16px; display: flex; justify-content: space-between;"><span>Export Queue</span> <span style="color: #6b7280; font-size: 12px;">Status, retry, cancel</span></div>
    </div>
  </div>
</div>

**Additional Decisions:**
- Favorites: Both dedicated page AND toggles/filters/sorting on list views
- Admin vs Analyst: Same UI, Admin has broader permissions
- Ops: Separate section with health, configuration, export queue (audit logs via external tooling)
- Force terminate: Ops-only action on Instance Detail page

### ADR-008: Generate from SQL Workflow (Resolved)

**Decision:** Comprehensive workflow for mapping creation with SQL-based schema inference.

**Key Sub-decisions:**

1. **Workflow Order:** Nodes must be defined before edges (enforced). Edge dropdowns populated by existing node labels.

2. **Type Casting:** Warn and let user fix. Show suggested SQL with CAST statement; don't auto-modify SQL.

3. **Column Order:** Require SQL fix. Primary key must be first column (nodes), from_key/to_key must be first two (edges). UI shows helpful error with fix suggestion.

4. **Schema Customization:** Editable after inference.
   - Editable: property names, property types, PK name, node label, edge type
   - Not editable: which column is PK (position 1), property order (matches SQL)
   - SQL defines source; graph schema is separate (mapping by position)

5. **SQL Change Detection:** Detect after validation.
   - Simple text diff shows "SQL modified, please validate"
   - Server compares column metadata after validation
   - If columns changed: reset customizations to defaults
   - If columns unchanged: preserve customizations

### ADR-009: Unified Mapping Diff Page (Resolved)

**Decision:** Dedicated `/compare` page for comparing any two (mapping, version) pairs.

**Key Features:**
- Supports same-mapping version diff AND cross-mapping comparison
- URL: `/compare?a={mapping_id}&av={version|latest}&b={mapping_id}&bv={version|latest}`
- Matching by label (nodes) and type name (edges) - same logic always
- Display: Summary + expandable side-by-side details
- Categories: matched+changed, matched+unchanged, only in A, only in B
- Multiple entry points (mapping detail, version list, mappings list, direct nav)

---

## Gaps: Open Questions Affecting UI/UX

### Critical (Blocks UI/UX Design)

**None** - All critical questions resolved.

| ID | Question | Impact | Status |
|----|----------|--------|--------|
| ~~OQ-025~~ | ~~Ops tools and GitOps boundary~~ | UI scope resolved by ADR-016 | **Resolved** |
| ~~OQ-021~~ | ~~Interface internationalization~~ | i18n with resource bundles (ADR-015) | **Resolved** |

### Medium (Can Proceed, May Cause Rework)

| ID | Question | Impact | Status |
|----|----------|--------|--------|
| OQ-024 | **Jupyter user-level headers** - How are user headers set for SDK requests? | Affects SDK auth documentation | Open |
| OQ-003 | **Domain configuration** - What domain hosts Control Plane and instance URLs? | Affects URL display, links | Open |
| OQ-004 | **CORS configuration** - Which origins allowed? | Affects frontend deployment | Open |

### Low (Can Defer)

| ID | Question | Impact | Status |
|----|----------|--------|--------|
| OQ-006 | Rate limiting | UI can show generic error | Defer to Phase 2 |
| OQ-007 | API versioning | Header or path based | Defer to Phase 2 |
| OQ-011 | WebSocket for algorithm progress | Polling already spec'd | Nice-to-have |
| OQ-012 | Algorithm cancellation | Not in MVP | Nice-to-have |

---

## Gaps: UX Specifications Needed

### 1. ~~"Generate from SQL" Workflow~~ (Resolved - ADR-008)

See ADR-008 in [decision.log.md](../process/decision.log.md) for complete specification.

### 2. ~~Version Diffing UX~~ (Resolved - ADR-009)

See ADR-009 in [decision.log.md](../process/decision.log.md) for complete specification.

Unified diff page at `/compare` supporting both same-mapping version comparison and cross-mapping comparison.

### 3. ~~Resource Relationships View~~ (Resolved - ADR-010)

See ADR-010 in [decision.log.md](../process/decision.log.md) for complete specification.

Full-width tree view on Mapping detail page (Resources tab), with expandable hierarchy and inline actions.

### ADR-011: Favorites UX (Resolved)

**Decision:** Star-based favorites with dedicated page and list filtering.

**Key Features:**
- Star icon (☆/★) on list rows and detail pages to toggle favorite
- Dedicated /favorites page with grouped sections (Mappings, Snapshots, Instances)
- Star toggle button on list views to filter favorites only
- Silent removal when favorited resource is deleted

### 4. ~~Combobox / Async Loading Behavior~~ (Resolved - ADR-012)

See ADR-012 in [decision.log.md](../process/decision.log.md) for complete specification.

**Summary:**
- Admin-configured allowed catalogs/schemas (constrains scope)
- Aggressive caching in Control Plane DB (24h TTL default)
- Schema Browser panel alongside SQL editor (not comboboxes)
- Instant load from cache, client-side search
- Strict validation: tables not in cache = error

### 5. ~~Responsive Behavior~~ (Resolved - ADR-013)

See ADR-013 in [decision.log.md](../process/decision.log.md) for complete specification.

**Summary:**
- Desktop only (no tablet/mobile)
- Minimum width: 1024px
- Stack vertically on narrow screens (1024-1279px)
- Side-by-side layouts at ≥1280px

### 6. ~~Accessibility Requirements~~ (Resolved - ADR-014)

See ADR-014 in [decision.log.md](../process/decision.log.md) for complete specification.

**Summary:**
- WCAG 2.1 AA compliance target
- Full keyboard navigation support
- Screen reader support not required (basic semantic HTML sufficient)
- WCAG AA color contrast (4.5:1 text, 3:1 UI)
- Visible focus indicators on all interactive elements
- No modals/dialogs/overlays (inline and page-based UI only)

---

## Questions UI/UX Designers Will Ask

Based on the specifications, designers will likely need clarity on:

1. **"What's the primary entry point after login?"** → Dashboard (decided)

2. **"How do users discover mappings they didn't create?"** → All resources visible; need to decide if there's "popular" or "recent by others" views

3. **"What happens when clicking a locked instance?"** → Can view, can query, cannot run algorithms; shows lock holder info

4. **"How prominent should lifecycle warnings be?"** → TTL expiring soon, inactivity timeout approaching - need to specify

5. **"Should there be shortcut flows?"** → e.g., "Create Instance" button directly on Snapshot detail page

6. **"What's the empty state for a new user?"** → Onboarding guidance, sample mapping, or just empty list with CTA

7. **"How are errors from external systems displayed?"** → Starburst errors, GCS errors - need user-friendly messaging

---

## Recommended Actions

### Before Starting UI/UX

1. **Resolve OQ-025 (Ops/GitOps boundary)** - Defines scope of Ops section
2. **Decide OQ-021 (Interface i18n)** - Affects all copy and string management

### During UI/UX Design

3. **Specify "Generate from SQL" workflow** - Critical for mapping creation UX
4. **Define version diffing display** - Needed for mapping detail page
5. **Define resource relationships visualization** - Needed for navigation/orientation
6. **Specify accessibility baseline** - Affects all component design

### Can Defer

7. Responsive behavior details (if desktop-first)
8. Advanced filtering/search capabilities
9. Notification preferences

---

## Related Documents

- [requirements.md](../foundation/requirements.md) - Functional requirements and UX requirements section
- [architectural.guardrails.md](../foundation/architectural.guardrails.md) - Hard constraints
- [decision.log.md](../process/decision.log.md) - ADRs and open questions
- [data-pipeline.reference.md](../reference/data-pipeline.reference.md) - Technical context for mapping creation

---

## Change History

| Date | Change |
|------|--------|
| 2025-12-11 | Initial assessment created |
| 2025-12-11 | Added ADR-006 (Authentication) and ADR-007 (Navigation) decisions |
| 2025-12-11 | Added ADR-008 (Generate from SQL Workflow) - 5 sub-decisions resolved |
| 2025-12-11 | Added ADR-009 (Unified Mapping Diff Page) |
| 2025-12-11 | Added ADR-010 (Resource Relationships View) |
| 2025-12-11 | Added ADR-011 (Favorites UX) |
| 2025-12-11 | Added ADR-012 (Schema Browser and Metadata Caching) |
| 2025-12-11 | Added ADR-013 (Responsive Behavior) |
| 2025-12-11 | Added ADR-014 (Accessibility Requirements) - All gaps resolved |
| 2025-12-12 | Added ADR-015 (Interface Internationalization) - resolved OQ-021 |
| 2025-12-12 | Added ADR-016 (Ops Section UI Scope) - clarified OQ-025; verdict updated to 100% ready |
