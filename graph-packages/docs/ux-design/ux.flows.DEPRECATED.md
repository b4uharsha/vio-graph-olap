# UX Flows and User Journeys

> **DEPRECATED** - This document is no longer maintained.
>
> The Graph OLAP Platform no longer includes a web interface. All user interaction
> is now through the Jupyter SDK. This document is retained for historical reference.
>
> See [jupyter-sdk.design.md](../component-designs/jupyter-sdk.design.md) for the current user interface design.

## Overview

User journeys, page inventory, navigation patterns, and interaction sequences for the Graph OLAP Platform web interface.

## Prerequisites

- [requirements.md](../foundation/requirements.md) - UX requirements section (lines 940-1062)
- [decision.log.md](../process/decision.log.md) - ADR-006 through ADR-017
- [ux.readiness-assessment.md](./ux.readiness-assessment.md) - Product engineering readiness

---

## Page Inventory

### All Users (Analyst, Admin, Ops)

| Page | URL | Purpose |
|------|-----|---------|
| Dashboard | `/` | Landing page, recent activity, quick stats |
| Mappings List | `/mappings` | Browse, filter, search mappings |
| Mapping Create | `/mappings/new` | Create new mapping |
| Mapping Detail | `/mappings/:id` | View mapping, versions, resources |
| Mapping Edit | `/mappings/:id/edit` | Edit mapping header and definition |
| Mapping Compare | `/compare` | Compare two mapping versions |
| Snapshots List | `/snapshots` | Browse, filter, search snapshots |
| Snapshot Detail | `/snapshots/:id` | View snapshot, progress, instances |
| Instances List | `/instances` | Browse, filter, search instances |
| Instance Detail | `/instances/:id` | View instance status, connection info, terminate |
| Favorites | `/favorites` | User's bookmarked resources |

### Admin Only

Admin users have the same pages as Analysts, plus edit/delete permissions on all resources.

### Ops Only

| Page | URL | Purpose |
|------|-----|---------|
| Cluster Health | `/ops/health` | System health, component status |
| Configuration | `/ops/config` | Lifecycle, concurrency, schema, maintenance |
| Export Queue | `/ops/exports` | Export status, retry, cancel |

**Note:** Audit logs are accessed via the company's external observability stack (not in web UI).

---

## Navigation Structure

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 13px;">
  <div style="display: flex; gap: 16px; flex-wrap: wrap;">
    <div style="border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; min-width: 320px; flex: 1;">
      <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 12px 16px; border-bottom: 1px solid #93c5fd;">
        <span style="font-weight: 600; color: #1d4ed8;">Main Navigation</span>
      </div>
      <div style="padding: 0;">
        <div style="padding: 12px 16px; border-bottom: 1px solid #f3f4f6; display: flex; align-items: center; gap: 12px;">
          <span style="width: 20px; text-align: center;">📊</span>
          <div>
            <div style="font-weight: 500;">Dashboard</div>
            <div style="font-size: 11px; color: #6b7280;">Recent activity, quick stats, getting started</div>
          </div>
        </div>
        <div style="padding: 12px 16px; border-bottom: 1px solid #f3f4f6; display: flex; align-items: center; gap: 12px;">
          <span style="width: 20px; text-align: center;">🗺️</span>
          <div>
            <div style="font-weight: 500;">Mappings</div>
            <div style="font-size: 11px; color: #6b7280;">Graph schema definitions</div>
          </div>
        </div>
        <div style="padding: 12px 16px; border-bottom: 1px solid #f3f4f6; display: flex; align-items: center; gap: 12px;">
          <span style="width: 20px; text-align: center;">📸</span>
          <div>
            <div style="font-weight: 500;">Snapshots</div>
            <div style="font-size: 11px; color: #6b7280;">Point-in-time data exports</div>
          </div>
        </div>
        <div style="padding: 12px 16px; border-bottom: 1px solid #f3f4f6; display: flex; align-items: center; gap: 12px;">
          <span style="width: 20px; text-align: center;">⚡</span>
          <div>
            <div style="font-weight: 500;">Instances</div>
            <div style="font-size: 11px; color: #6b7280;">Running graph databases</div>
          </div>
        </div>
        <div style="padding: 12px 16px; border-bottom: 1px solid #f3f4f6; display: flex; align-items: center; gap: 12px;">
          <span style="width: 20px; text-align: center;">⭐</span>
          <div>
            <div style="font-weight: 500;">Favorites</div>
            <div style="font-size: 11px; color: #6b7280;">Bookmarked resources</div>
          </div>
        </div>
        <div style="padding: 12px 16px; border-top: 2px solid #e5e7eb; margin-top: 8px; display: flex; align-items: center; gap: 12px; background: #fafafa;">
          <span style="width: 20px; text-align: center;">👤</span>
          <div>
            <div style="font-weight: 500; color: #6b7280;">User Menu</div>
            <div style="font-size: 11px; color: #9ca3af;">Profile, preferences, logout</div>
          </div>
        </div>
      </div>
    </div>
    <div style="border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; min-width: 280px;">
      <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 12px 16px; border-bottom: 1px solid #fcd34d;">
        <span style="font-weight: 600; color: #b45309;">Admin Section</span>
        <span style="font-size: 11px; color: #92400e; margin-left: 8px;">(Admin role only)</span>
      </div>
      <div style="padding: 12px 16px; font-size: 12px; color: #6b7280;">
        <div style="padding: 6px 0; display: flex; align-items: center; gap: 8px;">
          <span>✓</span> All Analyst capabilities
        </div>
        <div style="padding: 6px 0; display: flex; align-items: center; gap: 8px;">
          <span>✓</span> Edit/delete any user's resources
        </div>
      </div>
    </div>
    <div style="border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; min-width: 280px;">
      <div style="background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); padding: 12px 16px; border-bottom: 1px solid #d8b4fe;">
        <span style="font-weight: 600; color: #7c3aed;">Ops Section</span>
        <span style="font-size: 11px; color: #6d28d9; margin-left: 8px;">(Ops role only)</span>
      </div>
      <div style="padding: 0;">
        <div style="padding: 10px 16px; border-bottom: 1px solid #f3f4f6; display: flex; align-items: center; gap: 10px;">
          <span style="width: 18px; text-align: center;">💓</span>
          <div>
            <div style="font-weight: 500; font-size: 13px;">Cluster Health</div>
            <div style="font-size: 11px; color: #6b7280;">Metrics, component status</div>
          </div>
        </div>
        <div style="padding: 10px 16px; border-bottom: 1px solid #f3f4f6; display: flex; align-items: center; gap: 10px;">
          <span style="width: 18px; text-align: center;">⚙️</span>
          <div>
            <div style="font-weight: 500; font-size: 13px;">Configuration</div>
            <div style="font-size: 11px; color: #6b7280;">Lifecycle, Concurrency, Schema, Maintenance</div>
          </div>
        </div>
        <div style="padding: 10px 16px; display: flex; align-items: center; gap: 10px;">
          <span style="width: 18px; text-align: center;">📤</span>
          <div>
            <div style="font-weight: 500; font-size: 13px;">Export Queue</div>
            <div style="font-size: 11px; color: #6b7280;">Status, retry, cancel</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

