# Version Diffing

## Version Evolution Timeline

![version-evolution](diagrams/version-diffing/version-evolution.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Version Evolution Timeline
    accDescr: Shows how a mapping evolves through versions with different schema changes

    classDef version fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef added fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef modified fill:#FFF9C4,stroke:#F9A825,stroke-width:2px,color:#F57F17
    classDef removed fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C

    subgraph V1["Version 1 (Base)"]
        N1["Customer node"]:::version
        E1["PURCHASED edge"]:::version
    end

    subgraph V2["Version 2"]
        N2a["Customer node"]:::version
        N2b["+ Product node"]:::added
        E2["PURCHASED edge"]:::version
    end

    subgraph V3["Version 3"]
        N3a["~ Customer (modified)"]:::modified
        N3b["Product node"]:::version
        E3["PURCHASED edge"]:::version
    end

    subgraph V4["Version 4"]
        N4a["Customer node"]:::version
        N4b["Product node"]:::version
        E4["- PURCHASED (removed)"]:::removed
    end

    V1 -->|"Add Product"| V2
    V2 -->|"Modify Customer"| V3
    V3 -->|"Remove Edge"| V4
```

</details>

## Diff Operation Flow

![diff-operation](diagrams/version-diffing/diff-operation.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Diff Operation Flow
    accDescr: Shows how the diff() operation compares two mapping versions

    classDef input fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef process fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef output fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef result fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C

    subgraph Inputs["Input Parameters"]
        M[("mapping_id")]:::input
        FV["from_version"]:::input
        TV["to_version"]:::input
    end

    subgraph API["Control Plane API"]
        DIFF["diff(mapping_id,<br/>from_version,<br/>to_version)"]:::process
    end

    subgraph Comparison["Schema Comparison"]
        CN["Compare Nodes"]:::process
        CE["Compare Edges"]:::process
    end

    subgraph Output["MappingDiff Result"]
        SUM["summary<br/>{nodes_added, nodes_removed,<br/>nodes_modified, edges_*}"]:::output
        CHG["changes<br/>{nodes: [...], edges: [...]}"]:::output
    end

    subgraph Details["Change Details"]
        CT["change_type<br/>(added/removed/modified)"]:::result
        FROM["from_<br/>(old definition)"]:::result
        TO["to<br/>(new definition)"]:::result
        FC["fields_changed<br/>[sql, properties, ...]"]:::result
    end

    M & FV & TV --> DIFF
    DIFF --> CN & CE
    CN & CE --> SUM & CHG
    CHG --> CT & FROM & TO & FC
```

</details>

## Change Types Matrix

![change-types](diagrams/version-diffing/change-types.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Change Types Matrix
    accDescr: Shows the three change types and their from/to/fields_changed values

    classDef added fill:#C8E6C9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef removed fill:#FFCDD2,stroke:#C62828,stroke-width:2px,color:#B71C1C
    classDef modified fill:#FFF9C4,stroke:#F9A825,stroke-width:2px,color:#F57F17
    classDef field fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B

    subgraph Added["change_type: added"]
        A1["from_: None"]:::field
        A2["to: {definition}"]:::field
        A3["fields_changed: None"]:::field
    end
    A["New element<br/>not in from_version"]:::added --> Added

    subgraph Removed["change_type: removed"]
        R1["from_: {definition}"]:::field
        R2["to: None"]:::field
        R3["fields_changed: None"]:::field
    end
    R["Element removed<br/>not in to_version"]:::removed --> Removed

    subgraph Modified["change_type: modified"]
        M1["from_: {old definition}"]:::field
        M2["to: {new definition}"]:::field
        M3["fields_changed: [...]"]:::field
    end
    M["Element changed<br/>between versions"]:::modified --> Modified
```

</details>

## Reverse Diff Behavior

![reverse-diff](diagrams/version-diffing/reverse-diff.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Reverse Diff Behavior
    accDescr: Shows how reversing diff direction inverts the change types

    classDef forward fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef reverse fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef invert fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100

    subgraph Forward["Forward Diff (v1 → v4)"]
        F1["Product: added"]:::forward
        F2["Customer: modified"]:::forward
        F3["PURCHASED: removed"]:::forward
    end

    INV{{"Invert<br/>Direction"}}:::invert

    subgraph Reverse["Reverse Diff (v4 → v1)"]
        R1["Product: removed"]:::reverse
        R2["Customer: modified"]:::reverse
        R3["PURCHASED: added"]:::reverse
    end

    F1 --> INV --> R1
    F2 --> INV --> R2
    F3 --> INV --> R3
```

</details>

## Migration Planning Workflow

![migration-workflow](diagrams/version-diffing/migration-workflow.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Migration Planning Workflow
    accDescr: Shows how to use diff for planning schema migrations

    classDef user fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C
    classDef action fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef decision fill:#FFF9C4,stroke:#F9A825,stroke-width:2px,color:#F57F17
    classDef output fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B

    U[/"Analyst"/]:::user

    subgraph Plan["1. Review Changes"]
        D1["diff(mapping_id,<br/>current, target)"]:::action
        S1["Review summary<br/>counts"]:::output
    end

    subgraph Analyze["2. Analyze Impact"]
        D2["render_diff_details()<br/>with show_from_to"]:::action
        S2["Identify breaking<br/>changes"]:::output
    end

    subgraph Decide["3. Decision Point"]
        Q{{"Breaking<br/>changes?"}}:::decision
        SAFE["Safe to proceed"]:::output
        PLAN["Plan migration<br/>strategy"]:::output
    end

    subgraph Execute["4. Execute"]
        E1["Create new snapshot<br/>from target version"]:::action
        E2["Update dependent<br/>applications"]:::action
        E3["Switch instances<br/>to new snapshot"]:::action
    end

    U --> Plan
    D1 --> S1
    Plan --> Analyze
    D2 --> S2
    Analyze --> Decide
    Q -->|"No"| SAFE --> Execute
    Q -->|"Yes"| PLAN --> Execute
    E1 --> E2 --> E3
```

</details>

