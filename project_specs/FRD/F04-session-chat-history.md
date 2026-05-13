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
