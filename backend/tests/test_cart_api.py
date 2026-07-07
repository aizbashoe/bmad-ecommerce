"""Cart endpoint tests (TestClient, stubbed repos). Stories 3.1-3.5 ACs."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.cart import get_cart_service
from app.main import app
from app.models.cart import Cart
from app.models.product import Product
from app.services.cart import CartsService

client = TestClient(app)


class _FakeCartsRepo:
    def __init__(self):
        self.store: dict[str, Cart] = {}

    def get_cart(self, guest_id: str):
        return self.store.get(guest_id)

    def put_cart(self, cart: Cart):
        self.store[cart.guest_id] = cart
        return cart

    def put_empty_cart(self, guest_id: str):
        return self.put_cart(Cart(guest_id=guest_id, items=[]))


class _FakeProductsRepo:
    def __init__(self):
        self.products = {
            "p-1": Product(
                product_id="p-1", name="Headphones", description="d",
                price=3000, category="electronics", image_url="https://img/p-1", available=True,
            ),
            "p-2": Product(
                product_id="p-2", name="Sweater", description="d",
                price=1250, category="apparel", image_url="https://img/p-2", available=True,
            ),
            "p-out": Product(
                product_id="p-out", name="Sold Out", description="d",
                price=500, category="home", image_url="https://img/p-out", available=False,
            ),
        }

    def get_product(self, product_id: str):
        return self.products.get(product_id)


@pytest.fixture(autouse=True)
def stub_service():
    carts, products = _FakeCartsRepo(), _FakeProductsRepo()
    app.dependency_overrides[get_cart_service] = lambda: CartsService(
        repository=carts, products=products
    )
    yield
    app.dependency_overrides.clear()


def _new_session() -> str:
    """Establish a session and return its guest token."""
    return client.get("/cart").headers["X-Guest-Token"]


# --- Story 3.1: session ---

def test_get_cart_issues_token_when_absent():
    resp = client.get("/cart")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    gid = body["guestId"]
    uuid.UUID(gid)
    assert resp.headers.get("X-Guest-Token") == gid


def test_get_cart_malformed_token_400_envelope():
    resp = client.get("/cart", headers={"X-Guest-Token": "not-a-uuid"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "invalid_guest_token"
    assert body["error"]["message"]


def test_get_cart_canonicalizes_equivalent_uuid_forms():
    canonical = client.get("/cart").json()["guestId"]
    upper = client.get("/cart", headers={"X-Guest-Token": canonical.upper()})
    dashless = client.get("/cart", headers={"X-Guest-Token": canonical.replace("-", "")})
    assert upper.json()["guestId"] == canonical
    assert dashless.json()["guestId"] == canonical


# --- Story 3.2: add to cart ---

def test_add_item_creates_line_with_snapshot_and_totals():
    gid = _new_session()
    resp = client.post("/cart/items", json={"productId": "p-1", "quantity": 2},
                       headers={"X-Guest-Token": gid})
    assert resp.status_code == 200
    body = resp.json()
    line = body["items"][0]
    assert line["productId"] == "p-1"
    assert line["unitPrice"] == 3000 and line["quantity"] == 2  # snapshot + qty
    assert line["lineTotal"] == 6000
    assert body["subtotal"] == 6000
    assert body["shipping"] == 500  # flat shipping on a non-empty cart
    assert body["orderTotal"] == 6500


def test_add_same_product_increments_quantity():
    gid = _new_session()
    client.post("/cart/items", json={"productId": "p-1", "quantity": 1}, headers={"X-Guest-Token": gid})
    body = client.post("/cart/items", json={"productId": "p-1", "quantity": 2},
                       headers={"X-Guest-Token": gid}).json()
    assert len(body["items"]) == 1  # no duplicate line
    assert body["items"][0]["quantity"] == 3


def test_add_unknown_product_404():
    gid = _new_session()
    resp = client.post("/cart/items", json={"productId": "nope", "quantity": 1},
                       headers={"X-Guest-Token": gid})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_add_quantity_zero_422():
    gid = _new_session()
    resp = client.post("/cart/items", json={"productId": "p-1", "quantity": 0},
                       headers={"X-Guest-Token": gid})
    assert resp.status_code == 422  # Field(ge=1) rejects before the service
    assert resp.json()["error"]["code"] == "validation_error"


def test_add_quantity_too_large_422():
    gid = _new_session()
    resp = client.post("/cart/items", json={"productId": "p-1", "quantity": 100000},
                       headers={"X-Guest-Token": gid})
    assert resp.status_code == 422  # Field(le=999) — never a 500 from DynamoDB's number cap


def test_add_increment_over_999_rejected_400():
    gid = _new_session()
    client.post("/cart/items", json={"productId": "p-1", "quantity": 999}, headers={"X-Guest-Token": gid})
    resp = client.post("/cart/items", json={"productId": "p-1", "quantity": 1}, headers={"X-Guest-Token": gid})
    assert resp.status_code == 400  # accumulated line quantity capped at 999
    assert resp.json()["error"]["code"] == "quantity_limit"


def test_add_out_of_stock_product_409():
    gid = _new_session()
    resp = client.post("/cart/items", json={"productId": "p-out", "quantity": 1},
                       headers={"X-Guest-Token": gid})
    assert resp.status_code == 409  # enforced server-side, not just the disabled PDP button
    assert resp.json()["error"]["code"] == "product_unavailable"


def test_cart_persists_across_requests_same_token():
    """FR-7/FR-8: a second GET with the same token returns the previously-added item."""
    gid = _new_session()
    client.post("/cart/items", json={"productId": "p-1", "quantity": 2}, headers={"X-Guest-Token": gid})
    again = client.get("/cart", headers={"X-Guest-Token": gid}).json()
    assert again["guestId"] == gid
    assert again["items"][0]["productId"] == "p-1" and again["items"][0]["quantity"] == 2


# --- Story 3.3: view with totals ---

def test_empty_cart_has_zero_totals_and_no_shipping():
    body = client.get("/cart").json()
    assert body["items"] == []
    assert body["subtotal"] == 0 and body["shipping"] == 0 and body["orderTotal"] == 0


def test_totals_sum_multiple_lines():
    gid = _new_session()
    client.post("/cart/items", json={"productId": "p-1", "quantity": 1}, headers={"X-Guest-Token": gid})
    body = client.post("/cart/items", json={"productId": "p-2", "quantity": 2},
                       headers={"X-Guest-Token": gid}).json()
    assert body["subtotal"] == 3000 + 2 * 1250
    assert body["orderTotal"] == body["subtotal"] + 500


# --- Story 3.4: update quantity ---

def test_update_item_recomputes():
    gid = _new_session()
    client.post("/cart/items", json={"productId": "p-1", "quantity": 1}, headers={"X-Guest-Token": gid})
    body = client.patch("/cart/items/p-1", json={"quantity": 4}, headers={"X-Guest-Token": gid}).json()
    assert body["items"][0]["quantity"] == 4
    assert body["subtotal"] == 12000


def test_update_quantity_zero_removes_line():
    gid = _new_session()
    client.post("/cart/items", json={"productId": "p-1", "quantity": 1}, headers={"X-Guest-Token": gid})
    body = client.patch("/cart/items/p-1", json={"quantity": 0}, headers={"X-Guest-Token": gid}).json()
    assert body["items"] == [] and body["subtotal"] == 0


def test_update_missing_line_404():
    gid = _new_session()
    resp = client.patch("/cart/items/p-1", json={"quantity": 2}, headers={"X-Guest-Token": gid})
    assert resp.status_code == 404


def test_update_negative_quantity_422():
    gid = _new_session()
    resp = client.patch("/cart/items/p-1", json={"quantity": -1}, headers={"X-Guest-Token": gid})
    assert resp.status_code == 422


# --- Story 3.5: remove ---

def test_remove_item():
    gid = _new_session()
    client.post("/cart/items", json={"productId": "p-1", "quantity": 1}, headers={"X-Guest-Token": gid})
    body = client.delete("/cart/items/p-1", headers={"X-Guest-Token": gid}).json()
    assert body["items"] == []


def test_remove_missing_line_404():
    gid = _new_session()
    resp = client.delete("/cart/items/p-1", headers={"X-Guest-Token": gid})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"
