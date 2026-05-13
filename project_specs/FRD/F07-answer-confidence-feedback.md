---

## F07: Answer Confidence & Relevance Feedback

**Priority:** P2 — Post-MVP  
**PRD Reference:** §5 F7

**Description:** The system surfaces a confidence signal alongside each answer to help users understand when the retrieved document context is strong or weak. A low-confidence indicator is shown when retrieval scores fall below the threshold, guiding users to rephrase or upload better source material. Users can also rate each answer with a thumbs-up or thumbs-down, which is recorded in session state to support future quality analysis. Neither the confidence signal nor feedback results influence the v1 answer generation itself — they are observability and UX trust tools.

---

### Terminology

- **Confidence Signal:** A visual indicator (badge, icon, or color) attached to each assistant message reflecting the strength of retrieved context.
- **High Confidence:** All retrieved chunks have similarity ≥ the session's `confidence_threshold` (default 0.30); top-1 similarity ≥ 0.60.
- **Low Confidence:** The best retrieved chunk similarity is ≥ 0.30 but < 0.60; answer is generated but marked as potentially weak.
- **No Context (Fallback):** All retrieved chunks are below 0.30; the fallback "not found in documents" response is returned (established in F01).
- **Thumbs Feedback:** A binary user rating (positive / negative) per assistant message, stored in session.
- **Rephrasing Suggestion:** An optional UI prompt shown on low-confidence answers: "Try rephrasing your question or uploading additional documents."

---

### Sub-Features

- Confidence badge on each assistant message: `High`, `Low`, or none (fallback has no badge)
- Confidence badge styling: high = subtle green indicator; low = amber/yellow indicator
- Thumbs-up / thumbs-down buttons on each assistant message (icon buttons, not visible by default — appear on hover/focus)
- Feedback recorded per message in session store
- Feedback is one-shot per message: once submitted, buttons become inactive (shows selected state)
- Rephrasing suggestion shown inline below low-confidence answers
- Confidence score optionally visible in expanded citation panel (developer/debug mode; hidden by default in production)

---

### Process

**Confidence Signal Generation (server-side, during F01 query):**
1. After top-k retrieval, backend computes `max_similarity` = highest similarity score among retrieved chunks.
2. If `max_similarity` < 0.30 → `confidence = "none"` → return fallback response (see F01 §Process step 6c).
3. If 0.30 ≤ `max_similarity` < 0.60 → `confidence = "low"` → proceed with LLM generation but flag response.
4. If `max_similarity` ≥ 0.60 → `confidence = "high"` → proceed with LLM generation normally.
5. `confidence` value included in the `done` SSE event and stored with the message.

**Confidence Signal Display (client-side):**
1. Frontend reads `confidence` from the `done` event.
2. If `"high"`: renders a small green dot or "High confidence" badge near the answer timestamp.
3. If `"low"`: renders an amber "Low confidence" badge + rephrasing suggestion text below the answer.
4. If `"none"` (fallback): no confidence badge; the answer text itself explains the situation.

**User Feedback (thumbs):**
1. User hovers over or focuses an assistant message bubble → thumbs-up and thumbs-down icons appear.
2. User clicks thumbs-up or thumbs-down.
3. Frontend sends `POST /api/chat/feedback` with `{ message_id, rating: "positive" | "negative" }`.
4. Backend records feedback in the session message record.
5. Backend returns 200 with the updated message record.
6. Frontend updates the icon state to show the selected rating (filled icon); hides the unselected icon.
7. Buttons become disabled — feedback cannot be changed after submission in v1.
8. Feedback does not trigger any real-time model update or response modification.

---

### Inputs

**Feedback submission:**
- `message_id` (string UUID, required): The assistant message being rated.
- `rating` (string, required): Must be `"positive"` or `"negative"`.
- `session_id` (string, required): Via HTTP cookie.

---

### Outputs

**Feedback response (`POST /api/chat/feedback`):**
```json
{
  "message_id": "uuid-v4",
  "rating": "positive",
  "recorded_at": "2026-05-13T10:15:00Z"
}
```

**Confidence in message object (extends F01/F04 message schema):**
```json
{
  "message_id": "uuid-v4",
  "role": "assistant",
  "content": "The contract was signed on March 15, 2024.",
  "confidence": "high",
  "user_rating": null,
  "citations": [...]
}
```

**After feedback submission:**
```json
{
  "user_rating": "positive"
}
```

---

### Validation Rules

- `rating` must be exactly `"positive"` or `"negative"`; any other value returns 400 `INVALID_RATING`.
- Feedback may only be submitted for messages with `role = "assistant"`; submitting for a user message returns 400 `INVALID_MESSAGE_ROLE`.
- Feedback may only be submitted once per message per session; a second submission returns 409 `FEEDBACK_ALREADY_SUBMITTED`.
- `message_id` must belong to the current session; cross-session access returns 404 `MESSAGE_NOT_FOUND`.
- The confidence thresholds (0.30 and 0.60) are defaults; they may be overridden per-query via `confidence_threshold` (see F01), but the low/high split always uses:
  - `max_similarity < confidence_threshold` → fallback (no badge)
  - `confidence_threshold ≤ max_similarity < 0.60` → low badge
  - `max_similarity ≥ 0.60` → high badge
  *(The 0.60 split point is fixed; only the fallback threshold is configurable.)*

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Invalid rating value | 400 | INVALID_RATING | "Rating must be 'positive' or 'negative'" |
| Feedback on user message | 400 | INVALID_MESSAGE_ROLE | "Feedback can only be submitted for assistant messages" |
| Feedback already submitted | 409 | FEEDBACK_ALREADY_SUBMITTED | "Feedback has already been recorded for this message" |
| Message not found | 404 | MESSAGE_NOT_FOUND | "Message not found" |
| Session not found | 404 | SESSION_NOT_FOUND | "Session not found or expired" |

---

### API Surface (this feature)

See `Y1-api.md` §Feedback for full request/response schemas.

| Method | Path | Summary |
|---|---|---|
| `POST` | `/api/chat/feedback` | Submit thumbs-up or thumbs-down for an assistant message |

---

### Schema Surface (this feature)

Extends message records with feedback fields. See `Y0-schema.md` §Messages.

Additional fields added to message record by this feature:
- `confidence` (enum: high | low | none | null) — `null` for user messages
- `max_similarity` (float | null) — highest retrieval score; stored for analytics
- `user_rating` (enum: positive | negative | null) — null until feedback submitted
- `rating_recorded_at` (ISO 8601 datetime | null)
