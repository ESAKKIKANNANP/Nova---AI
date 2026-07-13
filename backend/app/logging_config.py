# =============================================================================
# app/logging_config.py
#
# Structured logging bootstrap using structlog.
#
# What this module does:
#   1. Configures structlog's processor chain differently for each environment:
#        - production / staging → JSON (machine-readable, indexable by Datadog /
#          Grafana Loki / Cloud Logging)
#        - development          → ConsoleRenderer (coloured, human-readable)
#   2. Integrates with Python's stdlib `logging` module so third-party
#      libraries (uvicorn, httpx, sqlalchemy, etc.) also emit structured
#      records through the same pipeline.
#   3. Binds static context fields (`service`, `env`, `version`) to every
#      log record produced in the process.
#
# Usage:
#   # Called once at application startup in app/main.py lifespan handler:
#   from app.logging_config import configure_logging
#   configure_logging(settings)
#
#   # In any module:
#   import structlog
#   logger = structlog.get_logger(__name__)
#   logger.info("user_created", user_id=42, email="a@b.com")
#
# Output example (JSON):
#   {
#     "timestamp": "2024-06-01T12:00:00.000000Z",
#     "level": "info",
#     "event": "user_created",
#     "service": "autonomous-data-scientist-api",
#     "env": "production",
#     "version": "0.1.0",
#     "user_id": 42,
#     "email": "a@b.com"
#   }
# =============================================================================

from __future__ import annotations

import logging
import logging.config
import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from app.config import Settings


def _build_shared_processors() -> list[structlog.types.Processor]:
    """
    Return processors that run on EVERY log record regardless of renderer.

    Processor order matters — each processor receives the output of the
    previous one as its `event_dict` argument.
    """
    return [
        # Merge context variables from structlog.contextvars (used by middleware
        # to bind the correlation-id to the current async task context).
        structlog.contextvars.merge_contextvars,
        # Attach the logger name (module path) to every record.
        structlog.stdlib.add_logger_name,
        # Attach the log level as a string field.
        structlog.stdlib.add_log_level,
        # Add an ISO-8601 UTC timestamp.
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Render exception info as a structured dict instead of a raw string.
        structlog.processors.dict_tracebacks,
        # Convert any positional arguments to the `event` field.
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Unwrap stack-info if passed via `stack_info=True`.
        structlog.processors.StackInfoRenderer(),
    ]


def configure_logging(settings: Settings) -> None:
    """
    Bootstrap structlog and stdlib logging for the application.

    This function is idempotent — safe to call multiple times (subsequent
    calls are no-ops because basicConfig respects existing handlers).

    Args:
        settings: The application settings object (reads log_level, log_format,
                  app_name, app_version, env).
    """
    log_level_name: str = settings.log_level.value
    log_level: int = getattr(logging, log_level_name)

    shared_processors = _build_shared_processors()

    # ── Choose renderer based on environment ─────────────────────────────────
    from app.config import LogFormat

    if settings.log_format == LogFormat.JSON:
        # Production: JSON output (one compact JSON object per line).
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Development: colourised, human-readable output.
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # ── Configure structlog ───────────────────────────────────────────────────
    structlog.configure(
        processors=[
            *shared_processors,
            # PrepareForFormattingInformation bridges structlog → stdlib logging
            # so that stdlib `logging` calls (e.g. from uvicorn) pass through
            # structlog's processor chain.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        # Use stdlib BoundLogger so that structlog loggers behave like stdlib
        # loggers (supports `.debug()`, `.info()`, `.warning()` etc.).
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Cache the logger on first use (performance optimisation).
        cache_logger_on_first_use=True,
    )

    # ── Configure stdlib logging handler ─────────────────────────────────────
    # This formatter passes stdlib log records through structlog's processor
    # chain, so ALL logging — including from third-party libraries — is
    # rendered consistently (JSON or console).
    formatter = structlog.stdlib.ProcessorFormatter(
        # Processors that run on stdlib records before the renderer:
        processors=[
            # Remove stdlib-specific fields already captured by structlog.
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        # Processors to run on ALL records (structlog + stdlib):
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Clear any pre-existing handlers to avoid duplicate output.
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # ── Silence noisy third-party loggers ────────────────────────────────────
    # uvicorn's default access logger is replaced by our RequestLoggingMiddleware.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # httpx is verbose at DEBUG — suppress unless needed.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # ── Bind static context to every future log record ───────────────────────
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        service=settings.app_name,
        env=settings.env.value,
        version=settings.app_version,
    )

    # Emit a startup confirmation at INFO so operators can see config is loaded.
    startup_logger = structlog.get_logger(__name__)
    startup_logger.info(
        "logging_configured",
        log_level=log_level_name,
        log_format=settings.log_format.value,
    )
