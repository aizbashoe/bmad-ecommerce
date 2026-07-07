# Import: Rozetka PDP (user-supplied inspiration reference)

Source: screenshot of a Rozetka product page (Electrolux EHF6241FOK cooktop). Provided by Artem as PDP visual/experience inspiration.

## Observed elements
- **Breadcrumb trail** across the top (Home / category / sub-category / … / this product).
- **Tab strip:** Про товар (About) · Характеристики (Specs) · Відгуки та питання 71/12 (Reviews & Q) · Купують разом (Bought-together) · Цей товар у інших продавців 24 (Other sellers).
- **Left column — image gallery:** large square image, prev/next arrows, corner badges (ТОП ПРОДАЖІВ orange, SMART, free-delivery blue circle, +300 bonus yellow circle).
- **Right column — buy panel:** product title, star rating + review count, product code, seller row (Продавець: ROZETKA), availability "Є в наявності" (in stock, green), price (struck old + red current), large green "Купити" (Buy) button + "Оплатити частинами" (installments) outline button, compare + wishlist(427) icons, bonus banner, bank-installment options row.
- **Below:** "this product from other sellers" cards (price + rating), Rozetka-AI Q prompt.

## Design language cues
Two-column PDP (gallery left / action panel right); green primary Buy; red current price; in-stock in green; badge chips on the image; card sections stacked below.

## Scope reconciliation (our POC data model + epic scope)
Epic 2 / Story 2.1 PDP shows only: name, description, price, image(s), availability, and a not-found state. **Add-to-cart is Epic 3 (story 3.2), not Epic 2.** **Not in our model:** reviews/ratings, seller, installments, bonus, "other sellers", specs table, bought-together. Breadcrumb can map to our single `category`. Adopt the two-column layout + visual language; the action panel is availability + (later) add-to-cart, not the full marketplace panel.
