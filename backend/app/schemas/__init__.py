"""Schemas package — Pydantic request/response models."""

from .learn import (
    LearnRequest,
    KnowledgePointBrief,
    LearnResponse,
    LearnSessionBrief,
    LearnSessionDetail,
)
from .chat import (
    ChatSendRequest,
    ChatMessageResponse,
    ChatSessionBrief,
    ChatSessionDetail,
)
from .document import (
    DocumentLearnRequest,
    DocumentSessionBrief,
    DocumentSessionDetail,
)
from .knowledge import (
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeResponse,
    KnowledgeListResponse,
)
from .history import (
    HistorySessionResponse,
    HistoryListResponse,
    HistoryStatsResponse,
)

__all__ = [
    # learn
    "LearnRequest",
    "KnowledgePointBrief",
    "LearnResponse",
    "LearnSessionBrief",
    "LearnSessionDetail",
    # chat
    "ChatSendRequest",
    "ChatMessageResponse",
    "ChatSessionBrief",
    "ChatSessionDetail",
    # document
    "DocumentLearnRequest",
    "DocumentSessionBrief",
    "DocumentSessionDetail",
    # knowledge
    "KnowledgeCreate",
    "KnowledgeUpdate",
    "KnowledgeResponse",
    "KnowledgeListResponse",
    # history
    "HistorySessionResponse",
    "HistoryListResponse",
    "HistoryStatsResponse",
]
