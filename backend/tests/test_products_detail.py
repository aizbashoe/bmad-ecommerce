"""GET /products/{id} (PDP) endpoint tests. Covers AC-1, AC-2, AC-6 of story 2.1."""

import pytest
from fastapi.testclient import TestClient

from app.api.products import get_catalog_service
from app.main import app
from app.models.product import Product
from app.services.catalog import CatalogService

client = TestClient(app)


class _FakeRepo:
    """Minimal repo double: knows one product (p-1); everything else is missing."""

    def get_product(self, product_id: str):
        if product_id == "p-1":
            return Product(
                product_id="p-1",
                name="Wireless Headphones",
                description="Over-ear ANC headphones with 30h battery.",
                price=349900,
                category="electronics",
                image_url="https://img/p-1",
                available=True,
            )
        return None

    # Present so /products/categories resolves for the shadowing regression test.
    def list_categories(self):
        return ["books", "electronics", "home"]


@pytest.fixture(autouse=True)
def stub_service():
    app.dependency_overrides[get_catalog_service] = lambda: CatalogService(repository=_FakeRepo())
    yield
    app.dependency_overrides.clear()


def test_get_product_ok_shape():
    resp = client.get("/products/p-1")
    assert resp.status_code == 200
    body = resp.json()
    # camelCase, includes description (distinguishes detail from the listing summary), AD-5/FR-5.
    assert set(body) == {"productId", "name", "description", "price", "imageUrl", "category", "available"}
    assert body["productId"] == "p-1"
    assert body["description"].startswith("Over-ear")
    assert isinstance(body["price"], int)  # cents, AD-6


def test_get_unknown_product_404_envelope():
    resp = client.get("/products/does-not-exist")
    assert resp.status_code == 404
    # Full {error:{code,message}} envelope, AD-5.
    body = resp.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"]  # non-empty message present


def test_oversized_product_id_422_not_500():
    """An id longer than the DynamoDB key limit is a clean 422 (validation), never a 500."""
    resp = client.get("/products/" + "x" * 300)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_categories_route_not_shadowed_by_detail_route():
    """Regression (Epic 1 retro action item): the literal /categories route must win over
    /{product_id}, else GET /products/categories would 404 as a 'missing product'."""
    resp = client.get("/products/categories")
    assert resp.status_code == 200
    assert resp.json() == {"categories": ["books", "electronics", "home"]}
