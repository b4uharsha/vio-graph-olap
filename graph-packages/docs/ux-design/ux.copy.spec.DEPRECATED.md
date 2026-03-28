# UI Copy Specification

> **DEPRECATED** - This document is no longer maintained.
>
> The Graph OLAP Platform no longer includes a web interface. All user interaction
> is now through the Jupyter SDK. This document is retained for historical reference.
>
> See [jupyter-sdk.design.md](../component-designs/jupyter-sdk.design.md) for the current user interface design.

## Overview

This document defines all user-facing text, error messages, labels, and help text for the Graph OLAP Platform web interface. All copy follows the internationalization (i18n) strategy defined in ADR-015.

**Prerequisites:**
- [ux.flows.md](./ux.flows.md) - User journeys and page structure
- [ux.components.spec.md](./ux.components.spec.md) - Component specifications
- [api.common.spec.md](../system-design/api.common.spec.md) - Error codes reference
- [requirements.md](../foundation/requirements.md) - Error message templates (lines 1028-1056)

---

## i18n Strategy (ADR-015)

### Bundle Structure

```
locales/
├── en/
│   ├── common.json      # Shared labels, buttons, navigation
│   ├── errors.json      # Error messages
│   ├── mappings.json    # Mapping-specific copy
│   ├── snapshots.json   # Snapshot-specific copy
│   ├── instances.json   # Instance-specific copy
│   └── ops.json         # Operations section copy
└── zh-CN/
    ├── common.json
    ├── errors.json
    ├── mappings.json
    ├── snapshots.json
    ├── instances.json
    └── ops.json
```

### Supported Languages

| Locale | Language | Coverage | Notes |
|--------|----------|----------|-------|
| en | English | Complete | Default, fallback for missing keys |
| zh-CN | Simplified Chinese | Complete | Primary user base |

### Locale Detection

1. User preference (stored in browser localStorage)
2. Browser `Accept-Language` header
3. Default: English (en)

### Fallback Chain

```
zh-CN key → en key → Key name (development only)
```

### Placeholder Syntax

```
"message": "Hello, {username}!"
"count": "You have {count, plural, =0 {no items} =1 {1 item} other {{count} items}}"
```

### Chinese Translation Guidelines

- **Placeholder spacing:** Always include a space after placeholders before Chinese text
  - Correct: `{field} 是必填项`
  - Incorrect: `{field}是必填项`
- **No space needed** before placeholders or between Chinese characters

### What's Internationalized

- Navigation labels
- Button text
- Form labels and placeholders
- Error messages
- Help text and tooltips
- Empty state messages
- Status labels
- Confirmation dialogs

### What's NOT Internationalized

- User-generated content (mapping names, descriptions)
- Data values from Starburst
- Log messages (English only for ops/debugging)
- API error codes (codes are universal, messages are i18n)

### Key Naming Conventions

All keys use dot-notation with consistent prefixes:

| Prefix | Usage |
|--------|-------|
| `nav.*` | Navigation labels |
| `page.*` | Page titles |
| `btn.*` | Button labels |
| `field.*` | Form field labels |
| `error.*` | Error messages (validation, page-level errors) |
| `toast.*` | Toast messages (success, info, warning) |
| `toast.error.*` | Toast error messages |
| `help.*` | Help text and tooltips |
| `status.*` | Status labels |

---

## Navigation Labels

### Primary Navigation

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| nav.dashboard | Dashboard | 仪表盘 |
| nav.mappings | Mappings | 映射 |
| nav.snapshots | Snapshots | 快照 |
| nav.instances | Instances | 实例 |
| nav.favorites | Favorites | 收藏 |

### Ops Section Navigation

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| nav.ops | Operations | 运维 |
| nav.ops.health | Cluster Health | 集群健康 |
| nav.ops.config | Configuration | 配置 |
| nav.ops.exports | Export Queue | 导出队列 |

### User Menu

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| user.menu | User Menu | 用户菜单 |
| user.preferences | Preferences | 偏好设置 |
| user.language | Language | 语言 |
| user.logout | Sign Out | 退出登录 |

---

