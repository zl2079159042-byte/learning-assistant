"""Pydantic schemas for Document sessions."""

import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentLearnRequest(BaseModel):
    """Request to start a document-based learn session."""

    source_text: str = Field(
        ...,
        min_length=1,
        max_length=200000,
        description="Full text content extracted from the document.",
    )
    source_filename: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Original document filename (e.g. 'notes.pdf').",
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
                "source_text": "Chapter 1: Introduction to Neural Networks...",
                "source_filename": "deep-learning-notes.txt",
                "session_id": None,
                "model": None,
            },
        },
    )


class DocumentSessionBrief(BaseModel):
    """Brief row shown in a document session list."""

    id: str = Field(..., description="Session id.")
    title: Optional[str] = Field(default=None, description="Session title.")
    source_filename: Optional[str] = Field(
        default=None, description="Original document filename."
    )
    status: str = Field(..., description="Session status (active / completed).")
    knowledge_count: int = Field(default=0, ge=0, description="Number of extracted knowledge points.")
    created_at: datetime.datetime = Field(..., description="Creation timestamp.")
    updated_at: Optional[datetime.datetime] = Field(
        default=None, description="Last activity timestamp."
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentSessionDetail(BaseModel):
    """Full document session detail including knowledge points."""

    id: str = Field(..., description="Session id.")
    type: str = Field(..., description="Session type.")
    title: Optional[str] = Field(default=None, description="Session title.")
    source_filename: Optional[str] = Field(default=None, description="Original document filename.")
    status: str = Field(..., description="Session status (active / completed).")
    knowledge_count: int = Field(default=0, ge=0, description="Number of extracted knowledge points.")
    created_at: datetime.datetime = Field(..., description="Creation timestamp.")
    updated_at: Optional[datetime.datetime] = Field(
        default=None, description="Last activity timestamp."
    )
    knowledge_points: list["KnowledgePointBrief"] = Field(
        default_factory=list, description="All knowledge points in this session."
    )

    model_config = ConfigDict(from_attributes=True)


# Import at bottom to avoid circular dependency
from .learn import KnowledgePointBrief  # noqa: E402
