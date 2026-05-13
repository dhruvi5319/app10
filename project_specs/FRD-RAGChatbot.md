# Functional Requirements Document: RAG Chatbot

**Project:** RAGChatbot  
**Acronym:** RAGChatbot  
**Version:** 1.0  
**Date:** 2026-05-13  
**Status:** Draft  
**Based on:** PRD-RAGChatbot.md v1.0

---

## Scope

This FRD specifies the detailed functional behavior of every feature in the RAGChatbot v1 product. It is the authoritative implementation reference: each feature section defines inputs, outputs, validation rules, error states, and the API/schema surfaces involved. Developers should implement exactly what is stated here without inferring undocumented behavior.

The FRD covers all nine PRD features (F0–F8) including three MVP-critical P0 features, three MVP-completing P1 features, two post-MVP P2 features, and one P3 backlog convenience feature.

---

## Conventions

- **Feature IDs** follow the PRD numbering: `F0` through `F8`. Chunk filenames use zero-padded format (`F00`, `F01`, …) for lexicographic sort order.
- **Required / Optional** labels indicate whether a field must be present for a request to succeed.
- **HTTP verbs** are uppercase; paths use `:param` notation for path parameters.
- **Error codes** are `SCREAMING_SNAKE_CASE` strings returned in JSON error bodies.
- **Status values** for documents are: `uploading` → `indexing` → `ready` | `error`.
- **Chunk** refers to a text segment produced during document ingestion (not a file chunk or FRD file chunk).
- Cross-references use the form `see F01 §Process` or `see Y0-schema.md §documents`.
- Full DDL lives in `Y0-schema.md`; full API specs live in `Y1-api.md`; the error catalog is in `Y2-errors.md`; integrations in `Y3-integrations.md`.

---

## Master Table of Contents

| Chunk File | Content |
|---|---|
| `00-header.md` | This file — title, conventions, TOC, shared terminology |
| `F00-document-upload-ingestion.md` | F0: Document Upload & Ingestion |
| `F01-rag-question-answering.md` | F1: RAG-Powered Question Answering |
| `F02-source-citations.md` | F2: Source Citations |
| `F03-document-library-management.md` | F3: Document Library Management |
| `F04-session-chat-history.md` | F4: Session-Scoped Chat History |
| `F05-premium-responsive-ui.md` | F5: Premium Responsive UI |
| `F06-multi-document-retrieval.md` | F6: Multi-Document Context Retrieval |
| `F07-answer-confidence-feedback.md` | F7: Answer Confidence & Relevance Feedback |
| `F08-export-copy-utilities.md` | F8: Export & Copy Utilities |
| `Y0-schema.md` | Consolidated Database / Storage Schema (DDL) |
| `Y1-api.md` | Consolidated REST API Endpoint Catalog |
| `Y2-errors.md` | Cross-Feature Error Catalog |
| `Y3-integrations.md` | External Integration Points |

---

## Cross-Cutting Terminology

| Term | Definition |
|---|---|
| **Session** | A browser session identified by a server-issued session ID cookie (`rag_session_id`). Scoped to a single user; cleared on explicit reset or server restart (v1). |
| **Document** | A user-uploaded file (PDF, TXT, or DOCX) stored and tracked by the backend, associated with a session. |
| **Chunk** | A fixed-size or semantically-bounded text segment produced by splitting a document during ingestion. The atomic unit stored in the vector index. |
| **Embedding** | A high-dimensional numeric vector representation of a chunk's text, produced by the embedding model and stored in the vector store. |
| **Vector Store** | The database of embeddings (Chroma or FAISS locally; Pinecone cloud) enabling semantic similarity search. |
| **RAG Pipeline** | The end-to-end flow: document ingestion → chunking → embedding → storage → query embedding → retrieval → LLM generation → answer with citations. |
| **LLM** | Large Language Model (OpenAI GPT-4 or Anthropic Claude) used for answer generation. |
| **Retrieval** | The step where a query embedding is compared against all chunk embeddings to return the top-k most similar chunks. |
| **Grounding** | The constraint that LLM answers must be derived only from retrieved document chunks, never from model training knowledge. |
| **Citation** | A reference attached to an answer identifying the source document and chunk/passage used in generating that answer. |
| **Ingestion Status** | The current state of a document in the pipeline: `uploading`, `indexing`, `ready`, or `error`. |
| **Top-k** | The number of most-similar chunks returned by retrieval; default k=5, configurable. |
| **Confidence Score** | A numeric value (0.0–1.0) derived from retrieval similarity scores indicating how relevant the retrieved context is to the query. |
| **Session Index** | The combined vector store contents for all documents within a given session. |
| **Transcript** | The full ordered list of user messages and assistant answers within a session. |

---

## Feature Priority Summary

| ID | Feature | Priority | MVP? |
|---|---|---|---|
| F0 | Document Upload & Ingestion | P0 | ✅ Yes |
| F1 | RAG-Powered Question Answering | P0 | ✅ Yes |
| F2 | Source Citations | P0 | ✅ Yes |
| F3 | Document Library Management | P1 | ✅ Yes |
| F4 | Session-Scoped Chat History | P1 | ✅ Yes |
| F5 | Premium Responsive UI | P1 | ✅ Yes |
| F6 | Multi-Document Context Retrieval | P2 | 🔄 Post-MVP |
| F7 | Answer Confidence & Relevance Feedback | P2 | 🔄 Post-MVP |
| F8 | Export & Copy Utilities | P3 | 🔄 Post-MVP |

---

## Non-Functional Requirements Summary

| Category | Requirement | Target |
|---|---|---|
| Performance | Answer generation latency (P95) | < 8 seconds end-to-end |
| Performance | 50-page PDF ingestion time | < 30 seconds |
| Performance | Vector search retrieval latency | < 500ms |
| Reliability | API uptime | 99.5% staging |
| Accuracy | Grounding compliance | 0% answers from non-uploaded content |
| Scalability | Documents per session (v1) | Up to 20 documents / ~2M tokens |
| Security | Document data isolation | Session documents not cross-accessible |
| Accessibility | Frontend compliance | WCAG 2.1 AA minimum |
| Browser Support | Frontend compatibility | Latest 2 versions Chrome, Firefox, Safari, Edge |
| Maintainability | Backend code coverage | > 70% unit test coverage on RAG pipeline |

---

*FRD-RAGChatbot v1.0 — generated 2026-05-13*
---

## F00: Document Upload & Ingestion

**Priority:** P0 — MVP Critical  
**PRD Reference:** §5 F0

**Description:** Users upload one or more documents (PDF, TXT, DOCX) via a drag-and-drop zone or file picker. The backend receives each file, validates it, extracts text using a format-appropriate parser, splits the text into overlapping chunks, generates embeddings for each chunk, and stores the embeddings in the session's vector index. The entire ingestion pipeline runs asynchronously so the UI can show real-time progress without blocking. No chatbot functionality is available until at least one document has reached `ready` status.

---

### Terminology

- **File Picker:** The native `<input type="file">` fallback for users who cannot drag-and-drop.
- **Drag-and-Drop Zone:** The highlighted UI area that accepts files dragged from the OS file manager.
- **Text Extraction:** Parsing a binary document format (PDF, DOCX) into plain Unicode text.
- **Chunking:** Splitting extracted text into overlapping fixed-size segments for embedding.
- **Chunk Size:** Number of tokens per chunk; default 512 tokens.
- **Chunk Overlap:** Number of tokens shared between adjacent chunks; default 64 tokens.
- **Document ID:** A UUID assigned by the backend upon upload acceptance; used to track status and reference citations.
- **Ingestion Pipeline:** The ordered sequence: receive → validate → parse → chunk → embed → index → mark ready.

---

### Sub-Features

- Drag-and-drop file upload area with visual drag-over feedback
- File picker fallback (`<input type="file" multiple accept=".pdf,.txt,.docx">`)
- Multi-file upload support (up to 20 documents per session)
- Format validation (PDF, TXT, DOCX only)
- File size validation (max 50MB per file; max 200MB total session)
- Asynchronous text extraction (PyMuPDF for PDF, python-docx for DOCX, plain decode for TXT)
- Configurable chunking with size and overlap parameters
- Embedding generation via configured embedding model
- Vector store indexing with chunk metadata (document_id, chunk_index, page_number where applicable)
- Real-time ingestion status updates (polling or SSE)
- Upload progress indicator per file
- Error reporting per file (does not halt other files in a batch)

---

### Process

1. User drops file(s) onto the drop zone or selects via file picker.
2. Frontend validates MIME type and file extension client-side; rejects invalid types immediately with an inline error.
3. Frontend displays a per-file upload card with filename, size, and a `uploading` spinner.
4. Frontend sends `POST /api/documents/upload` with the file as `multipart/form-data`, including the session cookie.
5. Backend validates: file extension, MIME type, file size (≤ 50MB), session total size (≤ 200MB), session document count (≤ 20). Returns 400 on any violation.
6. Backend assigns a UUID `document_id`, stores document metadata in the session store with status `uploading`, and returns `{ document_id, status: "uploading" }` immediately (202 Accepted).
7. Backend saves the raw file bytes to temporary storage.
8. Backend launches an async background task for ingestion:
   a. **Parse:** Extracts text using format parser. On parse failure, sets status to `error` with `parse_error` reason.
   b. **Chunk:** Splits text into segments of `chunk_size` tokens with `chunk_overlap` overlap. Skips empty chunks.
   c. **Embed:** Calls the embedding model API for each chunk batch. On API failure, retries up to 3 times with exponential backoff; on final failure, sets status to `error` with `embed_error` reason.
   d. **Index:** Inserts all chunk embeddings into the vector store with metadata `{ document_id, chunk_index, text, page_number }`. On index failure, sets status to `error` with `index_error` reason.
   e. Sets document status to `ready` and records `chunk_count` and `indexed_at` timestamp.
