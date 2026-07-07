"""Idempotent local table provisioning (AD-3).

Ensures every DynamoDB table this app owns exists (Products, Carts). Safe to re-run.
Run with:  python -m scripts.provision
(inside the api container:  docker compose exec api python -m scripts.provision)

The seed script (`scripts.seed`) provisions + fills Products; this ensures the Carts table
too, so the cart endpoints work locally without a seed. Requests never create tables
themselves (that would add per-request latency and couple the stateless API to provisioning).
"""

from app.repositories.carts import CartsRepository
from app.repositories.orders import OrdersRepository
from app.repositories.products import ProductsRepository


def provision() -> None:
    ProductsRepository().ensure_table()
    CartsRepository().ensure_table()
    OrdersRepository().ensure_table()
    print("Provisioned tables: Products, Carts, Orders")


if __name__ == "__main__":
    provision()
