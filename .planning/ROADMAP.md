# Project Roadmap
## RAG Chatbot

**Version:** 1.0
**Date:** 2026-05-13
**Status:** Active
**Based on:** PRD v1.0, FRD v1.0

---

## Overview

This roadmap transforms the RAG Chatbot PRD feature requirements (F0–F7) into three delivery phases. Phases are derived from natural dependency boundaries in the feature set — the backend pipeline must exist before the UI can use it; the core P0 Q&A loop must work before P1 session management layers on top; and P2 polish builds on a fully functional MVP.

**Core value (every phase must protect):** Users upload documents and receive accurate, cited answers sourced exclusively from those documents — never from external knowledge.

---

## Phases

- [x] **Phase 1: Foundation & RAG Pipeline** — Backend scaffolding, document ingestion pipeline, embedding, vector store, and the full backend RAG engine. No UI yet — verified via API only.
- [x] **Phase 2: Core MVP UI & Session** — React frontend wiring all P0 and P1 features: upload UI, chat Q&A with citations, document management panel, chat history, and error handling.
- [ ] **Phase 3: Polish & Developer Experience** — Responsive layout for mobile/tablet, accessibility (WCAG AA), and configurable RAG pipeline settings via `.env`.

---

## Progress Table

| Phase | Status | Completed |
|-------|--------|-----------|
| 1. Foundation & RAG Pipeline | Complete ✓ | 2026-05-26 |
| 2. Core MVP UI & Session | Gaps Found (2) | 2026-07-17 |
| 3. Polish & Developer Experience | Not started | — |

---

## Phase Details

---

### Phase 1: Foundation & RAG Pipeline

**Goal:** The backend is fully operational — it can receive a document, parse, chunk, embed, and index it, then accept a natural-language query, retrieve the most relevant chunks, call the LLM with a strict grounding prompt, and return a cited answer. All of this is verifiable via the REST API without any frontend UI.

**Depends on:** Nothing — this is the foundational phase.

**Features covered:**
- **F0** — Document Upload & Ingestion Pipeline (P0)
- **F1** — Chat Interface & Question Answering (P0, backend half only)
- **F2** — Source Citation & Passage Highlighting (P0, data model & backend only)

**Deliverables:**
1. FastAPI project scaffold: project structure, virtual environment, dependency lockfile (`requirements.txt` / `pyproject.toml`), `.env.example`, and server entry point.
2. Session management: `POST /api/sessions`, `GET /api/sessions/{session_id}` — creates and validates in-memory session state.
3. Document ingestion pipeline:
   - `POST /api/documents/upload` — accepts PDF, TXT, DOCX; validates type (magic bytes) and size (≤ 20 MB); rejects with correct error codes.
   - Parser layer: PyMuPDF for PDF (page-aware), python-docx for DOCX, UTF-8/latin-1 fallback for TXT.
   - Chunking: LangChain-compatible token-based splitter with configurable chunk size (default 500) and overlap (default 50).
   - Embedding: OpenAI `text-embedding-3-small` with batched calls (≤ 100 chunks/batch) and exponential backoff on rate-limit errors (3 retries).
   - Vector store: ChromaDB collection `session_{session_id}` with full metadata (`doc_id`, `filename`, `page_number`, `chunk_index`, `file_type`).
   - SQLite schema: `documents` and `chunks` tables with all constraints per FRD Y0.
4. Ingestion progress tracking: `GET /api/documents/{doc_id}/status` polling endpoint; SSE stream `GET /api/documents/upload/stream` returning `UPLOADING → PARSING → CHUNKING → EMBEDDING → INDEXING → READY / FAILED` stage events with `progress_pct`.
5. Chat Q&A backend:
   - `POST /api/chat/query` — validates session, non-empty query (1–2000 chars), and ≥ 1 READY document.
   - Query embedding → ChromaDB cosine-similarity top-k retrieval (default k=5).
   - Grounding prompt construction: strict system prompt ("answer ONLY from provided excerpts; refuse if absent"), context block with `[Source: filename, Page N, Chunk N]` headers, last 10 turns of chat history.
   - LLM call (OpenAI GPT-4o) with streaming enabled.
   - SSE stream `GET /api/chat/stream/{message_id}` delivering `{"type":"token","delta":"..."}` events and a final `{"type":"done","message":{...}}`.
