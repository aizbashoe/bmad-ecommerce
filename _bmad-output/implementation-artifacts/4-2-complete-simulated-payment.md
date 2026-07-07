---
baseline_commit: 2742fb054d8e24a2b3d2e8dd7cbe81ef0068dfea
---

# Story 4.2: Complete a simulated payment

Status: done

## Story

As an anonymous shopper,
I want to complete a payment step,
so that I can finish my purchase.

## Acceptance Criteria

1. **Given** valid shipping details, **When** I proceed through the payment step, **Then** the payment is **simulated and always succeeds** — satisfies FR-13.
2. **Given** the payment step, **Then** **no real payment gateway is called and no card data is collected or stored** (data minimization, NFR-4) — there are no card-number/CVV inputs.
3. **Given** a successful (simulated) payment, **Then** the flow proceeds to order placement (Story 4.3).

## Tasks / Subtasks

- [x] **Task 1 — Payment section on the checkout page (AC: 1, 2)** — add a "Payment" section to `CheckoutPage` matching `checkout-mock.html`: a single info notice ("Simulated payment — always succeeds. No real gateway is called and no card data is collected or stored."). No card fields, no method selection.
- [x] **Task 2 — Proceed on success (AC: 3)** — the single primary action (the "Place order" button) represents "pay + place": since payment always succeeds and collects nothing, there is no separate pay step to fail. The button (enabled once shipping is valid) proceeds directly to placement (wired in 4.3). Document that payment is a no-op success inline in the flow.

## Dev Notes

- **Payment is not a backend concern.** Success-only, no gateway, no card data (FR-13, NFR-4) → there is nothing to POST for "payment". It's a UI notice + the single Place-order action that (in 4.3) performs placement. Do not add a payment endpoint, a payment model, or any card field.
- **Merges into 4.1's CheckoutPage.** This story adds the Payment info-notice section (DESIGN.md `notice-info`) between Shipping details and the summary; the actual "proceed" is the Place-order button that 4.3 wires to `POST /checkout`.
- **Scope:** the payment *notice* + confirming the flow proceeds on the single success action. Order creation + cart clear is 4.3.
- [Source: epics.md Epic 4 / 4.2; FR-13, NFR-4; EXPERIENCE.md (Payment: "Simulated payment — always succeeds. No card data is collected or stored."); mockups/checkout-mock.html]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Completion Notes List

- Added the Payment info-notice section to `CheckoutPage` ("Simulated payment — always succeeds. No real gateway is called and no card data is collected or stored."). No card fields, no method selection, no payment endpoint/model (FR-13, NFR-4). The single Place-order action performs pay+place (4.3). Built cohesively with 4.1/4.3/4.4.
- **File List + consolidated Review Findings: see [4-3-place-order.md](4-3-place-order.md).** Story-4.2-specific: the Payment section in `CheckoutPage.tsx`.

### Review Findings

Reviewed with Epic 4 (Approve-with-patches). AC1-3 met: payment is a success-only UI notice with no gateway/card data; the flow proceeds via the single Place-order action. Full findings: [4-3 story → Review Findings](4-3-place-order.md).

### File List

See the consolidated File List in [4-3-place-order.md](4-3-place-order.md). Story-4.2-specific: Payment notice section in `frontend/src/pages/CheckoutPage.tsx`.
