---
title: Anonymous E-Commerce Storefront
status: final
created: 2026-07-06
updated: 2026-07-06
---

# PRD: Anonymous E-Commerce Storefront
*Working title — confirm.*

## 0. Document Purpose

This PRD is for the builder (Artem) and the downstream BMAD workflows (UX, Architecture, Epics/Stories). It builds on the finalized product brief at `_bmad-output/planning-artifacts/briefs/brief-bmad-ecommerce-2026-07-06/brief.md` and does not duplicate its framing. It is structured as: a Glossary that fixes vocabulary, features grouped with globally-numbered Functional Requirements (FR-N) nested under them, cross-cutting NFRs in their own section, and inline `[ASSUMPTION]` tags indexed at the end. Technology *choices* are deliberately deferred to the Architecture phase; this document states capabilities, not implementation.

## 1. Vision

A guest-only e-commerce storefront that carries an anonymous shopper through the full purchase funnel — browse (PLP), inspect (PDP), cart, guest checkout, order summary — with no accounts and no authentication anywhere. A shopper arrives, shops, and buys without ever signing in.

This is a **learning / proof-of-concept** build. Its purpose is to exercise the BMAD method end-to-end against a realistic full-stack shape (Python/FastAPI API, DynamoDB, TypeScript/React UI) that runs locally end-to-end. The one deliberately "real" technical target is **faceted search over a DynamoDB-backed catalog** — the most interesting problem in the slice. Success is a clean, complete, working loop, not revenue.

## 2. Target User

### 2.1 Jobs To Be Done

- **As the builder:** exercise BMAD from PRD to running code against a representative commerce slice, and validate the Python/AWS/TypeScript stack.
- **As the modeled shopper:** find a product quickly (search + filter), understand it (PDP), and buy it without a login wall.

### 2.2 Non-Users (v1)

- Registered/returning customers (no accounts exist).
- Store operators / merchandisers (no admin surface).
- Anyone requiring real payment, real fulfillment, or post-purchase account features.

### 2.3 Key User Journeys

- **UJ-1. Sam finds and buys a specific item as a guest.**
  - **Persona + context:** Sam, a first-time anonymous visitor who knows roughly what they want.
  - **Entry state:** Not authenticated; lands on the PLP. No login is ever requested.
  - **Path:** searches by keyword → narrows with the category facet and sorts by price → opens a PDP → adds to cart → opens cart, adjusts quantity → checks out as guest (shipping + simulated payment) → places order.
  - **Climax:** the order is placed and an order summary with a reference number is shown.
  - **Resolution:** Sam sees confirmation of what they bought; the cart is cleared. Realizes FR-2, FR-3, FR-4, FR-5, FR-6, FR-8..FR-15.
  - **Edge case:** if a filter/search combination returns nothing, the PLP shows an empty-state with a clear way to reset filters.

- **UJ-2. Sam browses without a goal.**
  - Sam, no specific target, lands on the PLP and pages through the catalog, using category facets and sort to explore, then drills into a PDP. Realizes FR-1, FR-3, FR-4, FR-5.

## 3. Glossary

*FRs, UJs, and metrics use these terms verbatim; no synonyms elsewhere.*

- **Catalog** — the full set of Products available to browse.
- **Product** — a sellable item with attributes (id, name, description, price, category, image(s), availability). Single price, single currency, no variants/SKUs in v1. *(confirmed)*
- **PLP (Product Listing Page)** — a paginated view over the Catalog supporting search, facets, and sort.
- **PDP (Product Detail Page)** — the detail view of one Product.
- **Facet** — a filterable Product attribute with selectable values. In v1 the only facet is **category**. *(confirmed; extensible in future)*
- **Cart** — the collection of Line Items for one anonymous shopper, keyed by Guest Token.
- **Line Item** — a Product plus quantity within a Cart.
- **Guest Token** — an opaque identifier that ties a Cart (and later an Order) to one anonymous browser session, with no personal identity. [ASSUMPTION: issued by the API, stored client-side; see NFRs.]
- **Checkout** — the flow that converts a Cart into an Order (shipping details + simulated payment).
- **Order** — an immutable record of a placed purchase: line items, totals, shipping details, reference number, timestamp.
- **Order Summary** — the confirmation view of a placed Order.
- **Subtotal** — sum of (Line Item price × quantity) across the Cart.
- **Order Total** — Subtotal plus a flat placeholder for shipping/tax. [ASSUMPTION: flat placeholder value, e.g. fixed shipping fee, zero tax; exact value TBD in build.]

## 4. Features

### 4.1 Catalog Browsing (PLP)

**Description:** The anonymous shopper browses the Catalog on the PLP with free-text search, faceted filtering, sorting, and pagination — all without authentication. This is the primary learning target of the project. Realizes UJ-1, UJ-2.

**Functional Requirements:**