9. Frontend polls `GET /api/documents/{document_id}/status` every 2 seconds until status is `ready` or `error`.
10. On `ready`: frontend updates the document card to a green checkmark and enables the chat input.
11. On `error`: frontend shows an error badge with the failure reason and a retry option.

---

### Inputs

- `file` (binary, required): The document file bytes, sent as `multipart/form-data` field named `file`.
- `session_id` (string, required): Session identifier sent as HTTP cookie `rag_session_id`. Auto-created if absent.
- `chunk_size` (integer, optional): Override default chunk size in tokens. Range: 128–2048. Default: 512.
- `chunk_overlap` (integer, optional): Override default chunk overlap in tokens. Must be < `chunk_size`. Default: 64.

---

### Outputs

**Immediate response (202 Accepted):**
```json
{
  "document_id": "uuid-v4",
  "filename": "report.pdf",
  "status": "uploading",
  "size_bytes": 1048576,
  "created_at": "2026-05-13T10:00:00Z"
}
```

**Status poll response:**
```json
{
  "document_id": "uuid-v4",
  "filename": "report.pdf",
  "status": "ready",
  "chunk_count": 143,
  "indexed_at": "2026-05-13T10:00:28Z",
  "error_reason": null
}
```

**Error status response:**
```json
{
  "document_id": "uuid-v4",
  "filename": "corrupt.pdf",
  "status": "error",
  "chunk_count": 0,
  "indexed_at": null,
  "error_reason": "parse_error"
}
```

---

### Validation Rules

