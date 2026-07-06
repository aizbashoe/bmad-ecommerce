---
baseline_commit: 2470adb
---

# Story 1.6: Sort results

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an anonymous shopper,
I want to sort the listing,
so that I can view products in the order most useful to me.

## Acceptance Criteria

1. **Sort options (FR-4).** `GET /products?sort=<s>` supports `price_asc` (low→high), `price_desc` (high→low), and a default. `sort` is an optional validated enum (`price_asc` | `price_desc`); default is `price_asc` (the current price-ascending order). An unknown value → 422 with the error envelope.
2. **Preserves filters (FR-4).** Sort composes with the active **search** and **category** filters — changing the sort reorders the *current* filtered result set; it does not clear search or categories.
3. **Both query paths honor sort (AD-4).** The direction is applied to **both** the `gsi_category` fast path and the `gsi_listing` composed path via `ScanIndexForward` (True = ascending, False = descending on the `price` sort key).
4. **Pagination under sort.** Cursor pagination works for either direction and pages through all matches once (no dup/gap), ending `nextCursor: null`. A cursor is only valid for the sort it was minted under; changing sort resets pagination (frontend refetches page 1).
5. **Contract (AD-5).** `sort` documented in OpenAPI; camelCase JSON unchanged; response shape unchanged (`ProductPage`).
6. **PLP sort control.** The PLP has a sort dropdown (Price: Low→High / High→Low). Changing it resets pagination and refetches page 1, **preserving** the active search term and selected categories; "Load more" carries the active sort. Default selection reflects `price_asc`.
7. **No-sort unchanged.** Omitting `sort` behaves exactly as today (price ascending), for every filter combination.
8. **Tested.** moto: `price_asc` vs `price_desc` ordering on the `gsi_category` fast path AND the `gsi_listing` composed path; sort combined with search and category; cursor round-trip under `price_desc` (no dup/gap). API: `?sort=price_desc` passthrough, `?sort=bogus` → 422 envelope.

## Tasks / Subtasks

