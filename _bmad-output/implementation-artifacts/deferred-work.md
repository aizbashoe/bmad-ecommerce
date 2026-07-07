# Deferred Work

## Deferred from: code review of story 3-1-establish-anonymous-guest-session (2026-07-07)

- **`put_empty_cart` is an unconditional put (get-or-create race)** [backend/app/repositories/carts.py] — two concurrent first requests for the same guestId can both write; benign in 3.1 (empty carts are identical) but becomes a **cart-overwrite / line-item-loss** race once Story 3.2 stores items. **Action for 3.2:** put with `ConditionExpression="attribute_not_exists(guestId)"` and treat `ConditionalCheckFailedException` as "exists → re-read".
- **`_from_item` discards stored `items`** [backend/app/repositories/carts.py] — hard-codes `items=[]`. Correct for 3.1; **Story 3.2 must parse the `L` list** (and add a non-empty round-trip test).
- **No issuance enforcement / rate-limit on client-supplied UUIDs** [backend/app/services/cart.py] — any valid UUID in `X-Guest-Token` get-or-creates a cart, so a client can self-assign ids the server never issued (unbounded empty-cart writes). POC-acceptable (UUID4 entropy prevents cross-guest access); production should gate creation behind a server-issued signed token and/or rate-limit.
- **`getCart` duplicates `get<T>`'s error-envelope/abort logic** [frontend/src/api/client.ts] — ~15 lines copied; factor a shared `parseError(res)` / `request` helper so the envelope contract can't drift between the two.
- **`ResourceNotFoundException` (unprovisioned Carts table) not distinguished from a generic 500** [backend/app/repositories/carts.py] — a DynamoDB `ClientError` is enveloped as `internal_error` 500 by the global handler (not a raw crash), but a missing table looks like any other error. Add table-missing-specific handling if the provisioning step is ever skipped in a shared env.

## Deferred from: code review of story 5-1-align-plp-with-ux (2026-07-07)

- **Card hover-lift not implemented** [frontend/src/pages/ProductListPage.tsx] — DESIGN.md (Elevation & Depth) + EXPERIENCE.md + `plp-mock.html` specify a `0 6px 18px rgba(0,0,0,.08)` hover lift on cards. Inline styles can't express `:hover`; needs a CSS-module or a `<style>` block. Fold into a small styling-polish pass (with the focus ring below).
- **`focus`-ring token missing** [frontend/src/theme/tokens.ts + PLP/PDP] — DESIGN.md defines `focus: #159f4a` and the a11y floor wants a visible green focus ring, but `tokens.color.focus` doesn't exist and no `outline` is set (browser default ring still shows — keyboard operability is intact). Add the token + an `:focus-visible` outline in the styling-polish pass.
- **Empty first page with a cursor shows "0 products + Load more" with no grid** [frontend/src/pages/ProductListPage.tsx] — the documented loop-to-fill state; consider an explicit affordance or auto-advance rather than a bare screen.
- **Hardcoded facet-label color `#374151`** [frontend/src/pages/ProductListPage.tsx] — not a DESIGN token; move to a token (e.g. a `text-secondary`) when the palette is extended.

## Deferred from: code review of story 2-1-view-product-detail (2026-07-07)

