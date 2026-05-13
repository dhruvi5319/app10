# Technical Architecture Document: RAGChatbot

**Project:** RAGChatbot  
**Version:** 1.0  
**Date:** 2026-05-13  
**Status:** Draft  
**Based on:** PRD-RAGChatbot v1.0, FRD-RAGChatbot v1.0

---

## 1. Architectural Overview

### 1.1 Architecture Pattern

RAGChatbot follows a **layered client-server architecture** with an embedded **event-driven pipeline** for document ingestion. The system is organized into four primary layers:

1. **Presentation Layer** — React SPA served as static assets; communicates with the backend exclusively via REST API and Server-Sent Events (SSE).
2. **API Layer** — FastAPI application exposing REST endpoints; handles request validation, session management, and orchestration.
3. **Pipeline Layer** — Asynchronous background workers managing document parsing, chunking, and embedding; the RAG retrieval-and-generation loop for query answering.
4. **Storage Layer** — In-memory session store (Python dict), local file system for uploaded files, and a pluggable vector store (Chroma by default).

The architecture is deliberately **single-server for v1** — all components run in the same Python process. This minimizes deployment complexity while validating the core product value. The vector store abstraction layer enables promotion to a hosted vector database (Pinecone) and a persistent SQL store without architectural rework.

### 1.2 Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API framework | FastAPI (Python) | Native async support; excellent ecosystem for LLM/ML workloads; automatic OpenAPI schema generation |
| Frontend framework | React 18 + TypeScript | User-specified; rich ecosystem for chat UI and drag-and-drop; component-based for citation/message reuse |
| Vector store (default) | ChromaDB (in-process) | Zero-config local deployment; supports metadata filtering for session isolation; easy swap to Pinecone |
| LLM streaming | Server-Sent Events (SSE) | Simpler than WebSockets for unidirectional streaming; native browser `EventSource` support |
| Session storage | In-memory Python dict | Sufficient for v1 single-user sessions; no DB dependency; 24-hour TTL with background cleanup |
| Document ingestion | Async background tasks (FastAPI `BackgroundTasks`) | Non-blocking upload response; real-time status polling model |
| State management (frontend) | Zustand | Lightweight; minimal boilerplate vs. Redux; suitable for session/document/message state |

### 1.3 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Browser (React SPA)                                 │
│                                                                               │
│  ┌────────────────────┐   ┌────────────────────┐   ┌─────────────────────┐  │
│  │  Document Library  │   │    Chat View        │   │   Upload Zone       │  │
│  │  (Sidebar Panel)   │   │  (Message Bubbles   │   │  (Drag & Drop)      │  │
│  │                    │   │   + Citations)      │   │                     │  │
│  └────────────────────┘   └────────────────────┘   └─────────────────────┘  │
│           │                        │  SSE stream               │             │
│           └────────────────────────┼───────────────────────────┘             │
│                         REST API / SSE                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │         FastAPI Application          │
                    │                                      │
                    │  ┌──────────────────────────────┐   │
                    │  │       API Router Layer        │   │
                    │  │  /api/documents  /api/chat    │   │
                    │  │  /api/session    /api/health  │   │
                    │  └──────────────┬───────────────┘   │
                    │                 │                    │
                    │  ┌──────────────▼───────────────┐   │
                    │  │      Session Manager          │   │
                    │  │  (In-memory dict, TTL 24h)    │   │
                    │  └──────────────┬───────────────┘   │
                    │                 │                    │
                    │  ┌──────────────▼───────────────┐   │
                    │  │    RAG Pipeline Orchestrator  │   │
                    │  │                               │   │
                    │  │  ┌──────────┐ ┌───────────┐  │   │
                    │  │  │ Ingestion│ │  Query    │  │   │
                    │  │  │ Pipeline │ │ Pipeline  │  │   │
                    │  │  └────┬─────┘ └─────┬─────┘  │   │
                    │  └───────┼─────────────┼────────┘   │
                    │          │             │             │
                    └──────────┼─────────────┼────────────┘
                               │             │
          ┌────────────────────┼─────────────┼────────────────────────┐
          │                    │  Storage Layer                        │
          │   ┌────────────────▼──┐       ┌──▼──────────────────────┐ │
          │   │   In-Memory Store │       │    Vector Store          │ │
          │   │  (Sessions,       │       │  (ChromaDB / FAISS /     │ │
          │   │   Documents,      │       │   Pinecone)              │ │
          │   │   Messages)       │       │                          │ │
          │   └───────────────────┘       └──────────────────────────┘ │
          │                                                              │
          │   ┌──────────────────────────────────────────────────────┐  │
          │   │              Local File System                        │  │
          │   │         ./data/uploads/  (temp files)                │  │
          │   │         ./data/chroma/   (vector index)              │  │
          │   └──────────────────────────────────────────────────────┘  │
          └──────────────────────────────────────────────────────────────┘
                               │             │
          ┌────────────────────┼─────────────┼────────────────────────┐
          │                    │  External APIs                        │
          │   ┌────────────────▼──┐       ┌──▼──────────────────────┐ │
          │   │   Embedding API   │       │     LLM API              │ │
          │   │  OpenAI           │       │  OpenAI GPT-4o /         │ │
          │   │  text-embedding   │       │  Anthropic Claude        │ │
          │   │  -3-small         │       │  (streaming)             │ │
          │   └───────────────────┘       └──────────────────────────┘ │
          └──────────────────────────────────────────────────────────────┘
```

### 1.4 RAG Pipeline Flow

```
Document Upload                    Query Answering
─────────────                    ────────────────
User uploads file                User submits question
       │                                │
       ▼                                ▼