- File extension must be one of: `.pdf`, `.txt`, `.docx` (case-insensitive).
- MIME type must match extension: `application/pdf`, `text/plain`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`.
- File size must not exceed 50MB (52,428,800 bytes).
- Session cumulative upload size must not exceed 200MB (209,715,200 bytes).
- Session document count must not exceed 20.
- `chunk_size` if provided must be integer in range [128, 2048].
- `chunk_overlap` if provided must be integer in range [0, chunk_size - 1].
- Empty files (0 bytes) are rejected.
- Files producing zero extractable text characters are rejected with reason `empty_document`.
- Scanned PDFs (image-only, no embedded text layer) produce zero text and are rejected with reason `no_text_layer`. *(OCR is out of scope for v1.)*

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Unsupported file type | 400 | INVALID_FILE_TYPE | "Supported formats: PDF, TXT, DOCX" |
| File exceeds 50MB | 400 | FILE_TOO_LARGE | "File must be under 50MB" |
| Session storage limit exceeded | 400 | SESSION_STORAGE_LIMIT | "Session storage limit of 200MB reached" |
| Session document count limit | 400 | SESSION_DOCUMENT_LIMIT | "Maximum 20 documents per session" |
| Empty file | 400 | EMPTY_FILE | "Uploaded file contains no data" |
| Parse failure (corrupt/unreadable) | 202→async error | PARSE_ERROR | "Could not extract text from this file" |
| No text layer (scanned PDF) | 202→async error | NO_TEXT_LAYER | "PDF appears to be image-only; OCR not supported in v1" |
| Embedding API failure after retries | 202→async error | EMBED_ERROR | "Embedding service unavailable; please retry" |
| Vector index failure | 202→async error | INDEX_ERROR | "Failed to index document; please retry" |
| Session not found / expired | 404 | SESSION_NOT_FOUND | "Session not found or expired" |
| Document ID not found | 404 | DOCUMENT_NOT_FOUND | "Document not found" |

---

### API Surface (this feature)

See `Y1-api.md` §Documents for full request/response schemas.

| Method | Path | Summary |
|---|---|---|
| `POST` | `/api/documents/upload` | Upload a document file; returns document_id and initial status |
| `GET` | `/api/documents/{document_id}/status` | Poll ingestion status for a specific document |
| `GET` | `/api/documents` | List all documents in the session (see F03) |

---

### Schema Surface (this feature)

Uses session-scoped in-memory store records and vector store entries. See `Y0-schema.md` §Documents and §Chunks.

Key metadata tracked per document:
- `document_id` (UUID)
- `session_id` (string)
- `filename` (string)
- `file_extension` (string)
- `size_bytes` (integer)
- `status` (enum: uploading | indexing | ready | error)
- `chunk_count` (integer)
- `error_reason` (string | null)
- `created_at` (ISO 8601 datetime)
- `indexed_at` (ISO 8601 datetime | null)
---

## F01: RAG-Powered Question Answering

**Priority:** P0 — MVP Critical  
**PRD Reference:** §5 F1

**Description:** Users type natural language questions in the chat input and receive answers generated exclusively from the content of their uploaded documents. The backend embeds the query, performs a top-k semantic search against the session's vector index, assembles a grounded prompt with the retrieved chunks, sends it to the LLM with a strict "answer only from the provided context" instruction, and streams the generated response back to the frontend. If no sufficiently relevant context is found, the system returns a standardized "not found in documents" response rather than attempting an unsupported answer.

---

### Terminology

- **Query Embedding:** The vector representation of the user's question, generated by the same embedding model used during ingestion.
- **Top-k Retrieval:** Selection of the k most semantically similar chunks to the query from the session index. Default k=5.
- **Grounded Prompt:** The LLM prompt that includes retrieved chunk text as the sole knowledge source, with an explicit instruction forbidding answers outside that context.
- **Streaming:** Server-Sent Events (SSE) or chunked HTTP transfer delivering the LLM's token output progressively to the frontend as it is generated.
- **Similarity Score:** A cosine similarity value (0.0–1.0) returned per retrieved chunk indicating relevance to the query.
- **Confidence Threshold:** Minimum acceptable similarity score for any retrieved chunk to be considered valid context. Default: 0.30.
- **Fallback Response:** The standardized message returned when no chunk meets the confidence threshold: *"The uploaded documents do not contain information about this topic."*

---

### Sub-Features

- Chat input field with send button
- Enter-key keyboard shortcut to submit query
- Query length validation (min 1 char, max 2000 chars)
- Requirement check: at least one document must be in `ready` state before querying is enabled
- Query embedding generation
- Top-k similarity search over session vector index
- Confidence threshold check with fallback response
- Grounded LLM prompt construction
- Streaming answer delivery via SSE
- Thinking/loading indicator while awaiting LLM response
- Answer rendering in chat bubble (markdown-safe)
- Source citations attached to each answer (see F02)
- Error state display if LLM or retrieval fails

---

### Process

1. User types a question in the chat input field and presses Enter or clicks the Send button.
2. Frontend validates: input is non-empty, length ≤ 2000 characters, at least one document is `ready`. If validation fails, shows inline error; does not submit.
3. Frontend optimistically appends the user message to the chat transcript with a timestamp.
4. Frontend sends `POST /api/chat/query` with `{ query, session_id (via cookie) }` and opens an SSE stream on the response.
5. Frontend displays a loading/thinking indicator bubble in the assistant position while awaiting the first token.
6. Backend receives query:
   a. **Embed Query:** Calls embedding model with the user's query text. On failure, returns 503.
   b. **Retrieve:** Performs top-k cosine similarity search in the session vector index. Returns up to k=5 chunks with similarity scores.
   c. **Confidence Check:** If the highest similarity score < 0.30, skips LLM call and returns the fallback response as a complete (non-streaming) response with `confidence: "low"` flag.
   d. **Prompt Assembly:** Builds the grounded prompt:
      - System instruction: *"You are a document assistant. Answer ONLY using the provided document excerpts below. If the answer cannot be found in the excerpts, say so explicitly. Do not use any outside knowledge."*
      - Document excerpts: Each retrieved chunk labeled with its source document name and chunk index.
      - User question appended at the end.
   e. **LLM Call:** Sends prompt to configured LLM with streaming enabled. Streams tokens back to the client via SSE as `data: {"token": "..."}` events.
   f. **Completion Event:** On LLM finish, sends SSE event `data: {"done": true, "citations": [...], "confidence": "high"|"low"}`.
7. Frontend renders tokens progressively in the assistant bubble as they arrive.
8. On the `done` event, frontend appends citation chips below the answer bubble (see F02) and removes the loading indicator.
9. Frontend scrolls the chat view to the latest message.
10. On stream error or connection drop, frontend shows an error message in the assistant bubble with a retry prompt.

---

### Inputs

- `query` (string, required): The user's natural language question. Min length: 1 character. Max length: 2000 characters.
- `session_id` (string, required): Session identifier via HTTP cookie `rag_session_id`.
- `k` (integer, optional): Override top-k retrieval count. Range: 1–20. Default: 5.
- `confidence_threshold` (float, optional): Override minimum similarity score. Range: 0.0–1.0. Default: 0.30.

---

### Outputs

**SSE stream events (during generation):**
```
data: {"token": "The"}
data: {"token": " contract"}
data: {"token": " expires"}
...
data: {"done": true, "message_id": "uuid-v4", "citations": [{"document_id": "uuid", "document_name": "contract.pdf", "chunk_index": 7, "chunk_text": "...", "similarity": 0.87}], "confidence": "high"}
```

**Fallback response (low confidence, non-streaming):**
```json
{
  "message_id": "uuid-v4",
  "answer": "The uploaded documents do not contain information about this topic.",
  "citations": [],
  "confidence": "low",
  "created_at": "2026-05-13T10:05:00Z"
}
```

**Chat message object (stored in session history after completion):**
```json
{
  "message_id": "uuid-v4",
  "role": "assistant",
  "content": "The contract expires on December 31, 2026.",
  "citations": [
    {
      "document_id": "uuid",
      "document_name": "contract.pdf",
      "chunk_index": 7,
      "chunk_text": "...expires on December 31, 2026...",
      "page_number": 4,
      "similarity": 0.87
    }
  ],
  "confidence": "high",
  "created_at": "2026-05-13T10:05:00Z"
}
```

---

### Validation Rules

- `query` must be non-empty after trimming whitespace.
- `query` length must not exceed 2000 characters.
- Session must have at least one document with status `ready`; otherwise returns 422 with `NO_READY_DOCUMENTS`.
- `k` if provided must be integer in [1, 20].
- `confidence_threshold` if provided must be float in [0.0, 1.0].
- Query may not be submitted while a previous query for the same session is still streaming (returns 429 `QUERY_IN_PROGRESS`).

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Empty query | 400 | EMPTY_QUERY | "Please enter a question" |
| Query too long | 400 | QUERY_TOO_LONG | "Question must be under 2000 characters" |
| No ready documents | 422 | NO_READY_DOCUMENTS | "Upload and index at least one document before asking questions" |
| Query already in progress | 429 | QUERY_IN_PROGRESS | "A question is already being processed for this session" |
| Query embedding failure | 503 | EMBED_ERROR | "Embedding service unavailable; please try again" |
| LLM API failure | 503 | LLM_UNAVAILABLE | "Answer generation service unavailable; please try again" |
| LLM timeout (> 30s) | 504 | LLM_TIMEOUT | "Answer generation timed out; please try again" |
| Vector search failure | 503 | RETRIEVAL_ERROR | "Document search service unavailable; please try again" |
| Session not found | 404 | SESSION_NOT_FOUND | "Session not found or expired" |

---

### API Surface (this feature)

See `Y1-api.md` §Chat for full request/response schemas.

| Method | Path | Summary |
|---|---|---|
| `POST` | `/api/chat/query` | Submit a question; returns SSE stream of answer tokens + final citations |
| `GET` | `/api/chat/history` | Retrieve session chat history (see F04) |

---

### Schema Surface (this feature)

Uses session-scoped message store and vector index. See `Y0-schema.md` §Messages and §VectorIndex.

Key metadata tracked per message:
- `message_id` (UUID)
- `session_id` (string)
- `role` (enum: user | assistant)
- `content` (string — full text)
- `citations` (JSON array of citation objects)
- `confidence` (enum: high | low | null)
- `created_at` (ISO 8601 datetime)

---

### Grounding Constraint — Implementation Note

The LLM system prompt **must** include all of the following constraints:

1. Explicit instruction to answer only from provided document excerpts.
2. Explicit instruction to state "I cannot find this information in the provided documents" if the answer is absent.
3. Explicit prohibition on referencing outside knowledge, training data, or general world knowledge.
4. No instruction that could be interpreted as permission to supplement with external facts.

Any change to the system prompt must be reviewed against these four requirements. Violation of grounding is a P0 defect.
---

## F02: Source Citations

**Priority:** P0 — MVP Critical  
**PRD Reference:** §5 F2

**Description:** Every assistant answer is accompanied by one or more citations identifying the exact source document and text passage used in generating that answer. Citations are displayed below the answer bubble as expandable chips; clicking a chip reveals the raw source passage. This feature is core to the product's trust and transparency promise — users must always be able to verify where an answer came from. Citations are assembled by the backend during the RAG retrieval step and attached to the answer's completion event.

---

### Terminology

- **Citation Chip:** A compact UI element (pill/badge) shown below an answer displaying the source document name and chunk reference.
- **Citation Panel:** The expanded view triggered by clicking a citation chip, showing the full raw passage text.
- **Source Passage:** The exact text of the chunk retrieved from the vector index and used in the LLM prompt.
- **Page Number:** The page of the source document where the chunk originated (available for PDF; estimated for DOCX; N/A for TXT).
- **Chunk Reference:** A human-readable label combining document name and chunk position (e.g., "contract.pdf — p. 4, excerpt 2").

---

### Sub-Features

- Citation chips rendered beneath each assistant answer bubble
- Expandable/collapsible citation panel showing raw passage text
- Multiple citations per answer when multiple chunks were used
- Visual distinction between citation area and answer text (muted/secondary styling)
- Document name displayed on each citation chip
- Page number displayed where available
- Similarity score optionally shown in expanded panel (dev/debug mode)
- Citations are read-only (no editing)
- "No citations" state for fallback (low-confidence) responses

---

### Process

1. During `POST /api/chat/query` (see F01 §Process step 6e), the backend collects all retrieved chunks that scored above the confidence threshold.
2. Backend assembles a `citations` array for each retrieved chunk: `{ document_id, document_name, chunk_index, chunk_text, page_number, similarity }`.
3. On LLM completion, backend sends the `done` SSE event with the `citations` array attached (see F01 §Outputs).
4. Frontend receives the `done` event and renders citation chips below the completed answer bubble.
5. Each chip displays: document name (truncated to 30 chars with ellipsis if longer) and page reference if available.
6. User clicks a citation chip → frontend expands the citation panel inline below the chip, showing the full `chunk_text` in a visually distinct (e.g., blockquote or bordered card) read-only text area.
7. Clicking the chip again (or a close button) collapses the panel.
8. Only one citation panel may be expanded at a time per message (expanding one collapses others).
9. For fallback/low-confidence responses: no citation chips are rendered; the answer itself contains the "not found" message.

---

### Inputs

Citations are not independently submitted by the user — they are generated by the backend as part of the query response (F01). The citation data flows from `POST /api/chat/query`.

Frontend inputs for citation interaction:
- `message_id` (string): Identifies which answer's citation panel is toggled.
- `citation_index` (integer): Index of the citation chip clicked within the answer's citation array.

---

### Outputs

**Citation object (included in `done` SSE event and stored in message history):**
```json
{
  "citation_index": 0,
  "document_id": "uuid-v4",
  "document_name": "annual-report-2025.pdf",
  "chunk_index": 23,
  "chunk_text": "Revenue for fiscal year 2025 totaled $4.2 billion, representing a 12% increase over the prior year...",
  "page_number": 8,
  "similarity": 0.91
}
```

**Citation chip display label (derived client-side):**
```
annual-report-2025.pdf — p. 8
```

**No-citation state (fallback response):**
```json
{
  "citations": [],
  "confidence": "low"
}
```

---

### Validation Rules

- `citations` array must be included in every `done` event; it may be empty only when `confidence` is `"low"`.
- `chunk_text` must not be empty; if a chunk's text is missing, that citation is omitted from the array.
- `document_name` must match the `filename` of the document record for the given `document_id`.
- `page_number` may be `null` for TXT files or when page extraction is not supported.
- `similarity` must be a float in [0.0, 1.0].
- Backend must not include chunks with similarity below the session's active `confidence_threshold` in the citations array.
- Maximum citations per answer: 10 (to prevent prompt/UI overload). If more than 10 chunks qualify, use the top 10 by similarity score.
- Citation text is read-only — the frontend must not provide any editing affordance on the `chunk_text`.

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Citations missing from done event (backend bug) | — | CLIENT: shows no citation chips | Answer displayed without citations; logged as warning |
| Document deleted between answer and citation view | — | — | Citation chip still shows stored text; document_id may be stale — this is acceptable for session history |
| chunk_text empty string | — | — | Citation omitted from array silently; backend logs warning |

*Citations do not have independent API endpoints — they are embedded in the chat query response. No separate error HTTP codes are defined for citation generation.*

---

### API Surface (this feature)

Citations are embedded in `POST /api/chat/query` response (see F01 and `Y1-api.md` §Chat). No separate citation endpoints exist in v1.

---

### Schema Surface (this feature)

Citations are stored as a JSON array within each message record. See `Y0-schema.md` §Messages.

Per-citation fields stored in message:
- `citation_index` (integer)
- `document_id` (UUID)
- `document_name` (string)
- `chunk_index` (integer)
- `chunk_text` (string)
- `page_number` (integer | null)
- `similarity` (float)
---

## F03: Document Library Management

**Priority:** P1 — MVP Completer  
**PRD Reference:** §5 F3

**Description:** Users can view all documents currently in their session via a document library sidebar or panel. Each document entry displays its filename, file type, size, and current ingestion status. Users can delete any document, which triggers removal from both the session metadata store and the vector index, ensuring deleted documents cannot influence future answers. The library shows an empty-state prompt when no documents are loaded.

---

### Terminology

- **Document Library:** The sidebar/panel listing all session documents with their statuses and management controls.
- **Delete Confirmation:** A modal or inline confirm prompt shown before executing document deletion to prevent accidental data loss.
- **Orphaned Chunks:** Vector index entries belonging to a deleted document — these must be purged synchronously on deletion.

---

### Sub-Features

- Document library sidebar/panel always visible in the main layout
- Per-document card showing: filename, file type icon, size (human-readable), status badge
- Status badge color coding: `uploading` (gray), `indexing` (blue/animated), `ready` (green), `error` (red)
- Delete button (trash icon) per document with confirmation prompt
- Confirmation modal: "Delete [filename]? This will remove it from the document index." with Cancel / Delete buttons
- Synchronous vector index purge of all chunks for the deleted document on confirmed delete
- Empty-state UI with upload call-to-action when document list is empty
- Document count summary (e.g., "3 documents · 4.2 MB")
- Polling or SSE-based status refresh to reflect indexing progress without page reload
- Error documents show a retry-upload affordance

---

### Process

1. On page load (or session init), frontend calls `GET /api/documents` to retrieve the full document list.
2. Frontend renders the document library with one card per document.
3. Frontend polls `GET /api/documents` every 3 seconds while any document is in `uploading` or `indexing` status; stops polling when all documents are `ready` or `error`.
4. User clicks the delete (trash) icon on a document card.
5. Frontend shows a confirmation modal with the document's filename and a warning that it will be removed from the index.
6. User clicks "Cancel" → modal closes; no action taken.
7. User clicks "Delete" → frontend disables the delete button and shows a spinner; sends `DELETE /api/documents/{document_id}`.
8. Backend:
   a. Validates `document_id` belongs to the current session; returns 404 if not.
   b. Removes all vector store chunks with `document_id` metadata matching the target document.
   c. Removes document metadata from the session store.
   d. Returns 204 No Content on success.
9. Frontend removes the document card from the list and updates the document count summary.
10. If the deleted document was the last `ready` document, frontend disables the chat input and shows a prompt to upload documents.
11. On `DELETE` failure, frontend shows an inline error on the document card with a retry option.

---

### Inputs

**List documents:**
- `session_id` (string, required): Via HTTP cookie `rag_session_id`.

**Delete document:**
- `session_id` (string, required): Via HTTP cookie `rag_session_id`.
- `document_id` (string, required): UUID of the document to delete; path parameter.

---

### Outputs

**Document list response (`GET /api/documents`):**
```json
{
  "session_id": "sess-abc123",
  "document_count": 2,
  "total_size_bytes": 2097152,
  "documents": [
    {
      "document_id": "uuid-v4",
      "filename": "report.pdf",
      "file_extension": "pdf",
      "size_bytes": 1048576,
      "status": "ready",
      "chunk_count": 143,
      "created_at": "2026-05-13T10:00:00Z",
      "indexed_at": "2026-05-13T10:00:28Z",
      "error_reason": null
    },
    {
      "document_id": "uuid-v4-2",
      "filename": "notes.txt",
      "file_extension": "txt",
      "size_bytes": 1048576,
      "status": "indexing",
      "chunk_count": 0,
      "created_at": "2026-05-13T10:01:00Z",
      "indexed_at": null,
      "error_reason": null
    }
  ]
}
```

**Delete success:** `204 No Content` (empty body)

**Empty session response:**
```json
{
  "session_id": "sess-abc123",
  "document_count": 0,
  "total_size_bytes": 0,
  "documents": []
}
```

---

### Validation Rules

- `GET /api/documents` with no session cookie creates and returns a new empty session (does not error).
- `DELETE /api/documents/{document_id}` must verify `document_id` belongs to the requesting session; cross-session access returns 404 (not 403) to avoid information leakage.
- Deletion of a document in `uploading` or `indexing` status is permitted; the backend must cancel or ignore the in-progress background task for that document ID.
- Deleting a document that does not exist (already deleted) returns 404 `DOCUMENT_NOT_FOUND`.
- Vector index purge is performed synchronously before returning 204; the response must not be sent until all chunks are removed.
- Document library must always reflect current state; stale cache is not acceptable — each `GET /api/documents` must read live session state.

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Document not found | 404 | DOCUMENT_NOT_FOUND | "Document not found" |
| Document belongs to different session | 404 | DOCUMENT_NOT_FOUND | "Document not found" (same as above — no info leak) |
| Vector index purge failure | 500 | INDEX_DELETE_ERROR | "Failed to remove document from index; please retry" |
| Session not found | 404 | SESSION_NOT_FOUND | "Session not found or expired" |

---

### API Surface (this feature)

See `Y1-api.md` §Documents for full request/response schemas.

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/documents` | List all documents in the current session |
| `DELETE` | `/api/documents/{document_id}` | Delete a document and purge its vector index entries |

