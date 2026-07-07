---
baseline_commit: e412f85cccd5de809117defd8ac86b7a5e4ab6c0
---

# Story 3.5: Remove a line item

Status: done

## Story

As an anonymous shopper,
I want to remove an item from my cart,
so that I don't buy something I changed my mind about.

## Acceptance Criteria

1. **Given** a Line Item in my cart, **When** I remove it, **Then** `DELETE /cart/items/{productId}` removes it and it no longer appears — satisfies FR-10.
2. **Given** the removal, **Then** the Subtotal and Order Total recompute accordingly.
3. **Given** a `productId` not in the cart, **Then** `DELETE` returns 404 `not_found` (envelope) — do not silently succeed on a missing line.
4. **Given** the cart page, **Then** each line-item row has a **Remove** control that deletes the item and re-renders the cart + header count; removing the last item shows the empty state.

## Tasks / Subtasks

- [x] **Task 1 — Service remove (AC: 1, 2, 3)** — `CartsService.remove_item(guest_id, product_id)`: load the cart; if the line is absent → `NotFoundError`; drop the line; `put_cart`; return the recomputed cart view. Reuse the removal path from `update_item(…, 0)`.
- [x] **Task 2 — API route (AC: 1, 3)** — `DELETE /cart/items/{product_id}` in `api/cart.py`: `X-Guest-Token` resolve/echo; bounded `product_id` path param; return the updated cart view (204-vs-200 → return the cart view 200 for the SPA to re-render).
- [x] **Task 3 — Frontend (AC: 4)** — `client.removeCartItem(productId)` (`DELETE`); the cart-page row Remove button calls it and refreshes cart + header count; last item removed → empty state.
- [x] **Task 4 — Tests + verify** — service remove (present, missing→404); API DELETE. Frontend build; live DELETE.

## Dev Notes

- **Shared removal path** — `remove_item` and `update_item(quantity=0)` (3.4) drop a line the same way; keep one private helper so behavior can't diverge.
- **404 on missing** (AC-3) — unlike update-to-0 which no-ops a set, an explicit DELETE of a non-existent line is a client error (404), not a silent success.
- **Recompute** on read (3.3 view), so remove just persists and returns the view.
- **Scope:** closes Epic 3. After 3.5, run the Epic 3 retrospective (optional) before Epic 4 (Checkout).
- [Source: epics.md Epic 3 / 3.5; ARCHITECTURE-SPINE AD-6; EXPERIENCE.md (remove control; empty state)]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Completion Notes List

- `DELETE /cart/items/{productId}` removes the line (shared `_drop_line` with 3.4's qty-0 path) and returns the recomputed `CartView`; a missing line → 404 (explicit delete of a non-existent line is a client error, not a silent success). Review patch: `remove_item` uses read-only `get_cart` (404 if cart/line absent). The cart-page row Remove button calls `removeCartItem` then `applyCart`; removing the last item shows the empty state.
- Built cohesively with 3.2/3.3/3.4. **File List + consolidated Review Findings: see [3-2-add-product-to-cart-from-pdp.md](3-2-add-product-to-cart-from-pdp.md).**

### Review Findings

Reviewed together with 3.2-3.5. AC1/AC3 covered (`test_remove_item`, `test_remove_missing_line_404`). Full findings: [3-2 story → Review Findings](3-2-add-product-to-cart-from-pdp.md).

### File List

See the consolidated File List in [3-2-add-product-to-cart-from-pdp.md](3-2-add-product-to-cart-from-pdp.md). Story-3.5-specific: `DELETE /cart/items/{id}` in `api/cart.py`, `CartsService.remove_item`, the cart-page Remove control.
