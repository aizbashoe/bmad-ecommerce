---
name: bmad-ecommerce storefront
status: final
updated: 2026-07-07
sources:
  - _bmad-output/planning-artifacts/prds/prd-bmad-ecommerce-2026-07-06/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-bmad-ecommerce-2026-07-06/ARCHITECTURE-SPINE.md
  - imports/ref-rozetka-plp.md
  - imports/ref-rozetka-pdp.md
  - imports/ref-rozetka-cart.md
  - imports/ref-rozetka-checkout.md
colors:
  brand:
    green: "#159f4a"        # primary action (buttons, active accents, links)
    green-dark: "#0f7d3a"   # hover/pressed
  price: "#d81e2c"          # price accent (Rozetka cue) — NOT a sale color here
  ink: "#17181a"            # primary text
  muted: "#6b7280"          # secondary text, counts, breadcrumb
  line: "#e5e7eb"           # borders, dividers
  bg: "#f4f5f7"             # page background
  surface: "#ffffff"        # cards, panels, sidebar
  header: "#1f1f1f"         # top navigation bar
  badge: "rgba(17,24,39,0.82)"  # category pill over imagery
  stock-in: "#0f7d3a"       # "In stock"
  stock-out: "#9ca3af"      # "Out of stock" (muted grey)
  focus: "#159f4a"          # focus-ring color
typography:
  family: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
  scale:
    h1: "22px/1.25 700"     # PDP product title
    h2: "17px/1.3 700"      # section headings ("About this product")
    h3: "15px/1.3 600"      # facet group title
    body: "14px/1.5 400"
    price-lg: "30px 800"    # PDP price
    price-sm: "18px 800"    # PLP card price
    meta: "13px/1.4 400"    # breadcrumb, counts, category line
    badge: "11px 700"       # uppercase, letter-spacing .03em
rounded:
  sm: "8px"                 # buttons, inputs, chips
  md: "10px"                # cards, panels, sidebar
  pill: "999px"             # badges, filter chips
spacing:
  base: "4px"
  scale: [4, 8, 12, 16, 20, 24, 28]
  gutter: "16px"            # grid gap
  page-max: "1240px"        # PLP shell max width (1180px on PDP)
components:
  button-primary: { bg: brand.green, fg: "#ffffff", radius: rounded.sm, height: "48px", weight: 700, hover: brand.green-dark, disabled: "#cbd5e1" }
  card: { bg: surface, border: line, radius: rounded.md, pad: "12px", hover-shadow: "0 6px 18px rgba(0,0,0,.08)" }
  badge-category: { bg: badge, fg: "#ffffff", radius: rounded.pill, size: typography.scale.badge, transform: uppercase }
  chip-filter: { bg: "#eef2ff", border: "#c7d2fe", radius: rounded.pill, pad: "4px 10px" }
  input: { border: line, radius: rounded.sm, pad: "11px 14px" }
  input-error: { border: "#b91c1c", message-color: "#b91c1c", message-size: "12px" }
  facet-checkbox: { accent: brand.green, size: "16px" }
  qty-stepper: { border: line, radius: rounded.sm, btn-bg: "#f3f4f6", height: "40px" }
  cart-row: { grid: "thumb 72px / name / qty / line-total / remove", divider: line, thumb: "72px" }
  summary-panel: { bg: surface, border: line, radius: rounded.md, sticky: true, total-weight: 800 }
  form-field: { label-size: typography.scale.meta, gap: "5px", two-up: "1fr 1fr" }
  notice-info: { bg: "#f0faf3", border: brand.green, radius: rounded.sm, pad: "14px 16px" }
---

# bmad-ecommerce — Visual Design

Rozetka-inspired storefront identity for an anonymous, account-free POC. Marketplace *look and layout* — dark header, green primary action, badge pills, card grid — but **honest to a lean data model**: single price, one category, an image, availability. No ratings, sellers, discounts, bonus points, or brand — we do not render chrome for data we do not store.

## Brand & Style

Clean, high-contrast, utilitarian retail. Voice is plain and direct (see EXPERIENCE.md → Voice and Tone). The green does the work of "action/positive"; the dark header anchors the brand; everything else stays neutral so product imagery leads. Desktop web only for this POC.

**Wordmark:** the store name is **BMAD POC Store**, shown in the header with "POC" in `{colors.brand.green}` (`BMAD `**`POC`**` Store`). Use this exact text everywhere the store is named.

