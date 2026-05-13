---

## Y3: External Integration Points

This section documents every external system the RAGChatbot backend depends on, the integration contract, failure modes, and fallback behavior.

---

### §1: Embedding Model API

**Purpose:** Generate vector embeddings for document chunks (during ingestion, F00) and for user queries (during answering, F01).

**Supported providers:**

| Provider | Model | Dimensions | Notes |
|---|---|---|---|
| OpenAI | `text-embedding-3-small` | 1536 | Default; cost-effective |
| OpenAI | `text-embedding-3-large` | 3072 | Higher quality; higher cost |
| sentence-transformers | `all-MiniLM-L6-v2` | 384 | Local; no API key needed; lower quality |

**Integration contract:**
- Input: Array of text strings (batch call)
- Output: Array of float vectors, one per input string
- Authentication: API key via `Authorization: Bearer {key}` header (OpenAI) or no auth (local sentence-transformers)
- Batch size limit: Max 100 texts per call (OpenAI); unlimited (local)

**Failure handling:**
- HTTP 429 (rate limit): Exponential backoff — retry after 1s, 2s, 4s (max 3 retries)
- HTTP 500/503: Retry up to 3 times with 2s backoff
- Timeout (> 10s per batch): Retry once; if second attempt also times out, fail with `EMBED_ERROR`
- On final failure during ingestion: set document status to `error` with reason `embed_error`
- On final failure during query: return `503 EMBED_ERROR` to client

**Config keys:** `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_API_KEY`

---

### §2: LLM (Answer Generation) API

**Purpose:** Generate natural language answers from the assembled grounded prompt (F01).

**Supported providers:**

| Provider | Model | Notes |
|---|---|---|
| OpenAI | `gpt-4o` | Default; best quality/speed balance |
| OpenAI | `gpt-4o-mini` | Faster; lower cost; slightly lower quality |
| Anthropic | `claude-3-5-sonnet-20241022` | Alternative; strong instruction following |

**Integration contract:**
- Protocol: Chat completions API with streaming enabled
- System prompt: Grounding instruction (see F01 §Grounding Constraint)
- User message: Assembled prompt with retrieved chunks + user query
- Response: Token stream via SSE (OpenAI) or streaming messages (Anthropic); backend relays to client as standardized SSE events
- Authentication: API key via `Authorization: Bearer {key}` (OpenAI) or `x-api-key: {key}` (Anthropic)

**Parameters sent to LLM:**
- `temperature`: 0.1 (low, for factual grounded answers)
- `max_tokens`: 1024 (configurable)
- `stream`: true

**Failure handling:**
- HTTP 429 (rate limit): Retry up to 2 times with 5s backoff; then return `503 LLM_UNAVAILABLE`
- HTTP 500/503: Retry up to 2 times with 3s backoff; then return `503 LLM_UNAVAILABLE`
- Timeout (> 30s for first token): Return `504 LLM_TIMEOUT` immediately without retry
- Mid-stream drop (connection reset): Close SSE stream to client; client shows interrupted error
- No partial retry of mid-stream failures in v1

**Config keys:** `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES`

---

### §3: Vector Store

**Purpose:** Store, search, and delete chunk embeddings (F00 ingestion, F01 retrieval, F03 deletion).

**Supported backends:**

| Backend | Type | Use Case |
|---|---|---|
| Chroma | Local / in-process | Default for development and single-instance deployment |
| FAISS | Local / file-based | Alternative local option; better performance at scale |
| Pinecone | Cloud / hosted | Production cloud deployment option |

**Integration contract:**
- **Upsert:** Insert chunk embeddings with metadata at ingestion time
- **Query:** Top-k cosine similarity search with optional metadata filter (`session_id`, `document_id`)
- **Delete:** Delete all vectors matching a metadata filter (for document deletion, F03)
- **Collection/index naming:** `session_{session_id}` (Chroma collection or FAISS file or Pinecone namespace)

