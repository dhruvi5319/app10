## 3. Data Model

### 3.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         In-Memory Store                          │
│                                                                   │
│  ┌──────────────────┐          ┌──────────────────────────────┐  │
│  │     Session      │          │           Document           │  │
│  ├──────────────────┤          ├──────────────────────────────┤  │
│  │ session_id (PK)  │◄────────┤ session_id (FK)              │  │
│  │ created_at       │  1      │ document_id (PK)             │  │
│  │ last_active_at   │  ──     │ filename                     │  │
│  │ document_ids[]   │  │      │ file_extension               │  │
│  │ message_ids[]    │  M      │ mime_type                    │  │
│  │ total_size_bytes │         │ size_bytes                   │  │
│  │ query_in_progress│         │ status (enum)                │  │
│  └──────────────────┘         │ chunk_count                  │  │
│           │                   │ chunk_size                   │  │
│           │ 1                 │ chunk_overlap                │  │
│           │                   │ error_reason                 │  │
│           │ M                 │ created_at                   │  │
│           ▼                   │ indexed_at                   │  │
│  ┌──────────────────┐         └──────────────────────────────┘  │
│  │     Message      │                      │                     │
│  ├──────────────────┤                      │ 1                   │
│  │ message_id (PK)  │                      │                     │
│  │ session_id (FK)  │                      │ M                   │
│  │ role (enum)      │                      ▼                     │
│  │ content          │         ┌──────────────────────────────┐  │
│  │ citations (JSON) │         │      ChunkMetadata            │  │
│  │ confidence (enum)│         │   (stored in vector store)    │  │
│  │ max_similarity   │         ├──────────────────────────────┤  │
│  │ user_rating      │         │ vector_id (PK, auto)         │  │
│  │ rating_recorded  │         │ document_id (FK)             │  │
│  │ created_at       │         │ session_id (FK)              │  │
│  └──────────────────┘         │ chunk_index                  │  │
│           │                   │ document_name                │  │
│           │ contains          │ chunk_text                   │  │
│           │ (embedded JSON)   │ page_number                  │  │
│           ▼                   │ token_count                  │  │
│  ┌──────────────────┐         │ embedding (vector)           │  │
│  │    Citation      │         └──────────────────────────────┘  │
│  │  (JSON array in  │                                            │
│  │   Message)       │                                            │
│  ├──────────────────┤                                            │
│  │ citation_index   │                                            │
│  │ document_id      │                                            │
│  │ document_name    │                                            │
│  │ chunk_index      │                                            │
│  │ chunk_text       │                                            │
│  │ page_number      │                                            │
│  │ similarity       │                                            │
│  └──────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Schema Notes

RAGChatbot v1 uses **in-memory session storage** (Python dicts) rather than a persistent SQL database, by design (no auth, single-user sessions, process lifetime scope). DDL is provided in SQL (PostgreSQL-compatible) for:
1. Future migration to persistent storage
2. Clear specification of all field types, constraints, and indexes
3. Reference for any developer implementing an equivalent persistent backend

The vector store (ChromaDB/FAISS/Pinecone) is managed via its native SDK; the `chunks` table below represents the logical schema of chunk metadata stored as vector payloads.

---

### 3.3 DDL — Sessions Table

```sql
-- ============================================================
-- sessions
-- One row per active browser session.
-- v1: mirrored in Python in-memory dict keyed by session_id.
-- ============================================================
CREATE TABLE sessions (
    session_id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at          TIMESTAMPTZ NOT NULL    DEFAULT NOW(),
    last_active_at      TIMESTAMPTZ NOT NULL    DEFAULT NOW(),
    total_size_bytes    BIGINT      NOT NULL    DEFAULT 0
                            CHECK (total_size_bytes >= 0),
    query_in_progress   BOOLEAN     NOT NULL    DEFAULT FALSE,
    expires_at          TIMESTAMPTZ NOT NULL    DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Index for TTL cleanup job
CREATE INDEX idx_sessions_expires_at ON sessions (expires_at);

-- ============================================================
-- Enforced limits (application layer, not DB constraints):
--   document count per session  ≤ 20
--   total_size_bytes            ≤ 209715200 (200 MB)
-- ============================================================
```

