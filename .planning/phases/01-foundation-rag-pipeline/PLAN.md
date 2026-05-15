# Phase 1 Plan: Foundation & RAG Pipeline

**Phase goal:** A fully operational FastAPI backend that ingests documents (PDF/DOCX/TXT), embeds and indexes them in ChromaDB, and answers natural-language questions with cited, strictly-grounded responses — all verifiable via REST API with no frontend.

**Source documents:** FRD F00, F01, F02, Y0 (schema), ROADMAP Phase 1

---

## Target Directory Layout

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI factory, lifespan, CORS, routers
│   ├── config.py                 # Pydantic BaseSettings, get_settings() singleton
│   ├── database.py               # aiosqlite: init_db(), helper CRUD functions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── errors.py             # ErrorCode enum + ErrorResponse schema
│   │   ├── session.py            # SessionState dataclass + in-memory registry
│   │   ├── document.py           # Document request/response Pydantic models
│   │   └── chat.py               # Chat request/response Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── sessions.py           # POST /api/sessions, GET /api/sessions/{id}
│   │   ├── documents.py          # Upload, status, SSE stream, list, delete
│   │   └── chat.py               # POST /api/chat/query, SSE stream, history, delete
│   ├── services/
│   │   ├── __init__.py
│   │   ├── parser.py             # PDF (PyMuPDF), DOCX (python-docx), TXT
│   │   ├── chunker.py            # Token-based splitter (tiktoken + langchain)
│   │   ├── embedder.py           # OpenAI embeddings, batching, retry backoff
│   │   ├── vector_store.py       # ChromaDB wrapper: upsert, query, delete
│   │   └── ingestion.py          # Pipeline orchestrator: parse→chunk→embed→index
│   └── utils/
│       ├── __init__.py
│       └── file_validation.py    # Magic-byte MIME detection, size/empty checks
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # TestClient, temp DB, ephemeral ChromaDB, mock OpenAI
│   ├── test_sessions.py
│   ├── test_documents.py
│   ├── test_ingestion.py         # Unit tests: parser, chunker, embedder, vector store
│   ├── test_chat.py
│   └── fixtures/
│       ├── sample.pdf
│       ├── sample.docx
│       └── sample.txt
├── uploads/                      # Runtime file storage (gitignored)
├── chroma_db/                    # ChromaDB persistence dir (gitignored)
├── rag_chatbot.db                # SQLite file (gitignored)
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Tasks

---

### T01 — Project Scaffold & Configuration

**What it delivers:** The skeleton every other task builds on. Directory structure, pinned dependencies, env config, FastAPI entry point, and the error code enum.

**Files:**

| File | Content |
|------|---------|
| `backend/requirements.txt` | Pinned deps (see list below) |
| `backend/pyproject.toml` | Project metadata + pytest/ruff config |
| `backend/.env.example` | All env vars with defaults documented |
| `backend/app/__init__.py` | Empty |
| `backend/app/config.py` | `Settings(BaseSettings)` + `get_settings()` cached singleton |
| `backend/app/main.py` | FastAPI factory with lifespan, CORS, routers, global exception handler |
| `backend/app/models/__init__.py` | Empty |
| `backend/app/models/errors.py` | `ErrorCode` str enum + `ErrorResponse` Pydantic model |
| `backend/app/routers/__init__.py` | Empty |
| `backend/app/services/__init__.py` | Empty |
| `backend/app/utils/__init__.py` | Empty |

**Pinned dependencies (`requirements.txt`):**
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

**`.env.example` content:**
```
# Required
OPENAI_API_KEY=sk-...

# LLM
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.0

# Embedding
EMBEDDING_MODEL=text-embedding-3-small

# Pipeline tuning
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K=5
CHAT_HISTORY_TURNS=10
MAX_FILE_SIZE_MB=20
MAX_DOCS_PER_SESSION=10

# Storage
UPLOADS_DIR=uploads
VECTOR_STORE_PATH=chroma_db
DATABASE_URL=rag_chatbot.db

# Server
LOG_LEVEL=INFO
```

**`config.py` spec:**
- `Settings(BaseSettings)` reads all the above via `model_config = SettingsConfigDict(env_file=".env")`
- Every field has a hard-coded default so the app starts without a `.env` file (except `OPENAI_API_KEY`, which defaults to `""`)
- `get_settings() -> Settings` decorated with `@lru_cache` — one instance per process

