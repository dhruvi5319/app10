
---

## F03: Document Management Panel

**Priority:** P1 — High, MVP  
**PRD Reference:** §6 F3

**Description:** A document library panel in the application UI lists all documents currently indexed in the session, allowing users to inspect what context is available and remove documents they no longer need. When a document is deleted, all associated chunks and embeddings are purged from the vector store so it no longer influences subsequent answers. The panel provides an empty state guide for new sessions and collapses on small screens to maximise chat area.

---

### Terminology

- **Document Panel:** A sidebar or bottom-sheet UI component listing all uploaded documents for the current session.
- **Document Card:** A list item in the panel representing one document; displays filename, file type icon, status badge, and upload timestamp.
- **Deletion:** Complete removal of a document's metadata record, stored file, text chunks, and vector store embeddings from the session.
- **Empty State:** The panel's display when no documents have been uploaded yet in the session.
- **Collapsible Panel:** The panel can be toggled hidden/visible; on desktop, it collapses to a narrow icon strip; on mobile it becomes a bottom drawer.

---

### Sub-features

- **F03-A:** Document list with filename, type icon, status, and timestamp
- **F03-B:** Delete button per document with confirmation dialog
- **F03-C:** Empty state message with upload call-to-action
- **F03-D:** Document count and storage summary in panel header
- **F03-E:** Collapsible panel behaviour

---

### Process

1. **Frontend** renders the Document Panel on the left sidebar (desktop) or as a bottom drawer toggle (mobile).
2. On session load, **frontend** calls `GET /api/documents?session_id={session_id}` to fetch the current document list.
3. **Frontend** renders one Document Card per document:
   - File type icon (PDF 🟥 / DOCX 🟦 / TXT 🟩)
   - Filename (truncated with ellipsis if > 30 chars; full name in tooltip)
   - Status badge: `READY` (green), `PROCESSING` (yellow spinner), `FAILED` (red)
   - Upload timestamp (relative: "2 minutes ago")
   - Delete icon button (disabled while document status is `PROCESSING`)
4. **Panel header** shows: "Documents (N / 10)" and total storage used in KB/MB.
5. **User** clicks the delete icon on a Document Card.
6. **Frontend** displays a confirmation dialog: "Delete {filename}? This will remove it from the current session and it cannot be undone." with `Cancel` and `Delete` buttons.
7. **User** confirms deletion. **Frontend** sends `DELETE /api/documents/{doc_id}?session_id={session_id}`.
8. **Backend** validates `doc_id` belongs to `session_id`, then:
   a. Deletes all chunk embeddings for `doc_id` from the vector store collection `session_{session_id}`.
   b. Deletes all `chunks` records for `doc_id`.
   c. Deletes the `documents` record.
   d. Removes the uploaded file from `uploads/{session_id}/{doc_id}/`.
9. **Backend** returns `200 OK` with `{"deleted": true, "doc_id": "..."}`.
10. **Frontend** removes the Document Card from the panel with a fade-out animation and decrements the document counter.
11. If all documents are deleted, the panel transitions to the **empty state**: "No documents uploaded yet. Drag a file here or click to upload."
12. **User** can click the collapse toggle to hide/show the panel. State is preserved in local storage for the session.

---

### Inputs

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `session_id` | string (UUID) | Yes | Active session |
| `doc_id` | string (UUID) | Yes (for delete) | Must belong to the provided `session_id` |

---

### Outputs

**GET /api/documents response (200 OK):**
```json
{
  "session_id": "uuid-v4",
  "document_count": 3,
  "total_size_bytes": 5242880,
  "documents": [
    {
      "doc_id": "uuid-v4",
      "filename": "report.pdf",
      "file_type": "pdf",
      "file_size_bytes": 1048576,
      "status": "READY",
      "chunk_count": 42,
      "page_count": 12,
      "uploaded_at": "2026-05-13T10:00:00Z"
    }
  ]
}
```

**DELETE /api/documents/{doc_id} response (200 OK):**
```json
{
  "deleted": true,
  "doc_id": "uuid-v4"
}
```

---

### Validation Rules

- The delete operation must verify `doc_id` belongs to the requesting `session_id` before deletion (no cross-session deletions).
- Delete must be an atomic operation: if vector store deletion fails, the metadata record must not be deleted (transaction-like approach; log the failure and surface error).
- The delete icon must be disabled (non-clickable, visually muted) while a document's status is `PROCESSING` or `UPLOADING`.
- Panel must refresh (re-fetch or update from state) after each successful upload (new card appears) and deletion (card removed).
- Document filenames longer than 30 characters must be truncated in the card display with an ellipsis; the full filename must be accessible via a tooltip (HTML `title` attribute or tooltip component).
- Status badges must accurately reflect the server-side status; frontend must poll `GET /api/documents/{doc_id}/status` for documents in `PROCESSING` state until they reach `READY` or `FAILED`.

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|----------|-------------|------------|---------|
| `doc_id` not found | 404 | `DOCUMENT_NOT_FOUND` | "Document not found." |
| `doc_id` does not belong to `session_id` | 403 | `DOCUMENT_ACCESS_DENIED` | "You do not have access to this document." |
| Delete fails (vector store error) | 500 | `DELETE_VECTOR_STORE_FAILURE` | "Could not fully remove the document. Please try again." |
| Delete fails (file system error) | 500 | `DELETE_FILE_FAILURE` | "Could not remove the document file. Please try again." |
| Fetch documents fails | 500 | `FETCH_DOCUMENTS_FAILURE` | "Could not load your documents. Please refresh." |

---

### API Surface (this feature)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/documents` | List all documents for a session |
| `DELETE` | `/api/documents/{doc_id}` | Delete document and all associated data |

Full request/response schemas → `Y1-api.md §Documents`

---

### Schema Surface (this feature)

Uses tables/collections:
- `documents` — metadata record (deleted on remove)
- `chunks` — text chunk records (deleted on remove)
- ChromaDB `session_{session_id}` — embeddings deleted by `doc_id` filter

Full DDL → `Y0-schema.md §Documents`