Format validation              Validate query & session
       │                                │
       ▼                                ▼
Text extraction                  Embed query via
(PyMuPDF/python-docx/TXT)       Embedding API
       │                                │
       ▼                                ▼
Text chunking                   Top-k vector search
(512 tokens, 64 overlap)        (cosine similarity)
       │                                │
       ▼                                ▼
Batch embedding via             Confidence check
Embedding API                   (threshold 0.30)
       │                         low │    high │
       ▼                             │         ▼
Vector store indexing          Fallback    Assemble grounded
(with metadata)               response    prompt + chunks
       │                                      │
       ▼                                      ▼
Status → "ready"               LLM streaming call (SSE)
                                              │
                                              ▼
                                       Stream tokens to
                                       frontend via SSE
                                              │
                                              ▼
                                    Attach citations to
                                    "done" event
```

### 1.5 Deployment Topology (v1)

```
┌──────────────────────────────────────────────────┐
│              Single Server / Container            │
│                                                   │
│  Port 3000: React dev server (or Nginx for prod)  │
│  Port 8000: FastAPI (uvicorn)                     │
│                                                   │
│  ./data/uploads/   — temp uploaded files          │
│  ./data/chroma/    — vector index persistence     │
│                                                   │
│  Process memory    — session/document/message     │
└──────────────────────────────────────────────────┘
           │                      │
    OPENAI_API_KEY         ANTHROPIC_API_KEY
    (embeddings + LLM)     (LLM alternative)
```

**v1 Deployment options:**
- **Local development:** `uvicorn main:app --reload` (backend) + `npm run dev` (frontend)
- **Single container:** Docker Compose with `backend` and `frontend` services + shared volume for `./data`
- **Cloud (future):** Replace in-memory store with Redis; replace ChromaDB with Pinecone; add PostgreSQL for persistence

---
## 2. Component Architecture

### 2.1 Backend Components

```
backend/
├── main.py                    # FastAPI app factory; lifespan handler; CORS config
├── config.py                  # AppConfig (pydantic-settings); env var loading
├── dependencies.py            # FastAPI dependency injection (session, config)
│
├── routers/
│   ├── documents.py           # /api/documents routes (upload, list, status, delete)
│   ├── chat.py                # /api/chat routes (query, history, clear, export)
│   ├── session.py             # /api/session routes (reset)
│   └── health.py              # /api/health route
│
├── services/
│   ├── session_service.py     # Session CRUD; TTL management; in-memory store
│   ├── document_service.py    # Document metadata CRUD; status transitions
│   ├── ingestion_service.py   # Async ingestion pipeline orchestrator
│   ├── query_service.py       # RAG query pipeline; SSE streaming
│   ├── embedding_service.py   # Embedding API abstraction (OpenAI / sentence-transformers)
│   ├── llm_service.py         # LLM API abstraction (OpenAI / Anthropic)
│   └── export_service.py      # Transcript export formatting (text / markdown)
│
├── pipeline/
│   ├── parser.py              # Document text extraction (PDF, DOCX, TXT)
│   ├── chunker.py             # Text chunking (fixed-size with overlap)
│   └── retriever.py           # Vector store query + confidence scoring
│
├── vectorstore/
│   ├── base.py                # Abstract VectorStore interface
│   ├── chroma_store.py        # ChromaDB implementation
│   ├── faiss_store.py         # FAISS implementation
│   └── pinecone_store.py      # Pinecone implementation
│
├── models/
│   ├── session.py             # Session, Document, Message Pydantic models
│   ├── requests.py            # API request body schemas
│   └── responses.py           # API response schemas
│
└── utils/
    ├── session_cookie.py      # Cookie read/write helpers
    └── retry.py               # Exponential backoff retry decorator
```

**Component Responsibilities:**

| Component | Responsibility |
|-----------|---------------|
| `session_service.py` | Create, read, update, delete sessions; enforce document/size limits; 24h TTL cleanup |
| `document_service.py` | CRUD for document metadata; status transitions (uploading → indexing → ready/error) |
| `ingestion_service.py` | Orchestrate: parse → chunk → embed → index; manages BackgroundTask lifecycle |
| `query_service.py` | Embed query → retrieve chunks → confidence check → assemble prompt → stream LLM → yield SSE events |
| `embedding_service.py` | Unified embedding interface; handles batching, retries, provider switching |
| `llm_service.py` | Unified LLM interface; handles streaming, retries, timeout enforcement |
| `parser.py` | Format-aware text extraction; returns (text, page_offsets) tuples |
| `chunker.py` | Token-aware text splitting with configurable size/overlap |
| `retriever.py` | Vector store similarity search with session/document metadata filters |
| `base.py` (vectorstore) | Abstract interface: `upsert`, `query`, `delete_by_filter`, `delete_collection` |

### 2.2 Frontend Components

```
frontend/src/
├── main.tsx                   # React entry point
├── App.tsx                    # Root component; session init; layout routing
│
├── components/
│   ├── layout/
│   │   ├── AppLayout.tsx      # Split-panel root: sidebar + main area
│   │   └── Sidebar.tsx        # Collapsible document library sidebar wrapper
│   │
│   ├── documents/
│   │   ├── DocumentLibrary.tsx    # Document list container; polling logic
│   │   ├── DocumentCard.tsx       # Single document: name, status badge, delete button
│   │   ├── UploadZone.tsx         # Drag-and-drop + file picker; validation feedback
│   │   └── StatusBadge.tsx        # Colored badge: uploading/indexing/ready/error
│   │
│   ├── chat/
│   │   ├── ChatView.tsx           # Scrollable message transcript; auto-scroll logic
│   │   ├── MessageBubble.tsx      # User or assistant message bubble with timestamp
│   │   ├── CitationChip.tsx       # Compact citation pill below assistant answers
│   │   ├── CitationPanel.tsx      # Expanded panel showing raw chunk_text
│   │   ├── ChatInput.tsx          # Text area + send button; Enter/Shift+Enter handling
│   │   └── LoadingIndicator.tsx   # Animated "thinking" dots during LLM generation
│   │
│   └── shared/
│       ├── ConfirmModal.tsx       # Reusable confirmation dialog (delete, clear, reset)
│       ├── EmptyState.tsx         # Onboarding / cleared state UI
│       ├── ErrorBanner.tsx        # Inline error with optional Retry button
│       └── SkeletonLoader.tsx     # Animated placeholder for loading states
│
├── hooks/
│   ├── useDocuments.ts        # Document list fetch + polling; delete action
│   ├── useUpload.ts           # File upload with progress; status tracking
│   ├── useChat.ts             # Chat history fetch; SSE stream management
│   └── useSession.ts          # Session init; reset action
│
├── stores/
│   └── appStore.ts            # Zustand store: session, documents, messages, uiState
│
├── api/
│   ├── client.ts              # Axios instance with base URL and cookie config
│   ├── documents.ts           # Document API calls (upload, list, status, delete)
│   ├── chat.ts                # Chat API calls (query SSE, history, clear, export)
│   ├── session.ts             # Session API calls (reset)
│   └── health.ts              # Health check
│
└── types/
    └── index.ts               # TypeScript interfaces for all domain objects