---

### Schema Surface (this feature)

Uses session-scoped document metadata store. See `Y0-schema.md` §Documents.

Fields relevant to library management:
- `document_id`, `session_id`, `filename`, `file_extension`, `size_bytes`
- `status` (enum: uploading | indexing | ready | error)
- `chunk_count`, `error_reason`, `created_at`, `indexed_at`
---

## F04: Session-Scoped Chat History

**Priority:** P1 — MVP Completer  
**PRD Reference:** §5 F4

**Description:** All user questions and assistant answers within a session are preserved as an ordered transcript and displayed in a scrollable chat view. The history persists for the duration of the browser session and is cleared either on an explicit "New Session" / "Clear Chat" action or on page refresh (v1 scope). No cross-session or cross-browser persistence is required in v1. The chat history API endpoint allows the frontend to restore the transcript on reconnection within the same server-side session lifetime.

---

### Terminology

- **Transcript:** The ordered, append-only list of all messages (user and assistant) for a session.
- **Message:** A single entry in the transcript: either a user query or an assistant answer (with citations).
- **Session Lifetime:** The duration a server-side session remains valid; in v1, tied to process memory (restarting the backend clears all sessions).
- **Clear Chat:** An explicit user action that deletes all messages from the transcript and resets the chat view to the empty state, while optionally preserving uploaded documents.
- **New Session:** Resets both chat history and document library, creating a fresh session cookie.

---

### Sub-Features

- Full conversation transcript in a vertically scrollable chat container
- User messages displayed right-aligned in distinct bubble style
- Assistant messages displayed left-aligned with a bot avatar/icon
- Relative timestamps on messages (e.g., "just now", "2 min ago"); absolute ISO time on hover
- Auto-scroll to the latest message when a new message is appended
- Manual scroll preserved when user scrolls up (no forced scroll if user is reading history)
- "Clear Chat" button to wipe the transcript for the current session (preserves documents)
- "New Session" action to reset everything (clears documents and chat)
- Empty state displayed when no messages exist: onboarding copy prompting first upload and question
- Chat history restored from server on reconnect within the same session

---

### Process

**Loading history on page load:**
1. Frontend reads `rag_session_id` cookie (if present).
2. Frontend calls `GET /api/chat/history` with the session cookie.
3. If session exists with messages: frontend renders the full transcript in chronological order, including citation chips for assistant messages.
4. If session exists but no messages: frontend shows empty state with onboarding copy.
5. If no session cookie or session not found: backend creates a new session, returns empty history, and sets `rag_session_id` cookie.
6. Frontend scrolls to the bottom of the transcript after render.

**Appending messages (per-query flow — see F01):**
1. On user query submit: user message appended to transcript immediately (optimistic).
2. On assistant answer complete: assistant message with citations appended to transcript; chat scrolled to bottom.

**Clear Chat:**
1. User clicks "Clear Chat" button.
2. Frontend shows a brief confirmation: "Clear conversation? Documents remain uploaded." with Cancel / Clear buttons.
3. User confirms → frontend sends `DELETE /api/chat/history`.
4. Backend removes all messages from the session transcript; documents and vector index are untouched.
5. Backend returns 204 No Content.
6. Frontend clears the chat view and displays the empty state.

**New Session:**
1. User clicks "New Session" (distinct from Clear Chat).
2. Frontend shows confirmation: "Start a new session? All documents and chat history will be cleared."
3. User confirms → frontend sends `POST /api/session/reset`.
4. Backend deletes all session data (messages, document metadata, vector index entries).
5. Backend creates a new session, returns new `rag_session_id` cookie.
6. Frontend clears both the document library and chat view; shows empty onboarding state.

---

### Inputs

**Get history:**
- `session_id` (string, required): Via HTTP cookie.

**Clear chat:**
- `session_id` (string, required): Via HTTP cookie.

**New session:**
- `session_id` (string, optional): Old session cookie used to identify what to delete.

---

### Outputs

**Chat history response (`GET /api/chat/history`):**
```json
{
  "session_id": "sess-abc123",
  "message_count": 4,
  "messages": [
    {
      "message_id": "uuid-1",
      "role": "user",
      "content": "What was the total revenue in 2025?",
      "citations": [],
      "confidence": null,
      "created_at": "2026-05-13T10:05:00Z"
    },
    {
      "message_id": "uuid-2",
      "role": "assistant",
      "content": "Revenue for fiscal year 2025 totaled $4.2 billion.",
      "citations": [
        {
          "citation_index": 0,
          "document_id": "uuid-doc",
          "document_name": "annual-report-2025.pdf",
          "chunk_index": 23,
          "chunk_text": "Revenue for fiscal year 2025 totaled $4.2 billion...",
          "page_number": 8,
          "similarity": 0.91
        }
      ],
      "confidence": "high",
      "created_at": "2026-05-13T10:05:06Z"
    }
  ]
}
```

**Clear success:** `204 No Content`

**New session response:**
```json
{
  "session_id": "sess-new-xyz",
  "message_count": 0,
  "document_count": 0
}
```

---

### Validation Rules

- Messages are stored in insertion order; the API returns them in ascending `created_at` order.
- Message `role` must be `"user"` or `"assistant"` — no other values.
- User messages have empty `citations` array and `null` `confidence`.
- Assistant messages must always have a `citations` array (may be empty for low-confidence answers) and a `confidence` value (`"high"` or `"low"`).
- `GET /api/chat/history` must not paginate in v1 — returns full transcript (max ~2M tokens of context per session limit provides a natural cap).
- `DELETE /api/chat/history` only clears messages; documents and vector index are not affected.
- `POST /api/session/reset` clears everything and sets a new session cookie; old session data must be fully purged.
- Auto-scroll behavior: the frontend scrolls to bottom on new message only if the user's scroll position was already at (or within 100px of) the bottom before the message arrived.

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Session not found on GET | 200 | — | Returns empty history with new session cookie (no error) |
| Session not found on DELETE | 404 | SESSION_NOT_FOUND | "Session not found or expired" |
| Session not found on reset | 200 | — | Creates new session anyway; returns new session data |

---

### API Surface (this feature)

