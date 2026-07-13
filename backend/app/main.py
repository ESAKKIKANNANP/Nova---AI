# =============================================================================
# app/main.py
#
# FastAPI application factory and entry point.
#
# Architecture:
#   - `create_app()` is a factory function (not a module-level global) so
#     tests can spin up fresh, isolated application instances.
#   - The `lifespan` async context manager handles startup and shutdown
#     hooks in a single, readable place (replaces on_event decorators).
#   - Middleware is registered in outermost-first order (the first
#     `add_middleware` call wraps all subsequent ones).
#   - Exception handlers are registered for AppException, HTTPException,
#     RequestValidationError, and the catch-all Exception.
#   - The module-level `app` object is what gunicorn / uvicorn imports.
#
# Middleware execution order (request direction ↓):
#   CORSMiddleware
#   CorrelationIdMiddleware
#   RequestLoggingMiddleware
#   → route handler
#   ← route handler
#   RequestLoggingMiddleware
#   CorrelationIdMiddleware
#   CORSMiddleware
# =============================================================================

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import Settings, get_settings
from app.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    request_validation_exception_handler,
    unhandled_exception_handler,
)
from app.logging_config import configure_logging
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routers import health

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan context manager — startup & shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application startup and shutdown hooks.

    Code BEFORE `yield` runs on startup.
    Code AFTER  `yield` runs on shutdown (even if an exception occurred).

    Add resource initialisation here as the application grows:
      - Database connection pool (e.g. SQLAlchemy async engine)
      - Redis client
      - ML model loading
      - Background task scheduler
    """
    settings: Settings = get_settings()

    # ── Startup ───────────────────────────────────────────────────────────────
    configure_logging(settings)
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        version=settings.app_version,
        env=settings.env.value,
        debug=settings.debug,
        host=settings.host,
        port=settings.port,
    )

    # TODO: initialise DB pool
    # TODO: initialise Redis client
    # TODO: warm ML models

    yield  # ← application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("application_shutdown", app_name=settings.app_name)

    # TODO: close DB pool
    # TODO: close Redis client


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Construct and configure the FastAPI application.

    Args:
        settings: Optional Settings instance.  When None, the cached
                  singleton from `get_settings()` is used.  Pass a custom
                  Settings in tests to override configuration without
                  touching environment variables.

    Returns:
        A fully configured FastAPI application instance.
    """
    _settings = settings or get_settings()

    # ── FastAPI instance ──────────────────────────────────────────────────────
    application = FastAPI(
        title=_settings.app_name,
        version=_settings.app_version,
        description=(
            "Production-ready FastAPI backend for the **Autonomous Data Scientist** platform.\n\n"
            "All responses follow the `ResponseEnvelope` schema: `success`, `data`, `error`, `meta`."
        ),
        openapi_url="/openapi.json",
        docs_url="/docs",           # Swagger UI
        redoc_url="/redoc",         # ReDoc UI
        debug=_settings.debug,
        lifespan=lifespan,
        # OpenAPI contact and license metadata
        contact={
            "name": "Autonomous Data Scientist Team",
            "url": "https://github.com/your-org/autonomous-data-scientist",
            "email": "team@example.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        # Group tags with descriptions for nicer Swagger docs
        openapi_tags=[
            {
                "name": "Health",
                "description": "Liveness and readiness probe endpoints for container orchestrators.",
            },
        ],
    )

    # ── CORS middleware ───────────────────────────────────────────────────────
    # Must be the outermost middleware so OPTIONS pre-flight requests are
    # handled before any authentication / logging logic runs.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.allowed_origins,
        allow_credentials=_settings.allow_credentials,
        allow_methods=_settings.allowed_methods,
        allow_headers=_settings.allowed_headers,
        expose_headers=["X-Correlation-ID"],  # expose our custom header to browsers
    )

    # ── Custom middleware ─────────────────────────────────────────────────────
    # Registered in reverse execution order (last added = outermost wrapper).
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(CorrelationIdMiddleware)

    # ── Exception handlers ────────────────────────────────────────────────────
    application.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    application.add_exception_handler(RequestValidationError, request_validation_exception_handler)  # type: ignore[arg-type]
    application.add_exception_handler(Exception, unhandled_exception_handler)

    # ── Routers ───────────────────────────────────────────────────────────────
    # Health probes are mounted at the root (no /api/v1 prefix) so
    # Kubernetes probes don't need to know the API version.
    application.include_router(health.router)

    # Future versioned routers go here:
    # application.include_router(users.router, prefix=_settings.api_v1_prefix)
    # application.include_router(datasets.router, prefix=_settings.api_v1_prefix)

    return application


# ---------------------------------------------------------------------------
# Module-level app instance (used by gunicorn / uvicorn)
#
# gunicorn invocation:
#   gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker
#
# uvicorn invocation (development):
#   uvicorn app.main:app --reload
# ---------------------------------------------------------------------------

app: FastAPI = create_app()
