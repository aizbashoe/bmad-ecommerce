---
baseline_commit: 9cb328b
---

# Story 1.5: Filter by category facet

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an anonymous shopper,
I want to filter products by category,
so that I can narrow the catalog to what I care about.

## Acceptance Criteria

1. **Category filter (FR-3, AD-4).** `GET /products?category=<c>` returns only Products in the selected category. Multiple categories are supported (repeat the param, e.g. `?category=home&category=books`) and combine as a logical OR (a Product in *any* selected category matches).
2. **Combines with search (FR-3 + FR-2).** `search` and `category` compose: results match the keyword **and** fall in one of the selected categories. Pagination (opaque cursor, `limit`) works for every combination and pages through all matches once (no dup/gap), ending `nextCursor: null`.
3. **Query strategy (AD-4).** A **single** category with **no search** queries `gsi_category` (PK=category, SK=price, price-ascending, cursor) — the AD-4 fast path. **Multiple** categories, or category **+ search**, query `gsi_listing` with a composed `FilterExpression` (`category IN (…)` and/or `contains(searchText, …)`) using the existing loop-to-fill. No table Scan.
4. **Cursor safety.** The opaque cursor accepts both `gsi_category` and `gsi_listing` key shapes; a cursor minted under one query used under an incompatible one is rejected as `invalid_cursor` (400) rather than 500.
5. **Facet values endpoint.** `GET /products/categories` returns the distinct category list (sorted) so the UI can render facet options. camelCase JSON, documented in OpenAPI.
6. **PLP facet UI.** The PLP shows category options (from `/products/categories`) as multi-select controls; selecting/deselecting refetches page 1 with the active categories **and** the active search term. Active filters are shown as removable chips with a **Clear all** control; removing/clearing refetches. Empty result shows the existing empty-state.
7. **No-filter unchanged.** With neither `category` nor `search`, behavior is exactly Story 1.3 (full catalog via `gsi_listing`, price ascending).
8. **Tested.** moto: single-category via gsi_category (sorted, paginated); multi-category OR on gsi_listing; category+search AND; cursor round-trip no dup/gap for each path; a gsi_category-minted cursor rejected on a gsi_listing query (invalid_cursor); `list_categories` returns the distinct sorted set. API: `?category=` single/multi passthrough, `?category=&search=` combined, `/products/categories` shape, bad-cursor 400.

## Tasks / Subtasks