**`main.py` spec:**
- `create_app() -> FastAPI` factory function
- `lifespan` context manager: calls `await init_db(settings.DATABASE_URL)` on startup
- CORS middleware: `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`
- Global exception handler for unhandled `Exception`: returns `HTTP 500` with `{"error_code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}`
- Health check: `GET /` → `{"status": "ok"}`
- Includes `sessions`, `documents`, `chat` routers under prefix `/api`

**`models/errors.py` spec:**
- `ErrorCode(str, Enum)` with all 16 values from FRD F00/F01:
  `SESSION_NOT_FOUND`, `INVALID_MIME_TYPE`, `FILE_TOO_LARGE`, `DOCUMENT_LIMIT_REACHED`,
  `EMPTY_FILE`, `NO_EXTRACTABLE_TEXT`, `EMBEDDING_RATE_LIMIT`, `EMBEDDING_UNAVAILABLE`,
  `PARSE_FAILURE`, `EMPTY_QUERY`, `QUERY_TOO_LONG`, `NO_DOCUMENTS_READY`,
  `LLM_RATE_LIMIT`, `LLM_UNAVAILABLE`, `LLM_EMPTY_RESPONSE`, `RETRIEVAL_FAILURE`
- `ErrorResponse(BaseModel)`: fields `error_code: str`, `message: str`, `details: dict | None = None`

**Acceptance criteria:**
- [ ] `pip install -r requirements.txt` completes without errors
- [ ] `uvicorn app.main:app --reload` starts on port 8000; `GET /` returns `{"status": "ok"}`
- [ ] `GET /docs` renders Swagger UI
- [ ] `get_settings()` resolves all defaults without a `.env` file
- [ ] All 16 `ErrorCode` values are present in `errors.py`

---

### T02 — SQLite Database Layer

**What it delivers:** The async SQLite schema (exact DDL from FRD Y0) and all CRUD helper functions used by every other module.

**Files:**

| File | Content |
|------|---------|
| `backend/app/database.py` | `init_db()`, `get_db()`, all helper functions |

**DDL (must match FRD Y0 character-for-character):**

```sql
PRAGMA foreign_keys = ON;

-- documents
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

-- chunks
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

-- messages
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

-- message_citations
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

**Helper functions to implement in `database.py`:**

| Function | Signature | Purpose |
|----------|-----------|---------|
| `init_db` | `async (db_path: str) -> None` | Runs DDL on startup; sets module-level `_DB_PATH` |
| `get_db` | `async () -> aiosqlite.Connection` | Opens connection with `row_factory = aiosqlite.Row` and `PRAGMA foreign_keys = ON` |
| `insert_document` | `async (db, doc_id, session_id, filename, file_type, file_size_bytes, file_path, status) -> None` | Inserts document row with `uploaded_at = utcnow()` |
| `update_document_status` | `async (db, doc_id, status, chunk_count?, page_count?, error_message?, ready_at?) -> None` | Dynamic UPDATE of whichever fields are provided |
| `get_document` | `async (db, doc_id) -> dict \| None` | Fetches single document row as dict |
| `list_documents` | `async (db, session_id) -> list[dict]` | All documents for a session, ordered by `uploaded_at ASC` |
| `delete_document` | `async (db, doc_id) -> None` | Deletes document row (cascades to chunks) |
| `count_session_documents` | `async (db, session_id) -> int` | Count of all documents for session |
| `count_ready_documents` | `async (db, session_id) -> int` | Count of READY documents for session |
| `insert_chunk` | `async (db, chunk_id, doc_id, session_id, chunk_index, page_number, token_count, text) -> None` | Inserts chunk row; caller batches commits |
| `insert_message` | `async (db, message_id, session_id, role, content, is_refusal?) -> None` | Inserts message row |
| `update_message` | `async (db, message_id, content, is_refusal) -> None` | Updates content + is_refusal after generation |
| `get_messages` | `async (db, session_id, limit?) -> list[dict]` | All messages for session, ordered by `created_at ASC` |
| `get_recent_messages` | `async (db, session_id, turns) -> list[dict]` | Last `turns * 2` messages (most recent N pairs), returned in chronological order |
| `delete_messages` | `async (db, session_id) -> None` | Deletes all messages for session (cascades to citations) |
| `insert_citation` | `async (db, message_id, chunk_id, doc_id, filename, page_number, chunk_index, excerpt, similarity_score) -> None` | Inserts citation row; caller batches commits |
| `get_citations` | `async (db, message_id) -> list[dict]` | All citations for a message, ordered by `id ASC` |

**Acceptance criteria:**
- [ ] `init_db()` creates all 4 tables on a fresh SQLite file without error
- [ ] Inserting an invalid `status` value raises `sqlite3.IntegrityError` (CHECK constraint)
- [ ] Deleting a document row cascades to delete its chunks; deleting a message cascades to delete its citations
- [ ] Inserting a duplicate `(doc_id, chunk_index)` pair raises `IntegrityError` (UNIQUE index)
- [ ] All helper functions are callable without runtime error in tests

---

### T03 — Session Management Endpoints

**What it delivers:** In-memory session registry and the two session endpoints that every other endpoint depends on for session validation.

**Files:**

| File | Content |
|------|---------|
| `backend/app/models/session.py` | `SessionState` dataclass + `sessions` dict |
| `backend/app/routers/sessions.py` | `POST /api/sessions`, `GET /api/sessions/{session_id}` |

**`models/session.py` spec:**
```python
@dataclass
class SessionState:
    session_id: str
    created_at: datetime
    document_ids: list[str] = field(default_factory=list)
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

