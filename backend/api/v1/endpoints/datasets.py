# =============================================================================
# backend/api/v1/endpoints/datasets.py
#
# Dataset upload endpoints.
# =============================================================================

import uuid
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, Depends, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.dataset import DatasetResponse
from services.dataset_service import DatasetService

from db.session import get_async_db

router = APIRouter(prefix="/datasets", tags=["Datasets"])

UPLOADED_DATASETS: dict[str, dict[str, str]] = {}

@router.post(
    "/upload", 
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a dataset file",
    description="Uploads a CSV, Excel, or Parquet file, validates it, stores it to disk, and saves metadata to PostgreSQL."
)
async def upload_dataset(
    file: Annotated[UploadFile, File(...)],
    project_id: Annotated[uuid.UUID | None, Form()] = None,
    db_session: AsyncSession = Depends(get_async_db)
):
    """
    Handle file upload endpoint.
    
    - **file**: The file to upload.
    - **project_id**: UUID of the project this dataset belongs to.
    """
    dataset = await DatasetService.process_file_upload(
        file=file,
        project_id=project_id or uuid.uuid4(),
        db_session=db_session
    )
    UPLOADED_DATASETS[str(dataset.id)] = {
        "id": str(dataset.id),
        "name": dataset.name,
        "storage_uri": dataset.storage_uri,
        "project_id": str(dataset.project_id),
    }
    return dataset
