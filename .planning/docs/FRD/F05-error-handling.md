
---

## F05: System Feedback & Error Handling

**Priority:** P1 — High, MVP  
**PRD Reference:** §6 F5

**Description:** The application provides clear, actionable feedback to users at every step of the upload and Q&A workflow. Error handling ensures that any degraded state — unsupported file, oversized upload, LLM outage, network failure — is communicated in plain language with a recovery path. The system never leaves the user staring at a silent spinner or a cryptic HTTP status code. Feedback covers both happy-path progress (upload stages, typing indicator) and all failure conditions across F00–F04.

---

### Terminology

- **Toast Notification:** A transient, non-blocking UI overlay that appears in a corner of the screen and auto-dismisses after 4–6 seconds. Used for non-critical confirmations and errors.
- **Inline Error:** An error message displayed within the relevant UI component (e.g., below the upload zone or input bar), persisting until the user takes corrective action.
- **Progress Stage:** One of the named processing steps shown during document ingestion: `UPLOADING → PARSING → CHUNKING → EMBEDDING → INDEXING → READY`.
- **Retry CTA:** A "Try again" button or link rendered within an error message that re-triggers the failed action.
- **Graceful Degradation:** The system continues to function for available features when one subsystem (e.g., LLM API) is unavailable.
- **Guard Message:** A proactive message shown before an error occurs, e.g., preventing empty query submission.

---

### Sub-features

- **F05-A:** Upload progress bar / stage indicator
- **F05-B:** Inline file validation errors (type, size)
- **F05-C:** LLM error toast with retry option
- **F05-D:** Empty query guard (disabled send button)
- **F05-E:** No-documents guard message for chat
- **F05-F:** Network error detection and retry suggestion
- **F05-G:** Processing failure indicator per document in the panel

---

### Process

#### Upload Feedback (F05-A, F05-B, F05-G)

1. When a user selects or drops files, **frontend** immediately validates each file client-side (type, size).
2. Files failing client-side validation receive an **inline error** beneath the upload zone: e.g., "report.exe — Unsupported file type. Only PDF, TXT, and DOCX are accepted."
3. Valid files are submitted to the backend. The upload zone displays a progress bar per file, labelled with the current stage.
4. Stages are updated via SSE events or polling (see F00 §Process step 11): `UPLOADING (0%)` → `PARSING` → `CHUNKING` → `EMBEDDING (X%)` → `INDEXING` → `READY ✓`.
5. On `READY`, the progress bar completes and is replaced by a green checkmark + filename in the Document Panel.
6. On `FAILED`, the progress bar turns red, the stage label shows "Failed", and an **inline error** appears with a specific message (e.g., "Could not parse this PDF — it may be password-protected.") and a Retry upload button.

#### Chat Query Guard (F05-D, F05-E)

7. The Send button is **disabled** (greyed out, not clickable) whenever:
   - The query input is empty or contains only whitespace.
   - A previous query is currently in-flight (awaiting LLM response).
8. If the user attempts to submit (e.g., presses Enter) while no documents are ready, **frontend** displays an **inline guard message** above the input bar: "Upload a document first to start asking questions."
9. This guard message auto-dismisses when the first document reaches `READY` status.

#### LLM Error Handling (F05-C)

10. If the LLM API returns an error or times out during a query, **frontend** receives the error response from the backend.
11. The typing indicator is removed. The assistant bubble that was forming is replaced with an error message in the chat thread: "I couldn't generate a response right now. [Try again]"
12. A **toast notification** appears in the top-right corner: "AI service error — please try again." with an auto-dismiss timer.
13. The "Try again" link in the error bubble re-submits the same query without requiring the user to retype it.

#### Network Error Handling (F05-F)

14. **Frontend** detects network failures (fetch throws `TypeError: Failed to fetch` or equivalent) for any API call.
15. A persistent **toast or banner** appears: "Connection lost. Check your network and [retry]."
16. Retry triggers the same API call. If successful, the toast dismisses and normal operation resumes.

---

### Inputs

