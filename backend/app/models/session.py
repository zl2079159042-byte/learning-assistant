"""LearningSession model."""

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class SessionType(str, enum.Enum):
    LEARN = "learn"
    CHAT = "chat"
    DOCUMENT = "document"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    type: Mapped[SessionType] = mapped_column(
        Enum(SessionType), nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(500))
    source_text: Mapped[Optional[str]] = mapped_column(Text)
    source_filename: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), nullable=False, default=SessionStatus.ACTIVE
    )
    knowledge_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    knowledge_points: Mapped[List["KnowledgePoint"]] = relationship(
        "KnowledgePoint",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<LearningSession(id={self.id!r}, type={self.type!r}, title={self.title!r})>"