6. Citation data model: `message_citations` table per FRD Y0 §Chat; every non-refusal assistant message stores `retrieved_chunks[]` with `filename`, `page_number`, `chunk_index`, `excerpt`, and `similarity_score`.
7. Document list endpoint: `GET /api/documents?session_id=...` returning full document list with status, chunk count, file size.
8. Document delete endpoint: `DELETE /api/documents/{doc_id}` — atomically removes vector store embeddings, `chunks` records, `documents` record, and uploaded file.
9. Chat history endpoints: `GET /api/chat/history/{session_id}`, `DELETE /api/chat/history/{session_id}`.
10. Startup: hard-coded defaults for all parameters (chunk size, overlap, top-k, etc.) with environment variable overrides — the full F07 config system is wired here so the backend is tunable from day one.

**Success Criteria** (what must be TRUE when Phase 1 completes):

1. A developer can `POST /api/documents/upload` with a real PDF and the response returns `status: "READY"` with a non-zero `chunk_count` — confirming parse, chunk, embed, and index all ran successfully.
2. Polling `GET /api/documents/{doc_id}/status` during upload returns the correct stage label (`PARSING`, `CHUNKING`, `EMBEDDING`, etc.) in sequence before resolving to `READY`.
3. A developer can `POST /api/chat/query` with a question whose answer exists in the uploaded document and receive an assistant response whose content cites a verbatim passage from that document (non-empty `retrieved_chunks[]` with `excerpt` text).
4. A developer can `POST /api/chat/query` with a question whose answer does NOT exist in any uploaded document and receive `is_refusal: true` with an explicit refusal message — no hallucinated content.
5. `DELETE /api/documents/{doc_id}` removes all embeddings: a subsequent `POST /api/chat/query` that previously used that document's content now returns `is_refusal: true` (or retrieves from remaining documents only).
6. Uploading a file > 20 MB, an unsupported type, or a corrupt PDF each return the correct HTTP status and `error_code` as specified in FRD F00 §Error States.

**Estimated effort:** Medium-Large — the majority of the backend complexity (parser, chunker, embedder, vector store, grounding prompt, streaming) lands here. Expect this to be the largest single phase.

---

**Status**: completed (2026-05-26)
**Last Updated**: 2026-05-26T15:43:02Z
### Phase 2: Core MVP UI & Session

**Goal:** The React frontend is fully built and wired to the Phase 1 backend. Every P0 and P1 feature is complete and usable end-to-end by a real user in a browser. Maya (legal analyst) and Ethan (researcher) can upload documents, ask questions, read cited answers, manage their document library, and scroll through session history without any developer tooling or configuration.

**Depends on:** Phase 1 (all backend endpoints must be operational).

**Features covered:**
- **F0** — Document Upload & Ingestion Pipeline (P0, frontend half)
- **F1** — Chat Interface & Question Answering (P0, frontend half)
- **F2** — Source Citation & Passage Highlighting (P0, frontend rendering)
- **F3** — Document Management Panel (P1)
- **F4** — Session-Scoped Chat History (P1)
- **F5** — System Feedback & Error Handling (P1)

**Deliverables:**
1. React project scaffold (Vite + TypeScript), Tailwind CSS or CSS Modules, component structure, API client module (fetch wrapper with session_id injection).
2. Session initialisation: on app load, call `POST /api/sessions` (or reuse existing cookie), store `session_id` in memory; call `GET /api/chat/history/{session_id}` and `GET /api/documents` to hydrate initial state.
3. Upload zone component (F0 frontend):
   - Drag-and-drop zone accepting `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/plain`.
   - Click-to-browse fallback (`<input type="file" accept=".pdf,.txt,.docx" multiple>`).
   - Client-side validation: extension check, 20 MB size cap — inline error shown immediately, file not sent.
   - Multi-file support: files queued and submitted sequentially or in parallel.
   - Per-file progress bar showing stage label (`Uploading → Parsing → Chunking → Embedding → Indexing → Ready ✓`), driven by SSE or polling against `GET /api/documents/{doc_id}/status`.
   - On READY: green checkmark + filename; document card added to Document Management Panel.
   - On FAILED: red progress bar with specific server error message and Retry button (re-submits same file bytes).
