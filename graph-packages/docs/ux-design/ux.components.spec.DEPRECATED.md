# UI Components Specification

> **DEPRECATED** - This document is no longer maintained.
>
> The Graph OLAP Platform no longer includes a web interface. All user interaction
> is now through the Jupyter SDK. This document is retained for historical reference.
>
> See [jupyter-sdk.design.md](../component-designs/jupyter-sdk.design.md) for the current user interface design.

## Overview

Component specifications for the Graph OLAP Platform web interface. Defines behavior, states, interactions, and accessibility requirements.

## Prerequisites

- [ux.flows.md](./ux.flows.md) - User flows and page layouts
- [decision.log.md](../process/decision.log.md) - ADR-013 (Responsive), ADR-014 (Accessibility)
- [requirements.md](../foundation/requirements.md) - UX requirements (lines 940-1062)

---

## Component Inventory

| Category | Components |
|----------|------------|
| Layout | Page Shell, List Layout, Detail Layout, Form Layout |
| Data Display | Resource Card, Status Badge, Progress Indicator, Timestamp, Data Table, Tree View, Diff Viewer |
| Interactive | Button, Text Input, Textarea, Select, Checkbox, SQL Editor, Star Toggle, Filter Chip, Search, Dropdown Menu |
| Feedback | Toast Notification, Empty State, Loading State, Error State, Inline Validation |

---

## Layout Components

### Page Shell

The consistent wrapper for all pages.

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 900px;">
  <div style="display: flex; min-height: 400px;">
    <div style="width: 220px; background: #1f2937; padding: 16px 0; color: white;">
      <div style="padding: 12px 20px; font-weight: 600; font-size: 14px; border-bottom: 1px solid #374151; margin-bottom: 8px;">
        Graph OLAP
      </div>
      <div style="padding: 10px 20px; background: #374151; border-left: 3px solid #3b82f6;">Dashboard</div>
      <div style="padding: 10px 20px; color: #9ca3af;">Mappings</div>
      <div style="padding: 10px 20px; color: #9ca3af;">Snapshots</div>
      <div style="padding: 10px 20px; color: #9ca3af;">Instances</div>
      <div style="padding: 10px 20px; color: #9ca3af;">Favorites</div>
      <div style="margin-top: auto; padding: 10px 20px; border-top: 1px solid #374151; color: #9ca3af; position: absolute; bottom: 16px;">
        alice.smith
      </div>
    </div>
    <div style="flex: 1; background: #f9fafb;">
      <div style="background: white; padding: 16px 24px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 18px; font-weight: 600; color: #1f2937;">Page Title</div>
        <div style="display: flex; gap: 12px; align-items: center;">
          <span style="color: #6b7280; font-size: 13px;">⚙️</span>
        </div>
      </div>
      <div style="padding: 24px; color: #6b7280;">
        [Page Content Area]
      </div>
    </div>
  </div>
</div>

**Structure:**
- **Sidebar** (220px fixed) - Navigation, user menu
- **Header** (56px fixed) - Page title, actions, settings
- **Content** (fluid) - Main page content with 24px padding

**Responsive (ADR-013):**
- Min width: 1024px
- Sidebar collapses to icons at < 1280px

---

### List Layout

Standard layout for resource lists (Mappings, Snapshots, Instances).

**Sections:**
1. **Header** - Title, description, primary action button
2. **Filters** - Search, dropdowns, filter chips
3. **Table** - Sortable columns, row actions
4. **Pagination** - Page info, prev/next buttons

---

### Detail Layout

Standard layout for resource detail pages. Uses single-page layout with section headings (no tabs).

**Sections:**
1. **Header** - Back link, title, favorite toggle, status badge, actions
2. **Metadata** - Owner, dates, key stats
3. **Content Sections** - Multiple sections with `<h2>` headings, separated by borders

---

### Form Layout

Standard layout for create/edit forms (Create Mapping, Edit Snapshot).

**Structure:**
1. **Header** - Form title, optional description
2. **Form Body** - Fields grouped in logical sections
3. **Actions** - Primary and secondary buttons, right-aligned

**Field Layout:**

| Property | Value |
|----------|-------|
| Label placement | Top-aligned (above input) |
| Required indicator | Red asterisk (*) after label |
| Help text | Below input, gray, 12px |
| Error text | Below input, red, replaces help text |
| Field spacing | 24px between fields |
| Section spacing | 32px between sections |

**Width Constraints:**
- Form max-width: 600px (single column)
- Full-width inputs within form container
- Form pages: centered in viewport

**Form Sections:**

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 13px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 600px;">
  <div style="padding: 20px;">
    <div style="font-size: 15px; font-weight: 600; color: #1f2937; margin-bottom: 16px;">Section Title</div>
    <div style="margin-bottom: 16px;">
      <div style="font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 4px;">Field Label <span style="color: #dc2626;">*</span></div>
      <div style="padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; color: #6b7280;">Input value</div>
      <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">Help text explaining the field</div>
    </div>
    <div>
      <div style="font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 4px;">Another Field</div>
      <div style="padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; color: #6b7280;">Optional input</div>
    </div>
  </div>
</div>

---

## Data Display Components

### Status Badge

Visual indicator for resource status. **This is the authoritative source for status colors** - other documents should reference this section.

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; display: flex; gap: 12px; flex-wrap: wrap; padding: 16px;">
  <span style="background: #dcfce7; color: #16a34a; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 500;">Ready</span>
  <span style="background: #dcfce7; color: #16a34a; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 500;">Running</span>
  <span style="background: #f3f4f6; color: #6b7280; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 500;">Pending</span>
  <span style="background: #dbeafe; color: #2563eb; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 500;">Creating</span>
  <span style="background: #dbeafe; color: #2563eb; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 500;">Starting</span>
  <span style="background: #fef3c7; color: #d97706; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 500;">Stopping</span>
  <span style="background: #fee2e2; color: #dc2626; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 500;">Failed</span>
