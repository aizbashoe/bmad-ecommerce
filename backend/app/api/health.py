"""Health endpoints.

- ``GET /health``       — liveness; no dependencies. Always 200 if the app is up.
- ``GET /health/deep``  — readiness; proves DynamoDB connectivity via list_tables()
                          (AC-7). Returns 503 (error envelope) if unreachable.

The deep check reaches the DynamoDB infra helper in the repository layer so boto3
stays quarantined there (AD-1); no table is created or required.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.errors import error_body
from app.repositories.dynamodb import list_table_names

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/deep")
def health_deep():
    try:
        tables = list_table_names()
    except Exception:  # noqa: BLE001 - surface any connectivity failure as 503
        # Do not leak endpoint/credential internals in the public response.
        return JSONResponse(
            status_code=503,
            content=error_body("dynamodb_unreachable", "DynamoDB not reachable"),
        )
    # Report reachability + a count; do not disclose the table inventory.
    return {"status": "ok", "dynamodb": "reachable", "tableCount": len(tables)}
