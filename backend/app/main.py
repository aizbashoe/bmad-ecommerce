"""FastAPI application entrypoint (AD-5, AD-8, AD-9).

Builds the app, applies CORS from config, mounts the aggregated API router, and
registers the error-envelope handlers. OpenAPI docs stay enabled at /docs and
/openapi.json (the contract source of truth). No module-level mutable state.
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import api_router
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    unhandled_error_handler,
    validation_exception_handler,
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Anonymous E-Commerce Storefront API",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    app.include_router(api_router)
    return app


app = create_app()
