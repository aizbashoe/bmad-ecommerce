"""GET /products endpoint tests (TestClient, stubbed service). Covers AC-1, AC-3, AC-5."""

import pytest
from fastapi.testclient import TestClient

from app.api.products import get_catalog_service
from app.core.errors import AppError
from app.services.catalog import CatalogService
from app.main import app

client = TestClient(app)


class _FakeRepo:
    def list_products(self, limit, cursor, search=None, categories=None, sort="price_asc"):
        if cursor == "BAD":
            raise AppError("Invalid pagination cursor", code="invalid_cursor", status_code=400)
        from app.models.product import Product

        # Echo the filters into the response so tests can assert passthrough.
        label = f"Match {search}" if search else "Item"
        category = (categories[0] if categories else "home")
        # Encode the sort into price ordering so the endpoint test can assert it was passed.
        items = [
            Product(
                product_id=f"p-{i}",
                name=f"{label} {i}",
                description="d",
                price=(1000 - i if sort == "price_desc" else 1000 + i),
                category=category,
                image_url=f"https://img/{i}",
                available=True,
            )
            for i in range(limit)
        ]
        return items, ("NEXT" if cursor is None else None)

    def list_categories(self):
        return ["books", "home", "toys"]


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


def test_search_param_passthrough_ok():
    resp = client.get("/products?limit=2&search=widget")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["items"][0]["name"].startswith("Match widget")


def test_search_too_long_422_envelope():
    resp = client.get(f"/products?search={'x' * 101}")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_single_category_passthrough():
    resp = client.get("/products?category=books&limit=2")
    assert resp.status_code == 200
    assert all(i["category"] == "books" for i in resp.json()["items"])


def test_multi_category_and_search_passthrough():
    resp = client.get("/products?category=home&category=books&search=mug&limit=1")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["category"] == "home"  # fake echoes first category
    assert item["name"].startswith("Match mug")


def test_categories_endpoint_shape():
    resp = client.get("/products/categories")
    assert resp.status_code == 200
    assert resp.json() == {"categories": ["books", "home", "toys"]}


def test_sort_passthrough_ok():
    resp = client.get("/products?sort=price_desc&limit=3")
    assert resp.status_code == 200
    prices = [i["price"] for i in resp.json()["items"]]
    # The fake echoes price_desc as descending prices -> proves sort reached the repo.
    assert prices == sorted(prices, reverse=True)


def test_bad_sort_422_envelope():
    resp = client.get("/products?sort=bogus")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"
