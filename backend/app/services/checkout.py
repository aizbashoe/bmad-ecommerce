"""CheckoutService — place an order from the cart (AD-1, AD-6, AD-7).

Snapshots the cart into an immutable Order (frozen prices, totals, shipping, reference,
timestamp) and places it via the OrdersRepository's atomic transaction (order write + cart
delete). Holds no boto3. Payment is a success-only simulation (FR-13) with nothing to call,
so there is no payment step here — placing the order IS the terminal action.
"""

import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError
from app.models.cart import CartLine
from app.models.order import Order, ShippingDetails
from app.repositories.carts import CartsRepository
from app.repositories.orders import OrdersRepository


class CheckoutService:
    def __init__(
        self,
        carts: CartsRepository | None = None,
        orders: OrdersRepository | None = None,
    ):
        self._carts = carts or CartsRepository()
        self._orders = orders or OrdersRepository()

    def place_order(self, guest_id: str, shipping: ShippingDetails) -> Order:
        cart = self._carts.get_cart(guest_id)
        if cart is None or not cart.items:
            raise AppError("Cart is empty", code="empty_cart", status_code=409)

        lines = [
            CartLine(
                product_id=i.product_id,
                name=i.name,
                unit_price=i.unit_price,
                image_url=i.image_url,
                quantity=i.quantity,
                line_total=i.unit_price * i.quantity,
            )
            for i in cart.items
        ]
        subtotal = sum(line.line_total for line in lines)
        shipping_cost = get_settings().flat_shipping  # cart is non-empty here
        order = Order(
            order_id=str(uuid.uuid4()),
            reference=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            guest_id=guest_id,
            items=lines,
            subtotal=subtotal,
            shipping=shipping_cost,
            order_total=subtotal + shipping_cost,
            shipping_details=shipping,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        # Atomic: write the Order + clear the Cart in one transaction (AD-7).
        self._orders.place_order_txn(order, carts_table=self._carts.table_name)
        return order

    def get_order(self, order_id: str, guest_id: str) -> Order:
        """Fetch an immutable order, scoped to its owning guest (confirmation page; no history)."""
        order = self._orders.get_order(order_id)
        if order is None or order.guest_id != guest_id:
            raise NotFoundError(f"Order '{order_id}' was not found")
        return order
