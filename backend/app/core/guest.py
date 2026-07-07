"""Guest-session id resolution (AD-2), shared by the cart and checkout services.

Issue (no token) or validate+canonicalize (token) the opaque guestId. Extracted so cart and
checkout resolve the token identically — a malformed token is a 400, never an arbitrary key.
"""

import uuid

from app.core.errors import AppError


def resolve_guest_id(token: str | None) -> str:
    if not token:
        return str(uuid.uuid4())
    try:
        # Validate AND canonicalize (uppercase/braces/urn/dashless all normalize to one key).
        return str(uuid.UUID(token))
    except ValueError as exc:
        raise AppError("Invalid guest token", code="invalid_guest_token", status_code=400) from exc
