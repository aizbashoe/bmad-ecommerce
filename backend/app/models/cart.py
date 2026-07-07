"""Cart domain + API models (AD-2 guest-keyed, AD-5 camelCase, AD-6 integer cents).

- `CartItem` — a stored line item (a snapshot of the product at add time: unit price, name,
  image — so the cart renders without re-fetching each product).
- `Cart` — the persisted aggregate keyed by `guestId`.
- `CartLine` / `CartView` — the API response: each line with its computed `lineTotal`, plus
  `subtotal`, `shipping` (flat), and `orderTotal` (Story 3.3, FR-11).
- `AddItemRequest` / `UpdateItemRequest` — request bodies (Stories 3.2 / 3.4).
"""

from pydantic import Field

from app.models import CamelModel


class CartItem(CamelModel):
    product_id: str
    name: str
    unit_price: int  # integer minor units (cents), AD-6 — snapshot at add time
    image_url: str
    quantity: int


class Cart(CamelModel):
    guest_id: str
    items: list[CartItem] = Field(default_factory=list)


class CartLine(CamelModel):
    product_id: str
    name: str
    unit_price: int
    image_url: str
    quantity: int
    line_total: int  # unit_price * quantity (cents)


class CartView(CamelModel):
    """The cart as returned to clients: lines with totals + order summary (FR-8, FR-11)."""

    guest_id: str
    items: list[CartLine] = Field(default_factory=list)
    subtotal: int  # Σ line_total (cents)
    shipping: int  # flat placeholder (cents); 0 when the cart is empty
    order_total: int  # subtotal + shipping (no tax)


class AddItemRequest(CamelModel):
    product_id: str
    # Upper bound keeps quantity*price well under DynamoDB's 38-digit Number limit (a huge
    # value would otherwise be a 500 on write); a clean 422 instead.
    quantity: int = Field(ge=1, le=999, description="Units to add (1-999).")


class UpdateItemRequest(CamelModel):
    quantity: int = Field(ge=0, le=999, description="New quantity (0-999); 0 removes the line.")
