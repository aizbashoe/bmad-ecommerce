"""CartsRepository tests (moto-mocked DynamoDB). Story 3.1: Carts table + get-or-create."""

import boto3
import pytest
from moto import mock_aws

from app.models.cart import Cart
from app.repositories import dynamodb as ddb_module
from app.repositories.carts import CartsRepository


@pytest.fixture
def repo(monkeypatch):
    """A CartsRepository backed by a fresh moto DynamoDB (region pinned; factory patched)."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        original = ddb_module.get_dynamodb_client
        original.cache_clear()
        monkeypatch.setattr(
            ddb_module,
            "get_dynamodb_client",
            lambda: boto3.client("dynamodb", region_name="us-east-1"),
        )
        yield CartsRepository(table_name="Carts")
        original.cache_clear()


def test_ensure_table_creates_carts_with_guestid_pk_and_no_gsi(repo):
    repo.ensure_table()
    client = boto3.client("dynamodb", region_name="us-east-1")
    desc = client.describe_table(TableName="Carts")["Table"]
    assert desc["KeySchema"] == [{"AttributeName": "guestId", "KeyType": "HASH"}]
    # A cart is fetched only by its guestId — no secondary index.
    assert desc.get("GlobalSecondaryIndexes") in (None, [])


def test_ensure_table_is_idempotent(repo):
    repo.ensure_table()
    repo.ensure_table()  # second call must not raise
    client = boto3.client("dynamodb", region_name="us-east-1")
    assert client.describe_table(TableName="Carts")["Table"]["TableStatus"] == "ACTIVE"


def test_get_cart_missing_returns_none(repo):
    repo.ensure_table()
    assert repo.get_cart("nope") is None


def test_put_then_get_roundtrips_empty_cart(repo):
    repo.ensure_table()
    created = repo.put_empty_cart("11111111-1111-1111-1111-111111111111")
    assert created == Cart(guest_id="11111111-1111-1111-1111-111111111111", items=[])
    got = repo.get_cart("11111111-1111-1111-1111-111111111111")
    assert got == created
    assert got.items == []
