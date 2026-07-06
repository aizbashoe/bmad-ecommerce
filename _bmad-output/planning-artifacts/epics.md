---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories", "step-04-final-validation"]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-bmad-ecommerce-2026-07-06/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-bmad-ecommerce-2026-07-06/ARCHITECTURE-SPINE.md
---

# Anonymous E-Commerce Storefront - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the Anonymous E-Commerce Storefront, decomposing the requirements from the PRD and Architecture spine into implementable stories. No UX design contract exists (the optional `bmad-ux` phase was skipped for this learning/POC); UI stories carry functional acceptance criteria rather than a visual-design handoff.

## Requirements Inventory

### Functional Requirements

FR-1: An anonymous shopper can view the Catalog as a paginated list of Products (name, price, image, link to PDP).
FR-2: An anonymous shopper can search Products by keyword (name/description); empty results show a reset-able empty state.
FR-3: An anonymous shopper can filter PLP results by one or more category Facet values (category is the only facet in v1); active filters are visible/removable with clear-all.
FR-4: An anonymous shopper can sort PLP results (price low→high, high→low, default) without losing active search/filters.
FR-5: An anonymous shopper can view a PDP (name, description, price, image(s), availability); unknown id → not-found state.
FR-6: An anonymous shopper can add a Product to the Cart from its PDP (quantity ≥ 1) with clear feedback.
FR-7: The system issues/recognizes a Guest Token so a Cart persists for an anonymous shopper with no login.
FR-8: An anonymous shopper can view the Cart (line items with unit price, quantity, line total, and Subtotal); contents survive reload within a session.
FR-9: An anonymous shopper can change a line item quantity (recomputes totals; quantity 0 removes the item).
FR-10: An anonymous shopper can remove a line item (Subtotal recomputes).
FR-11: The Cart displays Subtotal and Order Total using a flat placeholder for shipping/tax.
FR-12: An anonymous shopper can enter shipping details (name, address, city, region, postal code, country, email); required fields validated inline.
FR-13: An anonymous shopper completes a simulated payment step that always succeeds (no real gateway, no card data stored); no failure path in v1.
FR-14: An anonymous shopper can place the Order, converting the Cart into an immutable Order with a reference number; Cart is cleared after success.
FR-15: An anonymous shopper sees an Order Summary confirming the placed Order (reference, line items, totals, shipping); shown immediately post-checkout, no order-lookup page.
FR-16: The system provides a repeatable/idempotent way to load a synthetic Catalog into the data store, varied enough to exercise search, the category facet, and sorting.

### NonFunctional Requirements

NFR-1: No authentication or identity anywhere — the only session concept is the opaque Guest Token (governs FR-7).
NFR-2: Local-first — the system runs end-to-end locally (containerized API + local/emulated DynamoDB); this is the bar for "done." AWS deploy is a future enhancement.
NFR-3: Stateless API — no per-shopper mutable state in memory; all cart/order state in DynamoDB keyed by guestId.
NFR-4: Data minimization — no real payment data collected/stored; shipping details stored only as part of a placed Order; no analytics/tracking.
NFR-5: Performance — interactive PLP operations feel responsive on the seeded catalog (target p95 < 500ms locally).
NFR-6: Accessibility — baseline keyboard navigability and semantic markup on core flows (not a formal WCAG AA audit).
NFR-7: API contract — frontend/backend integrate over a documented HTTP/JSON API (OpenAPI) covering all flows.

### Additional Requirements