4. Document Management Panel component (F3):
   - Sidebar listing all `GET /api/documents` results; one Document Card per document.
   - Card shows: file-type icon (PDF/DOCX/TXT), filename (truncated > 30 chars with full-name tooltip), status badge (READY green / PROCESSING yellow spinner / FAILED red), relative upload timestamp.
   - Panel header: "Documents (N / 10)" and total storage in KB/MB.
   - Delete button per card: disabled while PROCESSING; confirmation dialog before `DELETE /api/documents/{doc_id}`; fade-out animation on success; counter decremented.
   - Empty state: "No documents uploaded yet. Drag a file here or click to upload."
   - Collapse toggle; collapsed state persisted in `localStorage`.
5. Chat interface component (F1 frontend):
   - Scrollable message thread: user messages right-aligned (dark bg), assistant messages left-aligned (light bg), each with a relative timestamp below the bubble.
   - Markdown rendering for assistant responses (bold, inline code, code blocks, lists) — use a lightweight renderer (e.g., `react-markdown`).
   - Input bar with textarea (Enter to send, Shift+Enter for newline) and Send button.
   - Send button disabled when: input is empty/whitespace, a query is in-flight, or no READY document exists.
   - Typing indicator (animated ellipsis) rendered as an assistant bubble while LLM is streaming.
   - SSE streaming: tokens appended to the assistant bubble in real time via `GET /api/chat/stream/{message_id}`; auto-scroll to bottom on each token.
   - On stream completion: typing indicator replaced by final message; `retrieved_chunks` passed to Citation component.
   - Guard message above input bar when no documents are READY: "Upload a document first to start asking questions." — auto-dismisses when first document reaches READY.
   - Chat toolbar: "Clear Chat" button (calls `DELETE /api/chat/history/{session_id}`); confirmation dialog; restores empty chat state without affecting documents.
6. Source Citation component (F2):
   - Rendered below each non-refusal assistant bubble.
   - Collapsible "Sources (N)" section header (collapsed by default); click to expand/collapse.
   - One Citation Card per item in `retrieved_chunks[]`, in returned order (most relevant first).
   - Card header: `📄 {filename} — page {page_number or "N/A"} — chunk {chunk_index + 1}`.
   - Card body: verbatim `excerpt` text in a blockquote/grey card; if excerpt > 800 chars, show first 800 with "Show more" toggle.
   - Visual divider between answer body and citation section; citation uses smaller font and secondary colour.
   - No citation section rendered when `is_refusal: true` or `retrieved_chunks` is empty.
7. Error handling across all components (F5):
   - Upload zone: inline file rejection errors (type/size) per file before submission.
   - Document card: inline `FAILED` state with server error message from SSE/polling.
   - Chat: LLM error replaces typing indicator with error bubble ("I couldn't generate a response right now. [Try again]") + top-right toast.
   - Network error: persistent banner "Connection lost. Check your network and [retry]." — retry re-fires failed request.
   - All error messages in plain language — no HTTP codes, no stack traces visible to user.
   - Toast logic: informational toasts auto-dismiss in 5 s; error toasts requiring action persist until dismissed.
8. Desktop layout: Document Panel (280 px fixed left column) + Chat panel (remaining width), both always visible on viewports ≥ 1024 px. (Full responsive behaviour deferred to Phase 3; desktop-first layout must be clean and functional.)

**Success Criteria** (what must be TRUE when Phase 2 completes):