- [x] **Task 1 — Repository: sort direction** (AC: #1, #2, #3, #4, #7)
  - [x] Add `sort: str = "price_asc"` to `ProductsRepository.list_products(...)`. Map to `ScanIndexForward`: `price_asc → True`, `price_desc → False`. Validate against `{"price_asc","price_desc"}`; an unknown value → `AppError(code="invalid_sort", status_code=400)` (the API also rejects it as 422 via the enum — keep the repo guard as a backstop).
  - [x] Apply `ScanIndexForward` in **both** paths: `_query_category_index` (fast path) and the `gsi_listing` composed query (replace the hardcoded `ScanIndexForward=True`). Everything else (FilterExpression, loop-to-fill, cursor codec) is unchanged.
  - [x] Cursor: no shape change — `LastEvaluatedKey` works for either direction. Do NOT try to make a cursor portable across sort directions (the frontend resets pagination on sort change; a reused cursor from the other direction still paginates from that point, which is acceptable, but the reset is the contract).
- [x] **Task 2 — Service + API** (AC: #1, #5)
  - [x] `CatalogService.list_products(..., sort)` passthrough.
  - [x] `GET /products` gains `sort: SortOption = Query(default=SortOption.price_asc)` where `SortOption` is a `str, Enum` (`price_asc`, `price_desc`) so FastAPI validates it (unknown → 422) and documents the allowed values in OpenAPI. Define `SortOption` in `app/models/catalog.py` (or `app/api/products.py`).
- [x] **Task 3 — Frontend sort control** (AC: #6)
  - [x] `client.ts`: add `sort?: "price_asc" | "price_desc"` to `listProducts` (append to query when set).
  - [x] `ProductListPage`: a `<select>` sort dropdown (Price: Low→High = `price_asc`, High→Low = `price_desc`), held in state (default `price_asc`). Changing it resets pagination and refetches page 1 via `applyFilters` **carrying search + selected categories + the new sort**; "Load more" and every `fetchPage` include the active sort. Thread `sort` through `fetchPage`/`applyFilters` alongside `search` and `categories`.
- [x] **Task 4 — Tests** (AC: #8)
  - [x] `backend/tests/test_products_sort.py` (moto): seed with distinct prices; `price_asc` returns non-decreasing, `price_desc` non-increasing — assert on **both** the single-category (gsi_category) path and a multi-category/search (gsi_listing) path; sort+search+category combined; a `price_desc` cursor round-trip pages all items once (no dup/gap).
  - [x] Extend `test_products_api.py`: `?sort=price_desc` → 200 (assert order if the fake echoes it, else shape); `?sort=bogus` → 422 `validation_error`; update `_FakeRepo.list_products` to accept `sort`.
- [x] **Task 5 — Verify locally + close Epic 1** (AC: all)
  - [x] `docker compose up -d --build api frontend`.
  - [x] `curl 'http://localhost:8000/products?sort=price_desc&limit=5'` → prices descending; `?sort=price_asc` → ascending; `?category=home&sort=price_desc` → descending within home; `?search=tee&sort=price_desc` → descending Tees; `?sort=bogus` → 422.
  - [x] Open `http://localhost:5173` → the sort dropdown reorders; search + categories persist across a sort change; Load more keeps the sort.

### Review Findings

*Code review 2026-07-07 (Blind Hunter + Edge Case Hunter + Acceptance Auditor). All 8 ACs + AD-1/4/5/9 satisfied; sort applied to both paths correctly; frontend threading clean. Severity at triage.*

- [x] [Review][Patch] MED — opaque cursor isn't bound to the query: replaying a cursor under a different sort/search/category (direct API) silently returns dup/gap [backend/app/repositories/products.py] — **fix once for all filters+sort**: encode a query fingerprint (sort + search + sorted categories) into the cursor and reject a mismatched replay as `invalid_cursor` (400). Closes the recurring 1.4/1.5/1.6 "cursor not bound" deferrals. Not reachable via the UI (it resets pagination on every change), but a real direct-API hazard. (blind+edge)
- [x] [Review][Patch] LOW — stale `list_products` docstring still says "price ascending" though sort is now a parameter [backend/app/repositories/products.py] — update. (blind)
- [x] [Review][Patch] LOW — test gaps: no cross-sort/cross-filter cursor-replay rejection test; `test_sort_passthrough_ok` asserts nothing about sort (FakeRepo doesn't echo it) [backend/tests] — add a replay-rejection test and echo+assert sort. (blind)
- [x] [Review][Defer] LOW — cursor has no integrity/signing (plain base64 JSON); a client can hand-craft a valid cursor. HMAC-sign if it ever matters (POC-acceptable; the fingerprint bind reduces impact). (blind)

*Dismissed: `_sort_ascending` 400 vs the API enum 422 (kept as internal defense-in-depth; unknown sort is rejected as 422 at the boundary); price-tie ordering (stable within a direction via the GSI's implicit productId tiebreak); enum/repo default-literal duplication (aligned, negligible drift risk).*

## Dev Notes

### Architecture patterns and constraints (MUST follow)

- **AD-4** — both GSIs use `price` as the sort key, so sort is just `ScanIndexForward` (True=asc, False=desc). No new index, no FilterExpression change. This is the smallest of the PLP stories — the plumbing (both paths, cursor, loop-to-fill) already exists; you're threading one parameter. [Source: ARCHITECTURE-SPINE.md#AD-4]
- **AD-1 layering** — sort logic stays in the repository; service/router pass the value. boto3 only in repositories. [Source: ARCHITECTURE-SPINE.md#AD-1]
- **AD-5** — use a FastAPI `Enum` param so the allowed values are validated (422 on bad input) and self-documented in OpenAPI; response shape unchanged. [Source: ARCHITECTURE-SPINE.md#AD-5]

### Building on Stories 1.3–1.5 (done & verified)

- `list_products(limit, cursor, search, categories)` currently hardcodes `ScanIndexForward=True` in the `gsi_listing` base_kwargs and in `_query_category_index`. Replace both with the mapped direction. Keep the composable FilterExpression, loop-to-fill, dedup/cap, and dual-shape cursor codec exactly as-is.
- `CatalogService.list_products` and `GET /products` (service via `Depends`, camelCase models) — extend the signature, don't restructure.
- Frontend `ProductListPage` already threads `{cursor, search, categories}` through `fetchPage`/`applyFilters` with a latest-wins `requestId` guard and cursor-driven paging — add `sort` to the same shape so those protections carry over. Chips/Clear-all are for filters; sort is a persistent control (default `price_asc`), not a chip.
- **Live env:** Docker up; 240 products seeded (prices vary). API `:8000`, UI `:5173`.
- **Commit policy:** fine-grained (repo sort / API+service+enum / frontend / tests); review fixes as their own `fix(...)`. `_bmad-output/` tracked — sprint-status flip rides with the commits. Propose & wait.
- **Epic 1 close-out:** this is the last Epic 1 story. After it's `done`, all of Epic 1's stories are complete — flip `epic-1` → `done` in sprint-status and consider `bmad-retrospective` (ER) before Epic 2 (PDP).

### Gotchas

- **Default semantics:** the PRD lists "default" as a sort option; map it to `price_asc` (there's no relevance score in this catalog). Don't invent a third ordering.
- **Cursor across sort change:** don't over-engineer portability — a `price_desc` cursor replayed under `price_asc` would resume mid-stream, so the frontend MUST reset the cursor when the sort changes (it already resets on filter change; add sort to that reset trigger).
- **Enum on the wire:** `SortOption(str, Enum)` values are the exact strings `price_asc`/`price_desc`; FastAPI serializes/validates them and rejects anything else with 422 (the existing `validation_exception_handler` envelope).

### Project Structure Notes

- Modified backend: `app/repositories/products.py` (sort→ScanIndexForward in both paths), `app/services/catalog.py`, `app/api/products.py` (+ `SortOption` enum, or in `models/catalog.py`). New test `backend/tests/test_products_sort.py`; modified `test_products_api.py`.
- Modified frontend: `src/api/client.ts` (sort), `src/pages/ProductListPage.tsx` (sort dropdown).
- Out of scope: PDP (Epic 2), cart (Epic 3), checkout (Epic 4). This story finishes Epic 1 (the PLP).

### References

- [Source: _bmad-output/planning-artifacts/architecture/architecture-bmad-ecommerce-2026-07-06/ARCHITECTURE-SPINE.md#AD-1, #AD-4, #AD-5]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.6]
- [Source: _bmad-output/implementation-artifacts/1-5-filter-by-category-facet.md — list_products dual path, cursor codec, PLP fetchPage/applyFilters]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Claude Opus 4.8)

### Debug Log References

- `cd backend && .venv/Scripts/python -m pytest -q` → **56 passed** (48 prior + 8 new).
- `cd frontend && npm run build` → tsc + vite build OK.
- Live (Docker): `?sort=price_desc` → prices descending; `?category=home&sort=price_desc` → home-only descending (gsi_category fast path); `?search=tee&sort=price_desc` → all-tee descending; `?sort=bogus` → 422.

### Completion Notes List

- `sort` added to `ProductsRepository.list_products` (default `price_asc`); `_sort_ascending` maps `price_asc→True`/`price_desc→False` (else `invalid_sort` 400), applied to **both** `_query_category_index` and the `gsi_listing` composed query. FilterExpression/loop-to-fill/dedup+cap/dual-cursor unchanged.
- `SortOption(str, Enum)` in `models/catalog.py`; `GET /products?sort=` validated by FastAPI (bad → 422) and documented in OpenAPI; `CatalogService` passthrough.
- Frontend: `sort` on `listProducts`; PLP sort `<select>` (Low→High / High→Low, default price_asc) threaded through `fetchPage`/`applyFilters` alongside search + categories; changing sort resets pagination; load-more carries sort; Clear-all keeps sort (persistent control, not a filter chip).
- boto3 confined to the repository (AD-1); camelCase + OpenAPI (AD-5). **Completes Epic 1 (PLP).**

### File List

- backend/app/repositories/products.py (modified — sort→ScanIndexForward in both paths, _sort_ascending)
- backend/app/services/catalog.py (modified — sort passthrough)
- backend/app/api/products.py (modified — sort enum query param)
- backend/app/models/catalog.py (modified — SortOption enum)
- backend/tests/test_products_sort.py (new)
- backend/tests/test_products_api.py (modified — sort passthrough + bad-sort 422, FakeRepo sort)
- frontend/src/api/client.ts (modified — SortOption + sort param)
- frontend/src/pages/ProductListPage.tsx (modified — sort dropdown threaded through)

### Change Log

- 2026-07-07: Implemented Story 1.6 — sort results (FR-4). price_asc/price_desc via ScanIndexForward on both GSI paths; preserves search + category filters and pagination; SortOption enum (bad → 422); PLP sort dropdown. Backend 56/56 tests pass; frontend builds; verified end-to-end (both paths asc/desc, combined with search/category, bad-sort 422). Completes Epic 1.
- 2026-07-07: Code review — all 8 ACs + AD-1/4/5/9 satisfied. 3 patches applied: **bound the opaque cursor to a query fingerprint (sort+search+categories)** so a cross-sort/cross-filter replay → invalid_cursor (verified live; consolidates the 1.4/1.5/1.6 "cursor not bound" deferrals); fixed stale docstring; added cursor-replay-rejection tests + sort-passthrough assertion. 1 deferred (cursor HMAC-signing). Backend 58/58 pass; frontend builds. Story done; File List += cursor codec change in repositories/products.py.
