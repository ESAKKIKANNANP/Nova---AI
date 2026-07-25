# =============================================================================
# backend/models/base.py
#
# Declarative base class for all SQLAlchemy database models.
# Provides automatic table name generation and standard audited fields.
# =============================================================================

from datetime import datetime, timezone
import uuid
from typing import Any

from sqlalchemy import DateTime, MetaData, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Standard naming convention for database constraints to ensure clean migrations
# and consistent naming in PostgreSQL.
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """
    Common base class for all database models.
    Inherits from SQLAlchemy's DeclarativeBase and uses custom metadata conventions.
    """
    metadata = metadata

    # Automatically generate __tablename__ based on class name in lowercase plural form.
    # (e.g., User -> users, Project -> projects)
    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = cls.__name__.lower()
        if name.endswith("y"):
            return f"{name[:-1]}ies"
        elif name.endswith("s"):
            return f"{name}es"
        return f"{name}s"

    # Common fields for all models
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the record (UUIDv4).",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp of when the record was created (UTC timezone-aware).",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp of when the record was last updated (UTC timezone-aware).",
    )
