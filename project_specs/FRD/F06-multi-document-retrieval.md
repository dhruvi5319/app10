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