**Note:** Audit logs are accessed via the company's external observability stack, not in this UI.

---

## Page Layouts

### Dashboard

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 900px;">
  <div style="background: #f8fafc; padding: 16px 24px; border-bottom: 1px solid #e5e7eb;">
    <div style="font-size: 18px; font-weight: 600; color: #1f2937;">Dashboard</div>
    <div style="font-size: 13px; color: #6b7280; margin-top: 4px;">Welcome back, <strong>alice.smith</strong></div>
  </div>
  <div style="padding: 24px; display: flex; gap: 24px; flex-wrap: wrap;">
    <div style="flex: 2; min-width: 300px;">
      <div style="font-weight: 600; color: #374151; margin-bottom: 12px;">Quick Stats</div>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 12px 16px; min-width: 100px;">
          <div style="font-size: 24px; font-weight: 600; color: #1d4ed8;">12</div>
          <div style="font-size: 11px; color: #6b7280;">My Mappings</div>
        </div>
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 12px 16px; min-width: 100px;">
          <div style="font-size: 24px; font-weight: 600; color: #16a34a;">8</div>
          <div style="font-size: 11px; color: #6b7280;">Ready Snapshots</div>
        </div>
        <div style="background: #fefce8; border: 1px solid #fef08a; border-radius: 6px; padding: 12px 16px; min-width: 100px;">
          <div style="font-size: 24px; font-weight: 600; color: #ca8a04;">3</div>
          <div style="font-size: 11px; color: #6b7280;">Running Instances</div>
        </div>
      </div>
      <div style="font-weight: 600; color: #374151; margin-top: 24px; margin-bottom: 12px;">Recent Activity</div>
      <div style="border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden;">
        <div style="padding: 10px 12px; border-bottom: 1px solid #f3f4f6; display: flex; justify-content: space-between;">
          <span><strong>Customer Graph v3</strong> snapshot completed</span>
          <span style="color: #6b7280; font-size: 11px;">2 min ago</span>
        </div>
        <div style="padding: 10px 12px; border-bottom: 1px solid #f3f4f6; display: flex; justify-content: space-between;">
          <span>Instance <strong>Analysis-001</strong> started</span>
          <span style="color: #6b7280; font-size: 11px;">15 min ago</span>
        </div>
        <div style="padding: 10px 12px; display: flex; justify-content: space-between;">
          <span><strong>Transaction Network</strong> mapping created</span>
          <span style="color: #6b7280; font-size: 11px;">1 hour ago</span>
        </div>
      </div>
    </div>
    <div style="flex: 1; min-width: 200px;">
      <div style="font-weight: 600; color: #374151; margin-bottom: 12px;">Quick Actions</div>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <button style="background: #2563eb; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-size: 13px;">+ Create Mapping</button>
        <button style="background: white; color: #374151; border: 1px solid #d1d5db; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-size: 13px;">Browse All Mappings</button>
        <button style="background: white; color: #374151; border: 1px solid #d1d5db; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-size: 13px;">View My Instances</button>
      </div>
      <div style="font-weight: 600; color: #374151; margin-top: 24px; margin-bottom: 12px;">Favorites</div>
      <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; font-size: 11px; color: #6b7280;">
        <div style="padding: 4px 0;">⭐ Customer Graph v3</div>
        <div style="padding: 4px 0;">⭐ Transaction Network</div>
        <div style="padding: 4px 0; color: #2563eb; cursor: pointer;">View all favorites →</div>
      </div>
    </div>
  </div>
</div>

---

### Mappings List

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 900px;">
  <div style="background: #f8fafc; padding: 16px 24px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
    <div>
      <div style="font-size: 18px; font-weight: 600; color: #1f2937;">Mappings</div>
      <div style="font-size: 13px; color: #6b7280; margin-top: 4px;">Graph schema definitions</div>
    </div>
    <button style="background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500;">+ Create Mapping</button>
  </div>
  <div style="padding: 16px 24px; background: #fafafa; border-bottom: 1px solid #e5e7eb; display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
    <input type="text" placeholder="Search mappings..." style="padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; min-width: 200px;">
    <select style="padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; background: white;">
      <option>All Owners</option>
      <option>My Mappings</option>
    </select>
    <button style="padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; background: white; cursor: pointer;">⭐ Favorites Only</button>
    <div style="margin-left: auto; font-size: 11px; color: #6b7280;">Showing 24 of 156 mappings</div>
  </div>
  <div style="padding: 0;">
    <table style="width: 100%; border-collapse: collapse;">
      <thead>
        <tr style="background: #f9fafb; border-bottom: 1px solid #e5e7eb;">
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">NAME</th>
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">OWNER</th>
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">VERSION</th>
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">SNAPSHOTS</th>
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">UPDATED</th>
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;"></th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom: 1px solid #f3f4f6;">
          <td style="padding: 12px 16px;"><span style="color: #ca8a04; cursor: pointer;">⭐</span> <strong style="color: #2563eb; cursor: pointer;">Customer Graph</strong></td>
          <td style="padding: 12px 16px; color: #6b7280;">alice.smith</td>
          <td style="padding: 12px 16px;"><span style="background: #dbeafe; color: #1d4ed8; padding: 2px 8px; border-radius: 4px; font-size: 11px;">v3</span></td>
          <td style="padding: 12px 16px; color: #6b7280;">5</td>
          <td style="padding: 12px 16px; color: #6b7280;">2 hours ago</td>
          <td style="padding: 12px 16px;"><span style="color: #6b7280; cursor: pointer;">⋮</span></td>
        </tr>
        <tr style="border-bottom: 1px solid #f3f4f6;">
          <td style="padding: 12px 16px;"><span style="color: #d1d5db; cursor: pointer;">☆</span> <strong style="color: #2563eb; cursor: pointer;">Transaction Network</strong></td>
          <td style="padding: 12px 16px; color: #6b7280;">bob.jones</td>
          <td style="padding: 12px 16px;"><span style="background: #dbeafe; color: #1d4ed8; padding: 2px 8px; border-radius: 4px; font-size: 11px;">v1</span></td>
          <td style="padding: 12px 16px; color: #6b7280;">2</td>
          <td style="padding: 12px 16px; color: #6b7280;">Yesterday</td>
          <td style="padding: 12px 16px;"><span style="color: #6b7280; cursor: pointer;">⋮</span></td>
        </tr>
        <tr style="border-bottom: 1px solid #f3f4f6; background: #fafafa;">
          <td style="padding: 12px 16px;"><span style="color: #d1d5db; cursor: pointer;">☆</span> <strong style="color: #2563eb; cursor: pointer;">Supply Chain</strong></td>
          <td style="padding: 12px 16px; color: #6b7280;">carol.wilson</td>
          <td style="padding: 12px 16px;"><span style="background: #dbeafe; color: #1d4ed8; padding: 2px 8px; border-radius: 4px; font-size: 11px;">v7</span></td>
          <td style="padding: 12px 16px; color: #6b7280;">12</td>
          <td style="padding: 12px 16px; color: #6b7280;">3 days ago</td>
          <td style="padding: 12px 16px;"><span style="color: #6b7280; cursor: pointer;">⋮</span></td>
        </tr>
      </tbody>
    </table>
  </div>
  <div style="padding: 12px 24px; background: #fafafa; border-top: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
    <div style="font-size: 11px; color: #6b7280;">Page 1 of 7</div>
    <div style="display: flex; gap: 4px;">
      <button style="padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; font-size: 12px; color: #9ca3af;">Previous</button>
      <button style="padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; font-size: 12px;">Next</button>
    </div>
  </div>
