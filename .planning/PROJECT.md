# RAG Chatbot

## What This Is

A document-based RAG (Retrieval-Augmented Generation) chatbot that allows users to upload documents and ask questions answered strictly from the content of those documents. The frontend is built in React with a beautiful, polished UI, and the backend is in Python (FastAPI) which is the best fit for LLM/vector-search workloads.

## Core Value

Users can upload any document and get accurate, document-grounded answers — the chatbot never answers from outside the provided documents.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can upload one or more documents (PDF, TXT, DOCX)
- [ ] System parses and indexes documents into a vector store
- [ ] User can ask questions in a chat interface
- [ ] System answers questions using only context from uploaded documents
- [ ] System cites the source document/passage for each answer
- [ ] User can manage (view/delete) uploaded documents
- [ ] Chat history is preserved within a session
- [ ] Beautiful, responsive React frontend

### Out of Scope

- Internet/web search — answers must come from uploaded documents only
- User authentication — single-user or session-based for v1
- Multi-user collaboration — single user per session for v1
- Mobile native app — web-first, responsive design covers mobile

## Context

- The core value proposition is strict document grounding: the chatbot must not hallucinate or pull in external knowledge
- Frontend in React (modern, component-based, beautiful design)
- Backend in Python (FastAPI) — ideal for integrating LLM APIs (OpenAI/Anthropic) and vector databases (Chroma, FAISS, Pinecone)
- RAG pipeline: document ingestion → chunking → embedding → vector store → retrieval → LLM answer generation with source citations
- Design should feel premium — clean chat UI, drag-and-drop upload, source highlighting

## Constraints

- **Tech Stack**: React frontend, Python/FastAPI backend — as specified by user
- **Grounding**: Answers must only reference uploaded document content — no external knowledge
- **v1 Scope**: Single-user session, no auth required for v1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python/FastAPI for backend | Best ecosystem for LLM integration, vector DBs, and embedding libraries | — Pending |
| React for frontend | User specified; rich ecosystem for chat UI components | — Pending |
| RAG over fine-tuning | No training data needed; works on any user-provided document immediately | — Pending |

---
*Last updated: 2026-05-13 after initialization*
