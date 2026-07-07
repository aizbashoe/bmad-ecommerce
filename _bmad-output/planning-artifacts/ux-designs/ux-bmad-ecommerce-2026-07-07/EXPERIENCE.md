---
name: bmad-ecommerce storefront — experience
status: final
updated: 2026-07-07
design: ./DESIGN.md
sources:
  - _bmad-output/planning-artifacts/prds/prd-bmad-ecommerce-2026-07-06/prd.md
  - _bmad-output/planning-artifacts/epics.md
  - imports/ref-rozetka-plp.md
  - imports/ref-rozetka-pdp.md
  - imports/ref-rozetka-cart.md
  - imports/ref-rozetka-checkout.md
---

# bmad-ecommerce — Experience

How the storefront *works*. Visual identity lives in [DESIGN.md](./DESIGN.md); this file owns information architecture, behavior, states, interactions, accessibility, and flows. **Both spines win on conflict with any mock or import.** Mockups: [plp](./mockups/plp-mock.html) · [pdp](./mockups/pdp-mock.html) · [cart](./mockups/cart-mock.html) · [checkout](./mockups/checkout-mock.html) · [order-summary](./mockups/order-summary-mock.html).

## Foundation

- **Form factor:** desktop web only (POC). No mobile/responsive spec this round.
- **UI system:** none imposed — hand-built React components styled to DESIGN.md tokens (the existing frontend uses inline styles; tokens formalize them).
- **Identity constraint (drives everything below):** anonymous, account-free. No login, no "my account," no order history. The only session concept is the opaque guest token (Epic 3). Data model per product is: name, description, single price (integer cents), one category, image(s), availability.
- **Epic scope this design covers:** the full purchase path — Epic 1 (PLP), Epic 2 (PDP), Epic 3 (Cart), Epic 4 (Checkout → Order Summary). Surfaces beyond the epic currently in build are designed forward so layout is locked; they light up as their epics land.

## Information Architecture

Flat, linear purchase path — five surfaces, no account area:

- **PLP** (`/`, `/products`) — the storefront home. Header (search) · left facet sidebar (Category) · toolbar (result count, sort) · product grid · Load-more.
- **PDP** (`/products/{id}`) — reached by clicking any card. Breadcrumb (Home / category / product) · two-column gallery + action panel · About section.
- **Cart** (`/cart`) — reached via the header cart icon or after Add-to-cart. Line-item list (left) + sticky order-summary panel (right) with a Checkout CTA.
- **Checkout** (`/checkout`) — sectioned single-page form (shipping → payment → order review) on the left + sticky summary with Place-order CTA on the right. Minimal header.
- **Order Summary** (`/order/confirmation`, transient) — shown immediately after placing an order; confirmation + reference + persisted order snapshot. No order-lookup page (account-free, per FR-15).
- **Header** is persistent on PLP/PDP/Cart: logo → PLP, search field, cart icon with a live item count (Epic 3+). Checkout/Order-Summary use a minimal logo-only header to keep the flow focused.

Closure: every stated need has a surface — browse/search/filter/sort → PLP; inspect → PDP; collect & manage → Cart; pay & place → Checkout; confirm → Order Summary. Unknown product id → PDP not-found; empty cart → Cart empty state. No orphan surfaces.

## Voice and Tone

Plain, concise, non-salesy microcopy (brand voice lives in DESIGN.md → Brand & Style):

- Search placeholder: "Search products…"
- Sort labels: "Price: Low → High", "Price: High → Low".
- Availability: "In stock" / "Out of stock".
- Empty (filtered): "No products match your filters." + a "Clear all filters" action.
- Empty (no search results): "No products found for '{term}'." + reset action.
- PDP not-found: "This product isn't available." + a link back to browsing.
- Error (load failure): "Could not load products." (retry by re-running the search/filter.)
- Cart empty: "Your cart is empty." + "Browse products" action.
- Cart line total helper: "₴X.XX each" under the name.
- Checkout section titles: "Shipping details", "Payment", "Order". Payment note: "Simulated payment — always succeeds. No card data is collected or stored."
- Field validation (inline, next to field): "{Field} is required.", "Enter a valid email."
- Place-order CTA: "Place order". Order-summary confirmation: "Thank you — your order is placed." + "Reference {ref}".

