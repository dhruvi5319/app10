---

## Y0: Database / Storage Schema

**Scope:** This section defines all data structures used by the RAGChatbot backend. Because v1 uses in-memory / server-side session storage (no persistent SQL database), schema definitions are expressed as Python dataclass / Pydantic model equivalents and JSON structures rather than SQL DDL. A migration to a persistent store (PostgreSQL + pgvector, or SQLite) in a future version should be straightforward from these definitions.

---

### §Sessions

Each server-side session is keyed by a UUID session ID stored in the `rag_session_id` HTTP cookie.

```python
class Session:
    session_id: str           # UUID v4; set as cookie value
    created_at: datetime      # UTC ISO 8601
    last_active_at: datetime  # Updated on each API call
    document_ids: list[str]   # Ordered list of document UUIDs in this session
    message_ids: list[str]    # Ordered list of message UUIDs in this session
    total_size_bytes: int     # Sum of all document sizes in bytes
    query_in_progress: bool   # True while an LLM stream is active
```

**Session lifetime (v1):** In-memory; lost on server restart. Session TTL: 24 hours of inactivity (auto-expire and purge).

**Session limits enforced:**
- `len(document_ids)` ≤ 20
- `total_size_bytes` ≤ 209,715,200 (200 MB)

---

### §Documents

One record per uploaded document file. Stored in session-scoped in-memory dict keyed by `document_id`.

```python
class Document:
    document_id: str              # UUID v4; assigned on upload acceptance
    session_id: str               # Parent session UUID
    filename: str                 # Original filename as uploaded (e.g., "report.pdf")
    file_extension: str           # Lowercase: "pdf" | "txt" | "docx"
    mime_type: str                # Validated MIME type string
    size_bytes: int               # File size in bytes
    status: DocumentStatus        # Enum: uploading | indexing | ready | error
    chunk_count: int              # Number of chunks successfully indexed (0 until ready)
    chunk_size: int               # Tokens per chunk used during ingestion (default 512)
    chunk_overlap: int            # Token overlap between chunks (default 64)
    error_reason: str | None      # Error code string if status == error; else None
    created_at: datetime          # UTC ISO 8601; set on upload acceptance
    indexed_at: datetime | None   # UTC ISO 8601; set when status transitions to ready

class DocumentStatus(str, Enum):
    UPLOADING = "uploading"
    INDEXING  = "indexing"
    READY     = "ready"
    ERROR     = "error"
```

**Error reason values:** `parse_error`, `no_text_layer`, `embed_error`, `index_error`, `empty_document`

---

### §Chunks

Chunks are NOT stored in the session in-memory store — they live exclusively in the vector store (Chroma/FAISS). However, each chunk carries the following metadata fields at index time:

```python
class ChunkMetadata:
    document_id: str      # UUID of the parent document
    session_id: str       # UUID of the parent session (used for session-scoped retrieval)
    chunk_index: int      # 0-based position of this chunk within the document
    document_name: str    # Filename of the parent document (denormalized for fast citation)
    chunk_text: str       # The raw text content of this chunk
    page_number: int | None  # Page number from source document; None for TXT files
    token_count: int      # Number of tokens in this chunk
```

**Vector store collection naming:**
- Chroma: one collection per session named `session_{session_id}`
- FAISS: one index file per session stored at `./data/indices/{session_id}.faiss` with a companion metadata JSON file

**Retrieval filter:** All queries filter by `session_id` metadata to ensure cross-session isolation.

---

### §Messages

One record per chat message (user or assistant). Stored in session-scoped in-memory list in insertion order.

```python
class Message:
    message_id: str               # UUID v4
    session_id: str               # Parent session UUID
    role: MessageRole             # Enum: user | assistant
    content: str                  # Full message text
    citations: list[Citation]     # Empty list for user messages; populated for assistant
    confidence: Confidence | None # None for user messages; high | low | none for assistant
    max_similarity: float | None  # Highest retrieval score; None for user messages
    user_rating: Rating | None    # None until feedback submitted (F07)
    rating_recorded_at: datetime | None
    created_at: datetime          # UTC ISO 8601

class MessageRole(str, Enum):
    USER      = "user"
    ASSISTANT = "assistant"

class Confidence(str, Enum):
    HIGH = "high"
    LOW  = "low"
    NONE = "none"

class Rating(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"

class Citation:
    citation_index: int       # 0-based index within this message's citations list
    document_id: str          # UUID of source document
    document_name: str        # Filename of source document
    chunk_index: int          # Chunk index within source document
    chunk_text: str           # Raw text of the chunk (stored at answer time)
    page_number: int | None   # Source page number; None if not available
    similarity: float         # Cosine similarity score [0.0, 1.0]
```

**Citation storage:** Stored as a JSON array within the message record (not a separate collection in v1).

**Message limits:** No hard per-session limit on message count in v1; natural cap from session size limits.

---

### §VectorIndex

The vector index is managed by the configured vector store library and is not directly modeled as application code. Key behavioral contracts:

| Property | Value |
|---|---|
| Index type | Chroma (default local) or FAISS (local) or Pinecone (cloud) |
| Embedding dimension | Matches configured embedding model (e.g., 1536 for `text-embedding-3-small`) |
| Similarity metric | Cosine similarity |
| Namespace / Collection | One per session (`session_{session_id}`) |
| Metadata stored per vector | `document_id`, `session_id`, `chunk_index`, `document_name`, `chunk_text`, `page_number` |
| Delete granularity | By `document_id` metadata filter (to support F03 document deletion) |
| Session isolation | Enforced via `session_id` metadata filter on all queries |

---

### §ConfigStore

Runtime configuration values (environment-variable sourced; not persisted in session store).

```python
class AppConfig:
    # Embedding
    embedding_provider: str      # "openai" | "sentence-transformers"
    embedding_model: str         # e.g., "text-embedding-3-small"
    embedding_api_key: str       # From environment variable

    # LLM
    llm_provider: str            # "openai" | "anthropic"
    llm_model: str               # e.g., "gpt-4o" | "claude-3-5-sonnet-20241022"
    llm_api_key: str             # From environment variable
    llm_timeout_seconds: int     # Default: 30
    llm_max_retries: int         # Default: 3

    # Vector Store
    vector_store_type: str       # "chroma" | "faiss" | "pinecone"
    vector_store_path: str       # Local path for Chroma/FAISS; Pinecone index name for cloud

    # RAG Parameters
    default_top_k: int           # Default: 5
    default_chunk_size: int      # Default: 512
    default_chunk_overlap: int   # Default: 64
    default_confidence_threshold: float  # Default: 0.30
    low_confidence_split: float  # Fixed: 0.60 (high vs. low boundary)

    # Session
    session_ttl_hours: int       # Default: 24
    max_documents_per_session: int   # Default: 20
    max_file_size_bytes: int     # Default: 52,428,800 (50MB)
    max_session_size_bytes: int  # Default: 209,715,200 (200MB)
```
