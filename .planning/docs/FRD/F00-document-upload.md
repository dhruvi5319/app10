
---

## F00: Document Upload & Ingestion Pipeline

**Priority:** P0 — Critical, MVP  
**PRD Reference:** §6 F0

**Description:** Users upload one or more documents (PDF, TXT, or DOCX) through the frontend's drag-and-drop or click-to-browse interface. The backend receives each file, validates it, parses it into plain text, splits the text into overlapping chunks, embeds each chunk, and stores the embeddings and metadata in the session-scoped vector store collection. This pipeline is the foundational prerequisite for all question-answering functionality — no Q&A is possible until at least one document reaches `READY` status.

---

### Terminology

- **Ingest Job:** A server-side processing task for a single uploaded document, tracked through stages `UPLOADING → PARSING → CHUNKING → EMBEDDING → INDEXING → READY`.
- **Chunk Overlap:** The number of tokens shared between consecutive chunks to preserve context at chunk boundaries (default: 50 tokens).
- **Page Number:** A 1-based integer identifying the source PDF page from which a chunk was extracted. `null` for TXT and DOCX (no inherent pagination).
- **File Header Validation:** Magic-byte inspection to confirm true file type regardless of extension, preventing extension-spoofing attacks.

---

### Sub-features

- **F00-A:** Drag-and-drop upload zone on the frontend
- **F00-B:** Click-to-browse file picker fallback
- **F00-C:** Multi-file upload in a single interaction
- **F00-D:** Backend file validation (type, size, structure)
- **F00-E:** Document parsing (PDF → PyMuPDF, DOCX → python-docx, TXT → utf-8)
- **F00-F:** Text chunking (overlapping token-based segments)
- **F00-G:** Embedding generation per chunk
- **F00-H:** Vector store indexing with metadata
- **F00-I:** Real-time upload progress reporting to frontend

---

### Process

1. **Frontend** renders an upload zone accepting `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, and `text/plain` MIME types.
2. **User** drags files onto the zone or clicks to open a file picker; selects one or more files.
3. **Frontend** validates each file client-side: checks extension (`.pdf`, `.txt`, `.docx`) and size (≤ 20 MB). Files failing this check display an inline error immediately without sending to the server.
4. **Frontend** sends a `POST /api/documents/upload` multipart/form-data request containing the file and `session_id`.
5. **Backend** validates the file server-side: MIME type (magic-byte check), size, and document count per session (≤ 10). Rejects with `422` on violation (see Error States).
6. **Backend** assigns a `doc_id` (UUID v4), saves the raw file to `uploads/{session_id}/{doc_id}/{filename}`, and creates a document record with status `PARSING`.
7. **Backend** parses the file to plain text:
   - PDF: extracts text page-by-page using PyMuPDF; records page boundaries.
   - DOCX: extracts paragraph and table text using python-docx.
   - TXT: reads the file as UTF-8; falls back to `latin-1` if UTF-8 decode fails.
8. **Backend** splits text into overlapping chunks using a token-based splitter (default: 500 tokens per chunk, 50-token overlap). Each chunk records `chunk_index` and `page_number` (null for TXT/DOCX).
9. **Backend** calls the embedding model API for each chunk (batched in groups of up to 100 chunks). Retries up to 3 times with exponential backoff on rate-limit errors.
10. **Backend** upserts each chunk's embedding and metadata into the vector store collection named `session_{session_id}`.
11. **Backend** updates the document record status to `READY` and returns the completed document object to the frontend via the response (or a polling/SSE endpoint).
12. **Frontend** displays a success indicator (green checkmark + filename) and adds the document to the Document Management Panel (see F03).

---

### Inputs

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `file` | multipart file | Yes | PDF, TXT, or DOCX; ≤ 20 MB; valid magic bytes |
| `session_id` | string (UUID) | Yes | Must match an active session |

---

### Outputs

**Success (201 Created):**
```json
{
  "doc_id": "uuid-v4",
  "session_id": "uuid-v4",
  "filename": "report.pdf",
  "file_type": "pdf",
  "file_size_bytes": 1048576,
  "status": "READY",
  "chunk_count": 42,
  "page_count": 12,
  "uploaded_at": "2026-05-13T10:00:00Z"
}
```

**Progress (SSE / polling, during processing):**
```json
{
  "doc_id": "uuid-v4",
  "status": "EMBEDDING",
  "progress_pct": 65,
  "message": "Embedding chunk 27 of 42..."
}
```

---

### Validation Rules

- File extension must be one of `.pdf`, `.txt`, `.docx` (case-insensitive).
- File MIME type detected via magic bytes must match: PDF → `application/pdf`, DOCX → `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, TXT → `text/plain` or starts with `text/`.
- File size must be ≤ 20 MB (20,971,520 bytes).
- Session must not already contain 10 documents (≤ 9 existing documents to allow one more).
- Uploaded file must not be an empty file (0 bytes).
- Parsed text must not be empty after extraction (some PDFs are image-only scans with no extractable text).
- `session_id` must be a valid UUID v4 matching a known active session.
- Duplicate filenames within a session are permitted (different `doc_id` assigned each time).

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|----------|-------------|------------|---------|
| Unsupported file type (client-side) | — (client only) | `INVALID_FILE_TYPE` | "Only PDF, TXT, and DOCX files are supported." |
| Unsupported MIME type (server-side) | 422 | `INVALID_MIME_TYPE` | "File type not accepted. Supported: PDF, TXT, DOCX." |
| File exceeds 20 MB | 413 | `FILE_TOO_LARGE` | "File exceeds the 20 MB limit. Please reduce the file size." |
| Session document limit reached | 422 | `DOCUMENT_LIMIT_REACHED` | "Maximum of 10 documents per session. Delete a document to upload another." |
| Empty file uploaded | 422 | `EMPTY_FILE` | "The uploaded file is empty." |
| PDF has no extractable text | 422 | `NO_EXTRACTABLE_TEXT` | "This PDF appears to be image-only and contains no extractable text." |
| Embedding API rate limit (after retries) | 502 | `EMBEDDING_RATE_LIMIT` | "Embedding service is temporarily busy. Please try again in a moment." |
| Embedding API unavailable | 503 | `EMBEDDING_UNAVAILABLE` | "Embedding service is unavailable. Check API key configuration." |
| File parse failure (corrupt file) | 422 | `PARSE_FAILURE` | "Could not parse the document. The file may be corrupt or password-protected." |
| Session not found | 404 | `SESSION_NOT_FOUND` | "Session not found. Please refresh the page to start a new session." |

---

### API Surface (this feature)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents/upload` | Upload and ingest a document |
| `GET` | `/api/documents/{doc_id}/status` | Poll ingestion progress |
| `GET` | `/api/documents/upload/stream` | SSE stream of ingestion progress |

Full request/response schemas → `Y1-api.md §Documents`

---

### Schema Surface (this feature)

Uses tables/collections:
- `documents` — document metadata record per session
- `chunks` — text chunk metadata (text, chunk_index, page_number, doc_id)
- ChromaDB collection `session_{session_id}` — chunk embeddings + metadata

Full DDL → `Y0-schema.md §Documents`
