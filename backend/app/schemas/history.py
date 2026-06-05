"""Schemas for the history router."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HistorySessionResponse(BaseModel):
    """Summary of a past learning session for the history list."""

    id: str
    type: str
    title: Optional[str] = None
    source_filename: Optional[str] = None
    status: str
    knowledge_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HistoryListResponse(BaseModel):
    """Paginated history list."""

    items: list[HistorySessionResponse]
    total: int
    page: int
    page_size: int


class HistoryStatsResponse(BaseModel):
    """Aggregated learning statistics."""

    total_sessions: int
    learn_sessions: int
    chat_sessions: int
    document_sessions: int
    total_knowledge_points: int
    total_messages: int
