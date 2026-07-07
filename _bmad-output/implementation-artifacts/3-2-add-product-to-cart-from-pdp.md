---
baseline_commit: e412f85cccd5de809117defd8ac86b7a5e4ab6c0
---

# Story 3.2: Add a product to the cart from the PDP

Status: done

## Story

As an anonymous shopper,
I want to add a product to my cart from its detail page,
so that I can collect items I intend to buy.

## Acceptance Criteria

1. **Given** a PDP with a valid guest token, **When** I add the product with quantity ≥ 1, **Then** `POST /cart/items` creates or updates the corresponding Line Item under my `guestId` — satisfies FR-6.
2. **Given** the line item, **Then** its **unit price is captured in integer minor units (cents)** (AD-6), snapshotted from the product at add time (plus name + imageUrl for display), so the cart can render without re-fetching each product.
3. **Given** an add for a product already in the cart, **When** I add again, **Then** the existing line item's quantity **increments** (no duplicate line).
4. **Given** an unknown `productId` or `quantity < 1`, **Then** the API returns a 4xx with the `{error:{code,message}}` envelope (`not_found` / `validation_error`) — never a 500.
5. **Given** the PDP, **Then** the **Add to cart** control is now **enabled** (with the quantity stepper), and on success the header **cart count updates** as feedback (FR-6).
6. **Given** AD-1/AD-3, **Then** cart mutations stay in `CartsService` + `CartsRepository`; the service may read `ProductsRepository` to snapshot the product. No boto3 above repositories.

## Tasks / Subtasks

- [x] **Task 1 — Line-item model (AC: 2)** — `CartItem(CamelModel)` in `models/cart.py`: `product_id`, `name`, `unit_price` (cents), `image_url`, `quantity` (int ≥ 1). `Cart.items: list[CartItem]`.
- [x] **Task 2 — Repository items mapping (AC: 1, 3, 6)** — `CartsRepository._to_item`/`_from_item` map `items` as a DynamoDB List of Maps (round-trip). Add `put_cart(cart)` (full write). Keep `get_cart`/`put_empty_cart`. (Retires the 3.1 `_from_item`-discards-items deferral.)
- [x] **Task 3 — Service add (AC: 1, 2, 3, 4, 6)** — `CartsService.add_item(guest_id, product_id, quantity)`: `quantity ≥ 1` else `AppError validation_error 400`; look up the product via `ProductsRepository.get_product` → `NotFoundError` if absent; get-or-create cart; if the line exists increment quantity, else append a snapshot `CartItem`; `put_cart`; return the cart. Inject the products repo for testability.
- [x] **Task 4 — API route (AC: 1, 4)** — `POST /cart/items` in `api/cart.py`: body `{productId, quantity}` (Pydantic request model, `quantity: int Field(ge=1)`); `X-Guest-Token` header (resolve session); echo the token; return the updated `Cart`. 
- [x] **Task 5 — Frontend (AC: 5)** — `client.addToCart(productId, quantity)` (`POST /cart/items`, token round-trip); a `CartContext` (count + `refresh()`), provided in `App`; `StoreHeader` shows the live count; the PDP **enables** Add-to-cart + stepper, calls `addToCart` then `refresh()`, with success feedback.
- [x] **Task 6 — Tests + verify** — repo items round-trip; service add (new, increment, unknown product 404, qty 0 → 400); API `POST /cart/items`. Backend `pytest` green; frontend build; live add via `curl` + PDP.

## Dev Notes

- **Line item is a snapshot** — capture `unitPrice`/`name`/`imageUrl` from the product at add time (AD-6); the cart renders from the snapshot (no per-item product re-fetch). Staleness is acceptable at POC scale.
- **Cross-repo read** — `CartsService` depends on `ProductsRepository` for the snapshot (AD-1 allows service→repository; still no boto3 in the service). Inject both repos in the constructor for tests.
- **Concurrency** — retire the 3.1 deferral partially: `put_cart` is a full read-modify-write. A conditional/optimistic write is still deferred (POC single-user); note it.
- **Header cart count** — needs shared state across PDP↔header. Add a `CartContext` (`{ count, refresh }`) in `frontend/src/state/`; `refresh()` calls `getCart` and derives count = Σ quantities. Provide it in `App` (inside `BrowserRouter`).
- **Scope:** add + increment only. Viewing the cart page + totals is 3.3; qty change is 3.4; remove is 3.5.
- [Source: epics.md Epic 3 / 3.2; ARCHITECTURE-SPINE AD-2/3/6; EXPERIENCE.md (Add-to-cart feedback, cart count Epic 3+)]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Debug Log References

- Stories 3.2-3.5 built cohesively (one cart aggregate) then reviewed together. `pytest -q` → 85 passed; frontend `tsc -b && vite build` clean; live (docker): add (subtotal/shipping/orderTotal correct), increment, PATCH, PATCH-0-removes, DELETE, delete-missing 404, add-unknown 404, add-qty-0 422, oversized-qty 422, out-of-stock 409.

### Completion Notes List