See `Y1-api.md` §Chat and §Session for full request/response schemas.

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/chat/history` | Retrieve full session transcript |
| `DELETE` | `/api/chat/history` | Clear all messages (preserves documents) |
| `POST` | `/api/session/reset` | Reset session — clears documents, vectors, and messages |

---

### Schema Surface (this feature)

Uses session-scoped message store. See `Y0-schema.md` §Messages and §Sessions.

Key message fields: `message_id`, `session_id`, `role`, `content`, `citations` (JSON), `confidence`, `created_at`.
---

## F05: Premium Responsive UI

**Priority:** P1 — MVP Completer  
**PRD Reference:** §5 F5

**Description:** The React frontend is designed and implemented to a premium, polished standard — clean layout, smooth animations, accessible color contrast, and full responsiveness from desktop to mobile. The UI must feel professional and delightful without sacrificing usability. This feature defines the frontend UX specifications that cut across all other features and govern how they are rendered.

---

### Terminology

- **Split-Panel Layout:** The two-column desktop layout with the document library on the left and the chat area on the right.
- **Collapsed Sidebar:** On mobile/tablet viewports, the document library collapses into a drawer or tab rather than a persistent panel.
- **Drag-Over State:** Visual feedback applied to the upload drop zone when a file is held over it during a drag operation.
- **Skeleton Loader:** A placeholder UI element (gray animated bar) shown in place of content while data is loading.
- **Focus Ring:** A visible outline around the currently focused interactive element, required for keyboard navigation.
- **WCAG AA:** Web Content Accessibility Guidelines 2.1 Level AA — the minimum accessibility standard required.
- **Onboarding Empty State:** The first-run UI shown when no documents have been uploaded, guiding the user to start.

---

### Sub-Features

- **Layout:** Split-panel (sidebar + main chat) on desktop; collapsible drawer on mobile
- **Upload Zone:** Drag-and-drop area with drag-over highlight, animated border, and descriptive copy
- **Document Library:** Card-based list with status badges, file type icons, size display, delete button
- **Chat Bubbles:** Distinct styles for user (right-aligned, accent color) and assistant (left-aligned, neutral) messages
- **Citation Chips:** Compact pill elements below assistant messages; expandable inline panels
- **Loading States:** Thinking indicator (animated dots or typing animation) during LLM generation; skeleton loaders on initial data fetch
- **Animations:** Smooth message entrance slide-in; citation panel expand/collapse transition; upload progress bar animation
- **Accessibility:** WCAG 2.1 AA contrast ratios; full tab-order keyboard navigation; focus rings on all interactive elements; ARIA labels on icon-only buttons
- **Responsive Layout:** Adapts gracefully at 320px, 768px, 1024px, and 1440px breakpoints
- **Empty States:** Onboarding copy for no-documents state and no-messages state
- **Error States:** Inline error messages styled consistently (red/destructive variant)
- **Color Palette:** Semantic color tokens (primary, secondary, muted, destructive, success, warning)

---

### Process

*This feature describes layout and interaction specifications; it has no server-side process. Frontend rendering processes are described per-interaction below.*

**Page Load:**
1. App shell renders immediately with split-panel layout and skeleton placeholders.
2. Frontend fetches session data (`GET /api/documents`, `GET /api/chat/history`) in parallel.
3. Skeletons replaced with real content on data arrival; smooth fade-in transition.
4. If no documents: onboarding empty state shown in document library and chat area.

**Drag-and-Drop Upload:**
1. User drags file(s) over the drop zone → drop zone border animates to accent color, background tints.
2. User drops files → border returns to default; upload cards appear with progress spinners.
3. If user drags off the window → drop zone returns to default state immediately.

**Responsive Behavior:**
- ≥ 1024px (desktop): Persistent sidebar (left, ~280px) + main chat area (remaining width). Sidebar scrolls independently.
- 768px–1023px (tablet): Sidebar collapses to an icon-strip; tap on document icon expands a full-height drawer overlay.
- < 768px (mobile): Single-column layout. Document library accessible via a bottom sheet or top tab. Chat takes full screen width.

**Keyboard Navigation:**
- Tab order: Upload zone → Document library items → Chat input → Send button → Clear chat → New session.
- Enter on upload zone opens the file picker.
- Enter in chat input submits query (Shift+Enter inserts newline).
- Escape closes open modals, citation panels, and drawer overlays.

**Accessibility Requirements:**
- All color pairs must meet WCAG AA contrast ratio (≥ 4.5:1 for normal text, ≥ 3:1 for large text).
- All interactive elements must have accessible name via visible label or `aria-label`.
- Status badges must not rely on color alone — include text label (e.g., "Ready", "Error").
- Images and icons must have `alt` text or `aria-hidden` if decorative.
- Dynamic content updates (new messages, status changes) must use ARIA live regions (`aria-live="polite"`).

---

### Inputs

*Frontend-only feature; all inputs are user interactions (clicks, drags, keyboard) and API responses from other features.*

---

### Outputs

*Rendered React UI — no API responses produced by this feature directly.*

Key rendered components:
- `<AppLayout>`: Root split-panel layout
- `<DocumentLibrary>`: Sidebar document list with cards and status badges
- `<UploadZone>`: Drag-and-drop upload area
- `<ChatView>`: Scrollable message transcript
- `<MessageBubble>`: Individual user or assistant message
- `<CitationChip>` / `<CitationPanel>`: Citation display components
- `<ChatInput>`: Text input + send button
- `<LoadingIndicator>`: Thinking dots animation
- `<EmptyState>`: Onboarding or cleared-state UI
- `<ConfirmModal>`: Reusable confirmation dialog

---

### Validation Rules

- All breakpoints (320px, 768px, 1024px, 1440px) must be visually tested and free of horizontal overflow.
- No interactive element may be unreachable by keyboard alone.
- All WCAG AA contrast ratios must pass automated axe-core audit with zero violations.
- File type icons must be visually distinct (PDF ≠ TXT ≠ DOCX).
- Upload progress bar must visually complete and transition to "ready" state without a flash of empty state.
- Chat auto-scroll must not hijack manual scroll — see F04 §Validation Rules for scroll logic.
- Animations must respect `prefers-reduced-motion` media query — all animations disabled if user has motion reduction preference set.
- Loading skeletons must appear within 100ms of a network request start (no blank screen flash).

---

### Error States

| Scenario | UI Behavior |
|---|---|
| Network request fails | Inline error banner with "Retry" button; no full-page error screen |
| LLM stream interrupted | Error bubble in chat: "Answer generation failed. Please try again." with retry button |
| Upload rejected (client-side validation) | Red inline error below upload zone: specific reason (e.g., "Only PDF, TXT, and DOCX supported") |
| Delete fails | Red inline error on document card: "Delete failed. Try again." |
| Session expired | Toast notification: "Your session has expired. Starting a new session." — auto-reset |

---

### API Surface (this feature)

No new API endpoints. This feature consumes all endpoints from F00–F04 and F06–F08.

---

### Schema Surface (this feature)

No new schema entities. Frontend state managed in React component state and/or a lightweight state manager (e.g., Zustand or Redux Toolkit).

Frontend state shape (informational):
- `session`: `{ session_id, document_count, total_size_bytes }`
- `documents`: `Document[]` (mirroring server document records)
- `messages`: `Message[]` (mirroring server message records)
- `uiState`: `{ isUploading, isQuerying, sidebarOpen, activeModal, activeCitationPanel }`
---

## F06: Multi-Document Context Retrieval

**Priority:** P2 — Post-MVP  
**PRD Reference:** §5 F6

**Description:** When multiple documents are indexed in a session, the retrieval step searches across all of them simultaneously in a single vector query. Answers and citations may draw from multiple documents, and each citation clearly identifies which document it originated from. An optional document-scope filter allows users to restrict a query to a specific document. This feature extends F01 and F02 — multi-document retrieval is the default behavior when more than one document is `ready`; no configuration is needed beyond uploading multiple documents.

---

### Terminology

- **Session Index:** The unified vector store namespace containing chunks from all `ready` documents in the session.
- **Cross-Document Retrieval:** A single top-k query that returns chunks from any document in the session index, ranked by similarity without document-level bias.
- **Document Filter:** An optional query parameter restricting retrieval to chunks from a specific `document_id`.
- **Multi-Source Answer:** An answer whose citations reference two or more distinct documents.
- **Document Attribution:** The per-citation `document_id` and `document_name` fields that identify the source document for each chunk.

---

### Sub-Features

- All `ready` document chunks stored in a shared session-scoped vector namespace (or collection prefix)
- Top-k retrieval query spans the full session namespace by default
- Per-citation document attribution (already provided by F02; this feature ensures multi-doc correctness)
- Optional document filter parameter on `POST /api/chat/query`
- UI indicator when an answer draws from multiple documents (e.g., "From 2 documents" label above citations)
- Document filter UI control (dropdown or document chip selector) — v1 nice-to-have; implementation optional

---

### Process

1. Each document chunk is stored in the vector index with metadata `{ document_id, document_name, chunk_index, page_number }` — this tagging is performed during F00 ingestion.
2. When a user submits a query (F01 §Process), the retrieval step queries the full session namespace without any document filter unless one is explicitly provided.
3. If `document_filter` is set in the request:
   a. Backend applies a metadata filter to the vector search: only chunks with matching `document_id` are candidates.
   b. If no chunks exist for the specified document, returns an error `DOCUMENT_NOT_IN_INDEX`.
   c. If the document's status is not `ready`, returns 422 `DOCUMENT_NOT_READY`.
4. Top-k results may include chunks from different documents; each result retains its full metadata.
5. The `citations` array in the response lists all retrieved chunks with their `document_id` and `document_name` (see F02).
6. Frontend detects when citations reference more than one unique `document_id` and renders a "From N documents" summary label above the citation chips.
7. Document filter UI (if implemented):
   a. A dropdown or chip-list above the chat input lists all `ready` documents.
   b. Selecting a document sets `document_filter` on the next query; clearing returns to cross-document retrieval.
   c. Visual indicator in the chat input area shows when a filter is active.

---

### Inputs

In addition to F01 inputs:
- `document_filter` (string UUID, optional): Restricts retrieval to chunks from the specified document. If provided, must be a `document_id` belonging to the current session with status `ready`.

---

### Outputs

Multi-document answer (same structure as F01/F02 outputs, citations from multiple documents):
```json
{
  "message_id": "uuid-v4",
  "answer": "The acquisition was valued at $500M according to the press release, and the integration timeline of 18 months is detailed in the strategy document.",
  "citations": [
    {
      "citation_index": 0,
      "document_id": "uuid-doc-1",
      "document_name": "press-release.pdf",
      "chunk_index": 5,
      "chunk_text": "...acquisition valued at $500 million...",
      "page_number": 1,
      "similarity": 0.93
    },
    {
      "citation_index": 1,
      "document_id": "uuid-doc-2",
      "document_name": "strategy-2025.docx",
      "chunk_index": 42,
      "chunk_text": "...integration timeline of 18 months...",
      "page_number": 7,
      "similarity": 0.88
    }
  ],
  "confidence": "high",
  "document_sources": ["press-release.pdf", "strategy-2025.docx"],
  "created_at": "2026-05-13T10:10:00Z"
}
```

---

### Validation Rules

- All chunks must be stored with a `document_id` metadata field at index time — this is a hard requirement enforced in F00 ingestion.
- If `document_filter` is provided: `document_id` must exist in the current session and have status `ready`; otherwise return the appropriate error.
- Retrieval with no filter must not be biased toward any document — the ranking is purely by cosine similarity.
- `document_sources` in the response is a deduplicated list of document names referenced by at least one citation.
- The "From N documents" label in the UI is shown only when `document_sources` contains 2 or more entries.
- When only one document is in the session, behavior is identical to single-document retrieval; no special handling needed.

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| document_filter references unknown document_id | 404 | DOCUMENT_NOT_FOUND | "Document not found in this session" |
| document_filter references document not yet ready | 422 | DOCUMENT_NOT_READY | "Document is still being indexed; please wait" |
| No chunks found for filtered document | 422 | DOCUMENT_NOT_IN_INDEX | "Document has no indexed content" |

---

### API Surface (this feature)

Extends `POST /api/chat/query` with optional `document_filter` parameter. See `Y1-api.md` §Chat.

No new endpoints introduced by this feature.

---

### Schema Surface (this feature)

No new schema entities. Relies on chunk metadata `document_id` established in F00. See `Y0-schema.md` §Chunks.
---

## F07: Answer Confidence & Relevance Feedback

**Priority:** P2 — Post-MVP  
**PRD Reference:** §5 F7

**Description:** The system surfaces a confidence signal alongside each answer to help users understand when the retrieved document context is strong or weak. A low-confidence indicator is shown when retrieval scores fall below the threshold, guiding users to rephrase or upload better source material. Users can also rate each answer with a thumbs-up or thumbs-down, which is recorded in session state to support future quality analysis. Neither the confidence signal nor feedback results influence the v1 answer generation itself — they are observability and UX trust tools.

---

### Terminology

- **Confidence Signal:** A visual indicator (badge, icon, or color) attached to each assistant message reflecting the strength of retrieved context.
- **High Confidence:** All retrieved chunks have similarity ≥ the session's `confidence_threshold` (default 0.30); top-1 similarity ≥ 0.60.
- **Low Confidence:** The best retrieved chunk similarity is ≥ 0.30 but < 0.60; answer is generated but marked as potentially weak.
- **No Context (Fallback):** All retrieved chunks are below 0.30; the fallback "not found in documents" response is returned (established in F01).
- **Thumbs Feedback:** A binary user rating (positive / negative) per assistant message, stored in session.
- **Rephrasing Suggestion:** An optional UI prompt shown on low-confidence answers: "Try rephrasing your question or uploading additional documents."

---

### Sub-Features

- Confidence badge on each assistant message: `High`, `Low`, or none (fallback has no badge)
- Confidence badge styling: high = subtle green indicator; low = amber/yellow indicator
- Thumbs-up / thumbs-down buttons on each assistant message (icon buttons, not visible by default — appear on hover/focus)
- Feedback recorded per message in session store
- Feedback is one-shot per message: once submitted, buttons become inactive (shows selected state)
- Rephrasing suggestion shown inline below low-confidence answers
- Confidence score optionally visible in expanded citation panel (developer/debug mode; hidden by default in production)

---

### Process

**Confidence Signal Generation (server-side, during F01 query):**
1. After top-k retrieval, backend computes `max_similarity` = highest similarity score among retrieved chunks.
2. If `max_similarity` < 0.30 → `confidence = "none"` → return fallback response (see F01 §Process step 6c).
3. If 0.30 ≤ `max_similarity` < 0.60 → `confidence = "low"` → proceed with LLM generation but flag response.
4. If `max_similarity` ≥ 0.60 → `confidence = "high"` → proceed with LLM generation normally.
5. `confidence` value included in the `done` SSE event and stored with the message.

**Confidence Signal Display (client-side):**
1. Frontend reads `confidence` from the `done` event.
2. If `"high"`: renders a small green dot or "High confidence" badge near the answer timestamp.
3. If `"low"`: renders an amber "Low confidence" badge + rephrasing suggestion text below the answer.
4. If `"none"` (fallback): no confidence badge; the answer text itself explains the situation.

**User Feedback (thumbs):**
1. User hovers over or focuses an assistant message bubble → thumbs-up and thumbs-down icons appear.
2. User clicks thumbs-up or thumbs-down.
3. Frontend sends `POST /api/chat/feedback` with `{ message_id, rating: "positive" | "negative" }`.
4. Backend records feedback in the session message record.
5. Backend returns 200 with the updated message record.
6. Frontend updates the icon state to show the selected rating (filled icon); hides the unselected icon.
7. Buttons become disabled — feedback cannot be changed after submission in v1.
8. Feedback does not trigger any real-time model update or response modification.

---

### Inputs

**Feedback submission:**
- `message_id` (string UUID, required): The assistant message being rated.
- `rating` (string, required): Must be `"positive"` or `"negative"`.
- `session_id` (string, required): Via HTTP cookie.

---

### Outputs

**Feedback response (`POST /api/chat/feedback`):**
```json
{
  "message_id": "uuid-v4",
  "rating": "positive",
  "recorded_at": "2026-05-13T10:15:00Z"
}
```

**Confidence in message object (extends F01/F04 message schema):**
```json
{
  "message_id": "uuid-v4",
  "role": "assistant",
  "content": "The contract was signed on March 15, 2024.",
  "confidence": "high",
  "user_rating": null,
  "citations": [...]
}
```

**After feedback submission:**
```json
{
  "user_rating": "positive"
}
```

---

### Validation Rules

- `rating` must be exactly `"positive"` or `"negative"`; any other value returns 400 `INVALID_RATING`.
- Feedback may only be submitted for messages with `role = "assistant"`; submitting for a user message returns 400 `INVALID_MESSAGE_ROLE`.
- Feedback may only be submitted once per message per session; a second submission returns 409 `FEEDBACK_ALREADY_SUBMITTED`.
- `message_id` must belong to the current session; cross-session access returns 404 `MESSAGE_NOT_FOUND`.
- The confidence thresholds (0.30 and 0.60) are defaults; they may be overridden per-query via `confidence_threshold` (see F01), but the low/high split always uses:
  - `max_similarity < confidence_threshold` → fallback (no badge)
  - `confidence_threshold ≤ max_similarity < 0.60` → low badge
  - `max_similarity ≥ 0.60` → high badge
  *(The 0.60 split point is fixed; only the fallback threshold is configurable.)*

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Invalid rating value | 400 | INVALID_RATING | "Rating must be 'positive' or 'negative'" |
| Feedback on user message | 400 | INVALID_MESSAGE_ROLE | "Feedback can only be submitted for assistant messages" |
| Feedback already submitted | 409 | FEEDBACK_ALREADY_SUBMITTED | "Feedback has already been recorded for this message" |
| Message not found | 404 | MESSAGE_NOT_FOUND | "Message not found" |
| Session not found | 404 | SESSION_NOT_FOUND | "Session not found or expired" |

---

### API Surface (this feature)

See `Y1-api.md` §Feedback for full request/response schemas.

| Method | Path | Summary |
|---|---|---|
| `POST` | `/api/chat/feedback` | Submit thumbs-up or thumbs-down for an assistant message |

---

### Schema Surface (this feature)

Extends message records with feedback fields. See `Y0-schema.md` §Messages.

Additional fields added to message record by this feature:
- `confidence` (enum: high | low | none | null) — `null` for user messages
- `max_similarity` (float | null) — highest retrieval score; stored for analytics
- `user_rating` (enum: positive | negative | null) — null until feedback submitted
- `rating_recorded_at` (ISO 8601 datetime | null)
---

## F08: Export & Copy Utilities

**Priority:** P3 — Backlog / Post-MVP  
**PRD Reference:** §5 F8

**Description:** Users can copy individual assistant answers to the clipboard or export the full chat transcript as a downloadable file (plain text or Markdown). Source citation text can also be copied independently. These utilities support the common workflow of researching a document set and then using the findings in an external document, email, or report. All export/copy actions are client-side where possible; the transcript export endpoint is provided for completeness and to ensure consistent formatting.

---

### Terminology

- **Copy-to-Clipboard:** Writing text content to the browser clipboard using the Clipboard API (`navigator.clipboard.writeText`).
- **Transcript Export:** Generating and downloading the full session chat history as a `.txt` or `.md` file.
- **Export Format (Plain Text):** A human-readable text file with user/assistant labels and citation references.
- **Export Format (Markdown):** A `.md` file with heading-formatted metadata, bold speaker labels, blockquoted citations, and proper Markdown formatting for downstream editors.

---

### Sub-Features

- Copy button (icon) on each assistant message bubble
- Copy citation text button within each expanded citation panel
- "Export Transcript" button in the chat header or menu
- Format selection for export: Plain Text or Markdown
- Download triggered client-side (browser `<a download>` or `Blob` URL)
- Optional server-side export endpoint for consistent formatting
- Success feedback on copy (transient "Copied!" tooltip or icon state change)

---

### Process

**Copy Answer:**
1. User hovers over or focuses an assistant message bubble → copy icon appears (alongside thumbs buttons if F07 is enabled).
2. User clicks copy icon.
3. Frontend calls `navigator.clipboard.writeText(message.content)`.
4. On success: copy icon briefly changes to a checkmark and a "Copied!" tooltip appears for 2 seconds.
5. On clipboard API failure (permission denied): frontend falls back to `document.execCommand('copy')` with a selected `<textarea>`.
6. No server call is made for copying individual answers.

**Copy Citation Text:**
1. User expands a citation panel (see F02 §Process).
2. A copy icon appears within the citation panel header.
3. User clicks copy → frontend calls `navigator.clipboard.writeText(citation.chunk_text)`.
4. Same success/fallback behavior as above.

**Export Transcript:**
1. User clicks "Export Transcript" button.
2. Frontend shows a format selection dropdown or modal: "Plain Text (.txt)" or "Markdown (.md)".
3. User selects format and clicks "Download".
4. Frontend calls `GET /api/chat/export?format=text|markdown`.
5. Backend generates the formatted transcript string and returns it as a downloadable file response with appropriate `Content-Disposition` header.
6. Frontend triggers download via the response blob.

**Export format — Plain Text:**
```
RAGChatbot Transcript
Session: sess-abc123
Exported: 2026-05-13 10:30:00

