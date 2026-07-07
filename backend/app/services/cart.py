"""CartsService — guest-session resolution + cart lifecycle (AD-1, AD-2, AD-9).

Sits between the cart router and CartsRepository; holds no boto3. Story 3.1: resolve (or
issue) the opaque guest session and return its (empty) cart. Line-item operations arrive
in later Epic 3 stories.
"""

import uuid

from app.core.errors import AppError
from app.models.cart import Cart
from app.repositories.carts import CartsRepository


class CartsService:
    def __init__(self, repository: CartsRepository | None = None):
        self._repo = repository or CartsRepository()

    def resolve_session(self, token: str | None) -> tuple[Cart, str]:
        """Resolve (or issue) the guest session; return (cart, guestId).

        - No token -> mint a new UUID `guestId` (first cart interaction).
        - A provided token must be a valid UUID (the opaque id the API issued); a malformed
          value -> 400 `invalid_guest_token` (never an arbitrary DynamoDB partition key).
        - Then get-or-create the empty cart for that guestId. Stateless: the cart lives only
          in DynamoDB keyed by guestId (AD-9), so any instance can serve any request.
        """
        if not token:
            guest_id = str(uuid.uuid4())
        else:
            try:
                # Validate AND canonicalize: uuid.UUID accepts equivalent forms (uppercase,
                # braces, urn:uuid:, dashless) — normalize so one logical id maps to one cart
                # key (FR-7) and the echoed header value is provably clean.
                guest_id = str(uuid.UUID(token))
            except ValueError as exc:
                raise AppError(
                    "Invalid guest token", code="invalid_guest_token", status_code=400
                ) from exc
        cart = self._repo.get_cart(guest_id) or self._repo.put_empty_cart(guest_id)
        return cart, guest_id
