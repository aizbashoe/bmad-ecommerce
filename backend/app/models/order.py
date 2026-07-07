"""Order + shipping models (AD-5 camelCase, AD-6 integer cents, AD-7 immutable snapshot).

An Order is an immutable snapshot taken at checkout: frozen line items (with unit prices),
totals, the shipping details, a human-readable reference, and a UTC timestamp. Never mutated.
"""

import re
from typing import Annotated

from pydantic import StringConstraints, field_validator

from app.models import CamelModel
from app.models.cart import CartLine

# Required shipping fields: trimmed, non-empty (server-side — the client form is not the authority).
Required = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class ShippingDetails(CamelModel):
    full_name: Required
    address1: Required
    address2: str = ""
    city: Required
    region: Required
    postal_code: Required
    country: Required
    email: Required

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("invalid email")
        return v


class Order(CamelModel):
    order_id: str
    reference: str  # human-readable, e.g. ORD-1A2B3C4D
    guest_id: str
    items: list[CartLine]  # frozen snapshot of the cart lines (unit prices + line totals)
    subtotal: int  # cents
    shipping: int  # flat shipping cost (cents)
    order_total: int  # subtotal + shipping (no tax), cents
    shipping_details: ShippingDetails
    created_at: str  # ISO-8601 UTC


class PlaceOrderRequest(CamelModel):
    shipping: ShippingDetails