---

[10:05:00] User: What was the total revenue in 2025?

[10:05:06] Assistant: Revenue for fiscal year 2025 totaled $4.2 billion.

Sources:
  [1] annual-report-2025.pdf, p. 8: "Revenue for fiscal year 2025 totaled $4.2 billion, representing a 12% increase..."

---
```

**Export format — Markdown:**
```markdown
# RAGChatbot Transcript

- **Session:** sess-abc123
- **Exported:** 2026-05-13 10:30:00

---

**User** *(10:05:00)*: What was the total revenue in 2025?

**Assistant** *(10:05:06)*: Revenue for fiscal year 2025 totaled $4.2 billion.

> **Sources**
> 1. `annual-report-2025.pdf`, p. 8: *"Revenue for fiscal year 2025 totaled $4.2 billion, representing a 12% increase..."*

---
```

---

### Inputs

**Export transcript request:**
- `session_id` (string, required): Via HTTP cookie.
- `format` (string, required): Query parameter. Must be `"text"` or `"markdown"`.

---

### Outputs

**Export response:**
- `Content-Type`: `text/plain; charset=utf-8` (for text) or `text/markdown; charset=utf-8` (for markdown)
- `Content-Disposition`: `attachment; filename="rag-transcript-{session_id}.txt"` or `...md`
- Body: Formatted transcript string

**Copy actions:** No server response — client-side only.

---

### Validation Rules

- `format` parameter must be `"text"` or `"markdown"`; any other value returns 400 `INVALID_EXPORT_FORMAT`.
- If chat history is empty, export returns a file with header metadata only and a note: "No messages in this session."
- Copy actions must silently degrade if the Clipboard API is unavailable — never show a hard error; show a soft "Copy unavailable in this browser" message at most.
- Exported transcript must include all messages in chronological order; no messages may be omitted.
- Citation text in export must be truncated to 500 characters with "..." if longer, to keep the exported file readable.

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Invalid export format | 400 | INVALID_EXPORT_FORMAT | "Format must be 'text' or 'markdown'" |
| Session not found | 404 | SESSION_NOT_FOUND | "Session not found or expired" |
| Clipboard API unavailable (client-side) | — | — | Soft UI message: "Copy unavailable in this browser" |

---

### API Surface (this feature)

See `Y1-api.md` §Export for full request/response schemas.

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/chat/export` | Download full session transcript as text or markdown file |

