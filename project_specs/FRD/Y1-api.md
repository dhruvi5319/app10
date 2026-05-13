---

## Y1: REST API Endpoint Catalog

**Base URL:** `/api`  
**Content-Type:** `application/json` (all requests/responses unless noted)  
**Auth:** Session cookie `rag_session_id` (HTTP-only, SameSite=Lax). Auto-issued on first request if absent.  
**Error format:**
```json
{ "error_code": "SCREAMING_SNAKE_CASE", "message": "Human-readable message", "detail": {} }
```

---

### §Documents

#### POST /api/documents/upload

Upload a document file for ingestion into the session vector index.

**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | binary | Yes | Document file bytes |
| `chunk_size` | integer | No | Tokens per chunk [128–2048]; default 512 |
| `chunk_overlap` | integer | No | Token overlap [0, chunk_size-1]; default 64 |

**Responses:**

`202 Accepted`
```json
{
  "document_id": "uuid-v4",
  "filename": "report.pdf",
  "status": "uploading",
  "size_bytes": 1048576,
  "created_at": "2026-05-13T10:00:00Z"
}
```

`400 Bad Request` — validation errors (INVALID_FILE_TYPE, FILE_TOO_LARGE, SESSION_STORAGE_LIMIT, SESSION_DOCUMENT_LIMIT, EMPTY_FILE)

---

#### GET /api/documents/{document_id}/status

Poll ingestion status for a specific document.

**Path parameters:** `document_id` (UUID)

**Responses:**

`200 OK`
```json
{
  "document_id": "uuid-v4",
  "filename": "report.pdf",
  "status": "ready",
  "chunk_count": 143,
  "indexed_at": "2026-05-13T10:00:28Z",
  "error_reason": null
}
```

`404 Not Found` — DOCUMENT_NOT_FOUND

---

#### GET /api/documents

List all documents in the current session.

**Responses:**

`200 OK`
```json
{
  "session_id": "sess-abc123",
  "document_count": 2,
  "total_size_bytes": 2097152,
  "documents": [
    {
      "document_id": "uuid-v4",
      "filename": "report.pdf",
      "file_extension": "pdf",
      "size_bytes": 1048576,
      "status": "ready",
      "chunk_count": 143,
      "created_at": "2026-05-13T10:00:00Z",
      "indexed_at": "2026-05-13T10:00:28Z",
      "error_reason": null
    }
  ]
}
```

*Returns empty `documents` array (not 404) if session has no documents. Creates session if no cookie present.*

---

#### DELETE /api/documents/{document_id}

Delete a document and purge all its vector index entries.

**Path parameters:** `document_id` (UUID)

**Responses:**

`204 No Content` — success; body empty  
`404 Not Found` — DOCUMENT_NOT_FOUND  
`500 Internal Server Error` — INDEX_DELETE_ERROR

---

### §Chat

#### POST /api/chat/query

Submit a question and receive a streamed answer via Server-Sent Events.

**Request body (JSON):**

| Field | Type | Required | Notes |
|---|---|---|---|
| `query` | string | Yes | User question; 1–2000 chars |
| `k` | integer | No | Top-k retrieval count [1–20]; default 5 |
| `confidence_threshold` | float | No | Min similarity [0.0–1.0]; default 0.30 |
| `document_filter` | string (UUID) | No | Restrict retrieval to one document (F06) |

**Response:** `text/event-stream` (SSE)

Stream events during generation:
```
data: {"token": "The"}
data: {"token": " contract"}
...
```

Final event:
```
data: {
  "done": true,
  "message_id": "uuid-v4",
  "citations": [
    {
      "citation_index": 0,
      "document_id": "uuid",
      "document_name": "contract.pdf",
      "chunk_index": 7,
      "chunk_text": "...expires on December 31, 2026...",
      "page_number": 4,
      "similarity": 0.87
    }
  ],
  "confidence": "high",
  "max_similarity": 0.87,
  "document_sources": ["contract.pdf"],
  "created_at": "2026-05-13T10:05:06Z"
}
```

Low-confidence fallback (non-streaming, `200 OK` with JSON body):
```json
{
  "message_id": "uuid-v4",
  "answer": "The uploaded documents do not contain information about this topic.",
  "citations": [],
  "confidence": "none",
  "max_similarity": 0.18,
  "document_sources": [],
  "created_at": "2026-05-13T10:05:00Z"
}
```

**Error responses:**

