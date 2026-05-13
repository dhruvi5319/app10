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
