---

### Flow 01: Ask a Question & Receive a Streamed Answer

**User Stories:** US-1.1 · US-1.2 · US-1.3 · US-2.1 · US-2.2 · US-7.1 (P2)
**Feature Ref:** F1, F2, F7
**Personas:** All three — core product loop

**Trigger:** At least one document has `ready` status. Chat input is enabled.

```
[Chat Input: enabled, placeholder "Ask a question about your documents…"]
       │
       ├── [Optional: set document filter (P2)] — see Flow 04
       │
       ▼
[User types question → presses Enter or clicks Send]
       │
       ├── Empty / whitespace ──▶ Inline error: "Please enter a question"
       │                          (no request sent)
       │
       ├── > 2000 chars ─────────▶ Inline error: "Question must be under 2000 characters"
       │                          character counter shows near limit
       │
       └── Valid query ──────────▶ [User message appended optimistically, right-aligned]
                                   [Chat input DISABLED — prevents duplicate submission]
                                   [Thinking indicator appears: animated dots in assistant position]
                                          │
                                          ▼
                                   [POST /api/chat/query → SSE stream opens]
                                          │
                          ┌───────────────┴───────────────┐
                          │ No chunks ≥ 0.30 similarity   │ Chunks found
                          ▼                               ▼
                 [Fallback response               [Tokens stream into
                  (non-streaming):                 assistant bubble
                  "The uploaded documents          word-by-word]
                  do not contain information       │
                  about this topic."]              ▼
                          │                [done event received]
                          │                       │
                          └───────────────┬───────┘
                                          ▼
                              [Full answer rendered in bubble]
                              [Thinking indicator removed]
                              [Chat input RE-ENABLED]
                              [Chat auto-scrolls to bottom
                               (if user was already at bottom)]
                                          │
                          ┌───────────────┴───────────────┐
                          │ confidence: "low" (fallback)   │ confidence: "high"/"low" w/ citations
                          ▼                               ▼
                 [No citation chips]              [Citation chips appear below bubble]
                 [No confidence badge]            [Confidence badge (P2):
                                                   green "High confidence" OR
                                                   amber "Low confidence" +
                                                   "Try rephrasing your question…"]
                                                          │
                                               [User may expand citation — Flow 02]
                                               [User may rate answer (P2) — hover/focus]
                                               [User may copy answer (P3)]
```

**Stream error path:**
```
[SSE stream drops / network error mid-generation]
       │
       ▼
[Error message in assistant bubble:
 "Answer generation failed. Please try again."
 [Retry] button]
```

**Steps (detailed):**

1. **Input validation (client-side, instant):** Empty → inline error, no request. Over limit → counter turns red, submit blocked.
2. **Optimistic append:** User message bubble appears immediately at bottom of chat transcript (right-aligned, accent color background, timestamp "just now").
3. **Thinking indicator:** Animated three-dot pulse appears in assistant bubble position. This is the signal the system is working — never leave the user in silence.
4. **Streaming tokens:** Each token appends to the assistant bubble text in real time. The bubble grows naturally as text is added. Markdown is rendered safely.
5. **Done event:** Citations array and confidence score arrive. Chips render below the bubble. Confidence badge renders at top of bubble (P2).
6. **Fallback state:** No chips. Answer text itself signals the absence. No confidence badge shown (the text IS the signal per US-1.3).
7. **Chat scroll logic:** Auto-scrolls to bottom only if user was within 100px of bottom before the message arrived. Manual scroll position is preserved if user is reading history.

**Exit points:**
- User reads answer → may expand citations (Flow 02), ask follow-up (loop Flow 01), copy answer (US-8.1), or rate (US-7.2)
