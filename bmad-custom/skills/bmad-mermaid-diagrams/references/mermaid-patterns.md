# Mermaid Patterns — catalog, templates, and lint rules

The `bmad-mermaid-diagrams` skill reads this file before generating. Each entry: **when to use**,
a **canonical template**, and notes. Emit diagrams as fenced ```mermaid blocks. Below the catalog is
a single **lint checklist** applied to every generated block.

---

## 1. Component / layer view — `flowchart`

**When:** an architecture with layers/components and directed dependencies (e.g. ports-and-adapters:
`api → services → repositories → datastore`; the rule "boto3 only in repositories").

```mermaid
flowchart LR
  subgraph API["API layer (FastAPI routers)"]
    R["/products routes"]
  end
  subgraph SVC["Service layer"]
    S["CatalogService"]
  end
  subgraph REPO["Repository layer (boto3 ONLY here)"]
    P["ProductsRepository"]
  end
  DB[("DynamoDB<br/>Products + GSIs")]
  R --> S --> P --> DB
```

Notes: use `subgraph` for layers; `[( )]` cylinder for datastores; `<br/>` for line breaks inside
labels. Direction `LR` (left-right) for layered flows, `TD` (top-down) for hierarchies.

## 2. Data model — `erDiagram`

**When:** entities/tables with attributes, keys, and relationships (DynamoDB tables + GSIs, or
relational schemas).

```mermaid
erDiagram
  PRODUCTS {
    string productId PK
    string category "gsi_category HASH"
    number price "gsi_category/gsi_listing RANGE (cents)"
    string listingPk "gsi_listing HASH (const PRODUCT)"
    bool available
  }
  CARTS ||--o{ CART_ITEMS : contains
  CARTS {
    string guestId PK
  }
  CART_ITEMS {
    string productId PK
    number quantity
  }
```

Notes: cardinality tokens — `||` exactly one, `o{` zero-or-many, `|{` one-or-many; combine as
`||--o{`. Put key/index hints in the quoted comment column. For a single DynamoDB table, one entity
block with `PK` + index annotations is clearer than forcing relations.

## 3. Request flow — `sequenceDiagram`

**When:** showing how one request traverses the layers (an endpoint's happy path and/or error path).

```mermaid
sequenceDiagram
  actor U as Shopper
  participant API as Router
  participant SVC as CatalogService
  participant REPO as ProductsRepository
  participant DB as DynamoDB
  U->>API: GET /products/{id}
  API->>SVC: get_product(id)
  SVC->>REPO: get_product(id)
  REPO->>DB: GetItem(PK=id)
  alt found
    DB-->>REPO: item
    REPO-->>SVC: Product
    SVC-->>API: ProductDetail
    API-->>U: 200 JSON
  else missing
    DB-->>REPO: (no item)
    REPO-->>SVC: None
    SVC-->>API: NotFoundError
    API-->>U: 404 {error:{code,message}}
  end
```

Notes: `->>` solid call, `-->>` dashed return; `alt/else/end` for branches; `actor` for humans.

## 4. Status lifecycle — `stateDiagram-v2`

**When:** a lifecycle/state machine (story or epic status; order state).

```mermaid
stateDiagram-v2
  [*] --> backlog
  backlog --> ready_for_dev: create-story
  ready_for_dev --> in_progress: dev-story
  in_progress --> review: dev complete
  review --> done: code-review approves
  done --> [*]
```

Notes: `[*]` is start/end; transition labels after `:`. Use underscores in state ids (avoid hyphens
that Mermaid may misparse); put the human label in the transition text.

## 5. Hierarchy / coverage / dependency — `flowchart TD`

**When:** epics→stories→FRs coverage, or module/task dependencies.

```mermaid
flowchart TD
  E1["Epic 1: Browse & Discover"] --> S13["1.3 Pagination (FR-1)"]
  E1 --> S14["1.4 Search (FR-2)"]
  E1 --> S15["1.5 Facet (FR-3)"]
  E1 --> S16["1.6 Sort (FR-4)"]
```

## 6. Process flow — `flowchart TD`

**When:** the BMAD phase/skill lifecycle or any process.

```mermaid
flowchart TD
  A[Brief] --> B[PRD] --> C[UX] --> D[Architecture] --> E[Epics & Stories]
  E --> F[Readiness] --> G[Sprint Planning]
  G --> H{Story cycle}
  H --> I[create-story] --> J[dev-story] --> K[code-review] --> H
```

---

## Lint checklist (apply to EVERY generated block)

1. **Kind header** is present and valid on the first line: one of `flowchart`/`graph`,
   `erDiagram`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`, `gantt`.
2. **Labels with spaces/punctuation/parentheses/braces are quoted**: `A["GET /x (v1)"]`, not
   `A[GET /x (v1)]`. Unquoted `()`/`{}`/`,`/`:` inside labels are the #1 parse failure.
3. **Node ids are safe**: alphanumeric/underscore, no spaces, not reserved words (`end`, `class`,
   `state`, `subgraph`, `graph`). Lowercase `end` as a bare id breaks flowcharts — rename to `end_`.
4. **Brackets balanced**: every `[`,`(`,`{`,`subgraph` has its close (`]`,`)`,`}`,`end`).
5. **Arrows match the kind**: flowchart `-->`/`---`/`-.->`; sequence `->>`/`-->>`; ER `||--o{` etc.
   Don't mix a sequence arrow into a flowchart.
6. **erDiagram**: cardinality on both sides (`||`,`o{`,`|{`,`}o`,`}|`); attribute lines are
   `type name` (+ optional `PK`/`FK` + optional quoted comment).
7. **stateDiagram-v2**: uses `[*]` for start/end; state ids have no hyphens.
8. **sequenceDiagram**: every `participant`/`actor` referenced by an arrow is declared; `alt/opt/loop`
   are closed with `end`.
9. **Readability**: prefer &lt;= ~20 nodes; split otherwise. Provide a heading + one-line caption
   above each block.
10. **Fencing**: exactly one ```mermaid block per diagram; nothing else inside the fence.
