## 6. Technology Stack

### 6.1 Backend Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | Python | 3.11+ | Backend runtime |
| API Framework | FastAPI | 0.111+ | REST API, SSE streaming, async request handling |
| ASGI Server | Uvicorn | 0.29+ | ASGI server; production: uvicorn + gunicorn |
| Data Validation | Pydantic v2 | 2.7+ | Request/response schema validation; config models |
| Settings | pydantic-settings | 2.2+ | Environment variable loading with type coercion |
| Session Cookies | FastAPI built-in | — | `Response.set_cookie`, `Request.cookies` |
| Async Tasks | FastAPI `BackgroundTasks` | — | Non-blocking document ingestion pipeline |
| Document Parsing — PDF | PyMuPDF (`fitz`) | 1.24+ | Fast PDF text extraction with page-level metadata |
| Document Parsing — DOCX | python-docx | 1.1+ | DOCX paragraph/table extraction |
| Document Parsing — TXT | Python stdlib | — | UTF-8 text decode with latin-1 fallback |
| Text Chunking | LangChain `RecursiveCharacterTextSplitter` | 0.2+ | Token-aware chunking with configurable size/overlap |
| Token Counting | tiktoken | 0.7+ | OpenAI-compatible token counting |
| Embedding (OpenAI) | openai | 1.30+ | `text-embedding-3-small` / `text-embedding-3-large` |
| Embedding (local) | sentence-transformers | 3.0+ | `all-MiniLM-L6-v2` for local/offline use |
| LLM (OpenAI) | openai | 1.30+ | GPT-4o with streaming |
| LLM (Anthropic) | anthropic | 0.28+ | Claude 3.5 Sonnet with streaming |
| Vector Store (default) | chromadb | 0.5+ | In-process local vector store with metadata filtering |
| Vector Store (alt) | faiss-cpu | 1.8+ | Local FAISS index with companion metadata JSON |
| Vector Store (cloud) | pinecone | 4.0+ | Pinecone hosted index with namespace isolation |
| HTTP Client | httpx | 0.27+ | Async HTTP for external API calls |
| Testing | pytest + pytest-asyncio | 8.x / 0.23+ | Backend unit/integration tests |
| Test coverage | pytest-cov | 5.x | Coverage reporting (target: > 70% on RAG pipeline) |

### 6.2 Frontend Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | TypeScript | 5.4+ | Type-safe frontend development |
| Framework | React | 18.3+ | Component-based UI |
| Build Tool | Vite | 5.x | Fast dev server and production bundler |
| State Management | Zustand | 4.5+ | Lightweight global state (session, documents, messages) |
| HTTP Client | Axios | 1.7+ | REST API calls with cookie support |
| SSE Streaming | native `fetch` + `ReadableStream` | — | POST SSE stream parsing (EventSource only supports GET) |
| Styling | Tailwind CSS | 3.4+ | Utility-first CSS; responsive breakpoints; WCAG colors |
| Component Library | shadcn/ui + Radix UI | latest | Accessible base components (modals, badges, buttons) |
| Drag and Drop | react-dropzone | 14.x | File drag-and-drop with validation hooks |
| Markdown Rendering | react-markdown | 9.x | Safe rendering of LLM markdown output |
| Icons | Lucide React | 0.381+ | Consistent icon set (trash, thumbs, copy, etc.) |
| Date/Time | date-fns | 3.x | Relative timestamps ("2 min ago") |
| Accessibility Testing | axe-core (dev) | 4.9+ | Automated WCAG AA audit in development |
| Testing | Vitest + React Testing Library | 1.x / 16.x | Component unit tests |

### 6.3 Infrastructure & DevOps

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Containerization | Docker + Docker Compose | 26.x | Local dev and production packaging |
| Reverse Proxy | Nginx | 1.25+ | Static file serving, API proxy, HTTPS termination |
| Environment Config | `.env` files | — | Local dev; production secrets via platform env vars |
| Version Control | Git | — | Source code management |
| Package Manager (BE) | pip + `requirements.txt` | — | Python dependency management |
| Package Manager (FE) | npm | 10.x | Node package management |

### 6.4 Environment Variables

```bash
# ── Embedding ──────────────────────────────────────────────────
EMBEDDING_PROVIDER=openai                    # "openai" | "sentence-transformers"
EMBEDDING_MODEL=text-embedding-3-small       # Model name
EMBEDDING_API_KEY=sk-...                     # OpenAI API key (if provider=openai)

# ── LLM ────────────────────────────────────────────────────────
LLM_PROVIDER=openai                          # "openai" | "anthropic"
LLM_MODEL=gpt-4o                             # Model name
LLM_API_KEY=sk-...                           # Provider API key
LLM_TIMEOUT_SECONDS=30                       # First-token timeout
LLM_MAX_RETRIES=3                            # Max retry attempts

# ── Vector Store ───────────────────────────────────────────────
VECTOR_STORE_TYPE=chroma                     # "chroma" | "faiss" | "pinecone"
VECTOR_STORE_PATH=./data/chroma              # Local path (chroma/faiss)
PINECONE_API_KEY=                            # Pinecone key (if type=pinecone)
PINECONE_INDEX_NAME=                         # Pinecone index name

# ── RAG Parameters ─────────────────────────────────────────────
DEFAULT_TOP_K=5
DEFAULT_CHUNK_SIZE=512
DEFAULT_CHUNK_OVERLAP=64
DEFAULT_CONFIDENCE_THRESHOLD=0.30

# ── Session ────────────────────────────────────────────────────
SESSION_TTL_HOURS=24
MAX_DOCUMENTS_PER_SESSION=20
MAX_FILE_SIZE_BYTES=52428800                 # 50 MB
MAX_SESSION_SIZE_BYTES=209715200             # 200 MB

# ── Server ─────────────────────────────────────────────────────
ALLOWED_ORIGINS=http://localhost:3000
UPLOAD_DIR=./data/uploads
```

---
