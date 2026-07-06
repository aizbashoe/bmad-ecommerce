"""Product domain model (AD-5 camelCase on the wire, AD-6 money as integer cents).

A pure domain type — no DynamoDB item shapes. The ProductsRepository maps this
to/from DynamoDB items; nothing above the repository sees storage details (AD-1).
"""

from pydantic import Field

from app.models import CamelModel


class Product(CamelModel):
    product_id: str
    name: str
    description: str
    price: int = Field(ge=0)  # integer minor units (cents), AD-6
    category: str
    image_url: str
    available: bool = True
