"""Learn router — POST /api/learn/analyze (SSE) and GET /api/learn/{id}."""

import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models import LearningSession, KnowledgePoint, SessionType, SessionStatus
from app.prompts import get_system_prompt
from app.schemas.learn import (
    LearnRequest,
    LearnResponse,
    LearnSessionDetail,
    KnowledgePointBrief,
)
from app.services import get_adapter, get_default_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learn", tags=["learn"])


def _parse_knowledge_points(raw_text: str) -> list[dict]:
    """Parse LLM output into a list of knowledge-point dicts.

    Splits on ``---`` separators and extracts title + content from each block.
    Falls back to a single knowledge point if parsing fails.
    """
    blocks = [b.strip() for b in raw_text.split("---") if b.strip()]
    points: list[dict] = []

    for block in blocks:
        lines = block.strip().split("\n")
        title = ""
        start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("## ") or stripped.startswith("## 📌"):
                title = stripped.lstrip("#").lstrip("📌").strip()
                start = i + 1
                break
        if not title:
            # Use first non-empty line as fallback title
            for line in lines:
                if line.strip():
                    title = line.strip().lstrip("#").strip()
                    break
        if not title:
            title = "Untitled"
        content = "\n".join(lines[start:]).strip()
        if not content:
            content = block
        points.append({"title": title[:500], "content": content})

    return points


async def _stream_learn_analysis(
    content: str,
    session: LearningSession,
    db: AsyncSession,
    model: str | None = None,
) -> AsyncIterator[dict]:
    """Stream learn-analysis events as SSE dicts."""
    adapter = get_adapter(model) if model else get_default_adapter()

    messages = [
        {"role": "system", "content": get_system_prompt("learn")},
        {"role": "user", "content": content},
    ]

    full_response = ""

    try:
        async for token in adapter.chat_stream(messages):
            full_response += token
            yield {"data": json.dumps({"type": "token", "data": token})}

        # Parse knowledge points from the full response
        points = _parse_knowledge_points(full_response)

        stored_points = []
        for p in points:
            kp = KnowledgePoint(
                session_id=session.id,
                title=p["title"],
                content=p["content"],
            )
            db.add(kp)
            stored_points.append(kp)

        session.knowledge_count = len(stored_points)
        if not session.title and stored_points:
            session.title = stored_points[0].title

        await db.commit()

        # Emit each knowledge point as an event
        for kp in stored_points:
            await db.refresh(kp)
            yield {
                "data": json.dumps(
                    {
                        "type": "knowledge_point",
                        "data": json.dumps(
                            {
                                "id": kp.id,
                                "title": kp.title,
                                "content": kp.content,
                                "category": kp.category,
                                "tags": kp.tags,
                                "mastery_level": kp.mastery_level,
                                "review_count": kp.review_count,
                            },
                            default=str,
                        ),
                    }
                )
            }

        yield {"data": json.dumps({"type": "done", "data": session.id})}

    except Exception as exc:
        logger.exception("Learn analysis failed for session %s", session.id)
        yield {"data": json.dumps({"type": "error", "data": str(exc)})}


@router.post("/analyze")
async def analyze_learn(
    request: LearnRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze learning material and stream knowledge points via SSE.

    Creates a new learn session (or reuses an existing one) and streams
    tokens followed by parsed knowledge-point events.
    """
    if request.session_id:
        result = await db.execute(
            select(LearningSession)
            .options(selectinload(LearningSession.knowledge_points))
            .where(LearningSession.id == request.session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        # Append new content
        existing = session.source_text or ""
        session.source_text = existing + "\n\n" + request.content
    else:
        session = LearningSession(
            type=SessionType.LEARN,
            source_text=request.content,
            status=SessionStatus.ACTIVE,
        )
        db.add(session)

    await db.commit()
    await db.refresh(session)

    return EventSourceResponse(
        _stream_learn_analysis(request.content, session, db, request.model)
    )


@router.get("/{session_id}", response_model=LearnSessionDetail)
async def get_learn_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a learn session by ID, including all knowledge points."""
    result = await db.execute(
        select(LearningSession)
        .options(selectinload(LearningSession.knowledge_points))
        .where(LearningSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