```

**Key Frontend Patterns:**

| Pattern | Implementation |
|---------|---------------|
| Session cookie | Axios `withCredentials: true`; cookie set by backend; auto-created on first request |
| SSE streaming | `EventSource` API on `POST /api/chat/query`; custom hook handles token accumulation |
| Status polling | `useDocuments` hook polls `GET /api/documents` every 3s while any doc is `uploading`/`indexing` |
| Optimistic updates | User message appended to chat immediately on submit before backend response |
| Reduced motion | CSS `@media (prefers-reduced-motion: reduce)` disables all transitions/animations |
| ARIA live regions | `aria-live="polite"` on chat container; status badge text included for screen readers |

---
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
## 4. API Design

### 4.1 API Conventions

| Convention | Value |
|-----------|-------|
| Base URL | `/api` |
| Content-Type (requests) | `application/json` (except multipart upload) |
| Content-Type (responses) | `application/json` (except SSE and file export) |
| Authentication | Session cookie `rag_session_id` (HTTP-only, SameSite=Lax) |
| Session auto-creation | On `GET /api/documents`, `GET /api/chat/history`, `POST /api/session/reset` |
| Error format | `{ "error_code": "SCREAMING_SNAKE_CASE", "message": "...", "detail": {} }` |
| Streaming | Server-Sent Events (SSE) for `POST /api/chat/query` |
| Versioning | No versioning in v1; prefix `/api/v1/` reserved for future |

---

### 4.2 TypeScript Interfaces — Domain Types

```typescript
// ─── Enums ─────────────────────────────────────────────────────────────────

type DocumentStatus = 'uploading' | 'indexing' | 'ready' | 'error';
type MessageRole    = 'user' | 'assistant';
type ConfidenceLevel = 'high' | 'low' | 'none';
type UserRating     = 'positive' | 'negative';
type ExportFormat   = 'text' | 'markdown';

// ─── Session ───────────────────────────────────────────────────────────────

interface Session {
  session_id:        string;       // UUID v4
  created_at:        string;       // ISO 8601
  last_active_at:    string;       // ISO 8601
  document_count:    number;
  total_size_bytes:  number;
  query_in_progress: boolean;
}

// ─── Document ──────────────────────────────────────────────────────────────

interface Document {
  document_id:    string;               // UUID v4
  session_id:     string;               // UUID v4
  filename:       string;
  file_extension: 'pdf' | 'txt' | 'docx';
  mime_type:      string;
  size_bytes:     number;
  status:         DocumentStatus;
  chunk_count:    number;
  chunk_size:     number;               // default 512
  chunk_overlap:  number;               // default 64
  error_reason:   string | null;
  created_at:     string;               // ISO 8601
  indexed_at:     string | null;        // ISO 8601
}

// ─── Citation ──────────────────────────────────────────────────────────────

interface Citation {
  citation_index: number;               // 0-based
  document_id:    string;               // UUID v4
  document_name:  string;
  chunk_index:    number;
  chunk_text:     string;
  page_number:    number | null;
  similarity:     number;               // [0.0, 1.0]
}

// ─── Message ───────────────────────────────────────────────────────────────

interface Message {
  message_id:          string;          // UUID v4
  session_id:          string;          // UUID v4
  role:                MessageRole;
  content:             string;
  citations:           Citation[];      // empty array for user messages
  confidence:          ConfidenceLevel | null;  // null for user messages
  max_similarity:      number | null;   // null for user messages
  user_rating:         UserRating | null;
  rating_recorded_at:  string | null;   // ISO 8601
  created_at:          string;          // ISO 8601
}

// ─── SSE Events ────────────────────────────────────────────────────────────

interface SSETokenEvent {
  token: string;
}

interface SSEDoneEvent {
  done:             true;
  message_id:       string;             // UUID v4
  citations:        Citation[];
  confidence:       ConfidenceLevel;
  max_similarity:   number;
  document_sources: string[];           // deduplicated document filenames
  created_at:       string;             // ISO 8601
}

