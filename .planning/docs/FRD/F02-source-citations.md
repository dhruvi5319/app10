
---

## F02: Source Citation & Passage Highlighting

**Priority:** P0 — Critical, MVP  
**PRD Reference:** §6 F2

**Description:** Every assistant answer is accompanied by one or more citations that identify the exact source document and the verbatim passage used to generate the response. Citations are the product's primary trust mechanism — they allow users to independently verify every factual claim against the original document. Each citation displays the filename, page number (where available), and the raw text excerpt from the retrieved chunk. When an answer draws from multiple chunks or documents, all contributing citations are listed.

---

### Terminology

- **Citation:** A structured reference attached to an assistant message containing source document metadata and an excerpt of the chunk text that informed the answer.
- **Excerpt:** The verbatim text of a retrieved chunk, displayed in the citation card so users can read the exact passage used.
- **Citation Card:** A collapsible UI component rendered below an assistant message bubble, displaying one citation per retrieved chunk.
- **Inline Citation Marker:** An optional superscript marker `[1]`, `[2]` etc. placed within the answer text indicating which passage supports which statement (post-MVP enhancement; tracked here for design alignment).
- **Page Reference:** A 1-based page number from the source PDF. `N/A` for TXT and DOCX files.

---

### Sub-features

- **F02-A:** Citation data attached to every non-refusal assistant message
- **F02-B:** Citation cards rendered below each answer bubble
- **F02-C:** Expandable/collapsible citation section (collapsed by default)
- **F02-D:** Verbatim excerpt display in each citation card
- **F02-E:** Page number display for PDF sources
- **F02-F:** Multiple citations per answer (one card per contributing chunk)
- **F02-G:** Visual distinction between answer body and citation section

---

### Process

1. **Backend** completes answer generation (see F01 §Process steps 7–12). The `retrieved_chunks` list is already available from the retrieval step.
2. **Backend** includes the full `retrieved_chunks` array in the final message object returned to the frontend (see F01 §Outputs).
3. **Frontend** receives the final message object and inspects `retrieved_chunks`:
   - If `is_refusal` is `true` or `retrieved_chunks` is empty: renders no citation section.
   - Otherwise: renders a citation section below the assistant bubble.
4. **Frontend** renders a collapsible citation container labelled "Sources (N)" where N is the number of retrieved chunks.
5. For each chunk in `retrieved_chunks`, **frontend** renders a Citation Card containing:
   - **Header:** `📄 {filename}` — page `{page_number}` (or `page N/A` for non-PDF) — chunk `{chunk_index + 1}`
   - **Body:** The verbatim `excerpt` text in a visually distinct blockquote or grey card.
6. **User** may click the citation section header to expand/collapse all citation cards.
7. Citation section is visually separated from the answer body by a divider line; uses smaller font size and secondary colour to distinguish from the primary response.
8. If the same document contributes multiple chunks to an answer, each chunk is listed as a separate citation card (not collapsed or merged).

---

### Inputs

Citation data is derived entirely from the query response pipeline (F01). No additional user inputs are required specifically for citation display.

| Field (from F01 response) | Type | Description |
|--------------------------|------|-------------|
| `retrieved_chunks` | array | List of chunk objects used in answer generation |
| `retrieved_chunks[].filename` | string | Name of the source document |
| `retrieved_chunks[].page_number` | integer \| null | 1-based page number; null for TXT/DOCX |
| `retrieved_chunks[].chunk_index` | integer | 0-based chunk position within the document |
| `retrieved_chunks[].excerpt` | string | Verbatim text of the chunk (up to 500 tokens) |
| `retrieved_chunks[].doc_id` | string (UUID) | Source document identifier |
| `is_refusal` | boolean | If true, no citations are shown |

---

### Outputs

**UI output (rendered per answer):**
- A collapsible "Sources (N)" section beneath each non-refusal assistant bubble.
- N citation cards, one per retrieved chunk.
- Each card shows: document name, page reference, verbatim excerpt.

**No additional API endpoint required** — citation data is embedded in the message object from `POST /api/chat/query` and `GET /api/chat/stream/{message_id}`.

---

### Validation Rules

- Citations must only be shown when `is_refusal` is `false` and `retrieved_chunks` is non-empty.
- Excerpt text must be displayed verbatim — no truncation beyond the chunk's natural length (up to 500 tokens). If a chunk excerpt exceeds 800 characters, the card may show the first 800 characters followed by a "Show more" toggle.
- Page number must display as `N/A` when `page_number` is `null`; must not display `null` or `0` to the user.
- Citation cards must be rendered in the same order as `retrieved_chunks` in the response (i.e., ranked by cosine similarity, most relevant first).
- Every assistant message with `is_refusal: false` must have at least one citation; if `retrieved_chunks` is empty but `is_refusal` is false, this is a backend data integrity error that should be logged.
- Citation section must remain attached to its parent message — it must not reorder or detach when new messages arrive.

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|----------|-------------|------------|---------|
| `retrieved_chunks` empty for non-refusal answer | — (FE log only) | `CITATION_DATA_MISSING` | Frontend logs warning; displays "Source data unavailable for this answer." in citation area |
| Excerpt text missing for a chunk | — (FE defensive) | — | Frontend renders "[Excerpt unavailable]" in place of missing excerpt |
| Page number is `0` (invalid) | — (FE defensive) | — | Frontend renders `N/A` for any page_number ≤ 0 |

*No HTTP errors are specific to citation display — errors originate upstream in F01.*

---

### API Surface (this feature)

Citation data is embedded in the F01 message response. No dedicated citation endpoints exist in v1.

See `Y1-api.md §Chat` for the full message object schema including `retrieved_chunks`.

---

### Schema Surface (this feature)

Citation data is stored via the `retrieved_chunks` join table and `chunks` metadata table.

Full DDL → `Y0-schema.md §Chat` and `§Documents`
