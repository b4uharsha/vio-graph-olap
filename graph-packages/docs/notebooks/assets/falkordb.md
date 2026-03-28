# FalkorDB

## Ryugraph vs FalkorDB Architecture

![wrapper-comparison](diagrams/falkordb/wrapper-comparison.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Ryugraph vs FalkorDB Architecture
    accDescr: Shows the different architectures of Ryugraph and FalkorDB wrappers

    classDef ryugraph fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef falkor fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef storage fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef api fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    subgraph Ryugraph["Ryugraph Wrapper"]
        direction TB
        R_API[["REST API<br/>(FastAPI)"]]:::api
        R_ENGINE["KuzuDB Engine"]:::ryugraph
        R_DISK[("Disk Storage<br/>8Gi RAM")]:::storage
        R_NX["NetworkX<br/>Integration"]:::ryugraph
    end

    subgraph FalkorDB["FalkorDB Wrapper"]
        direction TB
        F_API[["REST API<br/>(FastAPI)"]]:::api
        F_ENGINE["FalkorDB Module"]:::falkor
        F_REDIS["Redis Server"]:::falkor
        F_MEM[("In-Memory<br/>12Gi RAM")]:::storage
    end

    R_API --> R_ENGINE
    R_ENGINE --> R_DISK
    R_ENGINE -.-> R_NX

    F_API --> F_ENGINE
    F_ENGINE --> F_REDIS
    F_REDIS --> F_MEM
```

</details>

## Feature Comparison Matrix

![feature-comparison](diagrams/falkordb/feature-comparison.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Feature Comparison Matrix
    accDescr: Shows which features are available in each wrapper type

    classDef both fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef ryuonly fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef falkoronly fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100

    subgraph Both["Both Wrappers"]
        B1["Cypher Queries"]:::both
        B2["Schema Introspection"]:::both
        B3["Algorithm API<br/>(/algo/*)"]:::both
        B4["Lock Management"]:::both
        B5["Health Checks"]:::both
    end

    subgraph RyuOnly["Ryugraph Only"]
        R1["NetworkX Export"]:::ryuonly
        R2["Disk Persistence"]:::ryuonly
        R3["Lower Memory"]:::ryuonly
    end

    subgraph FalkorOnly["FalkorDB Only"]
        F1["In-Memory Speed"]:::falkoronly
        F2["Redis Module"]:::falkoronly
        F3["Cypher CALL Procedures"]:::falkoronly
    end
```

</details>

## Algorithm API Flow

![algorithm-api](diagrams/falkordb/algorithm-api.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
sequenceDiagram
    accTitle: Algorithm API Flow
    accDescr: Shows the async algorithm execution workflow

    participant C as Client
    participant W as Wrapper
    participant E as Executor
    participant G as Graph

    C->>W: POST /algo/pagerank
    W->>E: Queue execution
    W-->>C: {execution_id, status: "queued"}

    activate E
    E->>W: Acquire lock
    W-->>E: Lock granted

    E->>G: Execute algorithm
    Note over G: Process nodes...
    G-->>E: Results

    E->>G: Write scores
    E->>W: Release lock
    deactivate E

    C->>W: GET /algo/status/{id}
    W-->>C: {status: "completed", nodes_updated: 100}

    C->>W: GET /lock
    W-->>C: {locked: false}
```

</details>

## Wrapper Selection Decision Tree

![selection-tree](diagrams/falkordb/selection-tree.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Wrapper Selection Decision Tree
    accDescr: Helps choose between Ryugraph and FalkorDB based on requirements

    classDef decision fill:#FFF9C4,stroke:#F9A825,stroke-width:2px,color:#F57F17
    classDef ryugraph fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef falkordb fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20

    START([Start]) --> Q1{{Need NetworkX<br/>integration?}}
    Q1 -->|Yes| RYU["Use Ryugraph"]:::ryugraph
    Q1 -->|No| Q2{{Priority: Speed<br/>or Memory?}}
    Q2 -->|Speed| FAL["Use FalkorDB"]:::falkordb
    Q2 -->|Memory| RYU
    Q2 -->|Either| Q3{{Large graph<br/>>1M nodes?}}
    Q3 -->|Yes| RYU
    Q3 -->|No| Q4{{Need CALL<br/>procedures?}}
    Q4 -->|Yes| FAL
    Q4 -->|No| RYU

    Q1:::decision
    Q2:::decision
    Q3:::decision
    Q4:::decision
```

</details>

## FalkorDB Memory Architecture

![memory-architecture](diagrams/falkordb/memory-architecture.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: FalkorDB Memory Architecture
    accDescr: Shows how FalkorDB stores graph data in Redis memory

    classDef redis fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef graph fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef data fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef api fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    subgraph Pod["FalkorDB Pod (12Gi RAM)"]
        API["FastAPI<br/>Wrapper"]:::api

        subgraph Redis["Redis Server"]
            MOD["FalkorDB<br/>Module"]:::redis

            subgraph Graph["Graph Data (In-Memory)"]
                NODES["Node Matrix<br/>(sparse)"]:::data
                EDGES["Edge Matrix<br/>(sparse)"]:::data
                PROPS["Property Store<br/>(hash tables)"]:::data
                INDEX["Label Indices"]:::graph
            end
        end
    end

    API --> MOD
    MOD --> NODES & EDGES & PROPS
    INDEX --> NODES
```

</details>