## Page Titles

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| page.dashboard | Dashboard | 仪表盘 |
| page.mappings | Mappings | 映射列表 |
| page.mappings.create | Create Mapping | 创建映射 |
| page.mappings.detail | Mapping Details | 映射详情 |
| page.snapshots | Snapshots | 快照列表 |
| page.snapshots.detail | Snapshot Details | 快照详情 |
| page.instances | Instances | 实例列表 |
| page.instances.detail | Instance Details | 实例详情 |
| page.favorites | Favorites | 我的收藏 |
| page.compare | Compare Mappings | 对比映射 |
| page.ops.health | Cluster Health | 集群健康 |
| page.ops.config | Configuration | 系统配置 |
| page.ops.exports | Export Queue | 导出队列 |

---

## Button Labels

### Action Buttons

| Key | English | Chinese (zh-CN) | Context |
|-----|---------|-----------------|---------|
| btn.create | Create | 创建 | Primary action |
| btn.save | Save | 保存 | Form submission |
| btn.cancel | Cancel | 取消 | Cancel action |
| btn.delete | Delete | 删除 | Destructive action |
| btn.edit | Edit | 编辑 | Modify resource |
| btn.copy | Copy | 复制 | Duplicate resource |
| btn.close | Close | 关闭 | Close panel/dialog |
| btn.retry | Retry | 重试 | Retry failed action |
| btn.refresh | Refresh | 刷新 | Refresh data |

### Clipboard Actions

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| btn.copyToClipboard | Copy | 复制 |
| btn.copied | Copied! | 已复制! |
| btn.copyFailed | Failed | 复制失败 |

### Resource-Specific Actions

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| btn.createMapping | Create Mapping | 创建映射 |
| btn.newVersion | Create New Version | 创建新版本 |
| btn.createSnapshot | Create Snapshot | 创建快照 |
| btn.launchInstance | Launch Instance | 启动实例 |
| btn.terminate | Terminate | 终止 |
| btn.forceTerminate | Force Terminate | 强制终止 |
| btn.compare | Compare | 对比 |
| btn.validateSql | Validate SQL | 验证 SQL |
| btn.addNode | Add Node | 添加节点 |
| btn.addEdge | Add Edge | 添加边 |

### Filter/Sort Actions

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| btn.filter | Filter | 筛选 |
| btn.clearFilters | Clear Filters | 清除筛选 |
| btn.sortBy | Sort by | 排序 |
| btn.showFavorites | Favorites Only | 仅显示收藏 |

---

## Form Labels

### Common Fields

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| field.name | Name | 名称 |
| field.description | Description | 描述 |
| field.owner | Owner | 所有者 |
| field.createdAt | Created | 创建时间 |
| field.updatedAt | Updated | 更新时间 |
| field.status | Status | 状态 |
| field.lifecycle | Lifecycle | 生命周期 |
| field.expiresAt | Expires | 过期时间 |

### Mapping Fields

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| mapping.name | Mapping Name | 映射名称 |
| mapping.version | Version | 版本 |
| mapping.nodeDefinitions | Node Definitions | 节点定义 |
| mapping.edgeDefinitions | Edge Definitions | 边定义 |
| mapping.sql | SQL Query | SQL 查询 |
| mapping.label | Node Label | 节点标签 |
| mapping.edgeType | Edge Type | 边类型 |
| mapping.primaryKey | Primary Key | 主键 |
| mapping.sourceNode | Source Node | 源节点 |
| mapping.targetNode | Target Node | 目标节点 |
| mapping.properties | Properties | 属性 |

### Snapshot Fields

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| snapshot.mapping | Source Mapping | 源映射 |
| snapshot.version | Mapping Version | 映射版本 |
| snapshot.nodeCount | Nodes | 节点数 |
| snapshot.edgeCount | Edges | 边数 |
| snapshot.size | Size | 大小 |

### Instance Fields

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| instance.snapshot | Source Snapshot | 源快照 |
| instance.endpoint | Endpoint | 端点 |
| instance.locked | Locked | 已锁定 |
| instance.lockedBy | Locked By | 锁定者 |
| instance.algorithm | Algorithm | 算法 |

