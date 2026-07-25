# =============================================================================
# backend/models/report.py
#
# Report model tracking generated analytical outputs and document assets.
# =============================================================================

from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.project import Project
    from models.pipeline_run import PipelineRun


class Report(Base):
    """
    Report model representing generated analytical documents, summaries, and slides.
    Stores metadata and path locations of generated files (PDF, Jupyter notebooks, PPTX).
    """
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Title of the report.",
    )

    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="High-level plain English summary of the report.",
    )

    content_markdown: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="The markdown narrative body of the report.",
    )

    file_format: Mapped[str] = mapped_column(
        String(50),
        default="pdf",
        nullable=False,
        doc="Format of the saved report asset (e.g. pdf, html, docx, ipynb, pptx).",
    )

    storage_uri: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        doc="Full storage path for download (e.g. s3://bucket/reports/report.pdf).",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key reference to the project containing this report.",
    )

    pipeline_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(),
        ForeignKey("pipeline_runs.id", ondelete="SET NULL"),
        nullable=True,
        doc="Foreign key reference to the run that generated this report.",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="reports",
        doc="The project workspace containing this report.",
    )

    pipeline_run: Mapped[Optional["PipelineRun"]] = relationship(
        "PipelineRun",
        back_populates="reports",
        doc="The pipeline run that generated this report.",
    )