`400` — EMPTY_QUERY, QUERY_TOO_LONG  
`404` — SESSION_NOT_FOUND, DOCUMENT_NOT_FOUND (if document_filter invalid)  
`422` — NO_READY_DOCUMENTS, DOCUMENT_NOT_READY, DOCUMENT_NOT_IN_INDEX  
`429` — QUERY_IN_PROGRESS  
`503` — EMBED_ERROR, LLM_UNAVAILABLE, RETRIEVAL_ERROR  
`504` — LLM_TIMEOUT

---

#### GET /api/chat/history

Retrieve full session chat transcript in chronological order.

**Responses:**

`200 OK`
```json
{
  "session_id": "sess-abc123",
  "message_count": 4,
  "messages": [
    {
      "message_id": "uuid-1",
      "role": "user",
      "content": "What was the total revenue in 2025?",
      "citations": [],
      "confidence": null,
      "max_similarity": null,
      "user_rating": null,
      "rating_recorded_at": null,
      "created_at": "2026-05-13T10:05:00Z"
    },
    {
      "message_id": "uuid-2",
      "role": "assistant",
      "content": "Revenue for fiscal year 2025 totaled $4.2 billion.",
      "citations": [ { "...": "..." } ],
      "confidence": "high",
      "max_similarity": 0.91,
      "user_rating": null,
      "rating_recorded_at": null,
      "created_at": "2026-05-13T10:05:06Z"
    }
  ]
}
```

*Returns empty messages array (not 404) if no messages exist. Creates session if no cookie.*

---

#### DELETE /api/chat/history

Clear all messages from the session transcript (documents and vector index untouched).

**Responses:**

`204 No Content` — success  
`404 Not Found` — SESSION_NOT_FOUND

---

#### GET /api/chat/export

Download session transcript as a formatted text file.

**Query parameters:**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `format` | string | Yes | `"text"` or `"markdown"` |

**Responses:**

`200 OK` with file download  
- `Content-Type`: `text/plain; charset=utf-8` or `text/markdown; charset=utf-8`  
- `Content-Disposition`: `attachment; filename="rag-transcript-{session_id}.txt"` or `.md`  
- Body: Formatted transcript string

`400 Bad Request` — INVALID_EXPORT_FORMAT  
`404 Not Found` — SESSION_NOT_FOUND

---

### §Feedback

#### POST /api/chat/feedback

Submit user thumbs-up or thumbs-down rating for an assistant message.

**Request body (JSON):**

| Field | Type | Required | Notes |
|---|---|---|---|
| `message_id` | string (UUID) | Yes | Must be an assistant message in current session |
| `rating` | string | Yes | `"positive"` or `"negative"` |

**Responses:**

`200 OK`
```json
{
  "message_id": "uuid-v4",
  "rating": "positive",
  "recorded_at": "2026-05-13T10:15:00Z"
}
```

`400` — INVALID_RATING, INVALID_MESSAGE_ROLE  
`404` — MESSAGE_NOT_FOUND, SESSION_NOT_FOUND  
`409` — FEEDBACK_ALREADY_SUBMITTED

---

### §Session

#### POST /api/session/reset

Reset the entire session — purges all documents, vector index entries, and messages; creates a fresh session.

**Request:** No body required.

**Responses:**

`200 OK` (new session cookie set in response headers)
```json
{
  "session_id": "sess-new-xyz",
  "message_count": 0,
  "document_count": 0,
  "created_at": "2026-05-13T10:20:00Z"
}
```

*Always succeeds; if old session doesn't exist, a new one is created anyway.*

---

### §Health

#### GET /api/health

System health check — verifies all backend dependencies are reachable.

**Responses:**

`200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2026-05-13T10:00:00Z",
  "checks": {
    "vector_store": "ok",
    "embedding_api": "ok",
    "llm_api": "ok"
  }
}
```

`503 Service Unavailable`
```json
{
  "status": "degraded",
  "timestamp": "2026-05-13T10:00:00Z",
  "checks": {
    "vector_store": "ok",
    "embedding_api": "error",
    "llm_api": "ok"
  }
}
```

---

### API Summary Table

| Method | Path | Feature | Priority |
|---|---|---|---|
| `POST` | `/api/documents/upload` | F00 | P0 |
| `GET` | `/api/documents/{document_id}/status` | F00 | P0 |
| `GET` | `/api/documents` | F03 | P1 |
| `DELETE` | `/api/documents/{document_id}` | F03 | P1 |
| `POST` | `/api/chat/query` | F01, F02, F06 | P0 |
| `GET` | `/api/chat/history` | F04 | P1 |
| `DELETE` | `/api/chat/history` | F04 | P1 |
| `GET` | `/api/chat/export` | F08 | P3 |
| `POST` | `/api/chat/feedback` | F07 | P2 |
| `POST` | `/api/session/reset` | F04 | P1 |
| `GET` | `/api/health` | Infra | — |
