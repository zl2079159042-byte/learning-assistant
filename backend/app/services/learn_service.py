"""Learn service — text analysis and knowledge extraction.

Provides:
- create_learn_session: persist user-provided text as a new learn session
- analyze_text_stream: async generator that streams LLM analysis tokens as
  SSE events, parses knowledge points from the completed response, persists
  them to the database, and marks the session completed.
"""

import json
import re
from typing import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgePoint, LearningSession, SessionStatus, SessionType
from app.prompts import LEARN_SYSTEM_PROMPT
from app.services.llm import get_default_adapter


async def create_learn_session(
    *,
    db: AsyncSession,
    text: str,
    title: str | None = None,
) -> LearningSession:
    """Create a new LEARN session with the given source text.

    Args:
        db: async database session
        text: the learning material provided by the user
        title: optional human-readable title; defaults to first 80 chars of text

    Returns:
        the newly created LearningSession instance (already flushed, not committed)
    """
    session = LearningSession(
        type=SessionType.LEARN,
        title=title or (text[:80].replace("\n", " ") + "…" if len(text) > 80 else text),
        source_text=text,
        status=SessionStatus.ACTIVE,
    )
    db.add(session)
    await db.flush()
    return session


async def analyze_text_stream(
    *,
    db: AsyncSession,
    session_id: str,
) -> AsyncIterator[str]:
    """Stream the LLM analysis of a learn session's source text as SSE tokens.

    On completion the accumulated response is parsed into KnowledgePoint rows,
    the session's knowledge_count is updated, and its status is set to COMPLETED.

    Yields:
        SSE-formatted strings, e.g. ``data: {"token": "你好"}\\n\\n``.
        The final event includes ``"done": true`` and a ``knowledge_count``.

    Raises:
        ValueError: if the session is not found or has no source_text
    """
    # ── load session ──────────────────────────────────────────────────────
    stmt = select(LearningSession).where(LearningSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError(f"LearningSession {session_id!r} not found")
    if not session.source_text:
        raise ValueError(f"LearningSession {session_id!r} has no source_text")

    # ── build LLM context ──────────────────────────────────────────────────
    messages = [
        {"role": "system", "content": LEARN_SYSTEM_PROMPT},
        {"role": "user", "content": f"请分析以下学习材料：\n\n{session.source_text}"},
    ]

    # ── stream tokens ──────────────────────────────────────────────────────
    adapter = get_default_adapter()
    accumulated: list[str] = []

    async for token in adapter.chat_stream(messages):
        accumulated.append(token)
        yield _sse_event({"token": token})

    full_response = "".join(accumulated)

    # ── parse knowledge points ─────────────────────────────────────────────
    knowledge_points = _parse_knowledge_points(full_response)
    for kp in knowledge_points:
        db.add(
            KnowledgePoint(
                session_id=session_id,
                title=kp["title"],
                content=kp["content"],
                category=kp.get("category"),
                tags=kp.get("tags"),
            )
        )

    # ── finalise session ──────────────────────────────────────────────────
    session.knowledge_count = len(knowledge_points)
    session.status = SessionStatus.COMPLETED
    await db.flush()

    yield _sse_event({"done": True, "knowledge_count": len(knowledge_points)})


# ── helpers ──────────────────────────────────────────────────────────────────


def _sse_event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# Pattern: ## 📌 Title  (with optional emoji prefix)
_KP_HEADER_RE = re.compile(r"^##\s*(?:[📌🎯💡🔑🧠✏️⭐]+\s*)?(.+)$", re.MULTILINE)


def _parse_knowledge_points(response: str) -> list[dict]:
    """Parse the LLM response into a list of knowledge-point dicts.

    The learn system prompt instructs the LLM to separate points with ``---``
    and start each one with a ``## 📌 Title`` header.  This parser splits on
    those separators and extracts title + content for each block.
    """
    # Split on horizontal-rule separators (--- on its own line)
    blocks = re.split(r"\n---\n", response)
    points: list[dict] = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Extract title from the ## header
        match = _KP_HEADER_RE.search(block)
        if match:
            title = match.group(1).strip()
            # Remove the header line from content so we don't duplicate it
            content = block[match.end() :].strip()
        else:
            # Fallback: first line as title
            lines = block.split("\n")
            title = lines[0].lstrip("#").strip()
            content = "\n".join(lines[1:]).strip()

        # Attempt to extract tags from content lines like "标签：tag1, tag2"
        tags: str | None = None
        tag_match = re.search(r"标签[：:]\s*(.+)", content)
        if tag_match:
            tags = tag_match.group(1).strip()
        # Also check the end of title for a category hint like 【数学】
        cat_match = re.match(r"【(.+?)】", title)
        category = cat_match.group(1) if cat_match else None

        if title and content:
            points.append(
                {
                    "title": title[:500],
                    "content": content,
                    "category": category,
                    "tags": tags,
                }
            )

    return points
