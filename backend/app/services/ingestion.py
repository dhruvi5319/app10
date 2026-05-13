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

# Per-doc_id progress queues — SSE stream endpoints consume from these
_progress_queues: dict[str, asyncio.Queue] = {}


def get_progress_queue(doc_id: str) -> asyncio.Queue:
    """Get (or create) the progress queue for a document."""
    if doc_id not in _progress_queues:
        _progress_queues[doc_id] = asyncio.Queue()
    return _progress_queues[doc_id]


def remove_progress_queue(doc_id: str) -> None:
    """Clean up the queue after SSE stream closes."""
    _progress_queues.pop(doc_id, None)


async def _emit(doc_id: str, status: str, progress_pct: int, message: str) -> None:
    """Post a progress event to the doc's queue."""
    queue = get_progress_queue(doc_id)
    await queue.put(
        {
            "doc_id": doc_id,
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
    Full ingestion pipeline for a document.
    Status transitions: UPLOADING → PARSING → CHUNKING → EMBEDDING → INDEXING → READY/FAILED
    Progress events are posted to get_progress_queue(doc_id).
    """
    # Ensure queue exists before we start emitting
    get_progress_queue(doc_id)

    try:
        # ── PARSING ──────────────────────────────────────────────────────────
        await update_document_status(db, doc_id, "PARSING")
        await _emit(doc_id, "PARSING", 10, "Parsing document...")

        try:
            parsed = parse_document(file_bytes, file_type)
        except Exception as exc:
            error_msg = _extract_error_message(exc)
            await update_document_status(
                db, doc_id, "FAILED", error_message=error_msg
            )
            await _emit(doc_id, "FAILED", 0, f"Parse failed: {error_msg}")
            logger.error(f"Parse failed for doc {doc_id}: {error_msg}")
            return

        # ── CHUNKING ─────────────────────────────────────────────────────────
        await update_document_status(db, doc_id, "CHUNKING")
        await _emit(doc_id, "CHUNKING", 30, "Splitting document into chunks...")

        chunks = chunk_document(parsed, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)

        if not chunks:
            error_msg = "Document produced no chunks after splitting"
            await update_document_status(db, doc_id, "FAILED", error_message=error_msg)
            await _emit(doc_id, "FAILED", 0, error_msg)
            return

        # Persist chunk records to SQLite
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

        # ── EMBEDDING ────────────────────────────────────────────────────────
        await update_document_status(db, doc_id, "EMBEDDING")
        await _emit(doc_id, "EMBEDDING", 40, "Generating embeddings...")

        texts = [c.text for c in chunks]
        batch_size = 100
        total_batches = max(1, (len(texts) + batch_size - 1) // batch_size)

        try:
            embeddings = await embed_chunks(texts, model=settings.EMBEDDING_MODEL)
        except Exception as exc:
            error_msg = _extract_error_message(exc)
            await update_document_status(
                db, doc_id, "FAILED", error_message=error_msg
            )
            await _emit(doc_id, "FAILED", 0, f"Embedding failed: {error_msg}")
            logger.error(f"Embedding failed for doc {doc_id}: {error_msg}")
            return

        await _emit(doc_id, "EMBEDDING", 80, f"Embedded {len(chunks)} chunks")

        # ── INDEXING ─────────────────────────────────────────────────────────
        await update_document_status(db, doc_id, "INDEXING")
        await _emit(doc_id, "INDEXING", 90, "Indexing into vector store...")

        chunk_ids = [f"{doc_id}:{c.chunk_index}" for c in chunks]
        metadatas = [
            {
                "doc_id": doc_id,
                "session_id": session_id,
                "filename": filename,
                "file_type": file_type,
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,  # None → -1 handled in vector_store
                "token_count": c.token_count,
            }
            for c in chunks
        ]

        upsert_chunks(session_id, chunk_ids, embeddings, texts, metadatas)

        # ── READY ─────────────────────────────────────────────────────────────
        ready_at = datetime.now(timezone.utc).isoformat()
        page_count = parsed.page_count  # None for TXT/DOCX

        await update_document_status(
            db,
            doc_id,
            "READY",
            chunk_count=len(chunks),
            page_count=page_count,
            ready_at=ready_at,
        )
        await _emit(
            doc_id,
            "READY",
            100,
            f"Ready — {len(chunks)} chunks indexed",
        )
        logger.info(
            f"Ingestion complete: doc_id={doc_id}, "
            f"chunks={len(chunks)}, pages={page_count}"
        )

    except Exception as exc:
        # Catch-all safety net
        error_msg = _extract_error_message(exc)
        logger.error(f"Unexpected ingestion error for doc {doc_id}: {error_msg}", exc_info=True)
        try:
            await update_document_status(db, doc_id, "FAILED", error_message=error_msg)
            await _emit(doc_id, "FAILED", 0, f"Ingestion failed: {error_msg}")
        except Exception:
            pass


def _extract_error_message(exc: Exception) -> str:
    """Extract a human-readable error message from an exception."""
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, dict):
            return detail.get("message", str(exc))
        return str(detail)
    return str(exc)
