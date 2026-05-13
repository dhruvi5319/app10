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
