
---

## F00: Document Upload & Ingestion Pipeline

**Priority:** P0 — Critical MVP  
**PRD Reference:** §6 F0

**Description:** This feature accepts one or more documents (PDF, TXT, DOCX) from the user via drag-and-drop or file-browser upload, validates them, then executes the full ingestion pipeline: parse → chunk → embed → store in vector DB. It is the foundational pipeline that enables all question-answering. The frontend tracks upload and processing progress in real time, and the user receives explicit success or failure feedback per document.

---

### Terminology

- **Ingestion Pipeline:** The ordered sequence of parse → chunk → embed → store that transforms a raw file into retrievable embeddings.
- **Parser:** A format-specific library that converts binary file bytes into a plain-text string. PyMuPDF for PDF, python-docx for DOCX, UTF-8 read for TXT.
- **Chunker:** The component that splits parsed text into overlapping fixed-size segments using LangChain's `RecursiveCharacterTextSplitter` or equivalent.
- **Embedder:** The component that calls the embedding model API (OpenAI or sentence-transformers) to convert chunk text into float vectors.
- **Document Metadata:** Structured attributes stored alongside each chunk: `document_id`, `filename`, `file_type`, `chunk_index`, `page_number` (PDF only), `session_id`, `uploaded_at`.
- **Ingestion Status:** The frontend-visible lifecycle state of a document: `uploading` → `parsing` → `chunking` → `embedding` → `ready` | `error`.

---

### Sub-features

- **F00.1 — Drag-and-Drop Upload Area:** A drop zone component on the frontend that accepts dragged files and visually highlights on drag-over.
- **F00.2 — Click-to-Browse Fallback:** A hidden `<input type="file">` triggered by clicking the upload area, supporting multi-file selection.
- **F00.3 — Client-Side Pre-validation:** File type extension check and file size check before the request is sent to the backend.
- **F00.4 — Backend Validation:** MIME type verification and file size enforcement at the API layer before parsing begins.
- **F00.5 — Document Parsing:** Format-aware text extraction from binary file content.
- **F00.6 — Text Chunking:** Splitting extracted text into overlapping token-bounded segments.
- **F00.7 — Chunk Embedding:** Calling the embedding model to produce float vectors for each chunk.
- **F00.8 — Vector Store Indexing:** Persisting chunk text, embeddings, and metadata into ChromaDB (or FAISS fallback).
- **F00.9 — Progress Streaming:** Server-Sent Events (SSE) or polling endpoint to stream ingestion stage updates to the frontend.
- **F00.10 — Per-Document Status Feedback:** Displaying success (filename, chunk count) or failure (error message) per uploaded file.

---

### Process

1. User drags one or more files onto the upload drop zone, or clicks to browse and selects files.
2. **Client-side pre-validation (F00.3):**
   - For each file: check file extension against allowlist `[.pdf, .txt, .docx]`.
   - Check file size ≤ 20 MB.
   - If any file fails: display inline error for that file; remove it from the upload queue; continue processing remaining valid files.
3. Frontend shows each valid file in a pending state with a progress bar at 0%.
4. Frontend sends `POST /api/documents/upload` as `multipart/form-data` with all valid files and the session ID.
5. **Backend validation (F00.4):**
   - Verify `session_id` header is present and valid UUID format.
   - Verify each file's MIME type matches its extension (see Validation section).
   - Verify each file size ≤ 20 MB (server-side re-check).
   - Verify total documents in session ≤ 10 (after this upload).
   - If validation fails for a file, add it to the error list; continue processing remaining files.
6. For each valid file, the backend begins the ingestion pipeline asynchronously (one file at a time or concurrently per config):
   - **a. Parse (F00.5):** Invoke format-specific parser. Extract full text. For PDFs, track page numbers per extracted text segment.
   - **b. Chunk (F00.6):** Split text using `RecursiveCharacterTextSplitter` with `chunk_size=CHUNK_SIZE`, `chunk_overlap=CHUNK_OVERLAP` (from config). Assign `chunk_index` (0-based) to each chunk.
   - **c. Embed (F00.7):** Batch-call the embedding model API with all chunk texts. Retry with exponential backoff on rate-limit errors (max 3 retries).
   - **d. Store (F00.8):** Upsert chunk text, embedding vector, and metadata into the vector store collection keyed by `session_id`.
7. After each pipeline stage completes per file, emit a progress event (stage name + percentage) to the frontend polling endpoint.
8. On pipeline completion: update the document record status to `ready`; return `document_id`, `filename`, `chunk_count`.
9. Frontend updates the document's status card to show a green checkmark, filename, and chunk count.
10. On any pipeline failure: mark document status `error`; return structured error; frontend shows red status with error message.

---

### Inputs

