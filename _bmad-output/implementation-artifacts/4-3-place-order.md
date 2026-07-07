---
baseline_commit: 2742fb054d8e24a2b3d2e8dd7cbe81ef0068dfea
---

# Story 4.3: Place the order

Status: done

## Story

As an anonymous shopper,
I want to place my order,
so that my purchase is recorded and my cart is finalized.

## Acceptance Criteria

1. **Given** valid shipping details and a successful simulated payment, **When** I place the order, **Then** `POST /checkout` writes an **immutable Order** to the `Orders` table — a snapshot of line items (unit prices frozen), Subtotal, Order Total, shipping details, a human-readable **reference number**, and a **UTC timestamp** — per AD-3, AD-6, AD-7 — satisfies FR-14.
2. **Given** the order is placed, **Then** the **Cart is cleared as part of the same operation** — the Order write and the Cart delete happen **atomically** (DynamoDB `TransactWriteItems`) so a shopper can never end up charged-with-no-cart or cart-cleared-with-no-order (AD-7).
3. **Given** the Order exists, **Then** it is **never modified** after creation (immutable).
4. **Given** an empty cart (no items) or a missing/invalid guest token, **When** `POST /checkout` is called, **Then** it returns a 4xx with the `{error:{code,message}}` envelope (e.g. `empty_cart` 409 / `invalid_guest_token` 400) — never creates an empty order.
5. **Given** the frontend, **When** I click Place order (shipping valid), **Then** it calls `POST /checkout`, and on success routes to the Order Summary (Story 4.4) and the header cart count resets to 0.

## Tasks / Subtasks

- [x] **Task 1 — Order model + shipping model (AC: 1)** — `models/order.py`: `ShippingDetails(CamelModel)` (fullName, address1, address2?, city, region, postalCode, country, email); `Order(CamelModel)` (orderId, reference, guestId, items: list[CartLine-shape], subtotal, shipping, orderTotal, shipping: ShippingDetails, createdAt ISO-8601 UTC). Money integer cents (AD-6).
- [x] **Task 2 — OrdersRepository (AC: 1, 2, 3)** — `repositories/orders.py`: sole owner of the `Orders` table (PK `orderId`, no GSI). `ensure_table`; `_to_item`/`_from_item` (items as List-of-Maps, shipping as a Map); `get_order(order_id)`; and a **transactional place**: `place_order_txn(order, cart_guest_id)` using `transact_write_items` with a `Put` of the Order and a `Delete` of the `Carts` item (guestId) — one atomic call (AD-7). Guard `ClientError` (e.g. `TransactionCanceledException`).
- [x] **Task 3 — CheckoutService (AC: 1, 3, 4)** — `services/checkout.py`: `place_order(guest_id, shipping)`: load the cart (via `CartsRepository`); if empty → `AppError empty_cart 409`; build the immutable `Order` snapshot from the cart lines + totals + shipping + generated reference (`ORD-<8 hex>`) + `orderId` (uuid) + UTC timestamp; call `orders.place_order_txn(order, guest_id)`; return the `Order`. No boto3 in the service.
- [x] **Task 4 — API + provisioning (AC: 1, 4)** — `api/checkout.py`: `POST /checkout` (body `{shipping}`, `X-Guest-Token` header → `resolve_guest_id`; echo token; return the `Order`); `GET /orders/{orderId}` (returns the immutable order, scoped to the caller's guest token → 404 if the token doesn't own it, for the confirmation page — no browsable history). Register the router. Extend `scripts/provision.py` to ensure the `Orders` table.
- [x] **Task 5 — Frontend wire Place order (AC: 5)** — `client.placeOrder(shipping)` (`POST /checkout`) + `getOrder(orderId)` (`GET /orders/{id}`) + `Order`/`ShippingDetails` types. `CheckoutPage` Place-order button (enabled; reveals errors on invalid submit) → on valid submit calls `placeOrder(form)`, then `refresh()` the cart count (now 0) and navigate to `/order/{orderId}` (Story 4.4). Error → inline message; the button re-enables.
- [x] **Task 6 — Tests + verify** — repo: transactional place writes the order AND deletes the cart (moto); `get_order` round-trip. Service: place_order builds the snapshot + reference + timestamp; empty cart → 409. API: `POST /checkout` happy path returns the order + clears the cart (subsequent `GET /cart` empty); empty-cart 409; `GET /orders/{id}` returns it, wrong token → 404. Backend `pytest` green; frontend build; live: add → checkout → place → order returned, `GET /cart` empty, `GET /orders/{id}` returns the immutable order.

