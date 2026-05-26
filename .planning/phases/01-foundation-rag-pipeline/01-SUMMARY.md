---
phase: 01-foundation-rag-pipeline
plan: 01
subsystem: api
tags: [fastapi, chromadb, openai, sqlite, aiosqlite, pymupdf, python-docx, tiktoken, langchain]

# Dependency graph
requires: []
provides:
  - FastAPI backend with full REST API for document RAG Q&A
  - Document ingestion pipeline (PDF/DOCX/TXT → chunk → embed → ChromaDB)
  - SQLite persistence for sessions, documents, chunks, messages, citations
  - Chat endpoints with streaming SSE responses grounded in uploaded documents
  - Complete pytest test suite (37 tests, no real API key required)
affects: []

# Tech tracking
tech-stack:
  added:
    - FastAPI 0.111+
    - ChromaDB >=0.6.0 (EphemeralClient for tests, PersistentClient in prod)
    - OpenAI SDK 1.30+ (embeddings + streaming chat)
    - PyMuPDF >=1.24.3 (PDF parsing)
    - python-docx (DOCX parsing)
    - tiktoken + langchain-text-splitters (token-based chunking)
    - python-magic (MIME detection)
    - aiosqlite (async SQLite)
    - pytest-asyncio (async test support)
  patterns:
    - FastAPI factory pattern (create_app()) for testability
    - Per-request dependency injection for DB connections
    - Background task pattern with separate DB connection for ingestion
    - SSE streaming via asyncio.Queue (documents + chat)
    - Module-level singletons with injectable overrides for testing (vector_store, embedder)
    - lru_cache for settings singleton with cache_clear() in tests

key-files:
  created:
    - backend/app/main.py
    - backend/app/config.py
    - backend/app/database.py
    - backend/app/models/session.py
    - backend/app/models/errors.py
    - backend/app/models/document.py
    - backend/app/models/chat.py
    - backend/app/routers/sessions.py
    - backend/app/routers/documents.py
    - backend/app/routers/chat.py
    - backend/app/utils/file_validation.py
    - backend/app/services/parser.py
    - backend/app/services/chunker.py
    - backend/app/services/embedder.py
    - backend/app/services/vector_store.py
    - backend/app/services/ingestion.py
    - backend/tests/conftest.py
    - backend/tests/test_sessions.py
    - backend/tests/test_documents.py
    - backend/tests/test_ingestion.py
    - backend/tests/test_chat.py
    - backend/tests/fixtures/sample.txt
    - backend/tests/fixtures/sample.pdf
    - backend/tests/fixtures/sample.docx
    - backend/requirements.txt
    - backend/pyproject.toml
    - backend/.env.example
  modified:
    - backend/requirements.txt (relaxed version pins for Python 3.14 compatibility)
    - backend/tests/conftest.py (asyncio.run() fix for Python 3.14)
    - backend/tests/test_chat.py (asyncio.run() fix for Python 3.14)

key-decisions:
  - "FastAPI create_app() factory pattern for full testability"
  - "ChromaDB page_number=None stored as -1 (metadata limitation), converted back on query"
  - "CORS allow_origins=['*'] for development"
  - "Background ingestion uses separate DB connection (_run_ingestion wrapper)"
  - "SSE streaming via asyncio.Queue for both document progress and chat tokens"
  - "get_settings() @lru_cache with cache_clear() in test fixtures"
  - "Flexible version ranges (>=) in requirements.txt for Python 3.14 system package compatibility"

patterns-established:
  - "Deviation Rule 1 - Bug: asyncio.get_event_loop() → asyncio.run() for Python 3.14"
  - "Deviation Rule 3 - Blocking: pymupdf version pin relaxed from ==1.24.3 to >=1.24.3"

# Metrics
duration: 32min
completed: 2026-05-26
---

# Phase 01: Foundation & RAG Pipeline — Summary

**FastAPI RAG backend with PDF/DOCX/TXT ingestion, ChromaDB vector search, streaming OpenAI chat responses, and 37-test pytest suite**

## Performance

- **Duration:** 32 min
- **Started:** 2026-05-26T14:50:37Z
- **Completed:** 2026-05-26T15:22:07Z
- **Tasks:** 12
- **Files modified:** 27

## Accomplishments

- Full FastAPI backend with 10 REST endpoints (sessions, documents, chat)
- Document ingestion pipeline: PDF/DOCX/TXT → token-based chunks → OpenAI embeddings → ChromaDB
- Per-session SQLite persistence for documents, chunks, messages, and citations
- Streaming SSE endpoints for ingestion progress and LLM chat tokens
- 37 pytest tests covering all endpoints with mocked OpenAI — no real API key needed

## Task Commits

Each task was committed atomically:

1. **T01: Project Scaffold & Configuration** - `5c635f3` (feat)
2. **T02: SQLite Database Layer** - `458ce27` (feat)
3. **T03: Session Management Endpoints** - `1d75eaf` (feat)
4. **T04: File Validation Utility** - `4c172ee` (feat)
5. **T05: Document Parser** - `e0f448d` (feat)
6. **T06: Text Chunker** - `af218e8` (feat)
7. **T07: Embedding Service** - `a01c6ae` (feat)
8. **T08: Vector Store Wrapper** - `bb39067` (feat)
9. **T09: Document Ingestion Orchestrator** - `9873d4a` (feat)
10. **T10: Document Endpoints** - `ef99a95` (feat)
11. **T11: Chat Endpoints** - `60657e6` (feat)
12. **T12: Test Suite** - `f99021a` (feat)

