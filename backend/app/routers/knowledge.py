"""Knowledge router — CRUD for knowledge points with list/search."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import KnowledgePoint
from app.schemas.knowledge import (
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeResponse,
    KnowledgeListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("", response_model=KnowledgeListResponse)
async def list_knowledge(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
):
    """List knowledge points with optional search and filtering."""
    base_query = select(KnowledgePoint)
    count_query = select(func.count(KnowledgePoint.id))

    if search:
        pattern = f"%{search}%"
        base_query = base_query.where(
            KnowledgePoint.title.ilike(pattern)
            | KnowledgePoint.content.ilike(pattern)
        )
        count_query = count_query.where(
            KnowledgePoint.title.ilike(pattern)
            | KnowledgePoint.content.ilike(pattern)
        )

    if session_id:
        base_query = base_query.where(KnowledgePoint.session_id == session_id)
        count_query = count_query.where(KnowledgePoint.session_id == session_id)

    if category:
        base_query = base_query.where(KnowledgePoint.category == category)
        count_query = count_query.where(KnowledgePoint.category == category)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated items
    offset = (page - 1) * page_size
    items_result = await db.execute(
        base_query.order_by(KnowledgePoint.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = items_result.scalars().all()

    return KnowledgeListResponse(
        items=[KnowledgeResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    knowledge_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single knowledge point by ID."""
    result = await db.execute(
        select(KnowledgePoint).where(KnowledgePoint.id == knowledge_id)
    )
    kp = result.scalar_one_or_none()
    if kp is None:
        raise HTTPException(status_code=404, detail="Knowledge point not found")
    return kp


@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    knowledge_id: str,
    update: KnowledgeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a knowledge point. Only supplied fields are changed."""
    result = await db.execute(
        select(KnowledgePoint).where(KnowledgePoint.id == knowledge_id)
    )
    kp = result.scalar_one_or_none()
    if kp is None:
        raise HTTPException(status_code=404, detail="Knowledge point not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(kp, field, value)

    await db.commit()
    await db.refresh(kp)
    return kp


@router.delete("/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a knowledge point by ID."""
    result = await db.execute(
        select(KnowledgePoint).where(KnowledgePoint.id == knowledge_id)
    )
    kp = result.scalar_one_or_none()
    if kp is None:
        raise HTTPException(status_code=404, detail="Knowledge point not found")

    await db.delete(kp)
    await db.commit()
    return {"detail": "Knowledge point deleted", "id": knowledge_id}
