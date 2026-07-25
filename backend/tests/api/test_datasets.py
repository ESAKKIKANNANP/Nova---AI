# =============================================================================
# backend/tests/api/test_datasets.py
#
# Unit tests for the dataset upload endpoint.
# =============================================================================

import os
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from pathlib import Path

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_upload_dataset_success(async_client):
    """Test successful dataset upload with a valid CSV."""
    project_id = str(uuid.uuid4())
    
    # Create a dummy CSV file payload
    file_content = b"col1,col2\n1,2\n3,4"
    files = {"file": ("test_data.csv", file_content, "text/csv")}
    data = {"project_id": project_id}
    
    response = await async_client.post("/api/v1/datasets/upload", files=files, data=data)
    
    assert response.status_code == 201
    resp_json = response.json()
    
    assert "id" in resp_json
    assert resp_json["name"] == "test_data.csv"
    assert resp_json["source_type"] == "file_upload"
    assert resp_json["file_size_bytes"] == len(file_content)
    assert resp_json["project_id"] == project_id
    assert "uploads" in resp_json["storage_uri"]
    
    # Cleanup file
    if os.path.exists(resp_json["storage_uri"]):
        os.remove(resp_json["storage_uri"])

@pytest.mark.asyncio
async def test_upload_dataset_invalid_extension(async_client):
    """Test uploading a file with an unsupported extension."""
    project_id = str(uuid.uuid4())
    
    file_content = b"invalid data"
    files = {"file": ("test_script.py", file_content, "text/x-python")}
    data = {"project_id": project_id}
    
    response = await async_client.post("/api/v1/datasets/upload", files=files, data=data)
    
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]