1. A user (no developer setup required) can open the app in a browser, drag a PDF onto the upload zone, watch the progress bar advance through all stages, and see the document appear as READY in the Document Panel — all within 30 seconds for a 50-page PDF.
2. After uploading a document, the user can type a question whose answer appears in the document, press Enter, watch the typing indicator, and read a streaming assistant response that contains the correct answer — without the answer referencing any external knowledge.
3. Every assistant response that is not a refusal displays a collapsed "Sources (N)" section; clicking it reveals at least one Citation Card with the source filename and a verbatim excerpt from the document.
4. When the user asks a question that cannot be answered from the uploaded documents, the assistant responds with a clear refusal message and no citation section is shown — confirming the grounding constraint is upheld at the UI level.
5. The user can click the delete icon on a document in the Document Panel, confirm the dialog, and see the document disappear from the panel — and a subsequent question that previously relied on that document now returns a refusal or sources from remaining documents only.
6. The user can scroll back through all prior Q&A exchanges in the session thread and click "Clear Chat" to reset the conversation without losing uploaded documents.
7. All error states (unsupported file, file too large, LLM unavailable, network failure) surface a human-readable message with a clear recovery path — no blank screens, no silent failures, no raw HTTP error codes visible to the user.

**Estimated effort:** Medium-Large — large component surface (upload zone, progress, chat thread, streaming, citations, document panel, error system) but the backend is already complete; this is purely frontend wiring.

---

**Status**: In Progress
### Phase 3: Polish & Developer Experience

**Goal:** The application is production-quality: it works correctly on mobile and tablet viewports, meets WCAG AA accessibility standards, and is fully configurable by a developer via `.env` without touching application code. Jordan (technical evaluator) can tune every pipeline parameter and the product is usable by Maya on her phone or tablet.

**Depends on:** Phase 2 (full MVP must be complete before polish is applied).

**Features covered:**
- **F6** — Responsive & Accessible UI (P2)
- **F7** — Configurable RAG Pipeline Settings (P2)

**Deliverables:**
1. Responsive layout (F6):
   - Tablet breakpoint (600–1023 px): Document Panel collapsed to icon-strip (48 px) by default; toggle expands to full 280 px overlay or side-by-side; chat fills full width when panel is collapsed.
   - Mobile breakpoint (< 600 px): Document Panel hidden by default; "Documents" FAB or bottom-bar toggle opens a bottom drawer at ~60% viewport height with drag-to-dismiss; chat occupies full viewport.
   - Drag-and-drop upload zone degrades gracefully to tap-to-upload on touch devices.
   - All touch targets ≥ 44 × 44 px on mobile breakpoints.
   - Verified correct rendering at 320 px, 768 px, and 1440 px viewport widths.
2. Accessibility implementation (F6):
   - Full keyboard navigation: all interactive elements (buttons, inputs, upload zone, citation expand/collapse, panel toggle) reachable and operable via Tab + Enter/Space.
   - Visible focus states (outline/ring) on all focusable elements — no element has focus ring removed without a replacement.
   - Skip navigation link ("Skip to main content") as first DOM element, hidden until focused, jumping to chat input.
   - Chat message thread: `role="log"` + `aria-live="polite"` so screen readers announce new messages.
   - Typing indicator: `role="status"` + `aria-label="Assistant is typing"`.
   - All icon-only buttons have `aria-label` describing action (e.g., `aria-label="Delete document"`, not `aria-label="trash icon"`).
   - Upload zone: `role="button"` or `role="region"` + `aria-label="File upload area"`.
   - WCAG AA colour contrast: ≥ 4.5:1 for body text; ≥ 3:1 for large text and UI controls.
   - All font sizes in `rem` units; scales with browser text-size preferences.
   - Status badges use both colour AND text label (not colour alone).
   - Modal/dialog focus trap: delete confirmation and clear-chat dialogs trap focus within while open; focus returns to trigger element on close.
   - Semantic HTML: landmark elements (`<main>`, `<aside>`, `<nav>`, `<header>`), proper heading hierarchy.
   - Lighthouse accessibility audit score ≥ 90; axe-core zero critical violations.