type SSEEvent = SSETokenEvent | SSEDoneEvent;

// ─── Health ────────────────────────────────────────────────────────────────

type HealthStatus = 'ok' | 'error';

interface HealthChecks {
  vector_store:   HealthStatus;
  embedding_api:  HealthStatus;
  llm_api:        HealthStatus;
}

interface HealthResponse {
  status:    'healthy' | 'degraded';
  timestamp: string;
  checks:    HealthChecks;
}
```

---

### 4.3 TypeScript Interfaces — Request/Response Bodies

```typescript
// ─── Document Upload ───────────────────────────────────────────────────────

// Request: multipart/form-data
// Fields: file (binary), chunk_size? (number), chunk_overlap? (number)

interface UploadDocumentResponse {   // 202 Accepted
  document_id:  string;
  filename:     string;
  status:       'uploading';
  size_bytes:   number;
  created_at:   string;
}

interface DocumentStatusResponse {   // 200 OK
  document_id:   string;
  filename:      string;
  status:        DocumentStatus;
  chunk_count:   number;
  indexed_at:    string | null;
  error_reason:  string | null;
}

// ─── Document List ─────────────────────────────────────────────────────────

interface DocumentListResponse {     // 200 OK
  session_id:        string;
  document_count:    number;
  total_size_bytes:  number;
  documents:         Document[];
}

// ─── Chat Query ────────────────────────────────────────────────────────────

interface ChatQueryRequest {
  query:                string;      // 1–2000 chars
  k?:                   number;      // [1–20]; default 5
  confidence_threshold?: number;     // [0.0–1.0]; default 0.30
  document_filter?:     string;      // UUID of document to restrict retrieval
}

// Response: text/event-stream (SSE)
// Stream: SSETokenEvent events, then final SSEDoneEvent
// Low-confidence fallback: 200 JSON (non-streaming)

interface LowConfidenceFallbackResponse {  // 200 OK (non-streaming)
  message_id:       string;
  answer:           string;          // "The uploaded documents do not contain..."
  citations:        [];
  confidence:       'none';
  max_similarity:   number;
  document_sources: [];
  created_at:       string;
}

// ─── Chat History ──────────────────────────────────────────────────────────

interface ChatHistoryResponse {      // 200 OK
  session_id:    string;
  message_count: number;
  messages:      Message[];
}

// ─── Chat Feedback ─────────────────────────────────────────────────────────

interface FeedbackRequest {
  message_id: string;               // UUID of assistant message
  rating:     UserRating;           // 'positive' | 'negative'
}

interface FeedbackResponse {         // 200 OK
  message_id:   string;
  rating:       UserRating;
  recorded_at:  string;             // ISO 8601
}

// ─── Session Reset ─────────────────────────────────────────────────────────

interface SessionResetResponse {     // 200 OK
  session_id:     string;           // New session ID
  message_count:  number;           // Always 0
  document_count: number;           // Always 0
  created_at:     string;
}

// ─── Error Response ────────────────────────────────────────────────────────

interface APIError {
  error_code: string;               // SCREAMING_SNAKE_CASE
  message:    string;               // Human-readable
  detail:     Record<string, unknown>;
}
```

---

### 4.4 API Endpoint Reference

#### Documents API

| Method | Path | Auth | Request | Response | Description |
|--------|------|------|---------|----------|-------------|
| `POST` | `/api/documents/upload` | Cookie | `multipart/form-data` (file, chunk_size?, chunk_overlap?) | `202 UploadDocumentResponse` | Upload document; start async ingestion |
| `GET` | `/api/documents/{document_id}/status` | Cookie | — | `200 DocumentStatusResponse` | Poll ingestion status |
| `GET` | `/api/documents` | Cookie | — | `200 DocumentListResponse` | List all session documents |
| `DELETE` | `/api/documents/{document_id}` | Cookie | — | `204 No Content` | Delete document + purge vector chunks |

**POST /api/documents/upload — Error codes:**

| HTTP | Code | Trigger |
|------|------|---------|
| 400 | `INVALID_FILE_TYPE` | Extension/MIME not PDF/TXT/DOCX |
| 400 | `FILE_TOO_LARGE` | File > 50MB |
| 400 | `SESSION_STORAGE_LIMIT` | Session total > 200MB |
| 400 | `SESSION_DOCUMENT_LIMIT` | Session has 20 documents |
| 400 | `EMPTY_FILE` | 0-byte file |
| 404 | `SESSION_NOT_FOUND` | Session expired |

**DELETE /api/documents/{document_id} — Error codes:**

| HTTP | Code | Trigger |
|------|------|---------|
| 404 | `DOCUMENT_NOT_FOUND` | Not found or cross-session |
| 500 | `INDEX_DELETE_ERROR` | Vector purge failed |

---

#### Chat API

| Method | Path | Auth | Request | Response | Description |
|--------|------|------|---------|----------|-------------|
| `POST` | `/api/chat/query` | Cookie | `ChatQueryRequest` JSON | `text/event-stream` SSE or `200 LowConfidenceFallbackResponse` | Submit question; stream answer |
| `GET` | `/api/chat/history` | Cookie | — | `200 ChatHistoryResponse` | Full session transcript |
| `DELETE` | `/api/chat/history` | Cookie | — | `204 No Content` | Clear messages (keep documents) |
| `GET` | `/api/chat/export` | Cookie | `?format=text\|markdown` | `200 File download` | Download transcript |

**POST /api/chat/query — Error codes:**

| HTTP | Code | Trigger |
|------|------|---------|
| 400 | `EMPTY_QUERY` | Empty/whitespace query |
| 400 | `QUERY_TOO_LONG` | Query > 2000 chars |
| 404 | `SESSION_NOT_FOUND` | Session expired |
| 422 | `NO_READY_DOCUMENTS` | No ready documents |
| 422 | `DOCUMENT_NOT_READY` | document_filter target not ready |
| 422 | `DOCUMENT_NOT_IN_INDEX` | Filtered document has no chunks |
| 429 | `QUERY_IN_PROGRESS` | Another stream active |
| 503 | `EMBED_ERROR` | Embedding API failure |
| 503 | `LLM_UNAVAILABLE` | LLM API failure |
| 503 | `RETRIEVAL_ERROR` | Vector store failure |
| 504 | `LLM_TIMEOUT` | LLM exceeded 30s |

---

#### Feedback API

| Method | Path | Auth | Request | Response | Description |
|--------|------|------|---------|----------|-------------|
| `POST` | `/api/chat/feedback` | Cookie | `FeedbackRequest` JSON | `200 FeedbackResponse` | Rate an assistant message |

**POST /api/chat/feedback — Error codes:**

| HTTP | Code | Trigger |
|------|------|---------|
| 400 | `INVALID_RATING` | Rating not positive/negative |
| 400 | `INVALID_MESSAGE_ROLE` | Feedback on user message |
| 404 | `MESSAGE_NOT_FOUND` | Message not in session |
| 404 | `SESSION_NOT_FOUND` | Session expired |
| 409 | `FEEDBACK_ALREADY_SUBMITTED` | Already rated |

---

#### Session API

| Method | Path | Auth | Request | Response | Description |
|--------|------|------|---------|----------|-------------|
| `POST` | `/api/session/reset` | Cookie | — | `200 SessionResetResponse` | Reset everything; new session |
| `GET` | `/api/health` | None | — | `200\|503 HealthResponse` | Backend health check |

---

### 4.5 SSE Stream Protocol Detail

The `POST /api/chat/query` endpoint returns a `text/event-stream` response when retrieval confidence meets the threshold. Clients must handle two event structures:

```
# Token events (one per LLM output token)
data: {"token": "The"}\n\n
data: {"token": " acquisition"}\n\n
data: {"token": " was"}\n\n

