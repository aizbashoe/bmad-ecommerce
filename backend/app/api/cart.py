"""Cart HTTP routes (AD-1 HTTP layer, AD-2 guest token, AD-5 contract).

No business logic, no boto3 — delegates to CartsService. The guest token is read from the
`X-Guest-Token` request header (absent on first contact) and the resolved/issued token is
echoed in the `X-Guest-Token` response header so the client can store it.
"""

from fastapi import APIRouter, Depends, Header, Response

from app.models.cart import Cart
from app.services.cart import CartsService

router = APIRouter(prefix="/cart", tags=["cart"])


def get_cart_service() -> CartsService:
    # Constructed per request (stateless, AD-9). Injected via Depends so it can be overridden.
    return CartsService()


@router.get("", response_model=Cart)
def get_cart(
    response: Response,
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
    service: CartsService = Depends(get_cart_service),
) -> Cart:
    cart, guest_id = service.resolve_session(x_guest_token)
    # Echo the (possibly newly-issued) guest token so a first-contact client can store it (AD-2).
    response.headers["X-Guest-Token"] = guest_id
    return cart