3. Configurable RAG pipeline settings (F7):
   - `python-dotenv` integration: `.env` loaded at server startup; env vars override `.env` values.
   - Pydantic `BaseSettings` singleton (`Settings`) with all 16 configurable parameters per FRD F07 §Configuration Parameters: `LLM_PROVIDER`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `LLM_MODEL`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `CHAT_HISTORY_TURNS`, `MAX_FILE_SIZE_MB`, `MAX_DOCS_PER_SESSION`, `LLM_TEMPERATURE`, `VECTOR_STORE`, `VECTOR_STORE_PATH`, `UPLOADS_DIR`, `LOG_LEVEL`.
   - Hard-coded defaults for every parameter (system works out-of-the-box with only API key provided).
   - Startup validation: missing required API key → CRITICAL log + exit code 1; unrecognised `LLM_PROVIDER` or `VECTOR_STORE` → CRITICAL + exit; out-of-range numerics → clamped + WARNING; `CHUNK_OVERLAP ≥ CHUNK_SIZE` → auto-corrected + WARNING; `VECTOR_STORE_PATH` not writable → CRITICAL + exit.
   - Sanitised startup INFO log: all resolved parameters printed, API keys shown as `sk-...XXXX` (last 4 chars only).
   - `.env.example` committed to repo with all parameters documented; `.env` in `.gitignore`.
   - All backend pipeline components (upload, chunking, embedding, retrieval, LLM call) read from the `Settings` singleton — no hard-coded values remain in application code.

**Success Criteria** (what must be TRUE when Phase 3 completes):

1. A user on a mobile phone (320 px viewport) can tap the Documents button to open the drawer, tap to select and upload a PDF, and receive a cited answer in the chat — all core functionality works on mobile.
2. A keyboard-only user can navigate the entire application without a mouse: Tab through all interactive elements, upload a file, type and submit a question, expand a citation, delete a document, and clear chat — all without ever reaching a keyboard trap (except inside confirmation dialogs, which trap correctly and release on close).
3. Running the Lighthouse accessibility audit or axe-core against the live application returns a score ≥ 90 and zero critical WCAG AA violations.
4. A developer can create a `.env` file with `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=...`, `CHUNK_SIZE=300`, `TOP_K=8`, and `LLM_TEMPERATURE=0.2`, restart the server, and observe the startup log confirming all values were picked up — without any code changes.
5. Starting the server with no `.env` and no environment variables (other than a valid `OPENAI_API_KEY`) produces a working application with all defaults applied, confirming fallback defaults cover all parameters.
6. Starting the server with `LLM_PROVIDER=openai` but no `OPENAI_API_KEY` causes the server to exit immediately with a CRITICAL log message — it does not start and leave the user confused about why queries fail.

**Estimated effort:** Small-Medium — F7 backend config is well-specified and mechanical; F6 responsive layout is straightforward CSS work; accessibility implementation is the most careful part but is well-bounded.

---

## Coverage Validation

All 8 PRD features (F0–F7) are assigned to exactly one phase. No features are unassigned or duplicated.

| Feature | Description | Priority | MVP? | Phase |
|---------|-------------|----------|------|-------|
| **F0** | Document Upload & Ingestion Pipeline | P0 | ✅ | Phase 1 (backend) + Phase 2 (frontend) |
| **F1** | Chat Interface & Question Answering | P0 | ✅ | Phase 1 (backend) + Phase 2 (frontend) |
| **F2** | Source Citation & Passage Highlighting | P0 | ✅ | Phase 1 (data model) + Phase 2 (rendering) |
| **F3** | Document Management Panel | P1 | ✅ | Phase 2 |
| **F4** | Session-Scoped Chat History | P1 | ✅ | Phase 2 |
| **F5** | System Feedback & Error Handling | P1 | ✅ | Phase 2 |
| **F6** | Responsive & Accessible UI | P2 | ⚪ | Phase 3 |
| **F7** | Configurable RAG Pipeline Settings | P2 | ⚪ | Phase 3 |

> **Note on split features:** F0, F1, and F2 span Phase 1 and Phase 2 because they have a natural backend/frontend boundary. The backend RAG pipeline (Phase 1) and the frontend wiring (Phase 2) are distinct, independently verifiable units of work. Both phases must complete for these features to reach end-to-end functionality.

**Coverage:** 8/8 features assigned ✓ — No orphaned features.

---

## Dependency Map

```
Phase 1: Foundation & RAG Pipeline
    │
    │  (backend API must be operational before frontend is wired)
    ▼
Phase 2: Core MVP UI & Session
    │
    │  (full MVP functionality required before polish is applied)
    ▼
Phase 3: Polish & Developer Experience
```