</div>

**Status Color Palette:**

Colors follow semantic UX conventions: green (success/active), blue (in-progress), yellow (caution), red (error), gray (neutral/inactive).

| Category | Background | Text | Statuses |
|----------|------------|------|----------|
| Success | `#dcfce7` | `#16a34a` | Ready, Running, Completed, Active |
| In-Progress | `#dbeafe` | `#2563eb` | Creating, Starting |
| Caution | `#fef3c7` | `#d97706` | Stopping |
| Error | `#fee2e2` | `#dc2626` | Failed |
| Neutral | `#f3f4f6` | `#6b7280` | Pending, Queued, Stopped, Expired, Archived, Draft |

**Status-to-Color Mapping:**

| Status | Color | Rationale |
|--------|-------|-----------|
| Ready | Green | Success - resource is available |
| Running | Green | Active - instance is operational |
| Completed | Green | Success - algorithm finished |
| Active | Green | Resource is in use |
| Creating | Blue | In-progress - export running |
| Starting | Blue | In-progress - instance booting |
| Stopping | Yellow | Caution - instance winding down |
| Failed | Red | Error - operation failed |
| Pending/Queued | Gray | Neutral - waiting to start |
| Stopped | Gray | Neutral - terminal state |
| Expired | Gray | Neutral - lifecycle ended |
| Archived | Gray | Neutral - no longer active |
| Draft | Gray | Neutral - not published |

**Accessibility:** All color combinations meet WCAG AA 4.5:1 contrast ratio

---

### Progress Indicator

Shows progress for async operations.

**Determinate (known progress):**

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px; max-width: 400px;">
  <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
    <span style="font-weight: 500;">Exporting nodes</span>
    <span style="color: #6b7280;">2 of 3</span>
  </div>
  <div style="background: #e5e7eb; border-radius: 9999px; height: 8px; overflow: hidden;">
    <div style="background: #2563eb; height: 100%; width: 66%; border-radius: 9999px;"></div>
  </div>
</div>

**Indeterminate (unknown progress):**

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px; max-width: 400px;">
  <div style="display: flex; align-items: center; gap: 12px;">
    <div style="width: 20px; height: 20px; border: 2px solid #e5e7eb; border-top-color: #2563eb; border-radius: 50%;"></div>
    <span style="color: #6b7280;">Creating pod...</span>
  </div>
</div>

**Step Progress:**

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px; max-width: 500px;">
  <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px;">
    <div style="display: flex; align-items: center; gap: 8px;">
      <span style="width: 24px; height: 24px; background: #16a34a; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px;">✓</span>
      <span style="font-size: 12px; color: #16a34a;">Customer</span>
    </div>
    <div style="flex: 1; height: 2px; background: #16a34a;"></div>
    <div style="display: flex; align-items: center; gap: 8px;">
      <span style="width: 24px; height: 24px; background: #16a34a; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px;">✓</span>
      <span style="font-size: 12px; color: #16a34a;">Account</span>
    </div>
    <div style="flex: 1; height: 2px; background: #e5e7eb;"></div>
    <div style="display: flex; align-items: center; gap: 8px;">
      <span style="width: 24px; height: 24px; background: #2563eb; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px;">⏳</span>
      <span style="font-size: 12px; color: #2563eb; font-weight: 500;">Transaction</span>
    </div>
  </div>
</div>

---

### Timestamp

