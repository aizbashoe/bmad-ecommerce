---
baseline_commit: e412f85cccd5de809117defd8ac86b7a5e4ab6c0
---

# Story 3.4: Update a line item quantity

Status: done

## Story

As an anonymous shopper,
I want to change how many of an item I'm buying,
so that my cart reflects what I actually want.

## Acceptance Criteria

1. **Given** a Line Item in my cart, **When** I change its quantity to a positive number, **Then** `PATCH /cart/items/{productId}` updates it and the line total and Subtotal/Order Total recompute — satisfies FR-9.
2. **Given** I set the quantity to **0**, **Then** the Line Item is **removed** from the cart (same effect as delete).
3. **Given** a `productId` not in the cart, **Then** the API returns 404 `not_found` (envelope); a negative quantity → 4xx `validation_error` (FastAPI `Field(ge=0)` yields **422**, the same shape as the other request-validation errors).
4. **Given** the cart page, **Then** the line-item quantity **stepper** updates the item and re-renders the recomputed line total + summary (optimistic or refetch); stepping to 0 removes the row.

## Tasks / Subtasks

- [x] **Task 1 — Service update (AC: 1, 2, 3)** — `CartsService.update_item(guest_id, product_id, quantity)`: `quantity < 0` → `validation_error 400`; load the cart; if the line is absent → `NotFoundError`; if `quantity == 0` remove the line, else set it; `put_cart`; return the recomputed cart view.
- [x] **Task 2 — API route (AC: 1, 2, 3)** — `PATCH /cart/items/{product_id}` in `api/cart.py`: body `{quantity}` (`int Field(ge=0)`); `X-Guest-Token` resolve/echo; return the updated cart view. Register with a bounded `product_id` path param (mirror the 2.1 length cap).
- [x] **Task 3 — Frontend (AC: 4)** — `client.updateCartItem(productId, quantity)` (`PATCH`); the cart-page stepper calls it and refreshes the cart + header count; qty 0 removes the row.
- [x] **Task 4 — Tests + verify** — service update (increase, decrease, 0→remove, missing→404, negative→400); API PATCH. Frontend build; live PATCH.

## Dev Notes

- **0 removes** — AC-2 makes update-to-0 identical to delete (3.5); implement removal in `update_item` and have 3.5's delete reuse the same removal path.
- **Recompute** — the cart view (3.3) recomputes subtotal/shipping/order total on read, so update just persists the new quantity and returns the view.
- **Path param** — bound `product_id` (`Path(min_length=1, max_length=256)`) like `GET /products/{id}` (2.1) so an oversized id is a clean 422, not a 500.
- **Scope:** quantity change (+ 0-removes). Explicit remove control is 3.5.
- [Source: epics.md Epic 3 / 3.4; ARCHITECTURE-SPINE AD-6; EXPERIENCE.md (stepper recomputes; 0 removes)]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Completion Notes List

- `PATCH /cart/items/{productId}` updates the line and returns the recomputed `CartView`; `quantity == 0` removes the line via the shared `_drop_line` helper (reused by 3.5); a missing line → 404; negative → 422 (`Field(ge=0)`). The cart-page stepper decrements to 0 to remove. Review patch: `update_item` uses read-only `get_cart` (404 if cart/line absent — no orphan write). Bounded `product_id` path (422 on oversize, as 2.1).
- Built cohesively with 3.2/3.3/3.5. **File List + consolidated Review Findings: see [3-2-add-product-to-cart-from-pdp.md](3-2-add-product-to-cart-from-pdp.md).**

### Review Findings

Reviewed together with 3.2-3.5. AC1/AC2/AC3 covered (`test_update_item_recomputes`, `test_update_quantity_zero_removes_line`, `test_update_missing_line_404`, `test_update_negative_quantity_422`). AC3 wording corrected to 422 (`Field(ge=0)` validation shape). Full findings: [3-2 story → Review Findings](3-2-add-product-to-cart-from-pdp.md).

### File List

See the consolidated File List in [3-2-add-product-to-cart-from-pdp.md](3-2-add-product-to-cart-from-pdp.md). Story-3.4-specific: `PATCH /cart/items/{id}` in `api/cart.py`, `CartsService.update_item`, the cart-page stepper handlers.
