# Functional Requirements Document (FRD)
## RAG Chatbot

**Version:** 1.0  
**Date:** 2026-05-13  
**Status:** Active  
**Based on PRD:** v1.0 (2026-05-13)

---

## Scope

This document provides detailed functional specifications for every feature in the RAG Chatbot v1. It translates PRD feature descriptions into precise, implementable requirements covering inputs, outputs, validation rules, process flows, error handling, database schema, and REST API contracts. Developers should be able to implement any feature from this document without ambiguity or requiring additional clarification.

The RAG Chatbot enables users to upload documents (PDF, TXT, DOCX), ask natural-language questions, and receive answers generated exclusively from the content of those documents, with inline source citations for verification.

---

## How to Read This Document

- **Feature IDs** follow the PRD (`F0`–`F7`). Chunk files use zero-padded form (`F00`–`F07`).
- **Cross-feature files** are prefixed `Y0`–`Y3`: database schema, API endpoints, error catalog, integrations.
- **Process steps** are numbered; follow them in order.
- **Validation rules** are bulleted; all listed rules must be enforced before proceeding to the next step.
- **Error States** tables use four columns: Scenario | HTTP Status | Error Code | Message.
- **API Surface (this feature)** is a summary only — full request/response schemas are in `Y1-api.md`.
- **Schema Surface (this feature)** is a summary only — full DDL is in `Y0-schema.md`.
- Cross-references use the notation: `see F02 §Process` or `see Y1-api.md §Chat`.

---

## Table of Contents

| Chunk | Feature | Priority | MVP? |
|-------|---------|----------|------|
| [F00](#f00-document-upload--ingestion-pipeline) | Document Upload & Ingestion Pipeline | P0 | ✅ |
| [F01](#f01-chat-interface--question-answering) | Chat Interface & Question Answering | P0 | ✅ |
| [F02](#f02-source-citation--passage-highlighting) | Source Citation & Passage Highlighting | P0 | ✅ |
| [F03](#f03-document-management-panel) | Document Management Panel | P1 | ✅ |
| [F04](#f04-session-scoped-chat-history) | Session-Scoped Chat History | P1 | ✅ |
| [F05](#f05-system-feedback--error-handling) | System Feedback & Error Handling | P1 | ✅ |
| [F06](#f06-responsive--accessible-ui) | Responsive & Accessible UI | P2 | ⚪ |
| [F07](#f07-configurable-rag-pipeline-settings) | Configurable RAG Pipeline Settings | P2 | ⚪ |
| [Y0](#y0-database--vector-store-schema) | Database & Vector Store Schema | — | — |
| [Y1](#y1-rest-api-endpoints) | REST API Endpoints | — | — |
| [Y2](#y2-cross-feature-error-catalog) | Cross-Feature Error Catalog | — | — |
| [Y3](#y3-integration-points) | External Integration Points | — | — |

---

## Cross-Cutting Terminology

| Term | Definition |
|------|-----------|
| **Session** | A browser session identified by a server-assigned `session_id` UUID. Scoped in-memory on the server; destroyed on page refresh. |
| **Document** | A user-uploaded file (PDF, TXT, or DOCX) accepted for ingestion. |
| **Chunk** | A contiguous text segment produced by splitting a document. Stored with metadata (doc_id, chunk_index, page_number). |
| **Embedding** | A dense vector representation of a chunk, produced by an embedding model (OpenAI `text-embedding-3-small` or equivalent). |
| **Vector Store** | The database holding chunk embeddings and metadata (ChromaDB by default; FAISS as alternative). |
| **RAG Pipeline** | The end-to-end process: ingest → chunk → embed → store → retrieve → generate. |
| **Top-k** | The number of most-relevant chunks retrieved per query (configurable; default 5). |
| **LLM** | Large Language Model used for answer generation (OpenAI GPT-4o or Anthropic Claude). |
| **Grounding** | The constraint that LLM answers must derive solely from retrieved chunks, not the model's training data. |
| **Citation** | A reference attached to an answer identifying the source document, chunk excerpt, and page number. |
| **session_id** | A UUID assigned to each browser session; used to namespace vector store collections, chat history, and document lists. |
| **doc_id** | A UUID assigned to each uploaded document within a session. |
| **chunk_id** | A UUID or composite key (`doc_id:chunk_index`) identifying a specific text chunk. |
| **MIME type** | The content-type header or detected magic-byte type of an uploaded file. |
| **Cosine similarity** | The metric used for vector-store nearest-neighbour retrieval. |
| **Processing pipeline stages** | `UPLOADING` → `PARSING` → `CHUNKING` → `EMBEDDING` → `INDEXING` → `READY` (or `FAILED`). |

---

## Non-Functional Constraints (Reference)

| Category | Target |
|----------|--------|
| Response latency (P95) | < 5 seconds time-to-first-token |
| Upload-to-ready time | < 30 seconds for a 50-page PDF |
| Max file size | 20 MB per file |
| Max documents per session | 10 |
| Supported formats | PDF, TXT, DOCX |
| Retrieval hit rate | ≥ 85% relevant chunk in top-k |
| Grounding compliance | 100% — no external knowledge in answers |
| Frontend bundle | < 500 KB gzipped |
| Accessibility | WCAG AA |
| API key storage | Server-side only; never exposed to frontend |