## Dev Notes

- **Atomicity is the whole point (AD-7).** Use DynamoDB `TransactWriteItems` with two actions: `Put` the Order (into `orders_table`) and `Delete` the Cart item (from `carts_table`, key `guestId`). One transaction → the order-created and cart-cleared invariant can't half-apply. This is the Epic 3 retro action item #1 — the cart's read-modify-write put is NOT sufficient here.
- **Immutable Order (AD-7):** snapshot everything at placement (frozen unit prices from the cart lines, totals, shipping details, reference, timestamp). Never update an Order after creation; there is no PATCH/PUT.
- **Reference number:** human-readable, e.g. `f"ORD-{uuid4().hex[:8].upper()}"`. `orderId` = `str(uuid4())`. Timestamp = `datetime.now(timezone.utc).isoformat()`.
- **Reuse:** cart lines + totals come from the existing cart (`CartsRepository.get_cart` + `CartsService.to_view` math, or recompute the same way — keep integer cents, AD-6). Guest token resolution reuses `CartsService.resolve_guest_id` semantics (or a shared helper); malformed → 400.
- **Confirmation, not history (FR-15):** `GET /orders/{orderId}` exists only so the Order Summary page is refresh-safe; scope it to the guest token (the order stores `guestId`; mismatched/absent token → 404). There is no list/browse endpoint (account-free).
- **Scope:** order placement + retrieval-by-id + wiring. The Order Summary *page* is Story 4.4 (it consumes `GET /orders/{id}`).
- [Source: epics.md Epic 4 / 4.3; ARCHITECTURE-SPINE AD-3 (Orders table/repo), AD-6 (cents), AD-7 (immutable + atomic clear); epic-3-retro action items 1 & 2; EXPERIENCE.md (order placed, success-only)]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Debug Log References

- Epic 4 (4.1-4.4) built cohesively then reviewed together. `pytest -q` → 93 passed; frontend `tsc -b && vite build` clean. Live (docker): add in-stock product → `POST /checkout` returns the Order (reference `ORD-…`, integer-cents totals, UTC timestamp, shipping snapshot); **cart cleared atomically** (`GET /cart` empty); `GET /orders/{id}` owner → 200, wrong token → 404; empty-cart place → 409; invalid shipping → 422.

### Completion Notes List

- **Atomic place-order (AD-7):** `OrdersRepository.place_order_txn` uses DynamoDB `TransactWriteItems` (Put Order + Delete Cart) — one transaction, so order-created and cart-cleared can't half-apply. This closes Epic 3 retro action item #1 (the cart's read-modify-write put was insufficient). `Orders` table + `OrdersRepository` added (AD-3); `provision.py` extended.
- **Immutable Order (AD-7):** snapshot at placement (frozen line items + totals + shipping + reference `ORD-<hex>` + `orderId` uuid + UTC `createdAt`); no mutation path.
- **Shared guest resolution:** extracted `core/guest.resolve_guest_id` (issue/validate/canonicalize); `CartsService` now delegates to it (behavior-preserving) and `CheckoutService`/API reuse it.
- **`GET /orders/{id}`** is confirmation-by-id, scoped to the owning guest token (404 otherwise) — no browsable history (FR-15).
- **Review patches (2-pass):** server-side `ShippingDetails` validation (required non-empty + email → 422, no longer client-trusted); `ClientError` mapping narrowed (only `TransactionCanceled*` → 409, others re-raise as 500); frontend navigates before `refresh()` and routes `empty_cart` → `/cart`; OrderSummary guards `items` shape + shows `createdAt`.

### File List