sessions: dict[str, SessionState] = {}
```

**Router spec:**

`POST /api/sessions` → HTTP 201
- Generate UUID v4 `session_id`
- Create `SessionState`, store in `sessions` dict
- Return `{"session_id": "...", "created_at": "ISO-8601-UTC"}`

`GET /api/sessions/{session_id}` → HTTP 200 or 404
- Look up `sessions[session_id]`
- Found: return `{"session_id": "...", "created_at": "...", "document_count": N}`
- Not found: HTTP 404 with `{"detail": {"error_code": "SESSION_NOT_FOUND", "message": "..."}}`

**Acceptance criteria:**
- [ ] `POST /api/sessions` returns HTTP 201 with a valid UUID v4
- [ ] `GET /api/sessions/{id}` with known id returns HTTP 200 with `document_count: 0`
- [ ] `GET /api/sessions/nonexistent` returns HTTP 404 with `error_code: "SESSION_NOT_FOUND"`
- [ ] Two sequential POST calls return two distinct session IDs
- [ ] Tests in `tests/test_sessions.py` cover all four scenarios

---

### T04 — File Validation Utility

**What it delivers:** Magic-byte MIME detection and upload validation used by the document upload endpoint (T10). Pure utility — no FastAPI routing, no DB access.

**Files:**

| File | Content |
|------|---------|
| `backend/app/utils/file_validation.py` | `detect_mime_type()` + `validate_upload()` |

**`file_validation.py` spec:**

```python
ALLOWED_MIMES: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}
# Any text/* MIME also accepted as "txt" (covers text/x-python, text/csv, etc.)

def detect_mime_type(file_bytes: bytes) -> str:
    # Uses python-magic on first 2048 bytes; returns MIME string

def validate_upload(
    filename: str,
    file_bytes: bytes,
    file_size: int,
    settings: Settings,
) -> str:
    # Returns detected file_type ("pdf" / "txt" / "docx") on success
    # Raises HTTPException on failure:
    #   file_size == 0          → HTTP 422, EMPTY_FILE
    #   file_size > MAX_MB*1024²→ HTTP 413, FILE_TOO_LARGE
    #   MIME not in allowed set → HTTP 422, INVALID_MIME_TYPE
```

**Acceptance criteria:**
- [ ] Returns `"txt"` for a valid UTF-8 text buffer
- [ ] Returns `"pdf"` for a real PDF buffer (valid magic bytes)
- [ ] Raises `HTTP 413 / FILE_TOO_LARGE` for a 21 MB zero buffer
- [ ] Raises `HTTP 422 / EMPTY_FILE` for a 0-byte buffer
- [ ] Raises `HTTP 422 / INVALID_MIME_TYPE` for a JPEG buffer (bytes `FF D8 FF`)
- [ ] Unit tests for each branch in `tests/test_documents.py`

---

### T05 — Document Parser

**What it delivers:** Three-format parser producing `ParsedDocument` objects with full text and per-page chunks (PDF) or flat text (DOCX/TXT).

**Files:**

| File | Content |
|------|---------|
| `backend/app/services/parser.py` | `ParsedDocument`, `parse_pdf/docx/txt/document` |

**`parser.py` spec:**

```python
@dataclass
class ParsedDocument:
    text: str                         # Full concatenated text
    page_chunks: list[tuple[int, str]] # [(page_number, page_text), ...]; empty for non-PDF
    page_count: int | None            # PDF only; None for TXT/DOCX

