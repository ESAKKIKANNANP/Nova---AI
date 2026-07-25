# =============================================================================
# backend/tests/test_monitoring.py
#
# Unit tests for observability and monitoring endpoints.
# =============================================================================

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_prometheus_metrics_endpoint():
    """Verify that the /metrics endpoint is exposed and returning Prometheus data."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
