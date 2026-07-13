# =============================================================================
# app/routers/health.py
#
# Liveness and readiness probe endpoints.
#
# GET /health   — Liveness probe
#   Returns 200 as long as the Python process is running.
#   Kubernetes restarts the pod if this returns non-2xx.
#   DO NOT add dependency checks here — a temporarily-down DB should not
#   cause Kubernetes to restart a healthy pod.
#
# GET /readiness — Readiness probe
#   Returns 200 only when the application is ready to serve traffic.
#   Kubernetes stops routing traffic to the pod if this returns non-2xx.
#   Add dependency checks (DB ping, Redis ping, etc.) here.
#
# Both endpoints:
#   - Return typed Pydantic response models (documented in OpenAPI).
#   - Include the service name, version, and a UTC timestamp.
#   - Use the `ResponseEnvelope` wrapper for consistency.
# =============================================================================

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, status

from app.config import Settings, get_settings
from app.dependencies import get_logger
from app.schemas.health import (
    DependencyHealth,
    DependencyStatus,
    HealthResponse,
    HealthStatus,
    ReadinessResponse,
)

# ---------------------------------------------------------------------------
# Router setup
# ---------------------------------------------------------------------------

router = APIRouter(tags=["Health"])


# ---------------------------------------------------------------------------
# Liveness probe — GET /health
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description=(
        "Returns `200 OK` as long as the application process is running. "
        "Used by Kubernetes / Docker health checks to decide whether to "
        "**restart** the container.  Do not add dependency checks here."
    ),
    responses={
        200: {"description": "Application is alive."},
    },
)
async def health(
    settings: Annotated[Settings, Depends(get_settings)],
    logger: Annotated[structlog.stdlib.BoundLogger, Depends(get_logger)],
) -> HealthResponse:
    """Return liveness status."""
    logger.debug("health_check_called")
    return HealthResponse(
        status=HealthStatus.OK,
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Readiness probe — GET /readiness
# ---------------------------------------------------------------------------

@router.get(
    "/readiness",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description=(
        "Returns `200 OK` when **all** required dependencies are healthy. "
        "Used by Kubernetes to decide whether to **route traffic** to this "
        "pod.  Add actual dependency checks (DB ping, Redis ping, etc.) "
        "inside this handler as the application grows."
    ),
    responses={
        200: {"description": "Application is ready to serve traffic."},
        503: {"description": "One or more dependencies are unavailable."},
    },
)
async def readiness(
    settings: Annotated[Settings, Depends(get_settings)],
    logger: Annotated[structlog.stdlib.BoundLogger, Depends(get_logger)],
) -> ReadinessResponse:
    """
    Check all external dependencies and return readiness status.

    To add a real dependency check (e.g. Postgres):
        1. Inject the DB session via Depends.
        2. Execute a lightweight query (SELECT 1).
        3. Append a DependencyHealth(...) to `dep_results`.
        4. Set `overall_status = HealthStatus.DEGRADED` if any dep is DOWN.
    """
    dep_results: list[DependencyHealth] = []

    # ── Placeholder: no real dependencies in this scaffold ───────────────────
    # Example of what a Postgres check would look like:
    #
    #   start = time.perf_counter_ns()
    #   try:
    #       await db.execute(text("SELECT 1"))
    #       dep_results.append(DependencyHealth(
    #           name="postgres",
    #           status=DependencyStatus.UP,
    #           latency_ms=(time.perf_counter_ns() - start) / 1_000_000,
    #       ))
    #   except Exception as exc:
    #       dep_results.append(DependencyHealth(
    #           name="postgres",
    #           status=DependencyStatus.DOWN,
    #           error=str(exc),
    #       ))

    # Determine overall status: UNAVAILABLE if any dep is DOWN.
    overall_status = (
        HealthStatus.UNAVAILABLE
        if any(d.status == DependencyStatus.DOWN for d in dep_results)
        else HealthStatus.OK
    )

    http_status = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if overall_status == HealthStatus.UNAVAILABLE
        else status.HTTP_200_OK
    )

    logger.debug("readiness_check_called", overall_status=overall_status)

    from fastapi.responses import JSONResponse
    from pydantic import TypeAdapter

    response_body = ReadinessResponse(
        status=overall_status,
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
        dependencies=dep_results,
    )

    # Return non-200 status codes correctly by using JSONResponse directly
    # when the service is not ready.
    if http_status != status.HTTP_200_OK:
        return JSONResponse(  # type: ignore[return-value]
            status_code=http_status,
            content=response_body.model_dump(mode="json"),
        )

    return response_body
