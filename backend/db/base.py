# =============================================================================
# backend/db/base.py
#
# Import all database models here.
# This ensures that when Alembic imports `Base`, it registers all model schemas
# in `Base.metadata` for autogenerate.
# =============================================================================

# Import the Base metadata class
from models.base import Base  # noqa

# Import all models to register them on the Base metadata
from models.user import User  # noqa
from models.project import Project  # noqa
from models.dataset import Dataset  # noqa
from models.pipeline_run import PipelineRun  # noqa
from models.model_artifact import ModelArtifact  # noqa
from models.report import Report  # noqa
from models.chat_history import ChatHistory  # noqa
