"""Document ingestion orchestrator: parse → chunk → embed → index pipeline."""

import asyncio
import logging
from datetime import datetime, timezone

import aiosqlite

from app.config import Settings
from app.database import (
    insert_chunk,
    update_document_status,
)
from app.services.chunker import chunk_document
from app.services.embedder import embed_chunks
from app.services.parser import parse_document
from app.services.vector_store import upsert_chunks

logger = logging.getLogger(__name__)

# Per-doc_id asyncio queues consumed by SSE stream endpoint
_progress_queues: dict[str, asyncio.Queue] = {}


def get_progress_queue(doc_id: str) -> asyncio.Queue:
    """Get or create progress queue for a doc_id."""
    if doc_id not in _progress_queues:
        _progress_queues[doc_id] = asyncio.Queue()
    return _progress_queues[doc_id]


def remove_progress_queue(doc_id: str) -> None:
    """Remove progress queue after SSE stream ends."""
    _progress_queues.pop(doc_id, None)


async def _emit(doc_id: str, status: str, progress_pct: int, message: str) -> None:
    """Put a progress event onto the queue if one exists."""
    if doc_id in _progress_queues:
        await _progress_queues[doc_id].put(
            {
                "status": status,
                "progress_pct": progress_pct,
                "message": message,
            }
        )


async def ingest_document(
    doc_id: str,
    session_id: str,
    filename: str,
    file_type: str,
    file_bytes: bytes,
    db: aiosqlite.Connection,
    settings: Settings,
) -> None:
    """
    Pipeline: parse → chunk → embed → index → READY

    Each step:
    1. Update DB status
    2. Emit progress event to queue
    3. Perform work
    4. On error: mark FAILED with error_message, emit FAILED event, return
    """
    # ── Step 1: PARSE ─────────────────────────────────────────────────────────
    await update_document_status(db, doc_id, "PARSING")
    await _emit(doc_id, "PARSING", 10, "Parsing document...")

    try:
        parsed = parse_document(file_bytes, file_type)
    except Exception as exc:
        error_msg = _extract_error_message(exc)
        await update_document_status(db, doc_id, "FAILED", error_message=error_msg)
        await _emit(doc_id, "FAILED", 0, f"Parse failed: {error_msg}")
        logger.error("Parse failed for doc %s: %s", doc_id, error_msg)
        return

    # ── Step 2: CHUNK ─────────────────────────────────────────────────────────
    await update_document_status(db, doc_id, "CHUNKING")
    await _emit(doc_id, "CHUNKING", 30, "Chunking text...")

    chunks = chunk_document(parsed, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)

    if len(chunks) == 0:
        error_msg = "No chunks produced"
        await update_document_status(db, doc_id, "FAILED", error_message=error_msg)
        await _emit(doc_id, "FAILED", 0, error_msg)
        logger.warning("No chunks produced for doc %s", doc_id)
        return

    # ── Step 3: INSERT CHUNKS TO SQLITE ───────────────────────────────────────
    for chunk in chunks:
        chunk_id = f"{doc_id}:{chunk.chunk_index}"
        await insert_chunk(
            db,
            chunk_id=chunk_id,
            doc_id=doc_id,
            session_id=session_id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            token_count=chunk.token_count,
            text=chunk.text,
        )
    await db.commit()

    # ── Step 4: EMBED ─────────────────────────────────────────────────────────
    await update_document_status(db, doc_id, "EMBEDDING")
    await _emit(doc_id, "EMBEDDING", 40, "Generating embeddings...")

    texts = [c.text for c in chunks]

    try:
        embeddings = await embed_chunks(texts, model=settings.EMBEDDING_MODEL)
    except Exception as exc:
        error_msg = _extract_error_message(exc)
        await update_document_status(db, doc_id, "FAILED", error_message=error_msg)
        await _emit(doc_id, "FAILED", 0, f"Embedding failed: {error_msg}")
        logger.error("Embedding failed for doc %s: %s", doc_id, error_msg)
        return

    # ── Step 5: UPSERT TO CHROMADB ────────────────────────────────────────────
    await update_document_status(db, doc_id, "INDEXING")
    await _emit(doc_id, "INDEXING", 90, "Indexing in vector store...")

    chunk_ids = [f"{doc_id}:{c.chunk_index}" for c in chunks]
    metadatas = [
        {
            "doc_id": doc_id,
            "session_id": session_id,
            "filename": filename,
            "file_type": file_type,
            "chunk_index": c.chunk_index,
            "page_number": c.page_number,  # None → -1 handled in vector_store.upsert_chunks
            "token_count": c.token_count,
        }
        for c in chunks
    ]

    upsert_chunks(session_id, chunk_ids, embeddings, texts, metadatas)

    # ── Step 6: MARK READY ────────────────────────────────────────────────────
    ready_at = datetime.now(timezone.utc).isoformat()
    await update_document_status(
        db,
        doc_id,
        "READY",
        chunk_count=len(chunks),
        page_count=parsed.page_count,
        ready_at=ready_at,
    )
    await _emit(doc_id, "READY", 100, "Document ready")
    await db.commit()

    logger.info(
        "Ingestion complete: doc_id=%s, chunks=%d, pages=%s",
        doc_id,
        len(chunks),
        parsed.page_count,
    )


def _extract_error_message(exc: Exception) -> str:
    """Extract a human-readable error message from an exception."""
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, dict):
            return detail.get("message", str(exc))
        return str(detail)
    return str(exc)
