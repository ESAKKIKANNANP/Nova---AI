# =============================================================================
# backend/models/model_artifact.py
#
# ModelArtifact model tracking trained machine learning models.
# =============================================================================

from typing import TYPE_CHECKING, Optional, Dict, Any
import uuid

from sqlalchemy import ForeignKey, String, Boolean, JSON
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.project import Project
    from models.pipeline_run import PipelineRun


class ModelArtifact(Base):
    """
    ModelArtifact model representing a trained ML model (e.g. Random Forest, XGBoost).
    Tracks metadata, metrics, feature importances, and serialization path.
    """
    __tablename__ = "model_artifacts"

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="Human-readable name assigned to the model.",
    )

    algorithm: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Algorithm type (e.g. Random Forest Classifier, LightGBM Regressor).",
    )

    hyperparameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="JSON map of hyperparameter key-value pairs used for training.",
    )

    evaluation_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="JSON map of training and test performance metrics (e.g. F1, RMSE, ROC-AUC).",
    )

    feature_importance: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="JSON map of feature names and their corresponding importance weights.",
    )

    storage_uri: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        doc="URI for access to the serialized model file (e.g. MLflow path, S3 path, pickle, ONNX).",
    )

    is_deployed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Boolean flag indicating if the model has been deployed to a REST endpoint.",
    )

    deployment_endpoint: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        doc="REST URL endpoint where the model is serving real-time predictions.",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key reference to the project containing this model.",
    )

    pipeline_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(),
        ForeignKey("pipeline_runs.id", ondelete="SET NULL"),
        nullable=True,
        doc="Foreign key reference to the pipeline execution run that trained this model.",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="models",
        doc="The project workspace containing this model.",
    )

    pipeline_run: Mapped[Optional["PipelineRun"]] = relationship(
        "PipelineRun",
        back_populates="models",
        doc="The pipeline run that trained this model.",
    )
