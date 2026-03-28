# UX Design (Tier 4)

> **DEPRECATED** - This documentation is no longer maintained.
>
> The Graph OLAP Platform no longer includes a web interface. All user interaction
> is now through the Jupyter SDK. These documents are retained for historical reference.
>
> See [jupyter-sdk.design.md](../component-designs/jupyter-sdk.design.md) for the current user interface design.

User experience design for the HTMX web interface.

## Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [ux.readiness-assessment.md](./ux.readiness-assessment.md) | Assessment of product specs for UI/UX readiness, gaps, decisions | Complete |
| [ux.flows.md](./ux.flows.md) | User journeys, page inventory, interaction sequences, HTML mockups | Complete |
| [ux.components.spec.md](./ux.components.spec.md) | UI component specifications, states, accessibility, HTML mockups | Complete |
| [ux.copy.spec.md](./ux.copy.spec.md) | i18n strategy, error messages, labels, help text, notifications | Complete |
| [ux.review-findings.md](./ux.review-findings.md) | Gap analysis, consistency issues, improvement recommendations | Complete |
| `ux.wireframes.md` | Visual design system (colors, typography, spacing) | Deferred |

## Reading Order

1. **Start here:** [ux.readiness-assessment.md](./ux.readiness-assessment.md) - Understand what's decided, what's open
2. [ux.flows.md](./ux.flows.md) - Page inventory, navigation, user journeys with mockups
3. [ux.components.spec.md](./ux.components.spec.md) - Component behavior and accessibility
4. [ux.copy.spec.md](./ux.copy.spec.md) - All user-facing text, i18n patterns
5. [process/decision.log.md](../process/decision.log.md) - ADR-006 through ADR-017 (UX decisions)

## Prerequisites

- [foundation/requirements.md](../foundation/requirements.md) - UX requirements section (lines 974-1095)
- [system-design/api.common.spec.md](../system-design/api.common.spec.md) - Error codes reference
- [reference/data-pipeline.reference.md](../reference/data-pipeline.reference.md) - Technical context for mapping creation UI

## Key ADRs (in decision.log.md)

| ADR | Topic |
|-----|-------|
| ADR-006 | Authentication (external OIDC, no login screen) |
| ADR-007 | Navigation structure (resource-centric, Ops section) |
| ADR-008 | Generate from SQL workflow (5 sub-decisions) |
| ADR-009 | Unified mapping diff page |
| ADR-010 | Resource relationships view (tree on Mapping detail) |
| ADR-011 | Favorites UX (star toggle, dedicated page) |
| ADR-012 | Schema Browser and metadata caching |
| ADR-013 | Responsive behavior (1024px min, 1280px side-by-side) |
| ADR-014 | Accessibility (WCAG 2.1 AA, no modals) |
| ADR-015 | Internationalization (en + zh-CN, resource bundles) |
| ADR-016 | Ops section UI scope |
| ADR-017 | Maintenance mode behavior |
