---
baseline_commit: 9592b6851a102930e3e88875b25fe9acb1d0dd5f
---

# Story 2.1: View product detail (PDP)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an anonymous shopper,
I want to open a product and see its full details,
so that I can decide whether to buy it.

## Acceptance Criteria

1. **Given** a seeded catalog, **When** I request `GET /products/{id}` for an existing product, **Then** the API returns 200 with the product's `productId`, `name`, `description`, `price` (integer cents), `imageUrl`, `category`, and `available` — camelCase per AD-5 — satisfying FR-5.
2. **Given** a product id that does not exist, **When** I request `GET /products/{id}`, **Then** the API returns **404** with the `{error:{code,message}}` envelope (code `not_found`) per AD-5 — never a 500 and never an empty 200.
3. **Given** the storefront, **When** I click a product card on the PLP, **Then** the app navigates to the PDP for that product id (client-side route `/products/:id`) and renders name, description, price, image, and availability using the UX two-column layout (gallery left / action panel right) with a breadcrumb `Home / {category} / {name}`.
4. **Given** an unknown id in the URL, **When** the PDP loads and the API returns 404 `not_found`, **Then** the UI shows a distinct **not-found state** ("This product isn't available." + a link back to browsing) — **not** the generic "Could not load" error state. A genuine network/500 error still shows the generic error state.
5. **Given** AD-1, **Then** all DynamoDB access for the lookup stays inside `ProductsRepository` (a new `get_product` method); the service and HTTP layers hold no boto3.
6. **Given** the router registration, **Then** `GET /products/{id}` is registered **after** `GET /products/categories` and `GET /products` so the literal `categories` route is never shadowed by the `{product_id}` path param — proven by a regression test that `GET /products/categories` still returns the category list (not a "product not found").
7. **Given** the shared UX shell, **Then** both the PLP and the PDP render inside a common header showing the **"BMAD POC Store"** wordmark (POC in green) using the DESIGN.md tokens; the PDP action panel shows an **Add to cart** control that is present but **disabled** (wired in Epic 3), with a note, and availability shown as "In stock"/"Out of stock".

## Tasks / Subtasks

- [x] **Task 1 — Backend: `ProductDetail` model + repository lookup (AC: 1, 5)**
  - [x] Add `ProductDetail` response model to `backend/app/models/catalog.py` (camelCase, incl. `description`) with `from_product(Product)`.
  - [x] `ProductsRepository.get_product` (GetItem on `productId`, `None` on miss) — already present from scaffolding; reused as-is.
  - [x] Repo unit tests against moto (found → `Product`; missing → `None`) — already present (`test_products_repository.py`).
- [x] **Task 2 — Backend: service + 404 (AC: 1, 2, 5)**
  - [x] `CatalogService.get_product` → `ProductDetail`; `None` → `NotFoundError` (404, code `not_found`).
  - [x] Added `NotFoundError(AppError)` in `core/errors.py`; flows through `app_error_handler` into the envelope.
- [x] **Task 3 — Backend: route (AC: 1, 2, 6)**
  - [x] `@router.get("/{product_id}")` registered **last** (after `/categories` and `""`).
  - [x] API tests: detail 200 with `description`; unknown → 404 `not_found` envelope (`test_products_detail.py`).
  - [x] **Route-shadowing regression test:** `GET /products/categories` still returns the `CategoryList`.
