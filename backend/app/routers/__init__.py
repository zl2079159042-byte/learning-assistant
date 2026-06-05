"""Routers package."""

from .learn import router as learn_router
from .chat import router as chat_router
from .document import router as document_router
from .knowledge import router as knowledge_router
from .history import router as history_router

__all__ = [
    "learn_router",
    "chat_router",
    "document_router",
    "knowledge_router",
    "history_router",
]
