"""Tests for chat query, streaming, history, and delete endpoints."""

import asyncio
import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def upload_txt(client, session_id):
    """Upload sample.txt and return doc_id."""
    txt = (FIXTURES_DIR / "sample.txt").read_bytes()
    resp = client.post(
        "/api/documents/upload",
        data={"session_id": session_id},
        files={"file": ("sample.txt", io.BytesIO(txt), "text/plain")},
    )
    assert resp.status_code == 202
    return resp.json()["doc_id"]


def force_doc_ready(client, session_id, doc_id):
    """Force a document to READY status directly in the DB for testing."""
    import asyncio
    from app.database import get_db, update_document_status

    async def _set_ready():
        db = await get_db()
        try:
            await update_document_status(db, doc_id, "READY", chunk_count=5, page_count=None)
        finally:
            await db.close()

    asyncio.run(_set_ready())


def seed_vector_store(session_id, doc_id):
    """Seed the vector store with a fake chunk so queries can retrieve something."""
    from app.services.vector_store import upsert_chunks

    FAKE_EMBEDDING = [0.0] * 1536
    upsert_chunks(
        session_id,
        [f"{doc_id}:0"],
        [FAKE_EMBEDDING],
        ["The contract was signed on March 15 2024."],
        [
            {
                "doc_id": doc_id,
                "session_id": session_id,
                "filename": "sample.txt",
                "file_type": "txt",
                "chunk_index": 0,
                "page_number": None,
                "token_count": 10,
            }
        ],
    )


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


def test_query_empty_returns_422(client, sample_session):
    """POST /api/chat/query with empty query returns 422 EMPTY_QUERY."""
    resp = client.post(
        "/api/chat/query",
        json={"session_id": sample_session, "query": "   "},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error_code"] == "EMPTY_QUERY"


def test_query_too_long_returns_422(client, sample_session):
    """POST /api/chat/query with 2001-char query returns 422 QUERY_TOO_LONG."""
    resp = client.post(
        "/api/chat/query",
        json={"session_id": sample_session, "query": "x" * 2001},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error_code"] == "QUERY_TOO_LONG"


def test_query_no_docs_returns_422(client, sample_session):
    """POST /api/chat/query with no READY documents returns 422 NO_DOCUMENTS_READY."""
    resp = client.post(
        "/api/chat/query",
        json={"session_id": sample_session, "query": "What is the contract date?"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error_code"] == "NO_DOCUMENTS_READY"


def test_query_unknown_session_returns_404(client):
    """POST /api/chat/query with unknown session returns 404."""
    resp = client.post(
        "/api/chat/query",
        json={"session_id": "no-such-session", "query": "test"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["error_code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# Chat query with mocked LLM
# ---------------------------------------------------------------------------


def test_query_returns_message_id(client, sample_session, mock_openai_embeddings, mock_openai_chat):
    """POST /api/chat/query with READY doc returns message_id."""
    doc_id = upload_txt(client, sample_session)
    force_doc_ready(client, sample_session, doc_id)
    seed_vector_store(sample_session, doc_id)

    resp = client.post(
        "/api/chat/query",
        json={"session_id": sample_session, "query": "When was the contract signed?"},
    )
    assert resp.status_code == 200
    assert "message_id" in resp.json()


# ---------------------------------------------------------------------------
# Chat history tests
# ---------------------------------------------------------------------------


def test_get_history_empty(client, sample_session):
    """GET /api/chat/history/{session_id} returns empty list initially."""
    resp = client.get(f"/api/chat/history/{sample_session}")
    assert resp.status_code == 200
    assert resp.json()["messages"] == []


def test_get_history_unknown_session_returns_404(client):
    """GET /api/chat/history/{session_id} with unknown session returns 404."""
    resp = client.get("/api/chat/history/unknown-session-id")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error_code"] == "SESSION_NOT_FOUND"


def test_delete_history(client, sample_session, mock_openai_embeddings, mock_openai_chat):
    """DELETE /api/chat/history/{session_id} returns 204 and clears messages."""
    # Seed a user message directly
    import asyncio
    from app.database import get_db, insert_message
    import uuid

    async def _insert():
        db = await get_db()
        try:
            await insert_message(db, str(uuid.uuid4()), sample_session, "user", "hello")
        finally:
            await db.close()

    asyncio.run(_insert())

    # Verify it exists
    hist_resp = client.get(f"/api/chat/history/{sample_session}")
    assert len(hist_resp.json()["messages"]) >= 1

    # Delete
    del_resp = client.delete(f"/api/chat/history/{sample_session}")
    assert del_resp.status_code == 204

    # Verify cleared
    hist_resp2 = client.get(f"/api/chat/history/{sample_session}")
    assert hist_resp2.json()["messages"] == []


def test_delete_history_unknown_session_returns_404(client):
    """DELETE /api/chat/history/{session_id} with unknown session returns 404."""
    resp = client.delete("/api/chat/history/unknown-session-id")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error_code"] == "SESSION_NOT_FOUND"
