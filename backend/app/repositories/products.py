"""ProductsRepository — sole owner of the Products table (AD-1, AD-3).

The only place Products DynamoDB access lives: table provisioning, item mapping,
and writes. Domain code uses `Product`; DynamoDB item shapes never leak out of here.

Key design (AD-4), which the PLP stories (1.3–1.6) query:
  - Table PK  : productId (S)
  - gsi_category : category (S) HASH, price (N) RANGE  -> category facet + price sort
  - gsi_listing  : listingPk (S, const "PRODUCT") HASH, price (N) RANGE -> full listing + price sort
Both GSIs project ALL. Money is an integer minor-unit (cents) Number (AD-6).
"""

import base64
import json
import time

from botocore.exceptions import ClientError

from app.core.errors import AppError
from app.models.product import Product
from app.repositories import dynamodb

GSI_CATEGORY = "gsi_category"
GSI_LISTING = "gsi_listing"
LISTING_PK_VALUE = "PRODUCT"  # constant partition for the unfiltered listing GSI

# A gsi_listing LastEvaluatedKey carries the GSI keys + base-table key. A decoded cursor
# whose keys aren't a subset of these is not one we minted -> reject as invalid_cursor.
_LISTING_CURSOR_KEYS = frozenset({"listingPk", "price", "productId"})


