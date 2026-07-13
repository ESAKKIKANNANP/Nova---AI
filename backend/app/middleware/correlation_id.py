# =============================================================================
# app/middleware/correlation_id.py
#
# Correlation-ID propagation middleware.
#
# What it does:
#   1. On every incoming request, reads the `X-Correlation-ID` header.
#   2. If the header is absent, generates a new UUID4.
#   3. Binds the ID to structlog's contextvars store so every log record
#      emitted during the request lifecycle automatically includes it.
#   4. Injects the ID into the response headers so clients and API gateways
#      can correlate requests end-to-end.
#
# Why correlation IDs matter:
#   - Distributed systems: trace a single user request across multiple
#     microservices by forwarding X-Correlation-ID downstream.
#   - Debugging: grep logs by correlation_id to see the full story of a
#     single request without cross-contamination from other requests.
#   - Support: give clients the correlation_id so they can share it when
#     reporting issues.
#
# Structlog contextvars:
#   structlog.contextvars are async-task-local (backed by contextvars.Context).
#   This means the correlation_id bound here is isolated to the current
#   request's async execution context — concurrent requests get their own IDs.
# =============================================================================

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# The header name clients should send / receive.
CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that attaches a correlation ID to every request.

    Registration (in main.py):
        app.add_middleware(CorrelationIdMiddleware)

    The middleware runs AFTER CORS and BEFORE route handlers, so every
    structured log record produced by a route already has `correlation_id`.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger = structlog.get_logger(__name__)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # ── 1. Resolve or generate the correlation ID ─────────────────────────
        correlation_id: str = (
            request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())
        )

        # ── 2. Bind to structlog contextvars ──────────────────────────────────
        # `clear_contextvars` resets any IDs leftover from a previous request
        # in the same async task (relevant when tasks are reused from a pool).
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # ── 3. Also expose on the request state so middleware / routes can
        #       read it without going through structlog ──────────────────────
        request.state.correlation_id = correlation_id

        # ── 4. Call the next middleware / route handler ────────────────────────
        response: Response = await call_next(request)

        # ── 5. Inject the ID into the response so clients can reference it ─────
        response.headers[CORRELATION_ID_HEADER] = correlation_id

        return response