---

### 3.4 DDL — Documents Table

```sql
-- ============================================================
-- documents
-- One row per uploaded file.
-- v1: stored in Python dict within session object.
-- ============================================================

CREATE TYPE document_status AS ENUM (
    'uploading',
    'indexing',
    'ready',
    'error'
);

CREATE TABLE documents (
    document_id         UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID            NOT NULL
                            REFERENCES sessions (session_id)
                            ON DELETE CASCADE,
    filename            TEXT            NOT NULL,
    file_extension      VARCHAR(10)     NOT NULL
                            CHECK (file_extension IN ('pdf', 'txt', 'docx')),
    mime_type           TEXT            NOT NULL,
    size_bytes          BIGINT          NOT NULL
                            CHECK (size_bytes > 0 AND size_bytes <= 52428800),
    status              document_status NOT NULL    DEFAULT 'uploading',
    chunk_count         INTEGER         NOT NULL    DEFAULT 0
                            CHECK (chunk_count >= 0),
    chunk_size          INTEGER         NOT NULL    DEFAULT 512
                            CHECK (chunk_size BETWEEN 128 AND 2048),
    chunk_overlap       INTEGER         NOT NULL    DEFAULT 64
                            CHECK (chunk_overlap >= 0),
    error_reason        TEXT            NULL,
    created_at          TIMESTAMPTZ     NOT NULL    DEFAULT NOW(),
    indexed_at          TIMESTAMPTZ     NULL,
    -- Derived constraint: chunk_overlap < chunk_size (enforced at app layer)
    CONSTRAINT chk_chunk_overlap_lt_size CHECK (chunk_overlap < chunk_size)
);

-- Index for session-scoped document listing
CREATE INDEX idx_documents_session_id     ON documents (session_id);
-- Index for status polling
CREATE INDEX idx_documents_status         ON documents (session_id, status);
-- Index for document deletion by session
CREATE INDEX idx_documents_session_status ON documents (session_id, status, document_id);

-- ============================================================
-- Allowed error_reason values (enforced at app layer):
--   'parse_error' | 'no_text_layer' | 'embed_error'
--   'index_error' | 'empty_document'
-- ============================================================
```

---

### 3.5 DDL — Chunks Table (Vector Store Metadata)

```sql
-- ============================================================
-- chunks
-- Logical schema for chunk metadata stored as vector payloads
-- in ChromaDB/FAISS/Pinecone. Not a SQL table in v1.
-- Provided for migration reference and documentation clarity.
-- ============================================================
CREATE TABLE chunks (
    chunk_id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID        NOT NULL
                        REFERENCES documents (document_id)
                        ON DELETE CASCADE,
    session_id      UUID        NOT NULL
                        REFERENCES sessions (session_id)
                        ON DELETE CASCADE,
    chunk_index     INTEGER     NOT NULL
                        CHECK (chunk_index >= 0),
    document_name   TEXT        NOT NULL,
    chunk_text      TEXT        NOT NULL
                        CHECK (char_length(chunk_text) > 0),
    page_number     INTEGER     NULL
                        CHECK (page_number IS NULL OR page_number > 0),
    token_count     INTEGER     NOT NULL
                        CHECK (token_count > 0),
    -- embedding stored in vector store, not in SQL
    -- embedding      vector(1536) NOT NULL,  -- pgvector for future migration
    created_at      TIMESTAMPTZ NOT NULL    DEFAULT NOW(),

    UNIQUE (document_id, chunk_index)
);

-- Index for session-scoped retrieval (used in all vector queries)
CREATE INDEX idx_chunks_session_id   ON chunks (session_id);
-- Index for document-scoped deletion (used in F03 delete)
CREATE INDEX idx_chunks_document_id  ON chunks (document_id);
-- Index for document filter queries (F06)
CREATE INDEX idx_chunks_doc_session  ON chunks (session_id, document_id);

-- ============================================================
-- In ChromaDB: stored as collection "session_{session_id}"
--   with metadata: document_id, session_id, chunk_index,
--                  document_name, chunk_text, page_number
-- In FAISS: stored as .faiss binary + _meta.json companion
-- ============================================================
```

