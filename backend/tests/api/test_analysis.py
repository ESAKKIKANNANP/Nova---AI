# =============================================================================
# backend/tests/api/test_analysis.py
#
# Unit tests for the analysis endpoints.
# =============================================================================

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from main import app
from services.pipeline_service import PipelineService
from graphs.checkpointers.postgres_checkpointer import get_memory_checkpointer
from api.v1.endpoints.analysis import get_pipeline_service

# Use a globally shared mock service so background tasks mutate the same checkpointer the GET requests read.
shared_memory_checkpointer = get_memory_checkpointer()
shared_pipeline_service = PipelineService(checkpointer=shared_memory_checkpointer)

def override_get_pipeline_service():
    return shared_pipeline_service

app.dependency_overrides[get_pipeline_service] = override_get_pipeline_service

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_trigger_analysis(async_client):
    """Test that POST /analyze returns 202 and starts the job."""
    project_id = str(uuid.uuid4())
    req_data = {
        "dataset_id": "ds-123",
        "project_id": project_id,
        "user_goal": "Test analysis"
    }
    
    response = await async_client.post("/api/v1/analyze", json=req_data)
    assert response.status_code == 202
    assert response.json()["job_id"] == project_id
    assert response.json()["status"] == "queued"

@pytest.mark.asyncio
async def test_get_analysis_status_and_report(async_client):
    """Test polling status and getting the report."""
    project_id = str(uuid.uuid4())
    
    # 1. Trigger job
    req_data = {
        "dataset_id": "ds-456",
        "project_id": project_id,
        "user_goal": "Run fast analysis"
    }
    await async_client.post("/api/v1/analyze", json=req_data)
    
    # Note: Because BackgroundTasks in TestClient run synchronously after the response is returned,
    # the state will actually be populated immediately in the checkpointer!
    
    # 2. Poll Status until complete
    import anyio
    status_data = {}
    for _ in range(50):
        status_resp = await async_client.get(f"/api/v1/analyze/{project_id}/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        if status_data.get("is_complete"):
            break
        await anyio.sleep(0.1)
        
    assert status_data["job_id"] == project_id
    assert status_data["current_node"] == "problem_detection_node"
    assert status_data["is_complete"] is True
    
    # 3. Get Report
    report_resp = await async_client.get(f"/api/v1/analyze/{project_id}/report")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["job_id"] == project_id
    assert "artifacts" in report_data