# Final done event (one, at end of stream)
data: {
  "done": true,
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "citations": [
    {
      "citation_index": 0,
      "document_id": "...",
      "document_name": "contract.pdf",
      "chunk_index": 7,
      "chunk_text": "...full passage text...",
      "page_number": 4,
      "similarity": 0.87
    }
  ],
  "confidence": "high",
  "max_similarity": 0.87,
  "document_sources": ["contract.pdf"],
  "created_at": "2026-05-13T10:05:06Z"
}\n\n
```

**Client implementation notes:**
- Use `EventSource` for GET endpoints; for POST with body, use `fetch` with `ReadableStream` and manual SSE parsing
- Accumulate `token` events into a string buffer; render buffer progressively
- On receiving `done: true`, finalize message and render citations
- On connection error mid-stream: show "Answer generation was interrupted" error bubble

---
## 5. Security Architecture

### 5.1 Authentication Model

RAGChatbot v1 uses **anonymous session-based authentication** — there are no user accounts. Identity is established solely by the session cookie.

| Property | Value |
|----------|-------|
| Mechanism | HTTP-only session cookie `rag_session_id` |
| Cookie flags | `HttpOnly=true`, `SameSite=Lax`, `Secure=true` (in production) |
| Session ID format | UUID v4 (128 bits of entropy; not guessable) |
| Session creation | Auto-created on first `GET /api/documents`, `GET /api/chat/history`, or `POST /api/session/reset` |
| Session lifetime | 24 hours of inactivity; server-side TTL enforced |
| Cross-session isolation | All data access is filtered by `session_id`; cross-session access returns 404 (not 403) to avoid leaking existence |

### 5.2 Authorization Model

Since there are no user accounts in v1, authorization is purely **session-scoped**:

| Rule | Implementation |
|------|---------------|
| Documents are session-private | Every document query includes `session_id` filter; `document_id` alone is never sufficient |
| Messages are session-private | Every message query includes `session_id` filter |
| Vector chunks are session-private | All vector store queries include `session_id` metadata filter |
| Cross-session access returns 404 | `DOCUMENT_NOT_FOUND` / `MESSAGE_NOT_FOUND` — never 403 — to avoid confirming resource existence |
| No admin endpoints | No privileged operations; all routes operate only within caller's session scope |

### 5.3 Document Data Isolation

```
Session A                    Session B
─────────                    ─────────
  doc-1 ──→ chunks            doc-3 ──→ chunks
  doc-2 ──→ chunks            doc-4 ──→ chunks
             │                            │
             └─── VectorStore ────────────┘
                  (filtered by session_id on every query)
