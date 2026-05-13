---

### Flow 04: Multi-Document Filter & Export (P2/P3)

**User Stories:** US-6.1 · US-6.2 · US-8.1 · US-8.3
**Feature Ref:** F6, F8
**Personas:** Maya (cross-doc comparison, export to slides), Daniel (isolate specific contract), Jordan (copy findings to Slack)

---

#### Sub-flow 4A: Document Filter (P2 — US-6.2)

**Trigger:** User wants to restrict a query to one specific document (e.g., "only search contract-a.pdf").

```
[Chat Input Area — document filter control above input]
[Default: "All documents" (no filter active)]

  [All documents ▼]  [Type your question here...]  [Send]

       │
       ▼ [User clicks filter dropdown]
┌──────────────────────────────┐
│  ✓ All documents             │
│    contract-a.pdf  (Ready)   │
│    contract-b.pdf  (Ready)   │
│    notes.txt       (Ready)   │
│    report.docx     (Indexing)│  ← grayed out / disabled
└──────────────────────────────┘
       │
       ▼ [User selects "contract-a.pdf"]
┌──────────────────────────────────────────────────────┐
│  Searching: contract-a.pdf ✕                        │
│  [contract-a.pdf ▼]  [Type your question...]  [Send] │
└──────────────────────────────────────────────────────┘
  (visual indicator that filter is active)
       │
       ▼ [Submit query with filter active]
  [Query sent with document_id filter]
  [Citations will only reference contract-a.pdf]
       │
  [User clicks ✕ on filter badge]
       ▼
  [Filter cleared → "All documents" restored]
```

**Edge cases:**
- Documents in `indexing` state appear in dropdown but are **disabled** (grayed, not selectable)
- Filtering to a document with no indexed content → error response: "Document has no indexed content"
- Filter persists across queries in the same session until explicitly cleared

---

#### Sub-flow 4B: Copy Answer to Clipboard (P3 — US-8.1)

**Trigger:** User hovers or focuses an assistant message bubble.

```
[Assistant bubble (hovered / keyboard focused)]
┌─────────────────────────────────────────────────────────────┐
│ The contract expires on December 31, 2026.                  │
│                                             [📋] [👍] [👎] │  ← appear on hover/focus
└─────────────────────────────────────────────────────────────┘
       │
       ▼ [Click 📋 copy button]
  [Clipboard API called with answer text]
       │
  ┌────┴────────┐
  │ Success     │ Fallback / Error
  ▼             ▼
[Icon → ✓]   [Try execCommand]
["Copied!"    │
 tooltip 2s]  ├── Success → same success state
              └── Fail → soft message: "Copy unavailable in this browser"
```

---

#### Sub-flow 4C: Export Transcript (P3 — US-8.3)

**Trigger:** User clicks "Export Transcript" in the app header or via a menu.

```
[App Header → "Export" button (or ··· menu)]
       │
       ▼
┌────────────────────────────────────────────────────┐
│  Export Transcript                                 │
│                                                   │
│  Select format:                                   │
│  ◉ Plain Text (.txt)                              │
│  ○ Markdown (.md)                                 │
│                                                   │
│  [Cancel]              [Download]                 │
└────────────────────────────────────────────────────┘
       │
       ▼ [User selects format, clicks Download]
  [GET /api/chat/export?format=text|markdown]
  [Browser triggers file download]
       │
  [Empty chat?]
  ├── Yes → file contains header metadata + "No messages in this session."
  └── No  → all messages in chronological order, timestamps, speaker labels, citations (truncated to 500 chars)
```

---

#### Sub-flow 4D: Rate an Answer — Thumbs Up/Down (P2 — US-7.2)

**Trigger:** User hovers or focuses an assistant message bubble (same hover state as copy).

```
[Assistant bubble controls visible: [📋] [👍] [👎]]
       │
       ▼ [User clicks 👍 or 👎]
  [POST /api/chat/feedback { message_id, rating: "positive"|"negative" }]
       │
  [Selected icon: filled/active state]
  [Unselected icon: hidden]
  [Both buttons disabled — cannot change rating (v1)]
```

**Note:** Feedback buttons appear alongside the copy button on hover/focus. Once rated, the selected icon stays filled; the unselected icon disappears. No success toast needed — the visual state change is sufficient feedback.
