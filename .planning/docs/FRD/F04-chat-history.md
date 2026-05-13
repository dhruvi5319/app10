
---

## F04: Session-Scoped Chat History

**Priority:** P1 — High, MVP  
**PRD Reference:** §6 F4

**Description:** The conversation thread is preserved for the entire duration of the browser session. Users can scroll back through all prior questions and answers within the same session, maintaining research context across a long workflow. History is stored server-side in memory keyed by `session_id`. It does not persist across page refreshes in v1 — a refresh assigns a new `session_id` and resets all state. Users may also clear the chat thread without losing their uploaded documents.

---

### Terminology

- **Chat History:** The ordered list of all `user` and `assistant` messages within a session, stored server-side and rendered in the chat thread.
- **Message Turn:** A pair of one user message and one assistant response. Used as the unit when truncating history for the LLM context window.
- **Clear Chat:** A user-initiated action that deletes all messages from the session's chat history without deleting uploaded documents.
- **Auto-scroll:** Automatic scrolling of the chat thread to the most recent message after each new message is appended.
- **Session Reset:** Loss of chat history upon page refresh (v1 behaviour); a new `session_id` is assigned and the in-memory history is not recoverable.

---

### Sub-features

- **F04-A:** Full chat thread rendered from session history on load
- **F04-B:** Auto-scroll to latest message on new response
- **F04-C:** Scrollable message thread (older messages accessible by scrolling up)
- **F04-D:** Per-message timestamp display
- **F04-E:** Clear conversation button
- **F04-F:** History context injected into LLM prompt for conversational continuity (see F01 §Process step 9)

---

### Process

1. **Frontend** initialises on load, calls `GET /api/sessions` (or `POST /api/sessions` if no session cookie) to obtain or create a `session_id`.
2. **Frontend** calls `GET /api/chat/history/{session_id}` to fetch any existing messages (empty array for a new session).
3. **Frontend** renders the full chat thread from the returned message list, oldest first, most recent at the bottom.
4. **Frontend** auto-scrolls to the bottom of the thread on initial load and after each new message.
5. Each message bubble displays:
   - **User messages:** right-aligned, dark background, user avatar / "You" label.
   - **Assistant messages:** left-aligned, light background, bot avatar / "Assistant" label.
   - **Timestamp:** displayed below each bubble in a muted, small font (e.g., "10:03 AM").
6. When a new Q&A exchange completes (see F01 §Process), **backend** appends both the user message and the assistant message to the session's in-memory chat history list.
7. **Backend** includes up to the last N full turns (default `N=10`) in the LLM context window when constructing the grounding prompt. Oldest turns are dropped first if the context window would overflow.
8. **User** clicks the "Clear Chat" button (located in the chat panel header or toolbar).
9. **Frontend** shows a confirmation dialog: "Clear conversation? Your uploaded documents will not be affected." with `Cancel` and `Clear` buttons.
10. **User** confirms. **Frontend** sends `DELETE /api/chat/history/{session_id}`.
11. **Backend** clears the in-memory message list for the session. Returns `200 OK` with `{"cleared": true}`.
12. **Frontend** removes all message bubbles from the thread, showing the empty chat state: "Ask a question about your uploaded documents."
13. On page refresh, a new `session_id` is issued; prior history is irrecoverably lost (v1 scope; by design).

---

### Inputs

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `session_id` | string (UUID) | Yes | Must be an active in-memory session |

---

### Outputs

**GET /api/chat/history/{session_id} (200 OK):**
```json
{
  "session_id": "uuid-v4",
  "message_count": 4,
  "messages": [
    {
      "message_id": "uuid-v4",
      "role": "user",
      "content": "What is the payment term?",
      "is_refusal": null,
      "retrieved_chunks": null,
      "created_at": "2026-05-13T10:00:00Z"
    },
    {
      "message_id": "uuid-v4",
      "role": "assistant",
      "content": "The payment term is Net 30.",
      "is_refusal": false,
      "retrieved_chunks": [ { "...": "..." } ],
      "created_at": "2026-05-13T10:00:05Z"
    }
  ]
}
```

**DELETE /api/chat/history/{session_id} (200 OK):**
```json
{
  "cleared": true,
  "session_id": "uuid-v4"
}
```

---

### Validation Rules

- Chat history must be isolated per `session_id`; a request with one `session_id` must never receive messages from another session.
- Messages must be returned in chronological order (ascending `created_at`).
- Clearing chat history must only clear messages; it must not affect documents, embeddings, or the vector store collection.
- The "Clear Chat" button must not be enabled (or visible) when the chat thread is already empty.
- LLM context injection must cap history at the last N turns to avoid exceeding the model's context window; N defaults to 10 and is configurable (see F07).
- User messages with `content` that is empty or whitespace-only must not be stored in history (prevented upstream in F01 validation).

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|----------|-------------|------------|---------|
| Session not found (history fetch) | 404 | `SESSION_NOT_FOUND` | "Session not found. Please refresh to start a new session." |
| Session not found (clear history) | 404 | `SESSION_NOT_FOUND` | "Session not found. Please refresh to start a new session." |
| Internal error saving message | 500 | `HISTORY_WRITE_FAILURE` | Logged server-side; non-blocking — answer still returned to user |
| History fetch failure | 500 | `HISTORY_FETCH_FAILURE` | "Could not load chat history. Showing an empty thread." |

---

### API Surface (this feature)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/chat/history/{session_id}` | Retrieve all messages for session |
| `DELETE` | `/api/chat/history/{session_id}` | Clear all messages for session |
| `POST` | `/api/sessions` | Create a new session (returns `session_id`) |
| `GET` | `/api/sessions/{session_id}` | Validate / retrieve session info |

Full request/response schemas → `Y1-api.md §Sessions` and `§Chat`

---

### Schema Surface (this feature)

Uses in-memory structures (not persisted in v1):
- `sessions` — in-memory dict keyed by `session_id`; contains message list and document list
- `messages` — in-memory list within each session entry

No on-disk schema for chat history in v1. Full in-memory structure documented in `Y0-schema.md §In-Memory State`
