# Admin Operations

## Bulk Delete Safety Mechanisms

![safety-mechanisms](diagrams/admin-operations/safety-mechanisms.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Bulk Delete Safety Mechanisms
    accDescr: Shows the four safety mechanisms that protect against accidental bulk deletions

    classDef safety fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef danger fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef info fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1

    subgraph SafetyMechanisms["Four Safety Mechanisms"]
        direction TB
        S1["1. Admin Role Required<br/>403 for non-admins"]:::safety
        S2["2. Filter Required<br/>Cannot delete ALL"]:::safety
        S3["3. Expected Count<br/>Validates match count"]:::safety
        S4["4. Max 100 Limit<br/>Hard cap per operation"]:::safety
    end

    REQ([Bulk Delete Request]):::info --> S1
    S1 -->|Pass| S2
    S2 -->|Pass| S3
    S3 -->|Pass| S4
    S4 -->|Pass| EXEC["Execute Deletions"]:::danger

    S1 -->|Fail| REJECT1["403 Forbidden"]:::danger
    S2 -->|Fail| REJECT2["400 Bad Request<br/>(no filter)"]:::danger
    S3 -->|Fail| REJECT3["400 Bad Request<br/>(count mismatch)"]:::danger
    S4 -->|Fail| REJECT4["400 Bad Request<br/>(>100 matches)"]:::danger
```

</details>

## Bulk Delete Workflow

![bulk-delete-workflow](diagrams/admin-operations/bulk-delete-workflow.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
sequenceDiagram
    accTitle: Bulk Delete Workflow
    accDescr: Shows the recommended workflow for safely executing bulk deletions

    participant Admin as Admin User
    participant API as Control Plane API
    participant DB as Database

    Note over Admin,DB: Step 1: Preview with Dry Run

    Admin->>API: bulk_delete(dry_run=true)
    API->>DB: Query matching resources
    DB-->>API: 5 resources matched
    API-->>Admin: {matched_count: 5, matched_ids: [...]}

    Note over Admin,DB: Step 2: Verify and Confirm

    Admin->>Admin: Review matched_ids
    Admin->>Admin: Confirm expected_count=5

    Note over Admin,DB: Step 3: Execute with Safety

    Admin->>API: bulk_delete(dry_run=false, expected_count=5)
    API->>DB: Verify count still matches
    alt Count matches
        API->>DB: Delete each resource
        DB-->>API: Deleted
        API-->>Admin: {deleted_count: 5, failed_ids: []}
    else Count changed
        API-->>Admin: 400 Error (count mismatch)
    end
```

</details>

## Filter Types

![filter-types](diagrams/admin-operations/filter-types.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Bulk Delete Filter Types
    accDescr: Shows the available filters for targeting resources in bulk delete operations

    classDef filter fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef example fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef resource fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20

    subgraph Filters["Available Filters"]
        direction TB
        F1["name_prefix<br/>(string match)"]:::filter
        F2["status<br/>(exact match)"]:::filter
        F3["created_by<br/>(user filter)"]:::filter
    end

    subgraph Examples["Example Values"]
        direction TB
        E1["'test-', 'dev-',<br/>'cleanup-'"]:::example
        E2["'pending', 'failed',<br/>'terminated'"]:::example
        E3["'analyst_alice@e2e.local',<br/>'system'"]:::example
    end

    subgraph Resources["Target Resources"]
        direction TB
        R1["Instances"]:::resource
        R2["Snapshots"]:::resource
        R3["Mappings"]:::resource
    end

    F1 --> E1
    F2 --> E2
    F3 --> E3

    Filters --> Resources
```

</details>

## Role Access Matrix

![role-access](diagrams/admin-operations/role-access.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Admin Operations Role Access
    accDescr: Shows which roles can access admin bulk operations

    classDef admin fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef ops fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef analyst fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef allowed fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef denied fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C

    subgraph AdminOps["Admin Operations"]
        direction TB
        OP1["Bulk Delete<br/>Instances"]
        OP2["Bulk Delete<br/>Snapshots"]
        OP3["Bulk Delete<br/>Mappings"]
        OP4["Force Retry<br/>Failed Exports"]
    end

    ADMIN[["Admin<br/>(Carol)"]]:::admin
    OPS[["Ops<br/>(Dave)"]]:::ops
    ANALYST[["Analyst<br/>(Alice)"]]:::analyst

    ADMIN -->|"✓ Full Access"| AdminOps
    OPS -->|"✗ 403 Forbidden"| AdminOps
    ANALYST -->|"✗ 403 Forbidden"| AdminOps

    style OP1 fill:#F3E5F5,stroke:#7B1FA2,color:#4A148C
    style OP2 fill:#F3E5F5,stroke:#7B1FA2,color:#4A148C
    style OP3 fill:#F3E5F5,stroke:#7B1FA2,color:#4A148C
    style OP4 fill:#F3E5F5,stroke:#7B1FA2,color:#4A148C
```

</details>

## Response Structure

![response-structure](diagrams/admin-operations/response-structure.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Bulk Delete Response Structure
    accDescr: Shows the fields returned by bulk delete operations

    classDef field fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef success fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef error fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C

    subgraph Response["BulkDeleteResponse"]
        direction TB
        F1["dry_run: boolean"]:::field
        F2["matched_count: int"]:::field
        F3["matched_ids: list"]:::field
        F4["deleted_count: int"]:::success
        F5["deleted_ids: list"]:::success
        F6["failed_ids: list"]:::error
        F7["errors: dict"]:::error
    end

    subgraph DryRun["Dry Run Mode"]
        DR1["matched_count = 5"]
        DR2["deleted_count = 0"]
        DR3["Preview only"]
    end

    subgraph RealRun["Real Execution"]
        RR1["matched_count = 5"]
        RR2["deleted_count = 5"]
        RR3["Resources deleted"]
    end

    Response --> DryRun
    Response --> RealRun
```

</details>