- **Breadcrumb category not navigable** [frontend/src/pages/ProductDetailPage.tsx] — the `{category}` crumb is a `<span>`, not a link (EXPERIENCE.md → Interaction Primitives specifies breadcrumb→category nav). Requires URL-driven PLP filters (currently in-component state). Do it with the **PLP-restyle story** (query-param facets).
- **PLP does not reset the cursor on `invalid_cursor`** [frontend/src/pages/ProductListPage.tsx + api/client.ts] — the enabling `ApiError{code}` now exists (2.1); the PLP catch still shows generic copy. Now cheap: on `ApiError.code === "invalid_cursor"`, reset the cursor and refetch page 1. (Completes Epic 1 retro Action Item 1's second half.)
- **No image `onError` fallback** [frontend PLP + PDP] — a broken/empty `imageUrl` shows the browser's broken-image glyph. Add an `onError` swap to a neutral placeholder (applies to both the PLP card and the PDP gallery).
- **Empty `description` renders an empty "About this product" section** [frontend/src/pages/ProductDetailPage.tsx] — hide the section (or show a placeholder) when `description` is blank. Cosmetic; POC seed always populates it.
- **PDP effect has no `AbortController` cleanup** [frontend/src/pages/ProductDetailPage.tsx] — the request-id guard prevents stale-state application, but the in-flight `getProduct` fetch isn't cancelled on unmount / id change (StrictMode double-fires in dev). Wire an abort signal into `getProduct` and abort in the effect cleanup.
- **No frontend test runner** [frontend] — AC3/AC4/AC7 behavior is covered only by the build + live check (spec-permitted). Add Vitest + a client test (404 body → `ApiError{code:"not_found"}`; not-found vs generic branch) when the UI matures.
- **`_from_item` bare `KeyError`** [backend/app/repositories/products.py] — reused by `get_product`; a partially-written item raises an opaque `KeyError` → 500. Still unreachable (repo owns all writes). Same long-standing deferral as 1.2/1.3.

## Deferred from: code review of story 1-5-filter-by-category-facet (2026-07-06)

- **`gsi_listing` single hot partition** [backend/app/repositories/products.py] — every unfiltered/multi-category/search query hits one partition (`listingPk="PRODUCT"`) and filters within it; loop-to-fill amplifies reads. Fine at POC scale; beyond it, shard the listing partition (e.g. `listingPk = "PRODUCT#<n>"`) or move search/facets to OpenSearch (the AD-4 production path).
- **`toggleCategory` functional-update race** [frontend/src/pages/ProductListPage.tsx] — derives `next` from the `selected` closure; two toggles in one render batch can race. Use `setSelected(prev => …)` and derive the fetch categories from the computed value. Low impact (single-user POC + request-id guard).
- **`ValidationException` labeling on paged calls** [backend/app/repositories/products.py] — a paged `ValidationException` is always mapped to `invalid_cursor`; distinguish cursor/key errors from other validation failures if more filters are added.
- **Route-shadowing regression test** [backend/app/api/products.py] — add a test that `/products/categories` still resolves once a `/products/{id}` (PDP, Epic 2) route exists.
- **Case-insensitive category** — category match is exact (`gsi_category`/`IN`); a mismatched-case value via direct API returns empty. Normalize if needed.

## Deferred from: code review of story 1-4-search-products-by-keyword (2026-07-06)

- **~~Cursor not bound to the search term~~ — RESOLVED in Story 1.6** — the cursor now embeds a query fingerprint (sort + search + categories); a mismatched replay → `invalid_cursor` 400. This closes the search (1.4) and category (1.5) "cursor not bound" items too.
- **Frontend discards the error envelope** [frontend/src/api/client.ts] — 400 `invalid_cursor` shows as a generic error and the bad cursor isn't reset. (Same as the Story 1.3 deferral.) Parse `{error:{code,message}}` and reset the cursor on `invalid_cursor`.
- **Search is substring, not token, and not Unicode-normalized** [backend searchText/contains] — `contains` matches contiguous substrings ("tee" ⊂ "canteen"; "red shirt" misses reordered text) and does no NFC/NFKC folding. Acceptable at POC scale; revisit with tokenization or a search engine (the AD-4 OpenSearch path) if search quality matters.

## Deferred from: code review of story 1-3-browse-catalog-with-pagination (2026-07-06)

- **`Limit` + `FilterExpression` under-fills pages** [backend/app/repositories/products.py] — DynamoDB applies `Limit` before a `FilterExpression`, so once Stories 1.4 (search) / 1.5 (category facet) add filters, a page can return fewer than `limit` matches (or zero) while more exist. Those stories must loop-to-fill (keep querying with the cursor until `limit` matches are accumulated) or filter above the repo. **Action for 1.4/1.5.**
- **`_from_item` bare `KeyError`** [backend/app/repositories/products.py] — an item missing a projected attribute raises an opaque KeyError. Unreachable now (repo owns all writes); harden with validation if external writers appear. (Same deferral as Story 1.2.)
- **Frontend discards the error envelope** [frontend/src/api/client.ts] — `get<T>` throws a generic message; the PLP can't distinguish a 400 stale/`invalid_cursor` from a network error. When the UI matures, parse `{error:{code,message}}` and reset the cursor on `invalid_cursor`.
- **Unbounded PLP item growth** [frontend/src/pages/ProductListPage.tsx] — "Load more" appends without a cap/virtualization; fine at the POC's ~240-item catalog, revisit for large catalogs.

## Deferred from: code review of story 1-2-provision-products-table-and-seed-catalog (2026-07-06)

- **`ensure_table` accepts an existing table with a mismatched schema** [backend/app/repositories/products.py] — describe-then-return does not compare KeySchema/GSIs. Fine for the POC; if the table schema ever evolves, add a schema-diff/migration check.
- **`_from_item` raises a bare `KeyError` on a partially-written item** [backend/app/repositories/products.py] — unreachable now (the repo owns all writes); harden with descriptive validation if external writers are ever introduced.
- **Runtime image ships the seed script** (`COPY scripts ./scripts`) [backend/Dockerfile] — deliberate so `docker compose exec api python -m scripts.seed` works; move the seed to a separate job/stage before any real deployment.


## Deferred from: code review of story 1-1-project-scaffold-and-local-runtime (2026-07-06)

- **`/docs` + `/openapi.json` exposed with no gating** [backend/app/main.py] — accepted for the local POC (docs are the contract source of truth). Before any shared/AWS deploy, gate docs behind config (e.g. disable when `dynamodb_endpoint` is empty / "prod").
- **Frontend container runs the Vite dev server** [frontend/Dockerfile] — fine for local-first walking skeleton. Add a `vite build` + static-serve stage before any real deployment.
- **`.env.example` `DYNAMODB_ENDPOINT` only valid inside the compose network** [.env.example] — `http://dynamodb-local:8000` doesn't resolve when running the backend directly on the host (that needs `http://localhost:8001`). Add a host-run variant/note if/when someone runs the API outside Docker.
