
---

## Y0: Database & Vector Store Schema

This file documents the complete data model for the RAG Chatbot v1. Storage is split into two tiers:

1. **Relational / in-memory store** — Python dicts / SQLite (lightweight) for document metadata, chunk text metadata, and session/chat history.
2. **Vector store** — ChromaDB (default) or FAISS for chunk embeddings and cosine-similarity retrieval.

> **v1 Note:** In-memory storage is acceptable for the session-scoped single-user v1. If SQLite is chosen for metadata persistence, the DDL below applies. If purely in-memory, the schema serves as the canonical data structure specification.

---

### §Sessions — In-Memory State

The session store is an in-memory Python dict, keyed by `session_id`.

```python
# In-memory session registry (server-side)
sessions: dict[str, SessionState] = {}

@dataclass
class SessionState:
    session_id: str          # UUID v4
    created_at: datetime
    documents: list[str]     # list of doc_ids in this session
    messages: list[Message]  # ordered chat history
```

**Session lifecycle:** Created on `POST /api/sessions`. Destroyed on page refresh (client assigns new UUID or server expires after N minutes inactivity — configurable, default 60 min).

---

### §Documents — SQLite DDL

```sql
-- documents table: one row per uploaded document per session
CREATE TABLE documents (
    doc_id          TEXT PRIMARY KEY,           -- UUID v4
    session_id      TEXT NOT NULL,              -- owning session UUID
    filename        TEXT NOT NULL,              -- original upload filename
    file_type       TEXT NOT NULL               -- 'pdf' | 'txt' | 'docx'
                    CHECK(file_type IN ('pdf', 'txt', 'docx')),
    file_size_bytes INTEGER NOT NULL            -- file size in bytes
                    CHECK(file_size_bytes > 0),
    status          TEXT NOT NULL DEFAULT 'UPLOADING'
                    CHECK(status IN ('UPLOADING','PARSING','CHUNKING',
                                     'EMBEDDING','INDEXING','READY','FAILED')),
    chunk_count     INTEGER,                    -- set after INDEXING; null during processing
    page_count      INTEGER,                    -- PDF only; null for TXT/DOCX
    error_message   TEXT,                       -- populated on FAILED status
    uploaded_at     TEXT NOT NULL,              -- ISO 8601 UTC timestamp
    ready_at        TEXT,                       -- ISO 8601 UTC timestamp; null until READY
    file_path       TEXT NOT NULL               -- server-side path: uploads/{session_id}/{doc_id}/{filename}
);

CREATE INDEX idx_documents_session ON documents(session_id);
CREATE INDEX idx_documents_status  ON documents(session_id, status);
```

---

### §Chunks — SQLite DDL

```sql
-- chunks table: one row per text chunk per document
CREATE TABLE chunks (
    chunk_id        TEXT PRIMARY KEY,           -- '{doc_id}:{chunk_index}' or UUID v4
    doc_id          TEXT NOT NULL
                    REFERENCES documents(doc_id) ON DELETE CASCADE,
    session_id      TEXT NOT NULL,              -- denormalised for fast session-scoped deletes
    chunk_index     INTEGER NOT NULL,           -- 0-based position within document
    page_number     INTEGER,                    -- 1-based PDF page; NULL for TXT/DOCX
    token_count     INTEGER NOT NULL,           -- actual token count of this chunk
    text            TEXT NOT NULL,              -- verbatim chunk text (UTF-8)
    created_at      TEXT NOT NULL               -- ISO 8601 UTC timestamp
);

CREATE INDEX idx_chunks_doc    ON chunks(doc_id);
CREATE INDEX idx_chunks_session ON chunks(session_id);
-- Ensure chunks are unique per document and index position
CREATE UNIQUE INDEX idx_chunks_doc_index ON chunks(doc_id, chunk_index);
```

---

### §Chat — In-Memory / SQLite DDL