- [x] **Task 1 — Repository: category filtering** (AC: #1, #2, #3, #4, #7)
  - [x] Extend `ProductsRepository.list_products(limit, cursor, search=None, categories=None)` (`categories: list[str] | None`).
  - [x] **Fast path:** exactly one category AND no search → query `gsi_category` with `KeyConditionExpression = category = :c`, `ScanIndexForward=True`, `Limit`, `ExclusiveStartKey` from the cursor. (Single-partition, natively price-sorted + paginated — the AD-4 lesson.)
  - [x] **Composed path:** multiple categories, or any search → query `gsi_listing` (existing loop-to-fill) with the composed `FilterExpression`: add `contains(searchText, :q)` when searching (from 1.4) and `category IN (:c0, :c1, …)` when categories present; join clauses with `AND`. Reuse `_chunks`/expr-value building.
  - [x] **Cursor codec:** allow both key shapes — accept `_LISTING_CURSOR_KEYS` (`listingPk, price, productId`) and a new `_CATEGORY_CURSOR_KEYS` (`category, price, productId`). Keep the `ClientError`→`invalid_cursor` guard so a cursor used against the wrong index yields 400, not 500.
  - [x] Normalize/validate categories (trim, drop empties); an empty list = no category filter.
- [x] **Task 2 — Repository: distinct categories** (AC: #5)
  - [x] Add `list_categories() -> list[str]`: return the distinct, sorted category set. A paginated `Scan` projecting only `category` is acceptable at POC scale (document it); or query the known set. Keep it in `ProductsRepository` (AD-1/AD-3).
- [x] **Task 3 — Service + API** (AC: #1, #2, #5)
  - [x] `CatalogService.list_products(..., categories)` passthrough; add `CatalogService.list_categories()`.
  - [x] `GET /products` gains `category: list[str] | None = Query(default=None)` (repeatable). Trim/drop-empty before use.
  - [x] `GET /products/categories` → a `CategoryList` model (`{ "categories": [str] }`, camelCase) via the service. Register the route in `api_router` (mind route ordering so `/products/categories` isn't shadowed by a `/products/{id}` route — none exists yet, but order it before any future param route).
- [x] **Task 4 — Frontend facet UI** (AC: #6)
  - [x] `client.ts`: `listProducts({ limit, cursor, search, categories })` appends repeated `category` params; add `listCategories(): Promise<string[]>` + `CategoryList` type.
  - [x] `ProductListPage`: on mount, fetch categories; render a multi-select (checkbox list or chips). Selecting a category resets pagination and refetches page 1 with `{ search: activeSearch, categories: selected }`; load-more carries both. Show active filters (search term + each category) as removable chips + a **Clear all** that resets both search and categories. Keep the latest-wins request-id guard from 1.4.
- [x] **Task 5 — Tests** (AC: #8)
  - [x] `backend/tests/test_products_category.py` (moto): seed products across ≥3 categories; single-category (assert gsi_category path — only that category, price-ascending, paginated); multi-category OR; category+search AND; cursor round-trip no dup/gap on both paths; a `gsi_category`-minted cursor passed to a multi-category (`gsi_listing`) call → `invalid_cursor`; `list_categories` distinct+sorted.
  - [x] Extend `test_products_api.py`: `?category=home`, `?category=home&category=books`, `?category=home&search=x`, `/products/categories` shape; update `_FakeRepo` to accept `categories` + add `list_categories`.
- [x] **Task 6 — Verify locally** (AC: all)
  - [x] `docker compose up -d --build api frontend` (data already seeded with `searchText`/`category`).
  - [x] `curl 'http://localhost:8000/products/categories'` → the distinct list. `curl 'http://localhost:8000/products?category=home&limit=5'` → only home, price asc. `curl 'http://localhost:8000/products?category=home&category=books&search=mug'` → combined. Open `http://localhost:5173` → category checkboxes filter, chips remove, Clear all resets; combine with the search box.

### Review Findings

*Code review 2026-07-06 (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Dual query-path + bidirectional cursor rejection confirmed correct; 7/8 ACs full, AC-8 partial (test gap). Severity at triage.*

- [x] [Review][Patch] MED — >100 `?category=` params → uncaught `ValidationException` → 500 (DynamoDB `IN` max 100 operands) [backend/app/repositories/products.py] — dedup categories, and cap at 100 → 400. (blind+edge)
- [x] [Review][Patch] MED — empty-page-with-cursor shows "No products match" AND "Load more" together [frontend/src/pages/ProductListPage.tsx] — `isEmpty` must also require `!cursor`. (blind+edge)
- [x] [Review][Patch] MED — AC-8 test gap: no composed-path (gsi_listing) cursor round-trip, and only one cross-index direction tested [backend/tests/test_products_category.py] — add a multi-category/limit-paged round-trip (no dup/gap) + a listing-cursor-on-fast-path rejection. (auditor)
- [x] [Review][Patch] LOW — `list_categories` Scan uses `ConsistentRead=True` (needless RCU; facet options don't need read-after-write) [backend/app/repositories/products.py] — drop it. (blind)
- [x] [Review][Defer] LOW — `toggleCategory` derives `next` from the `selected` closure; two toggles in one batch can race — use functional update. (blind)
- [x] [Review][Defer] LOW — a non-cursor `ValidationException` on a paged call is mislabeled `invalid_cursor` (the >100 cap removes the main source). (blind)
- [x] [Review][Defer] LOW — no regression test that `/products/categories` isn't shadowed once a future `/products/{id}` exists. (blind)
- [x] [Review][Defer] MED — `gsi_listing` uses a single constant partition (`listingPk="PRODUCT"`); the filter/loop-to-fill path hits one hot partition — degrades beyond POC scale (architecture-level; already noted). (blind)
- [x] [Review][Defer] LOW — case-mismatched category via direct API silently returns empty (UI emits data-exact values). (edge)

*Dismissed: filtered pages may exceed `limit` (by design — no-trim keeps the cursor gap-free, documented); the numerous "verified handled" items both hunters confirmed (empty vs None categories, non-existent/whitespace categories, cross-index cursor both directions, 1→2 switch with stale cursor, empty-table facet, unicode, chip removal keeping categories).*

## Dev Notes

### Architecture patterns and constraints (MUST follow)

- **AD-4 is the point of this story.** `gsi_category` (PK=category, SK=price) was provisioned in Story 1.2 exactly for this facet. Use it for the single-category fast path — that's the DynamoDB lesson (native partition + sort + cursor, no filter scan). For multi-select / combined-with-search, the single-partition Query can't span categories, so fall back to `gsi_listing` + `FilterExpression` (the composable path built in 1.4). Document this split. [Source: ARCHITECTURE-SPINE.md#AD-4]
- **AD-1 layering** — all query logic + cursor codec stays in `ProductsRepository`; service/router just pass `categories`. boto3 only in repositories. [Source: ARCHITECTURE-SPINE.md#AD-1]
- **AD-5 contract** — `category` is a repeatable query param; `/products/categories` returns camelCase JSON documented in OpenAPI; errors use the envelope; cursor stays opaque. [Source: ARCHITECTURE-SPINE.md#AD-5]
- **Loop-to-fill still applies** on the `gsi_listing` composed path (Limit before FilterExpression) — reuse it; do not reintroduce the under-fill bug. [Source: _bmad-output/implementation-artifacts/1-4-search-products-by-keyword.md]

### Building on Stories 1.2–1.4 (done & verified)

- `list_products(limit, cursor, search)` already builds an **optional `filter_clauses` list** joined with `AND` and does loop-to-fill on `gsi_listing` — Story 1.4 was written to be composable for exactly this. Add the `category IN` clause there; add the `gsi_category` fast-path branch above it.
- `_encode_cursor`/`_decode_cursor` + `_LISTING_CURSOR_KEYS` exist ([backend/app/repositories/products.py]). Add `_CATEGORY_CURSOR_KEYS` and let `_decode_cursor` accept whichever set matches; the `ClientError`→`invalid_cursor` guard already covers a cross-index cursor.
- Items already carry `category` (Story 1.2) and `searchText` (Story 1.4); `gsi_category` projects ALL, so `searchText` is available there too (but the fast path is single-category-no-search, so it won't need it).
- `CatalogService`, `GET /products` (service via `Depends`), `ProductSummary`/`ProductPage` (CamelModel) — extend, don't duplicate.
- Frontend: `ProductListPage` has search + the latest-wins `requestId` guard + cursor-driven paging (1.4). Add categories to the same `fetchPage({cursor, search, categories})` shape so the guard and load-more keep working.
- **Route ordering:** register `/products/categories` before any `/products/{id}` path (none yet — PDP is Epic 2 — but keep it in mind).
- **Live env:** Docker up; 240 products seeded (6 categories: apparel, electronics, home, books, toys, sports). API `:8000`, UI `:5173`.
- **Commit policy:** fine-grained (repo category+categories / API+service / frontend / tests); review fixes as their own `fix(...)`. `_bmad-output/` is tracked — the sprint-status flip rides with the story commits. Propose & wait for approval.

### Gotchas

- **`IN` expression values:** build `:c0..:cN` placeholders dynamically; DynamoDB caps `IN` at 100 operands (fine here). `category`/`searchText` aren't reserved words, so no `ExpressionAttributeNames` needed.
- **Cursor coherence:** switching category selection changes the query path/keys, so always reset the cursor (refetch page 1) when the filter set changes — never carry a cursor across a filter change (the frontend does this; the invalid_cursor guard is the backstop).
- **`list_categories` cost:** a Scan is O(table); fine for 240 items. Note it as a POC choice (a maintained category set or a GSI-count is the production path) — add to deferred-work if raised in review.

### Project Structure Notes

- Modified backend: `app/repositories/products.py` (category branch + `_CATEGORY_CURSOR_KEYS` + `list_categories`), `app/services/catalog.py`, `app/api/products.py` (+ `/products/categories`), `app/models/catalog.py` (`CategoryList`). New test `backend/tests/test_products_category.py`; modified `test_products_api.py`.
- Modified frontend: `src/api/client.ts` (categories), `src/pages/ProductListPage.tsx` (facet UI).
- Out of scope: **sort controls (Story 1.6)**, PDP (Epic 2). Do not build them.

### References

- [Source: _bmad-output/planning-artifacts/architecture/architecture-bmad-ecommerce-2026-07-06/ARCHITECTURE-SPINE.md#AD-1, #AD-4, #AD-5]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5]
- [Source: _bmad-output/implementation-artifacts/1-4-search-products-by-keyword.md — composable FilterExpression, loop-to-fill, cursor codec, PLP request-id guard]
- [Source: _bmad-output/implementation-artifacts/1-2-provision-products-table-and-seed-catalog.md — gsi_category schema, seeded categories]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Claude Opus 4.8)

### Debug Log References

- `cd backend && .venv/Scripts/python -m pytest -q` → **45 passed** (36 prior + 9 new).
- `cd frontend && npm run build` → tsc + vite build OK.
- Live (Docker): `/products/categories` → 6 distinct sorted; `?category=home` → gsi_category path, price-ascending; `?category=home&category=books&limit=80` → 40 home + 40 books, no others; `?category=home&search=mug` → AND (all home & mug).

### Completion Notes List

- `ProductsRepository.list_products` now takes `categories`; **AD-4 fast path** (single category, no search) → `gsi_category` Query (native price sort + cursor); otherwise `gsi_listing` + composed FilterExpression (`category IN (...)` and/or `contains(searchText)`) with the existing loop-to-fill.
- Added `_CATEGORY_CURSOR_KEYS`; `_decode_cursor` validates per active path, so a cross-index cursor is rejected as `invalid_cursor` (400) — verified by test.
- `list_categories()` — distinct+sorted via a projection Scan (POC-acceptable; noted for review). `CategoryList` model + `GET /products/categories` (registered before the listing route). `category` is a repeatable query param on `GET /products`.
- Frontend: `listCategories` + `categories` on `listProducts`; PLP renders category checkboxes, combines with search, removable chips + **Clear all**; keeps the latest-wins request-id guard and cursor-driven paging.
- boto3 confined to the repository (AD-1); camelCase + OpenAPI (AD-5). Scope kept to the facet — sort (1.6) not built.

### File List

- backend/app/repositories/products.py (modified — categories param, gsi_category fast path, _CATEGORY_CURSOR_KEYS, list_categories)
- backend/app/services/catalog.py (modified — categories passthrough + list_categories)
- backend/app/api/products.py (modified — category param + GET /products/categories)
- backend/app/models/catalog.py (modified — CategoryList)
- backend/tests/test_products_category.py (new)
- backend/tests/test_products_api.py (modified — category/categories tests, FakeRepo update)
- frontend/src/api/client.ts (modified — categories + listCategories)
- frontend/src/pages/ProductListPage.tsx (modified — category facet UI; review: isEmpty guards on !cursor)

### Change Log

- 2026-07-06: Implemented Story 1.5 — category facet (FR-3). Single-category via gsi_category (AD-4 fast path), multi-category OR + category+search via gsi_listing composed FilterExpression + loop-to-fill; dual-shape cursor codec; GET /products/categories; PLP multi-select facet with chips + Clear all. Backend 45/45 tests pass; frontend builds; verified end-to-end (both GSI paths, combined search, categories endpoint).
- 2026-07-06: Code review — dual query-path + cursor logic confirmed correct; 4 patches applied: dedup+cap categories at 100 (>100 was a 500 → now 400 too_many_categories, verified live), isEmpty guards on `!cursor` (no more "no results" + "Load more" together), added composed-path cursor round-trip + reverse cross-index + >100 cap tests, dropped ConsistentRead on the categories scan. 5 deferred, dismissals noted. Backend 48/48 tests pass; frontend builds. Story done.
