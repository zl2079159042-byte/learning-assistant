"""Knowledge service — CRUD with pagination and keyword search.

Provides:
- create_knowledge_point
- get_knowledge_point
- update_knowledge_point
- delete_knowledge_point
- list_knowledge_points  (paginated, keyword-filtered)
"""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func, or_, select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgePoint


# ── schemas (lightweight inline types; can migrate to Pydantic later) ────────


@dataclass
class KnowledgePointCreate:
    """Data required to create a new knowledge point."""

    title: str
    content: str
    category: str | None = None
    tags: str | None = None
    mastery_level: float = 0.0


@dataclass
class KnowledgePointUpdate:
    """Fields that may be updated on an existing knowledge point."""

    title: str | None = None
    content: str | None = None
    category: str | None = None
    tags: str | None = None
    mastery_level: float | None = None


@dataclass
class KnowledgePointListResult:
    """Pagination wrapper returned by list_knowledge_points."""

    items: list[KnowledgePoint]
    total: int
    page: int
    page_size: int


# ── CRUD ─────────────────────────────────────────────────────────────────────


async def create_knowledge_point(
    *,
    db: AsyncSession,
    session_id: str,
    data: KnowledgePointCreate,
) -> KnowledgePoint:
    """Create a single KnowledgePoint and flush it to the database.

    Args:
        db: async database session
        session_id: parent learning session id
        data: creation payload

    Returns:
        the newly persisted KnowledgePoint
    """
    kp = KnowledgePoint(
        session_id=session_id,
        title=data.title,
        content=data.content,
        category=data.category,
        tags=data.tags,
        mastery_level=data.mastery_level,
    )
    db.add(kp)
    await db.flush()
    return kp


async def get_knowledge_point(
    *,
    db: AsyncSession,
    knowledge_point_id: str,
) -> KnowledgePoint | None:
    """Fetch a single knowledge point by primary key.

    Returns ``None`` when the row does not exist.
    """
    stmt = select(KnowledgePoint).where(KnowledgePoint.id == knowledge_point_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_knowledge_point(
    *,
    db: AsyncSession,
    knowledge_point_id: str,
    data: KnowledgePointUpdate,
) -> KnowledgePoint:
    """Partially update a knowledge point.

    Raises:
        ValueError: if the knowledge point does not exist
    """
    kp = await get_knowledge_point(db=db, knowledge_point_id=knowledge_point_id)
    if kp is None:
        raise ValueError(f"KnowledgePoint {knowledge_point_id!r} not found")

    if data.title is not None:
        kp.title = data.title[:500]
    if data.content is not None:
        kp.content = data.content
    if data.category is not None:
        kp.category = data.category
    if data.tags is not None:
        kp.tags = data.tags
    if data.mastery_level is not None:
        kp.mastery_level = data.mastery_level
        kp.review_count += 1

    await db.flush()
    return kp


async def delete_knowledge_point(
    *,
    db: AsyncSession,
    knowledge_point_id: str,
) -> bool:
    """Delete a knowledge point by id.

    Returns:
        ``True`` if a row was deleted, ``False`` if the id did not exist.
    """
    stmt = sa_delete(KnowledgePoint).where(KnowledgePoint.id == knowledge_point_id)
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount > 0  # type: ignore[return-value]


async def list_knowledge_points(
    *,
    db: AsyncSession,
    session_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
) -> KnowledgePointListResult:
    """Return a paginated, optionally filtered list of knowledge points.

    Args:
        db: async database session
        session_id: if given, restrict results to this session
        page: 1-based page number (clamped to >= 1)
        page_size: items per page (clamped to 1..100)
        keyword: if given, filter rows whose title, content, or tags
                 contain the keyword (case-insensitive LIKE)

    Returns:
        KnowledgePointListResult with items, total count, and pagination info
    """
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)

    # ── base query ─────────────────────────────────────────────────────────
    base = select(KnowledgePoint)

    if session_id:
        base = base.where(KnowledgePoint.session_id == session_id)

    if keyword:
        pattern = f"%{keyword}%"
        base = base.where(
            or_(
                KnowledgePoint.title.ilike(pattern),
                KnowledgePoint.content.ilike(pattern),
                KnowledgePoint.tags.ilike(pattern),
            )
        )

    # ── total count ────────────────────────────────────────────────────────
    count_stmt = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # ── paginated rows ─────────────────────────────────────────────────────
    rows_stmt = (
        base.order_by(KnowledgePoint.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows_result = await db.execute(rows_stmt)
    items = list(rows_result.scalars().all())

    return KnowledgePointListResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
