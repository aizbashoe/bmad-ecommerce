# Story 2.1: View product detail (PDP)

Status: ready-for-dev

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

- [ ] **Task 1 — Backend: `ProductDetail` model + repository lookup (AC: 1, 5)**
  - [ ] Add `ProductDetail` response model to `backend/app/models/catalog.py` (camelCase: `productId`, `name`, `description`, `price`, `imageUrl`, `category`, `available`) with a `from_product(Product)` classmethod. (Distinct from `ProductSummary`, which omits `description`.)
  - [ ] Add `get_product(self, product_id: str) -> Product | None` to `ProductsRepository` using a DynamoDB **GetItem** on `PK = productId` (no GSI, no scan). Map the item via the existing `_from_item`; return `None` when the item is absent. Guard `ClientError` consistently with the rest of the repo.
  - [ ] Unit-test the repo against moto: found → `Product`; missing id → `None`.
- [ ] **Task 2 — Backend: service + 404 (AC: 1, 2, 5)**
  - [ ] Add `get_product(self, product_id: str) -> ProductDetail` to `CatalogService`: call the repo; if `None`, raise `AppError` with code `not_found` and HTTP 404; else return `ProductDetail.from_product(product)`.
  - [ ] Confirm `not_found`/404 flows through the existing `app_error_handler` into the `{error:{code,message}}` envelope (reuse the Epic 1 error machinery; add the code if not already present).
- [ ] **Task 3 — Backend: route (AC: 1, 2, 6)**
  - [ ] Add `@router.get("/{product_id}", response_model=ProductDetail)` to `backend/app/api/products.py`, registered **after** `/categories` and the `""` listing route. `product_id` via path param; delegate to `CatalogService.get_product`.
  - [ ] Add an API test: `GET /products/{existing}` → 200 with all fields incl. `description`; `GET /products/{unknown}` → 404 `not_found` envelope.
  - [ ] **Route-shadowing regression test (retro action item):** `GET /products/categories` still returns the `CategoryList` (asserts the literal route wins over `/{product_id}`).
- [ ] **Task 4 — Frontend: client envelope parsing + `getProduct` (AC: 1, 4)**
  - [ ] Refactor `get<T>` in `frontend/src/api/client.ts` to parse the `{error:{code,message}}` envelope on non-2xx: throw a typed `ApiError { status, code, message }` instead of the generic `Error("Request failed: …")`. Preserve the abort-timeout behavior; a network/abort failure throws a non-`ApiError` (generic) error.
  - [ ] Add `ProductDetail` interface (ProductSummary + `description`) and `getProduct(id: string): Promise<ProductDetail>` (URL-encode the id).
  - [ ] Keep existing callers working (listProducts/listCategories still resolve on 2xx; their error path now yields `ApiError` — verify the PLP still shows its generic error copy).
- [ ] **Task 5 — Frontend: router + shared shell (AC: 3, 7)**
  - [ ] Add `react-router-dom` (v7, React 19 compatible) to `frontend/package.json`.
  - [ ] Create a design-tokens module (CSS variables from DESIGN.md frontmatter: colors, radius, spacing) and a `StoreHeader` component (dark bar, **BMAD POC Store** wordmark with POC in `--green`, search field, cart icon placeholder). Both PLP and PDP render inside this shell.
  - [ ] Wire routes in `App.tsx`: `/` → `ProductListPage`, `/products/:id` → `ProductDetailPage`. Replace the PLP card `href` full-navigation with a client-side `Link` (behavior identical: opens the PDP). **Do NOT restyle the PLP facet layout — that is a separate story.**
- [ ] **Task 6 — Frontend: PDP page (AC: 3, 4, 7)**
  - [ ] Create `frontend/src/pages/ProductDetailPage.tsx`: read `:id`, call `getProduct`, render the two-column layout (image gallery left; action panel right with breadcrumb `Home / {category} / {name}`, title, category, availability, price, disabled Add-to-cart + Epic-3 note) and an "About this product" section (the `description`). Match `mockups/pdp-mock.html` and the EXPERIENCE.md PDP spec.
  - [ ] Loading state while fetching; **not-found state** when the thrown error is an `ApiError` with status 404 / code `not_found`; generic error state otherwise.
- [ ] **Task 7 — Verify (AC: all)**
  - [ ] Backend: `pytest -q` all green (existing + new).
  - [ ] Frontend: `tsc -b && vite build` clean.
  - [ ] Live (docker compose): open a PLP card → PDP renders; hit `/products/does-not-exist` → not-found state; `curl /products/{id}` → 200; `curl /products/nope` → 404 envelope; `curl /products/categories` → still the category list.

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

### Completion Notes List

### File List
