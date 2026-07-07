---
baseline_commit: e412f85cccd5de809117defd8ac86b7a5e4ab6c0
---

# Story 3.3: View the cart with totals

Status: done

## Story

As an anonymous shopper,
I want to see everything in my cart with a running total,
so that I know what I am about to buy and what it costs.

## Acceptance Criteria

1. **Given** items in my cart, **When** I open the cart, **Then** `GET /cart` returns each Line Item (product, unit price, quantity, **line total**) and the cart page displays them — satisfies FR-8.
2. **Given** the cart, **Then** the response/page show **Subtotal = Σ(unitPrice × quantity)** and **Order Total = Subtotal + flatShipping** (config constant, no tax) per AD-6 — satisfies FR-11.
3. **Given** I reload the page in the same session, **Then** the cart contents persist (keyed by `guestId`) — no login prompt.
4. **Given** an empty cart, **Then** the page shows the empty state ("Your cart is empty." + Browse action), not an empty summary panel (EXPERIENCE.md).
5. **Given** the UX, **Then** the cart page matches `mockups/cart-mock.html` + DESIGN.md tokens: card line-item rows (thumbnail, name, unit price, line total) + a sticky order-summary panel (Subtotal / Shipping / Order Total) + a Checkout CTA (Epic 4 — present, routes to `/checkout` which is a later epic; may be a disabled/placeholder link).

## Tasks / Subtasks

- [x] **Task 1 — Cart view with totals (AC: 1, 2)** — API cart view includes each item's `lineTotal` (unit×qty) + `subtotal`, `shipping` (`get_settings().flat_shipping`), `orderTotal`. Compute in `CartsService` (money stays integer cents, AD-6). `GET /cart` returns them (extend the Story 3.1/3.2 cart response).
- [x] **Task 2 — Cart page (AC: 1, 3, 4, 5)** — `frontend/src/pages/CartPage.tsx` at route `/cart`: fetch via `getCart`; line-item rows + sticky summary per the mock/tokens; empty state; Checkout CTA (placeholder link to `/checkout`). Add the header cart icon → `/cart` link.
- [x] **Task 3 — Tests + verify** — service totals (subtotal, shipping, order total; empty cart); API shape includes lineTotal/subtotal/shipping/orderTotal. Frontend build; live: add items then `GET /cart` shows totals; reload persists.

## Dev Notes

- **Totals live in the service** (AD-6, integer cents): `subtotal = Σ item.unit_price*qty`; `shipping = settings.flat_shipping`; `order_total = subtotal + shipping`. Return them on the cart view model (e.g. `CartView` extending items with computed fields, or add fields to `Cart`). Empty cart → subtotal 0; the **page** decides whether to show shipping (shows empty state instead).
- **Persistence (AC-3)** is already provided by the guest token (3.1) — reload re-fetches `GET /cart` with the stored token. No new persistence work; just verify.
- **Checkout CTA** routes to `/checkout` (Epic 4). Since that route doesn't exist yet, render it as a disabled button or a link with a note; do not build checkout.
- **Scope:** display + totals. Quantity change is 3.4; remove is 3.5 (the stepper/remove controls may be rendered but their handlers land in 3.4/3.5 — or build read-only here and wire in 3.4/3.5).
- [Source: epics.md Epic 3 / 3.3; ARCHITECTURE-SPINE AD-6; EXPERIENCE.md (cart IA, empty state, summary panel); mockups/cart-mock.html]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Completion Notes List

- `GET /cart` returns `CartView`: each `CartLine` with `lineTotal`, plus `subtotal`/`shipping`/`orderTotal` (integer cents, AD-6; shipping 0 when empty, no tax). `CartPage.tsx` renders card line-item rows + a sticky order-summary panel per `cart-mock.html`/tokens, with an empty state and a disabled Checkout CTA (Epic 4). Persistence (AC-3) verified: a 2nd `GET /cart` with the same token returns the added items (`test_cart_persists_across_requests_same_token`).
- Built cohesively with 3.2/3.4/3.5. **File List + consolidated Review Findings: see [3-2-add-product-to-cart-from-pdp.md](3-2-add-product-to-cart-from-pdp.md).** Story-specific: `CartPage.tsx` (A), totals in `services/cart.py::to_view`.

### Review Findings

Reviewed together with Stories 3.2-3.5 (Approve-with-patches). AC1/AC2 (lines + totals) and AC4 (empty state) covered by tests; AC3 (reload persists) covered by `test_cart_persists_across_requests_same_token`. Deferred (minor, visual): cart row omits the mock's category chip and the "Subtotal (N items)" count. Full findings: [3-2 story → Review Findings](3-2-add-product-to-cart-from-pdp.md).

### File List

See the consolidated File List in [3-2-add-product-to-cart-from-pdp.md](3-2-add-product-to-cart-from-pdp.md). Story-3.3-specific: `frontend/src/pages/CartPage.tsx` (A), `backend/app/services/cart.py::to_view` (M).
