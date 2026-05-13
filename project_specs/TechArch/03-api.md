## 4. API Design

### 4.1 API Conventions

| Convention | Value |
|-----------|-------|
| Base URL | `/api` |
| Content-Type (requests) | `application/json` (except multipart upload) |
| Content-Type (responses) | `application/json` (except SSE and file export) |
| Authentication | Session cookie `rag_session_id` (HTTP-only, SameSite=Lax) |
| Session auto-creation | On `GET /api/documents`, `GET /api/chat/history`, `POST /api/session/reset` |
| Error format | `{ "error_code": "SCREAMING_SNAKE_CASE", "message": "...", "detail": {} }` |
| Streaming | Server-Sent Events (SSE) for `POST /api/chat/query` |
| Versioning | No versioning in v1; prefix `/api/v1/` reserved for future |

---

### 4.2 TypeScript Interfaces — Domain Types

```typescript
// ─── Enums ─────────────────────────────────────────────────────────────────

type DocumentStatus = 'uploading' | 'indexing' | 'ready' | 'error';
type MessageRole    = 'user' | 'assistant';
type ConfidenceLevel = 'high' | 'low' | 'none';
type UserRating     = 'positive' | 'negative';
type ExportFormat   = 'text' | 'markdown';

// ─── Session ───────────────────────────────────────────────────────────────

interface Session {
  session_id:        string;       // UUID v4
  created_at:        string;       // ISO 8601
  last_active_at:    string;       // ISO 8601
  document_count:    number;
  total_size_bytes:  number;
  query_in_progress: boolean;
}

// ─── Document ──────────────────────────────────────────────────────────────

interface Document {
  document_id:    string;               // UUID v4
  session_id:     string;               // UUID v4
  filename:       string;
  file_extension: 'pdf' | 'txt' | 'docx';
  mime_type:      string;
  size_bytes:     number;
  status:         DocumentStatus;
  chunk_count:    number;
  chunk_size:     number;               // default 512
  chunk_overlap:  number;               // default 64
  error_reason:   string | null;
  created_at:     string;               // ISO 8601
  indexed_at:     string | null;        // ISO 8601
}

// ─── Citation ──────────────────────────────────────────────────────────────

interface Citation {
  citation_index: number;               // 0-based
  document_id:    string;               // UUID v4
  document_name:  string;
  chunk_index:    number;
  chunk_text:     string;
  page_number:    number | null;
  similarity:     number;               // [0.0, 1.0]
}

// ─── Message ───────────────────────────────────────────────────────────────

interface Message {
  message_id:          string;          // UUID v4
  session_id:          string;          // UUID v4
  role:                MessageRole;
  content:             string;
  citations:           Citation[];      // empty array for user messages
  confidence:          ConfidenceLevel | null;  // null for user messages
  max_similarity:      number | null;   // null for user messages
  user_rating:         UserRating | null;
  rating_recorded_at:  string | null;   // ISO 8601
  created_at:          string;          // ISO 8601
}

// ─── SSE Events ────────────────────────────────────────────────────────────

interface SSETokenEvent {
  token: string;
}

interface SSEDoneEvent {
  done:             true;
  message_id:       string;             // UUID v4
  citations:        Citation[];
  confidence:       ConfidenceLevel;
  max_similarity:   number;
  document_sources: string[];           // deduplicated document filenames
  created_at:       string;             // ISO 8601
}

type SSEEvent = SSETokenEvent | SSEDoneEvent;

// ─── Health ────────────────────────────────────────────────────────────────

type HealthStatus = 'ok' | 'error';

interface HealthChecks {
  vector_store:   HealthStatus;
  embedding_api:  HealthStatus;
  llm_api:        HealthStatus;
}

interface HealthResponse {
  status:    'healthy' | 'degraded';
  timestamp: string;
  checks:    HealthChecks;
}
```

---

### 4.3 TypeScript Interfaces — Request/Response Bodies

