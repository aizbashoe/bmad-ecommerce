"""Sort tests for ProductsRepository (moto). Covers FR-4 / AC-1..4, AC-7, AC-8."""

import boto3
import pytest
from moto import mock_aws

from app.models.product import Product
from app.repositories import dynamodb as ddb_module
from app.repositories.products import ProductsRepository


def _p(i: int, category: str, name: str | None = None) -> Product:
    return Product(
        product_id=f"p-{i:04d}",
        name=name or f"Item {i}",
        description=f"desc {i}",
        price=100 + i * 10,  # distinct, increasing with i
        category=category,
        image_url=f"https://img/{i}",
        available=True,
    )


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
        r.batch_put([_p(i, ["home", "books", "toys"][i % 3]) for i in range(1, 31)])
        yield r
        original.cache_clear()


def test_fast_path_asc_and_desc(repo):
    """Single-category (gsi_category) path honors sort direction."""
    asc, _ = repo.list_products(limit=50, categories=["home"], sort="price_asc")
    desc, _ = repo.list_products(limit=50, categories=["home"], sort="price_desc")
    asc_prices = [p.price for p in asc]
    desc_prices = [p.price for p in desc]
    assert asc_prices == sorted(asc_prices)
    assert desc_prices == sorted(desc_prices, reverse=True)
    assert asc_prices == list(reversed(desc_prices))  # same set, opposite order


def test_listing_path_asc_and_desc(repo):
    """Multi-category (gsi_listing composed) path honors sort direction."""
    asc, _ = repo.list_products(limit=50, categories=["home", "books"], sort="price_asc")
    desc, _ = repo.list_products(limit=50, categories=["home", "books"], sort="price_desc")
    assert [p.price for p in asc] == sorted(p.price for p in asc)
    assert [p.price for p in desc] == sorted((p.price for p in desc), reverse=True)


def test_default_is_price_ascending(repo):
    default, _ = repo.list_products(limit=50)
    assert [p.price for p in default] == sorted(p.price for p in default)


def test_sort_with_search_and_category(repo):
    repo.put_product(_p(2, "home", name="Special Mug A"))
    repo.put_product(_p(5, "home", name="Special Mug B"))
    items, _ = repo.list_products(limit=50, categories=["home"], search="special", sort="price_desc")
    assert [p.price for p in items] == sorted((p.price for p in items), reverse=True)
    assert all("special" in p.name.lower() and p.category == "home" for p in items)


def test_desc_cursor_roundtrip_no_dup(repo):
    seen: list[str] = []
    prices: list[int] = []
    cursor = None
    guard = 0
    while True:
        guard += 1
        assert guard < 30
        items, cursor = repo.list_products(limit=7, sort="price_desc", cursor=cursor)
        seen.extend(p.product_id for p in items)
        prices.extend(p.price for p in items)
        if cursor is None:
            break
    assert len(seen) == 30 and len(set(seen)) == 30  # all once, no dup
    assert prices == sorted(prices, reverse=True)  # descending across all pages


def test_invalid_sort_raises(repo):
    from app.core.errors import AppError

    with pytest.raises(AppError) as exc:
        repo.list_products(limit=5, sort="bogus")
    assert exc.value.code == "invalid_sort"


def test_cursor_bound_to_sort_rejects_replay_under_other_direction(repo):
    """A cursor minted under price_asc replayed under price_desc must be rejected, not
    silently paginate the reversed scan (dup/gap). Same fix guards search/category changes."""
    from app.core.errors import AppError

    _, cursor = repo.list_products(limit=5, sort="price_asc")
    assert cursor is not None
    with pytest.raises(AppError) as exc:
        repo.list_products(limit=5, sort="price_desc", cursor=cursor)
    assert exc.value.code == "invalid_cursor"


def test_cursor_bound_to_filters_rejects_changed_category(repo):
    _, cursor = repo.list_products(limit=4, categories=["home", "books"])
    assert cursor is not None
    from app.core.errors import AppError

    with pytest.raises(AppError) as exc:
        repo.list_products(limit=4, categories=["home", "toys"], cursor=cursor)
    assert exc.value.code == "invalid_cursor"
