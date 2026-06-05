"""Document router — POST /api/document/upload (multipart) and POST /api/document/learn (SSE)."""

import json
import logging
import os
import uuid
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models import LearningSession, KnowledgePoint, SessionType, SessionStatus
from app.prompts import get_system_prompt
from app.schemas.document import DocumentLearnRequest, DocumentSessionDetail
from app.services import get_adapter, get_default_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/document", tags=["document"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".docx", ".pdf"}


def _extract_text(filepath: Path, filename: str) -> str:
    """Extract raw text from a supported file format."""
    ext = Path(filename).suffix.lower()

    if ext in {".txt", ".md", ".markdown"}:
        return filepath.read_text(encoding="utf-8", errors="replace")

    if ext == ".docx":
        try:
            from docx import Document

            doc = Document(str(filepath))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="python-docx is required to process .docx files",
            )

    if ext == ".pdf":
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(str(filepath))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="PyPDF2 is required to process .pdf files",
            )

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
    )


def _parse_knowledge_points(raw_text: str) -> list[dict]:
    """Parse LLM output into a list of knowledge-point dicts."""
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


async def _stream_document_analysis(
    text: str,
    session: LearningSession,
    db: AsyncSession,
    model: str | None = None,
) -> AsyncIterator[dict]:
    """Stream document-analysis events as SSE dicts."""
    adapter = get_adapter(model) if model else get_default_adapter()

    messages = [
        {"role": "system", "content": get_system_prompt("document")},
        {"role": "user", "content": text},
    ]

    full_response = ""

    try:
        async for token in adapter.chat_stream(messages):
            full_response += token
            yield {"data": json.dumps({"type": "token", "data": token})}

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
        logger.exception("Document analysis failed for session %s", session.id)
        yield {"data": json.dumps({"type": "error", "data": str(exc)})}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document (txt/md/docx/pdf), extract text, and create a session.

    Returns the session ID so the client can call ``/api/document/learn`` next.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Save to a unique filename
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = UPLOAD_DIR / safe_name

    content_bytes = await file.read()
    filepath.write_bytes(content_bytes)

    # Extract text
    try:
        text = _extract_text(filepath, file.filename)
    except HTTPException:
        # Clean up on failure
        if filepath.exists():
            filepath.unlink()
        raise

    if not text.strip():
        if filepath.exists():
            filepath.unlink()
        raise HTTPException(status_code=400, detail="No extractable text found in the document")

    # Create session
    session = LearningSession(
        type=SessionType.DOCUMENT,
        title=file.filename,
        source_filename=file.filename,
        source_text=text,
        status=SessionStatus.ACTIVE,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return {
        "session_id": session.id,
        "filename": file.filename,
        "text_length": len(text),
        "message": "Document uploaded successfully. Use POST /api/document/learn to start analysis.",
    }


@router.post("/learn")
async def learn_document(
    request: DocumentLearnRequest,
    db: AsyncSession = Depends(get_db),
):
    """Start LLM analysis of an uploaded document, streaming results via SSE.

    Requires a ``session_id`` from a prior ``POST /api/document/upload`` call.
    """
    result = await db.execute(
        select(LearningSession)
        .options(selectinload(LearningSession.knowledge_points))
        .where(LearningSession.id == request.session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.source_text:
        raise HTTPException(status_code=400, detail="Session has no document text to analyze")

    return EventSourceResponse(
        _stream_document_analysis(session.source_text, session, db, request.model)
    )


@router.get("/{session_id}", response_model=DocumentSessionDetail)
async def get_document_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a document session by ID, including all knowledge points."""
    result = await db.execute(
        select(LearningSession)
        .options(selectinload(LearningSession.knowledge_points))
        .where(LearningSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
