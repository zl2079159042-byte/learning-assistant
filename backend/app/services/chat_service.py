"""Chat service — conversational tutoring with message history.

Provides:
- get_or_create_chat_session: fetch an existing chat session or create a new one
- get_chat_messages: retrieve ordered messages for a session
- chat_stream: async generator yielding (token, session_id) tuples; persists
  user and AI messages and maintains a sliding 20-message context window.
"""

from typing import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage, LearningSession, MessageRole, SessionStatus, SessionType
from app.prompts import CHAT_SYSTEM_PROMPT
from app.services.llm import get_default_adapter

# Maximum number of recent messages included as LLM context.
_CONTEXT_LIMIT = 20


async def get_or_create_chat_session(
    *,
    db: AsyncSession,
    session_id: str | None = None,
    title: str | None = None,
) -> LearningSession:
    """Return an existing chat session or create a brand-new one.

    Args:
        db: async database session
        session_id: if provided the session is fetched and validated
        title: optional title for a newly created session

    Returns:
        a LearningSession with type == CHAT

    Raises:
        ValueError: if session_id is provided but the session does not exist
                    or is not a chat session
    """
    if session_id:
        stmt = select(LearningSession).where(LearningSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if session is None:
            raise ValueError(f"Chat session {session_id!r} not found")
        if session.type != SessionType.CHAT:
            raise ValueError(
                f"Session {session_id!r} is type={session.type.value}, not chat"
            )
        return session

    # Create new
    session = LearningSession(
        type=SessionType.CHAT,
        title=title or "Chat Session",
        status=SessionStatus.ACTIVE,
    )
    db.add(session)
    await db.flush()
    return session


async def get_chat_messages(
    *,
    db: AsyncSession,
    session_id: str,
) -> list[ChatMessage]:
    """Return all messages for a chat session, oldest first.

    Args:
        db: async database session
        session_id: the session whose messages to fetch

    Returns:
        list of ChatMessage ordered by created_at ascending
    """
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def chat_stream(
    *,
    db: AsyncSession,
    session_id: str,
    user_message: str,
) -> AsyncIterator[tuple[str, str]]:
    """Stream the AI tutor reply for a user message, yielding tokens one by one.

    Orchestration:
    1. Persist the incoming user message.
    2. Load the 20 most recent messages as context.
    3. Call the LLM in streaming mode.
    4. Accumulate the full AI response.
    5. Persist the AI message.
    6. Update the session's updated_at timestamp.

    Yields:
        ``(token, session_id)`` tuples, where *token* is a plain-text chunk.

    Raises:
        ValueError: if the session does not exist or is not a chat session
    """
    # ── validate session ───────────────────────────────────────────────────
    stmt = select(LearningSession).where(LearningSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError(f"Session {session_id!r} not found")
    if session.type != SessionType.CHAT:
        raise ValueError(
            f"Session {session_id!r} is type={session.type.value}, not chat"
        )

    # ── save user message ──────────────────────────────────────────────────
    user_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.USER,
        content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # ── build context (last 20 messages) ────────────────────────────────────
    recent_st = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(_CONTEXT_LIMIT)
    )
    recent_result = await db.execute(recent_st)
    recent_messages = list(recent_result.scalars().all())

    # Reverse to chronological order for the LLM
    recent_messages.reverse()

    llm_messages: list[dict] = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT}
    ]
    for msg in recent_messages:
        role = "assistant" if msg.role == MessageRole.AI else msg.role.value
        llm_messages.append({"role": role, "content": msg.content})

    # ── stream LLM response ────────────────────────────────────────────────
    adapter = get_default_adapter()
    accumulated: list[str] = []

    async for token in adapter.chat_stream(llm_messages):
        accumulated.append(token)
        yield (token, session_id)

    full_response = "".join(accumulated)

    # ── save AI message ────────────────────────────────────────────────────
    ai_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.AI,
        content=full_response,
    )
    db.add(ai_msg)
    await db.flush()

    # ── bump session timestamp ─────────────────────────────────────────────
    # Mark session as "touched" so updated_at reflects latest activity.
    from sqlalchemy import func

    session.updated_at = func.now()  # type: ignore[assignment]
    await db.flush()
