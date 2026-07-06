---
title: "Product Brief: Anonymous E-Commerce Storefront"
status: complete
created: 2026-07-06
updated: 2026-07-06
---

# Product Brief: Anonymous E-Commerce Storefront

## Executive Summary

A guest-only e-commerce storefront covering the core anonymous shopping journey: browse a catalog (PLP), inspect a product (PDP), build a cart, check out as a guest, and see an order summary. There are no accounts and no authentication anywhere in the experience — a shopper arrives, shops, and buys without ever signing in.

This is a **learning / proof-of-concept** build. Its real purpose is to exercise the BMAD-METHOD end-to-end against a realistic full-stack shape: a **Python (FastAPI) API on AWS ECS/Fargate with DynamoDB**, fronted by a **TypeScript/React UI**. The catalog is seeded with synthetic data and checkout payment is simulated, so no external integrations are required to run the full flow. The one deliberately "real" technical target is a **full search + faceted filtering** experience on the listing page — the most interesting piece to get right on a DynamoDB-backed stack.

Success is not measured in revenue; it is measured in whether the whole loop works cleanly, the code reflects the architecture, and the BMAD workflow produced it.

## The Problem

Teams evaluating an AI-driven development method (BMAD) and a specific cloud stack need a project that is small enough to finish but realistic enough to be honest. Toy "hello world" apps don't surface the real decisions — session/cart state without user accounts, faceted search on a NoSQL store, containerized deployment — while a full commercial storefront is far too large to serve as a learning vehicle. There is no lightweight-but-representative reference to point at.

## The Solution

A minimal storefront that walks an anonymous shopper through the complete purchase funnel:

- **PLP** — browse the catalog with free-text search, faceted filters (e.g. category, price, attributes), sorting, and pagination.
- **PDP** — a single product's detail: images, description, price, availability, add-to-cart.
- **Cart** — view, update quantities, remove line items, see subtotal; persisted against an anonymous session/guest token.
- **Guest checkout** — collect shipping details and a (simulated) payment step, then place the order.
- **Order summary** — a confirmation view of the placed order.

The backend is a FastAPI service (containerized for ECS/Fargate) over DynamoDB tables for products, carts, and orders. The frontend is a React/TypeScript SPA consuming the API. Cart and order state key off a guest/session token rather than a user identity.

## What Makes This Different

This is a reference/learning artifact, not a market entrant, so the "advantage" is honest scope discipline:

- **Representative, not exhaustive** — it includes the decisions that actually teach (guest session state, faceted search on DynamoDB, containerized deploy) and excludes everything that only adds ceremony (accounts, real payments, admin, promotions).
- **Buildable to done** — small enough that the BMAD story cycle can carry it from PRD to running code.
- The value is the *pattern* — a clean, correct slice of a commerce stack — that can later be extended, not a feature-complete product.

## Who This Serves

- **Primary: the builder(s)** — you (Artem) and anyone using this to learn BMAD and validate the Python/AWS/TypeScript stack. Success = the workflow and the code both hang together.
- **Secondary: the anonymous shopper (simulated persona)** — the user whose journey the app models: lands, searches/filters, views a product, adds to cart, checks out as a guest. They never authenticate. Success for them = completing a purchase without friction or a login wall.

## Success Criteria

- A shopper can complete the full loop end-to-end: search → filter → PDP → add to cart → guest checkout → order summary.
- PLP search returns relevant results with working facets, sorting, and pagination.
- Cart state survives page reloads within a session (keyed by guest token).
- The FastAPI service runs in a container and reads/writes DynamoDB (products, carts, orders).
- The React/TypeScript UI consumes the API for every flow.
- The project was produced through the BMAD phases (PRD → architecture → epics/stories → implemented stories).
- Runs locally end-to-end (containerized API + local/emulated DynamoDB) — this is the bar for "done." Deploying to real AWS ECS is a **stretch goal**, not a completion requirement.

## Scope

**In (v1):**
- Anonymous browsing: PLP with full-text search, faceted filtering, sorting, pagination
- PDP with add-to-cart
- Cart: add / update quantity / remove / subtotal, persisted by guest/session token
- Guest checkout: shipping details + simulated payment + order placement
- Order summary / confirmation
- Seeded synthetic catalog in DynamoDB
- FastAPI backend, containerized for ECS/Fargate; React/TypeScript frontend

**Out (explicitly):**
- User accounts, login, registration, or any authentication
- Real payment processing / payment gateways (payment is mocked)
- External catalog/PIM integration (catalog is seeded)
- Admin / merchandising / inventory management UI
- Promotions, discounts, taxes, shipping-rate calculation *(beyond a flat placeholder)*
- Order history, returns, post-purchase account features
- Email / notifications

## Vision

If it succeeds as a learning artifact, this becomes the reference slice a team extends: bolt on real auth, a real payment provider, a real catalog source, and observability, one BMAD epic at a time — turning a clean POC into the seed of a production storefront without rewriting the core.

---

## Decisions Locked

- **"Done" = runs locally** (containerized API + local/emulated DynamoDB). AWS ECS deployment is a future **enhancement**, not part of v1.
- **Tax/shipping** — flat placeholder only; no calculation modeled in v1.
- **Out of scope** confirmed: promotions/discounts/tax/shipping calculation, order history/returns/post-purchase features, email/notifications.

## Open Questions (deferred to Architecture phase)

1. **Non-functionals** — any latency, cost, or (eventual) AWS region constraints worth capturing when we design the architecture. Not blocking the brief.
