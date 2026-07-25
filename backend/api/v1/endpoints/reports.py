# =============================================================================
# backend/api/v1/endpoints/reports.py
#
# Downloadable endpoints for multi-format reports.
# =============================================================================

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

ARTIFACT_DIR = "artifacts/reports"

@router.get("/{session_id}/download")
async def download_report(session_id: str, format: str = "pdf"):
    """
    Downloads the master report for a given session in the requested format.
    Supported formats: pdf, docx, html, md
    """
    valid_formats = ["pdf", "docx", "html", "md"]
    if format not in valid_formats:
        raise HTTPException(status_code=400, detail=f"Invalid format. Must be one of {valid_formats}")
        
    file_name = f"report_{session_id}.{format}"
    file_path = os.path.join(ARTIFACT_DIR, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Report not found for session {session_id} in format {format}")
        
    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "html": "text/html",
        "md": "text/markdown"
    }
    
    return FileResponse(
        path=file_path,
        media_type=media_types[format],
        filename=file_name
    )
