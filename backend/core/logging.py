# =============================================================================
# core/logging.py
#
# Structured logging for the Autonomous Data Scientist backend.
#
# Why structlog?
# ──────────────
# Standard library ``logging`` emits flat text strings — fine for humans
# reading a terminal, but painful for log-aggregation systems (Loki, CloudWatch,
# Datadog) that expect JSON with queryable fields.  ``structlog`` solves this
# by routing every log call through a configurable processor pipeline that can
# output either colourised console text (development) or compact JSON
# (production / staging).
#
# Integration points
# ──────────────────
# 1. ``configure_logging(settings)`` — called ONCE at application startup
#    (in ``app/main.py`` lifespan / ``create_app``).
# 2. ``get_logger(name)`` — returns a bound logger with ``name`` pre-filled;
#    each module calls this at import time.
# 3. ``get_graph_logger(session_id, node)`` — returns a logger pre-bound with
#    LangGraph context fields; called at the top of every LangGraph node.
# 4. ``LoggingMiddleware`` — ASGI middleware that injects a correlation ID
#    into every request's structlog context so all log lines for a single HTTP
#    request share the same ``request_id`` field.
#
# Processor pipeline (development)
# ─────────────────────────────────
#   TimeStamper → add_log_level → add_logger_name → CallsiteParameter
#   → ConsoleRenderer (with colours)
#
# Processor pipeline (production / JSON)
# ───────────────────────────────────────
#   TimeStamper → add_log_level → add_logger_name → CallsiteParameter
#   → JSONRenderer
# =============================================================================

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

import structlog
from structlog.types import EventDict, Processor

if TYPE_CHECKING:
    from config import Settings


# ---------------------------------------------------------------------------
# Public logger factory functions
# ---------------------------------------------------------------------------

def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """
    Return a structlog ``BoundLogger`` bound with a ``logger`` field.

    Call at module level::

        log = get_logger(__name__)
        log.info("dataset_loaded", path="/data/iris.csv", rows=150)

    Args:
        name: Typically ``__name__``; used as the ``logger`` field in output.

    Returns:
        A structlog bound logger ready to emit structured events.
    """
    return structlog.get_logger(name or __name__)


def get_graph_logger(
    session_id: str,
    node_name: str,
    *,
    user_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> structlog.BoundLogger:
    """
    Return a logger pre-bound with LangGraph node context.

    Every LangGraph node should call this at its top level so that every
    log emitted by that node automatically includes ``session_id`` and
    ``node_name`` fields — making log queries trivial::

        logger = get_graph_logger(state["session_id"], "eda_node")
        logger.info("eda_started", row_count=1000)
        # → {"event": "eda_started", "session_id": "...", "node": "eda_node", ...}

    Args:
        session_id: LangGraph session / thread identifier.
        node_name:  Name of the current graph node.
        user_id:    Optional user identifier for correlation.
        extra:      Additional key-value pairs to bind.

    Returns:
        A structlog bound logger with graph context pre-attached.
    """
    bound: dict[str, Any] = {
        "session_id": session_id,
        "node": node_name,
    }
    if user_id:
        bound["user_id"] = user_id
    if extra:
        bound.update(extra)

    return structlog.get_logger(__name__).bind(**bound)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def configure_logging(settings: "Settings") -> None:
    """
    Configure structlog and the stdlib ``logging`` module.

    This must be called exactly **once**, at application startup, before any
    loggers are used.  Calling it multiple times is safe but redundant.

    Architecture
    ────────────
    structlog is configured to act as the *frontend* processor pipeline.
    Stdlib ``logging`` is the *backend* handler (writes to stdout).  The two
    are bridged by ``structlog.stdlib.ProcessorFormatter`` so that third-party
    libraries that use ``logging.getLogger()`` also produce structured output.

    Args:
        settings: The application ``Settings`` instance.  Controls
                  ``log_level`` and ``log_format``.
    """
    log_level_str: str   = settings.log_level.value    # e.g. "INFO"
    is_json: bool        = settings.log_format.value == "json"

    # ── Shared processors (run for every event) ──────────────────────────────
    shared_processors: list[Processor] = [
        # Add ISO-8601 timestamp as "timestamp" key
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Add log level as "level" key
        structlog.stdlib.add_log_level,
        # Add logger name as "logger" key
        structlog.stdlib.add_logger_name,
        # Add source location (file, function, line) in development
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ) if not is_json else structlog.processors.StackInfoRenderer(),
        # Render exceptions as structured dicts
        structlog.processors.ExceptionRenderer() if is_json
        else structlog.dev.ConsoleRenderer.plain_traceback,
    ]

    # ── structlog renderer (format-specific) ─────────────────────────────────
    renderer: Processor = (
        structlog.processors.JSONRenderer()
        if is_json
        else structlog.dev.ConsoleRenderer(colors=True, sort_keys=False)
    )

    # ── Configure structlog ───────────────────────────────────────────────────
    structlog.configure(
        processors=[
            # Merge stdlib extra fields into the event dict
            structlog.stdlib.merge_contextvars,
            # Allow log-level filtering at the structlog layer
            structlog.stdlib.filter_by_level,
            *shared_processors,
            # Hand off to stdlib for actual I/O
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ── Configure stdlib logging (backend) ───────────────────────────────────
    formatter = structlog.stdlib.ProcessorFormatter(
        # Foreign events (from third-party libs) pass through these processors
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level_str)

    # Silence noisy third-party loggers in production
    if not settings.is_development:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    get_logger(__name__).info(
        "logging_configured",
        level=log_level_str,
        format=settings.log_format.value,
        env=settings.env.value,
    )


# ---------------------------------------------------------------------------
# ASGI Correlation-ID Middleware
# ---------------------------------------------------------------------------

class LoggingMiddleware:
    """
    ASGI middleware that injects a correlation ID into every request's
    structlog context variables.

    Every log line emitted during a request will automatically include a
    ``request_id`` field, making it trivial to find all log lines for a single
    HTTP request in a log aggregation system.

    Usage in ``create_app()``::

        app.add_middleware(LoggingMiddleware)

    The correlation ID is read from the ``X-Request-ID`` header (if present)
    or generated as a new UUID4.  It is also injected into the response
    headers so clients can correlate client-side errors with server logs.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        import uuid

        headers = dict(scope.get("headers", []))
        request_id = (
            headers.get(b"x-request-id", b"").decode()
            or str(uuid.uuid4())
        )

        # Bind request_id into structlog's context vars for this async task
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_with_request_id(message: Any) -> None:
            if message["type"] == "http.response.start":
                headers_list = list(message.get("headers", []))
                headers_list.append(
                    (b"x-request-id", request_id.encode())
                )
                message = {**message, "headers": headers_list}
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            structlog.contextvars.clear_contextvars()
