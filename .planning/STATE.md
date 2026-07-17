# Project State

## Current Position
- **Phase:** 02-core-mvp-ui
- **Current Task:** T06 (T05 complete)
- **Next Task:** T06 — Document Panel Component
- **Status:** Phase 02 in progress

## Phase 02 Progress

### Completed Tasks
- [x] T01 — Project Scaffold & API Client (commit: bdc4b21)
- [x] T02 — Session Hook & Initialisation (files in bdc4b21; verified build passes)
- [x] T03 — Application Layout (pre-scaffolded in 0d5bff6; verified spec compliance + build passes)
- [x] T04 — Document API Module & useDocuments Hook (pre-scaffolded in 0d5bff6; verified spec compliance + build passes)
- [x] T05 — Upload Zone Component (commit: 30c06e6; build passes 0 errors)

### Pending Tasks
- [ ] T06 — Document Panel Component
- [ ] T07 — Chat API Module & useChat Hook
- [ ] T08 — Chat Interface Components
- [ ] T09 — Citation Components
- [ ] T10 — Feedback Components
- [ ] T11 — Integration & Wiring

## Phase 01 Progress (Complete)

### Completed Tasks
- [x] T01 — Project Scaffold & Configuration (commit: 5c635f3)
- [x] T02 — SQLite Database Layer (commit: 458ce27)
- [x] T03 — Session Management Endpoints (commit: 1d75eaf)
- [x] T04 — File Validation Utility (commit: 4c172ee)
- [x] T05 — Document Parser (commit: e0f448d)
- [x] T06 — Text Chunker (commit: af218e8)
- [x] T07 — Embedding Service (commit: a01c6ae)
- [x] T08 — Vector Store Wrapper (commit: bb39067)
- [x] T09 — Document Ingestion Orchestrator (commit: 9873d4a)
- [x] T10 — Document Endpoints (commit: ef99a95)
- [x] T11 — Chat Endpoints (commit: 60657e6)
- [x] T12 — Test Suite (commit: f99021a)

## Decisions
- Used `SettingsConfigDict(env_file=".env", extra="ignore")` in config to be permissive
- All 16 ErrorCode values defined as `str, Enum` for JSON serialization compatibility
- FastAPI `create_app()` factory pattern established for testability
- CORS set to `allow_origins=["*"]` for development
- _emit() only puts to queue if doc_id already in _progress_queues (no implicit creation)
- Document router uses prefix="/documents" with get_db_dep async generator dependency
- /upload/stream route registered before /{doc_id}/status to avoid path conflicts
- Background ingestion uses separate DB connection (_run_ingestion wrapper)
- Chat router uses prefix="/chat" with get_db_dep pattern; GROUNDING_SYSTEM_PROMPT as constant
- _generate_response opens own DB connection; refusal = no chunks OR "i could not find" in response
- ChromaDB page_number=None stored as -1 (metadata limitation), converted back on query
- asyncio.run() used instead of asyncio.get_event_loop().run_until_complete() for Python 3.14
- Flexible version ranges (>=) in requirements.txt for Python 3.14 system package compatibility

## Performance Metrics

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 01-foundation-rag-pipeline | T01-T12 | 32min | 12 | 27 |

## Last Session
- **Stopped At:** Completed Phase 02 T05 — Upload Zone Component (commit: 30c06e6; build passes 0 errors)
- **Resume From:** Phase 02 T06 — Document Panel Component
- **Timestamp:** 2026-07-17T17:40:00Z
