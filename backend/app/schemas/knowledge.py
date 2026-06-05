"""Pydantic schemas for Knowledge Points."""

import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeCreate(BaseModel):
    """Create a new knowledge point."""

    session_id: str = Field(
        ...,
        pattern=r"^[a-fA-F0-9\-]{36}$",
        description="Owning session id.",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Short title summarising the knowledge point.",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Full explanation / body of the knowledge point.",
    )
    category: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional category label.",
    )
    tags: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Comma-separated tags.",
    )
    mastery_level: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Initial mastery score between 0 and 1.",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Gradient Descent",
                "content": "Gradient descent is an optimisation algorithm...",
                "category": "machine-learning",
                "tags": "optimisation,maths",
                "mastery_level": 0.3,
            },
        },
    )


class KnowledgeUpdate(BaseModel):
    """Update an existing knowledge point. Every field is optional."""

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Updated title.",
    )
    content: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Updated content.",
    )
    category: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Updated category label.",
    )
    tags: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Updated comma-separated tags.",
    )
    mastery_level: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Updated mastery score.",
    )
    review_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Updated review count.",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Gradient Descent (revised)",
                "mastery_level": 0.7,
                "review_count": 3,
            },
        },
    )


class KnowledgeResponse(BaseModel):
    """Full knowledge point returned by the API."""

    id: str = Field(..., description="Knowledge point id.")
    session_id: str = Field(..., description="Owning session id.")
    title: str = Field(..., description="Knowledge point title.")
    content: str = Field(..., description="Knowledge point content.")
    category: Optional[str] = Field(default=None, description="Category label.")
    tags: Optional[str] = Field(default=None, description="Comma-separated tags.")
    mastery_level: float = Field(default=0.0, ge=0.0, le=1.0, description="Mastery score.")
    review_count: int = Field(default=0, ge=0, description="Review count.")
    created_at: datetime.datetime = Field(..., description="Creation timestamp.")

    model_config = ConfigDict(from_attributes=True)


class KnowledgeListResponse(BaseModel):
    """Paginated / batched list of knowledge points."""

    items: list[KnowledgeResponse] = Field(
        default_factory=list, description="Knowledge point items."
    )
    total: int = Field(default=0, ge=0, description="Total number of matching records.")
    page: int = Field(default=1, ge=1, description="Current page number.")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 42,
                "page": 1,
                "page_size": 20,
            },
        },
    )
