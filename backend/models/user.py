# =============================================================================
# backend/models/user.py
#
# User model representing application users and access management.
# =============================================================================

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.project import Project


class User(Base):
    """
    User model representing individuals within the Autonomous Data Scientist platform.
    Handles authentication, profiling, and workspaces/project ownership.
    """
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique email address used for login and notifications.",
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Salted, bcrypt-hashed password.",
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        doc="Full name of the user.",
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default="analyst",
        nullable=False,
        doc="Access control role (e.g., admin, data_steward, analyst, viewer).",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Flag indicating if the user's account is currently active.",
    )

    # Relationships
    # A user can own multiple projects
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        doc="List of projects owned by this user.",
    )
