# =============================================================================
# backend/tests/test_e2e_integration.py
#
# End-to-End integration test covering the entire AI pipeline:
# Upload -> Planner -> Analyzer -> Cleaning -> EDA -> Problem Detection -> End
# =============================================================================

import pytest
import uuid
import time
import os
from httpx import AsyncClient, ASGITransport
from main import app
from services.pipeline_service import PipelineService
from graphs.checkpointers.postgres_checkpointer import get_memory_checkpointer
from api.v1.endpoints.analysis import get_pipeline_service

# Use shared memory checkpointer for E2E
shared_checkpointer = get_memory_checkpointer()
shared_pipeline_service = PipelineService(checkpointer=shared_checkpointer)

def override_pipeline():
    return shared_pipeline_service

app.dependency_overrides[get_pipeline_service] = override_pipeline

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_full_pipeline_e2e(client):
    """
    Simulates a full user journey.
    """
    # 1. Ensure test dataset exists
    dataset_path = os.path.join(os.path.dirname(__file__), "fixtures", "customer_churn.csv")
    assert os.path.exists(dataset_path), "Test dataset missing. Run generate_test_data.py"

    project_id = str(uuid.uuid4())
    
    # 2. Trigger Analysis (mimicking frontend /analyze call)
    req_data = {
        "dataset_id": "churn-123",
        "project_id": project_id,
        "user_goal": "Predict customer churn"
    }
    
    start_time = time.time()
    
    trigger_resp = await client.post("/api/v1/analyze", json=req_data)
    assert trigger_resp.status_code == 202
    
    # 3. Poll for status until the background task completes
    import anyio
    status_data = {}
    for _ in range(50):
        status_resp = await client.get(f"/api/v1/analyze/{project_id}/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        if status_data.get("is_complete"):
            break
        await anyio.sleep(0.1)
        
    assert status_data["job_id"] == project_id
    assert status_data["is_complete"] is True
    
    # 4. Verify routing graph execution
    # Ensure it passed the is_dataset_valid condition and reached Problem Detection
    assert status_data["current_node"] == "problem_detection_node"
    
    # 5. Fetch Final Report
    report_resp = await client.get(f"/api/v1/analyze/{project_id}/report")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    
    end_time = time.time()
    
    print(f"\n[E2E] Pipeline completed successfully in {end_time - start_time:.2f} seconds.")
    print(f"[E2E] Reached Node: {status_data['current_node']}")
