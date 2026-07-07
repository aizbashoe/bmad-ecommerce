---
baseline_commit: 1cc8f49a9c39354e93b76d6861ce7c5f67d6c290
---

# Story 5.1: Align the PLP with the new UX

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an anonymous shopper,
I want the product list to match the storefront's visual design,
so that browsing feels like one coherent, polished store.

## Acceptance Criteria

1. **Given** the PLP, **When** it renders, **Then** the category facet appears in a **left sidebar** (checkbox list) with the results grid to its right in a two-column layout, per `EXPERIENCE.md` (PLP IA) and `mockups/plp-mock.html` — replacing the current top-bar checkbox row.
2. **Given** the toolbar, **Then** it shows the **result context** (a product count/label) on the left and the **existing sort control** on the right; the active-filter chips + **Clear all** are preserved (may move but must remain present and functional).
3. **Given** the product cards, **Then** they use the `DESIGN.md` tokens via `frontend/src/theme/tokens.ts` — card surface/border/radius, the category **badge** (dark pill over the image), the **price accent** (`tokens.color.price`), and the availability treatment ("In stock" green / "Out of stock" muted).
4. **Given** all Epic 1 PLP behavior, **Then** it is **preserved exactly**: keyword search (submit-driven), multi-category OR filter, price sort, cursor **"Load more"** (an empty page may still carry a cursor — never treat 0 new items as "the end"), empty/loading/error states, the latest-wins `requestId` guard, and client-side `<Link>` navigation to the PDP.
5. **Given** a stale/invalid cursor, **When** the client throws an `ApiError` with `code === "invalid_cursor"`, **Then** the PLP resets the cursor and refetches page 1 (rather than showing the generic error) — completing Epic 1 retro action item 1's second half (deferred from 2.1).
6. **Given** the restyle, **Then** the backend is unchanged and `tsc -b && vite build` passes; the PLP still renders inside the shared `StoreHeader` shell (no duplicate header).
7. **Given** the PDP breadcrumb category→filtered-PLP link (deferred from 2.1), **Then** it is implemented **only if** URL-driven PLP filters are introduced in this story; otherwise it is explicitly left deferred (do not fake it).

## Tasks / Subtasks

- [x] **Task 1 — Two-column shell + left facet sidebar (AC: 1, 2)**
  - [x] Body is now a `250px 1fr` grid: left `<aside>` "Category" facet (moved from the top-bar row) + right results column (toolbar + chips + grid + Load-more).
  - [x] Toolbar: result context ("Showing N products (more available)") left + existing sort `<select>` right. Search form kept above the two columns (header search out of scope).
  - [x] Chips + Clear-all preserved (now in the results column); `toggleCategory`/`applyFilters`/`onSortChange`/`clearAll` unchanged.
- [x] **Task 2 — Token-based card + control styling (AC: 3)**
  - [x] Cards/badge/price/availability/facet/buttons styled from `theme/tokens.ts` (card surface+line+radius, badge pill, price `tokens.color.price`, `stockIn`/`stockOut`, facet accent + Search/Load-more in `green`). Badge width-guard/ellipsis kept.
