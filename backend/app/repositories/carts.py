"""CartsRepository — sole owner of the Carts table (AD-1, AD-3).

Carts are keyed by the opaque `guestId` (AD-2): one item per guest, no GSI, no sort key.
As with ProductsRepository, boto3/DynamoDB access lives only here and the DynamoDB item
shape never leaks past this class. Line items arrive in Story 3.2.
"""

from botocore.exceptions import ClientError

from app.models.cart import Cart
from app.repositories import dynamodb


class CartsRepository:
    def __init__(self, table_name: str | None = None):
        from app.core.config import get_settings

        # Call via the module so a monkeypatch on dynamodb.get_dynamodb_client is honored.
        self._client = dynamodb.get_dynamodb_client()
        self._table = table_name or get_settings().carts_table

    @property
    def table_name(self) -> str:
        return self._table

    # ---- provisioning -----------------------------------------------------

    def ensure_table(self) -> None:
        """Create the Carts table if absent; safe no-op if it already exists.

        PK = guestId (S), PAY_PER_REQUEST, no GSI (a cart is fetched only by its guestId).
        """
        if self._table_exists():
            return
        try:
            self._client.create_table(
                TableName=self._table,
                BillingMode="PAY_PER_REQUEST",
                AttributeDefinitions=[{"AttributeName": "guestId", "AttributeType": "S"}],
                KeySchema=[{"AttributeName": "guestId", "KeyType": "HASH"}],
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

    # ---- item mapping -----------------------------------------------------

    @staticmethod
    def _to_item(cart: Cart) -> dict:
        # `items` is always an empty List here; Story 3.2 maps line items into it.
        return {"guestId": {"S": cart.guest_id}, "items": {"L": []}}

    @staticmethod
    def _from_item(item: dict) -> Cart:
        # Line-item parsing arrives in Story 3.2; the cart is empty in 3.1.
        return Cart(guest_id=item["guestId"]["S"], items=[])

    # ---- reads / writes ---------------------------------------------------

    def get_cart(self, guest_id: str) -> Cart | None:
        resp = self._client.get_item(TableName=self._table, Key={"guestId": {"S": guest_id}})
        item = resp.get("Item")
        return self._from_item(item) if item else None

    def put_empty_cart(self, guest_id: str) -> Cart:
        """Create (or reset to) an empty cart for a guest. Callers use get-or-create, so this
        only runs when no cart exists yet for the id."""
        cart = Cart(guest_id=guest_id, items=[])
        self._client.put_item(TableName=self._table, Item=self._to_item(cart))
        return cart