```typescript
// ─── Document Upload ───────────────────────────────────────────────────────

// Request: multipart/form-data
// Fields: file (binary), chunk_size? (number), chunk_overlap? (number)

interface UploadDocumentResponse {   // 202 Accepted
  document_id:  string;
  filename:     string;
  status:       'uploading';
  size_bytes:   number;
  created_at:   string;
}

interface DocumentStatusResponse {   // 200 OK
  document_id:   string;
  filename:      string;
  status:        DocumentStatus;
  chunk_count:   number;
  indexed_at:    string | null;
  error_reason:  string | null;
}

// ─── Document List ─────────────────────────────────────────────────────────

interface DocumentListResponse {     // 200 OK
  session_id:        string;
  document_count:    number;
  total_size_bytes:  number;
  documents:         Document[];
}

// ─── Chat Query ────────────────────────────────────────────────────────────

interface ChatQueryRequest {
  query:                string;      // 1–2000 chars
  k?:                   number;      // [1–20]; default 5
  confidence_threshold?: number;     // [0.0–1.0]; default 0.30
  document_filter?:     string;      // UUID of document to restrict retrieval
}

// Response: text/event-stream (SSE)
// Stream: SSETokenEvent events, then final SSEDoneEvent
// Low-confidence fallback: 200 JSON (non-streaming)

interface LowConfidenceFallbackResponse {  // 200 OK (non-streaming)
  message_id:       string;
  answer:           string;          // "The uploaded documents do not contain..."
  citations:        [];
  confidence:       'none';
  max_similarity:   number;
  document_sources: [];
  created_at:       string;
}

// ─── Chat History ──────────────────────────────────────────────────────────

interface ChatHistoryResponse {      // 200 OK
  session_id:    string;
  message_count: number;
  messages:      Message[];
}

// ─── Chat Feedback ─────────────────────────────────────────────────────────

interface FeedbackRequest {
  message_id: string;               // UUID of assistant message
  rating:     UserRating;           // 'positive' | 'negative'
}

interface FeedbackResponse {         // 200 OK
  message_id:   string;
  rating:       UserRating;
  recorded_at:  string;             // ISO 8601
}

// ─── Session Reset ─────────────────────────────────────────────────────────

interface SessionResetResponse {     // 200 OK
  session_id:     string;           // New session ID
  message_count:  number;           // Always 0
  document_count: number;           // Always 0
  created_at:     string;
}

// ─── Error Response ────────────────────────────────────────────────────────

interface APIError {
  error_code: string;               // SCREAMING_SNAKE_CASE
  message:    string;               // Human-readable
  detail:     Record<string, unknown>;
}
```

---

### 4.4 API Endpoint Reference

#### Documents API

| Method | Path | Auth | Request | Response | Description |
|--------|------|------|---------|----------|-------------|
| `POST` | `/api/documents/upload` | Cookie | `multipart/form-data` (file, chunk_size?, chunk_overlap?) | `202 UploadDocumentResponse` | Upload document; start async ingestion |
| `GET` | `/api/documents/{document_id}/status` | Cookie | — | `200 DocumentStatusResponse` | Poll ingestion status |
| `GET` | `/api/documents` | Cookie | — | `200 DocumentListResponse` | List all session documents |
| `DELETE` | `/api/documents/{document_id}` | Cookie | — | `204 No Content` | Delete document + purge vector chunks |

**POST /api/documents/upload — Error codes:**

| HTTP | Code | Trigger |
|------|------|---------|
| 400 | `INVALID_FILE_TYPE` | Extension/MIME not PDF/TXT/DOCX |
| 400 | `FILE_TOO_LARGE` | File > 50MB |
| 400 | `SESSION_STORAGE_LIMIT` | Session total > 200MB |
| 400 | `SESSION_DOCUMENT_LIMIT` | Session has 20 documents |
| 400 | `EMPTY_FILE` | 0-byte file |
| 404 | `SESSION_NOT_FOUND` | Session expired |

**DELETE /api/documents/{document_id} — Error codes:**

| HTTP | Code | Trigger |
|------|------|---------|
| 404 | `DOCUMENT_NOT_FOUND` | Not found or cross-session |
| 500 | `INDEX_DELETE_ERROR` | Vector purge failed |

