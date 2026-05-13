# Phase 1 Plan: Foundation & RAG Pipeline

## Goal

Stand up a fully operational Python/FastAPI backend that can receive a document, run it through the complete parse → chunk → embed → index pipeline, then accept a natural-language query and return a cited, strictly-grounded answer — all verifiable through the REST API with no frontend required.

---

## Directory Layout (target state after this phase)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory, lifespan, CORS, router registration
│   ├── config.py                  # Settings (Pydantic BaseSettings), env var defaults
│   ├── database.py                # SQLite connection, table creation, helper queries
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py             # SessionState dataclass + in-memory registry
│   │   ├── document.py            # Pydantic request/response schemas for documents
│   │   ├── chat.py                # Pydantic schemas for chat messages, citations
│   │   └── errors.py              # Error response schema, error code enum
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── sessions.py            # POST /api/sessions, GET /api/sessions/{id}
│   │   ├── documents.py           # Upload, status, list, delete, SSE stream
│   │   └── chat.py                # POST /api/chat/query, SSE stream, history, delete
│   ├── services/
│   │   ├── __init__.py
│   │   ├── parser.py              # PDF (PyMuPDF), DOCX (python-docx), TXT parser
│   │   ├── chunker.py             # Token-based splitter, configurable size/overlap
│   │   ├── embedder.py            # OpenAI text-embedding-3-small, batching, backoff
│   │   ├── vector_store.py        # ChromaDB wrapper: upsert, query, delete
│   │   └── ingestion.py           # Orchestrator: runs parse→chunk→embed→index pipeline
│   └── utils/
│       ├── __init__.py
│       └── file_validation.py     # Magic-byte MIME detection, size checks
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures: test client, temp DB, mock OpenAI
│   ├── test_sessions.py
│   ├── test_documents.py
│   ├── test_ingestion.py          # Unit tests: parser, chunker, embedder
│   ├── test_chat.py
│   └── fixtures/
│       ├── sample.pdf             # Small real PDF for integration tests
│       ├── sample.docx
│       └── sample.txt
├── uploads/                       # Runtime file storage (gitignored)
├── chroma_db/                     # ChromaDB persistence dir (gitignored)
├── rag_chatbot.db                 # SQLite database file (gitignored)
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Tasks

### T01 — Project Scaffold & Configuration

**Description:** Create the `backend/` directory structure, dependency files, environment configuration, and the FastAPI application entry point. This is the foundation everything else builds on.

**Files to create/modify:**
- `backend/pyproject.toml` — project metadata, tool config (pytest, ruff)
- `backend/requirements.txt` — pinned dependencies:
  ```
  fastapi==0.111.0
  uvicorn[standard]==0.29.0
  python-multipart==0.0.9
  pydantic==2.7.1
  pydantic-settings==2.2.1
  python-dotenv==1.0.1
  openai==1.30.1
  chromadb==0.5.0
  pymupdf==1.24.3
  python-docx==1.1.2
  langchain-text-splitters==0.2.1
  tiktoken==0.7.0
  python-magic==0.4.27
  aiosqlite==0.20.0
  httpx==0.27.0
  pytest==8.2.0
  pytest-asyncio==0.23.6
  ```
- `backend/.env.example` — all env vars with defaults documented:
  ```
  # Required
  OPENAI_API_KEY=sk-...

  # LLM settings
  LLM_MODEL=gpt-4o
  LLM_TEMPERATURE=0.0

  # Embedding settings
  EMBEDDING_MODEL=text-embedding-3-small

  # Pipeline tuning
  CHUNK_SIZE=500
  CHUNK_OVERLAP=50
  TOP_K=5
  CHAT_HISTORY_TURNS=10
  MAX_FILE_SIZE_MB=20
  MAX_DOCS_PER_SESSION=10

  # Storage paths
  UPLOADS_DIR=uploads
  VECTOR_STORE_PATH=chroma_db
  DATABASE_URL=rag_chatbot.db

  # Server
  LOG_LEVEL=INFO
  ```