**Chroma specifics:**
- Client mode: In-process (same Python process as FastAPI) for v1
- Persistence path: `./data/chroma/` (configurable via env var)
- Collection auto-created on first document upload; auto-deleted on session reset

**FAISS specifics:**
- Index stored as `.faiss` binary + companion `_meta.json` for chunk metadata
- Path: `./data/faiss/{session_id}.faiss`
- Metadata deletion requires rebuilding the index (FAISS does not support in-place deletion); implemented by filtering in-memory

**Pinecone specifics:**
- Index must be pre-created with correct dimensions and cosine metric
- Namespaces used per session for isolation
- Namespace deletion on session reset via `delete_all=True` in namespace

**Failure handling:**
- Query failure: Return `503 RETRIEVAL_ERROR`
- Upsert failure: Set document status to `error` with reason `index_error`
- Delete failure: Return `500 INDEX_DELETE_ERROR`
- For Pinecone: apply retry with exponential backoff (max 3 attempts) before surfacing error

**Config keys:** `VECTOR_STORE_TYPE`, `VECTOR_STORE_PATH`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`

---

### §4: Document Parsing Libraries

**Purpose:** Extract plain text from uploaded document files during ingestion (F00).

**Libraries used:**

| Format | Library | Notes |
|---|---|---|
| PDF | PyMuPDF (`fitz`) | Fast, robust; handles embedded text; does not OCR image-only pages |
| DOCX | python-docx | Extracts paragraph text; tables as text rows; headers/footers included |
| TXT | Python stdlib (`open`, `read`) | UTF-8 decode with fallback to latin-1 |

**Integration contract:**
- Input: Raw file bytes
- Output: Plain text string (Unicode) + optional page-number offsets for PDF
- Page number tracking: PDF provides per-page text blocks; DOCX estimates page breaks by paragraph count heuristic; TXT has no pages

**Failure handling:**
- PyMuPDF raises exception on corrupt PDF: catch, set `error_reason = "parse_error"`
- PyMuPDF returns empty text on image-only PDF: detect zero-length output, set `error_reason = "no_text_layer"`
- python-docx raises exception on corrupt DOCX: catch, set `error_reason = "parse_error"`
- TXT decode failure (e.g., binary file with `.txt` extension): catch `UnicodeDecodeError`, set `error_reason = "parse_error"`
- Zero-length text after successful parse: set `error_reason = "empty_document"`

**No external API calls:** All parsing is done locally with installed Python packages; no network dependency.

---

### §5: Browser Clipboard API

**Purpose:** Copy-to-clipboard functionality for individual answers and citations (F08).

**Integration contract:**
- Primary: `navigator.clipboard.writeText(text)` — async, requires HTTPS or localhost
- Fallback: `document.execCommand('copy')` via programmatically selected `<textarea>` — synchronous, deprecated but widely supported

**Failure handling:**
- If both methods fail: show soft message "Copy unavailable in this browser" — never throw an unhandled error
- No server involvement; purely client-side

---

### Integration Dependency Matrix

| Feature | Embedding API | LLM API | Vector Store | Parse Libraries | Clipboard API |
|---|---|---|---|---|---|
| F00: Upload & Ingestion | ✅ | — | ✅ | ✅ | — |
| F01: Q&A | ✅ | ✅ | ✅ | — | — |
| F02: Citations | — | — | — | — | — |
| F03: Doc Library | — | — | ✅ (delete) | — | — |
| F04: Chat History | — | — | — | — | — |
| F05: UI | — | — | — | — | — |
| F06: Multi-Doc | ✅ | ✅ | ✅ | — | — |
| F07: Confidence | ✅ | ✅ | ✅ | — | — |
| F08: Export/Copy | — | — | — | — | ✅ |

---

*FRD-RAGChatbot v1.0 — Y3 Integrations — generated 2026-05-13*