| Signal | Source | Action Triggered |
|--------|--------|-----------------|
| File extension invalid | User file selection | Inline error, file rejected |
| File > 20 MB | User file selection | Inline error, file rejected |
| Backend `FAILED` status | SSE / polling | Document card error state |
| Backend `422` / `413` | Upload response | Inline error in upload zone |
| Backend `503` (LLM) | Chat query response | Error bubble + toast |
| Backend `429` (rate limit) | Chat query response | Error bubble + retry hint |
| `fetch` network error | Any API call | Network error banner |
| Empty input field | User interaction | Send button disabled |
| No ready documents | User attempts query | Guard message above input |

---

### Outputs

**Progress event (SSE, during upload):**
```json
{
  "type": "progress",
  "doc_id": "uuid-v4",
  "stage": "EMBEDDING",
  "progress_pct": 65,
  "message": "Embedding chunk 27 of 42..."
}
```

**Error event (SSE, upload failure):**
```json
{
  "type": "error",
  "doc_id": "uuid-v4",
  "stage": "PARSING",
  "error_code": "PARSE_FAILURE",
  "message": "Could not parse the document. The file may be corrupt or password-protected."
}
```

**Chat error response (500 / 503):**
```json
{
  "error_code": "LLM_UNAVAILABLE",
  "message": "The AI service is currently unavailable. Please check your configuration.",
  "retryable": true
}
```

---

### Validation Rules

- The Send button state (enabled/disabled) must be computed reactively from: `inputIsNonEmpty && hasReadyDocument && !queryInFlight`.
- Inline file errors must list both the filename and the specific reason for rejection.
- All error messages surfaced to the user must be in plain language — no HTTP status codes, stack traces, or internal error codes visible in the UI.
- Error codes (e.g., `PARSE_FAILURE`) are transmitted in the API response body for logging/debugging but are never displayed in the UI.
- The Retry CTA for a failed upload must re-submit the same file bytes without requiring the user to re-select the file.
- Toast notifications must auto-dismiss after 5 seconds for informational messages and must persist (require manual dismiss) for error messages where user action is required.
- Stage progress percentages during EMBEDDING are calculated as `(chunks_embedded / total_chunks) * 100`; other stages are displayed as indeterminate spinners.

---

### Error States

| Scenario | HTTP Status | Error Code | UI Feedback |
|----------|-------------|------------|-------------|
| Client-side type rejection | — | `INVALID_FILE_TYPE` | Inline error below upload zone |
| Client-side size rejection | — | `FILE_TOO_LARGE` | Inline error below upload zone |
| Server-side MIME rejection | 422 | `INVALID_MIME_TYPE` | Inline error on document card |
| Server-side size rejection | 413 | `FILE_TOO_LARGE` | Inline error on document card |
| Parse failure (corrupt file) | 422 | `PARSE_FAILURE` | Document card "Failed" + inline message |
| No extractable text (image PDF) | 422 | `NO_EXTRACTABLE_TEXT` | Document card "Failed" + inline message |
| Document limit reached | 422 | `DOCUMENT_LIMIT_REACHED` | Inline error in upload zone |
| LLM unavailable | 503 | `LLM_UNAVAILABLE` | Error bubble in chat + toast |
| LLM rate limited | 429 | `LLM_RATE_LIMIT` | Error bubble in chat + retry link |
| Embedding unavailable | 503 | `EMBEDDING_UNAVAILABLE` | Document card "Failed" + toast |
| Network failure (any call) | — | — | Persistent network error banner |
| Empty query attempt | — | — | Send button disabled (no message shown) |
| Query with no ready documents | — | — | Guard message above input bar |

---

### API Surface (this feature)

Error states are returned by the endpoints defined in F00, F01, F03, F04. No dedicated error endpoints exist. See `Y2-errors.md` for the complete cross-feature error catalog with all HTTP status codes and error code strings.

---

### Schema Surface (this feature)

No additional schema tables. Error events are ephemeral SSE payloads and are not persisted. Document `status` field covers the `FAILED` state in the `documents` record.

Full DDL → `Y0-schema.md §Documents`
