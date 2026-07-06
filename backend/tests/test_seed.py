"""Seed tests (moto-mocked DynamoDB). Covers AC-3, AC-4."""

import boto3
import pytest
from moto import mock_aws

from app.repositories import dynamodb as ddb_module
from app.repositories.products import ProductsRepository
from scripts import seed


@pytest.fixture
def moto_ddb(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        original = ddb_module.get_dynamodb_client
        original.cache_clear()
        monkeypatch.setattr(
            ddb_module,
            "get_dynamodb_client",
            lambda: boto3.client("dynamodb", region_name="us-east-1"),
        )
        yield
        original.cache_clear()


def test_generate_products_shape():
    products = seed.generate_products()
    assert 100 <= len(products) <= 500
    categories = {p.category for p in products}
    assert len(categories) >= 4
    assert all(isinstance(p.price, int) and p.price >= 0 for p in products)
    # Deterministic: regenerating yields identical ids/prices.
    again = seed.generate_products()
    assert [(p.product_id, p.price) for p in products] == [(p.product_id, p.price) for p in again]


def test_seed_is_idempotent(moto_ddb):
    seed.main()
    repo = ProductsRepository(table_name="Products")
    count_after_first = repo.count()
    assert count_after_first == len(seed.generate_products())

    # Re-running must not create duplicates — count stays stable.
    seed.main()
    assert repo.count() == count_after_first