```

- **Vector store queries** always pass `session_id` as a metadata filter. Even if two sessions share a Chroma collection (they don't in v1, but defensively), the filter ensures isolation.
- **Chroma collection naming** (`session_{session_id}`) provides physical namespace isolation as a defense-in-depth layer.
- **FAISS** uses per-session index files (`./data/faiss/{session_id}.faiss`), providing filesystem-level isolation.
- **Session reset** (`POST /api/session/reset`) purges all vector data for the old session before returning the new session ID.

### 5.4 Input Validation & Injection Prevention

| Attack Vector | Mitigation |
|--------------|-----------|
| Malicious file upload | Extension + MIME type whitelist; file size limits; parsed in isolated library (PyMuPDF/python-docx) |
| Prompt injection via document content | LLM system prompt explicitly prohibits external knowledge; document content is presented as "context" not "instructions" |
| Prompt injection via user query | Query is appended as a user turn, not injected into the system prompt; system prompt constraints are prepended |
| Cross-session data access | All DB/vector queries include `session_id` filter enforced in the service layer |
| Path traversal (file storage) | Uploaded files stored with UUID-based filenames; original filenames stored as metadata only |
| Large payload DoS | File size limits (50MB/file, 200MB/session); query length limit (2000 chars); session document count limit (20) |
| Concurrent query abuse | `query_in_progress` flag per session; 429 on concurrent query attempt |

### 5.5 API Security

| Concern | Implementation |
|---------|---------------|
| CORS | FastAPI CORS middleware; allowed origins configured via `ALLOWED_ORIGINS` env var (default: `http://localhost:3000`) |
| HTTPS | Required in production; `Secure` cookie flag enforced |
| Rate limiting | `query_in_progress` mutex per session prevents LLM API abuse; global rate limiting delegated to reverse proxy (nginx) in production |
| Error information leakage | Error responses use `error_code` enum + safe `message`; stack traces never exposed to client |
| Secrets management | All API keys loaded from environment variables; never hardcoded; `.env` excluded from version control |

### 5.6 Data Protection

| Category | Approach |
|----------|---------|
| Uploaded files | Stored temporarily in `./data/uploads/{document_id}/`; deleted after successful indexing (or on error cleanup) |
| Vector embeddings | Session-scoped; deleted on session reset or document deletion |
| Chat history | In-memory; lost on server restart; no cross-session persistence |
| API keys | Environment variables only; never logged |
| PII in documents | No PII extraction; content treated as opaque text for RAG pipeline |

### 5.7 Security Headers

```python
# FastAPI middleware configuration
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # restrict in production
)

# Response headers (via middleware or nginx):
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
# Content-Security-Policy: default-src 'self'; ...
```

---
## 6. Technology Stack

### 6.1 Backend Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | Python | 3.11+ | Backend runtime |
| API Framework | FastAPI | 0.111+ | REST API, SSE streaming, async request handling |
| ASGI Server | Uvicorn | 0.29+ | ASGI server; production: uvicorn + gunicorn |
| Data Validation | Pydantic v2 | 2.7+ | Request/response schema validation; config models |
| Settings | pydantic-settings | 2.2+ | Environment variable loading with type coercion |
| Session Cookies | FastAPI built-in | — | `Response.set_cookie`, `Request.cookies` |
| Async Tasks | FastAPI `BackgroundTasks` | — | Non-blocking document ingestion pipeline |
| Document Parsing — PDF | PyMuPDF (`fitz`) | 1.24+ | Fast PDF text extraction with page-level metadata |
| Document Parsing — DOCX | python-docx | 1.1+ | DOCX paragraph/table extraction |
| Document Parsing — TXT | Python stdlib | — | UTF-8 text decode with latin-1 fallback |
| Text Chunking | LangChain `RecursiveCharacterTextSplitter` | 0.2+ | Token-aware chunking with configurable size/overlap |
| Token Counting | tiktoken | 0.7+ | OpenAI-compatible token counting |
| Embedding (OpenAI) | openai | 1.30+ | `text-embedding-3-small` / `text-embedding-3-large` |
| Embedding (local) | sentence-transformers | 3.0+ | `all-MiniLM-L6-v2` for local/offline use |
| LLM (OpenAI) | openai | 1.30+ | GPT-4o with streaming |
| LLM (Anthropic) | anthropic | 0.28+ | Claude 3.5 Sonnet with streaming |
| Vector Store (default) | chromadb | 0.5+ | In-process local vector store with metadata filtering |
| Vector Store (alt) | faiss-cpu | 1.8+ | Local FAISS index with companion metadata JSON |
| Vector Store (cloud) | pinecone | 4.0+ | Pinecone hosted index with namespace isolation |
| HTTP Client | httpx | 0.27+ | Async HTTP for external API calls |
| Testing | pytest + pytest-asyncio | 8.x / 0.23+ | Backend unit/integration tests |
| Test coverage | pytest-cov | 5.x | Coverage reporting (target: > 70% on RAG pipeline) |

### 6.2 Frontend Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | TypeScript | 5.4+ | Type-safe frontend development |
| Framework | React | 18.3+ | Component-based UI |
| Build Tool | Vite | 5.x | Fast dev server and production bundler |
| State Management | Zustand | 4.5+ | Lightweight global state (session, documents, messages) |
| HTTP Client | Axios | 1.7+ | REST API calls with cookie support |
| SSE Streaming | native `fetch` + `ReadableStream` | — | POST SSE stream parsing (EventSource only supports GET) |
| Styling | Tailwind CSS | 3.4+ | Utility-first CSS; responsive breakpoints; WCAG colors |
| Component Library | shadcn/ui + Radix UI | latest | Accessible base components (modals, badges, buttons) |
| Drag and Drop | react-dropzone | 14.x | File drag-and-drop with validation hooks |
| Markdown Rendering | react-markdown | 9.x | Safe rendering of LLM markdown output |
| Icons | Lucide React | 0.381+ | Consistent icon set (trash, thumbs, copy, etc.) |
| Date/Time | date-fns | 3.x | Relative timestamps ("2 min ago") |
| Accessibility Testing | axe-core (dev) | 4.9+ | Automated WCAG AA audit in development |
| Testing | Vitest + React Testing Library | 1.x / 16.x | Component unit tests |

