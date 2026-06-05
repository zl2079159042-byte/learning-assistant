"""History router — GET paginated sessions with type filter and GET /stats with counts."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import LearningSession, KnowledgePoint, ChatMessage
from app.schemas.history import (
    HistorySessionResponse,
    HistoryListResponse,
    HistoryStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
async def list_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    type: Optional[str] = Query(
        None,
        alias="type",
        description="Filter by session type: learn / chat / document",
    ),
    db: AsyncSession = Depends(get_db),
):
    """List past learning sessions with pagination and optional type filter."""
    base_query = select(LearningSession).order_by(LearningSession.updated_at.desc())
    count_query = select(func.count(LearningSession.id))

    if type:
        base_query = base_query.where(LearningSession.type == type)
        count_query = count_query.where(LearningSession.type == type)

    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginated items
    offset = (page - 1) * page_size
    items_result = await db.execute(base_query.offset(offset).limit(page_size))
    items = items_result.scalars().all()

    return HistoryListResponse(
        items=[HistorySessionResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=HistoryStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated learning statistics."""
    # Total sessions
    total_sessions_result = await db.execute(
        select(func.count(LearningSession.id))
    )
    total_sessions = total_sessions_result.scalar() or 0

    # Sessions by type
    learn_count_result = await db.execute(
        select(func.count(LearningSession.id)).where(
            LearningSession.type == "learn"
        )
    )
    learn_sessions = learn_count_result.scalar() or 0

    chat_count_result = await db.execute(
        select(func.count(LearningSession.id)).where(
            LearningSession.type == "chat"
        )
    )
    chat_sessions = chat_count_result.scalar() or 0

    doc_count_result = await db.execute(
        select(func.count(LearningSession.id)).where(
            LearningSession.type == "document"
        )
    )
    document_sessions = doc_count_result.scalar() or 0

    # Total knowledge points
    kp_result = await db.execute(select(func.count(KnowledgePoint.id)))
    total_knowledge_points = kp_result.scalar() or 0

    # Total chat messages
    msg_result = await db.execute(select(func.count(ChatMessage.id)))
    total_messages = msg_result.scalar() or 0

    return HistoryStatsResponse(
        total_sessions=total_sessions,
        learn_sessions=learn_sessions,
        chat_sessions=chat_sessions,
        document_sessions=document_sessions,
        total_knowledge_points=total_knowledge_points,
        total_messages=total_messages,
    )
