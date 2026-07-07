"""CatalogService — catalog domain logic (AD-1 service layer).

Sits between the API routers and ProductsRepository. Holds no boto3; maps domain
Products to API response models. Grows with search/facet/sort in Stories 1.4–1.6.
"""

from app.core.errors import NotFoundError
from app.models.catalog import CategoryList, ProductDetail, ProductPage, ProductSummary
from app.repositories.products import ProductsRepository


class CatalogService:
    def __init__(self, repository: ProductsRepository | None = None):
        self._repo = repository or ProductsRepository()

    def list_products(
        self,
        limit: int = 24,
        cursor: str | None = None,
        search: str | None = None,
        categories: list[str] | None = None,
        sort: str = "price_asc",
    ) -> ProductPage:
        products, next_cursor = self._repo.list_products(
            limit=limit, cursor=cursor, search=search, categories=categories, sort=sort
        )
        return ProductPage(
            items=[ProductSummary.from_product(p) for p in products],
            next_cursor=next_cursor,
        )

    def list_categories(self) -> CategoryList:
        return CategoryList(categories=self._repo.list_categories())

    def get_product(self, product_id: str) -> ProductDetail:
        """Return one product's detail (FR-5); unknown id -> 404 not_found (AD-5)."""
        product = self._repo.get_product(product_id)
        if product is None:
            raise NotFoundError(f"Product '{product_id}' was not found")
        return ProductDetail.from_product(product)