---

### Schema Surface (this feature)

No new schema entities. Reads from message store (see `Y0-schema.md` §Messages). Export is read-only.
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
---

## Y1: REST API Endpoint Catalog

**Base URL:** `/api`  
**Content-Type:** `application/json` (all requests/responses unless noted)  
**Auth:** Session cookie `rag_session_id` (HTTP-only, SameSite=Lax). Auto-issued on first request if absent.  
**Error format:**
```json
{ "error_code": "SCREAMING_SNAKE_CASE", "message": "Human-readable message", "detail": {} }
```

---

### §Documents

#### POST /api/documents/upload

Upload a document file for ingestion into the session vector index.

**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | binary | Yes | Document file bytes |
| `chunk_size` | integer | No | Tokens per chunk [128–2048]; default 512 |
| `chunk_overlap` | integer | No | Token overlap [0, chunk_size-1]; default 64 |

**Responses:**

`202 Accepted`
```json
{
  "document_id": "uuid-v4",
  "filename": "report.pdf",
  "status": "uploading",
  "size_bytes": 1048576,
  "created_at": "2026-05-13T10:00:00Z"
}
```

`400 Bad Request` — validation errors (INVALID_FILE_TYPE, FILE_TOO_LARGE, SESSION_STORAGE_LIMIT, SESSION_DOCUMENT_LIMIT, EMPTY_FILE)

---

#### GET /api/documents/{document_id}/status

Poll ingestion status for a specific document.

**Path parameters:** `document_id` (UUID)

**Responses:**

`200 OK`
```json
{
  "document_id": "uuid-v4",
  "filename": "report.pdf",
  "status": "ready",
  "chunk_count": 143,
  "indexed_at": "2026-05-13T10:00:28Z",
  "error_reason": null
}
```

`404 Not Found` — DOCUMENT_NOT_FOUND

---

#### GET /api/documents

List all documents in the current session.

**Responses:**

`200 OK`
```json
{
  "session_id": "sess-abc123",
  "document_count": 2,
  "total_size_bytes": 2097152,
  "documents": [
    {
      "document_id": "uuid-v4",
      "filename": "report.pdf",
      "file_extension": "pdf",
      "size_bytes": 1048576,
      "status": "ready",
      "chunk_count": 143,
      "created_at": "2026-05-13T10:00:00Z",
      "indexed_at": "2026-05-13T10:00:28Z",
      "error_reason": null
    }
  ]
}
```

*Returns empty `documents` array (not 404) if session has no documents. Creates session if no cookie present.*

---

#### DELETE /api/documents/{document_id}

Delete a document and purge all its vector index entries.

**Path parameters:** `document_id` (UUID)

**Responses:**

`204 No Content` — success; body empty  
`404 Not Found` — DOCUMENT_NOT_FOUND  
`500 Internal Server Error` — INDEX_DELETE_ERROR

---

### §Chat

#### POST /api/chat/query

Submit a question and receive a streamed answer via Server-Sent Events.

**Request body (JSON):**

| Field | Type | Required | Notes |
|---|---|---|---|
| `query` | string | Yes | User question; 1–2000 chars |
| `k` | integer | No | Top-k retrieval count [1–20]; default 5 |
| `confidence_threshold` | float | No | Min similarity [0.0–1.0]; default 0.30 |
| `document_filter` | string (UUID) | No | Restrict retrieval to one document (F06) |

**Response:** `text/event-stream` (SSE)

Stream events during generation:
```
data: {"token": "The"}
data: {"token": " contract"}
...
```

Final event:
```
data: {
  "done": true,
  "message_id": "uuid-v4",
  "citations": [
    {
      "citation_index": 0,
      "document_id": "uuid",
      "document_name": "contract.pdf",
      "chunk_index": 7,
      "chunk_text": "...expires on December 31, 2026...",
      "page_number": 4,
      "similarity": 0.87
    }
  ],
  "confidence": "high",
  "max_similarity": 0.87,
  "document_sources": ["contract.pdf"],
  "created_at": "2026-05-13T10:05:06Z"
}
```

Low-confidence fallback (non-streaming, `200 OK` with JSON body):
```json
{
  "message_id": "uuid-v4",
  "answer": "The uploaded documents do not contain information about this topic.",
  "citations": [],
  "confidence": "none",
  "max_similarity": 0.18,
  "document_sources": [],
  "created_at": "2026-05-13T10:05:00Z"
}
```

**Error responses:**

`400` — EMPTY_QUERY, QUERY_TOO_LONG  
`404` — SESSION_NOT_FOUND, DOCUMENT_NOT_FOUND (if document_filter invalid)  
`422` — NO_READY_DOCUMENTS, DOCUMENT_NOT_READY, DOCUMENT_NOT_IN_INDEX  
`429` — QUERY_IN_PROGRESS  
`503` — EMBED_ERROR, LLM_UNAVAILABLE, RETRIEVAL_ERROR  
`504` — LLM_TIMEOUT

---

#### GET /api/chat/history

Retrieve full session chat transcript in chronological order.

**Responses:**

`200 OK`
```json
{
  "session_id": "sess-abc123",
  "message_count": 4,
  "messages": [
    {
      "message_id": "uuid-1",
      "role": "user",
      "content": "What was the total revenue in 2025?",
      "citations": [],
      "confidence": null,
      "max_similarity": null,
      "user_rating": null,
      "rating_recorded_at": null,
      "created_at": "2026-05-13T10:05:00Z"
    },
    {
      "message_id": "uuid-2",
      "role": "assistant",
      "content": "Revenue for fiscal year 2025 totaled $4.2 billion.",
      "citations": [ { "...": "..." } ],
      "confidence": "high",
      "max_similarity": 0.91,
      "user_rating": null,
      "rating_recorded_at": null,
      "created_at": "2026-05-13T10:05:06Z"
    }
  ]
}
```