Shared across Epic 4 (built together):
- `backend/app/core/guest.py` (A) — shared `resolve_guest_id`.
- `backend/app/models/order.py` (A) — `ShippingDetails` (validated), `Order`, `PlaceOrderRequest`.
- `backend/app/repositories/orders.py` (A) — `OrdersRepository` + `place_order_txn` (atomic).
- `backend/app/services/checkout.py` (A) — `CheckoutService.place_order` / `get_order`.
- `backend/app/api/checkout.py` (A) — `POST /checkout`, `GET /orders/{id}`.
- `backend/app/api/__init__.py` (M) — register checkout router.
- `backend/app/services/cart.py` (M) — delegate `resolve_guest_id` to `core/guest`.
- `backend/scripts/provision.py` (M) — ensure `Orders` table.
- `backend/tests/test_orders_repository.py` (A), `backend/tests/test_checkout_api.py` (A).
- `frontend/src/api/client.ts` (M) — generic `authedFetch<T>`; `Order`/`ShippingDetails`; `placeOrder`/`getOrder`.
- `frontend/src/pages/CheckoutPage.tsx` (A) — shipping form + payment notice + place-order (4.1/4.2/4.3).
- `frontend/src/pages/OrderSummaryPage.tsx` (A) — confirmation (4.4).
- `frontend/src/App.tsx` (M) — `/checkout` + `/order/:orderId` routes.
- `frontend/src/pages/CartPage.tsx` (M) — Checkout button → `/checkout`.

### Review Findings

*Code review 2026-07-07 (Blind Hunter + Edge Case Hunter + Acceptance Auditor), covering Stories 4.1-4.4 together. Approve-with-patches. All ACs across 4.1-4.4 satisfied; AD-1/3/5/6/7 hold; money + atomicity core verified. Severity at triage; reviewer in parens.*

- [x] [Review][Patch] **MED — no server-side shipping validation** [backend/app/models/order.py] — `ShippingDetails` was bare `str`; a direct `POST /checkout` could persist an immutable order with empty address / invalid email (client-trusted). Fix: required fields `StringConstraints(strip_whitespace, min_length=1)` + email regex validator → 422; test added. (blind + edge)
- [x] [Review][Patch] **MED — blanket `ClientError → 409 order_failed`** [backend/app/repositories/orders.py] — masked throttling/internal faults as a retryable conflict. Fix: only `TransactionCanceled*` → 409; re-raise the rest (→ 500 envelope). (blind + edge)
- [x] [Review][Patch] LOW — place-order coupled navigate to `refresh()` [frontend/src/pages/CheckoutPage.tsx] — navigate to the summary first, then fire-and-forget `refresh()`; route `empty_cart` → `/cart` (retry can't succeed). (edge)
- [x] [Review][Patch] LOW — OrderSummary didn't guard `items` shape / didn't show the order date [frontend/src/pages/OrderSummaryPage.tsx] — added an `Array.isArray` guard + render `createdAt`. (blind + edge)
- [x] [Review][Patch] LOW — stale CheckoutPage header comment ("not yet wired") [frontend/src/pages/CheckoutPage.tsx] — updated to reflect the wired place-order. (blind)
- [x] [Review][Defer] LOW — cart read→write is not conditional (a concurrent add between snapshot and the transaction is dropped) [backend] — POC single-user; a cart-version `ConditionExpression` on the Delete is the fix. → deferred-work.
- [x] [Review][Defer] LOW — `reference` is 32 bits (birthday-collision at scale); display-only (orderId is the key). → deferred-work.
- [x] [Review][Defer] LOW — `guestId` (session bearer) returned in Order/Cart bodies [pre-existing Epic 3 pattern] — omit from the response projection later. → deferred-work.
- [x] [Review][Defer] LOW — place-order client timeout after a server-side commit shows an unrecoverable error [frontend] — indeterminate-state reconciliation; POC-acceptable. → deferred-work.

*Dismissed (1): EXPERIENCE.md says "Place-order button disabled while invalid" but we use reveal-on-submit — Story 4.1 AC6 permits "gate so clicking does nothing beyond validation," and reveal-on-submit is better UX (a disabled button leaves an untouched required field with no error cue — the exact gap raised in the 4.1 review).*
