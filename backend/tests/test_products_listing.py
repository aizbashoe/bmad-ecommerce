"""Pagination tests for ProductsRepository.list_products (moto). Covers AC-1, AC-2, AC-7."""

import boto3
import pytest
from moto import mock_aws

from app.core.errors import AppError
from app.models.product import Product
from app.repositories import dynamodb as ddb_module
from app.repositories.products import ProductsRepository


@pytest.fixture
def repo(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        original = ddb_module.get_dynamodb_client
        original.cache_clear()
        monkeypatch.setattr(
            ddb_module,
            "get_dynamodb_client",
            lambda: boto3.client("dynamodb", region_name="us-east-1"),
        )
        r = ProductsRepository(table_name="Products")
        r.ensure_table()
        # 30 products with distinct, increasing prices for deterministic ordering.
        r.batch_put(
            [
                Product(
                    product_id=f"p-{i:04d}",
                    name=f"Item {i}",
                    description=f"desc {i}",
                    price=100 + i,
                    category="electronics" if i % 2 else "home",
                    image_url=f"https://img/{i}",
                    available=True,
                )
                for i in range(1, 31)
            ]
        )
        yield r
        original.cache_clear()


def test_pages_cover_all_items_price_ascending_no_dupes(repo):
    seen: list[str] = []
    prices: list[int] = []
    cursor = None
    pages = 0
    while True:
        products, cursor = repo.list_products(limit=10, cursor=cursor)
        pages += 1
        seen.extend(p.product_id for p in products)
        prices.extend(p.price for p in products)
        if cursor is None:
            break
        assert len(products) == 10  # full pages until the last

    assert pages == 3
    assert len(seen) == 30
    assert len(set(seen)) == 30  # no duplicates across pages
    assert prices == sorted(prices)  # price ascending across the whole sequence


def test_last_page_has_null_cursor(repo):
    _, cursor = repo.list_products(limit=100)  # all 30 in one page
    assert cursor is None


def test_cursor_roundtrips_between_pages(repo):
    page1, cursor = repo.list_products(limit=5)
    assert len(page1) == 5 and cursor is not None
    page2, _ = repo.list_products(limit=5, cursor=cursor)
    assert {p.product_id for p in page1}.isdisjoint({p.product_id for p in page2})


def test_bad_cursor_raises_invalid_cursor(repo):
    with pytest.raises(AppError) as exc:
        repo.list_products(limit=5, cursor="not-a-valid-cursor!!")
    assert exc.value.code == "invalid_cursor"
    assert exc.value.status_code == 400


def test_crafted_valid_base64_wrong_keys_is_invalid_cursor(repo):
    """A decodable base64 JSON object with the wrong shape must be 400, never a 500."""
    import base64
    import json

    forged = base64.urlsafe_b64encode(json.dumps({"foo": "bar"}).encode()).decode()
    with pytest.raises(AppError) as exc:
        repo.list_products(limit=5, cursor=forged)
    assert exc.value.code == "invalid_cursor"
    assert exc.value.status_code == 400


def test_real_cursor_from_page1_decodes_and_continues(repo):
    """End-to-end: a cursor minted by page 1 decodes cleanly and returns fresh items."""
    page1, cursor = repo.list_products(limit=5)
    assert cursor is not None
    page2, _ = repo.list_products(limit=5, cursor=cursor)
    assert len(page2) == 5
    assert {p.product_id for p in page1}.isdisjoint({p.product_id for p in page2})
