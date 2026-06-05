"""Chat router — POST /api/chat/send (SSE) and GET /api/chat/{id} with messages."""

import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models import LearningSession, ChatMessage, SessionType, SessionStatus, MessageRole
from app.prompts import get_system_prompt
from app.schemas.chat import ChatSendRequest, ChatSessionDetail
from app.services import get_adapter, get_default_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def _stream_chat(
    user_message: str,
    session: LearningSession,
    db: AsyncSession,
    model: str | None = None,
) -> AsyncIterator[dict]:
    """Stream the AI chat response as SSE events."""
    adapter = get_adapter(model) if model else get_default_adapter()

    # Build conversation history
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    history = result.scalars().all()

    llm_messages = [{"role": "system", "content": get_system_prompt("chat")}]
    for msg in history:
        role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
        llm_messages.append({"role": role, "content": msg.content})

    # Add the new user message
    llm_messages.append({"role": "user", "content": user_message})

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=user_message,
    )
    db.add(user_msg)

    full_response = ""

    try:
        async for token in adapter.chat_stream(llm_messages):
            full_response += token
            yield {"data": json.dumps({"type": "token", "data": token})}

        # Save AI response
        ai_msg = ChatMessage(
            session_id=session.id,
            role=MessageRole.AI,
            content=full_response,
        )
        db.add(ai_msg)

        # Auto-title on first exchange
        if not session.title and full_response:
            session.title = user_message[:100]

        await db.commit()

        yield {
            "data": json.dumps(
                {
                    "type": "done",
                    "data": json.dumps(
                        {
                            "session_id": session.id,
                            "message_id": ai_msg.id,
                        }
                    ),
                }
            )
        }

    except Exception as exc:
        logger.exception("Chat streaming failed for session %s", session.id)
        yield {"data": json.dumps({"type": "error", "data": str(exc)})}


@router.post("/send")
async def send_message(
    request: ChatSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message and stream the AI reply via SSE.

    Creates a new chat session if ``session_id`` is omitted, otherwise
    continues an existing conversation.
    """
    if request.session_id:
        result = await db.execute(
            select(LearningSession)
            .options(selectinload(LearningSession.messages))
            .where(LearningSession.id == request.session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = LearningSession(
            type=SessionType.CHAT,
            status=SessionStatus.ACTIVE,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # Emit the session_id first so the client can persist it
    async def generator_with_session_id():
        yield {"data": json.dumps({"type": "session_id", "data": session.id})}
        async for event in _stream_chat(request.content, session, db, request.model):
            yield event

    return EventSourceResponse(generator_with_session_id())


@router.get("/{session_id}", response_model=ChatSessionDetail)
async def get_chat_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a chat session by ID, including all messages."""
    result = await db.execute(
        select(LearningSession)
        .options(selectinload(LearningSession.messages))
        .where(LearningSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
