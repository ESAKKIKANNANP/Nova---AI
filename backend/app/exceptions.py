# =============================================================================
# app/exceptions.py
#
# Application exception hierarchy and FastAPI exception handlers.
#
# Architecture:
#   - `AppException` is the single base class for all domain-level errors.
#     It carries an HTTP status code, a machine-readable error code (for
#     clients to branch on), a human-readable message, and optional detail.
#   - Concrete subclasses (NotFoundException, etc.) set sensible defaults so
#     call sites can raise them with minimal boilerplate.
#   - Two exception handlers are registered in main.py:
#       `app_exception_handler`  — catches AppException subclasses
#       `http_exception_handler` — catches FastAPI's built-in HTTPException
#     Both emit the same structured `ErrorResponse` JSON shape so clients
#     only need to handle one error format.
#   - An `unhandled_exception_handler` catches everything else and returns
#     a 500 without leaking internal details to the caller.
#
# Error response shape (all errors):
#   {
#     "success": false,
#     "error": {
#       "code": "NOT_FOUND",
#       "message": "Resource not found.",
#       "detail": null          # optional extra context
#     }
#   }
# =============================================================================

from __future__ import annotations

import structlog
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class AppException(Exception):
    """
    Base class for all application-level exceptions.

    Attributes:
        status_code: HTTP status code to return to the client.
        error_code:  Machine-readable error identifier (UPPER_SNAKE_CASE).
        message:     Human-readable error message (safe to expose to clients).
        detail:      Optional structured data providing extra context.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        detail: object = None,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail
        # Allow per-instance overrides of class-level defaults.
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


class NotFoundException(AppException):
    """Raised when a requested resource does not exist (404)."""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"

    def __init__(self, message: str = "Resource not found.", detail: object = None) -> None:
        super().__init__(message=message, detail=detail)


class ValidationException(AppException):
    """Raised when incoming data fails business-rule validation (422)."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"

    def __init__(self, message: str = "Validation failed.", detail: object = None) -> None:
        super().__init__(message=message, detail=detail)


class UnauthorizedException(AppException):
    """Raised when authentication credentials are missing or invalid (401)."""
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"

    def __init__(self, message: str = "Authentication required.", detail: object = None) -> None:
        super().__init__(message=message, detail=detail)


class ForbiddenException(AppException):
    """Raised when an authenticated user lacks permission for the action (403)."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"

    def __init__(self, message: str = "You do not have permission to perform this action.", detail: object = None) -> None:
        super().__init__(message=message, detail=detail)


class ConflictException(AppException):
    """Raised when a request conflicts with the current state of the server (409)."""
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"

    def __init__(self, message: str = "Resource conflict.", detail: object = None) -> None:
        super().__init__(message=message, detail=detail)


class ServiceUnavailableException(AppException):
    """Raised when a downstream dependency is unavailable (503)."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"

    def __init__(self, message: str = "A required service is currently unavailable.", detail: object = None) -> None:
        super().__init__(message=message, detail=detail)


# ---------------------------------------------------------------------------
# Shared error-response builder
# ---------------------------------------------------------------------------

def _build_error_body(error_code: str, message: str, detail: object = None) -> dict:
    """Return the standard error response dictionary."""
    return {
        "success": False,
        "data": None,
        "error": {
            "code": error_code,
            "message": message,
            "detail": detail,
        },
    }


# ---------------------------------------------------------------------------
# Exception handlers (registered in main.py)
# ---------------------------------------------------------------------------

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle all AppException subclasses.

    Logs the error at WARNING level (expected errors) and returns a
    structured JSON response.
    """
    logger.warning(
        "application_exception",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_body(exc.error_code, exc.message, exc.detail),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle FastAPI / Starlette's built-in HTTPException.

    Maps it to the same error envelope shape as AppException so clients
    only need to handle one format.
    """
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=str(exc.detail),
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_body(
            error_code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        ),
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle pydantic RequestValidationError (422 Unprocessable Entity).

    Surfaces the individual field errors in the `detail` payload so the
    client knows exactly which fields failed and why.
    """
    field_errors = [
        {
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    logger.warning(
        "request_validation_error",
        path=request.url.path,
        method=request.method,
        errors=field_errors,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_build_error_body(
            error_code="REQUEST_VALIDATION_ERROR",
            message="Request body or query parameters failed validation.",
            detail=field_errors,
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for any exception not caught by the handlers above.

    Logs at ERROR level with full traceback but returns a safe 500 response
    that does NOT expose internal details to the caller.
    """
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_build_error_body(
            error_code="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred. Please try again later.",
        ),
    )
