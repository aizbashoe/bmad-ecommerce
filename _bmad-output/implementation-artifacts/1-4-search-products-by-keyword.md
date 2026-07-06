---
baseline_commit: 170eade
---

# Story 1.4: Search products by keyword

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an anonymous shopper,
I want to search products by keyword,
so that I can quickly find items matching what I have in mind.

## Acceptance Criteria

1. **Keyword search on the listing (FR-2, AD-4).** `GET /products?search=<kw>` returns only Products whose **name or description** matches the keyword; non-matching Products are excluded. Matching is **case-insensitive substring** matching.
2. **Combines with pagination.** Search results are paginated with the same opaque cursor contract as Story 1.3 (`limit`, `nextCursor`), and paging through a search yields every match once — no duplicates, no gaps — ending with `nextCursor: null`.
3. **Loop-to-fill (correctness).** Because DynamoDB applies `Limit` **before** a `FilterExpression`, a naive single query would under-fill pages. The repository must **accumulate matches across underlying pages** (following `LastEvaluatedKey`) until it has at least `limit` matches or the index is exhausted; the returned `nextCursor` must resume correctly after the last scanned page (no skipped matches).
4. **Empty result state (FR-2).** When a search matches nothing, the API returns an empty `items` list with `nextCursor: null`, and the PLP shows an explicit empty-state message with a **clear-search / reset** action.
5. **No-search unchanged.** `GET /products` with no `search` param behaves exactly as Story 1.3 (full catalog, price ascending).
6. **Contract (AD-5).** `search` is an optional, length-bounded query param; camelCase JSON; validation/errors use the existing envelope; endpoint documented in OpenAPI.
7. **Tested.** moto tests: matches only name/description hits, case-insensitive, excludes non-matches, empty-result → empty list + null cursor, loop-to-fill returns a full page when matches are sparse across the index, and cursor round-trip over a filtered result set has no dup/gap. API test: `?search=` passthrough + 200 shape. Frontend smoke optional.

## Tasks / Subtasks