```sql
-- messages table: one row per user or assistant message in a session
CREATE TABLE messages (
    message_id      TEXT PRIMARY KEY,           -- UUID v4
    session_id      TEXT NOT NULL,              -- owning session UUID
    role            TEXT NOT NULL               -- 'user' | 'assistant'
                    CHECK(role IN ('user', 'assistant')),
    content         TEXT NOT NULL,              -- full message text (markdown for assistant)
    is_refusal      INTEGER,                    -- 1 = refusal, 0 = normal, NULL for user msgs
    created_at      TEXT NOT NULL               -- ISO 8601 UTC timestamp
);

CREATE INDEX idx_messages_session ON messages(session_id, created_at);

-- message_citations: links an assistant message to the chunks it used
CREATE TABLE message_citations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      TEXT NOT NULL
                    REFERENCES messages(message_id) ON DELETE CASCADE,
    chunk_id        TEXT NOT NULL,              -- references chunks.chunk_id
    doc_id          TEXT NOT NULL,              -- denormalised for convenience
    filename        TEXT NOT NULL,              -- denormalised filename at time of answer
    page_number     INTEGER,                    -- denormalised page number at time of answer
    chunk_index     INTEGER NOT NULL,
    excerpt         TEXT NOT NULL,              -- verbatim chunk text at time of retrieval
    similarity_score REAL                       -- cosine similarity score (0.0–1.0)
);

CREATE INDEX idx_citations_message ON message_citations(message_id);
```

---

### §Vector Store — ChromaDB Collection Schema

ChromaDB uses a per-session collection named `session_{session_id}`.

```python
# ChromaDB collection per session
collection_name = f"session_{session_id}"  # e.g., "session_f47ac10b-58cc-..."

# Each chunk is upserted into the collection with:
collection.upsert(
    ids=[chunk_id],                  # str: '{doc_id}:{chunk_index}'
    embeddings=[embedding_vector],   # list[float]: dimension depends on model
                                     #   text-embedding-3-small → 1536-dim
    documents=[chunk_text],          # str: verbatim chunk text
    metadatas=[{
        "doc_id":       doc_id,      # str: UUID v4
        "session_id":   session_id,  # str: UUID v4
        "filename":     filename,    # str: e.g., "report.pdf"
        "file_type":    file_type,   # str: 'pdf' | 'txt' | 'docx'
        "chunk_index":  chunk_index, # int: 0-based
        "page_number":  page_number, # int | None: 1-based PDF page
        "token_count":  token_count, # int
    }]
)
```

**Deletion** by `doc_id` (used in F03 document delete):
```python
collection.delete(where={"doc_id": doc_id})
```

**Query** (used in F01 retrieval):
```python
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=top_k,
    where={"session_id": session_id},  # namespace isolation
    include=["documents", "metadatas", "distances"]
)
```

---

### §FAISS Alternative

When `VECTOR_STORE=faiss`, a FAISS `IndexFlatIP` (inner-product, i.e., cosine similarity after L2 normalisation) is used. Metadata is stored separately in the SQLite `chunks` table. The FAISS index is serialised to `{VECTOR_STORE_PATH}/session_{session_id}.faiss` on disk. Chunk IDs are mapped via an in-memory list parallel to the FAISS index.

---

### §File Storage Layout

```
{UPLOADS_DIR}/
└── {session_id}/
    └── {doc_id}/
        └── {original_filename}       # raw uploaded file; retained for potential re-processing
```

Files are deleted when the corresponding document record is deleted (F03).

---

### §Constraints Summary

| Constraint | Value | Source |
|-----------|-------|--------|
| Max documents per session | 10 | F00, F07 |
| Max file size | 20 MB | F00, F07 |
| Chunk size range | 100–2000 tokens | F07 |
| Chunk overlap | 0–500 tokens; < chunk_size | F07 |
| Top-k range | 1–20 | F07 |
| Supported file types | pdf, txt, docx | F00 |
| Session timeout | 60 min inactivity (configurable) | F04 |
| Embedding dimensions | 1536 (text-embedding-3-small) | Y3 |