def parse_pdf(file_bytes: bytes) -> ParsedDocument:
    # fitz.open(stream=file_bytes, filetype="pdf")
    # Iterates pages with page.get_text(); page_number is 1-based
    # Raises HTTP 422 / PARSE_FAILURE if fitz.open() raises
    # Raises HTTP 422 / NO_EXTRACTABLE_TEXT if full_text.strip() is empty

def parse_docx(file_bytes: bytes) -> ParsedDocument:
    # docx.Document(io.BytesIO(file_bytes))
    # Extracts paragraph text + table cell text
    # page_count = None, page_chunks = []
    # Raises HTTP 422 / PARSE_FAILURE if Document() raises
    # Raises HTTP 422 / NO_EXTRACTABLE_TEXT if result is empty

def parse_txt(file_bytes: bytes) -> ParsedDocument:
    # Tries UTF-8 decode; falls back to latin-1
    # page_count = None, page_chunks = []
    # Raises HTTP 422 / NO_EXTRACTABLE_TEXT if text.strip() is empty

def parse_document(file_bytes: bytes, file_type: str) -> ParsedDocument:
    # Dispatcher: routes to parse_pdf / parse_docx / parse_txt
```

**Acceptance criteria:**
- [ ] `parse_pdf(sample.pdf)` returns non-empty text with `page_count ≥ 1` and `len(page_chunks) == page_count`
- [ ] `parse_pdf(b"not a pdf")` raises `HTTP 422 / PARSE_FAILURE`
- [ ] `parse_docx(sample.docx)` returns non-empty text with `page_count = None`
- [ ] `parse_txt(utf8_bytes)` and `parse_txt(latin1_bytes)` both return correct text
- [ ] Unit tests for all parsers in `tests/test_ingestion.py`

---

### T06 — Text Chunker

**What it delivers:** Token-based recursive text splitter producing `ChunkResult` objects with global `chunk_index`, `page_number`, and `token_count`.

**Files:**

| File | Content |
|------|---------|
| `backend/app/services/chunker.py` | `ChunkResult`, `chunk_document()` |

**`chunker.py` spec:**

```python
@dataclass
class ChunkResult:
    chunk_index: int        # global 0-based index across whole document
    text: str
    page_number: int | None # 1-based PDF page; None for TXT/DOCX
    token_count: int

