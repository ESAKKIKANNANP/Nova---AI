# =============================================================================
# backend/services/dataset_service.py
#
# Business logic for processing dataset uploads, validating files,
# writing to disk, and persisting metadata to PostgreSQL.
# =============================================================================

import os
import shutil
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.dataset import Dataset

log = logging.getLogger(__name__)

# Constants for validation
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".parquet"}
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB limit
UPLOAD_DIR = Path("uploads")

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class DatasetService:
    """
    Service handling dataset ingestion and database persistence.
    """
    
    @staticmethod
    async def process_file_upload(
        file: UploadFile,
        project_id: uuid.UUID,
        db_session: AsyncSession
    ) -> Dataset:
        """
        Validates the file, saves it to disk, and creates a Dataset record.
        
        Args:
            file: The uploaded file from FastAPI.
            project_id: The UUID of the project this dataset belongs to.
            db_session: Active SQLAlchemy async session.
            
        Returns:
            The created Dataset SQLAlchemy model.
        """
        log.info("Processing dataset upload", extra={
            "file_name": file.filename,
            "project_id": str(project_id)
        })
        
        # 1. Validate File Extension
        filename = file.filename or "unknown_file"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            log.warning("Invalid file type attempted", extra={"file_name": filename, "ext": ext})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
            
        # 2. File Size Validation & Saving
        dataset_id = uuid.uuid4()
        safe_filename = f"{dataset_id}{ext}"
        file_path = UPLOAD_DIR / safe_filename
        
        file_size = 0
        try:
            with open(file_path, "wb") as buffer:
                # Read in chunks to avoid blowing up memory and validate size
                while chunk := await file.read(1024 * 1024):  # 1MB chunks
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE_BYTES:
                        log.warning("File exceeded maximum size limit", extra={"max_size": MAX_FILE_SIZE_BYTES})
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds the maximum size limit of {MAX_FILE_SIZE_BYTES / (1024*1024)} MB."
                        )
                    buffer.write(chunk)
        except HTTPException:
            # Clean up partial file if size exceeded
            if file_path.exists():
                file_path.unlink()
            raise
        except Exception as e:
            log.error("Error saving file to disk", extra={"error": str(e)})
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save uploaded file."
            )
            
        log.info("File saved successfully", extra={"path": str(file_path), "size": file_size})
        
        # 3. Save Metadata to PostgreSQL
        try:
            dataset = Dataset(
                id=dataset_id,
                name=filename,
                source_type="file_upload",
                storage_uri=str(file_path.absolute()),
                file_size_bytes=file_size,
                project_id=project_id
            )
            db_session.add(dataset)
            await db_session.commit()
            await db_session.refresh(dataset)
            log.info("Dataset record created", extra={"dataset_id": str(dataset.id)})
            return dataset
            
        except Exception as e:
            log.error("Database error during dataset creation", extra={"error": str(e)})
            await db_session.rollback()
            if file_path.exists():
                file_path.unlink()  # Rollback file creation
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save dataset metadata to the database."
            )
