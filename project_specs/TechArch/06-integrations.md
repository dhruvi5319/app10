## 7. Integration Points

### 7.1 Integration Overview

```
┌──────────────────────────────────────────────────────────┐
│                   RAGChatbot Backend                      │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Ingestion Pipeline                               │    │
│  │  parser → chunker → embedder → vector indexer    │    │
│  │                         │              │         │    │
│  └─────────────────────────┼──────────────┼─────────┘    │
│                             │              │              │
│  ┌──────────────────────────┼──────────────┼─────────┐    │
│  │  Query Pipeline          │              │         │    │
│  │  embedder → retriever → LLM caller      │         │    │
│  │       │          │          │           │         │    │
│  └───────┼──────────┼──────────┼───────────┼─────────┘    │
└──────────┼──────────┼──────────┼───────────┼──────────────┘
           │          │          │           │
           ▼          ▼          ▼           ▼
    ┌──────────┐ ┌─────────┐ ┌──────┐ ┌──────────────┐
    │ Document │ │ Embed.  │ │ LLM  │ │ Vector Store │
    │ Parsers  │ │   API   │ │  API │ │  (Chroma /   │
    │(local)   │ │(OpenAI/ │ │(OpenAI│ │ FAISS /      │
    │          │ │sentence-│ │/Claude│ │ Pinecone)    │
    │          │ │ transf.)│ │      │ │              │
    └──────────┘ └─────────┘ └──────┘ └──────────────┘
```

---

### 7.2 Embedding API Integration

**Purpose:** Generate vector representations for document chunks (ingestion) and user queries (at query time).

**Abstraction:** `EmbeddingService` abstract class with concrete `OpenAIEmbeddingService` and `LocalEmbeddingService` implementations. Switched via `EMBEDDING_PROVIDER` env var.

| Property | OpenAI | sentence-transformers |
|----------|--------|-----------------------|
| Model | `text-embedding-3-small` (default) or `text-embedding-3-large` | `all-MiniLM-L6-v2` |
| Dimensions | 1536 / 3072 | 384 |
| Transport | HTTPS REST API | Local Python library |
| Auth | `Authorization: Bearer {EMBEDDING_API_KEY}` | None |
| Batch size | Up to 100 texts per call | Unlimited |
| Cost | ~$0.02 per 1M tokens (3-small) | Free (local CPU) |

**Retry Policy:**
```
HTTP 429 (rate limit): backoff 1s → 2s → 4s (max 3 retries)
HTTP 500/503:          backoff 2s → 2s → 2s (max 3 retries)
Timeout (> 10s/batch): retry once; on second timeout → EMBED_ERROR
Ingestion failure:     set document.status = "error", error_reason = "embed_error"
Query failure:         return 503 EMBED_ERROR to client
```

---

### 7.3 LLM API Integration

**Purpose:** Generate grounded natural language answers from assembled prompts containing retrieved document chunks.

**Abstraction:** `LLMService` abstract class with `OpenAILLMService` and `AnthropicLLMService` implementations. Switched via `LLM_PROVIDER` env var. Both implementations normalize to the same SSE event protocol.

| Property | OpenAI | Anthropic |
|----------|--------|-----------|
| Default model | `gpt-4o` | `claude-3-5-sonnet-20241022` |
| Streaming | Chat Completions streaming API | Messages streaming API |
| Auth header | `Authorization: Bearer {LLM_API_KEY}` | `x-api-key: {LLM_API_KEY}` |
| Temperature | 0.1 | 0.1 |
| Max tokens | 1024 (configurable) | 1024 (configurable) |

**Grounding System Prompt (enforced on all LLM calls):**
```
You are a document assistant. Answer ONLY using the provided document excerpts below.
If the answer cannot be found in the excerpts, say so explicitly.
Do not use any outside knowledge, training data, or general world knowledge.
Do not speculate or infer beyond what is directly stated in the excerpts.
```

**Retry Policy:**
```
HTTP 429:        backoff 5s → 5s (max 2 retries) → 503 LLM_UNAVAILABLE
HTTP 500/503:    backoff 3s → 3s (max 2 retries) → 503 LLM_UNAVAILABLE
First token > 30s: immediate 504 LLM_TIMEOUT (no retry)
Mid-stream drop: close SSE to client; client shows interrupted error
```

---

### 7.4 Vector Store Integration

**Purpose:** Store, search, and delete chunk embeddings with session/document metadata for fast semantic retrieval.

