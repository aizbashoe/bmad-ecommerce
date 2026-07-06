"""ProductsRepository tests (moto-mocked DynamoDB). Covers AC-1, AC-2, AC-5, AC-7."""

import boto3
import pytest
from moto import mock_aws

from app.models.product import Product
from app.repositories import dynamodb as ddb_module
from app.repositories.products import GSI_CATEGORY, GSI_LISTING, ProductsRepository


@pytest.fixture
def repo(monkeypatch):
    """A ProductsRepository backed by a fresh moto DynamoDB.

    ProductsRepository calls `dynamodb.get_dynamodb_client()` via the module, so patching
    that attribute on `ddb_module` is honored. Region is pinned explicitly so the suite
    is independent of any ambient AWS_REGION/AWS_DEFAULT_REGION.
    """
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        original = ddb_module.get_dynamodb_client
        original.cache_clear()
        monkeypatch.setattr(
            ddb_module,
            "get_dynamodb_client",
            lambda: boto3.client("dynamodb", region_name="us-east-1"),
        )
        yield ProductsRepository(table_name="Products")
        original.cache_clear()


def _sample(i: int) -> Product:
    return Product(
        product_id=f"p-{i:04d}",
        name=f"Sample {i}",
        description=f"desc {i}",
        price=1000 + i,
        category="electronics" if i % 2 else "home",
        image_url=f"https://img/{i}",
        available=True,
    )


def test_ensure_table_creates_table_with_correct_key_schemas(repo):
    repo.ensure_table()
    client = boto3.client("dynamodb", region_name="us-east-1")
    desc = client.describe_table(TableName="Products")["Table"]

    # Base table PK.
    assert desc["KeySchema"] == [{"AttributeName": "productId", "KeyType": "HASH"}]

    # Attribute types — price MUST be Number (N), or price sort/range breaks (AD-4/AD-6).
    attr_types = {a["AttributeName"]: a["AttributeType"] for a in desc["AttributeDefinitions"]}
    assert attr_types["price"] == "N"
    assert attr_types["category"] == "S"
    assert attr_types["listingPk"] == "S"

    # Both GSIs with exact key schemas.
    gsis = {g["IndexName"]: g["KeySchema"] for g in desc["GlobalSecondaryIndexes"]}
    assert gsis[GSI_CATEGORY] == [
        {"AttributeName": "category", "KeyType": "HASH"},
        {"AttributeName": "price", "KeyType": "RANGE"},
    ]
    assert gsis[GSI_LISTING] == [
        {"AttributeName": "listingPk", "KeyType": "HASH"},
        {"AttributeName": "price", "KeyType": "RANGE"},
    ]


def test_ensure_table_is_idempotent_no_op(repo, monkeypatch):
    repo.ensure_table()
    # A second call must NOT attempt to create the table again.
    calls = {"n": 0}
    real_create = repo._client.create_table

    def spy(*args, **kwargs):
        calls["n"] += 1
        return real_create(*args, **kwargs)

    monkeypatch.setattr(repo._client, "create_table", spy)
    repo.ensure_table()
    assert calls["n"] == 0  # existing table -> no create attempted


def test_put_product_writes_expected_attributes(repo):
    repo.ensure_table()
    repo.put_product(_sample(1))
    client = boto3.client("dynamodb", region_name="us-east-1")
    item = client.get_item(TableName="Products", Key={"productId": {"S": "p-0001"}})["Item"]
    assert item["listingPk"] == {"S": "PRODUCT"}
    assert item["price"] == {"N": "1001"}  # integer minor units, AD-6
    assert item["available"] == {"BOOL": True}


def test_batch_put_and_roundtrip(repo):
    repo.ensure_table()
    products = [_sample(i) for i in range(1, 31)]  # spans >1 batch chunk of 25
    repo.batch_put(products)
    assert repo.count() == 30
    got = repo.get_product("p-0005")
    assert got == _sample(5)


def test_get_missing_product_returns_none(repo):
    repo.ensure_table()
    assert repo.get_product("nope") is None
