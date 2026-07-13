# =============================================================================
# app/schemas/common.py
#
# Shared Pydantic response models used across every endpoint.
#
# Design decisions:
#   - Every API response is wrapped in `ResponseEnvelope[T]`.  This gives
#     clients a consistent contract: check `success` first, then read `data`
#     or `error` accordingly.
#   - Generic typing (`ResponseEnvelope[T]`) lets OpenAPI generate accurate
#     per-endpoint schemas (e.g. `ResponseEnvelope[UserResponse]`) without
#     repetitive wrapper classes.
#   - `ErrorDetail` mirrors the shape produced by the exception handlers in
#     `app/exceptions.py` so the OpenAPI spec documents error responses too.
#   - `MetaResponse` carries pagination metadata and is optional — set it
#     only on list endpoints.
#
# Example successful response (paginated list):
#   {
#     "success": true,
#     "data": [{"id": 1, "name": "Alice"}],
#     "error": null,
#     "meta": {
#       "page": 1,
#       "page_size": 20,
#       "total": 42,
#       "total_pages": 3
#     }
#   }
#
# Example error response:
#   {
#     "success": false,
#     "data": null,
#     "error": {
#       "code": "NOT_FOUND",
#       "message": "Resource not found.",
#       "detail": null
#     },
#     "meta": null
#   }
# =============================================================================

from __future__ import annotations

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

# Generic type variable for the payload inside the envelope.
T = TypeVar("T")


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Structured error payload embedded in failed responses."""

    code: str = Field(
        description="Machine-readable error identifier (UPPER_SNAKE_CASE).",
        examples=["NOT_FOUND", "VALIDATION_ERROR"],
    )
    message: str = Field(
        description="Human-readable error description safe to display to users.",
        examples=["Resource not found."],
    )
    detail: object | None = Field(
        default=None,
        description="Optional structured data providing extra context (e.g. field errors).",
    )


class MetaResponse(BaseModel):
    """
    Pagination metadata returned on list endpoints.

    Attach to `ResponseEnvelope.meta` when returning paginated collections.
    """

    page: int = Field(description="Current page number (1-indexed).", examples=[1])
    page_size: int = Field(description="Number of items per page.", examples=[20])
    total: int = Field(description="Total number of items across all pages.", examples=[42])
    total_pages: int = Field(description="Total number of pages.", examples=[3])

    @classmethod
    def build(cls, *, page: int, page_size: int, total: int) -> "MetaResponse":
        """
        Construct a MetaResponse and compute `total_pages` automatically.

        Args:
            page:      Current page number (1-indexed).
            page_size: Items per page.
            total:     Total number of items.

        Returns:
            A fully populated MetaResponse.
        """
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        return cls(page=page, page_size=page_size, total=total, total_pages=total_pages)


# ---------------------------------------------------------------------------
# Generic envelope
# ---------------------------------------------------------------------------

class ResponseEnvelope(BaseModel, Generic[T]):
    """
    Universal API response wrapper.

    All endpoints return this model so clients always deal with the same
    top-level shape regardless of the endpoint.

    Type parameter T constrains the `data` field — FastAPI uses it to
    generate accurate OpenAPI schemas for each endpoint.

    Usage (success):
        return ResponseEnvelope.ok(data=UserResponse(...))
        return ResponseEnvelope.ok(data=items, meta=MetaResponse.build(...))

    Usage (error — usually via exception handlers, not routes directly):
        return ResponseEnvelope.fail(
            code="NOT_FOUND",
            message="User not found.",
        )
    """

    success: bool = Field(description="True if the request succeeded, false otherwise.")
    data: T | None = Field(default=None, description="Response payload (null on error).")
    error: ErrorDetail | None = Field(default=None, description="Error information (null on success).")
    meta: MetaResponse | None = Field(default=None, description="Pagination metadata (list endpoints only).")

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def ok(
        cls,
        data: T,
        *,
        meta: MetaResponse | None = None,
    ) -> "ResponseEnvelope[T]":
        """
        Build a successful response envelope.

        Args:
            data: The payload to wrap.
            meta: Optional pagination metadata.

        Returns:
            ResponseEnvelope with success=True.
        """
        return cls(success=True, data=data, error=None, meta=meta)

    @classmethod
    def fail(
        cls,
        *,
        code: str,
        message: str,
        detail: object = None,
    ) -> "ResponseEnvelope[None]":
        """
        Build a failure response envelope.

        Prefer raising an AppException subclass from routes; this factory
        is provided for cases where you need to construct an error response
        directly (e.g. custom middleware).

        Args:
            code:    Machine-readable error code.
            message: Human-readable error message.
            detail:  Optional structured context.

        Returns:
            ResponseEnvelope with success=False.
        """
        return cls(
            success=False,
            data=None,
            error=ErrorDetail(code=code, message=message, detail=detail),
            meta=None,
        )