class ProductsRepository:
    def __init__(self, table_name: str | None = None):
        from app.core.config import get_settings

        # Call via the module so a monkeypatch on dynamodb.get_dynamodb_client is honored.
        self._client = dynamodb.get_dynamodb_client()
        self._table = table_name or get_settings().products_table

    @property
    def table_name(self) -> str:
        return self._table

    # ---- provisioning -----------------------------------------------------

    def ensure_table(self) -> None:
        """Create the table + GSIs if absent; safe no-op if it already exists (FR-16)."""
        if self._table_exists():
            return
        try:
            self._client.create_table(
                TableName=self._table,
                BillingMode="PAY_PER_REQUEST",
                AttributeDefinitions=[
                    {"AttributeName": "productId", "AttributeType": "S"},
                    {"AttributeName": "category", "AttributeType": "S"},
                    {"AttributeName": "price", "AttributeType": "N"},
                    {"AttributeName": "listingPk", "AttributeType": "S"},
                ],
                KeySchema=[{"AttributeName": "productId", "KeyType": "HASH"}],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": GSI_CATEGORY,
                        "KeySchema": [
                            {"AttributeName": "category", "KeyType": "HASH"},
                            {"AttributeName": "price", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                    },
                    {
                        "IndexName": GSI_LISTING,
                        "KeySchema": [
                            {"AttributeName": "listingPk", "KeyType": "HASH"},
                            {"AttributeName": "price", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                    },
                ],
            )
        except ClientError as exc:
            # Another caller created it between our check and create — treat as no-op.
            if exc.response.get("Error", {}).get("Code") != "ResourceInUseException":
                raise
        # Block until the table is ACTIVE, then until both GSIs finish backfilling —
        # table_exists only gates on table status, not IndexStatus (a new GSI can still
        # be CREATING when the table is ACTIVE, which would fail an immediate GSI query).
        self._client.get_waiter("table_exists").wait(TableName=self._table)
        self._wait_gsis_active()

    def _wait_gsis_active(self, max_wait_s: float = 30.0, interval_s: float = 0.5) -> None:
        waited = 0.0
        while True:
            gsis = self._client.describe_table(TableName=self._table)["Table"].get(
                "GlobalSecondaryIndexes", []
            )
            if all(g.get("IndexStatus") == "ACTIVE" for g in gsis):
                return
            if waited >= max_wait_s:
                return  # best-effort; don't block provisioning forever
            time.sleep(interval_s)
            waited += interval_s

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
    def _to_item(p: Product) -> dict:
        return {
            "productId": {"S": p.product_id},
            "name": {"S": p.name},
            "description": {"S": p.description},
            "price": {"N": str(p.price)},
            "category": {"S": p.category},
            "imageUrl": {"S": p.image_url},
            "available": {"BOOL": p.available},
            "listingPk": {"S": LISTING_PK_VALUE},
        }

    @staticmethod
    def _from_item(item: dict) -> Product:
        return Product(
            product_id=item["productId"]["S"],
            name=item["name"]["S"],
            description=item["description"]["S"],
            price=int(item["price"]["N"]),
            category=item["category"]["S"],
            image_url=item["imageUrl"]["S"],
            available=item["available"]["BOOL"],
        )

    # ---- writes -----------------------------------------------------------

    def put_product(self, product: Product) -> None:
        """Idempotent upsert keyed by productId."""
        self._client.put_item(TableName=self._table, Item=self._to_item(product))

    def batch_put(self, products: list[Product], max_attempts: int = 8) -> None:
        """Write many products via BatchWriteItem (25/request).

        Retries UnprocessedItems with capped exponential backoff; raises if items are
        still unprocessed after ``max_attempts`` rounds (prevents an unbounded hot loop
        under sustained throttling).
        """
        for chunk in _chunks(products, 25):
            request = {self._table: [{"PutRequest": {"Item": self._to_item(p)}} for p in chunk]}
            for attempt in range(max_attempts):
                resp = self._client.batch_write_item(RequestItems=request)
                request = resp.get("UnprocessedItems") or {}
                if not request:
                    break
                time.sleep(min(2 ** attempt * 0.05, 2.0))  # capped backoff
            else:
                raise RuntimeError(
                    f"batch_put: {len(request.get(self._table, []))} items still unprocessed "
                    f"after {max_attempts} attempts"
                )

    # ---- reads (minimal; PLP query methods arrive in stories 1.3–1.6) -----

    def list_products(
        self, limit: int = 24, cursor: str | None = None
    ) -> tuple[list[Product], str | None]:
        """Page the full catalog via gsi_listing, price ascending (AD-4, FR-1).

        Returns (products, next_cursor). `next_cursor` is an opaque base64 token or None
        on the last page — the raw LastEvaluatedKey is never exposed.
        """
        kwargs = {
            "TableName": self._table,
            "IndexName": GSI_LISTING,
            "KeyConditionExpression": "listingPk = :pk",
            "ExpressionAttributeValues": {":pk": {"S": LISTING_PK_VALUE}},
            "Limit": limit,
            "ScanIndexForward": True,  # price ascending
        }
        start_key = _decode_cursor(cursor, expected_keys=_LISTING_CURSOR_KEYS)
        if start_key:
            kwargs["ExclusiveStartKey"] = start_key
        try:
            resp = self._client.query(**kwargs)
        except ClientError as exc:
            # A structurally-valid but semantically-bad ExclusiveStartKey (wrong types,
            # a key from a different query) is a client error, not a server fault.
            code = exc.response.get("Error", {}).get("Code")
            if start_key and code == "ValidationException":
                raise AppError("Invalid pagination cursor", code="invalid_cursor", status_code=400) from exc
            raise
        products = [self._from_item(item) for item in resp.get("Items", [])]
        return products, _encode_cursor(resp.get("LastEvaluatedKey"))

    def get_product(self, product_id: str) -> Product | None:
        resp = self._client.get_item(
            TableName=self._table, Key={"productId": {"S": product_id}}
        )
        item = resp.get("Item")
        return self._from_item(item) if item else None

    def count(self) -> int:
        """Item count via a paginated Select=COUNT scan (test/verification helper)."""
        total, start_key = 0, None
        while True:
            kwargs = {"TableName": self._table, "Select": "COUNT", "ConsistentRead": True}
            if start_key:
                kwargs["ExclusiveStartKey"] = start_key
            resp = self._client.scan(**kwargs)
            total += resp.get("Count", 0)
            start_key = resp.get("LastEvaluatedKey")
            if not start_key:
                return total


def _chunks(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def _encode_cursor(last_evaluated_key: dict | None) -> str | None:
    """Encode a DynamoDB LastEvaluatedKey as an opaque urlsafe-base64 token (AD-4)."""
    if not last_evaluated_key:
        return None
    raw = json.dumps(last_evaluated_key, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode()


def _decode_cursor(cursor: str | None, expected_keys: frozenset[str] | None = None) -> dict | None:
    """Decode an opaque cursor back to an ExclusiveStartKey; bad input -> 400 invalid_cursor.

    Rejects (as invalid_cursor) anything that isn't base64-of-JSON-object, and — when
    ``expected_keys`` is given — anything whose keys aren't a subset of that set or whose
    values aren't single-type-tag attribute maps. This stops a crafted-but-decodable cursor
    from reaching DynamoDB and surfacing as a 500.
    """
    if not cursor:
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        if not isinstance(data, dict) or not data:
            raise ValueError("cursor is not a key object")
        if expected_keys is not None:
            if not set(data).issubset(expected_keys):
                raise ValueError("cursor keys do not match this query")
            for v in data.values():
                if not isinstance(v, dict) or len(v) != 1:
                    raise ValueError("cursor value is not a DynamoDB attribute")
        return data
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001 - any malformed cursor is a client error
        raise AppError("Invalid pagination cursor", code="invalid_cursor", status_code=400) from exc
