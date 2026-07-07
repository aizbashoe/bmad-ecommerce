# Import: Rozetka Cart (user-supplied inspiration reference)

Source: screenshot of `rozetka.com.ua/ua/cart/`. Provided by Artem as Cart inspiration.

## Observed elements
- Promo strip above header ("07-13.07 sale up to -60%").
- Same dark header (logo, catalog, green search).
- Page title "Кошик" (Cart).
- **Line-item row (in a card):** product thumbnail with a red "-30%" discount badge, product name, seller ("Продавець: Rozetka"), a quantity stepper (− 1 +), price (struck old grey + red current), a 3-dot overflow menu (remove / more).
- **"Додаткові послуги" (Additional services)** — collapsible section, checkbox list of paid add-ons (installation, protection plan, old-appliance removal).
- **Order block (bottom-right, green-bordered panel):** large total "7 500 ₴" + green "Оформити замовлення" (Place order / Checkout) button.

## Design language cues
Card-wrapped line items; blue quantity stepper; red current price; green checkout CTA in a highlighted summary panel; overflow (⋮) for row actions.

## Scope reconciliation (our Epic 3 cart — FR-8/9/10/11 + AD-6/AD-7)
Our cart shows: line items (product image, name, **unit price, quantity, line total**), a quantity stepper (change qty recomputes; qty 0 removes — FR-9), explicit remove (FR-10), **Subtotal = Σ(unitPrice×qty)** and **Order Total = Subtotal + flat shipping (no tax)** — FR-11 / AD-6. Persisted per opaque guest token (FR-7). Checkout button → Epic 4.
**Not in our model/scope:** discount badges/struck prices (no discounts), "additional services" add-ons, seller rows, promo strip. Adopt the *layout* (card line items + highlighted summary panel + green checkout CTA + stepper); keep it data-honest.
