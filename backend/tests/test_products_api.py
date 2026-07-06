"""GET /products endpoint tests (TestClient, stubbed service). Covers AC-1, AC-3, AC-5."""

import pytest
from fastapi.testclient import TestClient

from app.api.products import get_catalog_service
from app.core.errors import AppError
from app.services.catalog import CatalogService
from app.main import app

client = TestClient(app)


class _FakeRepo:
    def list_products(self, limit, cursor):
        if cursor == "BAD":
            raise AppError("Invalid pagination cursor", code="invalid_cursor", status_code=400)
        from app.models.product import Product

        items = [
            Product(
                product_id=f"p-{i}",
                name=f"Item {i}",
                description="d",
                price=1000 + i,
                category="home",
                image_url=f"https://img/{i}",
                available=True,
            )
            for i in range(limit)
        ]
        return items, ("NEXT" if cursor is None else None)


@pytest.fixture(autouse=True)
def stub_service():
    # Override the injected dependency (endpoint uses Depends(get_catalog_service)).
    app.dependency_overrides[get_catalog_service] = lambda: CatalogService(repository=_FakeRepo())
    yield
    app.dependency_overrides.clear()


def test_list_products_ok_shape():
    resp = client.get("/products?limit=3")
    assert resp.status_code == 200
    body = resp.json()
    assert body["nextCursor"] == "NEXT"
    assert len(body["items"]) == 3
    first = body["items"][0]
    assert set(first) == {"productId", "name", "price", "imageUrl", "category", "available"}
    assert isinstance(first["price"], int)  # cents, camelCase


def test_cursor_passthrough_returns_null_next():
    resp = client.get("/products?limit=2&cursor=SOMECURSOR")
    assert resp.status_code == 200
    assert resp.json()["nextCursor"] is None


@pytest.mark.parametrize("bad", ["0", "101", "-1", "abc"])
def test_limit_validation_422_envelope(bad):
    resp = client.get(f"/products?limit={bad}")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_invalid_cursor_400_envelope():
    resp = client.get("/products?cursor=BAD")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_cursor"
