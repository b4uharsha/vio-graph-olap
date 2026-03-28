# Exploring Schemas

## Schema Hierarchy

![schema-hierarchy](diagrams/exploring-schemas/schema-hierarchy.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Data Warehouse Schema Hierarchy
    accDescr: Shows the four-level hierarchy from catalog to column in data warehouse metadata

    classDef level1 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef level2 fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef level3 fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef level4 fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C
    classDef api fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B

    subgraph Hierarchy["Data Warehouse Hierarchy"]
        direction TB
        C1[(Catalog)]:::level1
        S1[Schema 1]:::level2
        S2[Schema 2]:::level2
        T1[Table A]:::level3
        T2[Table B]:::level3
        T3[Table C]:::level3
        Col1["id: INT"]:::level4
        Col2["name: VARCHAR"]:::level4
        Col3["created: TIMESTAMP"]:::level4

        C1 --> S1
        C1 --> S2
        S1 --> T1
        S1 --> T2
        S2 --> T3
        T1 --> Col1
        T1 --> Col2
        T1 --> Col3
    end

    subgraph API["SDK Methods"]
        direction TB
        M1["list_catalogs()"]:::api
        M2["list_schemas(catalog)"]:::api
        M3["list_tables(catalog, schema)"]:::api
        M4["list_columns(catalog, schema, table)"]:::api

        M1 --> M2 --> M3 --> M4
    end

    C1 -.- M1
    S1 -.- M2
    T1 -.- M3
    Col1 -.- M4
```

</details>

## Schema Cache Architecture

![schema-cache-architecture](diagrams/exploring-schemas/schema-cache-architecture.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Schema Cache Architecture
    accDescr: Shows how schema metadata flows from Starburst through cache to SDK clients

    classDef source fill:#ECEFF1,stroke:#455A64,stroke-width:2px,color:#263238
    classDef cache fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef api fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B
    classDef user fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C
    classDef admin fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100

    subgraph Source["Data Warehouse"]
        ST[(Starburst/<br/>Trino)]:::source
    end

    subgraph CP["Control Plane"]
        direction TB
        Cache["Schema Cache<br/>(SQLite Index)"]:::cache
        Refresh["Auto Refresh<br/>(Scheduled)"]:::cache

        Refresh -->|"Periodic"| Cache
    end

    subgraph SDK["Jupyter SDK"]
        direction TB
        List["list_* methods"]:::api
        Search["search_* methods"]:::api
    end

    subgraph Users["Users"]
        direction TB
        Analyst["Analysts<br/>(Read-Only)"]:::user
        Admin["Admins<br/>(Refresh/Stats)"]:::admin
    end

    ST -->|"Crawl<br/>Metadata"| Cache
    Cache -->|"Fast<br/>Queries"| List
    Cache -->|"Pattern<br/>Match"| Search
    List --> Analyst
    Search --> Analyst
    Admin -->|"admin_refresh()"| Refresh
    Admin -->|"get_stats()"| Cache
```

</details>

## Schema Discovery Workflow

![schema-discovery-workflow](diagrams/exploring-schemas/schema-discovery-workflow.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart LR
    accTitle: Schema Discovery Workflow
    accDescr: Shows the step-by-step process for discovering data warehouse tables before creating mappings

    classDef start fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C
    classDef browse fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef search fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20
    classDef inspect fill:#FFF8E1,stroke:#F57F17,stroke-width:2px,color:#E65100
    classDef output fill:#E1F5FE,stroke:#0277BD,stroke-width:2px,color:#01579B

    subgraph Start["1. Start"]
        Goal[/"What data<br/>do you need?"/]:::start
    end

    subgraph Browse["2. Browse (Know the Location)"]
        direction TB
        B1["list_catalogs()"]:::browse
        B2["list_schemas(cat)"]:::browse
        B3["list_tables(cat, schema)"]:::browse
        B1 --> B2 --> B3
    end

    subgraph Search["2. Search (Know the Name)"]
        direction TB
        S1["search_tables(pattern)"]:::search
        S2["search_columns(pattern)"]:::search
    end

    subgraph Inspect["3. Inspect"]
        direction TB
        I1["list_columns()"]:::inspect
        I2["View data types"]:::inspect
        I3["Check nullability"]:::inspect
        I1 --> I2 --> I3
    end

    subgraph Output["4. Ready to Map"]
        SQL[/"SQL queries<br/>for mapping"/]:::output
    end

    Goal --> Browse
    Goal --> Search
    Browse --> Inspect
    Search --> Inspect
    Inspect --> SQL
```

</details>

## Browse vs Search Decision

![browse-vs-search](diagrams/exploring-schemas/browse-vs-search.svg)

<details>
<summary>Mermaid Source</summary>

```mermaid
---
config:
  layout: elk
---
flowchart TB
    accTitle: Browse vs Search Decision
    accDescr: Helps users decide whether to browse or search based on their knowledge of the data warehouse

    classDef decision fill:#FFF9C4,stroke:#F9A825,stroke-width:2px,color:#F57F17
    classDef browse fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1
    classDef search fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20

    Q{{"Do you know which<br/>catalog/schema?"}}:::decision

    subgraph BrowsePath["Browse Path"]
        direction TB
        B1["list_catalogs()"]:::browse
        B2["Pick catalog"]:::browse
        B3["list_schemas(cat)"]:::browse
        B4["Pick schema"]:::browse
        B5["list_tables(cat, schema)"]:::browse
        B1 --> B2 --> B3 --> B4 --> B5
    end

    subgraph SearchPath["Search Path"]
        direction TB
        S1["search_tables(pattern)"]:::search
        S2["Review results"]:::search
        S3["Find full path"]:::search
        S1 --> S2 --> S3
    end

    Q -->|"Yes -<br/>Know location"| BrowsePath
    Q -->|"No -<br/>Know pattern"| SearchPath
```

</details>

