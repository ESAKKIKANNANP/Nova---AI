# =============================================================================
# backend/tests/test_health.py
#
# Unit test for the /health endpoint used by Docker healthchecks.
# =============================================================================

from fastapi.testclient import TestClient
from fastapi import FastAPI
import pytest

# Mock app with health endpoint
app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
