# =============================================================================
# backend/models/project.py
#
# Project model representing workspaces of analysis.
# =============================================================================

from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.user import User
    from models.dataset import Dataset
    from models.pipeline_run import PipelineRun
    from models.model_artifact import ModelArtifact
    from models.report import Report
    from models.chat_history import ChatHistory


class Project(Base):
    """
    Project model representing isolated analytical workspaces/folders.
    Organizes datasets, runs, models, reports, and logs.
    """
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="Name of the project workspace.",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed description of the project goals and context.",
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key pointing to the user who owns this project.",
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
        doc="The User who owns this project.",
    )

    datasets: Mapped[List["Dataset"]] = relationship(
        "Dataset",
        back_populates="project",
        cascade="all, delete-orphan",
        doc="Datasets attached to this project.",
    )

    pipeline_runs: Mapped[List["PipelineRun"]] = relationship(
        "PipelineRun",
        back_populates="project",
        cascade="all, delete-orphan",
        doc="Analysis runs triggered under this project.",
    )

    models: Mapped[List["ModelArtifact"]] = relationship(
        "ModelArtifact",
        back_populates="project",
        cascade="all, delete-orphan",
        doc="Trained model artifacts under this project.",
    )

    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="project",
        cascade="all, delete-orphan",
        doc="Narrative reports generated in this project.",
    )

    chat_histories: Mapped[List["ChatHistory"]] = relationship(
        "ChatHistory",
        back_populates="project",
        cascade="all, delete-orphan",
        doc="Conversational history threads for this project.",
    )