- `backend/app/config.py` — Pydantic `BaseSettings` class `Settings` reading all env vars above; `get_settings()` cached singleton; hard-coded defaults for every field
- `backend/app/__init__.py` — empty
- `backend/app/main.py` — FastAPI app factory with `lifespan` context manager (DB init on startup), CORS middleware (`allow_origins=["*"]` for dev), router inclusion, global exception handler returning `{"error_code": ..., "message": ...}`
- `backend/app/models/__init__.py` — empty
- `backend/app/models/errors.py` — `ErrorCode` string enum (all codes from FRD F00/F01), `ErrorResponse` Pydantic model
- `backend/app/routers/__init__.py` — empty
- `backend/app/services/__init__.py` — empty
- `backend/app/utils/__init__.py` — empty

**Acceptance criteria:**
- [ ] `cd backend && pip install -r requirements.txt` completes without errors
- [ ] `uvicorn app.main:app --reload` starts the server on port 8000
- [ ] `GET http://localhost:8000/` returns `{"status": "ok"}` (health check endpoint)
- [ ] `GET http://localhost:8000/docs` renders the Swagger UI
- [ ] `from app.config import get_settings; s = get_settings()` resolves all defaults without a `.env` file (except OPENAI_API_KEY)
- [ ] All `ErrorCode` enum values from FRD F00/F01 are present: `SESSION_NOT_FOUND`, `INVALID_MIME_TYPE`, `FILE_TOO_LARGE`, `DOCUMENT_LIMIT_REACHED`, `EMPTY_FILE`, `NO_EXTRACTABLE_TEXT`, `EMBEDDING_RATE_LIMIT`, `EMBEDDING_UNAVAILABLE`, `PARSE_FAILURE`, `EMPTY_QUERY`, `QUERY_TOO_LONG`, `NO_DOCUMENTS_READY`, `LLM_RATE_LIMIT`, `LLM_UNAVAILABLE`, `LLM_EMPTY_RESPONSE`, `RETRIEVAL_FAILURE`

---

### T02 — SQLite Database Layer

**Description:** Implement the SQLite schema (DDL) and async database helper module. Creates all four tables on startup with the exact constraints from FRD Y0.

**Files to create/modify:**
- `backend/app/database.py` — async `aiosqlite` connection pool, `init_db()` function that runs the DDL below on startup, helper functions: `insert_document()`, `update_document_status()`, `get_document()`, `list_documents()`, `delete_document()`, `insert_chunk()`, `insert_message()`, `get_messages()`, `delete_messages()`, `insert_citation()`, `get_citations()`

**DDL (exact from FRD Y0 — must be reproduced character-for-character):**

```sql
-- documents table
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

-- chunks table
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

-- messages table
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

-- message_citations table
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
```

**Acceptance criteria:**
- [ ] `init_db()` runs without error on a fresh SQLite file and creates all four tables with correct columns
- [ ] All CHECK constraints are enforced (attempt to insert invalid `status` raises `sqlite3.IntegrityError`)
- [ ] `ON DELETE CASCADE` is active: deleting a document row deletes its chunks; deleting a message row deletes its citations
- [ ] `UNIQUE INDEX` on `(doc_id, chunk_index)` raises `IntegrityError` on duplicate insert
- [ ] All helper functions (`insert_document`, `update_document_status`, etc.) callable in tests without errors

---

### T03 — Session Management Endpoints

**Description:** Implement the in-memory session registry and the two session API endpoints. Sessions are the namespace for all document and chat state.

**Files to create/modify:**
- `backend/app/models/session.py` — `SessionState` dataclass (fields: `session_id: str`, `created_at: datetime`, `document_ids: list[str]`, `last_active: datetime`); `sessions: dict[str, SessionState]` module-level registry
- `backend/app/routers/sessions.py` — two endpoints:
  - `POST /api/sessions` → generates UUID v4 session_id, creates `SessionState`, stores in registry, returns `{"session_id": ..., "created_at": ...}` with HTTP 201
  - `GET /api/sessions/{session_id}` → looks up registry; returns `{"session_id": ..., "created_at": ..., "document_count": N}` with HTTP 200, or `404` with `ErrorResponse(error_code="SESSION_NOT_FOUND", ...)` if not found
- `backend/app/main.py` — include `sessions` router under prefix `/api`

**Acceptance criteria:**
- [ ] `POST /api/sessions` returns HTTP 201 with a valid UUID v4 `session_id`
- [ ] `GET /api/sessions/{session_id}` with valid id returns HTTP 200 with `document_count: 0`
- [ ] `GET /api/sessions/nonexistent-id` returns HTTP 404 with `error_code: "SESSION_NOT_FOUND"`
- [ ] Two sequential `POST /api/sessions` calls return two distinct session IDs
- [ ] Test: `tests/test_sessions.py` — covers 201 creation, 200 lookup, 404 not-found

