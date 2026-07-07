"""Cart domain + API model (AD-2 guest-keyed, AD-5 camelCase on the wire).

Story 3.1 establishes the empty cart keyed by the anonymous `guestId`. Line items are
added in Story 3.2 — `items` is an (empty) list here and gains a typed element then.
"""

from pydantic import Field

from app.models import CamelModel


class Cart(CamelModel):
    guest_id: str
    items: list = Field(default_factory=list)  # line-item type arrives in Story 3.2
