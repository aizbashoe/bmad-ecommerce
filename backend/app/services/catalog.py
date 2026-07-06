"""CatalogService — catalog domain logic (AD-1 service layer).

Sits between the API routers and ProductsRepository. Holds no boto3; maps domain
Products to API response models. Grows with search/facet/sort in Stories 1.4–1.6.
"""

from app.models.catalog import CategoryList, ProductPage, ProductSummary
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
