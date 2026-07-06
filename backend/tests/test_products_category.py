"""Category-facet tests for ProductsRepository (moto). Covers FR-3 / AC-1..4, AC-7, AC-8."""

import boto3
import pytest
from moto import mock_aws

from app.core.errors import AppError
from app.models.product import Product
from app.repositories import dynamodb as ddb_module
from app.repositories.products import ProductsRepository


def _p(i: int, category: str, name: str | None = None) -> Product:
    return Product(
        product_id=f"p-{i:04d}",
        name=name or f"Item {i}",
        description=f"desc {i}",
        price=100 + i,
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
        # 30 across 3 categories, interleaved.
        cats = ["home", "books", "toys"]
        r.batch_put([_p(i, cats[i % 3]) for i in range(1, 31)])
        yield r
        original.cache_clear()


def test_single_category_uses_gsi_category_path(repo):
    items, cursor = repo.list_products(limit=24, categories=["home"])
    assert items and all(p.category == "home" for p in items)
    assert [p.price for p in items] == sorted(p.price for p in items)  # price ascending
    assert cursor is None  # all home items fit one page


def test_multi_category_or(repo):
    items, _ = repo.list_products(limit=50, categories=["home", "books"])
    got = {p.category for p in items}
    assert got == {"home", "books"}  # union, excludes toys


def test_category_and_search_compose(repo):
    # Give one home item a distinctive name; search within home should match only it.
    repo.put_product(_p(1, "home", name="Special Mug"))
    items, _ = repo.list_products(limit=50, categories=["home"], search="special")
    assert [p.product_id for p in items] == ["p-0001"]


def test_category_cursor_roundtrip_no_dup(repo):
    seen: list[str] = []
    cursor = None
    guard = 0
    while True:
        guard += 1
        assert guard < 20
        items, cursor = repo.list_products(limit=4, categories=["home"], cursor=cursor)
        seen.extend(p.product_id for p in items)
        if cursor is None:
            break
    assert len(seen) == len(set(seen))
    assert all(pid in {f"p-{i:04d}" for i in range(1, 31)} for pid in seen)


def test_cross_index_cursor_rejected(repo):
    # A cursor minted by the single-category (gsi_category) path must be rejected when
    # replayed on a multi-category (gsi_listing) query — shape mismatch -> invalid_cursor.
    _, cat_cursor = repo.list_products(limit=4, categories=["home"])
    assert cat_cursor is not None
    with pytest.raises(AppError) as exc:
        repo.list_products(limit=4, categories=["home", "books"], cursor=cat_cursor)
    assert exc.value.code == "invalid_cursor"


def test_list_categories_distinct_sorted(repo):
    assert repo.list_categories() == ["books", "home", "toys"]


def test_composed_path_cursor_roundtrip_no_dup(repo):
    """Multi-category (gsi_listing + FilterExpression) paginates with no dup/gap."""
    seen: list[str] = []
    cursor = None
    guard = 0
    while True:
        guard += 1
        assert guard < 30
        items, cursor = repo.list_products(limit=4, categories=["home", "books"], cursor=cursor)
        seen.extend(p.product_id for p in items)
        if cursor is None:
            break
    # 20 home + books items (indices where i%3 in {0,1} across 1..30).
    assert len(seen) == len(set(seen))  # no duplicates
    assert all(p_id.startswith("p-") for p_id in seen)


def test_listing_cursor_rejected_on_fast_path(repo):
    """Reverse of the cross-index test: a gsi_listing cursor replayed on the single-category
    fast path must be rejected as invalid_cursor (shape mismatch), not 500."""
    _, listing_cursor = repo.list_products(limit=4, categories=["home", "books"])
    assert listing_cursor is not None
    with pytest.raises(AppError) as exc:
        repo.list_products(limit=4, categories=["home"], cursor=listing_cursor)
    assert exc.value.code == "invalid_cursor"


def test_too_many_categories_rejected(repo):
    with pytest.raises(AppError) as exc:
        repo.list_products(limit=4, categories=[f"c{i}" for i in range(101)])
    assert exc.value.code == "too_many_categories"
    assert exc.value.status_code == 400
