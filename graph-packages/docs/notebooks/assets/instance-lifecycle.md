# Instance Lifecycle

## Instance State Machine

![instance-state-machine](diagrams/instance-lifecycle/instance-state-machine.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
stateDiagram-v2
    accTitle: Instance State Machine
    accDescr: Shows the lifecycle states of a Graph OLAP instance from creation to termination

    [*] --> pending: create()
    pending --> starting: pod_scheduled
    starting --> running: ready
    pending --> failed: error
    starting --> failed: error
    running --> stopped: delete()
    running --> stopped: ttl_expired
    stopped --> [*]
    failed --> [*]

    note right of pending
        Waiting for K8s
        to schedule pod
    end note

    note right of starting
        Downloading data,
        loading schema
    end note

    note right of running
        Ready for queries
        and algorithms
    end note

    note left of failed
        Check logs for
        error details
    end note
```

</details>

## TTL Management

![ttl-management](diagrams/instance-lifecycle/ttl-management.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: TTL Management Flow
    accDescr: Shows how instance Time-To-Live is managed and extended

    classDef action fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef time fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef state fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B
    classDef warning fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C

    subgraph Creation["Instance Creation"]
        C1["create(ttl=24)"]:::action
        T1["Default: 24h TTL"]:::time
    end

    subgraph Running["Running Instance"]
        I1["Instance Running"]:::state
        EXP["expires_at timestamp"]:::time
    end

    subgraph Extend["TTL Extension"]
        E1["extend_ttl(hours=48)"]:::action
        T2["New expires_at"]:::time
    end

    subgraph Expiry["Expiry Handling"]
        W1{"TTL<br/>Expired?"}:::warning
        DEL["Auto-deleted"]:::warning
        OK["Continue Running"]:::state
    end

    C1 --> T1 --> I1
    I1 --> EXP
    EXP --> W1
    W1 -->|"Yes"| DEL
    W1 -->|"No"| OK
    OK --> E1
    E1 --> T2
    T2 --> EXP
```

</details>

## Health Check Architecture

![health-check-architecture](diagrams/instance-lifecycle/health-check-architecture.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Health Check Architecture
    accDescr: Shows the two types of health checks and their return values

    classDef user fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C
    classDef method fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef result fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B
    classDef detail fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef bool fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1

    User[/"Analyst"/]:::user

    subgraph SDK["SDK Health Methods"]
        direction TB
        GH["get_health(instance_id)"]:::method
        CH["check_health(instance_id)"]:::method
    end

    subgraph GetHealthResult["get_health() Result"]
        direction TB
        R1["Dict with details"]:::result
        D1["status: 'healthy'"]:::detail
        D2["wrapper_type: 'ryugraph'"]:::detail
        D3["uptime: 3600"]:::detail
        D4["last_query: timestamp"]:::detail
    end

    subgraph CheckHealthResult["check_health() Result"]
        direction TB
        R2["Boolean"]:::bool
        B1["True = healthy"]:::bool
        B2["False = unhealthy"]:::bool
    end

    User --> SDK
    GH --> GetHealthResult
    CH --> CheckHealthResult
    R1 --> D1 & D2 & D3 & D4
    R2 --> B1 & B2
```

</details>

## Instance Progress Phases

![progress-phases](diagrams/instance-lifecycle/progress-phases.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Instance Startup Progress Phases
    accDescr: Shows the sequential phases of instance startup from scheduling to ready

    classDef phase fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef percent fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef ready fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef failed fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C

    P1["pod_scheduled<br/>0%"]:::phase
    P2["downloading<br/>25%"]:::phase
    P3["loading_schema<br/>50%"]:::phase
    P4["loading_data<br/>75%"]:::phase
    P5["ready<br/>100%"]:::ready
    PF["failed"]:::failed

    P1 -->|"K8s schedules pod"| P2
    P2 -->|"Parquet download"| P3
    P3 -->|"Schema loaded"| P4
    P4 -->|"Graph loaded"| P5

    P1 -.->|"error"| PF
    P2 -.->|"error"| PF
    P3 -.->|"error"| PF
    P4 -.->|"error"| PF
```

</details>

## Algorithm Lock Behavior

![algorithm-lock](diagrams/instance-lifecycle/algorithm-lock.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
sequenceDiagram
    accTitle: Algorithm Lock Behavior
    accDescr: Shows how instance locking works during algorithm execution

    participant A as Analyst
    participant SDK as SDK
    participant I as Instance

    A->>SDK: conn.get_lock()
    SDK->>I: Check lock status
    I-->>SDK: locked: false
    SDK-->>A: Not locked

    A->>SDK: conn.algo.pagerank()
    SDK->>I: Execute algorithm
    Note over I: Instance LOCKED<br/>during execution

    A->>SDK: conn.get_lock()
    SDK->>I: Check lock status
    I-->>SDK: locked: true
    SDK-->>A: Locked (algorithm running)

    I-->>SDK: Algorithm complete
    Note over I: Lock RELEASED

    A->>SDK: conn.get_lock()
    SDK->>I: Check lock status
    I-->>SDK: locked: false
    SDK-->>A: Not locked
```

</details>

