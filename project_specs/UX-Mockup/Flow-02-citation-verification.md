---

### Flow 02: Citation Verification (Expand & Read Source Passage)

**User Stories:** US-2.1 · US-2.2 · US-2.3 · US-8.2 (P3)
**Feature Ref:** F2, F8
**Personas:** Maya (verify before deliverable), Daniel (verbatim clause confirmation), Jordan (spec version verification — keyboard only)

**Trigger:** An assistant answer with one or more citation chips is visible in the chat transcript.

```
[Assistant answer bubble: complete, with citation chips below]

[Citation chips row:]
  ┌──────────────────────────┐  ┌──────────────────────────┐
  │ 📄 contract.pdf — p. 4   │  │ 📄 addendum.docx — p. 12 │
  └──────────────────────────┘  └──────────────────────────┘
        │  (focused / hovered)
        ▼
  [Click chip / press Enter on focused chip]
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │  Citation Panel (inline, below chip row)     │
  │                                             │
  │  annual-report-2025.pdf — p. 8, excerpt 1   │
  │  ┌─────────────────────────────────────────┐│
  │  │ "Revenue for fiscal year 2025 totaled   ││
  │  │  $4.2 billion, representing a 12%       ││
  │  │  increase over the prior year ended     ││
  │  │  December 31, 2024…"                    ││
  │  └─────────────────────────────────────────┘│
  │  [📋 Copy passage]          [✕ Close]       │
  └─────────────────────────────────────────────┘
        │                              │
        │                              ▼
        │                    [Panel collapses]
        │                    [Focus returns to chip]
        │
        ▼ (user clicks second chip while first panel open)
  [First panel collapses automatically]
  [Second chip's panel opens]
  (only one panel open per message at a time — US-2.2)
        │
        ▼ (user presses Escape)
  [Panel collapses]
  [Focus returns to chip]
```

**Multiple citations — "From N documents" label (P2 — US-6.1):**
```
[When citations reference 2+ distinct documents:]

  From 3 documents
  ┌──────────────────────────┐  ┌───────────────────────┐  ┌───────────────────┐
  │ 📄 report-a.pdf — p. 7  │  │ 📄 report-b.pdf — p.2 │  │ 📄 notes.txt      │
  └──────────────────────────┘  └───────────────────────┘  └───────────────────┘
```

**Steps (detailed):**

1. **Chip display:** After the `done` SSE event, chips render below the answer bubble. Each chip shows: file type icon (visually distinct PDF/TXT/DOCX) + document name (truncated to 30 chars, ellipsis) + page reference if available. TXT files: name only, no page number.
2. **Single-expand rule:** At most one citation panel is expanded at a time per message. Clicking a new chip auto-collapses any previously open panel for that message.
3. **Citation panel content:** Full `chunk_text` in a visually distinct read-only block (blockquote or bordered card, muted background). Document name + page/section reference as panel header. Verbatim text — no paraphrasing, no editing affordance.
4. **Copy passage (P3, US-8.2):** 📋 icon in panel header. Click → copies `chunk_text` to clipboard → icon briefly becomes ✓ checkmark → "Copied!" tooltip for 2 seconds.
5. **Keyboard:** Tab reaches chip → Enter/Space toggles panel → Escape closes panel.
6. **Fallback responses:** No chips rendered. The "not found" message IS the answer. No panel to expand.

**Exit points:**
- User closes panel → returns to reading the answer
- User copies passage → continues to external tool
- User asks follow-up question (loop back to Flow 01)
