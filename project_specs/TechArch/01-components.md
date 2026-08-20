## 2. Component Architecture

### 2.1 Backend Components

```
backend/
├── main.py                    # FastAPI app factory; lifespan handler; CORS config
├── config.py                  # AppConfig (pydantic-settings); env var loading
├── dependencies.py            # FastAPI dependency injection (session, config)
│
├── routers/
│   ├── documents.py           # /api/documents routes (upload, list, status, delete)
│   ├── chat.py                # /api/chat routes (query, history, clear, export)
│   ├── session.py             # /api/session routes (reset)
│   ├── settings.py            # /api/settings routes (GET, PUT) — F9
│   └── health.py              # /api/health route
│
├── services/
│   ├── session_service.py     # Session CRUD; TTL management; in-memory store
│   ├── document_service.py    # Document metadata CRUD; status transitions
│   ├── ingestion_service.py   # Async ingestion pipeline orchestrator
│   ├── query_service.py       # RAG query pipeline; SSE streaming
│   ├── embedding_service.py   # Embedding API abstraction (OpenAI / sentence-transformers)
│   ├── llm_service.py         # LLM API abstraction (OpenAI / Anthropic)
│   └── export_service.py      # Transcript export formatting (text / markdown)
│
├── pipeline/
│   ├── parser.py              # Document text extraction (PDF, DOCX, TXT)
│   ├── chunker.py             # Text chunking (fixed-size with overlap)
│   └── retriever.py           # Vector store query + confidence scoring
│
├── vectorstore/
│   ├── base.py                # Abstract VectorStore interface
│   ├── chroma_store.py        # ChromaDB implementation
│   ├── faiss_store.py         # FAISS implementation
│   └── pinecone_store.py      # Pinecone implementation
│
├── models/
│   ├── session.py             # Session, Document, Message Pydantic models
│   ├── requests.py            # API request body schemas
│   └── responses.py           # API response schemas
│
└── utils/
    ├── session_cookie.py      # Cookie read/write helpers
    ├── retry.py               # Exponential backoff retry decorator
    └── encryption.py          # Fernet encrypt/decrypt helpers (F9); reads SECRET_KEY env var
```

**Component Responsibilities:**

| Component | Responsibility |
|-----------|---------------|
| `session_service.py` | Create, read, update, delete sessions; enforce document/size limits; 24h TTL cleanup |
| `document_service.py` | CRUD for document metadata; status transitions (uploading → indexing → ready/error) |
| `ingestion_service.py` | Orchestrate: parse → chunk → embed → index; manages BackgroundTask lifecycle |
| `query_service.py` | Embed query → retrieve chunks → confidence check → assemble prompt → stream LLM → yield SSE events |
| `embedding_service.py` | Unified embedding interface; handles batching, retries, provider switching |
| `llm_service.py` | Unified LLM interface; handles streaming, retries, timeout enforcement |
| `parser.py` | Format-aware text extraction; returns (text, page_offsets) tuples |
| `chunker.py` | Token-aware text splitting with configurable size/overlap |
| `retriever.py` | Vector store similarity search with session/document metadata filters |
| `base.py` (vectorstore) | Abstract interface: `upsert`, `query`, `delete_by_filter`, `delete_collection` |
| `settings.py` (router) | `GET /api/settings` returns masked key + provider/model; `PUT /api/settings` encrypts and persists key — F9 |
| `encryption.py` (util) | `encrypt(plaintext) → token` / `decrypt(token) → plaintext` using Fernet; key sourced from `SECRET_KEY` env var — F9 |

### 2.2 Frontend Components

```
frontend/src/
├── main.tsx                   # React entry point
├── App.tsx                    # Root component; session init; layout routing
│
├── components/
│   ├── layout/
│   │   ├── AppLayout.tsx      # Split-panel root: sidebar + main area
│   │   └── Sidebar.tsx        # Collapsible document library sidebar wrapper
│   │
│   ├── documents/
│   │   ├── DocumentLibrary.tsx    # Document list container; polling logic
│   │   ├── DocumentCard.tsx       # Single document: name, status badge, delete button
│   │   ├── UploadZone.tsx         # Drag-and-drop + file picker; validation feedback
│   │   └── StatusBadge.tsx        # Colored badge: uploading/indexing/ready/error
│   │
│   ├── chat/
│   │   ├── ChatView.tsx           # Scrollable message transcript; auto-scroll logic
│   │   ├── MessageBubble.tsx      # User or assistant message bubble with timestamp
│   │   ├── CitationChip.tsx       # Compact citation pill below assistant answers
│   │   ├── CitationPanel.tsx      # Expanded panel showing raw chunk_text
│   │   ├── ChatInput.tsx          # Text area + send button; Enter/Shift+Enter handling
│   │   └── LoadingIndicator.tsx   # Animated "thinking" dots during LLM generation
│   │
│   ├── settings/
│   │   └── SettingsPanel.tsx      # LLM settings modal: provider, model, API key input — F9
│   │
│   └── shared/
│       ├── ConfirmModal.tsx       # Reusable confirmation dialog (delete, clear, reset)
│       ├── EmptyState.tsx         # Onboarding / cleared state UI
│       ├── ErrorBanner.tsx        # Inline error with optional Retry button
│       └── SkeletonLoader.tsx     # Animated placeholder for loading states
│
├── hooks/
│   ├── useDocuments.ts        # Document list fetch + polling; delete action
│   ├── useUpload.ts           # File upload with progress; status tracking
│   ├── useChat.ts             # Chat history fetch; SSE stream management
│   ├── useSession.ts          # Session init; reset action
│   └── useSettings.ts         # LLM settings fetch and update; masked key state — F9
│
├── stores/
│   └── appStore.ts            # Zustand store: session, documents, messages, uiState
│
├── api/
│   ├── client.ts              # Axios instance with base URL and cookie config
│   ├── documents.ts           # Document API calls (upload, list, status, delete)
│   ├── chat.ts                # Chat API calls (query SSE, history, clear, export)
│   ├── session.ts             # Session API calls (reset)
│   ├── settings.ts            # Settings API calls (GET /api/settings, PUT /api/settings) — F9
│   └── health.ts              # Health check
│
└── types/
    └── index.ts               # TypeScript interfaces for all domain objects
```

**Key Frontend Patterns:**

| Pattern | Implementation |
|---------|---------------|
| Session cookie | Axios `withCredentials: true`; cookie set by backend; auto-created on first request |
| SSE streaming | `EventSource` API on `POST /api/chat/query`; custom hook handles token accumulation |
| Status polling | `useDocuments` hook polls `GET /api/documents` every 3s while any doc is `uploading`/`indexing` |
| Optimistic updates | User message appended to chat immediately on submit before backend response |
| Reduced motion | CSS `@media (prefers-reduced-motion: reduce)` disables all transitions/animations |
| ARIA live regions | `aria-live="polite"` on chat container; status badge text included for screen readers |

---