</div>

---

### Mapping Detail

Single-page layout with section headings (no tabs).

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 900px;">
  <div style="background: #f8fafc; padding: 16px 24px; border-bottom: 1px solid #e5e7eb;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
      <div>
        <div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">← Back to Mappings</div>
        <div style="font-size: 18px; font-weight: 600; color: #1f2937; display: flex; align-items: center; gap: 8px;">
          Customer Graph
          <span style="color: #ca8a04; cursor: pointer; font-size: 16px;">⭐</span>
          <span style="background: #dbeafe; color: #1d4ed8; padding: 2px 8px; border-radius: 4px; font-size: 11px;">v3</span>
        </div>
        <div style="font-size: 13px; color: #6b7280; margin-top: 4px;">Customer relationship graph for fraud detection</div>
      </div>
      <div style="display: flex; gap: 8px;">
        <button style="background: white; color: #374151; border: 1px solid #d1d5db; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px;">Edit</button>
        <button style="background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px;">Create Snapshot</button>
      </div>
    </div>
    <div style="display: flex; gap: 24px; margin-top: 16px; font-size: 13px; color: #6b7280;">
      <div><strong>Owner:</strong> alice.smith</div>
      <div><strong>Created:</strong> Jan 15, 2025</div>
      <div><strong>Updated:</strong> 2 hours ago</div>
    </div>
  </div>

  <!-- Definition Section -->
  <div style="padding: 24px; border-bottom: 1px solid #e5e7eb;">
    <div style="font-size: 16px; font-weight: 600; color: #1f2937; margin-bottom: 16px;">Definition</div>
    <div style="font-weight: 500; color: #374151; margin-bottom: 12px;">Node Definitions</div>
    <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px;">
      <div style="border: 1px solid #d1d5db; border-radius: 6px; padding: 12px 16px; min-width: 180px; background: #fafafa;">
        <div style="font-weight: 500; color: #1f2937;">Customer</div>
        <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">PK: customer_id (STRING)</div>
        <div style="font-size: 11px; color: #6b7280;">5 properties</div>
      </div>
      <div style="border: 1px solid #d1d5db; border-radius: 6px; padding: 12px 16px; min-width: 180px; background: #fafafa;">
        <div style="font-weight: 500; color: #1f2937;">Account</div>
        <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">PK: account_id (STRING)</div>
        <div style="font-size: 11px; color: #6b7280;">3 properties</div>
      </div>
    </div>
    <div style="font-weight: 500; color: #374151; margin-bottom: 12px;">Edge Definitions</div>
    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
      <div style="border: 1px solid #d1d5db; border-radius: 6px; padding: 12px 16px; min-width: 220px; background: #fafafa;">
        <div style="font-weight: 500; color: #1f2937;">OWNS</div>
        <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">Customer → Account</div>
        <div style="font-size: 11px; color: #6b7280;">2 properties</div>
      </div>
      <div style="border: 1px solid #d1d5db; border-radius: 6px; padding: 12px 16px; min-width: 220px; background: #fafafa;">
        <div style="font-weight: 500; color: #1f2937;">TRANSFERRED_TO</div>
        <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">Account → Account</div>
        <div style="font-size: 11px; color: #6b7280;">4 properties</div>
      </div>
    </div>
  </div>

  <!-- Version History Section -->
  <div style="padding: 24px; border-bottom: 1px solid #e5e7eb;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <div style="font-size: 16px; font-weight: 600; color: #1f2937;">Version History</div>
      <button style="background: white; color: #374151; border: 1px solid #d1d5db; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">Compare Versions</button>
    </div>
    <div style="border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden;">
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #f0fdf4; border-left: 3px solid #16a34a;">
        <div>
          <div style="font-weight: 500; color: #1f2937;">v3 <span style="background: #dcfce7; color: #16a34a; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-left: 8px;">Current</span></div>
          <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Added transaction amount property • alice.smith • 2 hours ago</div>
        </div>
        <button style="background: white; color: #374151; border: 1px solid #d1d5db; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">Create Snapshot</button>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-top: 1px solid #e5e7eb;">
        <div>
          <div style="font-weight: 500; color: #1f2937;">v2</div>
          <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Added Account node type • alice.smith • 3 days ago</div>
        </div>
        <button style="background: white; color: #374151; border: 1px solid #d1d5db; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">Create Snapshot</button>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-top: 1px solid #e5e7eb;">
        <div>
          <div style="font-weight: 500; color: #1f2937;">v1</div>
          <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Initial version • alice.smith • Jan 15, 2025</div>
        </div>
        <button style="background: white; color: #374151; border: 1px solid #d1d5db; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">Create Snapshot</button>
      </div>
    </div>
  </div>

  <!-- Resources Section -->
  <div style="padding: 24px;">
    <div style="font-size: 16px; font-weight: 600; color: #1f2937; margin-bottom: 16px;">Resources</div>
    <div style="font-size: 11px; color: #6b7280; margin-bottom: 12px;">Snapshots and instances created from this mapping</div>
    <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px;">
      <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0;">
        <span style="color: #6b7280; cursor: pointer;">▼</span>
        <span>📸 January 2025 Snapshot</span>
        <span style="background: #dcfce7; color: #16a34a; padding: 1px 6px; border-radius: 4px; font-size: 10px;">Ready</span>
        <span style="font-size: 11px; color: #6b7280; margin-left: auto;">v3 • 2.4 GB</span>
      </div>
      <div style="margin-left: 24px; border-left: 1px solid #e5e7eb; padding-left: 16px;">
        <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0;">
          <span>⚡ Analysis-001</span>
          <span style="background: #dcfce7; color: #16a34a; padding: 1px 6px; border-radius: 4px; font-size: 10px;">Running</span>
          <span style="font-size: 11px; color: #6b7280; margin-left: auto;">alice.smith</span>
          <button style="padding: 2px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 10px; background: white; cursor: pointer;">Open</button>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0;">
          <span>⚡ Analysis-002</span>
          <span style="background: #f3f4f6; color: #6b7280; padding: 1px 6px; border-radius: 4px; font-size: 10px;">Stopped</span>
          <span style="font-size: 11px; color: #6b7280; margin-left: auto;">bob.jones</span>
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px; padding: 6px 0; margin-top: 8px;">
        <span style="color: #6b7280; cursor: pointer;">▶</span>
        <span>📸 December 2024 Snapshot</span>
        <span style="background: #dcfce7; color: #16a34a; padding: 1px 6px; border-radius: 4px; font-size: 10px;">Ready</span>
        <span style="font-size: 11px; color: #6b7280; margin-left: auto;">v2 • 1.8 GB</span>
      </div>
    </div>
  </div>
