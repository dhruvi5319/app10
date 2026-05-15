"""Unit tests for parser, chunker, embedder, and vector store."""

import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import chromadb
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FAKE_EMBEDDING = [0.0] * 1536


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_parse_txt_utf8():
    from app.services.parser import parse_txt
    text = "Hello, world! This is a test."
    result = parse_txt(text.encode("utf-8"))
    assert result.text == text
    assert result.page_count is None
    assert result.page_chunks == []


def test_parse_txt_latin1():
    from app.services.parser import parse_txt
    text = "Caf\xe9 au lait"  # latin-1 encoded byte
    result = parse_txt(text.encode("latin-1"))
    assert "Caf" in result.text


def test_parse_pdf_sample():
    from app.services.parser import parse_pdf
    pdf_bytes = (FIXTURES_DIR / "sample.pdf").read_bytes()
    result = parse_pdf(pdf_bytes)
    assert result.text.strip()
    assert result.page_count is not None and result.page_count >= 1
    assert len(result.page_chunks) == result.page_count


def test_parse_pdf_corrupt_raises():
    from fastapi import HTTPException
    from app.services.parser import parse_pdf
    with pytest.raises(HTTPException) as exc_info:
        parse_pdf(b"this is not a pdf")
    assert exc_info.value.status_code == 422


def test_parse_docx_sample():
    from app.services.parser import parse_docx
    docx_bytes = (FIXTURES_DIR / "sample.docx").read_bytes()
    result = parse_docx(docx_bytes)
    assert result.text.strip()
    assert result.page_count is None


# ---------------------------------------------------------------------------
# Chunker tests
# ---------------------------------------------------------------------------

def test_chunk_txt_document():
    from app.services.parser import parse_txt
    from app.services.chunker import chunk_document

    long_text = "The quick brown fox jumps over the lazy dog. " * 100
    parsed = parse_txt(long_text.encode("utf-8"))
    chunks = chunk_document(parsed, chunk_size=50, chunk_overlap=5)
    assert len(chunks) > 0
    # All chunk_index values are unique and sequential
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))
    # All page_numbers are None for TXT
    assert all(c.page_number is None for c in chunks)


def test_chunk_pdf_preserves_page_numbers():
    from app.services.parser import parse_pdf
    from app.services.chunker import chunk_document

    pdf_bytes = (FIXTURES_DIR / "sample.pdf").read_bytes()
    parsed = parse_pdf(pdf_bytes)
    chunks = chunk_document(parsed, chunk_size=50, chunk_overlap=5)
    # PDF chunks should have page_number set
    assert all(c.page_number is not None and c.page_number >= 1 for c in chunks)


def test_chunk_overlap_clamping():
    """chunk_overlap >= chunk_size should not crash."""
    from app.services.parser import parse_txt
    from app.services.chunker import chunk_document

    text = "word " * 200
    parsed = parse_txt(text.encode("utf-8"))
    # Should warn and clamp, not raise
    chunks = chunk_document(parsed, chunk_size=50, chunk_overlap=60)
    assert len(chunks) > 0


def test_chunk_token_counts():
    from app.services.parser import parse_txt
    from app.services.chunker import chunk_document

    text = "The contract was signed on March 15 2024. " * 50
    parsed = parse_txt(text.encode("utf-8"))
    chunks = chunk_document(parsed, chunk_size=100, chunk_overlap=10)
    assert all(c.token_count > 0 for c in chunks)


# ---------------------------------------------------------------------------
# Embedder tests (mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_embed_chunks_mocked(mock_openai_embeddings):
    from app.services.embedder import embed_chunks
    results = await embed_chunks(["hello world", "test sentence"])
    assert len(results) == 2
    assert len(results[0]) == 1536


@pytest.mark.asyncio
async def test_embed_batching(mock_openai_embeddings):
    """250 texts should result in 3 batches (100+100+50)."""
    from app.services.embedder import embed_chunks
    texts = [f"text {i}" for i in range(250)]
    results = await embed_chunks(texts)
    assert len(results) == 250
    # Each batch call has at most 100 items
    calls = mock_openai_embeddings.embeddings.create.call_args_list
    assert len(calls) == 3
    batch_sizes = [len(call.kwargs["input"]) for call in calls]
    assert batch_sizes == [100, 100, 50]


@pytest.mark.asyncio
async def test_embed_query_mocked(mock_openai_embeddings):
    from app.services.embedder import embed_query
    result = await embed_query("what is the contract date?")
    assert len(result) == 1536


# ---------------------------------------------------------------------------
# Vector store tests (ephemeral ChromaDB)
# ---------------------------------------------------------------------------

def test_vector_store_upsert_and_query(ephemeral_chroma):
    from app.services.vector_store import upsert_chunks, query_chunks

    session_id = "test-session-vs"
    chunk_ids = ["doc1:0"]
    embeddings = [FAKE_EMBEDDING]
    texts = ["The contract was signed on March 15 2024."]
    metadatas = [{
        "doc_id": "doc1",
        "session_id": session_id,
        "filename": "sample.txt",
        "file_type": "txt",
        "chunk_index": 0,
        "page_number": None,
        "token_count": 10,
    }]

    upsert_chunks(session_id, chunk_ids, embeddings, texts, metadatas)
    results = query_chunks(session_id, FAKE_EMBEDDING, top_k=1)

    assert len(results) == 1
    assert results[0]["chunk_id"] == "doc1:0"
    assert results[0]["filename"] == "sample.txt"
    assert results[0]["page_number"] is None  # -1 converted back to None


def test_vector_store_delete(ephemeral_chroma):
    from app.services.vector_store import upsert_chunks, query_chunks, delete_doc_chunks

    session_id = "test-session-del"
    upsert_chunks(
        session_id,
        ["doc2:0"],
        [FAKE_EMBEDDING],
        ["some text"],
        [{"doc_id": "doc2", "session_id": session_id, "filename": "f.txt",
          "file_type": "txt", "chunk_index": 0, "page_number": None, "token_count": 5}],
    )

    delete_doc_chunks(session_id, "doc2")
    results = query_chunks(session_id, FAKE_EMBEDDING, top_k=5)
    assert all(r["doc_id"] != "doc2" for r in results)


def test_vector_store_session_isolation(ephemeral_chroma):
    """Chunks from session A should not appear when querying session B."""
    from app.services.vector_store import upsert_chunks, query_chunks

    upsert_chunks(
        "session-a",
        ["docA:0"],
        [FAKE_EMBEDDING],
        ["session A text"],
        [{"doc_id": "docA", "session_id": "session-a", "filename": "a.txt",
          "file_type": "txt", "chunk_index": 0, "page_number": None, "token_count": 3}],
    )

    results = query_chunks("session-b", FAKE_EMBEDDING, top_k=5)
    assert all(r["doc_id"] != "docA" for r in results)
