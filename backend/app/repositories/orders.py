"""OrdersRepository — owner of the Orders table (AD-1, AD-3), plus the atomic place-order.

The order write and the cart delete must be atomic (AD-7) — a shopper can never be left
order-without-cart-cleared or cart-cleared-without-order. DynamoDB `TransactWriteItems` does
both in one call; because that transaction inherently spans the Orders + Carts tables, it lives
here (the order-placement owner) and takes the carts table name as a parameter.
"""

from botocore.exceptions import ClientError

from app.core.errors import AppError
from app.models.cart import CartLine
from app.models.order import Order, ShippingDetails
from app.repositories import dynamodb


class OrdersRepository:
    def __init__(self, table_name: str | None = None):
        from app.core.config import get_settings

        self._client = dynamodb.get_dynamodb_client()
        self._table = table_name or get_settings().orders_table

    @property
    def table_name(self) -> str:
        return self._table

    def ensure_table(self) -> None:
        """Create the Orders table if absent (PK orderId, PAY_PER_REQUEST, no GSI). Idempotent."""
        if self._table_exists():
            return
        try:
            self._client.create_table(
                TableName=self._table,
                BillingMode="PAY_PER_REQUEST",
                AttributeDefinitions=[{"AttributeName": "orderId", "AttributeType": "S"}],
                KeySchema=[{"AttributeName": "orderId", "KeyType": "HASH"}],
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") != "ResourceInUseException":
                raise
        self._client.get_waiter("table_exists").wait(TableName=self._table)

    def _table_exists(self) -> bool:
        try:
            self._client.describe_table(TableName=self._table)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
                return False
            raise

    # ---- mapping ----------------------------------------------------------

    @staticmethod
    def _to_item(order: Order) -> dict:
        sd = order.shipping_details
        return {
            "orderId": {"S": order.order_id},
            "reference": {"S": order.reference},
            "guestId": {"S": order.guest_id},
            "items": {
                "L": [
                    {
                        "M": {
                            "productId": {"S": i.product_id},
                            "name": {"S": i.name},
                            "unitPrice": {"N": str(i.unit_price)},
                            "imageUrl": {"S": i.image_url},
                            "quantity": {"N": str(i.quantity)},
                            "lineTotal": {"N": str(i.line_total)},
                        }
                    }
                    for i in order.items
                ]
            },
            "subtotal": {"N": str(order.subtotal)},
            "shipping": {"N": str(order.shipping)},
            "orderTotal": {"N": str(order.order_total)},
            "shippingDetails": {
                "M": {
                    "fullName": {"S": sd.full_name},
                    "address1": {"S": sd.address1},
                    "address2": {"S": sd.address2},
                    "city": {"S": sd.city},
                    "region": {"S": sd.region},
                    "postalCode": {"S": sd.postal_code},
                    "country": {"S": sd.country},
                    "email": {"S": sd.email},
                }
            },
            "createdAt": {"S": order.created_at},
        }

    @staticmethod
    def _from_item(item: dict) -> Order:
        items = [
            CartLine(
                product_id=m["M"]["productId"]["S"],
                name=m["M"]["name"]["S"],
                unit_price=int(m["M"]["unitPrice"]["N"]),
                image_url=m["M"]["imageUrl"]["S"],
                quantity=int(m["M"]["quantity"]["N"]),
                line_total=int(m["M"]["lineTotal"]["N"]),
            )
            for m in item.get("items", {}).get("L", [])
        ]
        sd = item["shippingDetails"]["M"]
        shipping = ShippingDetails(
            full_name=sd["fullName"]["S"],
            address1=sd["address1"]["S"],
            address2=sd["address2"]["S"],
            city=sd["city"]["S"],
            region=sd["region"]["S"],
            postal_code=sd["postalCode"]["S"],
            country=sd["country"]["S"],
            email=sd["email"]["S"],
        )
        return Order(
            order_id=item["orderId"]["S"],
            reference=item["reference"]["S"],
            guest_id=item["guestId"]["S"],
            items=items,
            subtotal=int(item["subtotal"]["N"]),
            shipping=int(item["shipping"]["N"]),
            order_total=int(item["orderTotal"]["N"]),
            shipping_details=shipping,
            created_at=item["createdAt"]["S"],
        )

    # ---- reads / atomic write --------------------------------------------

    def get_order(self, order_id: str) -> Order | None:
        resp = self._client.get_item(TableName=self._table, Key={"orderId": {"S": order_id}})
        item = resp.get("Item")
        return self._from_item(item) if item else None

    def place_order_txn(self, order: Order, carts_table: str) -> Order:
        """Atomically write the Order and delete the guest's Cart (AD-7) in one transaction."""
        try:
            self._client.transact_write_items(
                TransactItems=[
                    {"Put": {"TableName": self._table, "Item": self._to_item(order)}},
                    {"Delete": {"TableName": carts_table, "Key": {"guestId": {"S": order.guest_id}}}},
                ]
            )
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            # Only a genuine transaction conflict is a 409; other ClientErrors (throttling,
            # internal, validation) are server faults — re-raise so they surface as a 500 envelope.
            if code in ("TransactionCanceledException", "TransactionConflictException"):
                raise AppError(
                    "Could not place order — please try again", code="order_failed", status_code=409
                ) from exc
            raise
        return order
