"""Checkout endpoint tests (TestClient, stubbed repos). Story 4.3 ACs."""

from fastapi.testclient import TestClient

from app.api.checkout import get_checkout_service
from app.main import app
from app.models.cart import Cart, CartItem
from app.services.checkout import CheckoutService

client = TestClient(app)

GID = "11111111-1111-1111-1111-111111111111"
SHIP = {
    "fullName": "A B", "address1": "1 St", "address2": "", "city": "Kyiv",
    "region": "Kyiv", "postalCode": "01001", "country": "Ukraine", "email": "a@b.com",
}


class _FakeCarts:
    def __init__(self):
        self.store: dict[str, Cart] = {}

    @property
    def table_name(self) -> str:
        return "Carts"

    def get_cart(self, guest_id):
        return self.store.get(guest_id)


class _FakeOrders:
    def __init__(self, carts: _FakeCarts):
        self.orders = {}
        self._carts = carts

    def place_order_txn(self, order, carts_table):
        self.orders[order.order_id] = order
        self._carts.store.pop(order.guest_id, None)  # simulate the atomic cart delete
        return order

    def get_order(self, order_id):
        return self.orders.get(order_id)


def _install(with_cart: bool):
    carts = _FakeCarts()
    if with_cart:
        carts.store[GID] = Cart(
            guest_id=GID,
            items=[CartItem(product_id="p-1", name="Headphones", unit_price=3000, image_url="https://img/p-1", quantity=2)],
        )
    orders = _FakeOrders(carts)
    app.dependency_overrides[get_checkout_service] = lambda: CheckoutService(carts=carts, orders=orders)
    return carts


def teardown_function():
    app.dependency_overrides.clear()


def test_place_order_ok_snapshot_and_clears_cart():
    carts = _install(with_cart=True)
    resp = client.post("/checkout", json={"shipping": SHIP}, headers={"X-Guest-Token": GID})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reference"].startswith("ORD-")
    assert body["items"][0]["productId"] == "p-1" and body["items"][0]["lineTotal"] == 6000
    assert body["subtotal"] == 6000 and body["shipping"] == 500 and body["orderTotal"] == 6500
    assert body["shippingDetails"]["fullName"] == "A B"
    assert body["createdAt"]
    assert GID not in carts.store  # cart cleared
    oid = body["orderId"]
    got = client.get(f"/orders/{oid}", headers={"X-Guest-Token": GID})
    assert got.status_code == 200 and got.json()["orderId"] == oid  # confirmation fetch


def test_place_order_empty_cart_409():
    _install(with_cart=False)
    resp = client.post("/checkout", json={"shipping": SHIP}, headers={"X-Guest-Token": GID})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "empty_cart"


def test_place_order_invalid_shipping_422():
    _install(with_cart=True)
    bad = {**SHIP, "fullName": "", "email": "nonsense"}  # empty required + bad email
    resp = client.post("/checkout", json={"shipping": bad}, headers={"X-Guest-Token": GID})
    assert resp.status_code == 422  # server-side validation, not client-trusted
    assert resp.json()["error"]["code"] == "validation_error"


def test_place_order_malformed_token_400():
    _install(with_cart=True)
    resp = client.post("/checkout", json={"shipping": SHIP}, headers={"X-Guest-Token": "not-a-uuid"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_guest_token"


def test_get_order_wrong_token_404():
    _install(with_cart=True)
    oid = client.post("/checkout", json={"shipping": SHIP}, headers={"X-Guest-Token": GID}).json()["orderId"]
    other = "22222222-2222-2222-2222-222222222222"
    resp = client.get(f"/orders/{oid}", headers={"X-Guest-Token": other})
    assert resp.status_code == 404  # scoped to the owning guest — no browsable history
