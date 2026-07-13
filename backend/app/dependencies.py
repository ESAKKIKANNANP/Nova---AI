# =============================================================================
# app/dependencies.py
#
# Reusable FastAPI dependency providers.
#
# FastAPI's Dependency Injection system (`Depends`) allows you to declare
# shared resources — database sessions, auth context, settings, loggers —
# as typed function arguments.  FastAPI resolves and caches them per-request
# (or per-application, depending on the scope).
#
# This module contains:
#   - `get_settings`  — yields the cached Settings singleton
#   - `get_logger`    — yields a structlog logger with request-scoped context
#   - `get_pagination`— parses and validates pagination query parameters
#
# How to use in a route:
#
#   from typing import Annotated
#   from fastapi import Depends
#   from app.dependencies import get_settings, get_logger, PaginationParams
#   from app.config import Settings
#
#   @router.get("/items")
#   async def list_items(
#       settings: Annotated[Settings, Depends(get_settings)],
#       logger: Annotated[structlog.BoundLogger, Depends(get_logger)],
#       pagination: Annotated[PaginationParams, Depends(get_pagination)],
#   ):
#       logger.info("listing_items", page=pagination.page)
#       ...
#
# How to override in tests:
#
#   from app.config import Settings
#   from app.dependencies import get_settings
#
#   def override_settings():
#       return Settings(secret_key="test-secret", env="development")
#
#   app.dependency_overrides[get_settings] = override_settings
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import structlog
from fastapi import Depends, Query

from app.config import Settings, get_settings as _get_settings


# ---------------------------------------------------------------------------
# Settings dependency
# ---------------------------------------------------------------------------

def get_settings() -> Settings:
    """
    Provide the application Settings singleton via FastAPI DI.

    The underlying `_get_settings()` is wrapped in @lru_cache so this
    function is effectively free after the first call.

    Returns:
        Settings: The fully-validated, immutable application configuration.
    """
    return _get_settings()


# ---------------------------------------------------------------------------
# Logger dependency
# ---------------------------------------------------------------------------

def get_logger(
    settings: Annotated[Settings, Depends(get_settings)],
) -> structlog.stdlib.BoundLogger:
    """
    Provide a structlog BoundLogger pre-configured with request-level context.

    The logger returned here already has the service, env, and version fields
    bound via `configure_logging()` at startup.  Middleware binds the
    correlation_id to the contextvars store, so every log record emitted
    during the request automatically includes it.

    Args:
        settings: Injected Settings (used for the logger name).

    Returns:
        BoundLogger: A structlog logger bound to the application name.

    Example:
        logger.info("item_fetched", item_id=42, duration_ms=12.5)
    """
    return structlog.get_logger(settings.app_name)


# ---------------------------------------------------------------------------
# Pagination dependency
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PaginationParams:
    """
    Standard pagination parameters parsed from query string.

    Attributes:
        page:      1-indexed page number (default: 1).
        page_size: Number of items per page (default: 20, max: 100).
        offset:    Computed DB offset (page - 1) * page_size.
    """
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        """Return the zero-based item offset for SQL OFFSET clauses."""
        return (self.page - 1) * self.page_size


def get_pagination(
    page: Annotated[
        int,
        Query(ge=1, description="1-indexed page number."),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100, alias="pageSize", description="Items per page (max 100)."),
    ] = 20,
) -> PaginationParams:
    """
    Parse and validate standard pagination query parameters.

    Query params:
        page      (int, ≥1):       Page number, 1-indexed.  Default: 1.
        pageSize  (int, 1–100):    Items per page.          Default: 20.

    Returns:
        PaginationParams with `.page`, `.page_size`, and computed `.offset`.
    """
    return PaginationParams(page=page, page_size=page_size)
