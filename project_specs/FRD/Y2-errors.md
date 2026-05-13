---

## Y2: Cross-Feature Error Catalog

This catalog lists every error code that the RAGChatbot API can return, the HTTP status it uses, the feature that produces it, and guidance for clients on whether/how to retry.

**Error response format (all errors):**
```json
{
  "error_code": "SCREAMING_SNAKE_CASE",
  "message": "Human-readable message for display",
  "detail": {}
}
```

---

### Document & Ingestion Errors (F00, F03)

| Error Code | HTTP Status | Feature | Cause | Retry? |
|---|---|---|---|---|
| `INVALID_FILE_TYPE` | 400 | F00 | File extension or MIME type not PDF/TXT/DOCX | No — fix file type |
| `FILE_TOO_LARGE` | 400 | F00 | File exceeds 50MB | No — use smaller file |
| `SESSION_STORAGE_LIMIT` | 400 | F00 | Session total uploads exceed 200MB | No — delete documents first |
| `SESSION_DOCUMENT_LIMIT` | 400 | F00 | Session already has 20 documents | No — delete documents first |
| `EMPTY_FILE` | 400 | F00 | Uploaded file is 0 bytes | No — fix file |
| `DOCUMENT_NOT_FOUND` | 404 | F00, F03 | document_id not in session or cross-session access | No |
| `INDEX_DELETE_ERROR` | 500 | F03 | Vector store failed to purge document chunks | Yes — retry delete |
| `PARSE_ERROR` | async (stored in status) | F00 | Text extraction from file failed | Yes — retry upload |
| `NO_TEXT_LAYER` | async (stored in status) | F00 | PDF is image-only; no extractable text | No — OCR not supported in v1 |
| `EMBED_ERROR` (ingestion) | async (stored in status) | F00 | Embedding API unavailable during ingestion | Yes — retry upload after delay |
| `INDEX_ERROR` | async (stored in status) | F00 | Vector store write failed during ingestion | Yes — retry upload |
| `EMPTY_DOCUMENT` | async (stored in status) | F00 | File parsed but produced zero text characters | No — use a different file |

*Note: Async errors do not produce HTTP error responses — they update the document `status` to `error` and set `error_reason`. The frontend discovers them via status polling (F00 §Process step 9).*

---

### Query & Answer Errors (F01, F06)

| Error Code | HTTP Status | Feature | Cause | Retry? |
|---|---|---|---|---|
| `EMPTY_QUERY` | 400 | F01 | Query is empty or whitespace-only | No — provide query |
| `QUERY_TOO_LONG` | 400 | F01 | Query exceeds 2000 characters | No — shorten query |
| `NO_READY_DOCUMENTS` | 422 | F01 | No documents with status `ready` in session | No — wait for indexing or upload |
| `QUERY_IN_PROGRESS` | 429 | F01 | Another query stream is active for this session | Yes — wait for current query to complete |
| `EMBED_ERROR` (query) | 503 | F01 | Embedding API unavailable during query embedding | Yes — retry after 5s |
| `LLM_UNAVAILABLE` | 503 | F01 | LLM API call failed after retries | Yes — retry after 10s |
| `LLM_TIMEOUT` | 504 | F01 | LLM response exceeded 30s timeout | Yes — retry |
| `RETRIEVAL_ERROR` | 503 | F01 | Vector store query failed | Yes — retry after 5s |
| `DOCUMENT_NOT_READY` | 422 | F06 | document_filter references a non-ready document | No — wait for indexing |
| `DOCUMENT_NOT_IN_INDEX` | 422 | F06 | Filtered document has no indexed chunks | No — re-upload document |

---

### Chat History & Session Errors (F04)

| Error Code | HTTP Status | Feature | Cause | Retry? |
|---|---|---|---|---|
| `SESSION_NOT_FOUND` | 404 | F04, all | Session cookie absent or session expired | No — a new session is created on next GET |
| `INVALID_EXPORT_FORMAT` | 400 | F08 | Export format parameter not "text" or "markdown" | No — fix parameter |

*Note: `GET /api/documents`, `GET /api/chat/history`, and `POST /api/session/reset` never return SESSION_NOT_FOUND — they create a new session instead.*

---

### Feedback Errors (F07)

| Error Code | HTTP Status | Feature | Cause | Retry? |
|---|---|---|---|---|
| `INVALID_RATING` | 400 | F07 | Rating is not "positive" or "negative" | No — fix value |
| `INVALID_MESSAGE_ROLE` | 400 | F07 | Feedback submitted for a user-role message | No |
| `FEEDBACK_ALREADY_SUBMITTED` | 409 | F07 | Message already has a rating | No — one rating per message |
| `MESSAGE_NOT_FOUND` | 404 | F07 | message_id not found in session | No |

---

### Infrastructure Errors

| Error Code | HTTP Status | Feature | Cause | Retry? |
|---|---|---|---|---|
| `INTERNAL_SERVER_ERROR` | 500 | All | Unexpected server error | Yes — retry; report if persistent |
| `SERVICE_DEGRADED` | 503 | Health | One or more backend dependencies unavailable | Yes — retry after delay |

---

### HTTP Status Code Summary

| Status | Used For |
|---|---|
| 200 | Successful GET, POST (feedback, session reset), export |
| 202 | Document upload accepted (async ingestion begins) |
| 204 | Successful DELETE (no body) |
| 400 | Client input validation errors |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate feedback) |
| 422 | Semantic validation errors (e.g., no ready documents) |
| 429 | Rate limit / in-progress conflict |
| 500 | Server-side unexpected errors |
| 503 | External dependency unavailable |
| 504 | Gateway/LLM timeout |

---

### Client Error Handling Guidelines

1. **400 errors:** Display the `message` field to the user verbatim. Do not retry automatically.
2. **404 errors on documents/messages:** Remove the stale item from the UI; it may have been deleted in another tab.
3. **422 NO_READY_DOCUMENTS:** Disable the chat input; show "Upload and index a document to get started."
4. **429 QUERY_IN_PROGRESS:** Disable the send button until the current stream completes; no user-visible error needed.
5. **503/504 errors:** Show a transient error message with a "Retry" button; do not immediately retry automatically.
6. **Async document errors (status=error):** Show an error badge on the document card with the human-readable reason and a "Retry Upload" button.
7. **SSE stream errors:** If the SSE connection drops mid-stream, show an error bubble: "Answer generation was interrupted. Please try again."