**Plan metadata:** `docs(phase-01)` commits at each milestone

## Files Created/Modified

- `backend/app/main.py` - FastAPI factory, lifespan, CORS, exception handler
- `backend/app/config.py` - Pydantic Settings with lru_cache singleton
- `backend/app/database.py` - Async SQLite schema + 16 CRUD helpers
- `backend/app/models/session.py` - SessionState dataclass + in-memory registry
- `backend/app/models/errors.py` - 16 ErrorCode enum values + ErrorResponse
- `backend/app/models/document.py` - Upload/Status/List response models
- `backend/app/models/chat.py` - Query/Citation/Message/History models
- `backend/app/routers/sessions.py` - POST + GET session endpoints
- `backend/app/routers/documents.py` - Upload, status, SSE, list, delete
- `backend/app/routers/chat.py` - Query, SSE stream, history, delete history
- `backend/app/utils/file_validation.py` - Magic-byte MIME detection + size checks
- `backend/app/services/parser.py` - PDF/DOCX/TXT parsers → ParsedDocument
- `backend/app/services/chunker.py` - tiktoken + LangChain recursive splitter
- `backend/app/services/embedder.py` - Batched OpenAI embeddings with retry backoff
- `backend/app/services/vector_store.py` - ChromaDB wrapper with set_client() for tests
- `backend/app/services/ingestion.py` - Pipeline orchestrator with SSE progress queue
- `backend/tests/conftest.py` - 5 fixtures: ephemeral_chroma, client, mock_openai_embeddings, mock_openai_chat, sample_session
- `backend/tests/test_sessions.py` - 4 session tests
- `backend/tests/test_documents.py` - 8 document endpoint tests
- `backend/tests/test_ingestion.py` - 14 unit tests (parser, chunker, embedder, vector store)
- `backend/tests/test_chat.py` - 9 chat endpoint tests (incl. query, history, delete)
- `backend/tests/fixtures/sample.{txt,pdf,docx}` - Test fixture files

## Decisions Made

- **Factory pattern:** `create_app()` function enables TestClient without lifespan side effects
- **ChromaDB None→-1:** Metadata cannot store None; page_number=-1 sentinel used, converted back on query
- **Background DB connection:** Ingestion runs as BackgroundTask with own DB connection (Depends-managed connection closes before background tasks run)
- **SSE via asyncio.Queue:** Both document progress and chat token streams use module-level Queue dicts
- **CORS:** `allow_origins=["*"]` for development simplicity

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] asyncio.get_event_loop() → asyncio.run() for Python 3.14**
- **Found during:** T12 (Test Suite) initial test run
- **Issue:** Python 3.14 raises `RuntimeError: There is no current event loop in thread 'MainThread'` when calling `asyncio.get_event_loop()` without a running loop (behavior changed from earlier Python versions)
- **Fix:** Replaced `asyncio.get_event_loop().run_until_complete(coro)` with `asyncio.run(coro)` in `conftest.py` client fixture and `test_chat.py` helper functions
- **Files modified:** `backend/tests/conftest.py`, `backend/tests/test_chat.py`
- **Verification:** All 37 tests pass
- **Committed in:** `f99021a` (T12 commit)

**2. [Rule 3 - Blocking] pymupdf version pin relaxed for Python 3.14 compatibility**
- **Found during:** T12 initial `pip install -r requirements.txt`
- **Issue:** `pymupdf==1.24.3` cannot be installed on Python 3.14 (wheel build fails); version 1.27.2.3 is already installed and compatible
- **Fix:** Changed pinned versions to flexible `>=` ranges across requirements.txt
- **Files modified:** `backend/requirements.txt`
- **Verification:** `pip install -r requirements.txt` completes successfully
- **Committed in:** `f99021a` (T12 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both auto-fixes essential for Python 3.14 compatibility. No scope creep.

## Issues Encountered

- Python 3.14 changed asyncio behavior (no implicit default event loop in main thread) — fixed with `asyncio.run()`
- Strict version pins in requirements.txt incompatible with Python 3.14's pre-installed packages — fixed with flexible `>=` ranges

## User Setup Required

None - no external service configuration required for test suite. Production usage requires `OPENAI_API_KEY` environment variable.

## Self-Check

Verified created files exist:

```
[FOUND] backend/app/main.py
[FOUND] backend/app/config.py
[FOUND] backend/app/database.py
[FOUND] backend/app/services/ingestion.py
[FOUND] backend/app/routers/chat.py
[FOUND] backend/tests/conftest.py
[FOUND] backend/tests/test_sessions.py
[FOUND] backend/tests/test_documents.py
[FOUND] backend/tests/test_ingestion.py
[FOUND] backend/tests/test_chat.py
[FOUND] backend/tests/fixtures/sample.txt
[FOUND] backend/tests/fixtures/sample.pdf
[FOUND] backend/tests/fixtures/sample.docx
```

Verified commits exist in git log: 5c635f3, 458ce27, 1d75eaf, 4c172ee, e0f448d, af218e8, a01c6ae, bb39067, 9873d4a, ef99a95, 60657e6, f99021a

Test results: **37 passed, 0 failed** — `cd backend && pytest tests/ -v` exits 0

## Self-Check: PASSED

## Next Phase Readiness

- Backend is fully operational and tested
- All 12 tasks complete with atomic commits
- No blockers; test suite provides regression coverage
- Ready for Phase 2 (frontend or deployment)

---
*Phase: 01-foundation-rag-pipeline*
*Completed: 2026-05-26*