def chunk_document(
    parsed: ParsedDocument,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[ChunkResult]:
    # Safety: if chunk_overlap >= chunk_size, clamp to chunk_size // 4 + log warning
    # Uses RecursiveCharacterTextSplitter(length_function=tiktoken_len, ...)
    # tiktoken encoding: cl100k_base
    #
    # PDF path: chunk each page separately → carry page_number; assign global chunk_index
    # TXT/DOCX path: chunk full text; page_number = None for all chunks
    #
    # Filter out any split with token_count == 0
```

**Acceptance criteria:**
- [ ] All `chunk_index` values are unique and sequential starting at 0
- [ ] PDF chunks all have `page_number ≥ 1`; TXT/DOCX chunks all have `page_number = None`
- [ ] No chunk has `token_count == 0`
- [ ] `chunk_overlap ≥ chunk_size` does not crash — logs warning and clamps
- [ ] Unit tests in `tests/test_ingestion.py`

---

### T07 — Embedding Service

**What it delivers:** Batched OpenAI embedding calls (≤ 100/batch) with exponential backoff on rate-limit errors, and a single-query convenience wrapper.

**Files:**

| File | Content |
|------|---------|
| `backend/app/services/embedder.py` | `embed_chunks()`, `embed_query()` |

**`embedder.py` spec:**

```python
BATCH_SIZE = 100

async def embed_chunks(
    texts: list[str],
    model: str | None = None,   # defaults to settings.EMBEDDING_MODEL
) -> list[list[float]]:
    # Splits texts into batches of <= BATCH_SIZE
    # For each batch: calls openai.AsyncOpenAI().embeddings.create(input=batch, model=model)
    # Retry on openai.RateLimitError:
    #   wait 2^attempt seconds; up to 3 attempts
    #   after 3 failures: raise HTTP 502 / EMBEDDING_RATE_LIMIT
    # On openai.APIConnectionError or openai.APIStatusError:
    #   raise HTTP 503 / EMBEDDING_UNAVAILABLE
    # Returns flat list in input order (sort by response.data[i].index)

async def embed_query(text: str, model: str | None = None) -> list[float]:
    # Calls embed_chunks([text])[0]; same error handling
```

**Acceptance criteria:**
- [ ] 250 texts → exactly 3 API calls (100 + 100 + 50) — verifiable via mock call count
- [ ] Mocked client returns 1536-dim embeddings; `embed_chunks(["hello"])` returns list of length 1
- [ ] `RateLimitError` on all 3 attempts → `HTTP 502 / EMBEDDING_RATE_LIMIT`
- [ ] `APIConnectionError` → `HTTP 503 / EMBEDDING_UNAVAILABLE`
- [ ] Tests in `tests/test_ingestion.py` with `unittest.mock.AsyncMock`

---

### T08 — Vector Store Wrapper (ChromaDB)

**What it delivers:** Per-session ChromaDB collections with cosine similarity, upsert/query/delete operations, and `page_number = None → -1` conversion (ChromaDB metadata limitation).

**Files:**

| File | Content |
|------|---------|
| `backend/app/services/vector_store.py` | `get_or_create_collection()`, `upsert_chunks()`, `query_chunks()`, `delete_doc_chunks()`, `set_client()` |

**`vector_store.py` spec:**

```python
# Module-level client (PersistentClient by default; overrideable for tests)
_chroma_client: chromadb.ClientAPI | None = None

def set_client(client: chromadb.ClientAPI) -> None:
    # Used in tests to inject EphemeralClient

def get_or_create_collection(session_id: str) -> chromadb.Collection:
    # Collection name: f"session_{session_id}"
    # Metadata: {"hnsw:space": "cosine"}

def upsert_chunks(
    session_id: str,
    chunk_ids: list[str],         # f"{doc_id}:{chunk_index}"
    embeddings: list[list[float]],
    texts: list[str],
    metadatas: list[dict],        # must include: doc_id, session_id, filename,
                                  # file_type, chunk_index, page_number, token_count
) -> None:
    # Convert page_number=None → -1 in metadata before upsert (ChromaDB cannot store None)

def query_chunks(
    session_id: str,
    query_embedding: list[float],
    top_k: int = 5,
) -> list[dict]:
    # collection.query(query_embeddings=[...], n_results=min(top_k, count),
    #                  include=["documents","metadatas","distances"])
    # similarity_score = 1 - distance  (cosine distance → similarity)
    # Convert page_number=-1 back to None in returned dicts
    # Return list of: {chunk_id, text, doc_id, filename, page_number,
    #                  chunk_index, similarity_score}
    # On ChromaDB error: raise HTTP 500 / RETRIEVAL_FAILURE

def delete_doc_chunks(session_id: str, doc_id: str) -> None:
    # collection.delete(where={"doc_id": doc_id})
    # Best-effort: log warning on failure, do not raise
```

**Acceptance criteria:**
- [ ] Upsert one chunk → query with identical embedding → `similarity_score ≈ 1.0`
- [ ] `delete_doc_chunks` → subsequent query returns empty result for that `doc_id`
- [ ] `page_number = None` stored as `-1`; retrieved as `None`
- [ ] Two distinct sessions are isolated: session A query does not return session B chunks
- [ ] Tests in `tests/test_ingestion.py` using `chromadb.EphemeralClient()`

---

### T09 — Document Ingestion Orchestrator

**What it delivers:** The async pipeline gluing T05–T08 together with SQLite status updates and SSE progress events.

**Files:**

| File | Content |
|------|---------|
| `backend/app/services/ingestion.py` | `ingest_document()`, progress queue helpers |

**`ingestion.py` spec:**

```python
# Per-doc_id asyncio queues consumed by SSE stream endpoint
_progress_queues: dict[str, asyncio.Queue] = {}

def get_progress_queue(doc_id: str) -> asyncio.Queue: ...
def remove_progress_queue(doc_id: str) -> None: ...

async def ingest_document(
    doc_id: str,
    session_id: str,
    filename: str,
    file_type: str,
    file_bytes: bytes,
    db: aiosqlite.Connection,
    settings: Settings,
) -> None:
```

**Pipeline steps with status transitions and progress events:**

| Step | DB status | progress_pct | On error |
|------|-----------|-------------|---------|
| 1. Parse | `PARSING` | 10 | → `FAILED`, set `error_message`, return |
| 2. Chunk | `CHUNKING` | 30 | → `FAILED` if 0 chunks produced |
| 3. Insert chunks to SQLite | — | 30 | — |
| 4. Embed | `EMBEDDING` | 40–80 (per batch) | → `FAILED`, set `error_message`, return |
| 5. Upsert to ChromaDB | `INDEXING` | 90 | — |
| 6. Mark ready | `READY` | 100 | — |

- Each status transition calls `update_document_status(db, doc_id, status)` then `_emit(doc_id, status, pct, message)`
- `chunk_id = f"{doc_id}:{chunk.chunk_index}"`
- ChromaDB metadata shape: `{doc_id, session_id, filename, file_type, chunk_index, page_number, token_count}`
- After step 6: set `chunk_count = len(chunks)`, `page_count = parsed.page_count`, `ready_at = utcnow()`

**Acceptance criteria:**
- [ ] With `sample.pdf` + valid API key: final DB status is `READY`, `chunk_count > 0`
- [ ] Corrupt file input: final DB status is `FAILED`, `error_message` is non-null
- [ ] Progress events emitted in order: `PARSING → CHUNKING → EMBEDDING → INDEXING → READY`
- [ ] After completion: SQLite `chunks` rows match ChromaDB collection count
- [ ] PDF chunks have correct `page_number` values in SQLite

---

### T10 — Document Endpoints

**What it delivers:** Five document endpoints — upload (202 async), status poll, SSE progress stream, list, and delete.

**Files:**

| File | Content |
|------|---------|
| `backend/app/models/document.py` | `DocumentUploadResponse`, `DocumentStatusResponse`, `DocumentListResponse` |
| `backend/app/routers/documents.py` | All 5 document endpoints |

**Endpoint specs:**

**`POST /api/documents/upload`** (multipart: `file: UploadFile`, form field `session_id: str`)
1. Check `session_id` in `sessions` dict → 404 `SESSION_NOT_FOUND` if missing
2. Count existing docs → 422 `DOCUMENT_LIMIT_REACHED` if `count >= MAX_DOCS_PER_SESSION`
3. Read file bytes; call `validate_upload()` → raises on invalid type/size/empty
4. `doc_id = str(uuid.uuid4())`; save to `uploads/{session_id}/{doc_id}/{filename}`
5. `insert_document(db, ...)` with `status="UPLOADING"`; add `doc_id` to `sessions[session_id].document_ids`
6. Add `ingest_document(...)` as `BackgroundTasks` task
7. Return **HTTP 202** `{"doc_id", "session_id", "filename", "status": "UPLOADING"}`

**`GET /api/documents/{doc_id}/status`**
- Fetch from DB → 404 if not found
- Return full document object (all columns)

**`GET /api/documents/upload/stream?doc_id=...`** (SSE)
- `StreamingResponse(media_type="text/event-stream")`
- Reads from `get_progress_queue(doc_id)` until `status in ("READY", "FAILED")`
- Each event: `data: {json}\n\n`
- Calls `remove_progress_queue(doc_id)` after stream ends

**`GET /api/documents?session_id=...`**
- 404 if session not in `sessions`
- Returns `{"documents": [list of DocumentStatusResponse]}`

**`DELETE /api/documents/{doc_id}`**
- Fetch doc → 404 if not found
- `delete_doc_chunks(session_id, doc_id)` (vector store)
- `delete_document(db, doc_id)` (SQLite; cascades to chunks)
- Delete file from disk: `uploads/{session_id}/{doc_id}/`
- Remove from `sessions[session_id].document_ids`
- Return **HTTP 204**

**Acceptance criteria:**
- [ ] Upload returns HTTP 202 immediately (before ingestion completes)
- [ ] Status endpoint returns correct stage labels as ingestion progresses
- [ ] Upload 21 MB → HTTP 413 `FILE_TOO_LARGE`
- [ ] Upload JPEG → HTTP 422 `INVALID_MIME_TYPE`
- [ ] Upload to unknown session → HTTP 404 `SESSION_NOT_FOUND`
- [ ] Delete → HTTP 204; subsequent status call → HTTP 404
- [ ] SSE stream emits events in stage order ending with `READY` or `FAILED`
- [ ] Tests in `tests/test_documents.py`

---

### T11 — Chat Endpoints

**What it delivers:** Four chat endpoints — query submission, SSE token stream, history retrieval, and history delete — plus the background LLM generation task.

**Files:**

| File | Content |
|------|---------|
| `backend/app/models/chat.py` | `QueryRequest`, `CitationResponse`, `MessageResponse`, `QueryInitResponse`, `ChatHistoryResponse` |
| `backend/app/routers/chat.py` | All 4 chat endpoints + `_generate_response()` background task |

**Pydantic models:**
```python
class QueryRequest(BaseModel):
    session_id: str
    query: str
    include_history: bool = True

class CitationResponse(BaseModel):
    chunk_id: str; doc_id: str; filename: str
    page_number: int | None; chunk_index: int
    excerpt: str; similarity_score: float

class MessageResponse(BaseModel):
    message_id: str; session_id: str; role: str; content: str
    is_refusal: bool; retrieved_chunks: list[CitationResponse]; created_at: str

class QueryInitResponse(BaseModel):
    message_id: str

class ChatHistoryResponse(BaseModel):
    messages: list[MessageResponse]
```

**`POST /api/chat/query`** → HTTP 200
1. Validate `session_id` in `sessions` → 404 `SESSION_NOT_FOUND`
2. Strip query; empty → 422 `EMPTY_QUERY`; > 2000 chars → 422 `QUERY_TOO_LONG`
3. `count_ready_documents(db, session_id) == 0` → 422 `NO_DOCUMENTS_READY`
4. `insert_message(db, user_msg_id, session_id, "user", query)`
5. `assistant_msg_id = str(uuid.uuid4())`; insert placeholder assistant message
6. Create `asyncio.Queue`; store in `_pending_streams[assistant_msg_id]`
7. `asyncio.create_task(_generate_response(...))`
8. Return `{"message_id": assistant_msg_id}`

**`GET /api/chat/stream/{message_id}`** (SSE)
- 404 if `message_id` not in `_pending_streams`
- Reads queue until event with `type in ("done", "error")`
- Each event: `data: {json}\n\n`
- Pops `message_id` from `_pending_streams` on close

**`_generate_response(...)` background task:**
1. `embed_query(query)` → on failure emit `{"type": "error", ...}` to queue
2. `query_chunks(session_id, embedding, top_k)` → on failure emit error
3. Build context block per FRD F01:
   ```
   [Source: {filename}, Page {page_number}, Chunk {chunk_index}]
   {chunk_text}
   ```
4. Build LLM messages:
   - System: grounding prompt (exact text from FRD F01 §Process step 9)
   - Optional history: `get_recent_messages(db, session_id, turns=CHAT_HISTORY_TURNS)`
   - User: context block + `"\n\nQuestion: {query}"`
5. Stream `openai.chat.completions.create(stream=True)` → emit `{"type":"token","delta":"..."}` per chunk
6. Detect refusal: content matches pattern `"i could not find"` or `retrieved == []`
7. `update_message(db, assistant_msg_id, full_response, is_refusal)`
8. If not refusal: `insert_citation(...)` for each retrieved chunk; `await db.commit()`
9. Emit `{"type": "done", "message": {full MessageResponse}}`
10. Errors (RateLimitError, APIConnectionError): emit `{"type": "error", ...}` with correct `error_code`

**`GET /api/chat/history/{session_id}`** → HTTP 200 or 404
- Returns all messages + their citations from DB

**`DELETE /api/chat/history/{session_id}`** → HTTP 204 or 404
- `delete_messages(db, session_id)` (cascades to citations)

**Acceptance criteria:**
- [ ] Empty query → 422 `EMPTY_QUERY`
- [ ] 2001-char query → 422 `QUERY_TOO_LONG`
- [ ] No READY documents → 422 `NO_DOCUMENTS_READY`
- [ ] Unknown session → 404 `SESSION_NOT_FOUND`
- [ ] Query with mocked LLM → HTTP 200 with `message_id`; SSE stream emits `token` events then `done` event
- [ ] History endpoint returns messages; delete clears them
- [ ] Tests in `tests/test_chat.py`

---

### T12 — Test Suite

**What it delivers:** Complete pytest suite covering all endpoints with mocked OpenAI. No real API key required for any test.

**Files:**

| File | Tests |
|------|-------|
| `backend/tests/conftest.py` | Shared fixtures |
| `backend/tests/fixtures/sample.txt` | `"This is a test document. The contract was signed on March 15 2024."` |
| `backend/tests/fixtures/sample.pdf` | Minimal valid PDF with extractable text |
| `backend/tests/fixtures/sample.docx` | Minimal valid DOCX with one paragraph |
| `backend/tests/test_sessions.py` | 4 tests (create, get, 404, distinct IDs) |
| `backend/tests/test_documents.py` | 8 tests (upload TXT/PDF/DOCX, too large, wrong type, bad session, status, list, delete) |
| `backend/tests/test_ingestion.py` | 9 unit tests (parse_txt, parse_txt_latin1, parse_pdf, parse_docx, parse_pdf_corrupt, chunk_txt, chunk_pdf, embed_mocked, vector_store round-trip) |
| `backend/tests/test_chat.py` | 8 tests (empty query, too long, no docs, unknown session, query returns message_id, history empty, history delete, delete unknown session) |

**`conftest.py` fixtures:**

```python
@pytest.fixture(autouse=True)
def ephemeral_chroma():
    # Injects chromadb.EphemeralClient() into vector_store module; resets after each test

@pytest.fixture
def client(tmp_path):
    # Sets DATABASE_URL to tmp SQLite; UPLOADS_DIR to tmp dir
    # Clears get_settings() lru_cache; runs init_db(); clears sessions registry
    # Returns FastAPI TestClient

@pytest.fixture
def mock_openai_embeddings():
    # Patches embedder._get_client() to return AsyncMock returning 1536-dim zero vectors

@pytest.fixture
def mock_openai_chat():
    # Patches chat.openai.AsyncOpenAI to return AsyncMock streaming fake tokens

@pytest.fixture
def sample_session(client):
    # POST /api/sessions → returns session_id
```

**Acceptance criteria:**
- [ ] `cd backend && pytest tests/ -v` exits 0 with 0 failures
- [ ] All tests pass with no real `OPENAI_API_KEY` (mocked throughout)
- [ ] Session, document, and chat smoke tests all pass
- [ ] No test leaves state in shared globals (sessions cleared between tests)

---

## Task Dependency Graph

```
Wave 1: T01
         │
         ├─── T02 (database)
         ├─── T03 (sessions)
Wave 2:  ├─── T04 (file validation)
         └─── T05 (parser)
                │
Wave 3:        T06 (chunker)       T07 (embedder)    T08 (vector store)
                └──────────────────────┴────────────────┘
                                       │
Wave 4:                               T09 (ingestion orchestrator)
                                       │
                        ┌──────────────┴──────────────┐
Wave 5:               T10 (document endpoints)    T11 (chat endpoints)
                        └──────────────┬──────────────┘
                                       │
Wave 6:                               T12 (test suite)
```

**Dependency notes:**
- T02, T03, T04, T05 all depend only on T01 (config + error codes) — implement in parallel
- T06 depends on T05 (`ParsedDocument` type); T07 and T08 depend only on T01
- T09 depends on T02 + T05 + T06 + T07 + T08
- T10 depends on T03 + T04 + T09; T11 depends on T02 + T03 + T07 + T08
- T12 can only be written after T10 and T11 are complete

---

## Phase Success Criteria

All of the following must be TRUE before Phase 1 is considered complete:

1. **Upload → READY:** `POST /api/documents/upload` with a real PDF returns HTTP 202; polling `GET /api/documents/{doc_id}/status` eventually returns `status: "READY"` with `chunk_count > 0`.

2. **Stage sequence:** Status polling during upload returns stages in order: `UPLOADING → PARSING → CHUNKING → EMBEDDING → INDEXING → READY`.

3. **Answerable query:** After uploading `sample.pdf`, `POST /api/chat/query` with a question whose answer is in the document → SSE stream completes with `is_refusal: false` and `retrieved_chunks` containing at least one item with a non-empty `excerpt`.

4. **Refusal:** `POST /api/chat/query` with a question unrelated to any uploaded document → SSE `done` event has `is_refusal: true` and `retrieved_chunks: []`.

5. **Delete clears embeddings:** `DELETE /api/documents/{doc_id}` → subsequent query that relied on that document returns `is_refusal: true`.

6. **Validation errors:** Each of the following returns the correct HTTP status and `error_code`:
   - File > 20 MB → HTTP 413, `FILE_TOO_LARGE`
   - JPEG renamed `.pdf` → HTTP 422, `INVALID_MIME_TYPE`
   - Corrupt PDF → HTTP 422, `PARSE_FAILURE`
   - Empty query → HTTP 422, `EMPTY_QUERY`
   - No READY documents → HTTP 422, `NO_DOCUMENTS_READY`

7. **Tests pass:** `cd backend && pytest tests/ -v` exits 0 with all tests passing and no real API key required.
