"""Keyword search tests for ProductsRepository.list_products (moto). Covers FR-2 / AC-1..7."""

import boto3
import pytest
from moto import mock_aws

from app.models.product import Product
from app.repositories import dynamodb as ddb_module
from app.repositories.products import ProductsRepository


def _p(i: int, name: str, description: str, category: str = "home") -> Product:
    return Product(
        product_id=f"p-{i:04d}",
        name=name,
        description=description,
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
        yield r
        original.cache_clear()


def test_search_matches_name_and_description_only(repo):
    repo.batch_put(
        [
            _p(1, "Blue Widget", "a sturdy gadget"),      # name match "widget"
            _p(2, "Red Gizmo", "the best WIDGET around"),  # description match (case-insensitive)
            _p(3, "Green Thing", "nothing relevant here"), # no match
        ]
    )
    items, cursor = repo.list_products(limit=24, search="widget")
    ids = {p.product_id for p in items}
    assert ids == {"p-0001", "p-0002"}      # only name/description hits
    assert "p-0003" not in ids
    assert cursor is None


def test_search_is_case_insensitive(repo):
    repo.batch_put([_p(1, "SUPER Cap", "d"), _p(2, "plain sock", "d")])
    items, _ = repo.list_products(limit=24, search="super")
    assert [p.product_id for p in items] == ["p-0001"]


def test_empty_result_returns_empty_list_and_null_cursor(repo):
    repo.batch_put([_p(1, "Mug", "ceramic"), _p(2, "Lamp", "bright")])
    items, cursor = repo.list_products(limit=24, search="zzzznomatch")
    assert items == []
    assert cursor is None


def test_blank_search_behaves_like_no_search(repo):
    repo.batch_put([_p(i, f"Item {i}", "d") for i in range(1, 6)])
    all_items, _ = repo.list_products(limit=24)
    blank_items, _ = repo.list_products(limit=24, search="   ")
    assert {p.product_id for p in blank_items} == {p.product_id for p in all_items}


def test_loop_to_fill_gathers_sparse_matches_across_pages(repo):
    # 60 products; only every 10th matches "special". A naive Limit=5 query would return
    # 0 matches on the first page — loop-to-fill must dig until it has a full page.
    products = []
    for i in range(1, 61):
        if i % 10 == 0:
            products.append(_p(i, f"Special Item {i}", "d"))
        else:
            products.append(_p(i, f"Ordinary {i}", "d"))
    repo.batch_put(products)

    items, cursor = repo.list_products(limit=5, search="special")
    # There are 6 matches total; a full page of 5 must come back (not 0/1).
    assert len(items) >= 5
    assert all("special" in p.name.lower() for p in items)


def test_search_cursor_roundtrip_no_dup_no_gap(repo):
    # 40 matches; page through with limit=10 and assert full coverage, no duplicates.
    repo.batch_put([_p(i, f"Match {i}", "findme token") for i in range(1, 41)])
    seen: list[str] = []
    cursor = None
    guard = 0
    while True:
        guard += 1
        assert guard < 20
        items, cursor = repo.list_products(limit=10, cursor=cursor, search="findme")
        seen.extend(p.product_id for p in items)
        if cursor is None:
            break
    assert len(seen) == 40
    assert len(set(seen)) == 40
