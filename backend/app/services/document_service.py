"""Document service — file text extraction and document session creation.

Provides:
- extract_text: extract readable text from txt, md, docx, and pdf files
- create_document_session: persist an uploaded file to disk, create a
  DOCUMENT-type LearningSession with the extracted source text
"""

import os
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import LearningSession, SessionStatus, SessionType

# ── supported extensions ─────────────────────────────────────────────────────

_SUPPORTED_EXTENSIONS = frozenset({".txt", ".md", ".docx", ".pdf"})

# Default upload directory; can be overridden via environment.
_UPLOADS_DIR = Path(
    os.environ.get("UPLOADS_DIR", str(Path(__file__).resolve().parents[2] / "uploads"))
)


# ── public helpers ───────────────────────────────────────────────────────────


def is_supported(filename: str) -> bool:
    """Return True if the file extension is one we know how to parse."""
    return Path(filename).suffix.lower() in _SUPPORTED_EXTENSIONS


# ── text extraction ──────────────────────────────────────────────────────────


async def extract_text(*, file_content: bytes, filename: str) -> str:
    """Extract plain text from an in-memory file.

    Args:
        file_content: raw bytes of the uploaded file
        filename: original filename (used to guess the format)

    Returns:
        extracted text as a single string

    Raises:
        ValueError: if the file extension is unsupported or the file is unreadable
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in _SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {suffix!r}. "
            f"Supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}"
        )

    buffer = BytesIO(file_content)

    if suffix == ".txt":
        return _extract_txt(buffer)

    if suffix == ".md":
        return _extract_md(buffer)

    if suffix == ".docx":
        return _extract_docx(buffer)

    if suffix == ".pdf":
        return _extract_pdf(buffer)

    # Should be unreachable due to the guard above.
    raise ValueError(f"Unhandled extension: {suffix!r}")


# ── session creation ─────────────────────────────────────────────────────────


async def create_document_session(
    *,
    db: AsyncSession,
    file_content: bytes,
    filename: str,
    title: str | None = None,
) -> LearningSession:
    """Save an uploaded document and create a corresponding DOCUMENT session.

    1. Extract text from the file bytes.
    2. Persist the original file to the uploads directory.
    3. Create a LearningSession (type=DOCUMENT) with the extracted text.

    Args:
        db: async database session
        file_content: raw bytes of the uploaded file
        filename: original filename
        title: optional session title; defaults to the filename

    Returns:
        the newly created (flushed) LearningSession

    Raises:
        ValueError: if the file extension is unsupported or text extraction fails
    """
    # ── extract text ───────────────────────────────────────────────────────
    text = await extract_text(file_content=file_content, filename=filename)

    # ── save file to disk ──────────────────────────────────────────────────
    saved_path = _save_file(file_content=file_content, filename=filename)

    # ── create session ─────────────────────────────────────────────────────
    session = LearningSession(
        type=SessionType.DOCUMENT,
        title=title or filename,
        source_text=text,
        source_filename=str(saved_path),
        status=SessionStatus.ACTIVE,
    )
    db.add(session)
    await db.flush()
    return session


# ── internal extractors ──────────────────────────────────────────────────────


def _extract_txt(buffer: BytesIO) -> str:
    """Decode a plain-text file (UTF-8, with fallback)."""
    try:
        return buffer.read().decode("utf-8")
    except UnicodeDecodeError:
        buffer.seek(0)
        return buffer.read().decode("gbk", errors="replace")


def _extract_md(buffer: BytesIO) -> str:
    """Markdown files are plain-text — same logic as .txt."""
    return _extract_txt(buffer)


def _extract_docx(buffer: BytesIO) -> str:
    """Extract text from a .docx file using python-docx."""
    try:
        from docx import Document  # type: ignore[import-untyped]
    except ImportError:
        raise RuntimeError(
            "python-docx is required to process .docx files. "
            "Install it with: pip install python-docx"
        )

    doc = Document(buffer)  # type: ignore[var-annotated]
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_pdf(buffer: BytesIO) -> str:
    """Extract text from a .pdf file using PyPDF2."""
    try:
        from PyPDF2 import PdfReader  # type: ignore[import-untyped]
    except ImportError:
        raise RuntimeError(
            "PyPDF2 is required to process .pdf files. "
            "Install it with: pip install PyPDF2"
        )

    reader = PdfReader(buffer)  # type: ignore[var-annotated]
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


# ── file persistence ─────────────────────────────────────────────────────────


def _save_file(*, file_content: bytes, filename: str) -> Path:
    """Write file bytes to disk under the uploads directory.

    Deduplicates filenames by appending a counter when a name already exists.
    """
    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    base = Path(filename)
    stem, suffix = base.stem, base.suffix
    dest = _UPLOADS_DIR / base.name

    # Simple deduplication
    counter = 1
    while dest.exists():
        dest = _UPLOADS_DIR / f"{stem}_{counter}{suffix}"
        counter += 1

    dest.write_bytes(file_content)
    return dest