---

#### Chat API

| Method | Path | Auth | Request | Response | Description |
|--------|------|------|---------|----------|-------------|
| `POST` | `/api/chat/query` | Cookie | `ChatQueryRequest` JSON | `text/event-stream` SSE or `200 LowConfidenceFallbackResponse` | Submit question; stream answer |
| `GET` | `/api/chat/history` | Cookie | — | `200 ChatHistoryResponse` | Full session transcript |
| `DELETE` | `/api/chat/history` | Cookie | — | `204 No Content` | Clear messages (keep documents) |
| `GET` | `/api/chat/export` | Cookie | `?format=text\|markdown` | `200 File download` | Download transcript |

**POST /api/chat/query — Error codes:**

| HTTP | Code | Trigger |
|------|------|---------|
| 400 | `EMPTY_QUERY` | Empty/whitespace query |
| 400 | `QUERY_TOO_LONG` | Query > 2000 chars |
| 404 | `SESSION_NOT_FOUND` | Session expired |
| 422 | `NO_READY_DOCUMENTS` | No ready documents |
| 422 | `DOCUMENT_NOT_READY` | document_filter target not ready |
| 422 | `DOCUMENT_NOT_IN_INDEX` | Filtered document has no chunks |
| 429 | `QUERY_IN_PROGRESS` | Another stream active |
| 503 | `EMBED_ERROR` | Embedding API failure |
| 503 | `LLM_UNAVAILABLE` | LLM API failure |
| 503 | `RETRIEVAL_ERROR` | Vector store failure |
| 504 | `LLM_TIMEOUT` | LLM exceeded 30s |

---

#### Feedback API

| Method | Path | Auth | Request | Response | Description |
|--------|------|------|---------|----------|-------------|
| `POST` | `/api/chat/feedback` | Cookie | `FeedbackRequest` JSON | `200 FeedbackResponse` | Rate an assistant message |

**POST /api/chat/feedback — Error codes:**

| HTTP | Code | Trigger |
|------|------|---------|
| 400 | `INVALID_RATING` | Rating not positive/negative |
| 400 | `INVALID_MESSAGE_ROLE` | Feedback on user message |
| 404 | `MESSAGE_NOT_FOUND` | Message not in session |
| 404 | `SESSION_NOT_FOUND` | Session expired |
| 409 | `FEEDBACK_ALREADY_SUBMITTED` | Already rated |

---

#### Session API

| Method | Path | Auth | Request | Response | Description |
|--------|------|------|---------|----------|-------------|
| `POST` | `/api/session/reset` | Cookie | — | `200 SessionResetResponse` | Reset everything; new session |
| `GET` | `/api/health` | None | — | `200\|503 HealthResponse` | Backend health check |

---

### 4.5 SSE Stream Protocol Detail

The `POST /api/chat/query` endpoint returns a `text/event-stream` response when retrieval confidence meets the threshold. Clients must handle two event structures:

```
# Token events (one per LLM output token)
data: {"token": "The"}\n\n
data: {"token": " acquisition"}\n\n
data: {"token": " was"}\n\n

# Final done event (one, at end of stream)
data: {
  "done": true,
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "citations": [
    {
      "citation_index": 0,
      "document_id": "...",
      "document_name": "contract.pdf",
      "chunk_index": 7,
      "chunk_text": "...full passage text...",
      "page_number": 4,
      "similarity": 0.87
    }
  ],
  "confidence": "high",
  "max_similarity": 0.87,
  "document_sources": ["contract.pdf"],
  "created_at": "2026-05-13T10:05:06Z"
}\n\n
```

**Client implementation notes:**
- Use `EventSource` for GET endpoints; for POST with body, use `fetch` with `ReadableStream` and manual SSE parsing
- Accumulate `token` events into a string buffer; render buffer progressively
- On receiving `done: true`, finalize message and render citations
- On connection error mid-stream: show "Answer generation was interrupted" error bubble

---
