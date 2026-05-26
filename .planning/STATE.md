# Project State

## Current Position
- **Phase:** 01-foundation-rag-pipeline
- **Current Task:** T11 complete
- **Next Task:** T12
- **Status:** In progress

## Phase 01 Progress

### Completed Tasks
- [x] T01 — Project Scaffold & Configuration
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

### Pending Tasks
- [ ] T12 — Test Suite

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

## Last Session
- **Stopped At:** Completed T11 Chat Endpoints (commit: 60657e6)
- **Resume From:** T12 Test Suite
- **Timestamp:** 2026-05-26T18:30:00Z