### Lifecycle Fields

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| lifecycle.ttl | Time to Live | 存活时间 |
| lifecycle.inactivityTimeout | Inactivity Timeout | 闲置超时 |
| lifecycle.inherited | Inherited | 继承 |
| lifecycle.custom | Custom | 自定义 |

---

## Status Labels

**Note:** For status badge colors, see [ux.components.spec.md](./ux.components.spec.md#status-badge) (authoritative source for visual styling).

### Resource Status

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| status.draft | Draft | 草稿 |
| status.active | Active | 活跃 |
| status.archived | Archived | 已归档 |

### Snapshot Status

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| status.pending | Queued | 排队中 |
| status.creating | Creating | 创建中 |
| status.ready | Ready | 就绪 |
| status.failed | Failed | 失败 |
| status.expired | Expired | 已过期 |

### Instance Status

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| status.starting | Starting | 启动中 |
| status.running | Running | 运行中 |
| status.stopping | Stopping | 停止中 |
| status.stopped | Stopped | 已停止 |
| status.failed | Failed | 失败 |

### Algorithm Status

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| status.algo.running | Running | 运行中 |
| status.algo.completed | Completed | 已完成 |
| status.algo.failed | Failed | 失败 |

---

## Progress Messages

### Snapshot Creation Progress

| Phase | Key | English | Chinese (zh-CN) |
|-------|-----|---------|-----------------|
| pending | progress.snapshot.queued | Queued | 排队等待中 |
| creating (nodes) | progress.snapshot.exportingNodes | Exporting nodes | 正在导出节点 |
| creating (edges) | progress.snapshot.exportingEdges | Exporting edges | 正在导出边 |
| ready | progress.snapshot.complete | Complete | 导出完成 |
| failed | progress.snapshot.failed | Export failed | 导出失败 |

**Detail Templates:**

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| progress.snapshot.queuePosition | Position {position} in queue | 队列位置: 第 {position} 位 |
| progress.snapshot.exportingTable | Exporting {table}... | 正在导出 {table}... |
| progress.snapshot.tableComplete | {table}: {rows} rows | {table}: {rows} 行 |

### Instance Startup Progress

| Phase | Key | English | Chinese (zh-CN) |
|-------|-----|---------|-----------------|
| init | progress.instance.init | Initializing | 正在初始化 |
| schema | progress.instance.schema | Creating schema | 正在创建架构 |
| loading nodes | progress.instance.loadingNodes | Loading nodes | 正在加载节点 |
| loading edges | progress.instance.loadingEdges | Loading edges | 正在加载边 |
| running | progress.instance.ready | Ready | 已就绪 |
| failed | progress.instance.failed | Startup failed | 启动失败 |

**Detail Templates:**

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| progress.instance.scheduling | Scheduling pod... | 正在调度 Pod... |
| progress.instance.loadingTable | Loading {table}... | 正在加载 {table}... |
| progress.instance.stats | {nodes} nodes, {edges} edges | {nodes} 个节点, {edges} 条边 |

### Algorithm Execution Progress

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| progress.algo.running | Running {algorithm} | 正在运行 {algorithm} |
| progress.algo.elapsed | Elapsed: {duration} | 已用时: {duration} |
| progress.algo.startedBy | Started by {user} | 由 {user} 启动 |
| progress.algo.completed | Completed in {duration} | 完成, 耗时 {duration} |

---

## Error Messages

### Validation Errors (400)

| Code | Key | English | Chinese (zh-CN) |
|------|-----|---------|-----------------|
| VALIDATION_FAILED | error.validation.generic | Invalid input: {details} | 输入无效: {details} |
| - | error.validation.required | {field} is required | {field} 是必填项 |
| - | error.validation.tooLong | {field} must be {max} characters or less | {field} 不能超过 {max} 个字符 |
| - | error.validation.invalidFormat | {field} format is invalid | {field} 格式无效 |
| - | error.validation.sqlInvalid | SQL syntax error: {details} | SQL 语法错误: {details} |
| - | error.validation.pkNotFirst | Primary key column must be first in SELECT | 主键列必须在 SELECT 中排第一位 |
| - | error.validation.fkNotFirst | Foreign key columns must be first two in SELECT | 外键列必须在 SELECT 中排前两位 |

### Authentication/Authorization Errors (401/403)

| Code | Key | English | Chinese (zh-CN) |
|------|-----|---------|-----------------|
| UNAUTHORIZED | error.auth.unauthorized | Please sign in to continue | 请登录后继续 |
| PERMISSION_DENIED | error.auth.notOwner | You don't have permission to modify this {resource}. It belongs to {owner}. | 您没有权限修改此{resource}。它属于 {owner}。 |
| PERMISSION_DENIED | error.auth.roleRequired | This action requires {role} permissions. Contact an admin if you need access. | 此操作需要 {role} 权限。如需访问请联系管理员。 |

### Not Found Errors (404)

| Code | Key | English | Chinese (zh-CN) |
|------|-----|---------|-----------------|
| RESOURCE_NOT_FOUND | error.notFound.generic | The requested {resource} could not be found | 未找到请求的{resource} |
| MAPPING_VERSION_NOT_FOUND | error.notFound.version | Version {version} of this mapping does not exist | 此映射的版本 {version} 不存在 |
| ALGORITHM_NOT_FOUND | error.notFound.algorithm | Algorithm "{name}" is not available | 算法 "{name}" 不可用 |
| EXECUTION_NOT_FOUND | error.notFound.execution | Algorithm execution not found | 未找到算法执行记录 |

### Conflict Errors (409)

| Code | Key | English | Chinese (zh-CN) |
|------|-----|---------|-----------------|
| RESOURCE_LOCKED | error.conflict.locked | This instance is currently running algorithm "{algorithm}" started by {user} at {time}. Try again when it completes. | 此实例正在运行 "{algorithm}" 算法 (由 {user} 于 {time} 启动)。请等待完成后重试。 |
| CONCURRENCY_LIMIT_EXCEEDED | error.conflict.limitReached | You've reached your limit of {current}/{max} running instances. Terminate an existing instance to create a new one. | 您已达到运行实例上限 ({current}/{max})。请先终止现有实例后再创建新实例。 |
| RESOURCE_HAS_DEPENDENCIES | error.conflict.hasDependencies | Cannot delete this {resource}. It has {count} {dependentType}(s) that must be deleted first. | 无法删除此{resource}。请先删除关联的 {count} 个{dependentType}。 |
| SNAPSHOT_NOT_READY | error.conflict.snapshotNotReady | Cannot use this snapshot. It is still being created or has failed. | 无法使用此快照。它仍在创建中或已失败。 |
| INVALID_STATE | error.conflict.invalidState | This operation is not available in the current state | 当前状态下无法执行此操作 |
| ALREADY_EXISTS | error.conflict.alreadyExists | A {resource} with this name already exists | 已存在同名的{resource} |

### Timeout Errors (408)

| Code | Key | English | Chinese (zh-CN) |
|------|-----|---------|-----------------|
| QUERY_TIMEOUT | error.timeout.query | Query timed out after {duration}. Try a simpler query or add filters. | 查询超时 ({duration})。请尝试简化查询或添加过滤条件。 |

### Server Errors (500/503)

| Code | Key | English | Chinese (zh-CN) |
|------|-----|---------|-----------------|
| STARBURST_ERROR | error.external.starburst | Unable to connect to the data warehouse. This is usually temporary. Try again in a few minutes. | 无法连接数据仓库。这通常是暂时性的，请稍后重试。 |
| RYUGRAPH_ERROR | error.external.ryugraph | Graph database error. Try again or contact support if the problem persists. | 图数据库错误。请重试，如问题持续请联系支持。 |
| GCS_ERROR | error.external.gcs | Unable to access storage. This is usually temporary. Try again in a few minutes. | 无法访问存储。这通常是暂时性的，请稍后重试。 |
| SERVICE_UNAVAILABLE | error.maintenance | The system is currently in maintenance mode. Please try again later. | 系统正在维护中，请稍后重试。 |

### Generic Errors

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| error.generic | Something went wrong. Please try again. | 出了点问题，请重试。 |
| error.network | Unable to connect. Check your network connection. | 无法连接，请检查网络。 |
| error.unexpected | An unexpected error occurred. (Code: {code}) | 发生意外错误。(错误代码: {code}) |

---

## Help Text & Guidance

### Field Descriptions

| Field | Key | English | Chinese (zh-CN) |
|-------|-----|---------|-----------------|
| Mapping name | help.mapping.name | A unique name for this mapping. Use lowercase letters, numbers, and hyphens. | 映射的唯一名称。请使用小写字母、数字和连字符。 |
| Mapping description | help.mapping.description | Optional description to help others understand this mapping's purpose. | 可选描述，帮助他人理解此映射的用途。 |
| Node SQL | help.mapping.nodeSql | SQL query to extract nodes. First column must be the primary key. | 提取节点的 SQL 查询。第一列必须是主键。 |
| Edge SQL | help.mapping.edgeSql | SQL query to extract edges. First two columns must be source and target keys. | 提取边的 SQL 查询。前两列必须是源键和目标键。 |
| Node label | help.mapping.nodeLabel | Label to identify this node type in the graph (e.g., "Person", "Account"). | 图中标识此节点类型的标签 (如 "Person"、"Account")。 |
| Edge type | help.mapping.edgeType | Type name for this relationship (e.g., "OWNS", "TRANSFERRED_TO"). | 此关系的类型名称 (如 "OWNS"、"TRANSFERRED_TO")。 |
| Lifecycle TTL | help.lifecycle.ttl | Maximum time this resource will exist before automatic cleanup. | 此资源在自动清理前的最长存在时间。 |
| Inactivity timeout | help.lifecycle.inactivity | Resource will be cleaned up after this period of no activity. | 在此时间段内无活动后，资源将被清理。 |

### Schema Browser Help

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| help.schemaBrowser.title | Schema Browser | 模式浏览器 |
| help.schemaBrowser.description | Browse available catalogs, schemas, and tables. Click a table name to see its columns. | 浏览可用的目录、模式和表。点击表名查看其列。 |
| help.schemaBrowser.search | Type to filter tables... | 输入以过滤表... |
| help.schemaBrowser.empty | No tables match your search | 没有匹配的表 |

### SQL Editor Help

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| help.sql.validate | Validate SQL to check for errors and infer schema | 验证 SQL 以检查错误并推断模式 |
| help.sql.columnOrder | Column order matters: primary key first for nodes, source/target keys first for edges | 列顺序很重要：节点主键需排第一，边的源/目标键需排前两位 |
| help.sql.typeWarning | Some column types may need casting. See warnings after validation. | 某些列类型可能需要转换。验证后查看警告。 |

---

## Empty States

### Resource Lists

| Context | Key | English | Chinese (zh-CN) |
|---------|-----|---------|-----------------|
| No mappings | empty.mappings | No mappings yet | 暂无映射 |
| No snapshots | empty.snapshots | No snapshots yet | 暂无快照 |
| No instances | empty.instances | No running instances | 暂无运行中的实例 |
| No favorites | empty.favorites | No favorites yet | 暂无收藏 |
| Search no results | empty.search | No results match your search | 没有匹配的搜索结果 |
| Filter no results | empty.filter | No items match the selected filters | 没有匹配所选筛选条件的项目 |

### Empty State Guidance

| Context | Key | English | Chinese (zh-CN) |
|---------|-----|---------|-----------------|
| No mappings (Analyst) | empty.mappings.cta | Create your first mapping to get started | 创建您的第一个映射以开始 |
| No snapshots | empty.snapshots.cta | Create a snapshot from a mapping to export data | 从映射创建快照以导出数据 |
| No instances | empty.instances.cta | Launch an instance from a snapshot to run queries | 从快照启动实例以运行查询 |
| No favorites | empty.favorites.cta | Star your frequently used resources for quick access | 收藏常用资源以便快速访问 |

---

## Confirmations

### Delete Confirmations (Inline)

| Resource | Key | English | Chinese (zh-CN) |
|----------|-----|---------|-----------------|
| Mapping | confirm.delete.mapping | Delete mapping "{name}"? This will delete all versions. Snapshots and instances will be preserved. | 删除映射 "{name}"？这将删除所有版本。快照和实例将保留。 |
| Snapshot | confirm.delete.snapshot | Delete snapshot "{name}"? | 删除快照 "{name}"？ |
| Instance | confirm.terminate.instance | Terminate instance "{name}"? The graph data will be lost. | 终止实例 "{name}"？图数据将丢失。 |
| Instance (force) | confirm.forceTerminate | Force terminate instance "{name}"? This will immediately stop the instance even if an algorithm is running. | 强制终止实例 "{name}"？即使算法正在运行也会立即停止实例。 |

### Bulk Operation Confirmations

| Action | Key | English | Chinese (zh-CN) |
|--------|-----|---------|-----------------|
| Terminate multiple | confirm.bulk.terminate | Terminate {count} instances? The graph data will be lost. | 终止 {count} 个实例？图数据将丢失。 |
| Delete multiple | confirm.bulk.delete | Delete {count} {resource}? | 删除 {count} 个{resource}？ |
| Favorite multiple | confirm.bulk.favorite | Add {count} items to favorites? | 将 {count} 个项目添加到收藏？ |
| Unfavorite multiple | confirm.bulk.unfavorite | Remove {count} items from favorites? | 将 {count} 个项目从收藏中移除？ |

### Confirmation Buttons

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| confirm.yes | Yes, delete | 是，删除 |
| confirm.yesTerminate | Yes, terminate | 是，终止 |
| confirm.no | Cancel | 取消 |

---

## Toast Notifications

**Auto-dismiss durations** (see [ux.components.spec.md](./ux.components.spec.md) for visual spec):

| Type | Duration |
|------|----------|
| Success | 5 seconds |
| Info | 5 seconds |
| Warning | 10 seconds |
| Error | Manual dismiss only |

### Success Messages

| Action | Key | English | Chinese (zh-CN) |
|--------|-----|---------|-----------------|
| Create | toast.success.created | {resource} created successfully | {resource}创建成功 |
| Update | toast.success.updated | {resource} updated successfully | {resource}更新成功 |
| Delete | toast.success.deleted | {resource} deleted | {resource}已删除 |
| Copy | toast.success.copied | {resource} copied | {resource}已复制 |
| Terminate | toast.success.terminated | Instance terminated | 实例已终止 |
| Favorite | toast.success.favorited | Added to favorites | 已添加到收藏 |
| Unfavorite | toast.success.unfavorited | Removed from favorites | 已从收藏移除 |

### Info Messages

| Context | Key | English | Chinese (zh-CN) |
|---------|-----|---------|-----------------|
| Snapshot queued | toast.info.snapshotQueued | Snapshot creation started. You can track progress on the Snapshots page. | 快照创建已开始。您可以在快照页面跟踪进度。 |
| Instance starting | toast.info.instanceStarting | Instance is starting. This may take a few minutes. | 实例正在启动，可能需要几分钟。 |
| Algorithm started | toast.info.algorithmStarted | {algorithm} started. The instance is locked until it completes. | {algorithm} 已启动。实例在完成前处于锁定状态。 |

### Warning Messages

| Context | Key | English | Chinese (zh-CN) |
|---------|-----|---------|-----------------|
| Lifecycle warning | toast.warning.expiressSoon | This {resource} expires in {time} | 此{resource}将在 {time} 后过期 |
| SQL changed | toast.warning.sqlChanged | SQL has been modified. Please validate again. | SQL 已修改，请重新验证。 |
| Schema reset | toast.warning.schemaReset | Schema customizations have been reset due to column changes. | 由于列变更，架构自定义已重置。 |

### Error Messages

| Context | Key | English | Chinese (zh-CN) |
|---------|-----|---------|-----------------|
| Generic error | toast.error.generic | Operation failed. Please try again. | 操作失败，请重试。 |
| Network error | toast.error.network | Connection lost. Check your network. | 连接丢失，请检查网络。 |

---

## Bulk Operation Results

### Success Summary

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| bulk.success.all | All {count} items processed successfully | 全部 {count} 个项目处理成功 |
| bulk.success.partial | {success} of {total} items processed. {failed} failed. | {success}/{total} 个项目已处理。{failed} 个失败。 |

### Failure Details

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| bulk.failed.dependency | {name}: Has dependent resources | {name}: 存在依赖资源 |
| bulk.failed.permission | {name}: Permission denied | {name}: 权限不足 |
| bulk.failed.notFound | {name}: Not found (may have been deleted) | {name}: 未找到 (可能已被删除) |
| bulk.failed.locked | {name}: Instance is locked | {name}: 实例已锁定 |

---

## Ops Section Copy

### Cluster Health

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| ops.health.title | Cluster Health | 集群健康 |
| ops.health.status.healthy | All systems operational | 所有系统正常运行 |
| ops.health.status.degraded | Some systems experiencing issues | 部分系统存在问题 |
| ops.health.status.down | System outage detected | 检测到系统故障 |
| ops.health.component.controlPlane | Control Plane | 控制平面 |
| ops.health.component.database | Database | 数据库 |
| ops.health.component.starburst | Starburst | Starburst |
| ops.health.component.gcs | Cloud Storage | 云存储 |
| ops.health.component.pubsub | Message Queue | 消息队列 |

### Configuration

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| ops.config.title | Configuration | 配置 |
| ops.config.lifecycle | Lifecycle Defaults | 生命周期默认值 |
| ops.config.concurrency | Concurrency Limits | 并发限制 |
| ops.config.schema | Schema Configuration | 模式配置 |
| ops.config.maintenance | Maintenance Mode | 维护模式 |

### Maintenance Mode

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| ops.maintenance.enable | Enable Maintenance Mode | 启用维护模式 |
| ops.maintenance.disable | Disable Maintenance Mode | 停用维护模式 |
| ops.maintenance.status.enabled | Maintenance mode is enabled | 维护模式已启用 |
| ops.maintenance.status.disabled | Maintenance mode is disabled | 维护模式已停用 |
| ops.maintenance.warning | While enabled, users cannot create new mappings, snapshots, or instances. | 启用期间，用户无法创建新的映射、快照或实例。 |
| ops.maintenance.activeNotice | System is in maintenance mode. Creating new resources is temporarily disabled. | 系统正在维护中，暂时无法创建新资源。 |

### Export Queue

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| ops.exports.title | Export Queue | 导出队列 |
| ops.exports.pending | Pending | 等待中 |
| ops.exports.processing | Processing | 处理中 |
| ops.exports.completed | Completed | 已完成 |
| ops.exports.failed | Failed | 失败 |
| ops.exports.retry | Retry Export | 重试导出 |
| ops.exports.cancel | Cancel Export | 取消导出 |

**Note:** Audit logs are accessed via the company's external observability stack, not in this UI.

---

## Timestamps & Durations

### Relative Time

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| time.justNow | Just now | 刚刚 |
| time.minutesAgo | {count} minute ago | {count} 分钟前 |
| time.minutesAgo_plural | {count} minutes ago | {count} 分钟前 |
| time.hoursAgo | {count} hour ago | {count} 小时前 |
| time.hoursAgo_plural | {count} hours ago | {count} 小时前 |
| time.yesterday | Yesterday | 昨天 |
| time.daysAgo | {count} day ago | {count} 天前 |
| time.daysAgo_plural | {count} days ago | {count} 天前 |

### Duration Format

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| duration.days | {count}d | {count}天 |
| duration.hours | {count}h | {count}小时 |
| duration.minutes | {count}m | {count}分钟 |
| duration.seconds | {count}s | {count}秒 |

---

## Accessibility Labels

### ARIA Labels

| Key | English | Chinese (zh-CN) |
|-----|---------|-----------------|
| aria.nav.main | Main navigation | 主导航 |
| aria.nav.user | User menu | 用户菜单 |
| aria.btn.close | Close | 关闭 |
| aria.btn.expand | Expand | 展开 |
| aria.btn.collapse | Collapse | 收起 |
| aria.btn.favorite | Add to favorites | 添加到收藏 |
| aria.btn.unfavorite | Remove from favorites | 从收藏移除 |
| aria.table.sortAsc | Sort ascending | 升序排列 |
| aria.table.sortDesc | Sort descending | 降序排列 |
| aria.loading | Loading | 加载中 |
| aria.required | Required field | 必填字段 |

---

## Change History

| Date | Change |
|------|--------|
| 2025-12-12 | Initial version with complete i18n copy specifications |
