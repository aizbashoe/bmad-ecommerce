"""Checkout HTTP routes (AD-1 HTTP layer, AD-5 contract, AD-7 place order).

POST /checkout places the order (immutable Order + atomic cart clear); GET /orders/{id}
returns the immutable order for the post-checkout confirmation, scoped to the owning guest
token (no browsable order history — account-free, FR-15). No boto3 here.
"""

from fastapi import APIRouter, Depends, Header, Path, Response

from app.core.guest import resolve_guest_id
from app.models.order import Order, PlaceOrderRequest
from app.services.checkout import CheckoutService

router = APIRouter(tags=["checkout"])

_OrderId = Path(min_length=1, max_length=256, description="Order id.")


def get_checkout_service() -> CheckoutService:
    return CheckoutService()


@router.post("/checkout", response_model=Order)
def place_order(
    body: PlaceOrderRequest,
    response: Response,
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
    service: CheckoutService = Depends(get_checkout_service),
) -> Order:
    guest_id = resolve_guest_id(x_guest_token)
    order = service.place_order(guest_id, body.shipping)
    response.headers["X-Guest-Token"] = guest_id
    return order


@router.get("/orders/{order_id}", response_model=Order)
def get_order(
    response: Response,
    order_id: str = _OrderId,
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
    service: CheckoutService = Depends(get_checkout_service),
) -> Order:
    guest_id = resolve_guest_id(x_guest_token)
    order = service.get_order(order_id, guest_id)  # 404 unless the token owns the order
    response.headers["X-Guest-Token"] = guest_id
    return order