#### FR-1: Browse paginated catalog
An anonymous shopper can view the Catalog as a paginated list of Products. Realizes UJ-2.
**Consequences (testable):**
- The PLP returns a bounded page of Products with a page size and a way to page forward/back. [ASSUMPTION: default page size ~24.]
- Each result shows at least name, price, image, and links to its PDP.

#### FR-2: Free-text search
An anonymous shopper can search Products by keyword and see matching results on the PLP.
**Consequences (testable):**
- A keyword query returns Products whose name and/or description match; non-matching Products are excluded.
- An empty result set renders an explicit empty-state with a reset action.

#### FR-3: Faceted filtering
An anonymous shopper can narrow PLP results by selecting one or more category Facet values. (Category is the only facet in v1.)
**Consequences (testable):**
- Selecting one or more categories filters results to matching Products; multiple selections combine predictably.
- Active filters are visible and individually removable; a clear-all resets them.
- Search + facet combine (search then filter within results). [ASSUMPTION]

#### FR-4: Sorting
An anonymous shopper can sort PLP results (e.g. price low→high, high→low, and a default/relevance order).
**Consequences (testable):**
- Changing sort reorders the current result set without losing active search/filters.

**Feature-specific NFRs:**
- PLP search+filter+sort round-trip returns within a reasonable interactive budget on the seeded catalog. [ASSUMPTION: p95 < 500ms locally; confirm in Architecture.]

### 4.2 Product Detail (PDP)

**Description:** The shopper opens a single Product to see full detail and add it to the Cart. Realizes UJ-1.

#### FR-5: View product detail
An anonymous shopper can view a PDP showing the Product's name, description, price, image(s), and availability.
**Consequences (testable):**
- A valid Product id renders its detail; an unknown id renders a not-found state.

#### FR-6: Add to cart from PDP
An anonymous shopper can add a Product to the Cart from its PDP, with a quantity of at least 1.
**Consequences (testable):**
- Adding a Product creates or updates the corresponding Line Item in the shopper's Cart.
- The shopper gets clear feedback that the item was added (e.g. cart count updates).

### 4.3 Cart

**Description:** The Cart holds Line Items for one anonymous session, keyed by Guest Token, and persists across page reloads within that session. Realizes UJ-1.

#### FR-7: Establish guest session
The system issues and recognizes a Guest Token so a Cart can persist for an anonymous shopper without any login.
**Consequences (testable):**
- A first-time visitor is assigned a Guest Token; subsequent requests in the same session resolve to the same Cart.
- No personal identity is required or collected to hold a Cart.

#### FR-8: View cart
An anonymous shopper can view the Cart: each Line Item (product, unit price, quantity, line total) and the Subtotal.
**Consequences (testable):**
- Cart contents survive a page reload within the same session. [Success criterion from brief.]

#### FR-9: Update line item quantity
An anonymous shopper can change the quantity of a Line Item.
**Consequences (testable):**
- Setting quantity recomputes line total and Subtotal; setting quantity to 0 removes the Line Item. [ASSUMPTION]

#### FR-10: Remove line item
An anonymous shopper can remove a Line Item from the Cart.
**Consequences (testable):**
- Removed items no longer appear; Subtotal recomputes.

#### FR-11: Cart totals
The Cart displays Subtotal and an Order Total using a flat placeholder for shipping/tax.
**Consequences (testable):**
- Subtotal = sum of line totals; Order Total = Subtotal + flat placeholder. [ASSUMPTION: no tax/shipping calculation — flat value only.]

### 4.4 Guest Checkout

**Description:** Checkout converts the Cart into an Order by collecting shipping details and a simulated payment, then placing the order — no account, no real gateway. Realizes UJ-1.

#### FR-12: Enter shipping details
An anonymous shopper can enter shipping details (name, address fields, contact). [ASSUMPTION: fields = name, address line(s), city, region, postal code, country, email.]
**Consequences (testable):**
- Required fields are validated before the order can be placed; invalid input is surfaced inline.

#### FR-13: Simulated payment
An anonymous shopper completes a simulated payment step that always succeeds (no real charge, no real card data stored). No failure path in v1.
**Consequences (testable):**
- The payment step requires no real gateway and stores no real card data.
- The step always resolves as success and proceeds to order placement.

#### FR-14: Place order
An anonymous shopper can place the Order, converting the Cart into an immutable Order with a reference number.
**Consequences (testable):**
- Placing an Order persists it (line items snapshot, totals, shipping details, reference number, timestamp).
- The Cart is cleared after a successful order. [ASSUMPTION]

### 4.5 Order Summary

**Description:** After placing an Order, the shopper sees a confirmation summary. Realizes UJ-1.

#### FR-15: View order summary
An anonymous shopper sees an Order Summary confirming the placed Order: reference number, line items, totals, and shipping details.
**Consequences (testable):**
- The summary reflects the persisted Order exactly.
- The summary is shown immediately post-checkout; there is no retrievable order-lookup page in v1 (no accounts, no order history). *(confirmed — appropriate for an anonymous experience)*

