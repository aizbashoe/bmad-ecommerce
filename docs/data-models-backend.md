# Data Models — bmad-ecommerce (part: backend)

**Generated:** 2026-07-06 · DynamoDB (local: `amazon/dynamodb-local`)

Design principle (AD-3): **one aggregate ⇒ one table ⇒ one owning repository**. Money is an
integer minor-unit (cents) `Number` attribute (AD-6). Table names come from config.

## Products (implemented) — owner: `ProductsRepository`

The catalog table. Every item carries `listingPk="PRODUCT"` so it appears in the listing GSI.

**Key schema**

| Element | Attribute | Type |
|---------|-----------|------|
| Table PK (HASH) | `productId` | S |
| GSI `gsi_category` | `category` (HASH), `price` (RANGE) | S, N |
| GSI `gsi_listing` | `listingPk` (HASH, const `"PRODUCT"`), `price` (RANGE) | S, N |

Both GSIs use `ProjectionType: ALL`; table is `PAY_PER_REQUEST`.

**Item attributes**

| Attribute | Type | Notes |
|-----------|------|-------|
| `productId` | S | e.g. `p-0001` |
| `name` | S | |
| `description` | S | |
| `price` | N | integer cents (AD-6) |
| `category` | S | facet key (`gsi_category`) |
| `imageUrl` | S | |
| `available` | BOOL | |
| `listingPk` | S | constant `"PRODUCT"` — partition for `gsi_listing` |

**Access patterns**

| Pattern | Query |
|---------|-------|
| List all, price-sorted, paginated | Query `gsi_listing` `listingPk="PRODUCT"`, `ScanIndexForward=True`, `Limit`, `ExclusiveStartKey` |
| Get by id | GetItem `productId` |
| (planned) Filter by category | Query `gsi_category` `category=<c>` |

**Domain ↔ item mapping** lives entirely in `ProductsRepository._to_item`/`_from_item`.
Pagination cursors are `LastEvaluatedKey` encoded as opaque urlsafe-base64 (never exposed raw);
decode validates the key shape and rejects forged cursors as `invalid_cursor` (400).

**Seed:** `scripts/seed.py` loads a deterministic 240-product catalog (6 categories × 40),
idempotent (fixed ids overwrite). Run: `python -m scripts.seed`.

## Carts (planned — Epic 3) — owner: `CartsRepository`

Keyed by the anonymous **guest token** (`guestId`). Holds line items (productId + quantity).
Not yet implemented.

## Orders (planned — Epic 4) — owner: `OrdersRepository`

Immutable order snapshot (line items with frozen prices, totals, shipping, reference, timestamp),
created atomically at checkout (which also clears the cart). Not yet implemented.

## ERD (current + planned)

```mermaid
erDiagram
    PRODUCT ||--o{ CART_LINE : "referenced by"
    CART ||--o{ CART_LINE : contains
    ORDER ||--o{ ORDER_LINE : snapshots
    PRODUCT { string productId PK; string category; int price; string listingPk }
    CART    { string guestId PK }
    ORDER   { string orderId PK; string reference; string guestId }
```
*PRODUCT is implemented; CART and ORDER are planned.*
