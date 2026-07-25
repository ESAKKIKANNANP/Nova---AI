# =============================================================================
# backend/models/chat_history.py
#
# ChatHistory model tracking conversational history inside project workspaces.
# =============================================================================

from typing import TYPE_CHECKING, Optional, Dict, Any
import uuid

from sqlalchemy import ForeignKey, String, Text, JSON
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.project import Project


class ChatHistory(Base):
    """
    ChatHistory model representing conversation history messages.
    Stores messages between the user and the Autonomous Data Scientist agent.
    """
    __tablename__ = "chat_histories"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        nullable=False,
        index=True,
        doc="UUID grouping a sequence of messages into a single chat session/tab.",
    )

    sender: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Identifies who sent the message (e.g. user, agent, system).",
    )

    message_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Raw text message or query.",
    )

    additional_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Metadata for advanced rendering (e.g. chart specifications, suggested questions, state updates).",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key reference to the project containing this chat history.",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="chat_histories",
        doc="The project workspace containing this chat thread.",
    )
