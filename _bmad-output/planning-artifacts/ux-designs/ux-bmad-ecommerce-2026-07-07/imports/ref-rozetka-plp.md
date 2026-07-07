# Import: Rozetka PLP (user-supplied inspiration reference)

Source: screenshot of `bt.rozetka.com.ua/ua/builtin/c80078/` (Ukrainian marketplace, built-in appliances category). Provided by Artem as PLP visual/experience inspiration.

## Observed elements
- **Header (dark/black bar):** brand logo (green), prominent "Каталог" catalog button, large centered search field with mic icon + green "Знайти" search button; right-side icon cluster — list, notifications, compare (badge), wishlist (badge), cart.
- **Results toolbar:** result count top-left ("Знайдено 3794 товари"), sort dropdown top-right ("За рейтингом" = by rating), grid/list view toggle.
- **Left facet sidebar (collapsible sections w/ chevrons):** Продавець (seller) checkboxes+counts; Бренд (brand) with search box + "popular brands" checkboxes+counts + "показати ще" (show more); Ціна (price range) collapsible.
- **Product grid (~5 cols):** each card has — corner badge ("ТОП ПРОДАЖІВ" orange / "АКЦІЯ" red promo), wishlist heart (top-right), compare icon, large square image, color swatches, 2-line product name, star rating + review count, price (struck-through old + red current), green add-to-cart button, free-delivery chip, bonus-points badge.

## Design language cues
Green = primary action; red = current price; struck-through grey = old price; orange/red pill badges; dense, trust-signal-heavy marketplace layout; card-based grid.

## Scope reconciliation (our POC data model)
Our Product has only: id, name, description, price (single, integer cents), category, imageUrl, availability. **Not in our model:** ratings/reviews, seller, discounts/old price, bonus points, color swatches, brand facet, delivery. Category is our ONLY facet. Adopt the *layout/visual language* selectively; do not invent data we don't have.