- `files` (multipart file list, required): One or more files attached to the `multipart/form-data` POST body.
- `session_id` (string/UUID, required): Passed in the `X-Session-ID` request header. Identifies the session context.
- `CHUNK_SIZE` (integer, from config): Maximum tokens per chunk. Default: 500.
- `CHUNK_OVERLAP` (integer, from config): Overlap tokens between adjacent chunks. Default: 50.
- `EMBEDDING_MODEL` (string, from config): Embedding model name. Default: `text-embedding-3-small`.
- `MAX_FILE_SIZE_MB` (integer, from config): Per-file size cap. Default: 20.
- `MAX_DOCS_PER_SESSION` (integer, from config): Max documents per session. Default: 10.

---

### Outputs

**On success (HTTP 200):**
```json
{
  "results": [
    {
      "document_id": "uuid-string",
      "filename": "contract.pdf",
      "status": "ready",
      "chunk_count": 42,
      "page_count": 12,
      "uploaded_at": "2026-05-13T10:30:00Z"
    }
  ],
  "errors": []
}
```

**On partial failure (HTTP 207 Multi-Status):**
```json
{
  "results": [
    { "document_id": "uuid", "filename": "valid.pdf", "status": "ready", "chunk_count": 18 }
  ],
  "errors": [
    { "filename": "bad.exe", "error_code": "UNSUPPORTED_FILE_TYPE", "message": "File type .exe is not supported. Accepted: PDF, TXT, DOCX." }
  ]
}
```

**Progress event (SSE or polling, per file):**
```json
{ "document_id": "uuid", "filename": "report.pdf", "stage": "embedding", "progress_pct": 60 }
```

---

### Validation Rules

- File extension must be one of: `.pdf`, `.txt`, `.docx` (case-insensitive check on extension).
- MIME type must match extension:
  - `.pdf` → `application/pdf`
  - `.txt` → `text/plain`
  - `.docx` → `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- File size must be ≤ 20 MB (20 × 1,048,576 bytes).
- Session must not exceed 10 documents total after this upload. If uploading 3 files would bring the total to 11, reject the files that would exceed the cap (in order), not the entire batch.
- `session_id` must be a valid UUID v4 format.
- Parsed text must not be empty after extraction (empty document → `EMPTY_DOCUMENT` error).
- Chunk count after chunking must be ≥ 1.
- Filename must be ≤ 255 characters.
- Duplicate filename within the same session is allowed (documents are de-duplicated by `document_id`, not filename).

---

### Error States

| Scenario | HTTP Status | Error Code | User Message |
|----------|-------------|------------|-------------|
| File extension not in allowlist | 400 | `UNSUPPORTED_FILE_TYPE` | "File type `{ext}` is not supported. Upload PDF, TXT, or DOCX files." |
| File size exceeds 20 MB | 400 | `FILE_TOO_LARGE` | "File `{filename}` exceeds the 20 MB limit ({actual_size} MB)." |
| MIME type doesn't match extension | 400 | `MIME_TYPE_MISMATCH` | "File `{filename}` appears to be corrupt or misnamed. Check the file and try again." |
| Session document limit (10) reached | 400 | `SESSION_DOC_LIMIT_REACHED` | "You have reached the 10-document limit for this session. Delete a document to upload more." |
| Missing or invalid session ID | 400 | `INVALID_SESSION` | "Session not found. Refresh the page to start a new session." |
| Parsed text is empty | 422 | `EMPTY_DOCUMENT` | "No readable text found in `{filename}`. The file may be image-only or password-protected." |
| Parsing library throws exception | 500 | `PARSE_FAILED` | "Failed to parse `{filename}`. The file may be corrupt." |
| Embedding API rate limit exceeded (after retries) | 503 | `EMBEDDING_RATE_LIMIT` | "Indexing is temporarily delayed due to high demand. Please try again in a moment." |
| Embedding API unavailable | 503 | `EMBEDDING_UNAVAILABLE` | "The embedding service is unavailable. Check your API key and network connection." |
| Vector store write failure | 500 | `VECTOR_STORE_ERROR` | "Failed to index `{filename}`. Please try uploading again." |
| No files included in request | 400 | `NO_FILES_PROVIDED` | "No files were included in the upload request." |

---

### API Surface (this feature)

See `Y1-api.md` §Document Upload for full request/response schemas.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/documents/upload` | Upload and ingest one or more documents |
| `GET` | `/api/documents/upload/status/{document_id}` | Poll ingestion status for a specific document |

---

### Schema Surface (this feature)

Uses tables/collections: `documents`, `chunks` — see `Y0-schema.md` §Documents and §Chunks.

Key fields per chunk stored in vector store:
- `id` (chunk UUID)
- `document_id` (parent document UUID)
- `session_id`
- `text` (raw chunk text)
- `embedding` (float vector)
- `chunk_index` (integer, 0-based)
- `page_number` (integer or null)
- `filename`
- `file_type`

---
