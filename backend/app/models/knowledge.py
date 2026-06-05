"""KnowledgePoint model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(200))
    tags: Mapped[Optional[str]] = mapped_column(String(1000))
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    review_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    session: Mapped["LearningSession"] = relationship(
        "LearningSession", back_populates="knowledge_points"
    )

    def __repr__(self) -> str:
        return f"<KnowledgePoint(id={self.id!r}, title={self.title!r}, mastery_level={self.mastery_level!r})>"
