# =============================================================================
# backend/api/schemas/dataset.py
#
# Pydantic schemas for Dataset request/response structures.
# =============================================================================

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from uuid import UUID

class DatasetResponse(BaseModel):
    """
    Response schema representing an uploaded dataset.
    """
    id: UUID = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="Original filename")
    source_type: str = Field(..., description="Type of upload (e.g., file_upload)")
    storage_uri: str = Field(..., description="Path where the file is stored")
    file_size_bytes: int = Field(..., description="Size of the uploaded file in bytes")
    project_id: UUID = Field(..., description="The project this dataset belongs to")
    
    model_config = ConfigDict(from_attributes=True)