- [x] **Task 4 — Frontend: client envelope parsing + `getProduct` (AC: 1, 4)**
  - [x] Refactored `get<T>` to parse `{error:{code,message}}` → throw typed `ApiError{status,code,message}`; network/abort still throws a plain Error. Timeout preserved.
  - [x] Added `ProductDetail` interface + `getProduct(id)` (URL-encoded).
  - [x] PLP error path unchanged (still shows generic copy; it doesn't branch on code yet).
- [x] **Task 5 — Frontend: router + shared shell (AC: 3, 7)**
  - [x] Added `react-router-dom` ^7.18.1.
  - [x] `theme/tokens.ts` (DESIGN.md tokens) + `StoreHeader` (dark bar, **BMAD POC Store** wordmark, POC in green). Header search deferred to the PLP restyle; wordmark links home.
  - [x] Routes wired in `App.tsx`; PLP card `href` → client-side `<Link>`. PLP facet layout untouched.
- [x] **Task 6 — Frontend: PDP page (AC: 3, 4, 7)**
  - [x] `ProductDetailPage.tsx`: two-column gallery/action panel, breadcrumb, About section, disabled Add-to-cart + Epic-3 note.
  - [x] Loading / not-found (ApiError 404) / generic error states, with a latest-wins request-id guard.
- [x] **Task 7 — Verify (AC: all)**
  - [x] Backend: `pytest -q` → 61 passed.
  - [x] Frontend: `tsc -b && vite build` clean.
  - [x] Live (docker compose): `curl /products/{id}` → 200 with description; `/products/does-not-exist` → 404 `not_found`; `/products/categories` → category list; SPA serves `/` and `/products/:id` (200).

## Dev Notes

### What this story is (and is not)
- **Is:** the read-only PDP end-to-end — a keyed `GetItem` (no GSI/cursor/scan), a 404 not-found path, the client-side router, and the **shared UX shell** (header + tokens) that both pages now sit inside.
- **Is not:** the PLP facet **restyle** (top-checkbox → left sidebar). Per the UX adoption plan, that is a separate follow-up story. Keep the PLP body untouched here; it simply gains the shared header and client-side card links.
- **Add-to-cart is Epic 3.** Render the control + quantity per the mock but leave it disabled with a short note; do not add cart state, endpoints, or the guest token here.

### Backend (AD-1, AD-5, AD-6)
- Domain `Product` already carries everything the PDP needs — `product_id, name, description, price, category, image_url, available` (`backend/app/models/product.py`). `ProductSummary` intentionally omits `description`; add a sibling `ProductDetail` that includes it rather than widening the summary (keeps the PLP payload lean).
- **Single image:** the model has one `image_url`. The UX gallery shows one main image; there is **no** multi-image data — render a single image (the mock's thumbnail strip is decorative). Do not invent an images array.
- Lookup is a `GetItem` on the base table PK (`productId`) — the cheapest access path; no `gsi_category`/`gsi_listing` involvement, no cursor. Return `None` on miss; the service maps `None → AppError(not_found, 404)`.
- Reuse the Epic 1 error envelope (`backend/app/core/errors.py`, `app_error_handler`). The `not_found` code should render `{"error":{"code":"not_found","message":"..."}}`. Verify the code exists; add it if missing (mirror how `invalid_cursor`/`invalid_sort` are defined).
- **`_from_item` bare KeyError** (deferred since 1.2/1.3): a partially-written item would raise `KeyError`. Still unreachable (the repo owns all writes); the PDP `GetItem` reuses the same mapper. Not in scope to harden here — noted for awareness.

### Route ordering (retro action item #2 → AC 6)
`backend/app/api/products.py` currently registers `/categories` then `""`. Add `/{product_id}` **last**. FastAPI matches literal paths before path-param routes within a router, but the deferred-work item explicitly asked for an ordering + a regression test now that a `{product_id}` route exists — so add the test asserting `GET /products/categories` returns the category list, guarding against a future reordering regression. [Source: deferred-work.md → 1-5 review; epic-1-retro-2026-07-07.md → Action Item 2]

### Frontend error envelope (retro action item #1 → AC 4)
`get<T>` today throws `new Error("Request failed: {status}")` and drops the envelope. Refactor it to read the JSON body on failure and throw a typed `ApiError { status, code, message }`; on a genuine network/abort failure, keep throwing a plain error. The PDP branches on `err instanceof ApiError && (err.status === 404 || err.code === "not_found")` → not-found state; else generic. The PLP's existing catch shows its generic copy unchanged (it doesn't need to distinguish codes yet, but its stale-cursor handling — deferred — becomes easier later). [Source: deferred-work.md → 1-3/1-4 "frontend discards the error envelope"; epic-1-retro → Action Item 1]

### Frontend routing + shell (AC 3, 7)
- No router exists yet: `App.tsx` renders `ProductListPage` directly and the PLP links via plain `href` (full page nav). Introduce `react-router-dom` v7 (React 19-compatible) with a `BrowserRouter`. Routes: `/` (PLP), `/products/:id` (PDP). Swap the PLP card `<a href>` for `<Link>` so navigation is client-side (same destination).
- **Shared shell:** create `StoreHeader` + a tokens module. Wordmark text is exactly **"BMAD POC Store"** with "POC" in `--green` per DESIGN.md → Brand & Style. Tokens (colors/radius/spacing) come from DESIGN.md frontmatter — introduce them as CSS variables so the later PLP restyle and cart/checkout reuse them. Keep `formatPrice` as-is (`$`); currency symbol/localization is out of scope (the UX mocks used ₴ only illustratively).
- PDP layout + copy: follow `mockups/pdp-mock.html` and EXPERIENCE.md (IA, State Patterns, Voice and Tone, a11y floor — image `alt` = name, breadcrumb links, visible focus).

### Testing standards
- Backend: `pytest` + `moto` (`mock_aws`), FastAPI `TestClient` with `app.dependency_overrides` to inject a fake/seeded service or repo (the Epic 1 pattern). Cover: detail found (all fields incl. description), unknown → 404 envelope, and the `/categories` route-shadow regression.
- Frontend: `tsc -b && vite build` must pass. If a lightweight test runner is wired, add a client test that a 404 body → `ApiError{code:"not_found"}`; otherwise assert behavior via the live check in Task 7.

### Project Structure Notes
- New backend: `ProductDetail` in `models/catalog.py`; `get_product` in `services/catalog.py` and `repositories/products.py`; `/{product_id}` route in `api/products.py`. No new module/table (AD-3 unchanged — Products only).
- New frontend: `pages/ProductDetailPage.tsx`, a `components/StoreHeader.tsx` (new `components/` dir), a tokens module (e.g. `src/theme/tokens.ts` or a global CSS), router in `App.tsx`, `getProduct` + `ApiError` + `ProductDetail` in `api/client.ts`. `react-router-dom` added to deps.
- Conflicts/variances: adding a router changes `App.tsx`'s render tree; the PLP is wrapped but its internal layout is unchanged (restyle deferred). This is the intended shared-shell seam.

### References
- [Source: epics.md → Epic 2 / Story 2.1] — FR-5, AD-1, AD-5, ACs.
- [Source: ARCHITECTURE-SPINE.md] — AD-1 (boto3 only in repositories), AD-5 (OpenAPI/camelCase/error envelope), AD-6 (integer cents).
- [Source: ux-designs/ux-bmad-ecommerce-2026-07-07/DESIGN.md] — tokens, wordmark, PDP components.
- [Source: ux-designs/ux-bmad-ecommerce-2026-07-07/EXPERIENCE.md] — PDP IA, State Patterns (not-found), Voice and Tone, a11y floor, Flow 2.
- [Source: ux-designs/…/mockups/pdp-mock.html] — target layout.
- [Source: _bmad-output/implementation-artifacts/epic-1-retro-2026-07-07.md] — Action Items 1 & 2 (folded into AC 4 & 6).
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — route-shadow test; frontend error-envelope; `_from_item` KeyError.
- Code touched: `backend/app/api/products.py`, `backend/app/services/catalog.py`, `backend/app/repositories/products.py`, `backend/app/models/catalog.py`, `frontend/src/api/client.ts`, `frontend/src/App.tsx`, `frontend/src/pages/ProductListPage.tsx` (link only).

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Debug Log References

- `pytest -q` → 61 passed (58 prior + 3 new PDP tests).
- `npm run build` (`tsc -b && vite build`) → clean, 28 modules.
- Live (docker compose, rebuilt api+frontend): `GET /products/p-0143` → 200 with `description`; `GET /products/does-not-exist` → 404 `{"error":{"code":"not_found",...}}`; `GET /products/categories` → 6 categories (not shadowed); frontend `/` and `/products/p-0143` → 200 (SPA fallback).

### Completion Notes List

- Backend: added `ProductDetail` (adds `description` to the summary), `NotFoundError` (404/`not_found`), `CatalogService.get_product`, and the `/{product_id}` route registered **last** so the literal `/categories` + `""` routes win. `ProductsRepository.get_product` (GetItem) already existed from scaffolding and was reused unchanged.
- **Retro action items landed:** (1) `test_products_detail.py::test_categories_route_not_shadowed_by_detail_route` guards the route ordering; (2) `get<T>` now parses the error envelope into a typed `ApiError`, and the PDP renders a distinct not-found state vs. the generic error state.
- Frontend: introduced the shared shell (`react-router-dom` v7, `StoreHeader` with the **BMAD POC Store** wordmark, `theme/tokens.ts`), the router, and `ProductDetailPage`. **Scope fences held:** PLP facet layout untouched (only `href`→`<Link>`); Add-to-cart shown but disabled (Epic 3); `formatPrice` still `$`.
- Single product image rendered (model has one `imageUrl`); the mock's thumbnail strip was decorative — no invented images array.
- Deferred (unchanged): `_from_item` bare `KeyError` (repo owns all writes, unreachable). Header search intentionally deferred to the PLP-restyle story.

### File List

- `backend/app/models/catalog.py` (M) — add `ProductDetail`.
- `backend/app/core/errors.py` (M) — add `NotFoundError`.
- `backend/app/services/catalog.py` (M) — add `get_product`.
- `backend/app/api/products.py` (M) — add `GET /{product_id}` route (registered last).
- `backend/tests/test_products_detail.py` (A) — PDP endpoint + route-shadow regression tests.
- `frontend/src/api/client.ts` (M) — `ApiError` + envelope parsing; `ProductDetail` + `getProduct`.
- `frontend/src/theme/tokens.ts` (A) — DESIGN.md design tokens.
- `frontend/src/components/StoreHeader.tsx` (A) — shared shell header.
- `frontend/src/pages/ProductDetailPage.tsx` (A) — PDP page.
- `frontend/src/App.tsx` (M) — BrowserRouter + shell + routes.
- `frontend/src/pages/ProductListPage.tsx` (M) — card `href` → client-side `<Link>`.
- `frontend/package.json` + `package-lock.json` (M) — `react-router-dom` ^7.18.1.

### Change Log

- 2026-07-07: Implemented story 2.1 (PDP) — backend `GET /products/{id}` with 404 not-found envelope; frontend router + shared shell + PDP page; folded in Epic 1 retro action items (route-shadow test, error-envelope parsing). Status → review.
- 2026-07-07: Code review (3-lens adversarial) — Approve-with-patches. 3 patches applied (product_id length cap, abort-relabel fix, 404 message assertion), 7 deferred, 2 dismissed. Tests 62 passed. Status → done.

## Senior Developer Review (AI)

**Date:** 2026-07-07 · **Outcome:** Approve with patches · **Reviewers:** Blind Hunter · Edge Case Hunter · Acceptance Auditor (parallel). All 7 ACs met; ADs (AD-1/AD-5/AD-6) hold; both Epic 1 retro action items satisfied. No hard AC violations.

### Action Items — patched (3)

- [x] **[Med] `product_id` path param unbounded** (`backend/app/api/products.py`) — an oversized id reached `GetItem` → `ValidationException` → 500. Added `Path(min_length=1, max_length=256)` so it's a clean **422** before Dynamo (mirrors the `cursor` cap). This also neutralizes the "`get_product` lacks a `ClientError` guard" finding: the only client-fault error is stopped at the boundary; other `ClientError`s already envelope via `unhandled_error_handler`. New test `test_oversized_product_id_422_not_500`.
- [x] **[Med] Abort during error-body read mislabeled as `ApiError`** (`frontend/src/api/client.ts`) — if the timeout fired while reading a non-2xx body, the inner `catch` swallowed the `AbortError` and threw an `ApiError`, breaking the "network/abort → plain Error" contract. Now rethrows when `controller.signal.aborted`.
- [x] **[Low] 404 test asserted `code` but not `message`** (`backend/tests/test_products_detail.py`) — added a non-empty `message` assertion for the full AD-5 envelope shape.

### Deferred (7) — see deferred-work.md

Breadcrumb category→filtered-PLP link (needs URL-driven PLP filters — PLP-restyle story); PLP `invalid_cursor`-reset (the enabling `ApiError` now exists); image `onError` fallback (PLP+PDP); empty-`description` section hide; PDP `AbortController` effect cleanup; frontend test runner (Vitest); `_from_item` bare `KeyError` (already deferred since 1.2).

### Dismissed (2)

- 2xx with malformed/empty JSON body → throws a generic error → PDP already routes it to the generic error state (correct behavior, not an `ApiError`).
- `product_id` containing `/` → 404: POC ids contain no slashes; documented assumption, not a defect.
