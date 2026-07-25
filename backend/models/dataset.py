# =============================================================================
# backend/models/dataset.py
#
# Dataset model tracking ingested files and database references.
# =============================================================================

from typing import TYPE_CHECKING, Optional, Dict, Any, List
import uuid

from sqlalchemy import ForeignKey, String, BigInteger, Integer, JSON
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.project import Project
    from models.pipeline_run import PipelineRun


class Dataset(Base):
    """
    Dataset model storing metadata for ingested files, databases, or tables.
    Also records structural schema and summary statistics.
    """
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="Name of the dataset (e.g. customer_churn.csv).",
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of data source (e.g., file_upload, s3, snowflake, postgres).",
    )

    storage_uri: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        doc="Full storage URI/path to access the raw data (e.g. s3://bucket/data.parquet).",
    )

    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        doc="Total file size in bytes.",
    )

    row_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Total number of rows in the dataset.",
    )

    column_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Total number of columns in the dataset.",
    )

    schema_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="JSON structure describing columns, data types, and null counts.",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key reference to the project containing this dataset.",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="datasets",
        doc="The project workspace containing this dataset.",
    )

    pipeline_runs: Mapped[List["PipelineRun"]] = relationship(
        "PipelineRun",
        back_populates="dataset",
        doc="List of pipeline/analysis runs executed using this dataset.",
    )