---

### 3.6 DDL — Messages Table

```sql
-- ============================================================
-- messages
-- One row per chat message (user question or assistant answer).
-- v1: stored in Python list within session object.
-- ============================================================

CREATE TYPE message_role AS ENUM ('user', 'assistant');

CREATE TYPE confidence_level AS ENUM ('high', 'low', 'none');

CREATE TYPE user_rating AS ENUM ('positive', 'negative');

CREATE TABLE messages (
    message_id          UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID            NOT NULL
                            REFERENCES sessions (session_id)
                            ON DELETE CASCADE,
    role                message_role    NOT NULL,
    content             TEXT            NOT NULL
                            CHECK (char_length(content) > 0),
    -- citations stored as JSONB array (see Citation schema below)
    citations           JSONB           NOT NULL    DEFAULT '[]'::jsonb,
    confidence          confidence_level NULL,
    max_similarity      NUMERIC(5, 4)   NULL
                            CHECK (max_similarity IS NULL
                                OR max_similarity BETWEEN 0.0 AND 1.0),
    user_rating         user_rating     NULL,
    rating_recorded_at  TIMESTAMPTZ     NULL,
    created_at          TIMESTAMPTZ     NOT NULL    DEFAULT NOW(),

    -- user messages must not have confidence or similarity
    CONSTRAINT chk_user_msg_no_confidence
        CHECK (role <> 'user' OR (confidence IS NULL AND max_similarity IS NULL)),
    -- assistant messages must have citations array (can be empty)
    -- assistant messages must have confidence (unless NULL for legacy)
    -- rating recorded_at must accompany a rating
    CONSTRAINT chk_rating_timestamp
        CHECK ((user_rating IS NULL AND rating_recorded_at IS NULL)
            OR (user_rating IS NOT NULL AND rating_recorded_at IS NOT NULL))
);

-- Index for session transcript retrieval (ordered)
CREATE INDEX idx_messages_session_created ON messages (session_id, created_at ASC);
-- Index for feedback submission by message_id + session_id
CREATE INDEX idx_messages_session_id      ON messages (session_id);
-- Index for feedback lookup
CREATE INDEX idx_messages_message_id      ON messages (message_id);
-- GIN index for JSONB citation queries (future analytics)
CREATE INDEX idx_messages_citations_gin   ON messages USING GIN (citations);

-- ============================================================
-- Citation JSONB element schema (array of):
-- {
--   "citation_index": integer,       -- 0-based position in array
--   "document_id":    uuid string,   -- source document UUID
--   "document_name":  string,        -- filename of source document
--   "chunk_index":    integer,       -- chunk position in document
--   "chunk_text":     string,        -- raw passage text
--   "page_number":    integer|null,  -- source page (null for TXT)
--   "similarity":     float          -- cosine similarity [0.0, 1.0]
-- }
-- Constraints (enforced at app layer):
--   max 10 citations per message (top 10 by similarity)
--   chunk_text must not be empty string
--   similarity in [0.0, 1.0]
--   citation_index = array position (0, 1, 2, ...)
-- ============================================================
```

---

### 3.7 DDL — Sessions Summary View (convenience)

```sql
-- ============================================================
-- session_summary (view)
-- Convenience view aggregating session stats.
-- ============================================================
CREATE VIEW session_summary AS
SELECT
    s.session_id,
    s.created_at,
    s.last_active_at,
    s.expires_at,
    s.query_in_progress,
    COUNT(DISTINCT d.document_id)
        FILTER (WHERE d.status = 'ready')   AS ready_document_count,
    COUNT(DISTINCT d.document_id)           AS total_document_count,
    COALESCE(SUM(d.size_bytes), 0)          AS total_size_bytes,
    COUNT(DISTINCT m.message_id)            AS message_count
FROM sessions s
LEFT JOIN documents d ON d.session_id = s.session_id
LEFT JOIN messages  m ON m.session_id = s.session_id
GROUP BY s.session_id;
```

---
