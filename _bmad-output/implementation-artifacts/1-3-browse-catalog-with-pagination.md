---
baseline_commit: d85627e
---

# Story 1.3: Browse the catalog with pagination

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an anonymous shopper,
I want to see products in a paginated list,
so that I can explore the catalog without loading everything at once.

## Acceptance Criteria

1. **Paginated listing endpoint (FR-1, AD-4).** `GET /products` returns a bounded page of Products queried via `gsi_listing` (all items share `listingPk="PRODUCT"`, sorted by `price` ascending). Default page size ~24; `limit` is a query param (validated, capped, e.g. 1–100).
2. **Opaque cursor (AD-4).** The response includes a `nextCursor` — an **opaque base64 string** encoding DynamoDB's `LastEvaluatedKey` — or `null` on the last page. A raw `LastEvaluatedKey` is never exposed. Passing `?cursor=<nextCursor>` returns the following page; paging to the end eventually yields `nextCursor: null` with no overlap or gaps.
3. **Result shape (AD-5).** Each item exposes at least `productId`, `name`, `price` (integer cents), `imageUrl`, `category`, `available`. JSON is camelCase. `productId` is what the PLP links to for the PDP route (`/products/{productId}`).
4. **Layering (AD-1).** Flow is `api → services → repository`. The new `GET /products` router calls a `CatalogService`, which calls `ProductsRepository`. boto3 / cursor encoding stays inside the repository; no DynamoDB types surface above it.
5. **Contract in OpenAPI (AD-5).** The endpoint and its response model appear in `/openapi.json` and `/docs` with a typed response schema.
6. **PLP renders the grid.** The frontend PLP page fetches page 1 via the typed API client and renders a product grid (name, price, image, link to the PDP route). A "load more" / next-page control fetches the next page using `nextCursor`; the empty/last-page case is handled (no crash, control hidden/disabled).
7. **Tested.** Repository pagination is unit-tested under `moto` (seed > 1 page; assert price-ascending order, exact page sizes, cursor round-trip covers all items with no dup/gap, `null` at end). The API endpoint is tested with FastAPI `TestClient` (200 shape, `limit` validation → 422 envelope, cursor passthrough). A frontend smoke test is optional.

## Tasks / Subtasks

