"""Cart HTTP routes (AD-1 HTTP layer, AD-2 guest token, AD-5 contract).

No business logic, no boto3 — delegates to CartsService. The guest token is read from the
`X-Guest-Token` request header (absent on first contact) and the resolved/issued token is
echoed in the `X-Guest-Token` response header so the client can store it. Every response is
the computed cart view (lines + totals) so the SPA can re-render after any mutation.
"""

from fastapi import APIRouter, Depends, Header, Path, Response

from app.models.cart import AddItemRequest, CartView, UpdateItemRequest
from app.services.cart import CartsService

router = APIRouter(prefix="/cart", tags=["cart"])

# Bounded well under DynamoDB's key limit so an oversized id is a clean 422, not a 500 (as 2.1).
_ProductId = Path(min_length=1, max_length=256, description="Product id of the line item.")


def get_cart_service() -> CartsService:
    # Constructed per request (stateless, AD-9). Injected via Depends so it can be overridden.
    return CartsService()


def _echo(response: Response, guest_id: str) -> None:
    response.headers["X-Guest-Token"] = guest_id


@router.get("", response_model=CartView)
def get_cart(
    response: Response,
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
    service: CartsService = Depends(get_cart_service),
) -> CartView:
    cart, guest_id = service.resolve_session(x_guest_token)
    _echo(response, guest_id)
    return service.to_view(cart)


@router.post("/items", response_model=CartView)
def add_item(
    body: AddItemRequest,
    response: Response,
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
    service: CartsService = Depends(get_cart_service),
) -> CartView:
    guest_id = service.resolve_guest_id(x_guest_token)
    cart = service.add_item(guest_id, body.product_id, body.quantity)
    _echo(response, guest_id)
    return service.to_view(cart)


@router.patch("/items/{product_id}", response_model=CartView)
def update_item(
    body: UpdateItemRequest,
    response: Response,
    product_id: str = _ProductId,
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
    service: CartsService = Depends(get_cart_service),
) -> CartView:
    guest_id = service.resolve_guest_id(x_guest_token)
    cart = service.update_item(guest_id, product_id, body.quantity)
    _echo(response, guest_id)
    return service.to_view(cart)


@router.delete("/items/{product_id}", response_model=CartView)
def remove_item(
    response: Response,
    product_id: str = _ProductId,
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
    service: CartsService = Depends(get_cart_service),
) -> CartView:
    guest_id = service.resolve_guest_id(x_guest_token)
    cart = service.remove_item(guest_id, product_id)
    _echo(response, guest_id)
    return service.to_view(cart)
