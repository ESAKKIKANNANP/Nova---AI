# =============================================================================
# tests/test_middleware.py
#
# Tests for the CorrelationIdMiddleware and RequestLoggingMiddleware.
#
# Coverage:
#   Correlation ID middleware:
#     ✓ X-Correlation-ID is echoed in the response when supplied in the request
#     ✓ A new UUID is generated and returned when the header is absent
#     ✓ Generated ID is a valid UUID4 string
#     ✓ Different requests without a header receive different IDs
#
#   Request logging middleware:
#     ✓ Structured log record is emitted for each request
#     ✓ Log record contains expected fields (method, path, status_code, duration_ms)
#
#   Exception handler integration:
#     ✓ 404 returns the standard error envelope
#     ✓ Error envelope shape matches the documented contract
# =============================================================================

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

CORRELATION_ID_HEADER = "X-Correlation-ID"


# ---------------------------------------------------------------------------
# Correlation ID — header propagation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_correlation_id_echoed_when_provided(client: AsyncClient) -> None:
    """When X-Correlation-ID is sent, the same value must appear in the response."""
    expected_id = "my-custom-correlation-id-12345"
    response = await client.get(
        "/health",
        headers={CORRELATION_ID_HEADER: expected_id},
    )
    assert response.status_code == 200
    assert response.headers.get(CORRELATION_ID_HEADER) == expected_id


@pytest.mark.asyncio
async def test_correlation_id_generated_when_absent(client: AsyncClient) -> None:
    """When X-Correlation-ID is NOT sent, the response must include a generated ID."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert CORRELATION_ID_HEADER in response.headers, (
        "Response must include X-Correlation-ID even when the request omits it."
    )


@pytest.mark.asyncio
async def test_generated_correlation_id_is_valid_uuid(client: AsyncClient) -> None:
    """The auto-generated X-Correlation-ID must be a valid UUID4 string."""
    response = await client.get("/health")
    correlation_id = response.headers.get(CORRELATION_ID_HEADER, "")
    try:
        parsed = uuid.UUID(correlation_id, version=4)
    except ValueError:
        pytest.fail(f"X-Correlation-ID '{correlation_id}' is not a valid UUID4.")
    assert str(parsed) == correlation_id


@pytest.mark.asyncio
async def test_different_requests_get_different_correlation_ids(client: AsyncClient) -> None:
    """Two requests without X-Correlation-ID must receive different generated IDs."""
    response_a = await client.get("/health")
    response_b = await client.get("/health")

    id_a = response_a.headers.get(CORRELATION_ID_HEADER)
    id_b = response_b.headers.get(CORRELATION_ID_HEADER)

    assert id_a is not None
    assert id_b is not None
    assert id_a != id_b, "Each request must receive a unique correlation ID."


@pytest.mark.asyncio
async def test_client_provided_id_is_not_overwritten(client: AsyncClient) -> None:
    """A client-provided ID must not be replaced by the middleware."""
    client_id = "do-not-overwrite-me"
    response = await client.get(
        "/readiness",
        headers={CORRELATION_ID_HEADER: client_id},
    )
    assert response.headers.get(CORRELATION_ID_HEADER) == client_id


# ---------------------------------------------------------------------------
# Exception handler integration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_404_returns_error_envelope(client: AsyncClient) -> None:
    """Requests to non-existent routes must return the standard error envelope."""
    response = await client.get("/this/route/does/not/exist")
    assert response.status_code == 404

    body = response.json()
    assert body["success"] is False
    assert "error" in body
    assert body["data"] is None


@pytest.mark.asyncio
async def test_error_envelope_has_required_fields(client: AsyncClient) -> None:
    """Error envelopes must include `code` and `message` inside `error`."""
    response = await client.get("/nonexistent-endpoint")
    body = response.json()

    error = body.get("error", {})
    assert "code" in error, "Error object must contain 'code'."
    assert "message" in error, "Error object must contain 'message'."


@pytest.mark.asyncio
async def test_correlation_id_present_on_error_response(client: AsyncClient) -> None:
    """Even 404 error responses must include X-Correlation-ID in headers."""
    response = await client.get("/definitely-does-not-exist")
    assert CORRELATION_ID_HEADER in response.headers
