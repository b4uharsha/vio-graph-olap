# Authorization

## Role Permission Matrix

![role-permissions](diagrams/authorization/role-permissions.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Role Permission Matrix
    accDescr: Shows the three roles and their permission levels across resources

    classDef analyst fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef admin fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef ops fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef perm fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    subgraph Roles["User Roles (Hierarchical: Analyst < Admin < Ops)"]
        direction LR
        ANALYST[["Analyst<br/>(Data Users)"]]:::analyst
        ADMIN[["Admin<br/>(Full Access)"]]:::admin
        OPS[["Ops<br/>(Platform Operations)"]]:::ops
    end

    ANALYST -->|"inherits"| ADMIN
    ADMIN -->|"inherits"| OPS

    subgraph AnalystPerms["Analyst Permissions"]
        A1["Read All Resources"]:::perm
        A2["Create Own Resources"]:::perm
        A3["Modify/Delete Own"]:::perm
        A4["Query Any Instance"]:::perm
        A5["Algo on Own Instance"]:::perm
    end

    subgraph AdminPerms["Admin Permissions (inherits Analyst)"]
        D1["All Analyst Permissions"]:::perm
        D2["Modify/Delete Any"]:::perm
        D3["Algo on Any Instance"]:::perm
        D4["Terminate Any Instance"]:::perm
        D5["View Export Queue"]:::perm
    end

    subgraph OpsPerms["Ops Permissions (inherits Admin)"]
        O1["All Admin Permissions"]:::perm
        O2["View Configuration"]:::perm
        O3["Update Settings"]:::perm
        O4["System Maintenance"]:::perm
    end

    ANALYST --> AnalystPerms
    ADMIN --> AdminPerms
    OPS --> OpsPerms
```

</details>

## Ownership Model

![ownership-model](diagrams/authorization/ownership-model.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Resource Ownership Model
    accDescr: Shows how ownership is assigned when creating resources

    classDef user fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C
    classDef mapping fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef snapshot fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef instance fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100

    subgraph Alice["Alice (Analyst)"]
        ALICE[["analyst_alice@e2e.local"]]:::user
    end

    subgraph Bob["Bob (Analyst)"]
        BOB[["analyst_bob@e2e.local"]]:::user
    end

    subgraph Resources["Resource Ownership"]
        M1["Mapping A<br/>(owner: Alice)"]:::mapping
        S1["Snapshot 1<br/>(owner: Alice)"]:::snapshot
        S2["Snapshot 2<br/>(owner: Bob)"]:::snapshot
        I1["Instance X<br/>(owner: Alice)"]:::instance
        I2["Instance Y<br/>(owner: Bob)"]:::instance
    end

    ALICE -->|creates| M1
    M1 -->|"Bob creates snapshot<br/>from Alice's mapping"| S2
    ALICE -->|creates| S1
    S1 -->|"Alice creates instance"| I1
    S1 -->|"Bob creates instance<br/>from Alice's snapshot"| I2
    BOB -.->|owns| S2
    BOB -.->|owns| I2
```

</details>

## Instance Access Control

![instance-access](diagrams/authorization/instance-access.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Instance Access Control
    accDescr: Shows the difference between query access and algorithm execution permissions

    classDef query fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef algo fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef user fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C
    classDef instance fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100

    INST[("Instance<br/>(owner: Alice)"]]:::instance

    subgraph QueryAccess["Query Access (Read-Only)"]
        direction TB
        Q1["Any Analyst"]:::query
        Q2["Admin"]:::query
        Q_DESC["MATCH (n) RETURN n<br/>Read graph data"]
    end

    subgraph AlgoAccess["Algorithm Execution (Write)"]
        direction TB
        A1["Instance Owner Only"]:::algo
        A2["Admin (any instance)"]:::algo
        A_DESC["PageRank, Louvain, etc.<br/>Writes properties to nodes"]
    end

    QueryAccess -->|"✓ Allowed"| INST
    AlgoAccess -->|"✓ Owner/Admin Only"| INST

    BOB[["Bob<br/>(not owner)"]]:::user
    BOB -.->|"✗ 403 Forbidden"| AlgoAccess
```

</details>

## Admin Cross-User Access

![admin-access](diagrams/authorization/admin-access.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
sequenceDiagram
    accTitle: Admin Cross-User Access
    accDescr: Shows how admin can manage resources across user boundaries

    participant Alice as Alice (Analyst)
    participant Carol as Carol (Admin)
    participant API as Control Plane API
    participant M as Alice's Mapping
    participant I as Alice's Instance

    Note over Alice,I: Normal ownership boundaries

    Alice->>API: Update Mapping
    API->>M: ✓ Owner allowed
    M-->>Alice: Success

    Alice->>API: Run Algorithm
    API->>I: ✓ Owner allowed
    I-->>Alice: Completed

    Note over Carol,I: Admin bypasses ownership

    Carol->>API: Update Alice's Mapping
    API->>M: ✓ Admin allowed (any resource)
    M-->>Carol: Success

    Carol->>API: Run Algo on Alice's Instance
    API->>I: ✓ Admin allowed (any instance)
    I-->>Carol: Completed

    Carol->>API: Terminate Alice's Instance
    API->>I: ✓ Admin allowed (any instance)
    I-->>Carol: Deleted
```

</details>

## Permission Enforcement Flow

![permission-flow](diagrams/authorization/permission-flow.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Permission Enforcement Flow
    accDescr: Shows how the API checks permissions for each request

    classDef decision fill:#FFF9C4,stroke:#F9A825,stroke-width:2px,color:#F57F17
    classDef success fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef denied fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef action fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1

    START([API Request]) --> AUTH{{Authenticated?}}
    AUTH -->|No| DENY1["401 Unauthorized"]:::denied
    AUTH -->|Yes| READ{{Read Operation?}}

    READ -->|Yes| ALLOW1["✓ Allow<br/>(all users can read)"]:::success
    READ -->|No| ADMIN{{Is Admin?}}

    ADMIN -->|Yes| ALLOW2["✓ Allow<br/>(admin bypasses ownership)"]:::success
    ADMIN -->|No| OWN{{Is Resource Owner?}}

    OWN -->|Yes| ALLOW3["✓ Allow<br/>(owner permitted)"]:::success
    OWN -->|No| DENY2["403 Forbidden<br/>(not owner or admin)"]:::denied

    AUTH:::decision
    READ:::decision
    ADMIN:::decision
    OWN:::decision

    ALLOW1 --> EXEC["Execute Operation"]:::action
    ALLOW2 --> EXEC
    ALLOW3 --> EXEC
```

</details>


