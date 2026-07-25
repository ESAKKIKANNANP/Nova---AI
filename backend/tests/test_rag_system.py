# =============================================================================
# backend/tests/test_rag_system.py
#
# Unit tests for the Retrieval-Augmented Generation service and endpoints.
# =============================================================================

import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.v1.endpoints.rag import router
from services.rag_service import RAGService
from langchain_core.documents import Document

app = FastAPI()
app.include_router(router, prefix="/rag")
client = TestClient(app)

@pytest.fixture
def mock_chroma_env(monkeypatch):
    """Mocks out OpenAI and Chroma to prevent actual API calls during tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake_key")

@patch("services.rag_service.OpenAIEmbeddings")
@patch("services.rag_service.Chroma")
def test_rag_service_ingest_and_retrieve(mock_chroma_class, mock_embeddings_class, tmp_path, mock_chroma_env):
    
    mock_chroma_instance = MagicMock()
    mock_chroma_class.return_value = mock_chroma_instance
    
    service = RAGService(persist_directory=str(tmp_path))
    
    # Create a dummy text file
    dummy_txt = tmp_path / "test.txt"
    dummy_txt.write_text("The secret recipe is 42 apples.")
    
    # Test Ingestion
    chunks = service.ingest_document(str(dummy_txt), metadata={"source": "test.txt"})
    assert chunks > 0
    mock_chroma_instance.add_documents.assert_called_once()
    
    # Test Retrieval
    mock_doc = Document(page_content="The secret recipe is 42 apples.", metadata={"source": "test.txt"})
    mock_chroma_instance.similarity_search.return_value = [mock_doc]
    
    results = service.retrieve("What is the secret recipe?")
    assert len(results) == 1
    assert "42 apples" in results[0].page_content

@patch("api.v1.endpoints.rag.RAGService")
def test_rag_upload_endpoint(mock_rag_class, tmp_path, mock_chroma_env):
    mock_rag_instance = MagicMock()
    mock_rag_instance.ingest_document.return_value = 5
    mock_rag_class.return_value = mock_rag_instance
    
    import api.v1.endpoints.rag as rag_api
    rag_api.UPLOAD_DIR = str(tmp_path)
    
    # Create a dummy file for the upload
    dummy_txt = tmp_path / "upload.txt"
    dummy_txt.write_text("Hello World")
    
    with open(dummy_txt, "rb") as f:
        response = client.post("/rag/upload", files={"file": ("upload.txt", f, "text/plain")})
        
    assert response.status_code == 200
    assert response.json()["chunks_added"] == 5
    assert response.json()["filename"] == "upload.txt"
    
    # Test invalid extension
    with open(dummy_txt, "rb") as f:
        response = client.post("/rag/upload", files={"file": ("upload.exe", f, "application/octet-stream")})
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