### 4.6 Catalog Seed Data (supporting)

**Description:** The Catalog is populated from seeded synthetic data so every other feature has content to work against. Not a shopper-facing feature.

#### FR-16: Seed synthetic catalog
The system provides a repeatable way to load a synthetic Catalog (products with the attributes facets/search/sort depend on) into the data store.
**Consequences (testable):**
- Running the seed yields a Catalog large and varied enough to exercise search, at least two facets, and sorting. [ASSUMPTION: ~100–500 products across several categories.]
- The seed is idempotent/repeatable for local runs.

## 5. Cross-Cutting NFRs

- **No authentication / no identity.** No login, registration, or account exists anywhere. The only session concept is the opaque Guest Token (FR-7).
- **Local-first, containerized.** The system runs end-to-end locally: containerized API + local/emulated DynamoDB. This is the definition of "done." Deploying to real AWS ECS is a future enhancement, not a v1 requirement.
- **Stateless API.** The API holds no in-memory session state between requests (Cart/Order state lives in the data store keyed by Guest Token), so it is horizontally scalable / container-friendly. [ASSUMPTION]
- **Data minimization.** No real payment data is ever collected or stored. Shipping details are stored only as part of a placed Order. [ASSUMPTION: no PII beyond order shipping details; no analytics/tracking.]
- **Performance.** Interactive PLP operations feel responsive on the seeded catalog (see FR-4 feature NFR). Firm budgets deferred to Architecture.
- **Accessibility.** Baseline keyboard navigability and semantic markup for the core flows. [ASSUMPTION: WCAG "reasonable effort," not a formal AA audit for a POC.]
- **API contract.** The frontend and backend integrate over a documented HTTP/JSON API covering all flows above. Contract specifics defined in Architecture.

## 6. Non-Goals (Explicit)

- Not building accounts, login, or any authentication.
- Not integrating a real payment gateway or processing real charges.
- Not integrating an external catalog/PIM; catalog is seeded synthetic data.
- Not building admin, merchandising, or inventory-management surfaces.
- Not calculating promotions, discounts, taxes, or shipping rates (flat placeholder only).
- Not building order history, returns, or any post-purchase account features.
- Not sending email or notifications.

## 7. MVP Scope

### 7.1 In Scope
- PLP with search, faceted filtering, sorting, pagination (FR-1..FR-4)
- PDP with add-to-cart (FR-5, FR-6)
- Cart with guest-token persistence, quantity update, remove, totals (FR-7..FR-11)
- Guest checkout: shipping details, simulated payment, order placement (FR-12..FR-14)
- Order summary (FR-15)
- Seeded synthetic catalog (FR-16)
- FastAPI backend + React/TypeScript frontend, running locally against local/emulated DynamoDB

### 7.2 Out of Scope for MVP
- AWS ECS deployment — deferred; a future enhancement, not required for "done."
- All Non-Goals in §5 (accounts, real payment, PIM, admin, promotions/tax/shipping calc, order history, notifications).

## 8. Success Metrics

**Primary**
- **SM-1**: The full loop completes end-to-end — search → filter → PDP → add to cart → guest checkout → order summary — with a placed Order persisted. Validates FR-1..FR-15.
- **SM-2**: PLP search returns relevant results with working facets, sort, and pagination on the seeded catalog. Validates FR-1..FR-4.
- **SM-3**: Cart contents survive a page reload within a session (keyed by Guest Token). Validates FR-7, FR-8.

**Secondary**
- **SM-4**: The system runs entirely locally (containerized API + local/emulated DynamoDB) from a documented setup. Validates §5 local-first NFR.

**Counter-metrics (do not optimize)**
- **SM-C1**: Do not add features or polish beyond the slice to chase "completeness" — scope creep defeats the POC's purpose. Counterbalances SM-1.

## 9. Open Questions

1. **Non-functional targets** (latency budgets, eventual AWS region/cost) — deferred to Architecture.
2. **Flat placeholder value** for shipping/tax — pick a concrete value during build.
3. **Catalog size/shape** for the seed — confirm product count and category set during Architecture/build.

## 10. Assumptions Index

- §3 — Guest Token issued by API, stored client-side.
- §3 — Order Total = Subtotal + flat placeholder (fixed shipping, zero tax); value TBD.
- §4.1 FR-1 — default page size ~24.
- §4.1 FR-3 — search and category facet combine (filter within search results).
- §4.1 NFR — PLP p95 < 500ms locally (confirm in Architecture).
- §4.3 FR-9 — quantity 0 removes the line item.
- §4.4 FR-12 — shipping fields = name, address, city, region, postal code, country, email.
- §4.6 FR-16 — ~100–500 seeded products across several categories; idempotent seed.
- §5 — stateless API; data minimization (no PII beyond order shipping); baseline (not formal AA) accessibility.

*Confirmed by user (no longer open): single-price products / no variants; category is the only facet; simulated payment is success-only; cart cleared after order; no order-lookup page.*
