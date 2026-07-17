---
status: complete
phase: 02-core-mvp-ui
source: [SUMMARY.md, 02-02-SUMMARY.md, 02-08-SUMMARY.md]
started: 2026-07-17T19:57:50Z
updated: 2026-07-17T20:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. App Loads & Session Initializes
expected: Opening the app URL shows the two-column layout (Document Panel on the left, Chat panel on the right). No blank screen, no error screen. The UI is interactive within a few seconds.
result: issue
reported: "Failed to start session.  Please refresh the page to try again."
severity: blocker

### 2. Document Upload with Progress
expected: Drag a PDF onto the upload zone (or click to browse and select one). A progress bar appears showing stages: Uploading → Parsing → Chunking → Embedding → Indexing → Ready ✓. The document then appears in the Document Panel with a green READY badge and the correct filename.
result: skipped
reason: Session error from Test 1 prevents reaching the upload UI

### 3. Document Panel — Status & Count
expected: The Document Panel header shows "Documents (1 / 10)" after uploading one document. Each document card shows: the file-type icon, the filename (truncated if long), a green READY badge, and a delete button. An empty state ("No documents uploaded yet…") appears when no documents are present.
result: skipped
reason: Blocked by session initialization failure (Test 1)

### 4. Chat — Send Message & Streaming Response
expected: With a READY document in the panel, type a question whose answer exists in that document and press Enter (or click Send). A typing indicator (animated dots) appears as the assistant bubble while the LLM responds. Tokens stream into the bubble in real time. The final response contains the correct answer rendered with markdown (bold, lists, code blocks if applicable).
result: skipped
reason: Blocked by session initialization failure (Test 1)

### 5. Citation Section — Sources Expand
expected: Below each non-refusal assistant response, a collapsed "Sources (N)" section appears. Clicking it reveals Citation Cards — one per retrieved chunk — each showing the filename, page number, chunk number, and a verbatim excerpt from the document. Long excerpts (>800 chars) show a "Show more" toggle.
result: skipped
reason: Blocked by session initialization failure (Test 1)

### 6. Refusal — No Documents or Off-Topic Question
expected: Ask a question that cannot be answered from the uploaded document(s) (e.g., something completely unrelated). The assistant responds with a clear refusal message ("I could not find information about that in the uploaded documents" or similar). No citation section is displayed below the refusal message.
result: skipped
reason: Blocked by session initialization failure (Test 1)

### 7. Delete Document
expected: Click the delete icon on a document card in the Document Panel. A confirmation dialog appears. Confirm the deletion. The document disappears from the panel with a fade-out animation and the document count decrements. A subsequent question that relied on that document now returns a refusal (or cites only remaining documents).
result: skipped
reason: Blocked by session initialization failure (Test 1)

### 8. Clear Chat
expected: Click the "Clear Chat" button in the chat toolbar. A confirmation dialog appears. Confirm it. The message thread resets to empty (or shows the guard message if no READY document remains). The Document Panel is unaffected — all uploaded documents remain.
result: skipped
reason: Blocked by session initialization failure (Test 1)

### 9. Error Handling — Unsupported File & LLM Error
expected: (a) Drop a file with an unsupported type (e.g., .jpg or .exe) onto the upload zone — an inline error appears immediately on that file, it is not sent to the server. (b) If possible to trigger an LLM error (e.g., disconnect network briefly during a query), an error bubble replaces the typing indicator and a toast notification appears in the top-right corner.
result: skipped
reason: Blocked by session initialization failure (Test 1)

## Summary

total: 9
passed: 0
issues: 1
pending: 0
skipped: 8

## Self-Check

boot: 200
routes_probed: 5 ok / 0 failed
cookie: n/a
per_test:
  - test: 1
    verdict: pass
    note: "🤖 Auto-check: GET http://127.0.0.1:3000/ → 200. Frontend serves HTML. Backend POST /api/sessions → 201 with valid session_id. App is running."
  - test: 2
    verdict: skipped (needs human)
    note: "🤖 Auto-check: POST /api/sessions → 201, GET /api/documents?session_id=... → 200 (empty list). Upload flow requires file drag/drop — needs human."
  - test: 3
    verdict: skipped (needs human)
    note: "🤖 Auto-check: Document Panel state depends on upload completing — needs human to verify visual."
  - test: 4
    verdict: skipped (needs human)
    note: "🤖 Auto-check: POST /api/chat/query with no docs → 422 NO_DOCUMENTS_READY (correct guard). Full streaming flow needs a real uploaded document — needs human."
  - test: 5
    verdict: skipped (needs human)
    note: "🤖 Auto-check: Citation section rendering is visual and depends on a real LLM response — needs human."
  - test: 6
    verdict: advisory
    note: "🤖 Auto-check: POST /api/chat/query with no ready docs → 422 NO_DOCUMENTS_READY. Backend correctly rejects. UI guard message is visual — needs human."
  - test: 7
    verdict: skipped (needs human)
    note: "🤖 Auto-check: DELETE /api/documents/{doc_id} endpoint exists (backend Phase 1). Confirmation dialog and fade animation are visual — needs human."
  - test: 8
    verdict: skipped (needs human)
    note: "🤖 Auto-check: DELETE /api/chat/history/{session_id} endpoint exists (backend Phase 1). Clear Chat dialog is visual — needs human."
  - test: 9
    verdict: skipped (needs human)
    note: "🤖 Auto-check: Client-side file validation (type/size) is in the frontend — needs human to drop an unsupported file."

## Gaps

- truth: "Opening the app shows the two-column layout; session initializes on load without error"
  status: failed
  reason: "User reported: Failed to start session.  Please refresh the page to try again."
  severity: blocker
  test: 1
  source: user
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