*Returns empty messages array (not 404) if no messages exist. Creates session if no cookie.*

---

#### DELETE /api/chat/history

Clear all messages from the session transcript (documents and vector index untouched).

**Responses:**

`204 No Content` — success  
`404 Not Found` — SESSION_NOT_FOUND

---

#### GET /api/chat/export

Download session transcript as a formatted text file.

**Query parameters:**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `format` | string | Yes | `"text"` or `"markdown"` |

**Responses:**

`200 OK` with file download  
- `Content-Type`: `text/plain; charset=utf-8` or `text/markdown; charset=utf-8`  
- `Content-Disposition`: `attachment; filename="rag-transcript-{session_id}.txt"` or `.md`  
- Body: Formatted transcript string

`400 Bad Request` — INVALID_EXPORT_FORMAT  
`404 Not Found` — SESSION_NOT_FOUND

---

### §Feedback

#### POST /api/chat/feedback

Submit user thumbs-up or thumbs-down rating for an assistant message.

**Request body (JSON):**

| Field | Type | Required | Notes |
|---|---|---|---|
| `message_id` | string (UUID) | Yes | Must be an assistant message in current session |
| `rating` | string | Yes | `"positive"` or `"negative"` |

**Responses:**

`200 OK`
```json
{
  "message_id": "uuid-v4",
  "rating": "positive",
  "recorded_at": "2026-05-13T10:15:00Z"
}
```

`400` — INVALID_RATING, INVALID_MESSAGE_ROLE  
`404` — MESSAGE_NOT_FOUND, SESSION_NOT_FOUND  
`409` — FEEDBACK_ALREADY_SUBMITTED

---

### §Session

#### POST /api/session/reset

Reset the entire session — purges all documents, vector index entries, and messages; creates a fresh session.

**Request:** No body required.

**Responses:**

`200 OK` (new session cookie set in response headers)
```json
{
  "session_id": "sess-new-xyz",
  "message_count": 0,
  "document_count": 0,
  "created_at": "2026-05-13T10:20:00Z"
}
```

*Always succeeds; if old session doesn't exist, a new one is created anyway.*

---

### §Health

#### GET /api/health

System health check — verifies all backend dependencies are reachable.

**Responses:**

`200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2026-05-13T10:00:00Z",
  "checks": {
    "vector_store": "ok",
    "embedding_api": "ok",
    "llm_api": "ok"
  }
}
```

`503 Service Unavailable`
```json
{
  "status": "degraded",
  "timestamp": "2026-05-13T10:00:00Z",
  "checks": {
    "vector_store": "ok",
    "embedding_api": "error",
    "llm_api": "ok"
  }
}
```

---

### API Summary Table

| Method | Path | Feature | Priority |
|---|---|---|---|
| `POST` | `/api/documents/upload` | F00 | P0 |
| `GET` | `/api/documents/{document_id}/status` | F00 | P0 |
| `GET` | `/api/documents` | F03 | P1 |
| `DELETE` | `/api/documents/{document_id}` | F03 | P1 |
| `POST` | `/api/chat/query` | F01, F02, F06 | P0 |
| `GET` | `/api/chat/history` | F04 | P1 |
| `DELETE` | `/api/chat/history` | F04 | P1 |
| `GET` | `/api/chat/export` | F08 | P3 |
| `POST` | `/api/chat/feedback` | F07 | P2 |
| `POST` | `/api/session/reset` | F04 | P1 |
| `GET` | `/api/health` | Infra | — |
---

## Y2: Cross-Feature Error Catalog

This catalog lists every error code that the RAGChatbot API can return, the HTTP status it uses, the feature that produces it, and guidance for clients on whether/how to retry.

**Error response format (all errors):**
```json
{
  "error_code": "SCREAMING_SNAKE_CASE",
  "message": "Human-readable message for display",
  "detail": {}
}
```

---

### Document & Ingestion Errors (F00, F03)

| Error Code | HTTP Status | Feature | Cause | Retry? |
|---|---|---|---|---|
| `INVALID_FILE_TYPE` | 400 | F00 | File extension or MIME type not PDF/TXT/DOCX | No — fix file type |
| `FILE_TOO_LARGE` | 400 | F00 | File exceeds 50MB | No — use smaller file |
| `SESSION_STORAGE_LIMIT` | 400 | F00 | Session total uploads exceed 200MB | No — delete documents first |
| `SESSION_DOCUMENT_LIMIT` | 400 | F00 | Session already has 20 documents | No — delete documents first |
| `EMPTY_FILE` | 400 | F00 | Uploaded file is 0 bytes | No — fix file |
| `DOCUMENT_NOT_FOUND` | 404 | F00, F03 | document_id not in session or cross-session access | No |
| `INDEX_DELETE_ERROR` | 500 | F03 | Vector store failed to purge document chunks | Yes — retry delete |
| `PARSE_ERROR` | async (stored in status) | F00 | Text extraction from file failed | Yes — retry upload |
| `NO_TEXT_LAYER` | async (stored in status) | F00 | PDF is image-only; no extractable text | No — OCR not supported in v1 |
| `EMBED_ERROR` (ingestion) | async (stored in status) | F00 | Embedding API unavailable during ingestion | Yes — retry upload after delay |
| `INDEX_ERROR` | async (stored in status) | F00 | Vector store write failed during ingestion | Yes — retry upload |
| `EMPTY_DOCUMENT` | async (stored in status) | F00 | File parsed but produced zero text characters | No — use a different file |

*Note: Async errors do not produce HTTP error responses — they update the document `status` to `error` and set `error_reason`. The frontend discovers them via status polling (F00 §Process step 9).*

---

### Query & Answer Errors (F01, F06)

| Error Code | HTTP Status | Feature | Cause | Retry? |
|---|---|---|---|---|
| `EMPTY_QUERY` | 400 | F01 | Query is empty or whitespace-only | No — provide query |
| `QUERY_TOO_LONG` | 400 | F01 | Query exceeds 2000 characters | No — shorten query |
| `NO_READY_DOCUMENTS` | 422 | F01 | No documents with status `ready` in session | No — wait for indexing or upload |
| `QUERY_IN_PROGRESS` | 429 | F01 | Another query stream is active for this session | Yes — wait for current query to complete |
| `EMBED_ERROR` (query) | 503 | F01 | Embedding API unavailable during query embedding | Yes — retry after 5s |
| `LLM_UNAVAILABLE` | 503 | F01 | LLM API call failed after retries | Yes — retry after 10s |
| `LLM_TIMEOUT` | 504 | F01 | LLM response exceeded 30s timeout | Yes — retry |
| `RETRIEVAL_ERROR` | 503 | F01 | Vector store query failed | Yes — retry after 5s |
| `DOCUMENT_NOT_READY` | 422 | F06 | document_filter references a non-ready document | No — wait for indexing |
| `DOCUMENT_NOT_IN_INDEX` | 422 | F06 | Filtered document has no indexed chunks | No — re-upload document |

---

### Chat History & Session Errors (F04)

| Error Code | HTTP Status | Feature | Cause | Retry? |
|---|---|---|---|---|
| `SESSION_NOT_FOUND` | 404 | F04, all | Session cookie absent or session expired | No — a new session is created on next GET |
| `INVALID_EXPORT_FORMAT` | 400 | F08 | Export format parameter not "text" or "markdown" | No — fix parameter |

*Note: `GET /api/documents`, `GET /api/chat/history`, and `POST /api/session/reset` never return SESSION_NOT_FOUND — they create a new session instead.*

---

### Feedback Errors (F07)

| Error Code | HTTP Status | Feature | Cause | Retry? |
|---|---|---|---|---|
| `INVALID_RATING` | 400 | F07 | Rating is not "positive" or "negative" | No — fix value |
| `INVALID_MESSAGE_ROLE` | 400 | F07 | Feedback submitted for a user-role message | No |
| `FEEDBACK_ALREADY_SUBMITTED` | 409 | F07 | Message already has a rating | No — one rating per message |
| `MESSAGE_NOT_FOUND` | 404 | F07 | message_id not found in session | No |

---

### Infrastructure Errors

| Error Code | HTTP Status | Feature | Cause | Retry? |
|---|---|---|---|---|
| `INTERNAL_SERVER_ERROR` | 500 | All | Unexpected server error | Yes — retry; report if persistent |
| `SERVICE_DEGRADED` | 503 | Health | One or more backend dependencies unavailable | Yes — retry after delay |

---

### HTTP Status Code Summary

| Status | Used For |
|---|---|
| 200 | Successful GET, POST (feedback, session reset), export |
| 202 | Document upload accepted (async ingestion begins) |
| 204 | Successful DELETE (no body) |
| 400 | Client input validation errors |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate feedback) |
| 422 | Semantic validation errors (e.g., no ready documents) |
| 429 | Rate limit / in-progress conflict |
| 500 | Server-side unexpected errors |
| 503 | External dependency unavailable |
| 504 | Gateway/LLM timeout |

---

### Client Error Handling Guidelines

1. **400 errors:** Display the `message` field to the user verbatim. Do not retry automatically.
2. **404 errors on documents/messages:** Remove the stale item from the UI; it may have been deleted in another tab.
3. **422 NO_READY_DOCUMENTS:** Disable the chat input; show "Upload and index a document to get started."
4. **429 QUERY_IN_PROGRESS:** Disable the send button until the current stream completes; no user-visible error needed.
5. **503/504 errors:** Show a transient error message with a "Retry" button; do not immediately retry automatically.
6. **Async document errors (status=error):** Show an error badge on the document card with the human-readable reason and a "Retry Upload" button.
7. **SSE stream errors:** If the SSE connection drops mid-stream, show an error bubble: "Answer generation was interrupted. Please try again."
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
