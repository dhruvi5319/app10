"""SQLite async database layer using aiosqlite."""

import logging
from datetime import datetime, timezone
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

_DB_PATH: str = "rag_chatbot.db"

DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS documents (
    doc_id          TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    filename        TEXT NOT NULL,
    file_type       TEXT NOT NULL
                    CHECK(file_type IN ('pdf', 'txt', 'docx')),
    file_size_bytes INTEGER NOT NULL
                    CHECK(file_size_bytes > 0),
    status          TEXT NOT NULL DEFAULT 'UPLOADING'
                    CHECK(status IN ('UPLOADING','PARSING','CHUNKING',
                                     'EMBEDDING','INDEXING','READY','FAILED')),
    chunk_count     INTEGER,
    page_count      INTEGER,
    error_message   TEXT,
    uploaded_at     TEXT NOT NULL,
    ready_at        TEXT,
    file_path       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_session ON documents(session_id);
CREATE INDEX IF NOT EXISTS idx_documents_status  ON documents(session_id, status);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id        TEXT PRIMARY KEY,
    doc_id          TEXT NOT NULL
                    REFERENCES documents(doc_id) ON DELETE CASCADE,
    session_id      TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL,
    page_number     INTEGER,
    token_count     INTEGER NOT NULL,
    text            TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc     ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_session ON chunks(session_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_doc_index ON chunks(doc_id, chunk_index);

CREATE TABLE IF NOT EXISTS messages (
    message_id      TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    role            TEXT NOT NULL
                    CHECK(role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    is_refusal      INTEGER,
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);

CREATE TABLE IF NOT EXISTS message_citations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      TEXT NOT NULL
                    REFERENCES messages(message_id) ON DELETE CASCADE,
    chunk_id        TEXT NOT NULL,
    doc_id          TEXT NOT NULL,
    filename        TEXT NOT NULL,
    page_number     INTEGER,
    chunk_index     INTEGER NOT NULL,
    excerpt         TEXT NOT NULL,
    similarity_score REAL
);

CREATE INDEX IF NOT EXISTS idx_citations_message ON message_citations(message_id);
"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


async def init_db(db_path: str = "rag_chatbot.db") -> None:
    global _DB_PATH
    _DB_PATH = db_path
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.executescript(DDL)
        await db.commit()
    logger.info(f"Database initialized at {db_path}")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_DB_PATH)
    await db.execute("PRAGMA foreign_keys = ON")
    db.row_factory = aiosqlite.Row
    return db


# ---------------------------------------------------------------------------
# Document helpers
# ---------------------------------------------------------------------------

async def insert_document(
    db: aiosqlite.Connection,
    doc_id: str,
    session_id: str,
    filename: str,
    file_type: str,
    file_size_bytes: int,
    file_path: str,
    status: str = "UPLOADING",
) -> None:
    await db.execute(
        """
        INSERT INTO documents
            (doc_id, session_id, filename, file_type, file_size_bytes,
             status, uploaded_at, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (doc_id, session_id, filename, file_type, file_size_bytes,
         status, _utcnow(), file_path),
    )
    await db.commit()


async def update_document_status(
    db: aiosqlite.Connection,
    doc_id: str,
    status: str,
    chunk_count: int | None = None,
    page_count: int | None = None,
    error_message: str | None = None,
    ready_at: str | None = None,
) -> None:
    fields = ["status = ?"]
    values: list[Any] = [status]

    if chunk_count is not None:
        fields.append("chunk_count = ?")
        values.append(chunk_count)
    if page_count is not None:
        fields.append("page_count = ?")
        values.append(page_count)
    if error_message is not None:
        fields.append("error_message = ?")
        values.append(error_message)
    if ready_at is not None:
        fields.append("ready_at = ?")
        values.append(ready_at)

    values.append(doc_id)
    await db.execute(
        f"UPDATE documents SET {', '.join(fields)} WHERE doc_id = ?",
        values,
    )
    await db.commit()


async def get_document(db: aiosqlite.Connection, doc_id: str) -> dict | None:
    async with db.execute(
        "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None


async def list_documents(db: aiosqlite.Connection, session_id: str) -> list[dict]:
    async with db.execute(
        "SELECT * FROM documents WHERE session_id = ? ORDER BY uploaded_at ASC",
        (session_id,),
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def delete_document(db: aiosqlite.Connection, doc_id: str) -> None:
    await db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
    await db.commit()


async def count_session_documents(db: aiosqlite.Connection, session_id: str) -> int:
    async with db.execute(
        "SELECT COUNT(*) FROM documents WHERE session_id = ?", (session_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else 0


async def count_ready_documents(db: aiosqlite.Connection, session_id: str) -> int:
    async with db.execute(
        "SELECT COUNT(*) FROM documents WHERE session_id = ? AND status = 'READY'",
        (session_id,),
    ) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else 0


# ---------------------------------------------------------------------------
# Chunk helpers
# ---------------------------------------------------------------------------

async def insert_chunk(
    db: aiosqlite.Connection,
    chunk_id: str,
    doc_id: str,
    session_id: str,
    chunk_index: int,
    page_number: int | None,
    token_count: int,
    text: str,
) -> None:
    await db.execute(
        """
        INSERT INTO chunks
            (chunk_id, doc_id, session_id, chunk_index, page_number,
             token_count, text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (chunk_id, doc_id, session_id, chunk_index, page_number,
         token_count, text, _utcnow()),
    )
    # Commit is batched by caller


# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------

async def insert_message(
    db: aiosqlite.Connection,
    message_id: str,
    session_id: str,
    role: str,
    content: str,
    is_refusal: bool | None = None,
) -> None:
    await db.execute(
        """
        INSERT INTO messages (message_id, session_id, role, content, is_refusal, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (message_id, session_id, role, content,
         int(is_refusal) if is_refusal is not None else None,
         _utcnow()),
    )
    await db.commit()


async def update_message(
    db: aiosqlite.Connection,
    message_id: str,
    content: str,
    is_refusal: bool,
) -> None:
    await db.execute(
        "UPDATE messages SET content = ?, is_refusal = ? WHERE message_id = ?",
        (content, int(is_refusal), message_id),
    )
    await db.commit()


async def get_messages(
    db: aiosqlite.Connection,
    session_id: str,
    limit: int | None = None,
) -> list[dict]:
    query = "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC"
    params: tuple = (session_id,)
    if limit is not None:
        query += " LIMIT ?"
        params = (session_id, limit)
    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_recent_messages(
    db: aiosqlite.Connection,
    session_id: str,
    turns: int,
) -> list[dict]:
    """Get last N turns (user+assistant pairs = 2*turns messages)."""
    limit = turns * 2
    async with db.execute(
        """
        SELECT * FROM messages
        WHERE session_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (session_id, limit),
    ) as cursor:
        rows = await cursor.fetchall()
        return list(reversed([dict(r) for r in rows]))


async def delete_messages(db: aiosqlite.Connection, session_id: str) -> None:
    await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    await db.commit()


# ---------------------------------------------------------------------------
# Citation helpers
# ---------------------------------------------------------------------------

async def insert_citation(
    db: aiosqlite.Connection,
    message_id: str,
    chunk_id: str,
    doc_id: str,
    filename: str,
    page_number: int | None,
    chunk_index: int,
    excerpt: str,
    similarity_score: float | None,
) -> None:
    await db.execute(
        """
        INSERT INTO message_citations
            (message_id, chunk_id, doc_id, filename, page_number,
             chunk_index, excerpt, similarity_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (message_id, chunk_id, doc_id, filename, page_number,
         chunk_index, excerpt, similarity_score),
    )
    # Commit is batched by caller


async def get_citations(db: aiosqlite.Connection, message_id: str) -> list[dict]:
    async with db.execute(
        "SELECT * FROM message_citations WHERE message_id = ? ORDER BY id ASC",
        (message_id,),
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