**Abstraction:** `VectorStore` abstract class with three concrete implementations:

```python
class VectorStore(ABC):
    def upsert(self, vectors: list[VectorPayload]) -> None: ...
    def query(self, embedding: list[float], k: int,
              session_id: str, document_id: str | None = None
              ) -> list[QueryResult]: ...
    def delete_by_filter(self, session_id: str,
                         document_id: str | None = None) -> None: ...
    def delete_collection(self, session_id: str) -> None: ...
```

| Backend | Class | Use Case | Collection Naming |
|---------|-------|----------|------------------|
| ChromaDB | `ChromaVectorStore` | Default local dev & single-server prod | `session_{session_id}` |
| FAISS | `FAISSVectorStore` | Local alternative; better perf at scale | `{session_id}.faiss` file |
| Pinecone | `PineconeVectorStore` | Cloud/production deployment | namespace `{session_id}` |

**Metadata stored per vector:**
```python
{
    "document_id":   str,   # UUID
    "session_id":    str,   # UUID
    "chunk_index":   int,
    "document_name": str,
    "chunk_text":    str,
    "page_number":   int | None,
}
```

**Failure Handling:**

| Operation | Failure | Response |
|-----------|---------|---------|
| Upsert (ingestion) | Exception | Set document status = `error`, reason = `index_error` |
| Query | Exception | Return `503 RETRIEVAL_ERROR` |
| Delete (document) | Exception | Return `500 INDEX_DELETE_ERROR` |
| Delete (session reset) | Exception | Log warning; session reset proceeds anyway |

---

### 7.5 Document Parsing Libraries

**Purpose:** Extract plain text from uploaded document files during ingestion. All local — no network calls.

| Format | Library | Function | Notes |
|--------|---------|---------|-------|
| PDF | PyMuPDF (`fitz`) | `fitz.open(bytes)` | Extracts text with page boundaries; does not OCR |
| DOCX | python-docx | `Document(bytes)` | Extracts paragraphs, tables, headers/footers |
| TXT | Python stdlib | `bytes.decode('utf-8')` | Falls back to `latin-1` on UTF-8 decode error |

**Parse Output Contract:**
```python
@dataclass
class ParseResult:
    text: str                       # Full extracted text
    page_offsets: list[int] | None  # Char offset per page (PDF only)
    page_count: int | None          # Total pages (PDF/DOCX estimate only)
```

**Failure Handling:**
- `fitz.FitzError` → `error_reason = "parse_error"`
- Zero-length text after parse → `error_reason = "empty_document"`
- PyMuPDF returns empty text (image-only PDF) → `error_reason = "no_text_layer"`
- `python-docx.PackageNotFoundError` → `error_reason = "parse_error"`
- `UnicodeDecodeError` (TXT) → `error_reason = "parse_error"`

---

### 7.6 Browser Clipboard API (Frontend)

**Purpose:** Copy-to-clipboard for individual answers and citation text (F08).

**Implementation:**
```typescript
async function copyToClipboard(text: string): Promise<void> {
  try {
    // Primary: modern async Clipboard API (requires HTTPS or localhost)
    await navigator.clipboard.writeText(text);
  } catch {
    // Fallback: deprecated execCommand (broad support)
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  }
}
```

No server involvement. Failure is handled silently with a soft UI message.

---

### 7.7 Integration Dependency Matrix

| Feature | Embed API | LLM API | Vector Store | Parse Libs | Clipboard |
|---------|-----------|---------|-------------|-----------|---------|
| F00: Upload & Ingestion | ✅ Required | — | ✅ Required | ✅ Required | — |
| F01: Q&A (RAG) | ✅ Required | ✅ Required | ✅ Required | — | — |
| F02: Citations | — | — | — | — | — |
| F03: Doc Library | — | — | ✅ Delete only | — | — |
| F04: Chat History | — | — | — | — | — |
| F05: Premium UI | — | — | — | — | — |
| F06: Multi-Document | ✅ Required | ✅ Required | ✅ Required | — | — |
| F07: Confidence/Feedback | ✅ Required | ✅ Required | ✅ Required | — | — |
| F08: Export/Copy | — | — | — | — | ✅ Required |
| GET /api/health | ✅ Ping | ✅ Ping | ✅ Ping | — | — |

**Critical Path:** F00 + F01 require all three external integrations (Embed API, LLM API, Vector Store). The health endpoint verifies all three are reachable.

---

*TechArch-RAGChatbot v1.0 — generated 2026-05-13*
