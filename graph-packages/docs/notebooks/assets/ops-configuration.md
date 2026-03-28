# Ops Configuration

## Ops Role Overview

![ops-role](diagrams/ops-configuration/ops-role.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Ops Role Overview
    accDescr: Shows the Ops role capabilities for platform configuration and monitoring

    classDef ops fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef config fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef cluster fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef jobs fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    OPS[["Ops Role<br/>(Dave)"]]:::ops

    subgraph ConfigAPIs["Configuration Management"]
        direction TB
        C1["Lifecycle Config<br/>(TTL settings)"]:::config
        C2["Concurrency Config<br/>(limits)"]:::config
        C3["Maintenance Mode<br/>(enable/disable)"]:::config
        C4["Export Config<br/>(timeouts)"]:::config
    end

    subgraph ClusterAPIs["Cluster Monitoring"]
        direction TB
        CL1["Cluster Health<br/>(component status)"]:::cluster
        CL2["Cluster Instances<br/>(counts & capacity)"]:::cluster
        CL3["Prometheus Metrics<br/>(raw export)"]:::cluster
    end

    subgraph JobAPIs["Background Jobs"]
        direction TB
        J1["Trigger Jobs<br/>(manual execution)"]:::jobs
        J2["Job Status<br/>(running/last run)"]:::jobs
        J3["System State<br/>(counts & health)"]:::jobs
        J4["Export Jobs<br/>(queue management)"]:::jobs
    end

    OPS --> ConfigAPIs
    OPS --> ClusterAPIs
    OPS --> JobAPIs
```

</details>

## Configuration Categories

![config-categories](diagrams/ops-configuration/config-categories.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Configuration Categories
    accDescr: Shows the four main configuration areas managed by Ops

    classDef lifecycle fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef concurrency fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef maintenance fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef export fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100

    subgraph Lifecycle["Lifecycle Config"]
        direction TB
        L1["mapping.default_ttl"]:::lifecycle
        L2["mapping.default_inactivity"]:::lifecycle
        L3["snapshot.default_ttl"]:::lifecycle
        L4["instance.default_ttl"]:::lifecycle
    end

    subgraph Concurrency["Concurrency Config"]
        direction TB
        CO1["per_analyst<br/>(max instances per user)"]:::concurrency
        CO2["cluster_total<br/>(max instances cluster-wide)"]:::concurrency
    end

    subgraph Maintenance["Maintenance Mode"]
        direction TB
        M1["enabled<br/>(boolean)"]:::maintenance
        M2["message<br/>(user-facing)"]:::maintenance
    end

    subgraph Export["Export Config"]
        direction TB
        E1["max_duration_seconds<br/>(export timeout)"]:::export
    end
```

</details>

## Cluster Health Components

![cluster-health](diagrams/ops-configuration/cluster-health.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Cluster Health Components
    accDescr: Shows the components monitored by the cluster health endpoint

    classDef healthy fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef degraded fill:#FFF9C4,stroke:#F9A825,stroke-width:2px,color:#F57F17
    classDef unhealthy fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef component fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1

    HEALTH([Cluster Health Check])

    subgraph Components["Monitored Components"]
        direction LR
        DB["Database<br/>PostgreSQL"]:::component
        K8S["Kubernetes<br/>API Server"]:::component
        GCS["Cloud Storage<br/>GCS Bucket"]:::component
        TRINO["Trino<br/>Query Engine"]:::component
    end

    subgraph Status["Health Status"]
        direction TB
        HEALTHY["✓ Healthy<br/>All OK"]:::healthy
        DEGRADED["⚠ Degraded<br/>Some Issues"]:::degraded
        UNHEALTHY["✗ Unhealthy<br/>Critical Failure"]:::unhealthy
    end

    HEALTH --> Components
    Components --> Status
```

</details>

## Background Jobs

![background-jobs](diagrams/ops-configuration/background-jobs.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Background Job Management
    accDescr: Shows the background jobs that Ops can trigger and monitor

    classDef job fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C
    classDef action fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef limit fill:#FFF9C4,stroke:#F9A825,stroke-width:2px,color:#F57F17

    subgraph Jobs["Available Background Jobs"]
        direction TB
        J1["reconciliation<br/>(sync K8s state)"]:::job
        J2["lifecycle<br/>(TTL enforcement)"]:::job
        J3["export_reconciliation<br/>(retry failed exports)"]:::job
        J4["schema_cache<br/>(refresh cached schemas)"]:::job
    end

    subgraph OpsActions["Ops Actions"]
        direction TB
        A1["trigger_job(name, reason)"]:::action
        A2["get_job_status()"]:::action
        A3["get_state()"]:::action
        A4["get_export_jobs()"]:::action
    end

    subgraph RateLimit["Rate Limiting"]
        LIMIT["1 trigger per minute<br/>per job type"]:::limit
    end

    Jobs --> OpsActions
    A1 --> RateLimit
```

</details>

## Role Access Comparison

![role-access](diagrams/ops-configuration/role-access.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Ops vs Admin vs Analyst Access
    accDescr: Shows what each role can access in the platform

    classDef ops fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef admin fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef analyst fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef allowed fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef denied fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C

    subgraph Roles["User Roles (Hierarchical: Analyst < Admin < Ops)"]
        direction LR
        ANALYST[["Analyst"]]:::analyst
        ADMIN[["Admin"]]:::admin
        OPS[["Ops"]]:::ops
    end

    subgraph Capabilities["Capabilities"]
        direction TB

        subgraph AnalystCap["Analyst"]
            AN1["Create/Query Resources"]:::allowed
            AN2["Run Algorithms (own)"]:::allowed
        end

        subgraph AdminCap["Admin (inherits Analyst)"]
            AD1["All Analyst + Cross-User"]:::allowed
            AD2["Bulk Delete Operations"]:::allowed
        end

        subgraph OpsCap["Ops (inherits Admin + Analyst)"]
            OP0["All Admin/Analyst Data Capabilities"]:::allowed
            OP1["System Configuration"]:::allowed
            OP2["Cluster Monitoring"]:::allowed
            OP3["Background Job Control"]:::allowed
        end
    end

    ANALYST --> AnalystCap
    ADMIN --> AdminCap
    OPS --> OpsCap

    ANALYST -.->|"✗ 403"| OpsCap
    ADMIN -.->|"✗ 403"| OpsCap
```

</details>

Roles are hierarchical: `Analyst < Admin < Ops`. Ops inherits all Admin and Analyst data capabilities (resource CRUD, cross-user access, bulk operations). Admin and Analyst cannot access Ops-only endpoints (configuration, cluster monitoring, background jobs). See [`../../system-design/authorization.spec.md`](../../system-design/authorization.spec.md) for the complete RBAC matrix.