Display format based on recency (from requirements.md). **For i18n text strings, see [ux.copy.spec.md](./ux.copy.spec.md#timestamps--durations)** (authoritative source for copy).

| Age | Format Rule | i18n Key |
|-----|-------------|----------|
| < 1 minute | Static text | `time.justNow` |
| < 1 hour | Relative minutes | `time.minutesAgo` / `time.minutesAgo_plural` |
| < 24 hours | Relative hours | `time.hoursAgo` / `time.hoursAgo_plural` |
| < 7 days | Relative days | `time.daysAgo` / `time.daysAgo_plural` |
| >= 7 days | Absolute date | Locale-formatted date (e.g., "Jan 15, 2025" / "2025年1月15日") |

**Hover tooltip:** Show full timestamp with timezone in locale format.

**Implementation notes:**
- Use singular form when count = 1, plural otherwise
- Chinese does not distinguish singular/plural (same string for both)
- Use `Intl.RelativeTimeFormat` for relative times
- Use `Intl.DateTimeFormat` for absolute dates

---

### Breadcrumb

Navigation path shown on all detail/subpages. Not shown on list pages.

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px;">
  <div style="display: flex; align-items: center; gap: 8px; color: #6b7280;">
    <a href="#" style="color: #2563eb; text-decoration: none;">Mappings</a>
    <span>/</span>
    <a href="#" style="color: #2563eb; text-decoration: none;">Customer Graph</a>
    <span>/</span>
    <span style="color: #374151;">Version 3</span>
  </div>
</div>

**Structure:**
- Links for all ancestor pages
- Current page shown as plain text (not linked)
- Separator: `/` character

**Breadcrumb Paths:**

| Page | Breadcrumb |
|------|------------|
| Mapping Detail | Mappings / {mapping name} |
| Mapping Version | Mappings / {mapping name} / Version {n} |
| Compare Versions | Mappings / {mapping name} / Compare |
| Snapshot Detail | Snapshots / {snapshot name} |
| Instance Detail | Instances / {instance name} |
| Create Mapping | Mappings / Create |
| Edit Mapping | Mappings / {mapping name} / Edit |

**Behavior:**
- Each link navigates to that page
- Current page (last item) is not clickable
- Truncate long names with ellipsis (max 30 chars per segment)

---

### Data Table

Sortable, filterable table with row actions.

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; max-width: 700px;">
  <table style="width: 100%; border-collapse: collapse;">
    <thead>
      <tr style="background: #f9fafb;">
        <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px; cursor: pointer;">
          NAME <span style="color: #9ca3af;">↕</span>
        </th>
        <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #374151; font-size: 11px; cursor: pointer;">
          OWNER <span style="color: #2563eb;">↑</span>
        </th>
        <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">STATUS</th>
        <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;"></th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-top: 1px solid #f3f4f6;">
        <td style="padding: 12px 16px;"><strong style="color: #2563eb; cursor: pointer;">Customer Graph</strong></td>
        <td style="padding: 12px 16px; color: #6b7280;">alice.smith</td>
        <td style="padding: 12px 16px;"><span style="background: #dcfce7; color: #16a34a; padding: 2px 8px; border-radius: 9999px; font-size: 11px;">Ready</span></td>
        <td style="padding: 12px 16px;"><button style="background: none; border: none; color: #6b7280; cursor: pointer; font-size: 16px;">⋮</button></td>
      </tr>
      <tr style="border-top: 1px solid #f3f4f6; background: #fafafa;">
        <td style="padding: 12px 16px;"><strong style="color: #2563eb; cursor: pointer;">Transaction Network</strong></td>
        <td style="padding: 12px 16px; color: #6b7280;">bob.jones</td>
        <td style="padding: 12px 16px;"><span style="background: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 9999px; font-size: 11px;">Pending</span></td>
        <td style="padding: 12px 16px;"><button style="background: none; border: none; color: #6b7280; cursor: pointer; font-size: 16px;">⋮</button></td>
      </tr>
    </tbody>
  </table>
</div>

**Features:**
- **Sortable columns** - Click header to sort, show direction indicator
- **Row hover** - Subtle background change (`#fafafa`)
- **Row actions** - Overflow menu (⋮) with contextual actions
- **Clickable name** - Links to detail page
- **Keyboard navigation** - Arrow keys between rows, Enter to select

#### Bulk Selection Mode

When bulk operations are available, tables include selection checkboxes:

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; max-width: 700px;">
  <div style="background: #eff6ff; padding: 8px 16px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #bfdbfe;">
    <span style="font-weight: 500; color: #1d4ed8;">3 selected</span>
    <button style="padding: 4px 12px; background: #dc2626; color: white; border: none; border-radius: 4px; font-size: 11px; cursor: pointer;">Delete Selected</button>
    <button style="padding: 4px 12px; background: white; color: #374151; border: 1px solid #d1d5db; border-radius: 4px; font-size: 11px; cursor: pointer;">Cancel</button>
  </div>
  <table style="width: 100%; border-collapse: collapse;">
    <thead>
      <tr style="background: #f9fafb;">
        <th style="width: 40px; padding: 12px 16px;">
          <input type="checkbox" style="cursor: pointer;" checked>
        </th>
        <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">NAME</th>
        <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">STATUS</th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-top: 1px solid #f3f4f6; background: #eff6ff;">
        <td style="padding: 12px 16px;"><input type="checkbox" checked></td>
        <td style="padding: 12px 16px;"><strong>Customer Graph</strong></td>
        <td style="padding: 12px 16px;"><span style="background: #dcfce7; color: #16a34a; padding: 2px 8px; border-radius: 9999px; font-size: 11px;">Ready</span></td>
      </tr>
      <tr style="border-top: 1px solid #f3f4f6; background: #eff6ff;">
        <td style="padding: 12px 16px;"><input type="checkbox" checked></td>
        <td style="padding: 12px 16px;"><strong>Transaction Network</strong></td>
        <td style="padding: 12px 16px;"><span style="background: #dcfce7; color: #16a34a; padding: 2px 8px; border-radius: 9999px; font-size: 11px;">Ready</span></td>
      </tr>
      <tr style="border-top: 1px solid #f3f4f6; background: #eff6ff;">
        <td style="padding: 12px 16px;"><input type="checkbox" checked></td>
        <td style="padding: 12px 16px;"><strong>Fraud Detection</strong></td>
        <td style="padding: 12px 16px;"><span style="background: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 9999px; font-size: 11px;">Pending</span></td>
      </tr>
      <tr style="border-top: 1px solid #f3f4f6;">
        <td style="padding: 12px 16px;"><input type="checkbox"></td>
        <td style="padding: 12px 16px;"><strong>Risk Analysis</strong></td>
        <td style="padding: 12px 16px;"><span style="background: #dcfce7; color: #16a34a; padding: 2px 8px; border-radius: 9999px; font-size: 11px;">Ready</span></td>
      </tr>
    </tbody>
  </table>
</div>

**Bulk Selection Behavior:**

| Element | Behavior |
|---------|----------|
| Header checkbox | Unchecked: select all visible. Checked: deselect all. Indeterminate (-): some selected |
| Row checkbox | Toggle individual selection. Selected rows get highlight background |
| Selection toolbar | Appears when 1+ items selected. Shows count and available bulk actions |
| Cancel button | Clears all selections and hides toolbar |

**Bulk Action Confirmation:**

Destructive bulk actions (delete, terminate) require inline confirmation:

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #fecaca; border-radius: 8px; overflow: hidden; max-width: 500px; background: #fef2f2;">
  <div style="padding: 12px 16px;">
    <p style="margin: 0 0 8px 0; color: #991b1b; font-weight: 500;">Delete 3 snapshots?</p>
    <p style="margin: 0 0 12px 0; color: #7f1d1d; font-size: 11px;">This will permanently delete the selected snapshots. Any dependent instances will also be terminated.</p>
    <div style="display: flex; gap: 8px;">
      <button style="padding: 6px 16px; background: #dc2626; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer;">Delete 3 Snapshots</button>
      <button style="padding: 6px 16px; background: white; color: #374151; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; cursor: pointer;">Cancel</button>
    </div>
  </div>
</div>

**Partial Failure Handling:**

When some items in a bulk operation fail:

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #fecaca; border-radius: 8px; overflow: hidden; max-width: 500px;">
  <div style="background: #fef2f2; padding: 12px 16px; border-bottom: 1px solid #fecaca;">
    <p style="margin: 0; color: #991b1b; font-weight: 500;">2 of 3 items deleted. 1 failed.</p>
  </div>
  <div style="padding: 12px 16px; background: white;">
    <div style="display: flex; align-items: center; gap: 8px; padding: 4px 0;">
      <span style="color: #16a34a;">✓</span>
      <span>Customer Graph</span>
      <span style="color: #6b7280; font-size: 11px;">Deleted</span>
    </div>
    <div style="display: flex; align-items: center; gap: 8px; padding: 4px 0;">
      <span style="color: #16a34a;">✓</span>
      <span>Transaction Network</span>
      <span style="color: #6b7280; font-size: 11px;">Deleted</span>
    </div>
    <div style="display: flex; align-items: center; gap: 8px; padding: 4px 0;">
      <span style="color: #dc2626;">✗</span>
      <span>Fraud Detection</span>
      <span style="color: #dc2626; font-size: 11px;">Has active instances</span>
    </div>
  </div>
  <div style="padding: 8px 16px; background: #f9fafb; border-top: 1px solid #e5e7eb;">
    <button style="padding: 4px 12px; background: white; color: #374151; border: 1px solid #d1d5db; border-radius: 4px; font-size: 11px; cursor: pointer;">Dismiss</button>
  </div>
</div>

**Keyboard Shortcuts:**

| Key | Action |
|-----|--------|
| Space | Toggle selection on focused row |
| Shift+Click | Select range from last selected to clicked |
| Ctrl/Cmd+A | Select all visible rows |
| Escape | Clear selection |

---

### Resource Tree View

Hierarchical view of related resources (ADR-010).

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; max-width: 500px;">
  <div style="padding: 16px;">
    <div style="display: flex; align-items: center; gap: 8px; padding: 8px 0;">
      <span style="color: #6b7280; cursor: pointer;">▼</span>
      <span style="font-weight: 500;">Customer Graph</span>
      <span style="background: #dbeafe; color: #2563eb; padding: 1px 6px; border-radius: 4px; font-size: 10px;">v3</span>
    </div>
    <div style="margin-left: 24px; border-left: 1px solid #e5e7eb; padding-left: 16px;">
      <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0;">
        <span style="color: #6b7280; cursor: pointer;">▼</span>
        <span>📸 January 2025 Snapshot</span>
        <span style="background: #dcfce7; color: #16a34a; padding: 1px 6px; border-radius: 4px; font-size: 10px;">Ready</span>
      </div>
      <div style="margin-left: 24px; border-left: 1px solid #e5e7eb; padding-left: 16px;">
        <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0;">
          <span style="color: transparent;">▼</span>
          <span>⚡ Analysis-001</span>
          <span style="background: #dbeafe; color: #2563eb; padding: 1px 6px; border-radius: 4px; font-size: 10px;">Running</span>
          <button style="margin-left: auto; padding: 2px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 10px; background: white; cursor: pointer;">Open</button>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0;">
          <span style="color: transparent;">▼</span>
          <span>⚡ Analysis-002</span>
          <span style="background: #f3e8ff; color: #9333ea; padding: 1px 6px; border-radius: 4px; font-size: 10px;">Stopping</span>
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0;">
        <span style="color: #6b7280; cursor: pointer;">▶</span>
        <span>📸 December 2024 Snapshot</span>
        <span style="background: #dcfce7; color: #16a34a; padding: 1px 6px; border-radius: 4px; font-size: 10px;">Ready</span>
        <span style="color: #6b7280; font-size: 11px; margin-left: 4px;">(2 instances)</span>
      </div>
    </div>
  </div>
</div>

**Interactions:**
- **Expand/collapse** - Click arrow to toggle children
- **Inline actions** - Hover to show "Open" button
- **Count badge** - Show child count when collapsed

---

### Diff Viewer

Side-by-side comparison for mapping versions (ADR-009).

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; max-width: 700px;">
  <div style="display: flex; border-bottom: 1px solid #e5e7eb;">
    <div style="flex: 1; padding: 12px 16px; background: #fef2f2; border-right: 1px solid #e5e7eb;">
      <div style="font-weight: 500; color: #dc2626;">v2 (Previous)</div>
    </div>
    <div style="flex: 1; padding: 12px 16px; background: #f0fdf4;">
      <div style="font-weight: 500; color: #16a34a;">v3 (Current)</div>
    </div>
  </div>
  <div style="display: flex;">
    <div style="flex: 1; padding: 12px 16px; border-right: 1px solid #e5e7eb; font-family: monospace; font-size: 11px;">
      <div style="padding: 2px 0;">customer_id: STRING</div>
      <div style="padding: 2px 0; background: #fee2e2; margin: 0 -16px; padding-left: 16px;">- name: STRING</div>
      <div style="padding: 2px 0;">email: STRING</div>
    </div>
    <div style="flex: 1; padding: 12px 16px; font-family: monospace; font-size: 11px;">
      <div style="padding: 2px 0;">customer_id: STRING</div>
      <div style="padding: 2px 0; background: #dcfce7; margin: 0 -16px; padding-left: 16px;">+ full_name: STRING</div>
      <div style="padding: 2px 0;">email: STRING</div>
    </div>
  </div>
</div>

**Colors:**
- **Removed** - Red background (`#fee2e2`)
- **Added** - Green background (`#dcfce7`)
- **Changed** - Yellow background (`#fef3c7`)
- **Unchanged** - No background

---

## Interactive Components

### Button

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center;">
  <button style="background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer;">Primary</button>
  <button style="background: white; color: #374151; border: 1px solid #d1d5db; padding: 10px 20px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer;">Secondary</button>
  <button style="background: #dc2626; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer;">Danger</button>
  <button style="background: white; color: #2563eb; border: none; padding: 10px 20px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; text-decoration: underline;">Link</button>
  <button style="background: #e5e7eb; color: #9ca3af; border: none; padding: 10px 20px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: not-allowed;">Disabled</button>
</div>

**Variants:**

| Variant | Use Case |
|---------|----------|
| Primary | Main action (Create, Save, Submit) |
| Secondary | Alternative action (Cancel, Back) |
| Danger | Destructive action (Delete, Terminate) |
| Link | Navigation, low-emphasis action |

**States:**
- **Default** - Base appearance
- **Hover** - Darken background 10%
- **Focus** - 2px ring outline (keyboard)
- **Active** - Darken background 20%
- **Disabled** - Gray, cursor not-allowed

**Accessibility:**
- Visible focus ring (2px, offset 2px)
- Minimum touch target: 44x44px

---

### Copy to Clipboard

Used for copying endpoint URLs, SQL queries, connection strings.

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px; display: flex; flex-direction: column; gap: 16px; max-width: 400px;">
  <!-- Inline with text -->
  <div>
    <div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">SDK Endpoint</div>
    <div style="display: flex; align-items: center; gap: 8px; background: #f3f4f6; padding: 8px 12px; border-radius: 6px; font-family: monospace; font-size: 12px;">
      <span style="flex: 1; overflow: hidden; text-overflow: ellipsis;">https://instance-abc123.ryugraph.internal</span>
      <button style="background: white; border: 1px solid #d1d5db; padding: 4px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; white-space: nowrap;">Copy</button>
    </div>
  </div>
  <!-- After copy (success state) -->
  <div>
    <div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">After clicking Copy</div>
    <div style="display: flex; align-items: center; gap: 8px; background: #f3f4f6; padding: 8px 12px; border-radius: 6px; font-family: monospace; font-size: 12px;">
      <span style="flex: 1; overflow: hidden; text-overflow: ellipsis;">https://instance-abc123.ryugraph.internal</span>
      <button style="background: #dcfce7; border: 1px solid #16a34a; color: #16a34a; padding: 4px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; white-space: nowrap;">Copied!</button>
    </div>
  </div>
</div>

**Behavior:**

| State | Appearance | Duration |
|-------|------------|----------|
| Default | "Copy" button | - |
| Success | "Copied!" with green background | 2 seconds, then revert |
| Failure | "Failed" with red background | 2 seconds, then revert |

**Usage Locations:**
- Instance Detail: SDK Endpoint URL
- Mapping Detail: SQL queries in node/edge definitions
- Any monospace/code display

**Accessibility:**
- Button announces "Copy to clipboard" to screen readers
- Success/failure announced via `aria-live="polite"`

---

### Text Input

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px; max-width: 300px;">
  <div style="margin-bottom: 16px;">
    <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">Label</label>
    <input type="text" placeholder="Placeholder text" style="width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; box-sizing: border-box;">
    <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">Helper text</div>
  </div>
  <div style="margin-bottom: 16px;">
    <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">With Error</label>
    <input type="text" value="Invalid value" style="width: 100%; padding: 10px 12px; border: 2px solid #dc2626; border-radius: 6px; font-size: 14px; box-sizing: border-box; background: #fef2f2;">
    <div style="font-size: 11px; color: #dc2626; margin-top: 4px;">This field is required</div>
  </div>
  <div>
    <label style="display: block; font-size: 13px; font-weight: 500; color: #9ca3af; margin-bottom: 6px;">Disabled</label>
    <input type="text" value="Read only" disabled style="width: 100%; padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 14px; box-sizing: border-box; background: #f9fafb; color: #9ca3af;">
  </div>
</div>

**States:**
- **Default** - Gray border (`#d1d5db`)
- **Focus** - Blue border (`#2563eb`), ring outline
- **Error** - Red border (`#dc2626`), red helper text
- **Disabled** - Light gray background, muted text

---

### Star Toggle (Favorites)

Per ADR-011.

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px; display: flex; gap: 24px; align-items: center;">
  <div style="display: flex; align-items: center; gap: 8px;">
    <span style="font-size: 20px; color: #d1d5db; cursor: pointer;" title="Add to favorites">☆</span>
    <span style="color: #6b7280;">Not favorited</span>
  </div>
  <div style="display: flex; align-items: center; gap: 8px;">
    <span style="font-size: 20px; color: #eab308; cursor: pointer;" title="Remove from favorites">★</span>
    <span style="color: #6b7280;">Favorited</span>
  </div>
</div>

**Interactions:**
- **Click** - Toggle favorite state
- **Hover** - Show tooltip ("Add to favorites" / "Remove from favorites")
- **Animation** - Brief scale animation on toggle

**Accessibility:**
- `role="button"`, `aria-pressed="true/false"`
- Keyboard: Space/Enter to toggle

---

### Filter Chip

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px; display: flex; gap: 8px; flex-wrap: wrap;">
  <span style="background: white; border: 1px solid #d1d5db; padding: 6px 12px; border-radius: 9999px; font-size: 12px; cursor: pointer;">All</span>
  <span style="background: #2563eb; color: white; border: 1px solid #2563eb; padding: 6px 12px; border-radius: 9999px; font-size: 12px; cursor: pointer;">My Mappings</span>
  <span style="background: white; border: 1px solid #d1d5db; padding: 6px 12px; border-radius: 9999px; font-size: 12px; cursor: pointer;">⭐ Favorites</span>
  <span style="background: #f0fdf4; border: 1px solid #16a34a; color: #16a34a; padding: 6px 12px; border-radius: 9999px; font-size: 12px; cursor: pointer;">Ready ✕</span>
</div>

**States:**
- **Unselected** - White background, gray border
- **Selected** - Blue/colored background
- **Removable** - Show × icon, click to remove
- **Hover** - Darken slightly

---

### SQL Editor with Schema Browser

Based on ADR-012.

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 800px;">
  <div style="display: flex;">
    <div style="flex: 1; border-right: 1px solid #e5e7eb;">
      <div style="background: #f9fafb; padding: 8px 12px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: 500; font-size: 13px;">SQL Query</span>
        <button style="background: #2563eb; color: white; border: none; padding: 6px 16px; border-radius: 4px; font-size: 12px; cursor: pointer;">Validate</button>
      </div>
      <div style="padding: 12px; font-family: monospace; font-size: 13px; min-height: 150px; background: #1f2937; color: #e5e7eb;">
        <div><span style="color: #93c5fd;">SELECT</span></div>
        <div style="padding-left: 16px;">customer_id,</div>
        <div style="padding-left: 16px;">name,</div>
        <div style="padding-left: 16px;">email</div>
        <div><span style="color: #93c5fd;">FROM</span> hive.analytics.customers</div>
        <div><span style="color: #93c5fd;">WHERE</span> status = <span style="color: #86efac;">'active'</span></div>
      </div>
    </div>
    <div style="width: 240px; background: #fafafa;">
      <div style="background: #f3f4f6; padding: 8px 12px; border-bottom: 1px solid #e5e7eb;">
        <input type="text" placeholder="Search tables..." style="width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; box-sizing: border-box;">
      </div>
      <div style="padding: 8px 0; max-height: 200px; overflow-y: auto;">
        <div style="padding: 4px 12px;">
          <div style="color: #6b7280; font-size: 11px; font-weight: 500; padding: 4px 0;">hive.analytics</div>
          <div style="padding: 4px 0 4px 12px; cursor: pointer; font-size: 12px;">📋 customers</div>
          <div style="padding: 4px 0 4px 12px; cursor: pointer; font-size: 12px;">📋 accounts</div>
          <div style="padding: 4px 0 4px 12px; cursor: pointer; font-size: 12px;">📋 transactions</div>
        </div>
      </div>
    </div>
  </div>
</div>

**Schema Browser:**
- Shows allowed catalogs/schemas (admin-configured)
- Click table to insert name at cursor
- Expand table to see columns
- Search filters visible tables
- Loaded from cache (instant)

---

### Dropdown Menu

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px; position: relative; display: inline-block;">
  <button style="background: white; border: 1px solid #d1d5db; padding: 8px 12px; border-radius: 6px; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 8px;">
    Actions <span style="color: #6b7280;">▼</span>
  </button>
  <div style="position: absolute; top: 100%; left: 0; margin-top: 4px; background: white; border: 1px solid #d1d5db; border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-width: 160px; z-index: 10;">
    <div style="padding: 6px 0;">
      <div style="padding: 8px 16px; cursor: pointer; font-size: 13px;">Edit</div>
      <div style="padding: 8px 16px; cursor: pointer; font-size: 13px; background: #f3f4f6;">Duplicate</div>
      <div style="padding: 8px 16px; cursor: pointer; font-size: 13px;">Create Snapshot</div>
      <div style="border-top: 1px solid #e5e7eb; margin: 6px 0;"></div>
      <div style="padding: 8px 16px; cursor: pointer; font-size: 13px; color: #dc2626;">Delete</div>
    </div>
  </div>
</div>

**Behavior:**
- **Open** - Click trigger button
- **Close** - Click outside, press Escape, or select item
- **Navigation** - Arrow keys, Enter to select
- **Danger items** - Red text, separated by divider

---

## Feedback Components

### Toast Notification

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; padding: 16px; display: flex; flex-direction: column; gap: 12px; max-width: 400px;">
  <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 12px 16px; display: flex; align-items: flex-start; gap: 12px;">
    <span style="color: #16a34a; font-size: 16px;">✓</span>
    <div>
      <div style="font-weight: 500; color: #16a34a;">Success</div>
      <div style="font-size: 12px; color: #166534;">Mapping created successfully</div>
    </div>
    <span style="margin-left: auto; color: #6b7280; cursor: pointer;">×</span>
  </div>
  <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 12px 16px; display: flex; align-items: flex-start; gap: 12px;">
    <span style="color: #dc2626; font-size: 16px;">✕</span>
    <div>
      <div style="font-weight: 500; color: #dc2626;">Error</div>
      <div style="font-size: 12px; color: #991b1b;">Failed to create snapshot. Please try again.</div>
    </div>
    <span style="margin-left: auto; color: #6b7280; cursor: pointer;">×</span>
  </div>
  <div style="background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 12px 16px; display: flex; align-items: flex-start; gap: 12px;">
    <span style="color: #d97706; font-size: 16px;">⚠</span>
    <div>
      <div style="font-weight: 500; color: #d97706;">Warning</div>
      <div style="font-size: 12px; color: #92400e;">Your instance will expire in 1 hour</div>
    </div>
    <span style="margin-left: auto; color: #6b7280; cursor: pointer;">×</span>
  </div>
</div>

**Behavior:**
- **Position** - Top right, stacked
- **Auto-dismiss** - Success: 5s, Error: manual, Warning: 10s
- **Animation** - Slide in from right, fade out

---

### Empty State

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #e5e7eb; border-radius: 8px; padding: 48px 24px; text-align: center; max-width: 500px; background: #fafafa;">
  <div style="font-size: 48px; margin-bottom: 16px;">🗺️</div>
  <div style="font-size: 18px; font-weight: 600; color: #374151; margin-bottom: 8px;">No mappings yet</div>
  <div style="font-size: 14px; color: #6b7280; margin-bottom: 24px;">Mappings define how your relational data becomes a graph. Create your first mapping to get started.</div>
  <button style="background: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer;">Create Your First Mapping</button>
</div>

**Guidelines:**
- **Icon** - Relevant emoji or illustration
- **Title** - What's empty
- **Description** - Why and what to do
- **Action** - Clear CTA button

---

### Loading State

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #e5e7eb; border-radius: 8px; padding: 48px 24px; text-align: center; max-width: 500px;">
  <div style="width: 40px; height: 40px; border: 3px solid #e5e7eb; border-top-color: #2563eb; border-radius: 50%; margin: 0 auto 16px; animation: spin 1s linear infinite;"></div>
  <div style="font-size: 14px; color: #6b7280;">Loading mappings...</div>
</div>

**Guidelines:**
- Show after 200ms delay (avoid flash for fast loads)
- Use skeleton loaders for table/list content
- Show specific message ("Loading mappings..." not just "Loading...")

---

### Error State

**Page-Level Error:**

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #fecaca; border-radius: 8px; padding: 24px; max-width: 500px; background: #fef2f2;">
  <div style="display: flex; align-items: flex-start; gap: 12px;">
    <span style="font-size: 24px;">⚠️</span>
    <div>
      <div style="font-size: 16px; font-weight: 600; color: #dc2626; margin-bottom: 8px;">Failed to load mappings</div>
      <div style="font-size: 13px; color: #7f1d1d; margin-bottom: 16px;">We couldn't connect to the server. This might be a temporary issue.</div>
      <button style="background: white; color: #dc2626; border: 1px solid #fecaca; padding: 8px 16px; border-radius: 6px; font-size: 13px; cursor: pointer;">Try Again</button>
    </div>
  </div>
</div>

#### Error Boundaries (Partial Failures)

When part of a page fails while other parts succeed, use section-level error boundaries to allow graceful degradation.

**Section Error (Inline):**

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; max-width: 600px;">
  <div style="padding: 16px; border-bottom: 1px solid #e5e7eb;">
    <div style="font-weight: 600; margin-bottom: 4px;">Customer Graph</div>
    <div style="color: #6b7280; font-size: 11px;">Mapping Details</div>
  </div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #e5e7eb;">
    <div style="background: white; padding: 16px;">
      <div style="font-weight: 500; margin-bottom: 8px;">Overview</div>
      <div style="color: #6b7280; font-size: 11px;">Created: Jan 15, 2025</div>
      <div style="color: #6b7280; font-size: 11px;">Owner: alice.smith</div>
    </div>
    <div style="background: #fef2f2; padding: 16px;">
      <div style="display: flex; align-items: center; gap: 8px; color: #dc2626; font-weight: 500; margin-bottom: 8px;">
        <span>⚠️</span> Failed to load resources
      </div>
      <div style="color: #7f1d1d; font-size: 11px; margin-bottom: 12px;">Unable to fetch snapshot data</div>
      <button style="background: white; color: #dc2626; border: 1px solid #fecaca; padding: 4px 12px; border-radius: 4px; font-size: 11px; cursor: pointer;">Retry</button>
    </div>
  </div>
</div>

**Error Boundary Behavior:**

| Scenario | Behavior |
|----------|----------|
| Main content fails, sidebar loads | Show error in main content area; sidebar remains functional |
| Dashboard widget fails | Show inline error in widget; other widgets unaffected |
| Page section fails | Show inline error in section; other sections display normally |
| Detail section fails | Show inline retry; other sections display normally |

**Error Boundary Rules:**

1. **Isolate failures** - One section's failure should not crash the entire page
2. **Provide retry** - Each error boundary has its own "Retry" button
3. **Preserve navigation** - Global nav and sidebar remain functional
4. **Show context** - Error message indicates what failed, not generic "Something went wrong"
5. **Log for debugging** - Capture error details for developer console

**Dashboard Widget Error:**

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; max-width: 280px; background: #fef2f2;">
  <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
    <span style="font-weight: 500; color: #374151;">Recent Activity</span>
    <span style="color: #dc2626; font-size: 16px;">⚠️</span>
  </div>
  <div style="color: #7f1d1d; font-size: 11px; margin-bottom: 12px;">Couldn't load activity feed</div>
  <button style="background: white; color: #dc2626; border: 1px solid #fecaca; padding: 4px 12px; border-radius: 4px; font-size: 11px; cursor: pointer; width: 100%;">Retry</button>
</div>

**Implementation Notes:**

- Use React Error Boundaries or equivalent framework pattern
- Each boundary should catch errors independently
- Failed sections should not affect parent component state
- Retry should only refetch the failed section's data

---

## Motion and Animation

### Timing

| Duration | Use Case |
|----------|----------|
| 150ms | Micro-interactions (button hover, focus rings) |
| 200ms | State changes (expand/collapse, toggle) |
| 300ms | Entrance/exit (toast, dropdown, tooltip) |

### Easing

| Type | CSS | Use Case |
|------|-----|----------|
| Ease-out | `cubic-bezier(0, 0, 0.2, 1)` | Entrances (elements appearing) |
| Ease-in | `cubic-bezier(0.4, 0, 1, 1)` | Exits (elements disappearing) |
| Ease-in-out | `cubic-bezier(0.4, 0, 0.2, 1)` | State changes (expand/collapse) |

### Animated Elements

| Element | Animation | Duration |
|---------|-----------|----------|
| Toast notifications | Slide in from top-right, fade out | 300ms |
| Collapsible cards | Height expand/collapse | 200ms |
| Dropdowns | Fade + scale from origin | 200ms |
| Tooltips | Fade in | 150ms |
| Star toggle | Scale bounce | 200ms |
| Button hover | Background color | 150ms |
| Focus rings | Opacity | 150ms |

### No Animation

These elements change instantly (no transition):
- Page navigation (full page changes)
- Table sorting/filtering
- Form validation states
- Status badge changes

### Reduced Motion

Respect `prefers-reduced-motion: reduce` media query:
- Disable all animations except opacity fades
- Toast: fade only (no slide)
- Collapsible: instant (no height animation)

---

## Accessibility Requirements

Based on ADR-014.

### Keyboard Navigation

| Component | Keys |
|-----------|------|
| Buttons | Tab to focus, Enter/Space to activate |
| Links | Tab to focus, Enter to navigate |
| Dropdown | Tab to trigger, Arrow keys to navigate, Enter to select, Escape to close |
| Table | Tab to table, Arrow keys between cells, Enter on row to open |
| Star toggle | Tab to focus, Space to toggle |
| Modal (none used) | N/A - ADR-014 prohibits modals |

### Focus Indicators

All interactive elements must have visible focus:

```css
:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}
```

### Color Contrast

| Element | Minimum Ratio |
|---------|---------------|
| Body text | 4.5:1 |
| Large text (18px+) | 3:1 |
| UI components | 3:1 |
| Disabled elements | N/A (no contrast requirement) |

### Screen Reader Support

- Use semantic HTML (`<button>`, `<nav>`, `<main>`, `<table>`)
- All images have `alt` text
- Form inputs have associated labels
- Status badges include text (not just color)
- Progress updates announced via `aria-live`

### Focus Management

Focus must be programmatically managed after user actions to maintain keyboard accessibility.

**After Navigation Actions:**

| Action | Focus Target |
|--------|--------------|
| Page navigation | Main content heading (`<h1>`) or first interactive element |
| Section scroll (anchor link) | Section heading |
| Sidebar expand/collapse | Keep focus on toggle button |

**After CRUD Actions:**

| Action | Focus Target |
|--------|--------------|
| Create resource | New detail page: first heading or back link |
| Update resource | Keep focus on save button, show toast |
| Delete single item | Previous row in list, or next row if first, or empty state CTA if last |
| Delete via bulk action | Selection toolbar (cleared), or first row if toolbar hidden |
| Cancel action | Return focus to original trigger element |

**After Async Operations:**

| Action | Focus Target |
|--------|--------------|
| Form submission (success) | Toast notification (auto-dismiss will return focus to page) |
| Form submission (error) | First field with error, or error summary |
| Inline confirmation appears | First button in confirmation (Cancel or destructive action) |
| Inline confirmation dismissed | Original trigger button |
| Toast appears | Toast is announced via `aria-live`, focus remains in place |

**Implementation Pattern:**

```javascript
// After delete from list
const rows = tableRef.querySelectorAll('tbody tr');
const deletedIndex = /* index of deleted row */;
const nextFocus = rows[deletedIndex] || rows[deletedIndex - 1] || emptyStateCTA;
nextFocus?.focus();
```

**Announcements:**

Use `aria-live` regions for status updates that don't move focus:
- `aria-live="polite"` for success messages, progress updates
- `aria-live="assertive"` for errors requiring immediate attention

---

## Responsive Behavior

Based on ADR-013.

### Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Minimum | 1024px | Sidebar collapsed to icons, single column |
| Standard | 1280px+ | Full sidebar, side-by-side layouts |

### Component Adaptations

| Component | < 1280px | >= 1280px |
|-----------|----------|-----------|
| Sidebar | Icons only (48px) | Full (220px) |
| Detail page sections | Full width, stacked | Full width, stacked |
| Compare view | Stacked (vertical scroll) | Side-by-side |
| Filter bar | Wraps to multiple rows | Single row |

---

## Related Documents

- [ux.flows.md](./ux.flows.md) - User flows and page layouts
- [ux.copy.spec.md](./ux.copy.spec.md) - UI copy and messaging
- [decision.log.md](../process/decision.log.md) - ADR-013, ADR-014

---

## Change History

| Date | Change |
|------|--------|
| 2025-12-12 | Initial creation with component inventory and specifications |
