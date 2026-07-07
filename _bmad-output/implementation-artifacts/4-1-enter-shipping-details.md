---
baseline_commit: 2742fb054d8e24a2b3d2e8dd7cbe81ef0068dfea
---

# Story 4.1: Enter shipping details

Status: done

## Story

As an anonymous shopper,
I want to enter where my order should ship,
so that my purchase can be delivered.

## Acceptance Criteria

1. **Given** items in my cart, **When** I click Checkout on the cart page, **Then** I navigate to `/checkout` (the currently-disabled cart Checkout button is now wired to that route).
2. **Given** the checkout page, **When** it renders, **Then** it shows a **shipping form** (full name, address line 1, address line 2 [optional], city, region, postal code, country, email) alongside a **sticky order-summary panel** (Subtotal / Shipping / Order total from `GET /cart`), matching `checkout-mock.html` + DESIGN.md tokens — satisfies FR-12 (form).
3. **Given** I submit or leave required fields, **Then** required fields (all except address line 2) are **validated inline** — an error message appears next to each invalid field, and email is format-checked — and the primary button is blocked/does nothing until the form is valid (FR-12).
4. **Given** AD-7, **Then** **nothing is persisted** — the form is client state only; no API call is made in this story (payment is 4.2, order placement is 4.3).
5. **Given** an empty cart, **When** I open `/checkout`, **Then** I see a "Your cart is empty" message with a link back to browse (can't check out an empty cart), not a broken form.
6. **Given** the primary **Place order** button, **Then** it is present per the mock but **not yet wired** to place an order (it advances to payment/placement in 4.2/4.3) — render it disabled-until-valid with a note, or gate it so clicking does nothing beyond validation this story.

## Tasks / Subtasks

- [x] **Task 1 — Route + wire Checkout (AC: 1, 5)** — add `/checkout` route in `App.tsx` → new `CheckoutPage`; change the cart page Checkout button from disabled to a `<Link to="/checkout">` (or navigate). On `/checkout` with an empty cart, show the empty message + Browse link.
- [x] **Task 2 — CheckoutPage layout + summary (AC: 2)** — `frontend/src/pages/CheckoutPage.tsx`: two-column (sectioned form left, sticky summary right); fetch the cart via `getCart` for the summary (Subtotal/Shipping/Order total); tokens + `checkout-mock.html` layout. Minimal logo-only header is already the shared `StoreHeader` (leave as-is).
- [x] **Task 3 — Shipping form + inline validation (AC: 3, 4)** — controlled form state (no persistence); required-field validation on blur + on submit; email regex; error text next to each field (DESIGN.md `input-error`); `formErrors` derived; a `isValid` gate. Fields: fullName, address1, address2 (optional), city, region, postalCode, country (select), email.
- [x] **Task 4 — Place-order button placeholder (AC: 6)** — render the primary button; disabled while the form is invalid; on click (valid) it does NOT call any API this story (payment 4.2 / place 4.3) — a no-op or a note "Payment & placement arrive in Epic 4 stories 4.2-4.3". Do not build payment or `/checkout` API.
- [x] **Task 5 — Verify (AC: all)** — `tsc -b && vite build` clean; live: cart → Checkout → /checkout renders the form + summary; invalid fields show inline errors and block the button; empty cart → empty message. No network call on submit.

## Dev Notes

- **Frontend-only, no persistence (AD-7).** This story stores nothing server-side and calls no checkout API — the form is React state. Order placement (which snapshots the Order and clears the cart atomically) is Story 4.3. Payment (simulated) is 4.2. Keep those out.
- **Reuse, don't rebuild:** `getCart` already returns `subtotal`/`shipping`/`orderTotal` (Story 3.3) — the summary panel just renders them (mirror `CartPage`'s summary). `formatPrice` stays `$`. Tokens from `theme/tokens.ts`; the shared `StoreHeader` already wraps routes (don't add a header).
- **Validation:** required = fullName, address1, city, region, postalCode, country, email (address2 optional). Email: a simple format check (e.g. `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`). Show the error next to the field on blur and on attempted submit; keep the primary button gated on overall validity. Follow EXPERIENCE.md → Voice and Tone microcopy ("{Field} is required.", "Enter a valid email.").
- **Empty-cart guard (AC-5):** the checkout page fetches the cart; if `items.length === 0`, render the empty state instead of the form (you can't check out nothing). Also keep the cart-page Checkout button meaningful (it only shows when the cart has items anyway).
- **Layout:** left column = sectioned card(s): "Shipping details" (the form). The mock also shows Payment + Order sections and a right "Summary" panel with a green confirm CTA — build the shipping form + the summary panel now; the Payment section and wiring the CTA to place an order are 4.2/4.3 (render the CTA present-but-gated).
- **Scope fences:** no Orders table, no OrdersRepository, no `/checkout` backend, no payment, no cart clearing. Those are 4.2 (payment) and 4.3 (place order — atomic TransactWriteItems per the Epic 3 retro).
- [Source: epics.md Epic 4 / 4.1; ARCHITECTURE-SPINE AD-7 (nothing persisted until placed), AD-5; EXPERIENCE.md (checkout IA, Voice & Tone, a11y floor); mockups/checkout-mock.html]

### Project Structure Notes

- New: `frontend/src/pages/CheckoutPage.tsx`. Edit: `frontend/src/App.tsx` (route), `frontend/src/pages/CartPage.tsx` (wire Checkout button). No backend changes. No new deps.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Debug Log References

- `npm run build` (`tsc -b && vite build`) → clean. Live (docker): `/checkout` and `/cart` → 200; backend `/cart` unchanged → 200.

### Completion Notes List

- Frontend-only (AD-7): `CheckoutPage` at `/checkout` — two-column sectioned shipping form + sticky order-summary (reuses `getCart` totals). Inline validation (required fields + email regex) shows errors on blur/submit and gates the Place-order button. **No API call / no persistence** on submit (payment 4.2, place-order 4.3). Empty-cart guard renders the empty state. The cart Checkout button is now a `<Link to="/checkout">`.
- Scope fences held: no Orders table, no `/checkout` backend, no payment, no cart clearing. `formatPrice` still `$`; shared `StoreHeader` reused (no extra header).

### File List

- `frontend/src/pages/CheckoutPage.tsx` (A) — checkout shipping form + summary.
- `frontend/src/App.tsx` (M) — `/checkout` route.
- `frontend/src/pages/CartPage.tsx` (M) — Checkout button → `<Link to="/checkout">`.

### Change Log

- 2026-07-07: Implemented story 4.1 (checkout shipping details) — CheckoutPage form + inline validation + order summary; wired the cart Checkout button; no persistence (AD-7). Status → review.
