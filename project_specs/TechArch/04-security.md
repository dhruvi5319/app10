## 5. Security Architecture

### 5.1 Authentication Model

RAGChatbot v1 uses **anonymous session-based authentication** — there are no user accounts. Identity is established solely by the session cookie.

| Property | Value |
|----------|-------|
| Mechanism | HTTP-only session cookie `rag_session_id` |
| Cookie flags | `HttpOnly=true`, `SameSite=Lax`, `Secure=true` (in production) |
| Session ID format | UUID v4 (128 bits of entropy; not guessable) |
| Session creation | Auto-created on first `GET /api/documents`, `GET /api/chat/history`, or `POST /api/session/reset` |
| Session lifetime | 24 hours of inactivity; server-side TTL enforced |
| Cross-session isolation | All data access is filtered by `session_id`; cross-session access returns 404 (not 403) to avoid leaking existence |

### 5.2 Authorization Model

Since there are no user accounts in v1, authorization is purely **session-scoped**:

| Rule | Implementation |
|------|---------------|
| Documents are session-private | Every document query includes `session_id` filter; `document_id` alone is never sufficient |
| Messages are session-private | Every message query includes `session_id` filter |
| Vector chunks are session-private | All vector store queries include `session_id` metadata filter |
| Cross-session access returns 404 | `DOCUMENT_NOT_FOUND` / `MESSAGE_NOT_FOUND` — never 403 — to avoid confirming resource existence |
| No admin endpoints | No privileged operations; all routes operate only within caller's session scope |

### 5.3 Document Data Isolation

```
Session A                    Session B
─────────                    ─────────
  doc-1 ──→ chunks            doc-3 ──→ chunks
  doc-2 ──→ chunks            doc-4 ──→ chunks
             │                            │
             └─── VectorStore ────────────┘
                  (filtered by session_id on every query)
```

- **Vector store queries** always pass `session_id` as a metadata filter. Even if two sessions share a Chroma collection (they don't in v1, but defensively), the filter ensures isolation.
- **Chroma collection naming** (`session_{session_id}`) provides physical namespace isolation as a defense-in-depth layer.
- **FAISS** uses per-session index files (`./data/faiss/{session_id}.faiss`), providing filesystem-level isolation.
- **Session reset** (`POST /api/session/reset`) purges all vector data for the old session before returning the new session ID.

### 5.4 Input Validation & Injection Prevention

| Attack Vector | Mitigation |
|--------------|-----------|
| Malicious file upload | Extension + MIME type whitelist; file size limits; parsed in isolated library (PyMuPDF/python-docx) |
| Prompt injection via document content | LLM system prompt explicitly prohibits external knowledge; document content is presented as "context" not "instructions" |
| Prompt injection via user query | Query is appended as a user turn, not injected into the system prompt; system prompt constraints are prepended |
| Cross-session data access | All DB/vector queries include `session_id` filter enforced in the service layer |
| Path traversal (file storage) | Uploaded files stored with UUID-based filenames; original filenames stored as metadata only |
| Large payload DoS | File size limits (50MB/file, 200MB/session); query length limit (2000 chars); session document count limit (20) |
| Concurrent query abuse | `query_in_progress` flag per session; 429 on concurrent query attempt |

### 5.5 API Security

| Concern | Implementation |
|---------|---------------|
| CORS | FastAPI CORS middleware; allowed origins configured via `ALLOWED_ORIGINS` env var (default: `http://localhost:3000`) |
| HTTPS | Required in production; `Secure` cookie flag enforced |
| Rate limiting | `query_in_progress` mutex per session prevents LLM API abuse; global rate limiting delegated to reverse proxy (nginx) in production |
| Error information leakage | Error responses use `error_code` enum + safe `message`; stack traces never exposed to client |
| Secrets management | All API keys loaded from environment variables; never hardcoded; `.env` excluded from version control |

### 5.6 Data Protection

| Category | Approach |
|----------|---------|
| Uploaded files | Stored temporarily in `./data/uploads/{document_id}/`; deleted after successful indexing (or on error cleanup) |
| Vector embeddings | Session-scoped; deleted on session reset or document deletion |
| Chat history | In-memory; lost on server restart; no cross-session persistence |
| API keys | Environment variables only; never logged |
| PII in documents | No PII extraction; content treated as opaque text for RAG pipeline |

### 5.7 Security Headers

```python
# FastAPI middleware configuration
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # restrict in production
)

# Response headers (via middleware or nginx):
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
# Content-Security-Policy: default-src 'self'; ...
```

---
