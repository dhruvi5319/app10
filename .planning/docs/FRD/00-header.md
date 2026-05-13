# Functional Requirements Document (FRD)
## RAG Chatbot

**Version:** 1.0  
**Date:** 2026-05-13  
**Status:** Active  
**Project Acronym:** RAG  
**Based on PRD:** PRD.md v1.0

---

## Scope

This document defines the detailed functional requirements for the RAG Chatbot application. It specifies the exact behavior, inputs, outputs, validation rules, and error handling for every feature identified in the PRD. Developers should be able to implement any feature end-to-end using only this document and the referenced cross-feature specifications (schema, API, error catalog, integrations). Where a section says *"see Y1-api.md"* or *"see Y0-schema.md"*, consult those chunk files for the full specification.

This FRD covers **v1 scope only**. All items marked Out of Scope in the PRD are explicitly excluded.

---

## How to Read This Document

- **Feature IDs** follow PRD numbering: `F00`–`F07`. Zero-padded to ensure correct sort order.
- **Cross-feature chunks** are prefixed `Y`: `Y0-schema`, `Y1-api`, `Y2-errors`, `Y3-integrations`.
- **Process steps** are numbered (1. 2. 3.) and represent the sequential execution path, including both happy-path and branch steps.
- **Validation rules** are enforced before business logic executes. Any rule violation returns the associated error state immediately.
- **Error States** tables use columns: `Scenario | HTTP Status | Error Code | User Message`.
- **HTTP Status** codes are used by the backend REST API. Frontend handles them and maps to user-visible messages per `Y2-errors.md`.
- **IDs in error codes** use SCREAMING_SNAKE_CASE (e.g., `FILE_TOO_LARGE`).

---

## Shared Terminology

| Term | Definition |
|------|-----------|
| **Session** | A single browser visit identified by a server-side session ID. Ends on page refresh. All state (chat history, uploaded docs) is scoped to the session. |
| **Document** | A user-uploaded file (PDF, TXT, or DOCX) that has been successfully parsed, chunked, embedded, and indexed into the vector store. |
| **Chunk** | A fixed-size, overlapping text segment produced by splitting a document. The atomic unit of retrieval. |
| **Embedding** | A high-dimensional float vector representation of a chunk, produced by the embedding model. Stored in the vector store alongside the chunk text and metadata. |
| **Vector Store** | The local database (ChromaDB or FAISS) holding all embeddings and their associated chunk metadata. |
| **Retrieval** | The process of querying the vector store with a question embedding to find the top-k most semantically similar chunks. |
| **LLM** | The Large Language Model (OpenAI GPT-4o or Anthropic Claude) used for answer generation. |
| **Context Window** | The assembled text passed to the LLM, composed of the retrieved chunks plus the user's question. |
| **Grounding** | The strict constraint that LLM answers must be derived only from retrieved chunks, not from the model's parametric knowledge. |
| **Citation** | A reference attached to an LLM answer identifying the source document, chunk index, page (if available), and verbatim excerpt. |
| **Top-K** | The number of chunks retrieved from the vector store per query. Configurable; default 5. |
| **Chunk Size** | Maximum token length of a single chunk. Configurable; default 500 tokens. |
| **Chunk Overlap** | Number of tokens shared between adjacent chunks to preserve sentence context. Configurable; default 50 tokens. |
| **Session ID** | A UUID generated server-side at session initialization and stored in a browser cookie or returned in the response header. |
| **Temperature** | LLM sampling parameter (0.0–1.0) controlling answer randomness. Lower = more deterministic. Default 0.2. |
| **MIME Type** | HTTP content type identifying the file format (e.g., `application/pdf`, `text/plain`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`). |

---

## Table of Contents

| Chunk | Feature |
|-------|---------|
| [F00-document-upload.md](F00-document-upload.md) | F00: Document Upload & Ingestion Pipeline |
| [F01-chat-qa.md](F01-chat-qa.md) | F01: Chat Interface & Question Answering |
| [F02-source-citations.md](F02-source-citations.md) | F02: Source Citation & Passage Highlighting |
| [F03-document-management.md](F03-document-management.md) | F03: Document Management Panel |
| [F04-chat-history.md](F04-chat-history.md) | F04: Session-Scoped Chat History |
| [F05-error-handling.md](F05-error-handling.md) | F05: System Feedback & Error Handling |
| [F06-responsive-ui.md](F06-responsive-ui.md) | F06: Responsive & Accessible UI |
| [F07-rag-settings.md](F07-rag-settings.md) | F07: Configurable RAG Pipeline Settings |
| [Y0-schema.md](Y0-schema.md) | Database / Data Schema |
| [Y1-api.md](Y1-api.md) | REST API Endpoint Catalog |
| [Y2-errors.md](Y2-errors.md) | Cross-Feature Error Catalog |
| [Y3-integrations.md](Y3-integrations.md) | External Integration Points |

---