- [x] **Task 1 — Searchable attribute on items** (AC: #1)
  - [x] In `ProductsRepository._to_item`, add a `searchText` attribute = lowercased `f"{name} {description}"`. Update `_from_item` to ignore it (not part of the domain `Product`). This enables case-insensitive `contains` (DynamoDB has no lower() in expressions).
  - [x] Note in the seed/dev steps that the catalog must be **re-seeded** so existing items gain `searchText` (the seed is idempotent — re-running overwrites all 240 items). `gsi_listing` projects ALL, so `searchText` is available to the FilterExpression on the index query.
- [x] **Task 2 — Repository: filtered, loop-to-fill listing** (AC: #1, #2, #3, #5)
  - [x] Extend `ProductsRepository.list_products(limit, cursor, search: str | None = None)`.
  - [x] When `search` is falsy → existing single-query behavior (unchanged).
  - [x] When `search` is set → query `gsi_listing` (price ascending) with `FilterExpression = contains(searchText, :q)`, `:q = search.strip().lower()`. **Loop-to-fill:** repeatedly query following `LastEvaluatedKey`, accumulating matched items, until accumulated ≥ `limit` OR no `LastEvaluatedKey` remains. Use a bounded per-call scan `Limit` (e.g. `max(limit, 25)`) and a safety cap on iterations. Return the accumulated matches (may modestly exceed `limit`; do **not** trim past a page boundary or the trimmed matches would be skipped by the cursor) and `nextCursor` = the last scanned page's `LastEvaluatedKey` (encoded, or `None` if exhausted).
  - [x] Keep boto3 + cursor codec in the repository (AD-1). Reuse the existing `_encode_cursor`/`_decode_cursor` (shape validation still applies).
- [x] **Task 3 — Service + API param** (AC: #1, #5, #6)
  - [x] `CatalogService.list_products` passes `search` through to the repository.
  - [x] `GET /products` gains `search: str | None = Query(default=None, max_length=100)`. Trim before use; an all-whitespace/empty `search` is treated as no search.
- [x] **Task 4 — Frontend search** (AC: #1, #4)
  - [x] `frontend/src/api/client.ts`: `listProducts({ limit, cursor, search })` adds `search` to the query string when present.
  - [x] `ProductListPage`: add a search input + submit (Enter/button). Submitting resets pagination (clear items + cursor) and fetches page 1 for the term; "Load more" carries the active `search`. Show an empty-state ("No products match ‘<term>’") with a **Clear search** control that resets to the full catalog.
- [x] **Task 5 — Tests** (AC: #7)
  - [x] `backend/tests/test_products_search.py` (moto): seed products with known names/descriptions; assert `search` returns only name/description matches, case-insensitive; excludes non-matches; empty term → behaves as no-search; a rare term spread across the index still fills a page (loop-to-fill); empty-result → `([], None)`; cursor round-trip over a filtered set has no dup/gap.
  - [x] Extend `test_products_api.py`: `GET /products?search=foo` → 200 shape; overlong `search` (>100) → 422 envelope.
- [x] **Task 6 — Verify locally** (AC: all)
  - [x] `docker compose up -d --build api` then re-seed: `docker compose exec api python -m scripts.seed` (adds `searchText`).
  - [x] `curl 'http://localhost:8000/products?search=tee&limit=5'` → only matching products; page via `nextCursor`. `curl 'http://localhost:8000/products?search=zzzznomatch'` → `{"items":[],"nextCursor":null}`.
  - [x] Open `http://localhost:5173` → search box filters the grid; clearing restores the full catalog.

### Review Findings

*Code review 2026-07-06 (Blind Hunter + Edge Case Hunter + Acceptance Auditor). All 7 ACs + AD-1/4/5/9 satisfied; backend loop-to-fill confirmed no dup/no gap. Severity at triage.*

- [x] [Review][Patch] HIGH — PLP empty-page guard defeats loop-to-fill [frontend/src/pages/ProductListPage.tsx] — `setCursor(items.length>0 ? nextCursor : null)` treats an empty-but-cursored page (backend can return `[]`+cursor at the search iteration cap) as terminal → false "no results". Drive pagination off `nextCursor` instead. (blind+edge)
- [x] [Review][Patch] HIGH — no request sequencing → stale response clobbers results [frontend/src/pages/ProductListPage.tsx, api/client.ts] — a slow load-more/search resolving after a newer submit appends/overwrites the wrong term's results. Add latest-wins request-id guard (+ ignore superseded responses). (blind+edge)
- [x] [Review][Defer] MED — cursor not bound to the search term [backend repo / frontend] — a cursor minted under term A is structurally accepted under term B. Practical trigger removed by the request-sequencing fix; embedding the filter in the cursor deferred. (blind)
- [x] [Review][Defer] LOW — client discards `{error:{code,message}}`; 400 invalid_cursor shown as generic error, cursor not reset [frontend/src/api/client.ts] — deferred (same as Story 1.3).
- [x] [Review][Defer] LOW — substring (not token) + no Unicode normalization; "tee" matches "canteen", "red shirt" misses reordered text — documented POC limitation of `contains`. (edge)

*Dismissed (3): pre-1.4 items lacking `searchText` (resolved — the required re-seed overwrote all 240 items with `searchText`, verified live); overshoot returns > `limit` (by design — no-trim keeps the cursor gap-free; `limit` documented as a floor); backend empty-with-cursor at the 40-iteration cap (only reachable > ~1000 non-matching items; POC catalog is 240, and the nextCursor-driven frontend fix pages correctly regardless).*

## Dev Notes

### Architecture patterns and constraints (MUST follow)

- **AD-4 query strategy** — search extends the `gsi_listing` query with a `FilterExpression`; do NOT introduce a Scan. Pagination stays opaque-cursor based. [Source: ARCHITECTURE-SPINE.md#AD-4]
- **THE key gotcha (from Story 1.3 review / deferred-work):** DynamoDB `Limit` bounds items **examined**, applied **before** `FilterExpression`. A single `query(Limit=24, FilterExpression=…)` can return far fewer than 24 matches (or zero) while more exist deeper in the index. **You must loop-to-fill** (follow `LastEvaluatedKey`, accumulate matches) to return a usable page. This is the whole point of the story — get it right and test it with a sparse-match case. [Source: _bmad-output/implementation-artifacts/deferred-work.md]
- **AD-1 layering** — search logic (filter + loop-to-fill + cursor) lives in `ProductsRepository`; the service/router just pass the `search` string. boto3 only in the repository. [Source: ARCHITECTURE-SPINE.md#AD-1]
- **AD-5 contract** — `search` optional + length-capped; camelCase; existing error envelope; document in OpenAPI. [Source: ARCHITECTURE-SPINE.md#AD-5]
- **Case-insensitivity:** DynamoDB expressions have no `lower()`. Store a lowercased `searchText` on each item and `contains(searchText, :q)` with `:q` lowercased. This is why the catalog must be re-seeded.

### Building on Stories 1.2 & 1.3 (done & verified)

- `ProductsRepository.list_products(limit, cursor)` and the `_encode_cursor`/`_decode_cursor` helpers already exist ([backend/app/repositories/products.py]) — **extend** them, don't duplicate. `_LISTING_CURSOR_KEYS` shape validation and the `ClientError`→`invalid_cursor` guard already handle bad cursors; keep them.
- `_to_item`/`_from_item` are the mapping seam (Story 1.2). Add `searchText` in `_to_item` only.
- `CatalogService` (Story 1.3, [backend/app/services/catalog.py]) and `GET /products` ([backend/app/api/products.py], service via `Depends`) — thread `search` through both.
- Frontend: `listProducts`, `formatPrice`, and `ProductListPage` (grid + load-more) exist from Story 1.3 — add the search box + empty-state + reset; the load-more must retain the active search term.
- **Tests:** moto pattern (patch `dynamodb.get_dynamodb_client`, `AWS_DEFAULT_REGION` pinned, `mock_aws`, cache_clear before/after) from `test_products_listing.py`; API tests via `app.dependency_overrides` from `test_products_api.py`.
- **Live env:** Docker up; `user: root` on dynamodb-local; 240 products seeded (must re-seed after the `searchText` change). API `:8000`, UI `:5173`.
- **Commit policy:** fine-grained (repo search+loop-to-fill / API+service / frontend / tests); review fixes as their own `fix(...)` commits; propose and wait for approval. Note `_bmad-output/` is now tracked — the sprint-status flip rides with the story's commits.

### Scope guard

- Search **only**. The **category facet** is Story 1.5 and **sort controls** are Story 1.6 — do not build them here. (When 1.5 lands, search + category facet must combine; design `list_products` so a category filter can be added alongside `search` without a rewrite — e.g. build the FilterExpression from optional parts.)
- No PDP, cart, or checkout.

### References

- [Source: _bmad-output/planning-artifacts/architecture/architecture-bmad-ecommerce-2026-07-06/ARCHITECTURE-SPINE.md#AD-1, #AD-4, #AD-5]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md — Limit+FilterExpression loop-to-fill]
- [Source: _bmad-output/implementation-artifacts/1-3-browse-catalog-with-pagination.md — list_products, cursor codec, PLP, tests]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Claude Opus 4.8)

### Debug Log References

- `cd backend && .venv/Scripts/python -m pytest -q` → **36 passed** (28 prior + 8 new).
- `cd frontend && npm run build` → tsc + vite 8.1.3 build OK.
- Live (Docker, re-seeded): `?search=tee&limit=5` → 5 Tee products (loop-to-fill filled a full page despite sparse matches), nextCursor set; `?search=HOODIE` → case-insensitive, all hoodies; `?search=zzzznomatch` → `{"items":[],"nextCursor":null}`.

### Completion Notes List

- `searchText` (lowercased `name + " " + description`) added to `_to_item` for case-insensitive `contains` (DynamoDB has no lower()); required a re-seed (idempotent).
- `ProductsRepository.list_products(limit, cursor, search)`: builds an optional `FilterExpression` (composable for the 1.5 category facet) and **loops-to-fill** — follows `LastEvaluatedKey`, accumulating matches until ≥ limit or exhausted, with a bounded scan page (`max(limit,25)`) and iteration cap. `nextCursor` = last scanned page's key. No-search path unchanged.
- `search` threaded through `CatalogService` and `GET /products` (`Query(max_length=100)`, trimmed; blank = no search). Reused existing cursor codec + invalid_cursor guard. boto3 stays in the repository (AD-1).
- Frontend: `listProducts({search})`; PLP gains a search box, "Results for …" label, empty-state ("No products match …") + **Clear search**; load-more retains the active term.
- Scope kept to search — category facet (1.5) / sort (1.6) not built; FilterExpression left composable.

### File List

- backend/app/repositories/products.py (modified — searchText, list_products search + loop-to-fill)
- backend/app/services/catalog.py (modified — search passthrough)
- backend/app/api/products.py (modified — search query param)
- backend/tests/test_products_search.py (new)
- backend/tests/test_products_api.py (modified — search passthrough + max_length tests, FakeRepo search kwarg)
- frontend/src/api/client.ts (modified — listProducts search param)
- frontend/src/pages/ProductListPage.tsx (modified — search box, empty-state, clear-search)

### Change Log

- 2026-07-06: Implemented Story 1.4 — case-insensitive keyword search on GET /products (FR-2) via searchText + FilterExpression with loop-to-fill pagination (resolves the Story 1.3 Limit+FilterExpression deferral); PLP search UI with empty-state/clear. Backend 36/36 tests pass; frontend builds; verified end-to-end (re-seed, search, case-insensitivity, no-match).
- 2026-07-06: Code review — all 7 ACs + AD-1/4/5/9 satisfied; backend loop-to-fill confirmed no dup/gap. Applied 2 frontend patches: pagination now driven by nextCursor (was defeated by an items-length guard when loop-to-fill returns an empty-but-cursored page), and a latest-wins request-id guard against stale responses clobbering results on rapid search/load-more. 3 deferred, 3 dismissed (incl. searchText backfill — resolved by the re-seed). Backend 36/36 pass; frontend builds. Story done. File List += frontend/src/pages/ProductListPage.tsx (request-id + cursor-driven paging).
