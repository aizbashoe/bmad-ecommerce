"""Error envelope + handlers (AD-5).

Every error response uses the shape ``{"error": {"code", "message"}}``. Domain code
raises ``AppError`` (or subclasses); the handler maps it to that envelope. Registered
in ``app.main``. Later stories add subclasses (e.g. NotFoundError -> 404).
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base application error carrying an HTTP status, a stable code, and a message."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    """A requested resource does not exist -> 404 with code ``not_found`` (AD-5)."""

    status_code = 404
    code = "not_found"


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message))


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    # Do not leak internals; keep the envelope consistent.
    return JSONResponse(status_code=500, content=error_body("internal_error", "Internal server error"))


# Map FastAPI/Starlette's built-in errors into the same {error:{code,message}} envelope (AD-5),
# so every error response — including 404 and 422 — shares one shape.

_STATUS_CODE_NAMES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
}


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _STATUS_CODE_NAMES.get(exc.status_code, "http_error")
    return JSONResponse(status_code=exc.status_code, content=error_body(code, str(exc.detail)))


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content=error_body("validation_error", "Request validation failed"))
