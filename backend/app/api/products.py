"""Products HTTP routes (AD-1 HTTP layer, AD-5 contract).

No business logic and no boto3 here — delegates to CatalogService. FastAPI validates
`limit` (422 -> error envelope); a malformed cursor raises AppError(invalid_cursor) -> 400.
"""

from fastapi import APIRouter, Depends, Path, Query

from app.models.catalog import CategoryList, ProductDetail, ProductPage, SortOption
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
    sort: SortOption = Query(default=SortOption.price_asc, description="Sort order (price)."),
    service: CatalogService = Depends(get_catalog_service),
) -> ProductPage:
    return service.list_products(
        limit=limit, cursor=cursor, search=search, categories=category, sort=sort.value
    )


# Registered LAST so the literal `/categories` and the `""` listing routes are matched
# before this path-param route (they must never be shadowed by `/{product_id}`).
@router.get("/{product_id}", response_model=ProductDetail)
def get_product(
    # Bounded well under DynamoDB's 2048-byte key limit so an oversized id is a clean 422
    # (validation_error envelope) instead of a ValidationException -> 500 from GetItem.
    product_id: str = Path(min_length=1, max_length=256, description="Product id."),
    service: CatalogService = Depends(get_catalog_service),
) -> ProductDetail:
    return service.get_product(product_id)