**Cross-phase dependency details:**

| Dependency | Reason |
|-----------|--------|
| Phase 2 requires Phase 1 complete | Frontend components call Phase 1 API endpoints; upload progress SSE, chat streaming, citation data, and document management all depend on working backend routes. |
| Phase 3 requires Phase 2 complete | F6 responsive layout wraps existing components — components must exist in their final form before responsive breakpoints are applied. F7 config system requires all pipeline parameters to be in their final locations in code. |
| F7 (Phase 3) partially enables Phase 1 | The F07 config system is partially bootstrapped in Phase 1 (hard-coded defaults + env var overrides for API keys) to avoid hard-coded secrets from day one. Full F07 validation, logging, and `.env.example` are completed in Phase 3. |

---

## Non-Functional Requirements Traceability

The following NFRs from PRD §7 are addressed across phases:

| NFR | Target | Addressed In |
|-----|--------|-------------|
| Response latency P95 | < 5 seconds time-to-first-token | Phase 1 (streaming SSE) + Phase 2 (streaming UI) |
| Upload-to-ready time | < 30 seconds for 50-page PDF | Phase 1 (async pipeline, batched embeddings) |
| Retrieval hit rate | ≥ 85% relevant chunk in top-k | Phase 1 (chunking strategy, metadata filtering) |
| Grounding compliance | 100% — no external knowledge | Phase 1 (strict system prompt + refusal response) |
| File size limit | 20 MB per file | Phase 1 (backend validation) + Phase 2 (client-side validation) |
| Max docs per session | 10 | Phase 1 (backend guard) + Phase 2 (UI feedback) |
| Frontend bundle size | < 500 KB gzipped | Phase 2 (lightweight dependencies, code splitting) |
| Accessibility | WCAG AA | Phase 3 (F6 complete implementation) |
| API key security | Server-side only; never exposed to frontend | Phase 1 (no key in API responses) + Phase 3 (F7 .env) |

---

## Persona-to-Phase Mapping

| Persona | Phase where their primary needs are met |
|---------|----------------------------------------|
| **PER-01 Maya** (Legal Analyst) | Phase 2 — upload PDF, ask clause-level questions, expand citations, manage documents, scroll history |
| **PER-02 Ethan** (Researcher) | Phase 2 — batch upload PDFs, cross-document queries, markdown rendering, multi-citation answers |
| **PER-03 Jordan** (Developer/Evaluator) | Phase 3 — full `.env` config, startup logs, edge-case error handling; Phase 1 — API-level validation |

---

## Risk Register

| Risk | Impact | Phase | Mitigation |
|------|--------|-------|-----------|
| LLM ignores grounding instructions | High | Phase 1 | Strict system prompt with explicit refusal instruction; validated in Phase 1 success criteria (criterion 4) |
| Chunking strategy produces poor retrieval quality | High | Phase 1 | Default 500-token chunks with 50-token overlap; chunk parameters configurable via env vars from Phase 1 onwards |
| Embedding API rate limits slow large uploads | Medium | Phase 1 | Batched embedding calls (≤ 100/batch) with 3-retry exponential backoff |
| Large PDFs (100+ pages) exceed processing time NFR | Medium | Phase 1 | Async pipeline with SSE progress; 20 MB file cap; progress visible to user at all times |
| Image-only PDFs yield no extractable text | Medium | Phase 1 | PyMuPDF text extraction check; `NO_EXTRACTABLE_TEXT` error returned with clear message |
| OpenAI API unavailable during demo | High | Phase 2 | Error bubble + retry CTA in chat; `LLM_UNAVAILABLE` error code surfaced clearly (F5) |
| Streaming SSE cross-browser compatibility | Medium | Phase 2 | Use `EventSource` API (broadly supported); fallback to polling via `GET /api/documents/{doc_id}/status` |

---

*Document generated: 2026-05-13*
*Source: PROJECT.md, PRD.md v1.0, FRD v1.0 (F00–F07, Y0)*
*Next downstream: Implementation plans per phase*