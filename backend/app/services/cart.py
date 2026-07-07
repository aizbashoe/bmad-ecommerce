"""CartsService — guest session + cart lifecycle (AD-1, AD-2, AD-6, AD-9).

Sits between the cart router and the repositories; holds no boto3. Owns: guest-session
resolution (issue/validate/canonicalize the opaque guestId), get-or-create cart, add/update/
remove line items (snapshotting product fields from ProductsRepository at add time), and the
computed cart view (line totals + subtotal + flat shipping + order total). Money stays integer
cents throughout (AD-6).
"""

from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError
from app.core.guest import resolve_guest_id
from app.models.cart import Cart, CartItem, CartLine, CartView
from app.repositories.carts import CartsRepository
from app.repositories.products import ProductsRepository


class CartsService:
    def __init__(
        self,
        repository: CartsRepository | None = None,
        products: ProductsRepository | None = None,
    ):
        self._repo = repository or CartsRepository()
        self._products = products or ProductsRepository()

    # ---- guest session ----------------------------------------------------

    def resolve_guest_id(self, token: str | None) -> str:
        """Issue/validate/canonicalize the opaque guestId (shared with checkout)."""
        return resolve_guest_id(token)

    def resolve_session(self, token: str | None) -> tuple[Cart, str]:
        """Resolve the session and its (get-or-created) cart. Returns (cart, guestId)."""
        guest_id = self.resolve_guest_id(token)
        return self._get_or_create(guest_id), guest_id

    def _get_or_create(self, guest_id: str) -> Cart:
        return self._repo.get_cart(guest_id) or self._repo.put_empty_cart(guest_id)

    # ---- line-item mutations (Stories 3.2 / 3.4 / 3.5) --------------------

    def add_item(self, guest_id: str, product_id: str, quantity: int) -> Cart:
        if quantity < 1:
            raise AppError("Quantity must be >= 1", code="validation_error", status_code=400)
        product = self._products.get_product(product_id)
        if product is None:
            raise NotFoundError(f"Product '{product_id}' was not found")
        if not product.available:
            # Enforce stock server-side — the disabled PDP button is UX, not the authority.
            raise AppError(
                "Product is out of stock", code="product_unavailable", status_code=409
            )
        cart = self._get_or_create(guest_id)
        for item in cart.items:
            if item.product_id == product_id:
                # Cap the accumulated line quantity too (the request bound only caps the delta).
                if item.quantity + quantity > 999:
                    raise AppError(
                        "Cart line quantity cannot exceed 999",
                        code="quantity_limit",
                        status_code=400,
                    )
                item.quantity += quantity  # increment existing line (no duplicate)
                break
        else:
            cart.items.append(
                CartItem(
                    product_id=product.product_id,
                    name=product.name,
                    unit_price=product.price,  # snapshot at add time (AD-6)
                    image_url=product.image_url,
                    quantity=quantity,
                )
            )
        return self._repo.put_cart(cart)

    def update_item(self, guest_id: str, product_id: str, quantity: int) -> Cart:
        if quantity < 0:
            raise AppError("Quantity must be >= 0", code="validation_error", status_code=400)
        # Read-only lookup: mutating a line requires an existing cart+line (404 otherwise) —
        # never get-or-create here, so an errored mutation leaves no orphan empty cart.
        cart = self._repo.get_cart(guest_id)
        if cart is None or not any(i.product_id == product_id for i in cart.items):
            raise NotFoundError(f"Line item '{product_id}' is not in the cart")
        if quantity == 0:
            self._drop_line(cart, product_id)  # qty 0 removes (FR-9)
        else:
            for item in cart.items:
                if item.product_id == product_id:
                    item.quantity = quantity
                    break
        return self._repo.put_cart(cart)

    def remove_item(self, guest_id: str, product_id: str) -> Cart:
        cart = self._repo.get_cart(guest_id)  # read-only; 404 if the cart/line doesn't exist
        if cart is None or not any(i.product_id == product_id for i in cart.items):
            raise NotFoundError(f"Line item '{product_id}' is not in the cart")
        self._drop_line(cart, product_id)
        return self._repo.put_cart(cart)

    @staticmethod
    def _drop_line(cart: Cart, product_id: str) -> None:
        """Single removal path shared by update-to-0 (3.4) and delete (3.5)."""
        cart.items = [i for i in cart.items if i.product_id != product_id]

    # ---- view (Story 3.3) -------------------------------------------------

    def to_view(self, cart: Cart) -> CartView:
        """Project the stored cart to the API view: line totals + order summary (FR-8, FR-11)."""
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
        # Flat shipping applies only to a non-empty cart; no tax (AD-6, FR-11).
        shipping = get_settings().flat_shipping if lines else 0
        return CartView(
            guest_id=cart.guest_id,
            items=lines,
            subtotal=subtotal,
            shipping=shipping,
            order_total=subtotal + shipping,
        )
