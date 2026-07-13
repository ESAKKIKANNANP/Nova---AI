# =============================================================================
# app/schemas/health.py
#
# Pydantic models for the /health and /readiness endpoints.
#
# Keeping health-check schemas in a dedicated module makes it easy to:
#   - Extend readiness checks (add DB, cache, message-broker status) without
#     touching the router.
#   - Write precise type-checked tests against the response shape.
#   - Have OpenAPI generate accurate docs for the probe endpoints.
# =============================================================================

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    """Overall system health status."""
    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class DependencyStatus(StrEnum):
    """Status of a single external dependency."""
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"


class DependencyHealth(BaseModel):
    """
    Health information for a single external dependency (DB, cache, etc.).

    When adding a real dependency check (e.g. Postgres), instantiate this
    model inside `routers/health.py::readiness()` and append it to the
    `dependencies` list.
    """

    name: str = Field(description="Human-readable dependency name.", examples=["postgres"])
    status: DependencyStatus = Field(description="Whether this dependency is reachable.")
    latency_ms: float | None = Field(
        default=None,
        description="Round-trip latency in milliseconds (null if check was skipped).",
        examples=[3.2],
    )
    error: str | None = Field(
        default=None,
        description="Error message if the dependency is DOWN (null otherwise).",
    )


class HealthResponse(BaseModel):
    """
    Response model for the GET /health liveness probe.

    Kubernetes uses this endpoint to determine whether to restart the pod.
    Return 200 as long as the process is alive, even if dependencies are down.
    """

    status: HealthStatus = Field(
        description="Overall liveness status.",
        examples=[HealthStatus.OK],
    )
    service: str = Field(
        description="Name of this service.",
        examples=["Autonomous Data Scientist API"],
    )
    version: str = Field(
        description="Deployed application version.",
        examples=["0.1.0"],
    )
    timestamp: datetime = Field(
        description="UTC timestamp of this response.",
    )


class ReadinessResponse(BaseModel):
    """
    Response model for the GET /readiness readiness probe.

    Kubernetes uses this endpoint to decide whether to route traffic to the
    pod.  Returns 200 only when ALL required dependencies are healthy.

    The `dependencies` list is empty in this scaffold — add your real
    checks (Postgres ping, Redis ping, etc.) in the readiness route.
    """

    status: HealthStatus = Field(
        description="Overall readiness status.",
        examples=[HealthStatus.OK],
    )
    service: str = Field(
        description="Name of this service.",
        examples=["Autonomous Data Scientist API"],
    )
    version: str = Field(
        description="Deployed application version.",
        examples=["0.1.0"],
    )
    timestamp: datetime = Field(
        description="UTC timestamp of this response.",
    )
    dependencies: list[DependencyHealth] = Field(
        default_factory=list,
        description="Health status of each external dependency.",
    )