- [x] **Task 1 — Response models** (AC: #3, #5)
  - [x] Add `ProductSummary` (CamelModel: productId, name, price:int, imageUrl, category, available) and `ProductPage` (CamelModel: `items: list[ProductSummary]`, `nextCursor: str | None`) in `app/models/` (e.g. `app/models/catalog.py`). Reuse/derive from `Product` where sensible.
- [x] **Task 2 — Repository: paginated listing query** (AC: #1, #2, #4)
  - [x] Add `list_products(limit: int, cursor: str | None) -> tuple[list[Product], str | None]` to `ProductsRepository`.
  - [x] Query `gsi_listing` with `KeyConditionExpression` `listingPk = "PRODUCT"`, `ScanIndexForward=True` (price ascending), `Limit=limit`; pass `ExclusiveStartKey` decoded from `cursor` when present.
  - [x] Encode `LastEvaluatedKey` → opaque cursor and decode back **inside the repository** (base64 of compact JSON). Return `(products, next_cursor_or_None)`. Malformed cursor → raise a domain error mapped to a 400 envelope (see Task 4).
- [x] **Task 3 — CatalogService** (AC: #4)
  - [x] Create `app/services/catalog.py` with `CatalogService` holding a `ProductsRepository`; `list_products(limit, cursor)` returns `ProductPage` (maps `Product` → `ProductSummary`). No boto3 here.
- [x] **Task 4 — API endpoint** (AC: #1, #3, #5)
  - [x] Create `app/api/products.py`: `GET /products` with query params `limit: int = 24` (`Query(ge=1, le=100)`) and `cursor: str | None = None`, returning `ProductPage`. Include the router in `app/api/__init__.py`'s `api_router`.
  - [x] Add a `BadRequestError`/`ValidationError`-style `AppError` (code `invalid_cursor`, 400) for a malformed cursor, so it returns the `{error:{code,message}}` envelope (AD-5). Instantiate `CatalogService` per request (stateless, AD-9) — a simple module/dependency factory is fine.
- [x] **Task 5 — Backend tests** (AC: #7)
  - [x] `backend/tests/test_products_listing.py` (moto): seed ~30 products, page with `limit=10`, assert 3 pages of 10/10/10, `nextCursor` non-null then null, prices non-decreasing across the full sequence, and the union of pages == all productIds with no duplicates. Assert a bad cursor raises the domain error.
  - [x] Extend API tests (`test_products_api.py` or existing): `GET /products` → 200 with `items` + `nextCursor`; `?limit=0` and `?limit=101` → 422 with error envelope; `?cursor=not-base64` → 400 `invalid_cursor`. Mock the service/repo or run against moto.
- [x] **Task 6 — Frontend PLP** (AC: #6)
  - [x] `frontend/src/api/client.ts`: add `listProducts(params?: { limit?: number; cursor?: string }): Promise<ProductPage>` and the `ProductSummary`/`ProductPage` TS types (camelCase, matching the API).
  - [x] `frontend/src/pages/ProductListPage.tsx`: fetch page 1 on mount, render a responsive grid of cards (image, name, formatted price, link to `/products/:productId`), and a "Load more" button that appends the next page via `nextCursor` (hidden when `nextCursor` is null). Handle loading + error states.
  - [x] Wire `App.tsx` to render `ProductListPage` as the storefront home (keep it simple — a router is optional at this stage; if added, use it consistently).
  - [x] Format price for display from integer cents (e.g. `$${(price/100).toFixed(2)}`) — the only place cents becomes a display string (AD-6).
- [x] **Task 7 — Verify locally** (AC: #1, #2, #6)
  - [x] Stack up + seeded (`docker compose up -d`; seed already loaded). `curl 'http://localhost:8000/products?limit=5'` → 5 items + `nextCursor`; follow the cursor to page 2; confirm price-ascending and a final `nextCursor: null`.
  - [x] Open `http://localhost:5173` → grid of products renders; "Load more" pages through.

### Review Findings

*Code review 2026-07-06 (Blind Hunter + Edge Case Hunter + Acceptance Auditor). All 7 ACs + AD-1/4/5/6/9 satisfied. Severity set at triage.*

- [x] [Review][Patch] **HIGH — crafted valid-base64 cursor → 500 not 400** [backend/app/repositories/products.py] — `_decode_cursor` only checks `isinstance(dict)`; a well-formed base64 JSON dict with wrong keys reaches DynamoDB `query` and raises an uncaught `ClientError` (ValidationException) → 500. Fix: validate the decoded key shape AND wrap the query so a bad `ExclusiveStartKey` `ClientError` re-raises as `AppError(invalid_cursor, 400)`; add a real end-to-end decode test (base64 of `{"foo":"bar"}` → 400) — the FakeRepo API test masked this. (blind+edge)
- [x] [Review][Patch] MED — trailing empty page / phantom "Load more" [backend/app/repositories/products.py, frontend/src/pages/ProductListPage.tsx] — real DynamoDB returns a non-null LastEvaluatedKey when it stops exactly at Limit even if nothing remains; moto omits it (so the 3-page test passes but prod would be 4 with an empty last). Fix: frontend treats an empty load-more result as end (cursor→null); note repo look-ahead as the deeper fix. (blind+edge)
- [x] [Review][Patch] LOW — endpoint bypasses FastAPI DI [backend/app/api/products.py] — calls `get_catalog_service()` directly; use `Depends(get_catalog_service)` so overrides + OpenAPI DI work. (blind)
- [x] [Review][Patch] LOW — `productId` not URL-encoded in PDP href [frontend/src/pages/ProductListPage.tsx] — use `encodeURIComponent`. (blind)
- [x] [Review][Patch] LOW — no `max_length` on the `cursor` query param [backend/app/api/products.py] — bound it to avoid decoding an arbitrarily large blob. (edge)
- [x] [Review][Defer] MED — `Limit` + future `FilterExpression` (1.4–1.6) under-fills pages [backend/app/repositories/products.py] — deferred; DynamoDB applies Limit before filters, so search/facet stories must loop-to-fill. Logged for 1.4+.
- [x] [Review][Defer] MED — `_from_item` bare KeyError on an item missing a projected attr [backend/app/repositories/products.py] — deferred (same as Story 1.2; repo owns all writes, unreachable now).
- [x] [Review][Defer] LOW — client discards the `{error:{code,message}}` body; can't distinguish 400 stale-cursor from network error [frontend/src/api/client.ts] — deferred; parse the envelope + reset cursor on `invalid_cursor` when the UI grows.
- [x] [Review][Defer] LOW — unbounded PLP item growth (no virtualization/cap) [frontend/src/pages/ProductListPage.tsx] — deferred; fine at POC catalog size.

*Dismissed (4): StrictMode double page-1 fetch (dev-only, both replace, no dup); HMAC-signing the cursor (the 400 fix removes the 500 risk; tampering a public catalog is harmless); empty `imageUrl` broken-image fallback (seed always sets it); negative-price formatting (model enforces `price ≥ 0`).*

## Dev Notes

### Architecture patterns and constraints (MUST follow)

- **AD-4 query strategy** — this is the first real use of `gsi_listing`: `KeyConditionExpression = listingPk = "PRODUCT"`, sort key `price`. Every seeded item already carries `listingPk="PRODUCT"` (Story 1.2), so all appear in the index. Pagination uses DynamoDB `LastEvaluatedKey`; expose it **only** as an opaque base64 cursor — decode/encode lives in the repository. Do NOT Scan the table; query the GSI. [Source: ARCHITECTURE-SPINE.md#AD-4]
- **AD-1 layering** — `api/products.py → services/catalog.py → repositories/products.py`. The router does no DynamoDB and no business logic; the service maps domain→response models; the repository owns the query + cursor codec. [Source: ARCHITECTURE-SPINE.md#AD-1, #Consistency Conventions]
- **AD-5 contract** — response model is a typed Pydantic `CamelModel` so OpenAPI documents it and JSON is camelCase. Pagination is an opaque cursor (never raw keys). Errors use `{error:{code,message}}`; `limit` out of range is FastAPI's 422 (already mapped to the envelope in Story 1.1's `validation_exception_handler`). A malformed cursor is a 400 `invalid_cursor`. [Source: ARCHITECTURE-SPINE.md#AD-5]
- **AD-9 stateless** — no per-request state in memory; construct the service/repo per request (or via a cached client, as the repo already does). [Source: ARCHITECTURE-SPINE.md#AD-9]
- **AD-6 money** — `price` stays an integer (cents) end to end; convert to a display string only in the frontend. [Source: ARCHITECTURE-SPINE.md#AD-6]

### Building on Stories 1.1 & 1.2 (done & verified)

- `ProductsRepository` (Story 1.2) owns the `Products` table + `gsi_listing`/`gsi_category`; reuse it — add `list_products` there, do NOT create a new repo or a second boto3 client. Constants `GSI_LISTING`, `LISTING_PK_VALUE="PRODUCT"` already exist in `app/repositories/products.py`.
- `_from_item` already maps a DynamoDB item → `Product`; reuse it for query results.
- `CamelModel` base is in `app/models/__init__.py`; `Product` is in `app/models/product.py`.
- Error envelope + handlers (incl. 422 validation) exist from Story 1.1 in `app/core/errors.py` / `app/main.py`. Add a new `AppError` subclass or use `AppError(code="invalid_cursor", status_code=400)` for bad cursors.
- The API router aggregation is `app/api/__init__.py::api_router` — include the new products router there (health is already included).
- **Tests:** moto pattern from Story 1.2 (`test_products_repository.py`) — patch `dynamodb.get_dynamodb_client` on the module, `AWS_DEFAULT_REGION` pinned, `mock_aws`, `cache_clear` before/after. FastAPI `TestClient` pattern from `test_health.py`.
- **Frontend:** `frontend/src/api/client.ts` already has `getHealth()` + an AbortController-wrapped `get<T>` + base URL from `VITE_API_BASE_URL`; extend it. `App.tsx` currently renders the health status — replace/augment with the PLP. `pages/` and `state/` dirs exist (placeholders from 1.1). React 19 / Vite 8 / TS.
- **Live env:** Docker stack is up; dynamodb-local runs as `user: root`; 240 products already seeded (re-run `docker compose exec api python -m scripts.seed` if needed). API `http://localhost:8000`, frontend `http://localhost:5173`.
- **Commit policy:** fine-grained (e.g. models+repo query / service+endpoint / tests / frontend), review/verification fixes as their own `fix(...)` commits; propose and wait for approval.

### Implementation notes / gotchas

- A GSI query's `LastEvaluatedKey` includes the base table key **and** the GSI keys (productId, listingPk, price). Encode the whole dict; decode straight back into `ExclusiveStartKey`. Compact JSON (`separators=(",",":")`) → base64 (urlsafe) → str.
- DynamoDB `Limit` bounds items **scanned**, and for a single-partition GSI query that equals items returned until exhausted — fine here. `nextCursor` must be `null` when DynamoDB returns no `LastEvaluatedKey`.
- Guard against a decode that yields a non-dict / wrong shape → treat as `invalid_cursor` (400), don't 500.
- Keep the PLP minimal and honest — no search/facets/sort yet (those are Stories 1.4–1.6). Default order is price-ascending from `gsi_listing`; that's acceptable as the browse order for FR-1.

### Project Structure Notes

- New backend: `app/models/catalog.py`, `app/services/catalog.py`, `app/api/products.py`, `backend/tests/test_products_listing.py` (+ API tests). Modified: `app/repositories/products.py` (add `list_products`), `app/api/__init__.py` (include router), possibly `app/core/errors.py` (invalid_cursor).
- New frontend: `frontend/src/pages/ProductListPage.tsx` (+ optional small card component). Modified: `frontend/src/api/client.ts`, `frontend/src/App.tsx`.
- Out of scope: search (1.4), category facet (1.5), sort controls (1.6), PDP (Epic 2), cart (Epic 3). Do not build them here.

### References

- [Source: _bmad-output/planning-artifacts/architecture/architecture-bmad-ecommerce-2026-07-06/ARCHITECTURE-SPINE.md#AD-1, #AD-4, #AD-5, #AD-6, #AD-9]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]
- [Source: _bmad-output/implementation-artifacts/1-2-provision-products-table-and-seed-catalog.md — ProductsRepository, gsi_listing, seed]
- [Source: _bmad-output/implementation-artifacts/1-1-project-scaffold-and-local-runtime.md — API/router/error-envelope/typed-client patterns]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Claude Opus 4.8)

### Debug Log References

- `cd backend && .venv/Scripts/python -m pytest -q` → **26 passed** (15 prior + 11 new).
- `cd frontend && npm run build` → tsc + vite 8.1.3 build OK.
- Live (Docker, 240 seeded): `GET /products?limit=3` → prices 591/637/728 (ascending), opaque base64 `nextCursor`; page 2 via cursor → 774/865/911 (no overlap); `limit=0` → 422 `validation_error`; `cursor=bad!!` → 400 `invalid_cursor`. `/products` present in `/openapi.json`; frontend serves 200 at :5173.

### Completion Notes List

- `ProductSummary`/`ProductPage` response models (CamelModel → camelCase JSON, AD-5).
- `ProductsRepository.list_products(limit, cursor)` queries `gsi_listing` (listingPk="PRODUCT", price ascending); opaque urlsafe-base64 cursor encode/decode confined to the repo; malformed cursor → `AppError(invalid_cursor, 400)`.
- `CatalogService.list_products` maps domain Products → `ProductPage` (no boto3, AD-1).
- `GET /products` router (`limit` Query ge=1 le=100 default 24, `cursor`), included in `api_router`; instantiates the service per request (stateless, AD-9).
- Frontend: `listProducts` + `formatPrice` (cents→display only, AD-6) in the typed client; `ProductListPage` grid with load-more via cursor + loading/error/empty states; `App` renders the PLP.
- Scoped: no search/facet/sort (1.4–1.6), no PDP (Epic 2). Default browse order is price-ascending from `gsi_listing`.

### File List

- backend/app/models/catalog.py (new)
- backend/app/services/catalog.py (new)
- backend/app/api/products.py (new)
- backend/app/api/__init__.py (modified — include products router)
- backend/app/repositories/products.py (modified — list_products + cursor codec)
- backend/tests/test_products_listing.py (new)
- backend/tests/test_products_api.py (new)
- frontend/src/api/client.ts (modified — listProducts, types, formatPrice)
- frontend/src/pages/ProductListPage.tsx (new)
- frontend/src/App.tsx (modified — render PLP)

### Change Log

- 2026-07-06: Implemented Story 1.3 — paginated `GET /products` via gsi_listing with opaque cursor (FR-1), api→service→repository layering, PLP grid with load-more. Backend 26/26 tests pass; frontend builds; verified end-to-end (cursor pagination, validation, error envelopes).
- 2026-07-06: Code review — 0 critical to ACs; all 7 ACs + AD-1/4/5/6/9 satisfied. Applied 5 patches: **HIGH** crafted-cursor → 400 not 500 (key-shape validation + ClientError guard + real decode tests); empty-page load-more guard; `Depends` injection (+ test via dependency_overrides); `encodeURIComponent` on PDP href; `cursor` max_length. 4 deferred, 4 dismissed. Backend 28/28 tests pass; re-verified live (crafted cursor → 400, real pagination intact). Story **done**. File List += modified products.py/api/tests/frontend as above.