---

### T04 — File Validation Utility

**Description:** Implement the magic-byte MIME detection and upload validation logic used by the document upload endpoint. This is a pure utility module with no external dependencies beyond `python-magic`.

**Files to create/modify:**
- `backend/app/utils/file_validation.py` — functions:
  - `detect_mime_type(file_bytes: bytes) -> str` — uses `python-magic` to detect MIME from first 2048 bytes
  - `validate_upload(filename: str, file_bytes: bytes, file_size: int, settings: Settings) -> None` — raises `HTTPException` with correct status code and `ErrorCode` for each failure case:
    - size > `settings.MAX_FILE_SIZE_MB * 1024 * 1024` → HTTP 413, `FILE_TOO_LARGE`
    - size == 0 → HTTP 422, `EMPTY_FILE`
    - detected MIME not in `{application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, text/plain, text/*}` → HTTP 422, `INVALID_MIME_TYPE`

**MIME mapping (exact):**
```python
ALLOWED_MIMES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}
# Also accept any text/* as txt (covers text/x-python, etc. edge cases)
```

**Acceptance criteria:**
- [ ] `validate_upload` raises `HTTP 413` for a 21 MB buffer
- [ ] `validate_upload` raises `HTTP 422 / EMPTY_FILE` for 0-byte buffer
- [ ] `validate_upload` raises `HTTP 422 / INVALID_MIME_TYPE` for a `.jpg` file renamed to `.pdf`
- [ ] `validate_upload` passes for a valid 1 MB PDF buffer with matching magic bytes
- [ ] Test: unit tests in `tests/test_documents.py` covering each validation branch

---

### T05 — Document Parser Layer

**Description:** Implement the three-format parser service that converts uploaded files to `(text, page_map)` pairs. Handles PyMuPDF for PDF (page-aware), python-docx for DOCX, and UTF-8/latin-1 fallback for TXT.

**Files to create/modify:**
- `backend/app/services/parser.py` — functions:
  - `ParsedDocument` dataclass: `text: str`, `page_chunks: list[tuple[int, str]]` (page_number, page_text; empty list for non-PDF), `page_count: int | None`
  - `parse_pdf(file_bytes: bytes) -> ParsedDocument` — uses `fitz.open(stream=file_bytes, filetype="pdf")`; iterates pages with `page.get_text()`; raises `HTTPException(422, PARSE_FAILURE)` on corrupt file; raises `HTTPException(422, NO_EXTRACTABLE_TEXT)` if total extracted text is empty/whitespace
  - `parse_docx(file_bytes: bytes) -> ParsedDocument` — uses `python_docx.Document(io.BytesIO(file_bytes))`; extracts paragraph text and table cell text; page_count = None
  - `parse_txt(file_bytes: bytes) -> ParsedDocument` — tries `file_bytes.decode("utf-8")`; falls back to `file_bytes.decode("latin-1")`; page_count = None
  - `parse_document(file_bytes: bytes, file_type: str) -> ParsedDocument` — dispatcher

**Acceptance criteria:**
- [ ] `parse_pdf` with `tests/fixtures/sample.pdf` returns non-empty text and `page_count > 0`
- [ ] `parse_pdf` with a corrupt byte buffer raises `HTTP 422 / PARSE_FAILURE`
- [ ] `parse_pdf` with an image-only PDF (no text layer) raises `HTTP 422 / NO_EXTRACTABLE_TEXT`
- [ ] `parse_docx` with `tests/fixtures/sample.docx` returns non-empty text
- [ ] `parse_txt` with UTF-8 and latin-1 encoded bytes both return correct text
- [ ] Test: `tests/test_ingestion.py` unit tests for all three parsers

---

### T06 — Text Chunker

**Description:** Implement the token-based text chunker using `langchain-text-splitters`. Produces `Chunk` objects with `chunk_index`, `page_number`, and `token_count`.

