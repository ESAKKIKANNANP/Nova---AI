# =============================================================================
# app/middleware/request_logging.py
#
# Structured HTTP access-log middleware.
#
# What it logs (one JSON record per request):
#   {
#     "event":          "http_request",
#     "method":         "GET",
#     "path":           "/api/v1/items",
#     "status_code":    200,
#     "duration_ms":    12.4,
#     "correlation_id": "abc-123",   ← from CorrelationIdMiddleware
#     "client_ip":      "1.2.3.4",
#     "user_agent":     "curl/8.0",
#     "level":          "info",
#     "timestamp":      "2024-06-01T12:00:00Z"
#   }
#
# Design notes:
#   - Uses Python's `time.perf_counter_ns()` for sub-millisecond timing.
#   - Log level escalates to WARNING for 4xx, ERROR for 5xx.
#   - Health probe paths (/health, /readiness) are suppressed at DEBUG level
#     to avoid flooding logs in environments with frequent probes.
#   - Exceptions during processing are re-raised after logging so FastAPI's
#     exception handlers can still return the correct JSON error.
# =============================================================================

from __future__ import annotations

import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# Paths that generate too much noise at INFO (e.g. Kubernetes liveness probes).
_SUPPRESS_PATHS: frozenset[str] = frozenset({"/health", "/readiness"})

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that emits a structured log record for every request.

    Registration order in main.py:
        1. CorrelationIdMiddleware  (must run first to bind correlation_id)
        2. RequestLoggingMiddleware (reads correlation_id from contextvars)

    The middleware measures wall-clock time around `call_next()` so the
    `duration_ms` field includes all downstream middleware and route time.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_ns = time.perf_counter_ns()

        # Extract request metadata before calling the handler so it's
        # available even if the handler raises an exception.
        method = request.method
        path = request.url.path
        client_ip = (request.client.host if request.client else "unknown")
        user_agent = request.headers.get("user-agent", "")

        try:
            response: Response = await call_next(request)
        except Exception:
            # Log the error and re-raise — the exception handlers in main.py
            # will convert it to a structured JSON response.
            duration_ms = _elapsed_ms(start_ns)
            logger.error(
                "http_request",
                method=method,
                path=path,
                status_code=500,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise

        duration_ms = _elapsed_ms(start_ns)
        status_code = response.status_code

        # Choose log level based on HTTP status code.
        if status_code >= 500:
            log_fn = logger.error
        elif status_code >= 400:
            log_fn = logger.warning
        elif path in _SUPPRESS_PATHS:
            # Probe endpoints: log at DEBUG to keep INFO logs signal-only.
            log_fn = logger.debug
        else:
            log_fn = logger.info

        log_fn(
            "http_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 3),
            client_ip=client_ip,
            user_agent=user_agent,
        )

        return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _elapsed_ms(start_ns: int) -> float:
    """Return elapsed time in milliseconds since `start_ns` (nanoseconds)."""
    return (time.perf_counter_ns() - start_ns) / 1_000_000
