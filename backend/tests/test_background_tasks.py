# =============================================================================
# backend/tests/test_background_tasks.py
#
# Unit tests for ARQ Worker and Task Queue API.
# =============================================================================

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.v1.endpoints.tasks import router

app = FastAPI()
app.include_router(router, prefix="/tasks")
client = TestClient(app)

@pytest.mark.asyncio
@patch("api.v1.endpoints.tasks.get_redis_pool")
async def test_start_pipeline(mock_get_pool):
    # Mock the ARQ Redis pool and job
    mock_redis = AsyncMock()
    mock_job = AsyncMock()
    mock_job.job_id = "test_job_123"
    mock_redis.enqueue_job.return_value = mock_job
    
    mock_get_pool.return_value = mock_redis
    
    response = client.post(
        "/tasks/start-pipeline", 
        json={"session_id": "sess_1", "user_email": "test@example.com"}
    )
    
    assert response.status_code == 200
    assert response.json()["job_id"] == "test_job_123"
    mock_redis.enqueue_job.assert_called_once_with("run_ml_pipeline_task", "sess_1", "test@example.com")

@pytest.mark.asyncio
@patch("api.v1.endpoints.tasks.get_redis_pool")
async def test_get_job_status(mock_get_pool):
    mock_redis = AsyncMock()
    mock_get_pool.return_value = mock_redis
    
    # We must mock arq.jobs.Job since we instantiate it inside the route
    with patch("api.v1.endpoints.tasks.Job") as mock_job_class:
        mock_job_instance = AsyncMock()
        mock_status = type('obj', (object,), {'value': 'complete'})
        mock_job_instance.status.return_value = mock_status
        
        mock_result_info = type('obj', (object,), {'result': {'status': 'success'}})
        mock_job_instance.result_info.return_value = mock_result_info
        
        mock_job_class.return_value = mock_job_instance
        
        response = client.get("/tasks/test_job_123/status")
        
        assert response.status_code == 200
        assert response.json()["status"] == "complete"
        assert response.json()["result"]["status"] == "success"

@pytest.mark.asyncio
@patch("services.email_service.aiosmtplib.send")
async def test_email_service(mock_send, monkeypatch):
    from services.email_service import send_email
    
    # Test valid send
    monkeypatch.setattr("services.email_service.SMTP_USER", "user")
    monkeypatch.setattr("services.email_service.SMTP_HOST", "smtp.example.com")
    mock_send.return_value = (None, None) # aiosmtplib.send returns (dict, str) or similar, but anything is fine for return mock
    
    result = await send_email("test@example.com", "Subj", "Body")
    assert result is True
    mock_send.assert_called_once()
