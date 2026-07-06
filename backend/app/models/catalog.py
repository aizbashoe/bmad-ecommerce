"""Catalog API response models (AD-5: camelCase on the wire via CamelModel)."""

from app.models import CamelModel
from app.models.product import Product


class ProductSummary(CamelModel):
    """A product as shown in a listing (PLP card). productId links to the PDP route."""

    product_id: str
    name: str
    price: int  # integer minor units (cents), AD-6
    image_url: str
    category: str
    available: bool

    @classmethod
    def from_product(cls, p: Product) -> "ProductSummary":
        return cls(
            product_id=p.product_id,
            name=p.name,
            price=p.price,
            image_url=p.image_url,
            category=p.category,
            available=p.available,
        )


class ProductPage(CamelModel):
    """One page of products plus an opaque cursor to the next page (null on last page)."""

    items: list[ProductSummary]
    next_cursor: str | None = None


class CategoryList(CamelModel):
    """The distinct category values available for the PLP facet."""

    categories: list[str]