*(Derived from the Architecture Spine — each cites its governing AD. No starter template is specified; the foundation is hand-scaffolded per the spine's source tree.)*

- **AD-1** Ports & Adapters backend layering: `api → services → repository`; boto3/DynamoDB only inside `repositories/`. (Epic 1 scaffold + every backend story.)
- **AD-2** Anonymous identity via opaque `guestId` issued by API, carried in `X-Guest-Token`, stored client-side; Carts/Orders keyed by guestId.
- **AD-3** Separate DynamoDB tables per aggregate — Products, Carts, Orders — one repository each.
- **AD-4** Catalog query strategy: `gsi_category` (PK=category, SK=price) and `gsi_listing` (PK="PRODUCT", SK=price); free-text via FilterExpression `contains`; opaque base64 cursor pagination (LastEvaluatedKey).
- **AD-5** API contract: FastAPI OpenAPI is source of truth; error envelope `{error:{code,message}}`; JSON camelCase; typed frontend client.
- **AD-6** Money as integer minor units (cents); `Subtotal = Σ(unitPrice×qty)`; `OrderTotal = Subtotal + flatShipping`; no tax.
- **AD-7** Orders immutable; placing an order snapshots lines/totals/shipping/ref/timestamp AND clears the Cart atomically.
- **AD-8** 12-factor config (DynamoDB endpoint, table names, flatShipping, CORS via env); only local↔AWS diff is the DynamoDB endpoint.
- **AD-9** Stateless API (reinforces NFR-3).
- **Foundation/infra**: project scaffold (backend `app/` layers + frontend `src/`), `docker-compose.yml` orchestrating `api` + `amazon/dynamodb-local` + `frontend`; DynamoDB table + GSI provisioning for local; seed script (FR-16).
- **Stack (pinned)**: Python 3.13 / FastAPI 0.139.x / Uvicorn / Pydantic v2 / boto3; Node 22 LTS / TypeScript 5.x / React 19.2 / Vite 8.1; `amazon/dynamodb-local`; pytest + Vitest.

### UX Design Requirements

None — no UX design contract exists for this POC. UI stories specify functional acceptance criteria and reference the interaction behaviors defined in the PRD (empty states, inline validation, add-to-cart feedback).

### FR Coverage Map

- FR-1: Epic 1 — paginated catalog browse (PLP)
- FR-2: Epic 1 — free-text search
- FR-3: Epic 1 — category facet filtering
- FR-4: Epic 1 — sorting
- FR-16: Epic 1 — synthetic catalog seed (enabling)
- FR-5: Epic 2 — view product detail (PDP)
- FR-6: Epic 3 — add to cart from PDP
- FR-7: Epic 3 — establish guest session
- FR-8: Epic 3 — view cart
- FR-9: Epic 3 — update line item quantity
- FR-10: Epic 3 — remove line item
- FR-11: Epic 3 — cart totals
- FR-12: Epic 4 — enter shipping details
- FR-13: Epic 4 — simulated payment
- FR-14: Epic 4 — place order
- FR-15: Epic 4 — order summary

## Epic List

### Epic 1: Browse & Discover the Catalog (Foundation + PLP)
A shopper can open the storefront and browse, search, filter, and sort products. Early stories stand up the walking skeleton (ports-and-adapters backend scaffold, React/Vite frontend, `docker-compose` with `amazon/dynamodb-local`, Products table + `gsi_category`/`gsi_listing`, idempotent seed), then deliver the PLP end-to-end. Standalone; establishes the full stack for the read path.
**FRs covered:** FR-16, FR-1, FR-2, FR-3, FR-4

### Epic 2: Inspect a Product (PDP)
A shopper can open a Product to see full detail (name, description, price, images, availability), with a not-found state for unknown ids. Standalone; builds on the catalog from Epic 1.
**FRs covered:** FR-5

### Epic 3: Shopping Cart
A shopper can add Products to a Cart and manage it — view line items and totals, change quantities, remove items — persisted across reloads via an opaque Guest Token. Includes guest-session establishment and the add-to-cart action (placed here because it requires cart infrastructure, avoiding a forward dependency in Epic 2).
**FRs covered:** FR-6, FR-7, FR-8, FR-9, FR-10, FR-11

### Epic 4: Guest Checkout & Order
A shopper can check out as a guest and see an order confirmation: enter shipping details (inline validation), complete a simulated (success-only) payment, place the order as an immutable record with a reference number (clearing the Cart atomically), and view the Order Summary.
**FRs covered:** FR-12, FR-13, FR-14, FR-15

---

## Epic 1: Browse & Discover the Catalog (Foundation + PLP)

A shopper can open the storefront and browse, search, filter, and sort products. Early stories stand up the walking skeleton, then deliver the PLP end-to-end. Covers FR-16, FR-1, FR-2, FR-3, FR-4. Governed by AD-1, AD-3, AD-4, AD-5, AD-8, AD-9.

### Story 1.1: Project scaffold and local runtime (walking skeleton)

As the builder,
I want the backend, frontend, and local DynamoDB running together from one command,
So that every later story has a working end-to-end stack to build on.

**Acceptance Criteria:**

**Given** a clean checkout of the repo
**When** I run `docker-compose up`
**Then** three services start — the FastAPI `api`, `amazon/dynamodb-local`, and the React/Vite `frontend`
**And** the backend is scaffolded in the ports-and-adapters layout (`api/`, `services/`, `repositories/`, `models/`, `core/`) per AD-1
**And** the API exposes a health endpoint returning 200 and serves auto-generated OpenAPI docs (AD-5)
**And** all environment-specific values (DynamoDB endpoint, table names, CORS origins, `flatShipping`) are read from env vars (AD-8), with no per-request state held in memory (AD-9)
**And** the frontend loads in the browser and can reach the API (CORS configured).

### Story 1.2: Provision the Products table and seed a synthetic catalog

As the builder,
I want a Products table with its search indexes and a repeatable seed of sample products,
So that the storefront has realistic content to browse, search, filter, and sort.

**Acceptance Criteria:**

**Given** DynamoDB Local is running
**When** the local provisioning/seed script runs
**Then** a `Products` table is created with `PK = productId`, plus `gsi_category` (PK=category, SK=price) and `gsi_listing` (PK="PRODUCT", SK=price) per AD-3 and AD-4
**And** a synthetic catalog of ~100–500 Products across several categories is loaded, each with id, name, description, price (integer minor units per AD-6), category, image reference, and availability
**And** running the seed again is idempotent (no duplicates, safe re-run) — satisfies FR-16
**And** all DynamoDB access is confined to a `ProductsRepository` adapter (AD-1, AD-3).

### Story 1.3: Browse the catalog with pagination

As an anonymous shopper,
I want to see products in a paginated list,
So that I can explore the catalog without loading everything at once.

**Acceptance Criteria:**

**Given** a seeded catalog
**When** I open the PLP
**Then** `GET /products` returns a bounded page of Products (default ~24) via `gsi_listing`, each with name, price, image, and a link to its PDP — satisfies FR-1
**And** the response includes an opaque base64 pagination cursor (never a raw `LastEvaluatedKey`) per AD-4
**When** I page forward/back
**Then** the next/previous page loads using the cursor
**And** the PLP renders the results as a grid consuming the typed API client (AD-5).

### Story 1.4: Search products by keyword

As an anonymous shopper,
I want to search products by keyword,
So that I can quickly find items matching what I have in mind.

**Acceptance Criteria:**

**Given** a seeded catalog
**When** I enter a keyword and submit
**Then** `GET /products?search=...` returns Products whose name or description matches, via a DynamoDB `FilterExpression` `contains` per AD-4 — satisfies FR-2
**And** non-matching Products are excluded
**When** the query matches nothing
**Then** the PLP shows an explicit empty state with a clear action to reset the search.

### Story 1.5: Filter by category facet

As an anonymous shopper,
I want to filter products by category,
So that I can narrow the catalog to what I care about.

**Acceptance Criteria:**

**Given** a seeded catalog
**When** I select one or more category values
**Then** results are filtered to matching Products via `gsi_category` per AD-4 — satisfies FR-3
**And** multiple selected categories combine predictably
**And** active filters are visible and individually removable, with a clear-all control
**When** a search term and a category are both active
**Then** they combine (search, then filter within results).

### Story 1.6: Sort results

As an anonymous shopper,
I want to sort the listing,
So that I can view products in the order most useful to me.

**Acceptance Criteria:**

**Given** a PLP result set (with or without search/filters active)
**When** I choose a sort (price low→high, price high→low, or default)
**Then** the current results reorder accordingly — satisfies FR-4
**And** changing sort preserves any active search term and category filters
**And** pagination continues to work under the chosen sort.

## Epic 2: Inspect a Product (PDP)

A shopper can open a Product to see full detail. Covers FR-5. Governed by AD-1, AD-5.

### Story 2.1: View product detail

As an anonymous shopper,
I want to open a product and see its full details,
So that I can decide whether to buy it.

**Acceptance Criteria:**

**Given** a seeded catalog
**When** I open a PDP by product id (e.g. from a PLP link)
**Then** `GET /products/{id}` returns the Product and the page shows its name, description, price, image(s), and availability — satisfies FR-5
**When** the id does not exist
**Then** the API returns a 404 with the `{error:{code,message}}` envelope (AD-5) and the UI shows a not-found state
**And** all data access remains inside the `ProductsRepository` (AD-1).

## Epic 3: Shopping Cart

A shopper can add Products to a Cart and manage it, persisted across reloads via an opaque Guest Token. Covers FR-6, FR-7, FR-8, FR-9, FR-10, FR-11. Governed by AD-2, AD-3, AD-6, AD-9.

### Story 3.1: Establish an anonymous guest session

As an anonymous shopper,
I want the site to remember my cart without asking me to log in,
So that I can shop freely and keep my items across page loads.

**Acceptance Criteria:**

**Given** a first-time visitor with no guest token
**When** the client first needs a cart
**Then** the API issues an opaque `guestId` (UUID) and the client stores it and sends it on every cart/order request via the `X-Guest-Token` header per AD-2
**And** a `Carts` table keyed by `guestId` exists, accessed only through a `CartsRepository` (AD-3)
**And** subsequent requests with the same token resolve to the same Cart — satisfies FR-7
**And** no login, account, or personal identity is required at any point.

### Story 3.2: Add a product to the cart from the PDP

As an anonymous shopper,
I want to add a product to my cart from its detail page,
So that I can collect items I intend to buy.

**Acceptance Criteria:**

**Given** I am viewing a PDP with a valid guest token
**When** I add the product with a quantity of at least 1
**Then** `POST /cart/items` creates or updates the corresponding Line Item under my `guestId` — satisfies FR-6
**And** unit price is captured in integer minor units (AD-6)
**And** the UI gives clear feedback (e.g. the cart count updates).

### Story 3.3: View the cart with totals

As an anonymous shopper,
I want to see everything in my cart with a running total,
So that I know what I am about to buy and what it costs.

**Acceptance Criteria:**

**Given** I have items in my cart
**When** I open the cart
**Then** `GET /cart` returns each Line Item (product, unit price, quantity, line total) and the cart page displays them — satisfies FR-8
**And** the page shows the Subtotal = Σ(unitPrice × qty) and an Order Total = Subtotal + `flatShipping` (config constant, no tax) per AD-6 — satisfies FR-11
**When** I reload the page within the same session
**Then** the cart contents persist (keyed by `guestId`).

### Story 3.4: Update a line item quantity

As an anonymous shopper,
I want to change how many of an item I'm buying,
So that my cart reflects what I actually want.

**Acceptance Criteria:**

**Given** a Line Item in my cart
**When** I change its quantity to a positive number
**Then** `PATCH /cart/items/{productId}` updates it and the line total and Subtotal/Order Total recompute — satisfies FR-9
**When** I set the quantity to 0
**Then** the Line Item is removed from the cart.

### Story 3.5: Remove a line item

As an anonymous shopper,
I want to remove an item from my cart,
So that I don't buy something I changed my mind about.

**Acceptance Criteria:**

**Given** a Line Item in my cart
**When** I remove it
**Then** `DELETE /cart/items/{productId}` removes it and it no longer appears — satisfies FR-10
**And** the Subtotal and Order Total recompute accordingly.

## Epic 4: Guest Checkout & Order

A shopper can check out as a guest and see an order confirmation. Covers FR-12, FR-13, FR-14, FR-15. Governed by AD-3, AD-5, AD-6, AD-7.

### Story 4.1: Enter shipping details

As an anonymous shopper,
I want to enter where my order should ship,
So that my purchase can be delivered.

**Acceptance Criteria:**

**Given** I have items in my cart and start checkout
**When** I fill in the shipping form (name, address line(s), city, region, postal code, country, email)
**Then** required fields are validated inline before I can proceed — satisfies FR-12
**And** invalid or missing input is surfaced clearly next to the field
**And** no data is persisted until the order is placed (AD-7).

### Story 4.2: Complete a simulated payment

As an anonymous shopper,
I want to complete a payment step,
So that I can finish my purchase.

**Acceptance Criteria:**

**Given** valid shipping details
**When** I proceed through the payment step
**Then** the payment is simulated and always succeeds — satisfies FR-13
**And** no real payment gateway is called and no card data is collected or stored (data minimization, NFR-4)
**And** on success the flow proceeds to order placement.

### Story 4.3: Place the order

As an anonymous shopper,
I want to place my order,
So that my purchase is recorded and my cart is finalized.

**Acceptance Criteria:**

**Given** valid shipping details and a successful simulated payment
**When** I place the order
**Then** `POST /checkout` writes an immutable Order to the `Orders` table — a snapshot of line items (unit prices frozen), Subtotal, Order Total, shipping details, a human-readable reference number, and a UTC timestamp — per AD-3, AD-6, AD-7 — satisfies FR-14
**And** the Cart is cleared as part of the same operation (AD-7)
**And** the Order is never modified after creation.

### Story 4.4: View the order summary

As an anonymous shopper,
I want to see a confirmation of what I ordered,
So that I know the purchase went through and what it included.

**Acceptance Criteria:**

**Given** I have just placed an order
**When** the Order Summary displays
**Then** it shows the reference number, line items, Subtotal, Order Total, and shipping details, reflecting the persisted Order exactly — satisfies FR-15
**And** the summary is shown immediately after checkout (there is no order-lookup page, consistent with the anonymous, account-free design).
