"""Products HTTP routes (AD-1 HTTP layer, AD-5 contract).

No business logic and no boto3 here — delegates to CatalogService. FastAPI validates
`limit` (422 -> error envelope); a malformed cursor raises AppError(invalid_cursor) -> 400.
"""

from fastapi import APIRouter, Depends, Query

from app.models.catalog import CategoryList, ProductPage
from app.services.catalog import CatalogService

router = APIRouter(prefix="/products", tags=["products"])


def get_catalog_service() -> CatalogService:
    # Constructed per request (stateless, AD-9). Injected via Depends so it can be overridden.
    return CatalogService()


# Registered before the parameterized listing route; also before any future /products/{id}.
@router.get("/categories", response_model=CategoryList)
def list_categories(
    service: CatalogService = Depends(get_catalog_service),
) -> CategoryList:
    return service.list_categories()


@router.get("", response_model=ProductPage)
def list_products(
    limit: int = Query(default=24, ge=1, le=100, description="Page size (1–100)."),
    cursor: str | None = Query(
        default=None, max_length=2048, description="Opaque cursor from a previous page."
    ),
    search: str | None = Query(
        default=None, max_length=100, description="Case-insensitive keyword (name/description)."
    ),
    category: list[str] | None = Query(
        default=None, description="Filter by category; repeat for multiple (OR)."
    ),
    service: CatalogService = Depends(get_catalog_service),
) -> ProductPage:
    return service.list_products(limit=limit, cursor=cursor, search=search, categories=category)