### 6.3 Infrastructure & DevOps

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Containerization | Docker + Docker Compose | 26.x | Local dev and production packaging |
| Reverse Proxy | Nginx | 1.25+ | Static file serving, API proxy, HTTPS termination |
| Environment Config | `.env` files | — | Local dev; production secrets via platform env vars |
| Version Control | Git | — | Source code management |
| Package Manager (BE) | pip + `requirements.txt` | — | Python dependency management |
| Package Manager (FE) | npm | 10.x | Node package management |

### 6.4 Environment Variables

```bash
# ── Embedding ──────────────────────────────────────────────────
EMBEDDING_PROVIDER=openai                    # "openai" | "sentence-transformers"
EMBEDDING_MODEL=text-embedding-3-small       # Model name
EMBEDDING_API_KEY=sk-...                     # OpenAI API key (if provider=openai)

# ── LLM ────────────────────────────────────────────────────────
LLM_PROVIDER=openai                          # "openai" | "anthropic"
LLM_MODEL=gpt-4o                             # Model name
LLM_API_KEY=sk-...                           # Provider API key
LLM_TIMEOUT_SECONDS=30                       # First-token timeout
LLM_MAX_RETRIES=3                            # Max retry attempts

# ── Vector Store ───────────────────────────────────────────────
VECTOR_STORE_TYPE=chroma                     # "chroma" | "faiss" | "pinecone"
VECTOR_STORE_PATH=./data/chroma              # Local path (chroma/faiss)
PINECONE_API_KEY=                            # Pinecone key (if type=pinecone)
PINECONE_INDEX_NAME=                         # Pinecone index name

# ── RAG Parameters ─────────────────────────────────────────────
DEFAULT_TOP_K=5
DEFAULT_CHUNK_SIZE=512
DEFAULT_CHUNK_OVERLAP=64
DEFAULT_CONFIDENCE_THRESHOLD=0.30

# ── Session ────────────────────────────────────────────────────
SESSION_TTL_HOURS=24
MAX_DOCUMENTS_PER_SESSION=20
MAX_FILE_SIZE_BYTES=52428800                 # 50 MB
MAX_SESSION_SIZE_BYTES=209715200             # 200 MB

# ── Server ─────────────────────────────────────────────────────
ALLOWED_ORIGINS=http://localhost:3000
UPLOAD_DIR=./data/uploads
```

---
## 7. Integration Points

### 7.1 Integration Overview

```
┌──────────────────────────────────────────────────────────┐
│                   RAGChatbot Backend                      │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Ingestion Pipeline                               │    │
│  │  parser → chunker → embedder → vector indexer    │    │
│  │                         │              │         │    │
│  └─────────────────────────┼──────────────┼─────────┘    │
│                             │              │              │
│  ┌──────────────────────────┼──────────────┼─────────┐    │
│  │  Query Pipeline          │              │         │    │
│  │  embedder → retriever → LLM caller      │         │    │
│  │       │          │          │           │         │    │
│  └───────┼──────────┼──────────┼───────────┼─────────┘    │
└──────────┼──────────┼──────────┼───────────┼──────────────┘
           │          │          │           │
           ▼          ▼          ▼           ▼
    ┌──────────┐ ┌─────────┐ ┌──────┐ ┌──────────────┐
    │ Document │ │ Embed.  │ │ LLM  │ │ Vector Store │
    │ Parsers  │ │   API   │ │  API │ │  (Chroma /   │
    │(local)   │ │(OpenAI/ │ │(OpenAI│ │ FAISS /      │
    │          │ │sentence-│ │/Claude│ │ Pinecone)    │
    │          │ │ transf.)│ │      │ │              │
    └──────────┘ └─────────┘ └──────┘ └──────────────┘
```

---

### 7.2 Embedding API Integration

**Purpose:** Generate vector representations for document chunks (ingestion) and user queries (at query time).

**Abstraction:** `EmbeddingService` abstract class with concrete `OpenAIEmbeddingService` and `LocalEmbeddingService` implementations. Switched via `EMBEDDING_PROVIDER` env var.

| Property | OpenAI | sentence-transformers |
|----------|--------|-----------------------|
| Model | `text-embedding-3-small` (default) or `text-embedding-3-large` | `all-MiniLM-L6-v2` |
| Dimensions | 1536 / 3072 | 384 |
| Transport | HTTPS REST API | Local Python library |
| Auth | `Authorization: Bearer {EMBEDDING_API_KEY}` | None |
| Batch size | Up to 100 texts per call | Unlimited |
| Cost | ~$0.02 per 1M tokens (3-small) | Free (local CPU) |

**Retry Policy:**
```
HTTP 429 (rate limit): backoff 1s → 2s → 4s (max 3 retries)
HTTP 500/503:          backoff 2s → 2s → 2s (max 3 retries)
Timeout (> 10s/batch): retry once; on second timeout → EMBED_ERROR
Ingestion failure:     set document.status = "error", error_reason = "embed_error"
Query failure:         return 503 EMBED_ERROR to client
```

---

### 7.3 LLM API Integration

**Purpose:** Generate grounded natural language answers from assembled prompts containing retrieved document chunks.

**Abstraction:** `LLMService` abstract class with `OpenAILLMService` and `AnthropicLLMService` implementations. Switched via `LLM_PROVIDER` env var. Both implementations normalize to the same SSE event protocol.

