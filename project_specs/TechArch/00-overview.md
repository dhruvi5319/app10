# Technical Architecture Document: RAGChatbot

**Project:** RAGChatbot  
**Version:** 1.0  
**Date:** 2026-05-13  
**Status:** Draft  
**Based on:** PRD-RAGChatbot v1.0, FRD-RAGChatbot v1.0

---

## 1. Architectural Overview

### 1.1 Architecture Pattern

RAGChatbot follows a **layered client-server architecture** with an embedded **event-driven pipeline** for document ingestion. The system is organized into four primary layers:

1. **Presentation Layer** — React SPA served as static assets; communicates with the backend exclusively via REST API and Server-Sent Events (SSE).
2. **API Layer** — FastAPI application exposing REST endpoints; handles request validation, session management, and orchestration.
3. **Pipeline Layer** — Asynchronous background workers managing document parsing, chunking, and embedding; the RAG retrieval-and-generation loop for query answering.
4. **Storage Layer** — In-memory session store (Python dict), local file system for uploaded files, and a pluggable vector store (Chroma by default).

The architecture is deliberately **single-server for v1** — all components run in the same Python process. This minimizes deployment complexity while validating the core product value. The vector store abstraction layer enables promotion to a hosted vector database (Pinecone) and a persistent SQL store without architectural rework.

### 1.2 Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API framework | FastAPI (Python) | Native async support; excellent ecosystem for LLM/ML workloads; automatic OpenAPI schema generation |
| Frontend framework | React 18 + TypeScript | User-specified; rich ecosystem for chat UI and drag-and-drop; component-based for citation/message reuse |
| Vector store (default) | ChromaDB (in-process) | Zero-config local deployment; supports metadata filtering for session isolation; easy swap to Pinecone |
| LLM streaming | Server-Sent Events (SSE) | Simpler than WebSockets for unidirectional streaming; native browser `EventSource` support |
| Session storage | In-memory Python dict | Sufficient for v1 single-user sessions; no DB dependency; 24-hour TTL with background cleanup |
| Document ingestion | Async background tasks (FastAPI `BackgroundTasks`) | Non-blocking upload response; real-time status polling model |
| State management (frontend) | Zustand | Lightweight; minimal boilerplate vs. Redux; suitable for session/document/message state |

### 1.3 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Browser (React SPA)                                 │
│                                                                               │
│  ┌────────────────────┐   ┌────────────────────┐   ┌─────────────────────┐  │
│  │  Document Library  │   │    Chat View        │   │   Upload Zone       │  │
│  │  (Sidebar Panel)   │   │  (Message Bubbles   │   │  (Drag & Drop)      │  │
│  │                    │   │   + Citations)      │   │                     │  │
│  └────────────────────┘   └────────────────────┘   └─────────────────────┘  │
│           │                        │  SSE stream               │             │
│           └────────────────────────┼───────────────────────────┘             │
│                         REST API / SSE                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │         FastAPI Application          │
                    │                                      │
                    │  ┌──────────────────────────────┐   │
                    │  │       API Router Layer        │   │
                    │  │  /api/documents  /api/chat    │   │
                    │  │  /api/session    /api/health  │   │
                    │  └──────────────┬───────────────┘   │
                    │                 │                    │
                    │  ┌──────────────▼───────────────┐   │
                    │  │      Session Manager          │   │
                    │  │  (In-memory dict, TTL 24h)    │   │
                    │  └──────────────┬───────────────┘   │
                    │                 │                    │
                    │  ┌──────────────▼───────────────┐   │
                    │  │    RAG Pipeline Orchestrator  │   │
                    │  │                               │   │
                    │  │  ┌──────────┐ ┌───────────┐  │   │
                    │  │  │ Ingestion│ │  Query    │  │   │
                    │  │  │ Pipeline │ │ Pipeline  │  │   │
                    │  │  └────┬─────┘ └─────┬─────┘  │   │
                    │  └───────┼─────────────┼────────┘   │
                    │          │             │             │
                    └──────────┼─────────────┼────────────┘
                               │             │
          ┌────────────────────┼─────────────┼────────────────────────┐
          │                    │  Storage Layer                        │
          │   ┌────────────────▼──┐       ┌──▼──────────────────────┐ │
          │   │   In-Memory Store │       │    Vector Store          │ │
          │   │  (Sessions,       │       │  (ChromaDB / FAISS /     │ │
          │   │   Documents,      │       │   Pinecone)              │ │
          │   │   Messages)       │       │                          │ │
          │   └───────────────────┘       └──────────────────────────┘ │
          │                                                              │
          │   ┌──────────────────────────────────────────────────────┐  │
          │   │              Local File System                        │  │
          │   │         ./data/uploads/  (temp files)                │  │
          │   │         ./data/chroma/   (vector index)              │  │
          │   └──────────────────────────────────────────────────────┘  │
          └──────────────────────────────────────────────────────────────┘
                               │             │
          ┌────────────────────┼─────────────┼────────────────────────┐
          │                    │  External APIs                        │
          │   ┌────────────────▼──┐       ┌──▼──────────────────────┐ │
          │   │   Embedding API   │       │     LLM API              │ │
          │   │  OpenAI           │       │  OpenAI GPT-4o /         │ │
          │   │  text-embedding   │       │  Anthropic Claude        │ │
          │   │  -3-small         │       │  (streaming)             │ │
          │   └───────────────────┘       └──────────────────────────┘ │
          └──────────────────────────────────────────────────────────────┘
```

### 1.4 RAG Pipeline Flow

```
Document Upload                    Query Answering
─────────────                    ────────────────
User uploads file                User submits question
       │                                │
       ▼                                ▼
Format validation              Validate query & session
       │                                │
       ▼                                ▼
Text extraction                  Embed query via
(PyMuPDF/python-docx/TXT)       Embedding API
       │                                │
       ▼                                ▼
Text chunking                   Top-k vector search
(512 tokens, 64 overlap)        (cosine similarity)
       │                                │
       ▼                                ▼
Batch embedding via             Confidence check
Embedding API                   (threshold 0.30)
       │                         low │    high │
       ▼                             │         ▼
Vector store indexing          Fallback    Assemble grounded
(with metadata)               response    prompt + chunks
       │                                      │
       ▼                                      ▼
Status → "ready"               LLM streaming call (SSE)
                                              │
                                              ▼
                                       Stream tokens to
                                       frontend via SSE
                                              │
                                              ▼
                                    Attach citations to
                                    "done" event
```

### 1.5 Deployment Topology (v1)

```
┌──────────────────────────────────────────────────┐
│              Single Server / Container            │
│                                                   │
│  Port 3000: React dev server (or Nginx for prod)  │
│  Port 8000: FastAPI (uvicorn)                     │
│                                                   │
│  ./data/uploads/   — temp uploaded files          │
│  ./data/chroma/    — vector index persistence     │
│                                                   │
│  Process memory    — session/document/message     │
└──────────────────────────────────────────────────┘
           │                      │
    OPENAI_API_KEY         ANTHROPIC_API_KEY
    (embeddings + LLM)     (LLM alternative)
```

**v1 Deployment options:**
- **Local development:** `uvicorn main:app --reload` (backend) + `npm run dev` (frontend)
- **Single container:** Docker Compose with `backend` and `frontend` services + shared volume for `./data`
- **Cloud (future):** Replace in-memory store with Redis; replace ChromaDB with Pinecone; add PostgreSQL for persistence

---
