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
