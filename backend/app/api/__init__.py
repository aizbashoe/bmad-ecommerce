"""HTTP layer (AD-1): FastAPI routers only. No business logic, no boto3 here.

`api_router` aggregates all feature routers; later stories add products, cart,
checkout, orders routers alongside health.
"""

from fastapi import APIRouter

from app.api import cart, health, products

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