- [x] **Task 3 — invalid_cursor recovery (AC: 4, 5)**
  - [x] `fetchPage` catch: `err instanceof ApiError && err.code === "invalid_cursor" && opts.cursor` → reset items+cursor and refetch page 1 once (retry sends no cursor, so it can't re-trigger). Other errors keep the generic state. `ApiError` imported.
- [x] **Task 4 — Preserve all Epic 1 behavior (AC: 4)**
  - [x] All handlers/state unchanged: search submit resets paging; multi-category OR; sort preserves search+categories; Load-more off `nextCursor`; `isEmpty` requires `!cursor`; `requestId` guard intact; cards are `<Link>`.
- [x] **Task 5 — Breadcrumb link decision (AC: 7)**
  - [x] Decision: **URL-driven filters NOT introduced** this story → PDP breadcrumb category stays a non-link `<span>`; the item remains in `deferred-work.md`. (PLP filters are still in-component state.)
- [x] **Task 6 — Verify (AC: 6)**
  - [x] `tsc -b && vite build` clean (245 kB bundle).
  - [x] Live (docker compose, rebuilt frontend): PLP serves 200; backend listing + `/categories` unchanged (200); single header (no duplicate — StoreHeader from App.tsx).

## Dev Notes

### Scope & guardrails
- **Restyle only — no behavior change and no backend change.** Every Epic 1 capability must survive byte-for-byte in behavior. The risk here is a regression during the layout move, not new logic. Keep the existing state hooks and handlers; only change markup/styling and add the `invalid_cursor` recovery.
- The shared `StoreHeader` already renders above the PLP (from story 2.1 / `App.tsx`). **Do not add another header** in the PLP. The PLP body starts below the shell.
- `formatPrice` stays `$` (currency localization out of scope, as in 2.1). The `₴` in mocks is illustrative only.

### Current PLP state (what must be preserved) — `frontend/src/pages/ProductListPage.tsx`
- State: `items`, `cursor`, `loading`, `error`, `initialized`, `query`/`activeSearch`, `allCategories`, `selected`, `sort`, and `requestId` (latest-wins).
- `fetchPage({cursor?, search, categories, sort})` — sets `requestId`, calls `listProducts`, drops superseded responses, appends on cursor / replaces on page 1, sets `cursor = page.nextCursor`. **Load-more is cursor-driven** (loop-to-fill can return an empty page WITH a cursor).
- `applyFilters(search, categories, sortOpt)` resets items+cursor and refetches page 1. `onSubmit` (search), `toggleCategory` (OR facet), `onSortChange`, `clearAll` (keeps sort). `hasFilters`, `isEmpty = initialized && !error && items.length === 0 && !cursor`.
- Cards are already `<Link to={/products/:id}>` (from 2.1) with the category badge pill. Facet is currently a top `flex-wrap` checkbox row (`allCategories.map`).

### Target layout — `EXPERIENCE.md` + `mockups/plp-mock.html`
- Two-column: `~250px` left facet sidebar (surface card, "Category" heading, checkbox list, Clear-all) + fluid results column. Toolbar above the grid: result count/label left, sort select right. Grid: `repeat(auto-fill, minmax(200px, 1fr))` (unchanged), token-styled cards. See `DESIGN.md` → Layout & Spacing, Components; the mock is the visual target (spines win on any conflict).
- No result **counts per category** (we don't aggregate them — same honest-data stance as the UX contracts). "Result context" is the total/loaded label, not per-facet counts.

### invalid_cursor recovery (AC 5) — the deferred half of retro action item 1
- `ApiError { status, code, message }` already exists in `frontend/src/api/client.ts` (added in 2.1). `listProducts` rejects with it on a 400 `invalid_cursor`.
- In `fetchPage` catch: if it's an `ApiError` with `code === "invalid_cursor"` AND this call used a cursor, reset paging and refetch page 1 once (don't loop). Otherwise set the generic error. This keeps a stale "Load more" cursor from dead-ending the list.

### Testing standards
- No frontend test runner is wired (deferred; see `deferred-work.md`). Verify via `tsc -b && vite build` + the live docker check (the Epic 1 / 2.1 pattern). If you choose to add Vitest, that's a bonus, not required by this story.

### Project Structure Notes
- Touch only `frontend/src/pages/ProductListPage.tsx` (layout + styling + `invalid_cursor` recovery) and import `ApiError` + `tokens`. Optionally extract a small `FacetSidebar`/`Toolbar` component under `frontend/src/components/` if it improves clarity — not required. No backend, no new deps.

### References
- [Source: epics.md → Epic 5 / Story 5.1]
- [Source: ux-designs/ux-bmad-ecommerce-2026-07-07/EXPERIENCE.md] — PLP IA, Component Patterns, State Patterns (invalid_cursor), a11y floor.
- [Source: ux-designs/ux-bmad-ecommerce-2026-07-07/DESIGN.md] — tokens, card/badge/facet components, Layout & Spacing.
- [Source: ux-designs/…/mockups/plp-mock.html] — visual target.
- [Source: _bmad-output/implementation-artifacts/deferred-work.md → 2.1 review] — PLP invalid_cursor reset; breadcrumb category link.
- [Source: frontend/src/theme/tokens.ts, frontend/src/api/client.ts (ApiError), frontend/src/components/StoreHeader.tsx] — existing shared shell + tokens from 2.1.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Debug Log References

- `npm run build` (`tsc -b && vite build`) → clean (245 kB bundle).
- Live (docker compose, rebuilt frontend): PLP `/` → 200; backend `/products?limit=1` and `/products/categories` unchanged → 200; single shared header (StoreHeader from `App.tsx`, none added in the PLP).

### Completion Notes List

- Restyle-only, frontend-only: `ProductListPage.tsx` restructured into a `250px 1fr` two-column layout — left `<aside>` Category facet + right results column (toolbar with result context + sort, chips + Clear-all, grid, Load-more). All styling now flows from `theme/tokens.ts` (card, badge, price in the red accent, `stockIn`/`stockOut`, green Search/Load-more + facet accent).
- **All Epic 1 behavior preserved** — no handler or state logic changed; only markup/styling + the new catch branch.
- **invalid_cursor recovery (deferred from 2.1, retro action item 1 second half):** a stale Load-more cursor → 400 `invalid_cursor` now resets paging and reloads page 1 once (retry carries no cursor, so no loop); other errors still show the generic error.
- **Breadcrumb category link:** intentionally left deferred — URL-driven PLP filters were NOT introduced (PLP filters remain in-component state); the item stays in `deferred-work.md`.
- Backend untouched; `formatPrice` still `$`. Availability now shows "In stock"/"Out of stock" (was out-of-stock only) to match the mock.

### File List

- `frontend/src/pages/ProductListPage.tsx` (M) — two-column layout, token styling, invalid_cursor recovery, `ApiError`+`tokens` imports.

### Change Log

- 2026-07-07: Implemented story 5.1 (PLP UX alignment) — left-sidebar facet + token-styled cards; preserved all Epic 1 behavior; folded in the deferred PLP `invalid_cursor` cursor-reset. Frontend-only, no backend change. Status → review.
- 2026-07-07: Code review (3-lens adversarial) — Approve-with-patches. 2 patches applied (result-context label gated on loading/error; recovery no longer blanks items), 4 deferred. Build clean. Status → done.

## Senior Developer Review (AI)

**Date:** 2026-07-07 · **Outcome:** Approve with patches · **Reviewers:** Blind Hunter · Edge Case Hunter · Acceptance Auditor. All 7 ACs met; AC5 (`invalid_cursor` recovery) verified loop-safe and correct w.r.t. the `requestId` guard and the `finally` early-return; all Epic 1 behavior preserved; every DESIGN token value matches.

### Action Items — patched (2)

- [x] **[Med] Result-context label ignored `loading`/`error`** (new code) — showed a contradictory count next to the error message and flashed "Showing 0 products" during a refetch. Now: `loading` → "Loading…", `error` → blank, else the count.
- [x] **[Low] `invalid_cursor` recovery blanked items before the retry** — a failed page-1 retry left an empty grid. Dropped the eager `setItems([])`; the retry's success path replaces items, a failed retry keeps them.

### Deferred (4) — see deferred-work.md

Card hover-lift + `focus`-ring token (DESIGN specifies both; inline styles can't do `:hover`/`:focus` — needs a CSS-module/style-tag polish pass); empty-first-page-with-cursor affordance (documented loop-to-fill state); toolbar nested in the results column vs. full-width in the mock (within the spec wording); hardcoded `#374151` facet-label color.

### Dismissed (1)

- `invalid_cursor` arriving with no cursor (page-1) → falls through to the generic error: correct — the backend only 400s `invalid_cursor` for a *provided* cursor, so page-1 never legitimately hits it.