</div>

---

## Core User Flows

### Flow 1: Create Mapping (Generate from SQL)

Based on [ADR-8](../process/adr/ux/adr-008-generate-from-sql-workflow.md).

![mapping-creation-flow](diagrams/ux.flows/mapping-creation-flow.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#E3F2FD", "primaryTextColor": "#0D47A1", "primaryBorderColor": "#1565C0", "lineColor": "#37474F"}}}%%
flowchart LR
    accTitle: Mapping Creation Flow
    accDescr: User navigates from Mappings List to Create Mapping page

    %% Page/navigation styling (Infrastructure color)
    classDef page fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1

    %% Flow: List → Create Page
    A([Mappings List]):::page -->|Click Create Mapping| B([Create Mapping Page]):::page
```

</details>

**Create Mapping Page** (single-page form):

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 700px;">
  <div style="background: #f8fafc; padding: 16px 24px; border-bottom: 1px solid #e5e7eb;">
    <div style="font-size: 18px; font-weight: 600; color: #1f2937;">Create Mapping</div>
  </div>
  <div style="padding: 24px; max-width: 600px;">
    <!-- Header Section -->
    <div style="margin-bottom: 32px;">
      <div style="font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 16px;">Details</div>
      <div style="margin-bottom: 16px;">
        <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">Name <span style="color: #dc2626;">*</span></label>
        <input type="text" placeholder="e.g., Customer Graph" style="width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; box-sizing: border-box;">
      </div>
      <div>
        <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">Description</label>
        <textarea placeholder="Optional description" style="width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; box-sizing: border-box; min-height: 60px;"></textarea>
      </div>
    </div>
    <!-- Nodes Section -->
    <div style="margin-bottom: 32px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <div style="font-size: 14px; font-weight: 600; color: #374151;">Nodes</div>
        <button style="background: white; color: #2563eb; border: 1px solid #2563eb; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer;">+ Add Node</button>
      </div>
      <!-- Node Card - Collapsed (validated) -->
      <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; background: #fafafa;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #6b7280; cursor: pointer;">▶</span>
            <span style="font-size: 13px; font-weight: 500; color: #374151;">Customer</span>
            <span style="font-size: 11px; color: #16a34a;">✓ Valid</span>
          </div>
          <button style="color: #dc2626; background: none; border: none; font-size: 12px; cursor: pointer;">Remove</button>
        </div>
      </div>
      <!-- Node Card - Collapsed (validated) -->
      <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; background: #fafafa;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #6b7280; cursor: pointer;">▶</span>
            <span style="font-size: 13px; font-weight: 500; color: #374151;">Product</span>
            <span style="font-size: 11px; color: #16a34a;">✓ Valid</span>
          </div>
          <button style="color: #dc2626; background: none; border: none; font-size: 12px; cursor: pointer;">Remove</button>
        </div>
      </div>
      <!-- Node Card - Expanded (editing) -->
      <div style="border: 1px solid #2563eb; border-radius: 8px; padding: 16px; margin-bottom: 8px; background: white;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #2563eb; cursor: pointer;">▼</span>
            <input type="text" value="Order" placeholder="Node label" style="padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; font-weight: 500;">
          </div>
          <button style="color: #dc2626; background: none; border: none; font-size: 12px; cursor: pointer;">Remove</button>
        </div>
        <div style="margin-bottom: 8px;">
          <div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">SQL Query</div>
          <div style="display: flex; gap: 8px;">
            <textarea style="flex: 1; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; font-family: monospace; min-height: 40px;">SELECT order_id, total, status FROM orders</textarea>
            <button style="background: #f3f4f6; border: 1px solid #d1d5db; padding: 8px 12px; border-radius: 4px; font-size: 12px; cursor: pointer; white-space: nowrap;">Validate</button>
          </div>
        </div>
        <div style="font-size: 11px; color: #6b7280;">Not validated</div>
      </div>
    </div>
    <!-- Edges Section -->
    <div style="margin-bottom: 32px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <div style="font-size: 14px; font-weight: 600; color: #374151;">Edges</div>
        <button style="background: white; color: #2563eb; border: 1px solid #2563eb; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer;">+ Add Edge</button>
      </div>
      <!-- Edge Card - Collapsed (validated) -->
      <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; background: #fafafa;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #6b7280; cursor: pointer;">▶</span>
            <span style="font-size: 13px; font-weight: 500; color: #374151;">PURCHASED</span>
            <span style="font-size: 11px; color: #6b7280;">Customer → Product</span>
            <span style="font-size: 11px; color: #16a34a;">✓ Valid</span>
          </div>
          <button style="color: #dc2626; background: none; border: none; font-size: 12px; cursor: pointer;">Remove</button>
        </div>
      </div>
      <!-- Edge Card - Expanded (editing) -->
      <div style="border: 1px solid #2563eb; border-radius: 8px; padding: 16px; margin-bottom: 8px; background: white;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #2563eb; cursor: pointer;">▼</span>
            <input type="text" value="PLACED" placeholder="Edge type" style="padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; font-weight: 500; width: 100px;">
            <span style="color: #6b7280; font-size: 12px;">from</span>
            <select style="padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px;">
              <option>Customer</option>
              <option>Product</option>
              <option>Order</option>
            </select>
            <span style="color: #6b7280; font-size: 12px;">to</span>
            <select style="padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px;">
              <option>Order</option>
              <option>Customer</option>
              <option>Product</option>
            </select>
          </div>
          <button style="color: #dc2626; background: none; border: none; font-size: 12px; cursor: pointer;">Remove</button>
        </div>
        <div style="margin-bottom: 8px;">
          <div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">SQL Query</div>
          <div style="display: flex; gap: 8px;">
            <textarea style="flex: 1; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; font-family: monospace; min-height: 40px;">SELECT customer_id, order_id, placed_at FROM orders</textarea>
            <button style="background: #f3f4f6; border: 1px solid #d1d5db; padding: 8px 12px; border-radius: 4px; font-size: 12px; cursor: pointer; white-space: nowrap;">Validate</button>
          </div>
        </div>
        <div style="font-size: 11px; color: #6b7280;">Not validated</div>
      </div>
    </div>
    <!-- Actions -->
    <div style="display: flex; justify-content: flex-end; gap: 12px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
      <button style="background: white; color: #374151; border: 1px solid #d1d5db; padding: 10px 20px; border-radius: 6px; font-size: 13px; cursor: pointer;">Cancel</button>
      <button style="background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-size: 13px; cursor: pointer;">Create Mapping</button>
    </div>
  </div>
</div>

**Key Interactions:**

1. **Add/Remove** - Click "+ Add Node" or "+ Add Edge" to add cards; click "Remove" to delete
2. **Collapse/Expand** - Click ▶/▼ to toggle card. Collapsed shows label + status only. New cards open expanded.
3. **SQL Validation** - Each node/edge has its own SQL textarea and "Validate" button
4. **Schema Browser** - Panel alongside SQL editor showing available tables/columns (ADR-012)
5. **Type Warnings** - If type not supported, show warning with CAST suggestion (don't auto-modify SQL)
6. **Column Order** - PK must be first column (nodes), from/to keys must be first two (edges) - show error if wrong
7. **Edge Dropdowns** - From/To dropdowns populate with validated node labels
8. **Validation Required** - "Create Mapping" disabled until at least one node is validated

---

### Flow 2: Create Snapshot

![snapshot-creation-flow](diagrams/ux.flows/snapshot-creation-flow.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#E3F2FD", "primaryTextColor": "#0D47A1", "primaryBorderColor": "#1565C0", "lineColor": "#37474F"}}}%%
flowchart TB
    accTitle: Snapshot Creation Flow
    accDescr: Shows the user journey from creating a snapshot through various states to completion or failure

    %% Style definitions using Cagle semantic colors
    classDef page fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef form fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef pending fill:#ECEFF1,stroke:#455A64,stroke-width:2px,color:#263238
    classDef progress fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B
    classDef success fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef error fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C

    %% User journey through snapshot creation
    A([Mapping Detail]):::page -->|Click Create Snapshot| B[Create Snapshot Form<br>Name, Version, TTL]:::form
    B -->|Submit| C[PENDING<br>Waiting in queue...]:::pending
    C --> D[CREATING<br>Exporting nodes...]:::progress
    D --> E{Result}
    E -->|Success| F([READY<br>Create Instance]):::success
    E -->|Failure| G([FAILED<br>Retry / Delete]):::error
```

</details>

---

### Flow 3: Launch and Use Instance

![instance-usage-flow](diagrams/ux.flows/instance-usage-flow.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#E3F2FD", "primaryTextColor": "#0D47A1", "primaryBorderColor": "#1565C0", "lineColor": "#37474F"}}}%%
flowchart TB
    accTitle: Instance Usage Flow
    accDescr: Shows user journey from creating an instance through startup to running state with available actions

    %% Style definitions using Cagle semantic colors
    classDef page fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef form fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef progress fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B
    classDef success fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef action fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B

    %% User journey through instance creation and usage
    A([Snapshot Detail]):::page -->|Click Create Instance| B[Create Instance Form<br>Name, TTL]:::form
    B -->|Submit| C[STARTING<br>Creating pod...]:::progress
    C --> D([RUNNING<br>Connection Info Available]):::success

    %% Available actions on running instance
    D --> E[Extend TTL]:::action
    D --> F[Terminate]:::action
    D --> G[Use SDK / Explorer]:::action
```

</details>

**Button Behaviors:**

| Button | Action | Feedback |
|--------|--------|----------|
| Extend TTL | Immediately adds +24 hours to current TTL | Toast: "TTL extended. Expires in {X} hours" |
| Terminate | Inline confirmation, then terminates | Toast: "Instance terminated" |

**Extend TTL Rules:**
- Maximum TTL cap: 7 days from original creation
- Button disabled with tooltip "Maximum TTL reached" when at cap
- No confirmation required (non-destructive action)

---

### Flow 4: Compare Mapping Versions

Based on [ADR-9](../process/adr/ux/adr-009-unified-mapping-diff-page.md).

**Entry Points:**
1. Mapping Detail → Version History section → "Compare Versions" button
2. Direct URL: `/compare?a=123&av=2&b=123&bv=3`
3. Mappings List → Select two → "Compare"

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 900px;">
  <div style="background: #f8fafc; padding: 16px 24px; border-bottom: 1px solid #e5e7eb;">
    <div style="font-size: 18px; font-weight: 600; color: #1f2937;">Compare Mappings</div>
    <div style="display: flex; gap: 16px; margin-top: 12px; align-items: center;">
      <div style="flex: 1;">
        <div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">LEFT</div>
        <select style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px;">
          <option>Customer Graph v2</option>
        </select>
      </div>
      <div style="font-size: 20px; color: #9ca3af;">↔</div>
      <div style="flex: 1;">
        <div style="font-size: 11px; color: #6b7280; margin-bottom: 4px;">RIGHT</div>
        <select style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px;">
          <option>Customer Graph v3</option>
        </select>
      </div>
    </div>
  </div>
  <div style="padding: 16px 24px; background: #fafafa; border-bottom: 1px solid #e5e7eb;">
    <div style="font-weight: 600; color: #374151; margin-bottom: 12px;">Summary</div>
    <div style="display: flex; gap: 16px;">
      <div style="background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 8px 12px; font-size: 12px;">
        <strong style="color: #b45309;">2 Changed</strong>
      </div>
      <div style="background: #dcfce7; border: 1px solid #bbf7d0; border-radius: 6px; padding: 8px 12px; font-size: 12px;">
        <strong style="color: #16a34a;">1 Unchanged</strong>
      </div>
      <div style="background: #fee2e2; border: 1px solid #fecaca; border-radius: 6px; padding: 8px 12px; font-size: 12px;">
        <strong style="color: #dc2626;">1 Removed</strong>
      </div>
      <div style="background: #dbeafe; border: 1px solid #bfdbfe; border-radius: 6px; padding: 8px 12px; font-size: 12px;">
        <strong style="color: #2563eb;">1 Added</strong>
      </div>
    </div>
  </div>
  <div style="padding: 16px 24px;">
    <div style="font-weight: 600; color: #374151; margin-bottom: 12px;">Nodes</div>
    <div style="border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; margin-bottom: 16px;">
      <div style="padding: 12px 16px; background: #fef3c7; border-bottom: 1px solid #fcd34d; display: flex; justify-content: space-between; align-items: center;">
        <div><strong>Customer</strong> <span style="font-size: 11px; color: #b45309;">(Changed)</span></div>
        <span style="cursor: pointer; color: #6b7280;">▼ Expand</span>
      </div>
      <div style="padding: 12px 16px; background: #dcfce7; border-bottom: 1px solid #bbf7d0;">
        <strong>Account</strong> <span style="font-size: 11px; color: #16a34a;">(Unchanged)</span>
      </div>
      <div style="padding: 12px 16px; background: #dbeafe;">
        <strong>Merchant</strong> <span style="font-size: 11px; color: #2563eb;">(Added in v3)</span>
      </div>
    </div>
    <div style="font-weight: 600; color: #374151; margin-bottom: 12px;">Edges</div>
    <div style="border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden;">
      <div style="padding: 12px 16px; background: #fef3c7; border-bottom: 1px solid #fcd34d;">
        <strong>OWNS</strong> <span style="font-size: 11px; color: #b45309;">(Changed)</span>
      </div>
      <div style="padding: 12px 16px; background: #fee2e2;">
        <strong>RELATED_TO</strong> <span style="font-size: 11px; color: #dc2626;">(Removed in v3)</span>
      </div>
    </div>
  </div>
</div>

---

## User Preferences

Accessed via User Menu → Preferences. Available to all roles.

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 500px;">
  <div style="background: #f8fafc; padding: 16px 24px; border-bottom: 1px solid #e5e7eb;">
    <div style="font-size: 18px; font-weight: 600; color: #1f2937;">Preferences</div>
  </div>
  <div style="padding: 24px;">
    <div style="margin-bottom: 24px;">
      <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 8px;">Language</label>
      <select style="width: 100%; max-width: 250px; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;">
        <option>English</option>
        <option>中文 (简体)</option>
      </select>
      <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">Override browser language detection</div>
    </div>
    <div style="display: flex; justify-content: flex-end; gap: 12px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
      <button style="background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-size: 13px; cursor: pointer;">Save</button>
    </div>
  </div>
</div>

**Behavior:**
- Language preference stored in browser localStorage
- Applied immediately on save (page refreshes with new language)
- Persists across sessions on same browser
- Default: browser's language setting

---

## Ops Flows

### Flow 5: Cluster Health Monitoring

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 900px;">
  <div style="background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); padding: 16px 24px; border-bottom: 1px solid #d8b4fe;">
    <div style="font-size: 18px; font-weight: 600; color: #6d28d9;">Cluster Health</div>
    <div style="font-size: 13px; color: #7c3aed; margin-top: 4px;">System health and component status</div>
  </div>
  <div style="padding: 24px;">
    <div style="font-weight: 600; color: #374151; margin-bottom: 12px;">Component Status</div>
    <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px;">
      <div style="border: 1px solid #bbf7d0; background: #f0fdf4; border-radius: 6px; padding: 12px 16px; min-width: 140px;">
        <div style="font-weight: 500; color: #16a34a;">Database</div>
        <div style="font-size: 11px; color: #6b7280;">Connected (5ms)</div>
      </div>
      <div style="border: 1px solid #bbf7d0; background: #f0fdf4; border-radius: 6px; padding: 12px 16px; min-width: 140px;">
        <div style="font-weight: 500; color: #16a34a;">Pub/Sub</div>
        <div style="font-size: 11px; color: #6b7280;">Connected</div>
      </div>
      <div style="border: 1px solid #bbf7d0; background: #f0fdf4; border-radius: 6px; padding: 12px 16px; min-width: 140px;">
        <div style="font-weight: 500; color: #16a34a;">Kubernetes</div>
        <div style="font-size: 11px; color: #6b7280;">Connected</div>
      </div>
      <div style="border: 1px solid #fef08a; background: #fefce8; border-radius: 6px; padding: 12px 16px; min-width: 140px;">
        <div style="font-weight: 500; color: #ca8a04;">Starburst</div>
        <div style="font-size: 11px; color: #6b7280;">Slow (850ms)</div>
      </div>
    </div>
    <div style="font-weight: 600; color: #374151; margin-bottom: 12px;">Instance Summary</div>
    <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px;">
      <div style="border: 1px solid #d1d5db; border-radius: 6px; padding: 12px 16px; min-width: 100px; text-align: center;">
        <div style="font-size: 24px; font-weight: 600; color: #1f2937;">25</div>
        <div style="font-size: 11px; color: #6b7280;">Total</div>
      </div>
      <div style="border: 1px solid #d1d5db; border-radius: 6px; padding: 12px 16px; min-width: 100px; text-align: center;">
        <div style="font-size: 24px; font-weight: 600; color: #16a34a;">20</div>
        <div style="font-size: 11px; color: #6b7280;">Running</div>
      </div>
      <div style="border: 1px solid #d1d5db; border-radius: 6px; padding: 12px 16px; min-width: 100px; text-align: center;">
        <div style="font-size: 24px; font-weight: 600; color: #ca8a04;">2</div>
        <div style="font-size: 11px; color: #6b7280;">Starting</div>
      </div>
      <div style="border: 1px solid #d1d5db; border-radius: 6px; padding: 12px 16px; min-width: 100px; text-align: center;">
        <div style="font-size: 24px; font-weight: 600; color: #dc2626;">2</div>
        <div style="font-size: 11px; color: #6b7280;">Failed</div>
      </div>
    </div>
    <div style="font-weight: 600; color: #374151; margin-bottom: 12px;">Cluster Limits</div>
    <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 16px;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
        <span style="font-size: 13px;">Cluster Capacity</span>
        <span style="font-size: 13px; font-weight: 500;">25 / 50 instances</span>
      </div>
      <div style="background: #e5e7eb; border-radius: 4px; height: 8px;">
        <div style="background: #2563eb; border-radius: 4px; height: 8px; width: 50%;"></div>
      </div>
    </div>
  </div>
</div>

---

### Flow 6: Configuration Management

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 900px;">
  <div style="background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); padding: 16px 24px; border-bottom: 1px solid #d8b4fe;">
    <div style="font-size: 18px; font-weight: 600; color: #6d28d9;">Configuration</div>
  </div>
  <div style="border-bottom: 1px solid #e5e7eb;">
    <div style="display: flex;">
      <div style="padding: 12px 24px; border-bottom: 2px solid #7c3aed; color: #7c3aed; font-weight: 500; cursor: pointer;">Lifecycle</div>
      <div style="padding: 12px 24px; color: #6b7280; cursor: pointer;">Concurrency</div>
      <div style="padding: 12px 24px; color: #6b7280; cursor: pointer;">Schema Browser</div>
      <div style="padding: 12px 24px; color: #6b7280; cursor: pointer;">Maintenance</div>
    </div>
  </div>
  <div style="padding: 24px;">
    <div style="font-weight: 600; color: #374151; margin-bottom: 16px;">Lifecycle Defaults</div>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
      <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 16px;">
        <div style="font-weight: 500; color: #374151; margin-bottom: 12px;">Mapping</div>
        <div style="margin-bottom: 8px;">
          <label style="font-size: 11px; color: #6b7280; display: block; margin-bottom: 4px;">Default TTL</label>
          <select style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;">
            <option>No expiry</option>
          </select>
        </div>
        <div style="margin-bottom: 8px;">
          <label style="font-size: 11px; color: #6b7280; display: block; margin-bottom: 4px;">Inactivity Timeout</label>
          <select style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;">
            <option>30 days</option>
          </select>
        </div>
        <div>
          <label style="font-size: 11px; color: #6b7280; display: block; margin-bottom: 4px;">Max TTL</label>
          <select style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;">
            <option>365 days</option>
          </select>
        </div>
      </div>
      <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 16px;">
        <div style="font-weight: 500; color: #374151; margin-bottom: 12px;">Snapshot</div>
        <div style="margin-bottom: 8px;">
          <label style="font-size: 11px; color: #6b7280; display: block; margin-bottom: 4px;">Default TTL</label>
          <select style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;">
            <option>7 days</option>
          </select>
        </div>
        <div style="margin-bottom: 8px;">
          <label style="font-size: 11px; color: #6b7280; display: block; margin-bottom: 4px;">Inactivity Timeout</label>
          <select style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;">
            <option>3 days</option>
          </select>
        </div>
        <div>
          <label style="font-size: 11px; color: #6b7280; display: block; margin-bottom: 4px;">Max TTL</label>
          <select style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;">
            <option>30 days</option>
          </select>
        </div>
      </div>
      <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 16px;">
        <div style="font-weight: 500; color: #374151; margin-bottom: 12px;">Instance</div>
        <div style="margin-bottom: 8px;">
          <label style="font-size: 11px; color: #6b7280; display: block; margin-bottom: 4px;">Default TTL</label>
          <select style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;">
            <option>24 hours</option>
          </select>
        </div>
        <div style="margin-bottom: 8px;">
          <label style="font-size: 11px; color: #6b7280; display: block; margin-bottom: 4px;">Inactivity Timeout</label>
          <select style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;">
            <option>4 hours</option>
          </select>
        </div>
        <div>
          <label style="font-size: 11px; color: #6b7280; display: block; margin-bottom: 4px;">Max TTL</label>
          <select style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;">
            <option>7 days</option>
          </select>
        </div>
      </div>
    </div>
    <div style="margin-top: 24px; display: flex; justify-content: flex-end; gap: 8px;">
      <button style="padding: 10px 20px; border: 1px solid #d1d5db; border-radius: 6px; background: white; font-size: 13px; cursor: pointer;">Reset to Defaults</button>
      <button style="padding: 10px 20px; border: none; border-radius: 6px; background: #7c3aed; color: white; font-size: 13px; cursor: pointer;">Save Changes</button>
    </div>
  </div>
</div>

---

### Flow 7: Maintenance Mode

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 900px;">
  <div style="background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); padding: 16px 24px; border-bottom: 1px solid #d8b4fe;">
    <div style="font-size: 18px; font-weight: 600; color: #6d28d9;">Configuration</div>
  </div>
  <div style="border-bottom: 1px solid #e5e7eb;">
    <div style="display: flex;">
      <div style="padding: 12px 24px; color: #6b7280; cursor: pointer;">Lifecycle</div>
      <div style="padding: 12px 24px; color: #6b7280; cursor: pointer;">Concurrency</div>
      <div style="padding: 12px 24px; color: #6b7280; cursor: pointer;">Schema Browser</div>
      <div style="padding: 12px 24px; border-bottom: 2px solid #7c3aed; color: #7c3aed; font-weight: 500; cursor: pointer;">Maintenance</div>
    </div>
  </div>
  <div style="padding: 24px;">
    <div style="border: 2px solid #fecaca; background: #fef2f2; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <span style="font-size: 24px;">⚠️</span>
        <div>
          <div style="font-weight: 600; color: #dc2626; font-size: 16px;">Maintenance Mode</div>
          <div style="font-size: 13px; color: #7f1d1d;">When enabled, new resource creation will be blocked</div>
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
          <input type="checkbox" style="width: 20px; height: 20px;">
          <span style="font-weight: 500;">Enable Maintenance Mode</span>
        </label>
      </div>
      <div style="margin-bottom: 16px;">
        <label style="font-size: 11px; color: #6b7280; display: block; margin-bottom: 4px;">Message to display to users</label>
        <textarea style="width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; resize: vertical;" rows="2" placeholder="e.g., Scheduled maintenance until 14:00 UTC"></textarea>
      </div>
      <div style="font-size: 12px; color: #6b7280;">
        <strong>What happens when enabled:</strong>
        <ul style="margin: 8px 0; padding-left: 20px;">
          <li>New mappings, snapshots, and instances cannot be created</li>
          <li>Existing resources remain accessible (read-only operations)</li>
          <li>In-flight operations continue to completion</li>
          <li>Terminate and delete operations are still allowed</li>
        </ul>
      </div>
    </div>
    <div style="display: flex; justify-content: flex-end; gap: 8px;">
      <button style="padding: 10px 20px; border: none; border-radius: 6px; background: #dc2626; color: white; font-size: 13px; cursor: pointer;">Enable Maintenance Mode</button>
    </div>
  </div>
</div>

---

### Flow 8: Export Queue Management

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; max-width: 900px;">
  <div style="background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); padding: 16px 24px; border-bottom: 1px solid #d8b4fe; display: flex; justify-content: space-between; align-items: center;">
    <div>
      <div style="font-size: 18px; font-weight: 600; color: #6d28d9;">Export Queue</div>
      <div style="font-size: 13px; color: #7c3aed; margin-top: 4px;">Snapshot export jobs</div>
    </div>
    <div style="display: flex; gap: 12px;">
      <div style="background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 6px 12px; font-size: 12px;">
        <strong>5</strong> Queued
      </div>
      <div style="background: #dbeafe; border: 1px solid #bfdbfe; border-radius: 6px; padding: 6px 12px; font-size: 12px;">
        <strong>2</strong> Processing
      </div>
      <div style="background: #fee2e2; border: 1px solid #fecaca; border-radius: 6px; padding: 6px 12px; font-size: 12px;">
        <strong>1</strong> Dead Letter
      </div>
    </div>
  </div>
  <div style="padding: 16px 24px; background: #fafafa; border-bottom: 1px solid #e5e7eb; display: flex; gap: 12px; align-items: center;">
    <select style="padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; background: white;">
      <option>All Status</option>
      <option>Queued</option>
      <option>Processing</option>
      <option>Failed</option>
      <option>Dead Letter</option>
    </select>
  </div>
  <div style="padding: 0;">
    <table style="width: 100%; border-collapse: collapse;">
      <thead>
        <tr style="background: #f9fafb; border-bottom: 1px solid #e5e7eb;">
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">SNAPSHOT</th>
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">STATUS</th>
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">ATTEMPTS</th>
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">CREATED</th>
          <th style="text-align: left; padding: 12px 16px; font-weight: 500; color: #6b7280; font-size: 11px;">ACTIONS</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom: 1px solid #f3f4f6;">
          <td style="padding: 12px 16px;"><strong style="color: #2563eb;">Customer Graph - Jan 2025</strong></td>
          <td style="padding: 12px 16px;"><span style="background: #dbeafe; color: #1d4ed8; padding: 2px 8px; border-radius: 4px; font-size: 11px;">Processing</span></td>
          <td style="padding: 12px 16px; color: #6b7280;">1</td>
          <td style="padding: 12px 16px; color: #6b7280;">2 min ago</td>
          <td style="padding: 12px 16px; color: #9ca3af;">—</td>
        </tr>
        <tr style="border-bottom: 1px solid #f3f4f6; background: #fef2f2;">
          <td style="padding: 12px 16px;"><strong style="color: #2563eb;">Transaction Network</strong></td>
          <td style="padding: 12px 16px;"><span style="background: #fee2e2; color: #dc2626; padding: 2px 8px; border-radius: 4px; font-size: 11px;">Failed</span></td>
          <td style="padding: 12px 16px; color: #6b7280;">3</td>
          <td style="padding: 12px 16px; color: #6b7280;">15 min ago</td>
          <td style="padding: 12px 16px;">
            <button style="padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; font-size: 11px; cursor: pointer; margin-right: 4px;">Retry</button>
          </td>
        </tr>
        <tr style="border-bottom: 1px solid #f3f4f6;">
          <td style="padding: 12px 16px;"><strong style="color: #2563eb;">Supply Chain v7</strong></td>
          <td style="padding: 12px 16px;"><span style="background: #fef3c7; color: #b45309; padding: 2px 8px; border-radius: 4px; font-size: 11px;">Queued</span></td>
          <td style="padding: 12px 16px; color: #6b7280;">0</td>
          <td style="padding: 12px 16px; color: #6b7280;">1 min ago</td>
          <td style="padding: 12px 16px;">
            <button style="padding: 4px 12px; border: 1px solid #fecaca; border-radius: 4px; background: #fef2f2; color: #dc2626; font-size: 11px; cursor: pointer;">Cancel</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

---

## Error States

### Maintenance Mode Banner

When maintenance mode is enabled, show a persistent banner on all pages:

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 13px; background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 12px 16px; display: flex; align-items: center; gap: 12px; max-width: 900px;">
  <span style="font-size: 18px;">🔧</span>
  <div>
    <strong style="color: #b45309;">Maintenance Mode Active</strong>
    <span style="color: #92400e;"> — Scheduled maintenance until 14:00 UTC. New resource creation is temporarily disabled.</span>
  </div>
</div>

---

### Concurrency Limit Exceeded

<div style="font-family: system-ui, -apple-system, sans-serif; font-size: 13px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 16px; max-width: 500px;">
  <div style="display: flex; align-items: flex-start; gap: 12px;">
    <span style="font-size: 20px;">⚠️</span>
    <div>
      <div style="font-weight: 600; color: #dc2626; margin-bottom: 4px;">Instance Limit Reached</div>
      <div style="color: #7f1d1d; margin-bottom: 12px;">You have reached your limit of 5 running instances. Terminate an existing instance to create a new one.</div>
      <div style="display: flex; gap: 8px;">
        <button style="padding: 8px 16px; border: 1px solid #d1d5db; border-radius: 6px; background: white; font-size: 13px; cursor: pointer;">View My Instances</button>
      </div>
    </div>
  </div>
</div>

---

## Behavioral Patterns

### Concurrent Editing

**Decision:** Last-write-wins (no conflict detection).

When multiple users edit the same resource (e.g., mapping header) simultaneously:

| Scenario | Behavior |
|----------|----------|
| User A saves, then User B saves | User B's changes overwrite User A's |
| User A viewing stale data | No automatic refresh; User A sees their version until they reload |
| User A saves after User B | User A's save succeeds; User B's changes are lost |

**Rationale:**
- Acceptable for internal tool with small user base
- Reduces complexity (no locking, no conflict resolution UI)
- Mapping edits are infrequent and typically by single owner
- Users can coordinate verbally if needed

**Future consideration:** If conflicts become problematic, implement optimistic locking with "Resource was modified by another user. Reload to see changes." error on save.

---

### Session Timeout

**Decision:** Redirect to SSO on session expiry; unsaved work is lost.

Session is managed by the enterprise SSO provider (e.g., Ping, Okta). The web UI does not implement its own session management.

**Timeout Behavior:**

| Event | Behavior |
|-------|----------|
| Session expires | Next API call returns 401 Unauthorized |
| 401 received | UI redirects to SSO login page |
| After re-auth | User returns to the same URL they were on |
| Unsaved form data | Lost (no draft persistence) |

**No Pre-Timeout Warning:**
- SSO session length is controlled by enterprise policy (typically 8-12 hours)
- Web UI does not track session expiry time
- Users are not warned before timeout

**Rationale:**
- Consistent with other internal enterprise tools
- Simplifies implementation (no client-side session tracking)
- Long session times (8+ hours) make mid-work expiry rare
- Mapping creation is typically quick (<10 minutes)

---

## Related Documents

- [ux.components.spec.md](./ux.components.spec.md) - Component specifications
- [ux.copy.spec.md](./ux.copy.spec.md) - UI copy and messaging
- [decision.log.md](../process/decision.log.md) - ADR-006 through ADR-017

---

## Change History

| Date | Change |
|------|--------|
| 2025-12-12 | Initial creation with page inventory, navigation, and core flows |
