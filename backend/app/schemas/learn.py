"""Pydantic schemas for Learn sessions."""

import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LearnRequest(BaseModel):
    """Request to start or continue a learn session."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="The text content to analyse and extract knowledge points from.",
    )
    session_id: Optional[str] = Field(
        default=None,
        pattern=r"^[a-fA-F0-9\-]{36}$",
        description="Existing session id to continue; creates a new session when omitted.",
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
                "content": "Machine learning is a subset of artificial intelligence...",
                "session_id": None,
                "model": None,
            },
        },
    )


class KnowledgePointBrief(BaseModel):
    """A knowledge point returned inside a learn session."""

    id: str = Field(..., description="Knowledge point id.")
    title: str = Field(..., description="Short title summarising the knowledge point.")
    content: str = Field(..., description="Full explanation of the knowledge point.")
    category: Optional[str] = Field(default=None, description="Optional category label.")
    tags: Optional[str] = Field(default=None, description="Comma-separated tags.")
    mastery_level: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Mastery score between 0 and 1."
    )
    review_count: int = Field(default=0, ge=0, description="Times reviewed.")

    model_config = ConfigDict(from_attributes=True)


class LearnResponse(BaseModel):
    """Response after processing a learn request."""

    session_id: str = Field(..., description="Session id (new or existing).")
    title: Optional[str] = Field(default=None, description="Auto-generated session title.")
    status: str = Field(..., description="Session status (active / completed).")
    knowledge_points: list[KnowledgePointBrief] = Field(
        default_factory=list,
        description="Knowledge points extracted or updated during this request.",
    )
    created_at: datetime.datetime = Field(..., description="Session creation timestamp.")

    model_config = ConfigDict(from_attributes=True)


class LearnSessionBrief(BaseModel):
    """Brief row shown in a session list."""

    id: str = Field(..., description="Session id.")
    title: Optional[str] = Field(default=None, description="Session title.")
    status: str = Field(..., description="Session status.")
    knowledge_count: int = Field(default=0, ge=0, description="Number of knowledge points.")
    created_at: datetime.datetime = Field(..., description="Creation timestamp.")
    updated_at: Optional[datetime.datetime] = Field(
        default=None, description="Last update timestamp."
    )

    model_config = ConfigDict(from_attributes=True)


class LearnSessionDetail(BaseModel):
    """Full session detail including knowledge points."""

    id: str = Field(..., description="Session id.")
    title: Optional[str] = Field(default=None, description="Session title.")
    status: str = Field(..., description="Session status.")
    source_text: Optional[str] = Field(
        default=None, description="Original learning material."
    )
    knowledge_count: int = Field(default=0, ge=0, description="Number of knowledge points.")
    knowledge_points: list[KnowledgePointBrief] = Field(
        default_factory=list,
        description="All knowledge points belonging to this session.",
    )
    created_at: datetime.datetime = Field(..., description="Creation timestamp.")
    updated_at: Optional[datetime.datetime] = Field(
        default=None, description="Last update timestamp."
    )

    model_config = ConfigDict(from_attributes=True)