- Line items are a snapshot (unitPrice/name/imageUrl at add time, AD-6). Add increments an existing line. `CartsService` reads `ProductsRepository` for the snapshot (AD-1 service→repo; no boto3 above repos). Header count via a `CartContext`; PDP Add-to-cart enabled + `applyCart(response)` (no extra round-trip).
- **Review patches:** server-side out-of-stock enforcement (409 `product_unavailable`); quantity cap `le=999` (avoids a 500 from DynamoDB's number limit); update/remove use read-only `get_cart` (no orphan empty-cart write on a 404 path); header count from the mutation response instead of a second GET; unmount-safe "added" timer; aria pluralization.

### File List

Shared across Stories 3.2-3.5 (implemented together):
- `backend/app/models/cart.py` (M) — `CartItem`, `Cart`, `CartLine`, `CartView`, `AddItemRequest`, `UpdateItemRequest`.
- `backend/app/repositories/carts.py` (M) — items List-of-Maps `_to_item`/`_from_item`, `put_cart`.
- `backend/app/services/cart.py` (M) — `add_item`, `update_item`, `remove_item`, `_drop_line`, `to_view`, `resolve_guest_id`.
- `backend/app/api/cart.py` (M) — `POST /cart/items`, `GET /cart` (view), `PATCH`/`DELETE /cart/items/{id}`.
- `backend/tests/test_cart_api.py` (M), `backend/tests/test_carts_repository.py` (M) — cart tests.
- `frontend/src/api/client.ts` (M) — `Cart`/`CartLine` types, `cartFetch`, `getCart`/`addToCart`/`updateCartItem`/`removeCartItem`.
- `frontend/src/state/cart.tsx` (A) — `CartProvider`/`useCart` (count, refresh, applyCart).
- `frontend/src/App.tsx` (M) — `CartProvider` + `/cart` route.
- `frontend/src/components/StoreHeader.tsx` (M) — live cart count + link to `/cart`.
- `frontend/src/pages/ProductDetailPage.tsx` (M) — `AddToCartPanel` (3.2).
- `frontend/src/pages/CartPage.tsx` (A) — cart page (3.3-3.5).

### Review Findings

*Code review 2026-07-07 (Blind Hunter + Edge Case Hunter + Acceptance Auditor), covering Stories 3.2-3.5 together. Approve-with-patches. All ACs across 3.2-3.5 satisfied; AD-1/3/5/6 hold. Severity at triage; reviewer in parens.*

- [x] [Review][Patch] **MED — `add_item` never checked `product.available`** [backend/app/services/cart.py] — out-of-stock products were addable via the API (the disabled PDP button was the only gate). Fix: enforce server-side → 409 `product_unavailable`; test added. (blind + edge)
- [x] [Review][Patch] **MED — no upper bound on quantity → 500** [backend/app/models/cart.py] — a huge quantity overflowed DynamoDB's 38-digit Number on write → uncaught 500. Fix: `Field(le=999)` on add/update → clean 422; test added. (blind + edge)
- [x] [Review][Patch] LOW — PATCH/DELETE for a tokenless/new guest wrote an orphan empty cart then 404'd [backend/app/services/cart.py] — `update_item`/`remove_item` used get-or-create. Fix: read-only `get_cart` (404 if cart or line absent), no stray write. (blind + edge)
- [x] [Review][Patch] LOW — two network round-trips per mutation [frontend/src/state/cart.tsx, ProductDetailPage.tsx, CartPage.tsx] — `refresh()` did a second GET after each mutation. Fix: `applyCart(response)` updates the header count from the cart already returned. (blind)
- [x] [Review][Patch] LOW — cart mutation error didn't re-sync the view [frontend/src/pages/CartPage.tsx] — a failed mutation left a stale row. Fix: on error, `load()` re-syncs; `mutate` now uses the `requestId` guard too. (blind + edge)
- [x] [Review][Patch] LOW — "added" `setTimeout` not cleared on unmount [frontend/src/pages/ProductDetailPage.tsx] — cleared via a ref + effect cleanup. (blind + edge)
- [x] [Review][Patch] LOW — header aria-label said "1 items" [frontend/src/components/StoreHeader.tsx] — pluralized. (blind)
- [x] [Review][Patch] LOW — 3.4 AC wording said 400 but `Field(ge=0)` yields 422 [3-4 story] — reworded the AC to 422 `validation_error` (consistent with the 3.2 pattern; the service's `<0` branch is a defensive backstop). (auditor)
- [x] [Review][Defer] LOW — first-contact token race [frontend/src/state/cart.tsx] — concurrent tokenless requests can mint two guestIds; a just-added item can be orphaned. POC single-user; proper fix = gate mutations on a resolved session. → deferred-work.
- [x] [Review][Defer] LOW — read-modify-write `put_cart` has no conditional/optimistic write [backend/app/repositories/carts.py] — concurrent mutations last-write-wins. POC single-user. → deferred-work (carried from 3.1).
- [x] [Review][Defer] LOW — mock deviations: cart row omits category; "Subtotal (N items)" count; header hides count at 0 [frontend] — minor visual; spines-win-on-conflict, honest data. → deferred-work.

**Formal `/bmad-code-review` verification pass (2026-07-07, post-patch):** confirmed all 6 patches above hold + AD-1/3/5/6 + integer-cents math. Two residuals found and fixed:

- [x] [Review][Patch] **HIGH — failed cart mutation wedged the whole cart UI** [frontend/src/pages/CartPage.tsx] — REGRESSION from the "resync via `load()`" patch: `load()` bumps `requestId` synchronously, so `mutate`'s guarded `finally` skipped `setBusy(false)` → every stepper/remove stayed `disabled` until reload. Fix: set `setBusy(false)` explicitly in both terminal branches (before `load()`), drop the `finally`. (verify: correctness + edge)
- [x] [Review][Patch] MED — `add_item` increment could accumulate past the 999 cap [backend/app/services/cart.py] — the request `le=999` bounds the delta, not the sum. Fix: reject with 400 `quantity_limit` when `item.quantity + quantity > 999`; test added. Also disabled the "+" stepper at 999 on the cart page + PDP (avoids an opaque 422). (verify: correctness + edge)

*Dismissed (2): 2xx cart response missing `X-Guest-Token` → `expose_headers` is set + verified live (env misconfig, not a code path); `update_item` not re-validating product availability → snapshots are intentionally frozen (quantity bumps of a since-removed product are allowed at POC scale).*