## Component Patterns (behavioral)

Visual specs are in DESIGN.md → Components; here is behavior only.

- **Product card** — entire card is a single link to the PDP (`{components.card}`). Hover lifts. No add-to-cart on the card (add-to-cart is PDP-only, FR-6).
- **Category facet (sidebar)** — multi-select checkboxes (`{components.facet-checkbox}`); selecting/deselecting refetches page 1 immediately (no "apply" button). Multiple categories combine as OR. No result counts per category (we don't aggregate them; a possible later enhancement).
- **Active-filter chips** (`{components.chip-filter}`) — one per active category + the active search term; each individually removable; a Clear-all resets filters but preserves the sort (sort is a persistent control, not a filter).
- **Sort control** — a select in the toolbar; changing it re-fetches page 1 preserving active search + categories (FR-4).
- **Search** — submit-driven (Enter / Search button), not keystroke-live; resets pagination.
- **Load-more** — appends the next page; driven off `nextCursor` (an empty page may still carry a cursor — never treat "0 new items" as "the end").
- **Quantity stepper + Add-to-cart** (PDP action panel) — present in layout; disabled until Epic 3 wires the guest cart. On add, the header cart count increments as feedback (FR-6).
- **Cart line-item row** — thumbnail · name + unit price · quantity stepper · line total · remove. Changing the stepper recomputes line total + summary immediately (FR-9); stepping to **0 removes the line** (same effect as the explicit remove, FR-9/FR-10). Remove is also available as its own control.
- **Order-summary panel** (Cart & Checkout, sticky) — Subtotal (Σ unit×qty) · Shipping (flat constant) · Order Total; primary CTA (Checkout on Cart, Place order on Checkout). No promo-code field, no tax line.
- **Shipping form** (Checkout) — fields: full name, email, address line(s), city, region, postal code, country (select). Required fields validated **inline on blur and on submit** (FR-12); submit is blocked until valid. The form *is* the input — nothing is saved/editable server-side pre-order (anonymous).
- **Payment** (Checkout) — a single non-interactive notice: simulated, always succeeds, no card fields (FR-13, NFR-4). No method selection.
- **Place order** — one action performs simulated payment + writes the immutable Order + clears the cart atomically (FR-14, AD-7), then routes to Order Summary.

## State Patterns

Each surface specifies loading / empty / error / success, plus:

- **PLP loading:** disable the Search/Load-more buttons while a request is in flight; keep prior results visible (no full-page spinner).
- **PLP empty vs. more-pages:** only show the empty state when there are no items **and** no cursor. If items are 0 but a cursor exists (loop-to-fill mid-scan), show Load-more, not the empty state.
- **Out-of-stock product:** still browsable and openable; card and PDP show "Out of stock" in `{colors.stock-out}`; (later) Add-to-cart disabled.
- **PDP not-found (unknown id):** the API returns 404 `{error:{code,message}}`; the UI shows the not-found state (not a raw error) with a path back to the PLP.
- **Stale/invalid cursor (400 invalid_cursor):** the client resets the cursor and refetches page 1 rather than surfacing a raw error (Epic 1 retro action item).
- **Latest-wins:** out-of-order responses are dropped (request-id guard) so a slow earlier query can't clobber newer results.
- **Cart empty:** when the cart has no line items, show the empty state (not an empty summary panel) with a Browse action; the header count reads 0.
- **Cart persistence:** the cart survives reload within the session (keyed by the opaque guest token, FR-8); no login prompt ever appears.
- **Checkout invalid:** required-field errors surface inline; the Place-order button is disabled while the form is invalid — never a silent no-op.
- **Order placed (success-only):** payment always succeeds (no failure path in v1). On place, cart clears and the app routes to Order Summary; re-submitting or navigating back does not place a second order (the cart is already empty).
- **Order Summary is transient:** it reflects the just-placed immutable Order; there is no way to look an order up later (account-free) — this is intentional, communicated on the page.

## Interaction Primitives

- **Selection** — checkbox toggle (facet), immediate effect.
- **Navigation** — card→PDP, breadcrumb→PLP/category, logo→PLP.
- **Submission** — search (Enter/button); Add-to-cart (Epic 3).
- **Progressive disclosure** — Load-more (not infinite scroll, not numbered pages) — matches the opaque-cursor model (no random page access).
- **Feedback** — button disabled-while-loading; (Epic 3) cart-count increment on add.

## Accessibility Floor (behavioral)

Visual contrast is DESIGN.md's job; behavior here:

- Full keyboard operability: facet checkboxes, sort, search, card links, Load-more all tab-reachable and operable by keyboard (NFR-6).
- Visible focus ring (`{colors.focus}`) on every interactive element.
- Semantic markup: cards are `<a>`; the search is a `<form>`; facets are real `<input type=checkbox>` with associated `<label>`; the grid heading structure is meaningful (`<h1>` Products, product names not headings).
- Images carry `alt` = product name. Icon-only controls (chip remove ×) carry an `aria-label`.
- Not a formal WCAG AA audit — baseline only (per NFR-6).

## Key Flows

**Flow 1 — Oksana narrows to the right pair of headphones (PLP → PDP).**
Oksana, shopping on her laptop over lunch, lands on the PLP and sees 240 products in a dark-headered grid. She types "headphones" and hits Search — the grid refreshes to matching items, a "search: headphones" chip appears. She ticks **Electronics** in the left sidebar; the list tightens and an Electronics chip joins the first. She switches Sort to "Price: Low → High." Scanning the red prices and category badges, **the climax:** one card reads "Out of stock" in grey — she skips it and clicks the next, landing on its PDP. Breadcrumb shows Home / Electronics / product; the action panel says "In stock" with the price in red. She reads the About section. (Add-to-cart waits for Epic 3.)

**Flow 2 — A shared link to a delisted product (PDP not-found).**
Someone opens a bookmarked `/products/p-9999` for an item that no longer exists. Instead of a crash or a raw error, **the climax:** the page shows a calm "This product isn't available." with a button back to the catalog. Oksana clicks it and is back on the PLP, filters fresh. No dead end.

**Flow 3 — Oksana buys as a guest, no account (Cart → Checkout → Order Summary).**
From the PDP she picks quantity 1 and clicks Add to cart; the header cart count ticks to 1 — no login, no interruption. She opens the Cart: her headphones sit in a line-item row, and she bumps a second item to qty 2 — the line total and the sticky Order Total (Subtotal + flat shipping, no tax) recompute instantly. She clicks Checkout. On the focused checkout page she fills shipping details; she tabs past the postal code and it flags "Postal code is required." inline — Place order stays disabled until she fixes it. The Payment section is just a note: simulated, always succeeds. She clicks Place order. **The climax:** payment "succeeds," her cart empties, and she lands on the Order Summary — a green ✓, reference `ORD-7F3K-2026`, her exact line items, totals, and shipping address, all frozen. There's no "my orders" page and she doesn't miss one; the confirmation is the record. She clicks Continue shopping.

## Inspiration & Anti-patterns

- **Inspiration (Rozetka):** dark header + centered search, left facet sidebar, result-count + sort toolbar, badge pill over imagery, green primary / card grid; card-wrapped cart line items; sectioned checkout + sticky summary panel with a green confirm CTA.
- **Anti-patterns (deliberately NOT adopted):** star ratings & review counts, seller rows, struck-through discount pricing, bonus-points / installment banners, brand & price-range facets, "other sellers," bought-together, promo/top-seller badges (PLP/PDP); add-on services, promo-code fields, multiple delivery carriers / pickup / map / time-slots, multiple payment methods / cash-on-delivery / commissions, Smart-subscription upsell, saved/editable contact, tax line, and any order-lookup/account area (Cart/Checkout). All require data or concepts outside our model or the account-free scope. Adopting the *look* without the *data* would be dishonest chrome.
