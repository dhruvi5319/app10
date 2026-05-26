---
status: complete
phase: 01-foundation-rag-pipeline
source: [01-SUMMARY.md]
started: 2026-05-26T15:30:00Z
updated: 2026-05-26T15:45:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Session Creation
expected: POST /api/sessions returns 200 with a session_id (UUID). GET /api/sessions/{session_id} confirms the session exists.
result: pass

### 2. Document Upload — PDF reaches READY
expected: POST /api/documents/upload with a real PDF returns a doc_id. Polling GET /api/documents/{doc_id}/status eventually returns status "READY" with a non-zero chunk_count.
result: pass

### 3. Ingestion Progress Stages
expected: While a document is processing, GET /api/documents/{doc_id}/status returns the correct stage labels in sequence (UPLOADING → PARSING → CHUNKING → EMBEDDING → INDEXING → READY) — not just jumping straight to READY.
result: pass

### 4. File Type Rejection
expected: Uploading an unsupported file type (e.g., .jpg or .exe) returns an HTTP 4xx error with an error_code field — the server rejects it cleanly, no 500 error.
result: pass

### 5. File Size Rejection
expected: Uploading a file larger than 20 MB returns an HTTP 4xx error with an error_code indicating the size limit was exceeded.
result: pass

### 6. Chat Q&A with Citations
expected: POST /api/chat/query with a question whose answer exists in the uploaded document returns is_refusal: false and a non-empty retrieved_chunks[] array containing excerpt text and source metadata (filename, page_number, chunk_index).
result: pass

### 7. Chat Refusal for Out-of-Scope Question
expected: POST /api/chat/query with a question whose answer does NOT exist in any uploaded document returns is_refusal: true and a clear refusal message — no hallucinated content, no retrieved_chunks.
result: pass

### 8. Document Delete Removes Embeddings
expected: DELETE /api/documents/{doc_id} succeeds. A subsequent POST /api/chat/query that previously relied on that document's content now returns is_refusal: true — confirming embeddings were fully purged.
result: pass

### 9. Chat History Endpoints
expected: GET /api/chat/history/{session_id} returns prior messages from the session. DELETE /api/chat/history/{session_id} clears the history — a subsequent GET returns an empty list.
result: pass

### 10. Test Suite — 37 Tests Pass
expected: Running `cd backend && pytest tests/ -v` completes with 37 passed, 0 failed. No errors, no skipped tests due to missing dependencies.
result: pass

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0

## Gaps

[none]
