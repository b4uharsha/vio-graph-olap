# Advanced Mappings

## Mapping Hierarchy Structure

![mapping-hierarchy](diagrams/advanced-mappings/mapping-hierarchy.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Mapping Hierarchy Structure
    accDescr: Shows the relationship between mappings, versions, snapshots, and instances

    classDef mapping fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef version fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef snapshot fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef instance fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    subgraph Mapping["Mapping (id=123)"]
        M["Social Graph"]:::mapping
    end

    subgraph Versions["Versions"]
        V1["Version 1<br/>Person node"]:::version
        V2["Version 2<br/>+ Company node"]:::version
        V3["Version 3<br/>+ Location node"]:::version
    end

    subgraph Snapshots["Snapshots"]
        S1["Snapshot A<br/>(v1, ready)"]:::snapshot
        S2["Snapshot B<br/>(v2, ready)"]:::snapshot
        S3["Snapshot C<br/>(v3, ready)"]:::snapshot
    end

    subgraph Instances["Instances"]
        I1["Instance 1<br/>(running)"]:::instance
        I2["Instance 2<br/>(running)"]:::instance
    end

    M --> V1 & V2 & V3
    V1 --> S1
    V2 --> S2
    V3 --> S3
    S2 --> I1
    S3 --> I2
```

</details>

## Copy Mapping Workflow

![copy-workflow](diagrams/advanced-mappings/copy-workflow.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Copy Mapping Workflow
    accDescr: Shows how copy() creates an independent mapping from an existing one

    classDef original fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef action fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef copy fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef independent fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    O["Original Mapping<br/>(id=123, v2)"]:::original
    C["copy(123, 'new-name')"]:::action
    N["New Mapping<br/>(id=456, v1)"]:::copy

    O --> C --> N

    subgraph Independence["Independent Evolution"]
        direction TB
        O2["Original v3"]:::original
        N2["Copy v2"]:::copy
    end

    N --> N2
    O --> O2
```

</details>

## Version Diff Comparison

![version-diff](diagrams/advanced-mappings/version-diff.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Version Diff Comparison
    accDescr: Shows how diff() compares schema changes between versions

    classDef v1 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef v2 fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef added fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef removed fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef diff fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100

    subgraph V1["Version 1"]
        N1["Person"]:::v1
        E1["KNOWS"]:::v1
    end

    subgraph V2["Version 2"]
        N2["Person"]:::v2
        N3["Location"]:::added
        E2["KNOWS"]:::v2
        E3["LIVES_IN"]:::added
    end

    D{{"diff(1, 2)"}}:::diff

    V1 --> D --> V2

    subgraph Result["Diff Result"]
        R1["+1 node (Location)"]:::added
        R2["+1 edge (LIVES_IN)"]:::added
    end

    D --> Result
```

</details>

## Multi-Entity Graph Schema

![multi-entity-schema](diagrams/advanced-mappings/multi-entity-schema.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Multi-Entity Graph Schema
    accDescr: Example of a complex graph mapping with multiple node and edge types

    classDef person fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef company fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef location fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef edge fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    P["Person<br/>id, name, age"]:::person
    C["Company<br/>id, name, industry"]:::company
    L["Location<br/>id, city, country"]:::location

    P -->|"KNOWS"| P
    P -->|"WORKS_AT"| C
    P -->|"LIVES_IN"| L
    C -->|"LOCATED_IN"| L
```

</details>

