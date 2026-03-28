# Background Jobs

## Background Job Architecture

![job-architecture](diagrams/background-jobs/job-architecture.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Background Job Architecture
    accDescr: Shows how the scheduler coordinates background jobs in the control plane

    classDef scheduler fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef job fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef metric fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef target fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    subgraph ControlPlane["Control Plane"]
        SCHED[["APScheduler<br/>Scheduler"]]:::scheduler

        subgraph Jobs["Background Jobs"]
            J1["reconciliation<br/>(10s interval)"]:::job
            J2["lifecycle<br/>(10s interval)"]:::job
            J3["export_reconciliation<br/>(10s interval)"]:::job
            J4["schema_cache<br/>(10s interval)"]:::job
        end

        subgraph Metrics["Prometheus Metrics"]
            M1["background_job_execution_total"]:::metric
            M2["background_job_duration_seconds"]:::metric
            M3["reconciliation_passes_total"]:::metric
            M4["lifecycle_passes_total"]:::metric
        end
    end

    subgraph Targets["Managed Resources"]
        K8S[("Kubernetes<br/>Pods")]:::target
        DB[("Database<br/>State")]:::target
        CACHE[("Schema<br/>Cache")]:::target
    end

    SCHED --> J1 & J2 & J3 & J4
    J1 --> M1 & M2 & M3
    J2 --> M1 & M2 & M4
    J3 --> M1 & M2
    J4 --> M1 & M2

    J1 --> K8S
    J2 --> DB
    J3 --> DB
    J4 --> CACHE
```

</details>

## Job Responsibilities

![job-types](diagrams/background-jobs/job-types.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Background Job Responsibilities
    accDescr: Shows what each background job does in the system

    classDef reconciliation fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef lifecycle fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef export fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef cache fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    subgraph Reconciliation["Reconciliation Job"]
        direction TB
        R1["Detect orphaned pods<br/>(pods without instance)"]:::reconciliation
        R2["Detect missing pods<br/>(instances without pod)"]:::reconciliation
        R3["Fix status drift<br/>(sync DB with K8s)"]:::reconciliation
    end

    subgraph Lifecycle["Lifecycle Job"]
        direction TB
        L1["Check TTL expiry<br/>(terminate expired instances)"]:::lifecycle
        L2["Check inactivity<br/>(cleanup idle resources)"]:::lifecycle
        L3["Cascade deletions<br/>(cleanup orphaned snapshots)"]:::lifecycle
    end

    subgraph Export["Export Reconciliation Job"]
        direction TB
        E1["Find pending snapshots"]:::export
        E2["Re-queue stalled exports"]:::export
        E3["Update export status"]:::export
    end

    subgraph Cache["Schema Cache Job"]
        direction TB
        C1["Refresh stale schemas"]:::cache
        C2["Invalidate expired entries"]:::cache
        C3["Preload common schemas"]:::cache
    end
```

</details>

## Metrics Collection Flow

![metrics-flow](diagrams/background-jobs/metrics-flow.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
sequenceDiagram
    accTitle: Metrics Collection Flow
    accDescr: Shows how job execution generates Prometheus metrics

    participant S as Scheduler
    participant J as Job
    participant M as Metrics Registry
    participant P as Prometheus

    S->>J: Execute job
    activate J

    J->>M: background_job_execution_total{status="running"}
    Note over J: Execute job logic...

    alt Success
        J->>M: background_job_execution_total{status="success"}
        J->>M: background_job_duration_seconds.observe()
    else Failure
        J->>M: background_job_execution_total{status="failed"}
        J->>M: background_job_duration_seconds.observe()
    end

    deactivate J

    P->>M: GET /metrics
    M-->>P: Prometheus text format
```

</details>

## Job Execution Lifecycle

![execution-lifecycle](diagrams/background-jobs/execution-lifecycle.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
stateDiagram-v2
    accTitle: Job Execution Lifecycle
    accDescr: Shows the state transitions of a background job execution

    [*] --> Scheduled: Scheduler queues job

    Scheduled --> Running: Interval elapsed
    Running --> Success: Complete without error
    Running --> Failed: Exception raised
    Running --> Timeout: Max duration exceeded

    Success --> Scheduled: Wait for next interval
    Failed --> Scheduled: Wait for next interval
    Timeout --> Scheduled: Wait for next interval

    note right of Running
        Job-specific metrics
        updated during execution
    end note

    note left of Failed
        Failure logged to
        background_job_execution_total{status=failed}
    end note
```

</details>

## Production Metrics Dashboard

![production-metrics](diagrams/background-jobs/production-metrics.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Production Metrics Dashboard
    accDescr: Shows the key metrics exposed by the control plane for monitoring

    classDef golden fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef saturation fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef queue fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef job fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    subgraph GoldenSignals["Four Golden Signals"]
        direction TB
        LAT["Latency<br/>(request_duration_seconds)"]:::golden
        TRF["Traffic<br/>(http_requests_total)"]:::golden
        ERR["Errors<br/>(http_errors_total)"]:::golden
        SAT["Saturation<br/>(database_connections)"]:::saturation
    end

    subgraph ExportHealth["Export Pipeline Health"]
        direction TB
        QD["Queue Depth<br/>(export_queue_depth)"]:::queue
        ES["Export Status<br/>(pending/exporting/ready)"]:::queue
    end

    subgraph JobHealth["Background Job Health"]
        direction TB
        JE["Job Executions<br/>(background_job_execution_total)"]:::job
        JD["Job Duration<br/>(background_job_duration_seconds)"]:::job
        JF["Job Failures<br/>(status=failed label)"]:::job
    end

    GoldenSignals --> Prometheus[(Prometheus)]
    ExportHealth --> Prometheus
    JobHealth --> Prometheus
```

</details>

