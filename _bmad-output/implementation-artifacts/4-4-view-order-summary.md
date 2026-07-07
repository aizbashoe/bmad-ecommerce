---
baseline_commit: 2742fb054d8e24a2b3d2e8dd7cbe81ef0068dfea
---

# Story 4.4: View the order summary

Status: done

## Story

As an anonymous shopper,
I want to see a confirmation of what I ordered,
so that I know the purchase went through and what it included.

## Acceptance Criteria

1. **Given** I have just placed an order, **When** the Order Summary displays, **Then** it shows the **reference number, line items, Subtotal, Order Total, and shipping details**, reflecting the persisted Order exactly — satisfies FR-15.
2. **Given** the summary, **Then** it is shown **immediately after checkout** (route `/order/{orderId}`, fetched via `GET /orders/{id}`); there is **no order-lookup/history page** (account-free) — only this confirmation-by-id.
3. **Given** the order was placed, **Then** the header cart count reads 0 (the cart was cleared at placement).
4. **Given** an unknown/inaccessible order id (or a token that doesn't own it), **When** `/order/{id}` loads, **Then** a not-found state shows (mirrors the PDP 404 pattern), not a crash.

## Tasks / Subtasks

- [x] **Task 1 — OrderSummaryPage (AC: 1, 2, 4)** — `frontend/src/pages/OrderSummaryPage.tsx` at `/order/:orderId`: fetch `getOrder(orderId)`; render a success confirmation (✓ + "Thank you — your order is placed" + `Reference {reference}`), the line items (image/name/qty/lineTotal), Subtotal / Shipping / Order total, and the shipping address — matching `order-summary-mock.html` + tokens. Loading / not-found (ApiError 404) states. "Continue shopping" link → `/`.
- [x] **Task 2 — Route (AC: 2)** — add `/order/:orderId` route in `App.tsx`. (The navigation from Place-order in 4.3 targets this route.)
- [x] **Task 3 — Verify (AC: all)** — `tsc -b && vite build` clean; live: place an order → lands on `/order/{id}` showing reference + items + totals + shipping; header count 0; a bogus `/order/xxx` → not-found state.

## Dev Notes

- **Consumes 4.3's `GET /orders/{orderId}`.** The confirmation is refresh-safe because it fetches by id (scoped to the guest token). This is not a history/browse page (FR-15 — account-free); it's the single post-checkout confirmation.
- **Reuse:** `getOrder` + `Order`/`ShippingDetails` types (added in 4.3), `formatPrice`, tokens, the shared `StoreHeader`. Not-found follows the PDP pattern (`ApiError` status 404 / code `not_found` → not-found state).
- **Cart already cleared** at placement (4.3, atomic) — this page just reflects it; the header count (CartContext) was refreshed to 0 on navigation from checkout.
- **Scope:** the confirmation page only. Order creation/clear is 4.3.
- [Source: epics.md Epic 4 / 4.4; FR-15; EXPERIENCE.md (Order Summary transient, no lookup); mockups/order-summary-mock.html]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Completion Notes List

- `OrderSummaryPage` at `/order/:orderId` fetches `getOrder` and renders the confirmation (✓ + reference + `createdAt`), line items, Subtotal/Shipping/Order total, and shipping address — from the persisted immutable Order (FR-15). Loading / not-found (ApiError 404) / error states + `items`-shape guard. Confirmation-by-id only (no history). Header count is 0 (cart cleared at placement; refreshed on the checkout→summary navigation). Built cohesively with 4.1-4.3.
- **File List + consolidated Review Findings: see [4-3-place-order.md](4-3-place-order.md).** Story-4.4-specific: `OrderSummaryPage.tsx` (A) + `/order/:orderId` route.

### Review Findings

Reviewed with Epic 4 (Approve-with-patches). AC1/AC2/AC4 met (reference/items/totals/shipping from the persisted order; by-id, no history; unknown/unowned id → not-found). Review patches touching this page: `items`-shape guard + show `createdAt`. Full findings: [4-3 story → Review Findings](4-3-place-order.md).

### File List

See the consolidated File List in [4-3-place-order.md](4-3-place-order.md). Story-4.4-specific: `frontend/src/pages/OrderSummaryPage.tsx` (A), `/order/:orderId` route in `App.tsx`.
