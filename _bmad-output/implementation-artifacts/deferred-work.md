# Deferred Work

## UX improvements (suggested, 2026-07-07)

Curated UX/UI enhancements to raise the storefront from "functional POC" to "polished" — beyond the
per-review polish items already listed below (card hover-lift, focus-ring token, image `onError`,
breadcrumb→filtered-PLP, empty states). Grouped by surface; none are blockers. `[a11y]` = accessibility.

### Cross-cutting
- **Toast/notification system** — replace inline "Added to cart ✓" / error strings with a small toast (add-to-cart success, cart/checkout errors). Consistent, non-layout-shifting feedback. [frontend/src/components]
- **Skeleton loaders** — swap the plain "Loading…" text on PLP/PDP/Cart/Checkout for content skeletons (card/row/panel placeholders) to reduce perceived latency.
- **Responsive / mobile** — DESIGN.md is desktop-only for v1; add breakpoints (single-column grid, facet drawer, stacked checkout) so the storefront works on phones. [EXPERIENCE.md Responsive section]
- **Header search** — the shared `StoreHeader` has no search box (deferred from the PLP restyle); wire a header search that drives the PLP `?search=`. Pairs with URL-driven filters.
- **URL-driven PLP state** — put search/category/sort in the query string (`useSearchParams`) so results are shareable/back-button-safe; this also unblocks the deferred breadcrumb→filtered-PLP link.
- **Currency/i18n** — `formatPrice` is hardcoded `$`; make the currency/locale configurable (the seed/mock used ₴). [frontend/src/api/client.ts]
- **`prefers-reduced-motion`** — gate any added transitions/animations behind the media query. [a11y]

### PLP
- **Editable results affordances** — a "back to top" after long Load-more sessions; consider infinite-scroll vs the explicit button (keep the button for the opaque-cursor model, but focus the first newly-loaded card for keyboard users). [a11y]
- **Per-category counts in the facet** — show counts next to each category (needs a cheap aggregate; currently omitted honestly).
- **Active-filter summary** — "N results for 'term' in Electronics" context line above the grid.

### PDP
- **Add-to-cart feedback → toast + cart peek** — on add, briefly surface a mini cart summary (item added, N in cart) instead of the inline text.
- **Related products** — "More in {category}" strip (reuses the category facet query). Adds discovery.
- **Sticky action panel** — keep price + Add-to-cart in view while scrolling the description on tall pages.

### Cart
- **Editable quantity input** — allow typing a quantity (not just −/+), validated to 1–999; debounce the update.
- **Mini-cart dropdown** — a header cart peek (line items + subtotal + Go-to-cart) without a full navigation.
- **Undo remove** — a toast with "Undo" after removing a line (re-add from the snapshot).

### Checkout
- **Multi-step affordance** — a light progress indicator (Shipping → Payment → Confirm), even though it's one page, to orient the shopper.
- **Field-level success ticks** — show a valid ✓ on completed fields, not just errors on invalid ones.
- **Country as a searchable/typeahead select** — the list is short now, but typeahead scales better.

### Accessibility (a11y) — beyond the deferred focus-ring
- **`aria-live` regions** — announce async changes (cart count updates, PLP result refreshes, "Added to cart", "Order placed") to screen readers.
- **Form errors wired to inputs** — link each error message to its field via `aria-describedby` + `aria-invalid` (partly present; make it consistent across checkout).
- **Skip-to-content link** + semantic landmarks (`<nav>`, `<main>` present; add a skip link and ensure heading order).
- **Contrast audit** — verify the red price accent and muted greys meet WCAG AA on the surfaces used.

## Deferred from: code review of Epic 4 checkout stories 4-1..4-4 (2026-07-07)

- **Cart read→write is not conditional at placement** [backend/app/services/checkout.py + repositories/orders.py] — `place_order` snapshots the cart, then the transaction deletes whatever cart currently exists (no `ConditionExpression`). A concurrent add between the read and the transaction is dropped (order written without it). AD-7 makes write+delete atomic, not read→write. POC single-user; fix: carry a cart version/hash and add a `ConditionExpression` on the Delete, retry/409 on mismatch.
- **`reference` has only 32 bits of entropy** [backend/app/services/checkout.py] — `ORD-<8 hex>` collides ~birthday-bound at scale; display-only (orderId is the key). Widen or derive from orderId if it's ever used for lookup/support.
- **`guestId` (session bearer) returned in Order/Cart response bodies** [backend/app/api] — pre-existing Epic 3 pattern; anyone with a stored response payload holds the token that authorizes that guest's cart/orders. Omit `guestId` from the response projection (it isn't needed by the UI).
- **Place-order client timeout after a server-side commit** [frontend/src/api/client.ts + pages/CheckoutPage.tsx] — a >5s `POST /checkout` that still commits leaves the client showing an unrecoverable error (retry → empty_cart). Reconcile the indeterminate state (e.g. treat as pending / look up the latest order) rather than presenting failure.
- **No transaction-error-mapping test** [backend/tests] — the `place_order_txn` `ClientError` branch (409 vs re-raise) is untested (the fake never raises). Add a test that a non-cancellation `ClientError` surfaces as 500, not 409.

## Deferred from: code review of Epic 3 cart stories 3-2..3-5 (2026-07-07)

- **First-contact guest-token race** [frontend/src/state/cart.tsx + api/client.ts] — on a first visit with no stored token, `CartProvider`'s mount `getCart()` and a PDP add can both go out tokenless, minting two guestIds; if the empty `getCart` resolves last, the just-added item is stranded under an orphaned token. POC single-user (small window). Fix: gate mutations on a resolved session (await the initial `getCart` / don't overwrite a stored token with a newly-minted one).
- **`put_cart` has no conditional/optimistic write** [backend/app/repositories/carts.py] — concurrent mutations to the same cart last-write-wins (carried from 3.1's deferral, now real with line items). Fix: version attribute + `ConditionExpression`, or item-level updates instead of full-cart put.
- **Cart-page mock deviations** [frontend/src/pages/CartPage.tsx] — the row omits the mock's category chip ("… each · Electronics") and the summary omits "Subtotal (N items)"; header hides the count at 0 (EXPERIENCE says "reads 0"). Minor visual; data-honest. Fold into a cart polish pass.
- **`update_item` doesn't re-validate product availability** [backend/app/services/cart.py] — a line's quantity can be raised even if the product later went unavailable/was removed (snapshots are intentionally frozen). Acceptable at POC; revisit if stock enforcement must be continuous.
- **Two GETs on cart-page mount + mutation still possible via `refresh` on other surfaces** — mostly resolved (mutations now `applyCart` the response); the mount `getCart` remains (needed to establish/load). No action unless the mount fetch becomes a hotspot.

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