## Colors

- **Primary action** — `{colors.brand.green}` (hover `{colors.brand.green-dark}`): buy button, search button, active facet accents, links.
- **Price** — `{colors.price}`: the price accent, echoing Rozetka's signature red. Here it is *not* a discount signal — see Do's & Don'ts.
- **Text** — `{colors.ink}` primary, `{colors.muted}` secondary (counts, breadcrumb, category line).
- **Surfaces** — `{colors.bg}` page, `{colors.surface}` cards/panels/sidebar, `{colors.line}` borders.
- **Header** — `{colors.header}` dark bar with white content.
- **Availability** — `{colors.stock-in}` in-stock, `{colors.stock-out}` out-of-stock.

## Typography

System font stack (`{typography.family}`) — no web-font dependency (respects the POC's self-contained, offline-friendly bar). Sizes per `{typography.scale}`; price uses the heaviest weight for scannability (`{typography.scale.price-lg}` on PDP, `{typography.scale.price-sm}` on PLP cards).

## Layout & Spacing

- 4px base grid; gutters `{spacing.gutter}`.
- PLP shell max `{spacing.page-max}`; **two-column** `250px` facet sidebar + fluid product grid (4 cards/row at shell width).
- PDP shell max `1180px`; **two-column** `1.15fr` gallery + `1fr` action panel, with an "About this product" section below.
- Cart & Checkout shell max `1120px`; **content + sticky summary** — `1fr` line-items/form column + `320px` sticky order-summary panel. Order Summary is single-column, max `760px`.

## Elevation & Depth

Flat by default. Cards lift on hover only (`{components.card.hover-shadow}`). No ambient shadows on static surfaces — borders (`{colors.line}`) carry separation.

## Shapes

Rounded corners throughout: `{rounded.sm}` controls, `{rounded.md}` cards/panels, `{rounded.pill}` badges & filter chips. Square (1:1) product imagery.

## Components

- **Primary button** `{components.button-primary}` — green, full-height 48px; disabled state greyed (used for Add-to-cart before Epic 3 wiring).
- **Product card** `{components.card}` — image (1:1) with a category badge overlay, name (2-line clamp), price, availability. Entire card links to the PDP.
- **Category badge** `{components.badge-category}` — dark uppercase pill, top-left over the image; truncates with ellipsis.
- **Filter chip** `{components.chip-filter}` — active category filters, individually removable, with a Clear-all.
- **Facet checkbox** `{components.facet-checkbox}` — green accent; left-sidebar category list.
- **Input / search** `{components.input}` — paired with a green search button (segmented control in the header). Invalid form fields use `{components.input-error}` (red border + red helper message below).
- **Quantity stepper** `{components.qty-stepper}` — −/+ buttons flanking a numeric input; used on PDP and cart rows.
- **Cart line-item row** `{components.cart-row}` — thumbnail · name+unit price · stepper · line total (price color) · remove; divider between rows.
- **Order-summary panel** `{components.summary-panel}` — sticky right column; Subtotal / Shipping / Order-Total lines + a full-width primary CTA. Total row is the heaviest weight; no tax or promo line.
- **Form field** `{components.form-field}` — stacked label + control; two-up rows on wide fields (name/email, city/region, postal/country).
- **Info notice** `{components.notice-info}` — green-tinted callout; used for the simulated-payment note and the order-placed confirmation banner.

## Do's and Don'ts

- ✅ Use green **only** for actions/positive-affordances and the in-stock state.
- ✅ Keep the category badge the single overlay on imagery.
- ❌ **No struck-through "old price."** We have no discounts; the red price is a brand accent, never implies a markdown. If red-as-price tests as misleading, fall back to `{colors.ink}` for price (documented fallback).
- ❌ No star ratings, review counts, seller rows, bonus/installment banners, or brand facet — we don't store that data. Don't fake it.
- ❌ No "ТОП ПРОДАЖІВ"/promo badges — we have no such attribute.
- ❌ No promo-code field, add-on services, carrier/delivery-slot pickers, multiple payment methods, or tax line in Cart/Checkout — shipping is a single flat constant and payment is a success-only simulation.
- ✅ Keep the green info-notice for the simulated-payment note and the order-placed confirmation — green here means "positive/complete," consistent with its action/positive role.
