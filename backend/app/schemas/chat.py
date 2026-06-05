"""Pydantic schemas for Chat sessions."""

import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatSendRequest(BaseModel):
    """Send a message to an existing or new chat session."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The user message content.",
    )
    session_id: Optional[str] = Field(
        default=None,
        pattern=r"^[a-fA-F0-9\-]{36}$",
        description="Target session id; a new chat session is created when omitted.",
    )
    model: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="LLM model name override.",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "content": "What is gradient descent?",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "model": None,
            },
        },
    )


class ChatMessageResponse(BaseModel):
    """A single chat message (user or AI)."""

    id: str = Field(..., description="Message id.")
    session_id: str = Field(..., description="Owning session id.")
    role: str = Field(..., description="Message role: user / ai / system.")
    content: str = Field(..., description="Message content.")
    created_at: datetime.datetime = Field(..., description="Creation timestamp.")

    model_config = ConfigDict(from_attributes=True)


class ChatSessionBrief(BaseModel):
    """Brief row shown in a chat session list."""

    id: str = Field(..., description="Session id.")
    title: Optional[str] = Field(default=None, description="Auto-generated or user-set title.")
    status: str = Field(..., description="Session status (active / completed).")
    last_message: Optional[str] = Field(
        default=None,
        description="Preview of the most recent message (truncated).",
    )
    message_count: int = Field(default=0, ge=0, description="Total messages in the session.")
    created_at: datetime.datetime = Field(..., description="Creation timestamp.")
    updated_at: Optional[datetime.datetime] = Field(
        default=None, description="Last activity timestamp."
    )

    model_config = ConfigDict(from_attributes=True)


class ChatSessionDetail(BaseModel):
    """Full chat session detail including all messages."""

    id: str = Field(..., description="Session id.")
    type: str = Field(..., description="Session type.")
    title: Optional[str] = Field(default=None, description="Session title.")
    status: str = Field(..., description="Session status (active / completed).")
    created_at: datetime.datetime = Field(..., description="Creation timestamp.")
    updated_at: Optional[datetime.datetime] = Field(
        default=None, description="Last activity timestamp."
    )
    messages: list[ChatMessageResponse] = Field(
        default_factory=list, description="All messages in this session."
    )

    model_config = ConfigDict(from_attributes=True)
