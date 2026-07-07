# Import: Rozetka Checkout (user-supplied inspiration reference)

Source: two screenshots of `rozetka.com.ua/ua/checkout/`. Provided by Artem as Checkout inspiration.

## Observed elements
- Minimal header (logo only — focused flow).
- Title "Оформлення замовлення" (Checkout).
- **Contact data** block — name, editable ("Змінити").
- **Address** block — location, editable.
- Smart-subscription promo banner.
- **Order** section — seller, line item(s): image, name, unit price × qty, line total; "Редагувати товари" (edit items).
- **Delivery** ("Доставка") — radio list of carriers: store pickup (with address dropdown, "select on map", date/time slot picker), pickup points, courier, Nova Poshta, Meest — each with a price (mostly free).
- **Payment** ("Оплата") — radio list: pay-on-delivery (with commission note), pay-now by card, cashless for legal/individuals, etc.
- **Right summary panel ("Разом"):** promo codes (+Add), "1 item subtotal", "delivery cost" (Free), "To pay" total, pay-on-receipt commission, big green "Замовлення підтверджую" (Confirm order) button, legal-terms links.

## Design language cues
Focused single-page checkout; sectioned left column (contact → address → order → delivery → payment); sticky right summary panel with the total + green confirm CTA; radio-card selection for options.

## Scope reconciliation (our Epic 4 — FR-12/13/14/15 + AD-6/AD-7)
Our checkout is deliberately simple: a **single shipping form** (name, address line(s), city, region, postal code, country, email) with **inline validation** (FR-12); a **simulated payment step that always succeeds** — no real gateway, no card data stored (FR-13, NFR-4); **place order** → immutable Order snapshot + human-readable reference, **cart cleared atomically** (FR-14, AD-7); then the **Order Summary** (FR-15).
Right summary panel maps well: **Subtotal = Σ(unitPrice×qty)**, **flat shipping** constant, **Order Total** (AD-6), + Confirm/Place-order CTA.
**Not in our model/scope:** promo codes, multiple delivery carriers / pickup / map / time-slots (we use a flat shipping placeholder, no carrier choice), multiple payment methods / cash-on-delivery / commissions, Smart subscription, seller, discount pricing, editable saved contact (anonymous — the form IS the input). Adopt the *sectioned-form + sticky-summary layout* and green confirm CTA; keep it data-honest and account-free.
