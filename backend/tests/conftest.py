"""Pytest fixtures for the RAG Chatbot backend tests."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import chromadb
import pytest
from fastapi.testclient import TestClient

# Set test environment BEFORE importing app modules
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing-only")
os.environ.setdefault("LLM_MODEL", "gpt-4o")
os.environ.setdefault("EMBEDDING_MODEL", "text-embedding-3-small")

# Clear lru_cache so env vars take effect
from app.config import get_settings

get_settings.cache_clear()


FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_TXT = FIXTURES_DIR / "sample.txt"
SAMPLE_PDF = FIXTURES_DIR / "sample.pdf"
SAMPLE_DOCX = FIXTURES_DIR / "sample.docx"

# Fake 1536-dim embedding (zeros)
FAKE_EMBEDDING = [0.0] * 1536


def make_fake_embedding_response(texts: list[str]):
    """Build a mock OpenAI embedding response."""
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=FAKE_EMBEDDING, index=i) for i in range(len(texts))]
    return mock_response


def make_fake_stream_chunk(content: str):
    """Build a mock streaming completion chunk."""
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta = MagicMock()
    chunk.choices[0].delta.content = content
    return chunk


def make_fake_stream_done():
    """Build a terminal streaming chunk with no content."""
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta = MagicMock()
    chunk.choices[0].delta.content = None
    return chunk


# ---------------------------------------------------------------------------
# Database fixture — temp SQLite file per test
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return a temp SQLite path and set it as the DB_PATH for tests."""
    db_file = tmp_path / "test.db"
    return str(db_file)


# ---------------------------------------------------------------------------
# ChromaDB fixture — ephemeral in-memory client
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def ephemeral_chroma():
    """Inject an ephemeral ChromaDB client for all tests."""
    from app.services import vector_store

    client = chromadb.EphemeralClient()
    vector_store.set_client(client)
    yield client
    # Reset after test
    vector_store.set_client(None)


# ---------------------------------------------------------------------------
# FastAPI test client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_db_path, tmp_path):
    """Create a TestClient with a fresh temp database and ephemeral ChromaDB."""
    os.environ["DATABASE_URL"] = tmp_db_path
    os.environ["UPLOADS_DIR"] = str(tmp_path / "uploads")
    os.environ["VECTOR_STORE_PATH"] = str(tmp_path / "chroma")

    # Clear settings cache so new env vars take effect
    get_settings.cache_clear()

    from app.database import init_db
    import app.database as db_module

    db_module._DB_PATH = tmp_db_path

    # Run init_db synchronously using asyncio
    asyncio.run(init_db(tmp_db_path))

    # Clear session registry
    from app.models.session import sessions

    sessions.clear()

    from app.main import app

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    sessions.clear()


# ---------------------------------------------------------------------------
# Mock OpenAI fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_openai_embeddings():
    """Mock OpenAI embeddings to return FAKE_EMBEDDING without real API calls."""

    async def fake_create(**kwargs):
        texts = kwargs.get("input", [])
        if isinstance(texts, str):
            texts = [texts]
        return make_fake_embedding_response(texts)

    mock_client = MagicMock()
    mock_client.embeddings = MagicMock()
    mock_client.embeddings.create = AsyncMock(side_effect=fake_create)

    with patch("app.services.embedder._get_client", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_openai_chat():
    """Mock OpenAI chat completions to stream a fake answer."""
    fake_tokens = ["The contract", " was signed", " on March 15", " 2024."]

    async def fake_stream_context(*args, **kwargs):
        """Async context manager returning async iterable chunks."""
        chunks = [make_fake_stream_chunk(t) for t in fake_tokens]
        chunks.append(make_fake_stream_done())

        class FakeStream:
            def __aiter__(self):
                return self

            async def __anext__(self):
                if not chunks:
                    raise StopAsyncIteration
                return chunks.pop(0)

        return FakeStream()

    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=fake_stream_context)

    with patch("app.routers.chat.openai.AsyncOpenAI", return_value=mock_client):
        yield mock_client


# ---------------------------------------------------------------------------
# Session fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_session(client):
    """Create a session and return session_id."""
    resp = client.post("/api/sessions")
    assert resp.status_code == 201
    return resp.json()["session_id"]