| Property | OpenAI | Anthropic |
|----------|--------|-----------|
| Default model | `gpt-4o` | `claude-3-5-sonnet-20241022` |
| Streaming | Chat Completions streaming API | Messages streaming API |
| Auth header | `Authorization: Bearer {LLM_API_KEY}` | `x-api-key: {LLM_API_KEY}` |
| Temperature | 0.1 | 0.1 |
| Max tokens | 1024 (configurable) | 1024 (configurable) |

**Grounding System Prompt (enforced on all LLM calls):**
```
You are a document assistant. Answer ONLY using the provided document excerpts below.
If the answer cannot be found in the excerpts, say so explicitly.
Do not use any outside knowledge, training data, or general world knowledge.
Do not speculate or infer beyond what is directly stated in the excerpts.
```

**Retry Policy:**
```
HTTP 429:        backoff 5s → 5s (max 2 retries) → 503 LLM_UNAVAILABLE
HTTP 500/503:    backoff 3s → 3s (max 2 retries) → 503 LLM_UNAVAILABLE
First token > 30s: immediate 504 LLM_TIMEOUT (no retry)
Mid-stream drop: close SSE to client; client shows interrupted error
```

---

### 7.4 Vector Store Integration

**Purpose:** Store, search, and delete chunk embeddings with session/document metadata for fast semantic retrieval.

**Abstraction:** `VectorStore` abstract class with three concrete implementations:

```python
class VectorStore(ABC):
    def upsert(self, vectors: list[VectorPayload]) -> None: ...
    def query(self, embedding: list[float], k: int,
              session_id: str, document_id: str | None = None
              ) -> list[QueryResult]: ...
    def delete_by_filter(self, session_id: str,
                         document_id: str | None = None) -> None: ...
    def delete_collection(self, session_id: str) -> None: ...
```

| Backend | Class | Use Case | Collection Naming |
|---------|-------|----------|------------------|
| ChromaDB | `ChromaVectorStore` | Default local dev & single-server prod | `session_{session_id}` |
| FAISS | `FAISSVectorStore` | Local alternative; better perf at scale | `{session_id}.faiss` file |
| Pinecone | `PineconeVectorStore` | Cloud/production deployment | namespace `{session_id}` |

**Metadata stored per vector:**
```python
{
    "document_id":   str,   # UUID
    "session_id":    str,   # UUID
    "chunk_index":   int,
    "document_name": str,
    "chunk_text":    str,
    "page_number":   int | None,
}
```

**Failure Handling:**

| Operation | Failure | Response |
|-----------|---------|---------|
| Upsert (ingestion) | Exception | Set document status = `error`, reason = `index_error` |
| Query | Exception | Return `503 RETRIEVAL_ERROR` |
| Delete (document) | Exception | Return `500 INDEX_DELETE_ERROR` |
| Delete (session reset) | Exception | Log warning; session reset proceeds anyway |

---

### 7.5 Document Parsing Libraries

**Purpose:** Extract plain text from uploaded document files during ingestion. All local — no network calls.

| Format | Library | Function | Notes |
|--------|---------|---------|-------|
| PDF | PyMuPDF (`fitz`) | `fitz.open(bytes)` | Extracts text with page boundaries; does not OCR |
| DOCX | python-docx | `Document(bytes)` | Extracts paragraphs, tables, headers/footers |
| TXT | Python stdlib | `bytes.decode('utf-8')` | Falls back to `latin-1` on UTF-8 decode error |

**Parse Output Contract:**
```python
@dataclass
class ParseResult:
    text: str                       # Full extracted text
    page_offsets: list[int] | None  # Char offset per page (PDF only)
    page_count: int | None          # Total pages (PDF/DOCX estimate only)
```

**Failure Handling:**
- `fitz.FitzError` → `error_reason = "parse_error"`
- Zero-length text after parse → `error_reason = "empty_document"`
- PyMuPDF returns empty text (image-only PDF) → `error_reason = "no_text_layer"`
- `python-docx.PackageNotFoundError` → `error_reason = "parse_error"`
- `UnicodeDecodeError` (TXT) → `error_reason = "parse_error"`

---

### 7.6 Browser Clipboard API (Frontend)

**Purpose:** Copy-to-clipboard for individual answers and citation text (F08).

**Implementation:**
```typescript
async function copyToClipboard(text: string): Promise<void> {
  try {
    // Primary: modern async Clipboard API (requires HTTPS or localhost)
    await navigator.clipboard.writeText(text);
  } catch {
    // Fallback: deprecated execCommand (broad support)
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  }
}
```

No server involvement. Failure is handled silently with a soft UI message.

---

### 7.7 Integration Dependency Matrix

| Feature | Embed API | LLM API | Vector Store | Parse Libs | Clipboard |
|---------|-----------|---------|-------------|-----------|---------|
| F00: Upload & Ingestion | ✅ Required | — | ✅ Required | ✅ Required | — |
| F01: Q&A (RAG) | ✅ Required | ✅ Required | ✅ Required | — | — |
| F02: Citations | — | — | — | — | — |
| F03: Doc Library | — | — | ✅ Delete only | — | — |
| F04: Chat History | — | — | — | — | — |
| F05: Premium UI | — | — | — | — | — |
| F06: Multi-Document | ✅ Required | ✅ Required | ✅ Required | — | — |
| F07: Confidence/Feedback | ✅ Required | ✅ Required | ✅ Required | — | — |
| F08: Export/Copy | — | — | — | — | ✅ Required |
| GET /api/health | ✅ Ping | ✅ Ping | ✅ Ping | — | — |

**Critical Path:** F00 + F01 require all three external integrations (Embed API, LLM API, Vector Store). The health endpoint verifies all three are reachable.

---

*TechArch-RAGChatbot v1.0 — generated 2026-05-13*