**Files to create/modify:**
- `backend/app/services/chunker.py` — using `RecursiveCharacterTextSplitter` from `langchain_text_splitters` with `tiktoken` encoder:
  - `ChunkResult` dataclass: `chunk_index: int`, `text: str`, `page_number: int | None`, `token_count: int`
  - `chunk_document(parsed: ParsedDocument, chunk_size: int = 500, chunk_overlap: int = 50) -> list[ChunkResult]`
    - For PDF: chunk each page's text separately, carry through `page_number`; re-chunk if a page's text exceeds `chunk_size` tokens; assign global `chunk_index` across all pages
    - For TXT/DOCX: chunk the full concatenated text; `page_number = None` for all chunks
    - Use `tiktoken.get_encoding("cl100k_base")` for token counting
    - Filter out chunks with 0 tokens after splitting (can happen with whitespace-only segments)

**Acceptance criteria:**
- [ ] Chunking a 10-page PDF produces chunks where every chunk has `page_number` set to the originating page (1-based)
- [ ] All `chunk_index` values are unique and sequential (0, 1, 2, ...)
- [ ] No chunk has `token_count > chunk_size` (within a ±10% margin of the splitter's behaviour)
- [ ] `chunk_overlap=50` produces chunks where the last 50 tokens of chunk N overlap with the first 50 tokens of chunk N+1
- [ ] `chunk_document` with `chunk_overlap >= chunk_size` is safe (clamped or logs a warning without crashing)
- [ ] Test: unit tests in `tests/test_ingestion.py`

---

### T07 — Embedding Service

**Description:** Implement the OpenAI embedding service with batched API calls (≤ 100 chunks/batch) and exponential backoff on rate-limit errors (3 retries, initial delay 1 s, factor 2).

**Files to create/modify:**
- `backend/app/services/embedder.py` — using the `openai` async client:
  - `embed_chunks(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]`
    - Splits `texts` into batches of ≤ 100
    - Calls `client.embeddings.create(input=batch, model=model)` per batch
    - On `openai.RateLimitError`: waits `2^attempt` seconds, retries up to 3 times; after 3 failures raises `HTTPException(502, EMBEDDING_RATE_LIMIT)`
    - On `openai.APIConnectionError` or `openai.APIStatusError`: raises `HTTPException(503, EMBEDDING_UNAVAILABLE)`
    - Returns flat list of embedding vectors in input order
  - `embed_query(text: str, model: str = "text-embedding-3-small") -> list[float]` — single embedding for query-time use; same error handling

**Acceptance criteria:**
- [ ] `embed_chunks(["hello world"])` with valid API key returns a list of 1 vector of length 1536
- [ ] With `OPENAI_API_KEY=invalid`, `embed_chunks` raises `HTTPException(503, EMBEDDING_UNAVAILABLE)` (not a raw exception)
- [ ] Batching: a list of 250 texts results in exactly 3 API calls (100 + 100 + 50)
- [ ] Test: `tests/test_ingestion.py` with mocked OpenAI client (use `unittest.mock.AsyncMock`)

---

### T08 — Vector Store Wrapper (ChromaDB)

**Description:** Implement the ChromaDB service wrapper that creates per-session collections, upserts chunk embeddings with metadata, queries by cosine similarity, and deletes by `doc_id`.

**Files to create/modify:**
- `backend/app/services/vector_store.py` — using `chromadb` async client:
  - `get_or_create_collection(session_id: str) -> chromadb.Collection` — opens or creates `session_{session_id}` collection with cosine distance metric
  - `upsert_chunks(session_id: str, chunk_ids: list[str], embeddings: list[list[float]], texts: list[str], metadatas: list[dict]) -> None`
    - Upserts to collection with exact metadata shape from FRD Y0:
      ```python
      {
          "doc_id": doc_id,        # str: UUID v4
          "session_id": session_id,# str: UUID v4
          "filename": filename,    # str
          "file_type": file_type,  # str: 'pdf'|'txt'|'docx'
          "chunk_index": chunk_index, # int
          "page_number": page_number, # int|None → store as -1 if None (ChromaDB limitation)
          "token_count": token_count, # int
      }
      ```
  - `query_chunks(session_id: str, query_embedding: list[float], top_k: int = 5) -> list[dict]`
    - Calls `collection.query(query_embeddings=[query_embedding], n_results=top_k, where={"session_id": session_id}, include=["documents","metadatas","distances"])`
    - Returns list of dicts: `{chunk_id, text, doc_id, filename, page_number, chunk_index, similarity_score}` where `similarity_score = 1 - distance` (cosine)
    - Raises `HTTPException(500, RETRIEVAL_FAILURE)` on ChromaDB errors
  - `delete_doc_chunks(session_id: str, doc_id: str) -> None`
    - Calls `collection.delete(where={"doc_id": doc_id})`

**Acceptance criteria:**
- [ ] `upsert_chunks` + `query_chunks` round-trip: upsert one chunk, query with the same embedding → similarity_score ≈ 1.0
- [ ] `delete_doc_chunks` removes all chunks for that `doc_id`; subsequent query returns empty list
- [ ] `page_number = None` is stored as `-1` and converted back to `None` on retrieval
- [ ] Two sessions use isolated collections (query in session A does not return chunks from session B)
- [ ] Test: `tests/test_ingestion.py` using `chromadb.EphemeralClient()` in fixtures

---

### T09 — Document Ingestion Orchestrator

**Description:** Implement the ingestion pipeline orchestrator that ties together file validation → parsing → chunking → embedding → indexing, with status updates written to SQLite throughout. This is the service called by the upload endpoint.

**Files to create/modify:**
- `backend/app/services/ingestion.py` — `async def ingest_document(doc_id: str, session_id: str, filename: str, file_type: str, file_bytes: bytes, db, settings: Settings) -> None`:
  1. Update status → `PARSING`; call `parse_document(file_bytes, file_type)`; on error → update status → `FAILED` with error_message, re-raise
  2. Update status → `CHUNKING`; call `chunk_document(parsed, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)`
  3. Insert all `ChunkResult` rows into `chunks` table via `insert_chunk()`
  4. Update status → `EMBEDDING`; call `embed_chunks([c.text for c in chunks])`; on error → update status → `FAILED`, re-raise
  5. Update status → `INDEXING`; call `upsert_chunks(session_id, chunk_ids, embeddings, texts, metadatas)` where `chunk_id = f"{doc_id}:{c.chunk_index}"`
  6. Update status → `READY`; set `chunk_count = len(chunks)`, `ready_at = utcnow()`; update `page_count` for PDFs

  Progress events are emitted via an `asyncio.Queue` keyed by `doc_id` (see T10 for SSE consumer). Each status transition posts `{"doc_id": doc_id, "status": ..., "progress_pct": ..., "message": ...}` to the queue.

  Progress percentage mapping:
  - PARSING → 10%
  - CHUNKING → 30%
  - EMBEDDING → 70% (updates per batch: `30 + (batch_i / total_batches) * 40`)
  - INDEXING → 90%
  - READY → 100%

**Acceptance criteria:**
- [ ] End-to-end: `ingest_document(...)` with `tests/fixtures/sample.pdf` and a valid API key updates status to `READY` with non-zero `chunk_count` in the database
- [ ] Failed parse (corrupt file) sets status to `FAILED` and populates `error_message`
- [ ] Progress events emitted include `PARSING`, `CHUNKING`, `EMBEDDING`, `INDEXING`, `READY` in that order
- [ ] After ingestion, SQLite `chunks` table has one row per chunk with correct `page_number` values (for PDF)
- [ ] After ingestion, ChromaDB collection has the same number of embeddings as `chunks` rows

---

### T10 — Document Upload Endpoint & Progress Endpoints

**Description:** Implement the three document endpoints: `POST /api/documents/upload`, `GET /api/documents/{doc_id}/status`, and `GET /api/documents/upload/stream` (SSE). The upload endpoint kicks off the ingestion pipeline as a background task.

**Files to create/modify:**
- `backend/app/routers/documents.py` — endpoints:

  **`POST /api/documents/upload`** (multipart/form-data: `file: UploadFile`, `session_id: str`):
  - Validate session exists (→ 404 SESSION_NOT_FOUND)
  - Check document count ≤ 9 (→ 422 DOCUMENT_LIMIT_REACHED)
  - Read file bytes; call `validate_upload(filename, file_bytes, file_size, settings)`
  - Determine `file_type` from detected MIME
  - Assign `doc_id = str(uuid.uuid4())`; save file to `{settings.UPLOADS_DIR}/{session_id}/{doc_id}/{filename}`
  - Insert document record with status `UPLOADING`; add `doc_id` to session registry
  - Launch `ingest_document(...)` as `BackgroundTasks` task
  - Return HTTP 202 with `{"doc_id": ..., "session_id": ..., "filename": ..., "status": "UPLOADING"}`

  **`GET /api/documents/{doc_id}/status`**:
  - Fetch document from DB; return full document object:
    ```json
    {
      "doc_id": "...", "session_id": "...", "filename": "...",
      "file_type": "...", "file_size_bytes": ..., "status": "READY",
      "chunk_count": 42, "page_count": 12,
      "error_message": null, "uploaded_at": "...", "ready_at": "..."
    }
    ```
  - 404 if doc not found

  **`GET /api/documents/upload/stream`** (query param: `doc_id`):
  - SSE endpoint using `StreamingResponse` with `media_type="text/event-stream"`
  - Reads from `asyncio.Queue` keyed by `doc_id` (populated by ingestion service)
  - Emits `data: {json}\n\n` until `status` is `READY` or `FAILED`, then closes stream
  - Format: `data: {"doc_id": "...", "status": "PARSING", "progress_pct": 10, "message": "Parsing document..."}\n\n`

  **`GET /api/documents`** (query param: `session_id`):
  - Returns `{"documents": [...]}` list from DB for the session; 404 if session not found

  **`DELETE /api/documents/{doc_id}`**:
  - Fetch document (404 if not found)
  - Call `delete_doc_chunks(session_id, doc_id)` on vector store
  - Delete from SQLite `documents` table (cascades to `chunks`)
  - Delete file from disk: `{settings.UPLOADS_DIR}/{session_id}/{doc_id}/`
  - Remove `doc_id` from session registry
  - Return HTTP 204

**Acceptance criteria:**
- [ ] `POST /api/documents/upload` with `tests/fixtures/sample.pdf` returns HTTP 202 immediately (not waiting for ingestion)
- [ ] After polling `GET /api/documents/{doc_id}/status` until `status == "READY"`, `chunk_count > 0` and `page_count > 0`
- [ ] `POST /api/documents/upload` with a 21 MB buffer returns HTTP 413 with `error_code: "FILE_TOO_LARGE"`
- [ ] `POST /api/documents/upload` with a JPEG renamed to `.pdf` returns HTTP 422 with `error_code: "INVALID_MIME_TYPE"`
- [ ] `POST /api/documents/upload` with an invalid `session_id` returns HTTP 404 with `error_code: "SESSION_NOT_FOUND"`
- [ ] `DELETE /api/documents/{doc_id}` returns HTTP 204; subsequent `GET /api/documents/{doc_id}/status` returns 404
- [ ] SSE stream from `GET /api/documents/upload/stream?doc_id=...` emits events in order: UPLOADING → PARSING → CHUNKING → EMBEDDING → INDEXING → READY
- [ ] Test: `tests/test_documents.py` covering upload 202, status polling, validation errors, delete 204

---

### T11 — Chat Query & Streaming Endpoints

**Description:** Implement `POST /api/chat/query` (validates session + query, runs retrieval, initiates LLM generation), `GET /api/chat/stream/{message_id}` (SSE token stream), `GET /api/chat/history/{session_id}`, and `DELETE /api/chat/history/{session_id}`.

**Files to create/modify:**
- `backend/app/models/chat.py` — Pydantic schemas:
  - `QueryRequest`: `session_id: str`, `query: str`, `include_history: bool = True`
  - `CitationResponse`: `chunk_id: str`, `doc_id: str`, `filename: str`, `page_number: int | None`, `chunk_index: int`, `excerpt: str`, `similarity_score: float`
  - `MessageResponse`: `message_id: str`, `session_id: str`, `role: str`, `content: str`, `is_refusal: bool`, `retrieved_chunks: list[CitationResponse]`, `created_at: str`
- `backend/app/routers/chat.py` — endpoints:

  **`POST /api/chat/query`**:
  1. Validate session exists (→ 404 SESSION_NOT_FOUND)
  2. Strip and validate `query`: empty → 422 EMPTY_QUERY; > 2000 chars → 422 QUERY_TOO_LONG
  3. Check ≥ 1 READY document in session (→ 422 NO_DOCUMENTS_READY)
  4. Save user message to `messages` table
  5. Generate `message_id` for assistant reply; save placeholder assistant message with status marker; store in in-memory `pending_streams: dict[str, asyncio.Queue]`
  6. Launch background task: `generate_response(message_id, session_id, query, include_history, db, settings)`
  7. Return HTTP 200 with `{"message_id": message_id}`

  **`GET /api/chat/stream/{message_id}`** (SSE):
  - Read from `pending_streams[message_id]` queue
  - Emit `data: {"type": "token", "delta": "..."}\n\n` for each token
  - Emit final `data: {"type": "done", "message": {full MessageResponse}}\n\n`
  - Close stream; clean up queue

  **`generate_response(...)` background task** (in same file or `services/llm.py`):
  1. Call `embed_query(query)` → 503 on failure
  2. Call `query_chunks(session_id, query_embedding, settings.TOP_K)` → 500 on failure
  3. Build context block:
     ```
     [Source: {filename}, Page {page_number}, Chunk {chunk_index}]
     {chunk_text}
     ```
  4. Build messages for LLM:
     - System: `"You are a document assistant. Answer the user's question using ONLY the provided document excerpts. If the answer is not present in the excerpts, respond with: 'I could not find an answer to your question in the uploaded documents.' Do NOT use any external knowledge."`
     - Retrieve last `settings.CHAT_HISTORY_TURNS` message pairs from DB; include as alternating user/assistant messages
     - Final user message: context block + `"\n\nQuestion: {query}"`
  5. Call `openai.chat.completions.create(model=settings.LLM_MODEL, messages=..., temperature=settings.LLM_TEMPERATURE, stream=True)`
  6. For each streaming token, put `{"type": "token", "delta": token}` on the queue
  7. Assemble full response text; detect `is_refusal` if content matches refusal pattern
  8. Save assistant message to DB with `is_refusal` flag
  9. Save citations to `message_citations` for each retrieved chunk (skip if `is_refusal=True`)
  10. Put `{"type": "done", "message": {full MessageResponse}}` on queue

  **`GET /api/chat/history/{session_id}`**:
  - Return `{"messages": [...]}` with all messages + their citations from DB; 404 if session not found

  **`DELETE /api/chat/history/{session_id}`**:
  - Delete all messages for session from DB (cascades to citations); return HTTP 204

**Acceptance criteria:**
- [ ] `POST /api/chat/query` with empty `query` returns HTTP 422 with `error_code: "EMPTY_QUERY"`
- [ ] `POST /api/chat/query` with 2001-char query returns HTTP 422 with `error_code: "QUERY_TOO_LONG"`
- [ ] `POST /api/chat/query` with session that has 0 READY documents returns HTTP 422 with `error_code: "NO_DOCUMENTS_READY"`
- [ ] `POST /api/chat/query` with answerable question (after uploading sample PDF) → SSE stream returns `token` events then `done` event with `is_refusal: false` and non-empty `retrieved_chunks`
- [ ] `POST /api/chat/query` with question about unrelated topic → `done` event has `is_refusal: true` and empty `retrieved_chunks`
- [ ] `GET /api/chat/history/{session_id}` returns all prior messages including citations
- [ ] `DELETE /api/chat/history/{session_id}` returns HTTP 204; subsequent `GET /api/chat/history` returns empty `messages: []`
- [ ] Test: `tests/test_chat.py` covering validation errors, answerable query, refusal query, history, delete

---

### T12 — Test Suite (Smoke + Integration Tests)

**Description:** Write the complete test suite covering all endpoints with smoke tests and key integration scenarios. Uses `pytest-asyncio` with `TestClient` from FastAPI. Mocks OpenAI API calls so tests run without a real API key.

**Files to create/modify:**
- `backend/tests/conftest.py` — fixtures:
  - `client` — `TestClient(app)` with in-memory SQLite (`:memory:` or temp file) and `EphemeralClient` ChromaDB
  - `mock_openai` — `unittest.mock.patch` on `openai.AsyncOpenAI` returning fake embeddings (1536-dim zeros) and fake LLM tokens
  - `sample_session` — creates a session and returns `session_id`
  - `ready_document` — uploads `tests/fixtures/sample.txt` and polls until READY
- `backend/tests/fixtures/sample.pdf` — minimal valid PDF (can be generated with fpdf2 or included as binary)
- `backend/tests/fixtures/sample.docx` — minimal valid DOCX
- `backend/tests/fixtures/sample.txt` — "This is a test document. The contract was signed on March 15 2024."
- `backend/tests/test_sessions.py` — 4 tests: create session, get session, get unknown session, two sessions are distinct
- `backend/tests/test_documents.py` — 8 tests: upload TXT success, upload PDF success, upload DOCX success, upload too large, upload wrong type, upload unknown session, delete document, list documents
- `backend/tests/test_ingestion.py` — 6 unit tests: parse_pdf, parse_docx, parse_txt, chunk_document, embed_chunks (mocked), vector_store round-trip
- `backend/tests/test_chat.py` — 8 tests: query empty, query too long, query no-docs, query answerable (mocked LLM), query refusal (mocked LLM), stream events, get history, delete history

**Acceptance criteria:**
- [ ] `cd backend && pytest tests/ -v` passes with 0 failures (tests that need real OpenAI key are skipped if key absent)
- [ ] Test coverage ≥ 70% on `app/routers/` and `app/services/`
- [ ] All session, document, and chat endpoint smoke tests pass with mocked dependencies
- [ ] Fixture `ready_document` completes synchronously in tests (background ingestion awaited in test context)

---

## Task Dependency Graph

```
T01 (Scaffold)
├── T02 (SQLite)         — needs app/config.py from T01
├── T03 (Sessions)       — needs app structure from T01
└── T04 (File Validation) — needs Settings from T01

T02 → T09 (Ingestion)   — needs DB helper functions
T03 → T10 (Upload EP)   — needs session registry
T03 → T11 (Chat EP)     — needs session registry
T04 → T10 (Upload EP)   — needs validate_upload()

T05 (Parser)             — needs T01 (models/errors.py for HTTPException codes)
T06 (Chunker)            — needs T05 (ParsedDocument type)
T07 (Embedder)           — needs T01 (config, error codes)
T08 (Vector Store)       — needs T01 (config, error codes)

T09 (Ingestion)          — needs T02, T05, T06, T07, T08
T10 (Upload EP)          — needs T03, T04, T09
T11 (Chat EP)            — needs T02, T03, T07, T08
T12 (Tests)              — needs T10, T11 (all endpoints complete)
```

**Execution order (sequential, blocked by dependencies):**

```
Wave 1: T01
Wave 2: T02, T03, T04, T05     (all depend only on T01)
Wave 3: T06, T07, T08          (T06 needs T05; T07/T08 need T01)
Wave 4: T09                    (needs T02+T05+T06+T07+T08)
Wave 5: T10, T11               (both need T09 + session work from T03)
Wave 6: T12                    (tests need all endpoints)
```

## Estimated Tasks: 12

---

## Phase Success Criteria

When this plan is complete, the following must all be TRUE:

1. **Upload → READY:** `POST /api/documents/upload` with a real PDF returns `status: "UPLOADING"`; polling `GET /api/documents/{doc_id}/status` eventually returns `status: "READY"` with `chunk_count > 0`.

2. **Stage progression:** The status polling endpoint returns stages in order: `UPLOADING → PARSING → CHUNKING → EMBEDDING → INDEXING → READY`.

3. **Answerable query:** After uploading `sample.pdf`, `POST /api/chat/query` with `{"session_id": ..., "query": "What is described in the document?"}` → SSE stream completes with `is_refusal: false` and `retrieved_chunks` containing at least one item with a non-empty `excerpt`.

4. **Refusal:** `POST /api/chat/query` with `{"query": "What is the population of Mars?"}` → `is_refusal: true`, empty `retrieved_chunks`.

5. **Delete clears embeddings:** `DELETE /api/documents/{doc_id}` → subsequent `POST /api/chat/query` returns `is_refusal: true` (no remaining READY documents in session).

6. **Validation errors:** The following each return the specified error:
   - File > 20 MB → HTTP 413, `FILE_TOO_LARGE`
   - JPEG renamed to PDF → HTTP 422, `INVALID_MIME_TYPE`
   - Corrupt PDF → HTTP 422, `PARSE_FAILURE`
   - Empty query → HTTP 422, `EMPTY_QUERY`
   - No READY documents → HTTP 422, `NO_DOCUMENTS_READY`

7. **Tests pass:** `cd backend && pytest tests/ -v` exits 0 with all tests passing.
