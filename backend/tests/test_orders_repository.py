"""OrdersRepository tests (moto). Story 4.3: atomic place-order (order write + cart clear)."""

import boto3
import pytest
from moto import mock_aws

from app.models.cart import Cart, CartItem, CartLine
from app.models.order import Order, ShippingDetails
from app.repositories import dynamodb as ddb_module
from app.repositories.carts import CartsRepository
from app.repositories.orders import OrdersRepository


@pytest.fixture
def repos(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        original = ddb_module.get_dynamodb_client
        original.cache_clear()
        monkeypatch.setattr(
            ddb_module,
            "get_dynamodb_client",
            lambda: boto3.client("dynamodb", region_name="us-east-1"),
        )
        carts = CartsRepository(table_name="Carts")
        orders = OrdersRepository(table_name="Orders")
        carts.ensure_table()
        orders.ensure_table()
        yield carts, orders
        original.cache_clear()


def _order(guest_id: str = "g-1") -> Order:
    return Order(
        order_id="o-1",
        reference="ORD-TESTCODE",
        guest_id=guest_id,
        items=[CartLine(product_id="p-1", name="Headphones", unit_price=3000, image_url="https://img/p-1", quantity=2, line_total=6000)],
        subtotal=6000,
        shipping=500,
        order_total=6500,
        shipping_details=ShippingDetails(
            full_name="A B", address1="1 St", city="Kyiv", region="Kyiv",
            postal_code="01001", country="Ukraine", email="a@b.com",
        ),
        created_at="2026-07-07T00:00:00+00:00",
    )


def test_place_order_txn_writes_order_and_clears_cart(repos):
    carts, orders = repos
    carts.put_cart(Cart(guest_id="g-1", items=[CartItem(product_id="p-1", name="Headphones", unit_price=3000, image_url="https://img/p-1", quantity=2)]))
    order = _order("g-1")
    orders.place_order_txn(order, carts_table=carts.table_name)
    assert orders.get_order("o-1") == order  # immutable snapshot round-trips
    assert carts.get_cart("g-1") is None  # cart cleared atomically (AD-7)


def test_get_order_missing_returns_none(repos):
    _, orders = repos
    assert orders.get_order("nope") is None
