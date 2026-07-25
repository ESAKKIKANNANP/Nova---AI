# =============================================================================
# backend/api/v1/endpoints/rag.py
#
# FastAPI endpoints for document upload to the RAG knowledge base.
# =============================================================================

import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.rag_service import RAGService

router = APIRouter()
UPLOAD_DIR = "uploads/rag_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads a document (PDF, DOCX, TXT, CSV, MD) to be chunked and stored in the ChromaDB knowledge base.
    """
    valid_extensions = [".pdf", ".docx", ".txt", ".csv", ".md"]
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in valid_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type '{ext}'. Supported types: {', '.join(valid_extensions)}"
        )
        
    # Save file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Process through RAG service
    rag_service = RAGService()
    try:
        chunks_added = rag_service.ingest_document(file_path, metadata={"source": file.filename})
    except Exception as e:
        # Cleanup on failure
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")
        
    return {
        "filename": file.filename,
        "message": f"Successfully vectorized document.",
        "chunks_added": chunks_added
    }
