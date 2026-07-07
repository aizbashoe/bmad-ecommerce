"""GET /cart endpoint tests (TestClient, stubbed repo). Story 3.1 ACs 1-3."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.cart import get_cart_service
from app.main import app
from app.models.cart import Cart
from app.services.cart import CartsService

client = TestClient(app)


class _FakeRepo:
    """In-memory carts keyed by guestId — exercises the real CartsService get-or-create."""

    def __init__(self):
        self.store: dict[str, Cart] = {}

    def get_cart(self, guest_id: str):
        return self.store.get(guest_id)

    def put_empty_cart(self, guest_id: str):
        cart = Cart(guest_id=guest_id, items=[])
        self.store[guest_id] = cart
        return cart


@pytest.fixture(autouse=True)
def stub_service():
    repo = _FakeRepo()
    app.dependency_overrides[get_cart_service] = lambda: CartsService(repository=repo)
    yield
    app.dependency_overrides.clear()


def test_get_cart_issues_token_when_absent():
    resp = client.get("/cart")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    gid = body["guestId"]
    uuid.UUID(gid)  # issued id is a valid UUID
    assert resp.headers.get("X-Guest-Token") == gid  # echoed for the client to store


def test_get_cart_resolves_same_cart_for_same_token():
    gid = client.get("/cart").json()["guestId"]
    again = client.get("/cart", headers={"X-Guest-Token": gid})
    assert again.status_code == 200
    assert again.json()["guestId"] == gid  # FR-7: same token -> same cart
    assert again.headers.get("X-Guest-Token") == gid


def test_get_cart_malformed_token_400_envelope():
    resp = client.get("/cart", headers={"X-Guest-Token": "not-a-uuid"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "invalid_guest_token"
    assert body["error"]["message"]  # full {code,message} envelope


def test_get_cart_first_contact_with_valid_token_creates_and_persists():
    """A brand-new valid UUID in the header (not previously issued) resolves + creates a cart."""
    gid = "9f8b7a6c-1111-4222-8333-444455556666"
    resp = client.get("/cart", headers={"X-Guest-Token": gid})
    assert resp.status_code == 200
    assert resp.json()["guestId"] == gid
    # ...and it now persists: a second call returns the same cart.
    assert client.get("/cart", headers={"X-Guest-Token": gid}).json()["guestId"] == gid


def test_get_cart_canonicalizes_equivalent_uuid_forms():
    """Uppercase / dashless forms of the same UUID resolve to the SAME canonical guestId (FR-7)."""
    canonical = client.get("/cart").json()["guestId"]  # lowercase, dashed
    upper = client.get("/cart", headers={"X-Guest-Token": canonical.upper()})
    dashless = client.get("/cart", headers={"X-Guest-Token": canonical.replace("-", "")})
    assert upper.json()["guestId"] == canonical
    assert dashless.json()["guestId"] == canonical
