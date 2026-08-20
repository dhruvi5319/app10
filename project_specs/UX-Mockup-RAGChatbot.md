# UX Mockup: RAG Chatbot

**Project:** RAGChatbot
**Generated:** 2026-05-13
**Updated:** 2026-08-20 — Screen-05 added for Phase 5 (F9 LLM Settings Panel); gear icon trigger added to app header layout
**Based on:** UserStories-RAGChatbot.md · JOURNEYS-RAGChatbot.md · PRD-RAGChatbot.md · FRD-RAGChatbot.md

---

## Overview

### UX Approach

The RAG Chatbot UI is built around a single, trust-building moment: the user sees a verbatim passage from their own document appear beneath each answer. Every design decision flows from this insight.

**Three personas drive the design:**
- **Maya Patel (Research Analyst):** Batch-uploads PDFs, needs cross-document synthesis, exports to client deliverables
- **Daniel Torres (Legal Professional):** High-stakes clause verification, zero tolerance for hallucination, values explicit "not found" signals
- **Jordan Kim (Technical Knowledge Worker):** Keyboard-first, iterative sessions, multi-document cross-referencing

### Core Design Principles

1. **Trust through transparency** — Citations are never buried. They appear immediately after every answer, one click away from the verbatim source text.
2. **Status visibility at all times** — Document ingestion state is always visible. Users never query without knowing exactly which documents are ready.
3. **Keyboard-first affordances** — Enter submits, Tab navigates, Escape dismisses. No mouse required for any critical path.
4. **Progressive disclosure** — Citation details, confirmation prompts, and advanced filters appear only when needed. The default view is clean.
5. **Explicit over implicit** — "Not found" is a first-class response, not silence. Error states carry specific, actionable messages.
6. **No blank screens** — Skeleton loaders, empty states with calls-to-action, and loading indicators fill every wait moment.

### Design Language (Modern Aesthetic — Phase 3+)

The v1 implementation used a functional dark theme. The target design language elevates this to a premium, modern aesthetic:

**Visual Treatment**
- **Glassmorphism surfaces** — sidebar and input bar use `backdrop-filter: blur(…)` with semi-transparent backgrounds, creating depth and layering
- **Gradient accents** — primary actions use a `#6c63ff → #a855f7` purple gradient; user message bubbles use a subtle gradient fill
- **Glow effects** — focused inputs and hovered interactive elements emit a soft `box-shadow` glow using the accent colour at low opacity
- **Layered shadows** — cards use multi-stop shadows (`0 1px 2px …, 0 4px 16px …`) to lift off the background
- **Gradient borders** — key containers use a 1px border rendered via `background-image: linear-gradient(…)` on a pseudo-element or `border-image`

**Motion**
- Message bubbles animate in with a `slideUp` + `fadeIn` combination (200ms, ease-out)
- The upload zone pulses its accent border on drag-over
- Streaming cursor blinks at 1s intervals
- All state transitions (badge colour changes, panel collapse) use `transition: all 0.2s ease`

**Typography**
- Inter remains the primary typeface; weight scale extended to use 300 (light) for secondary text, 700 (bold) for headings and brand mark
- Brand mark in the chat header gets an `A` gradient treatment matching the accent gradient

**Colour Tokens Added**

| Token | Value | Purpose |
|---|---|---|
| `--gradient-accent` | `linear-gradient(135deg, #6c63ff, #a855f7)` | Primary action gradient |
| `--gradient-user-bubble` | `linear-gradient(135deg, #2d3250, #3d2f6e)` | User message fill |
| `--glow-accent` | `0 0 0 3px rgba(108,99,255,0.25)` | Focus/hover glow |
| `--glow-accent-strong` | `0 0 20px rgba(108,99,255,0.35)` | Ambient accent glow |
| `--surface-glass` | `rgba(26,29,38,0.7)` | Glassmorphism surface bg |
| `--shadow-deep` | `0 1px 2px rgba(0,0,0,0.4), 0 8px 32px rgba(0,0,0,0.35)` | Elevated card shadow |
| `--radius-xl` | `20px` | Larger pill/bubble radius |

**Accessibility Preservation**
All contrast ratios remain WCAG AA compliant. Glow effects are additive only — no colour information is conveyed by glow alone. `prefers-reduced-motion` media query disables non-essential animations.

### Layout Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  App Header: Logo · Session Controls (Clear Chat, New Session, Export)  [⚙] │
├──────────────────┬──────────────────────────────────────────┤
│                  │                                          │
│  Document        │  Chat Area                               │
│  Library         │  - Empty State / Message Transcript      │
│  Sidebar         │  - Streaming Answer Bubbles              │
│  (~280px)        │  - Citation Chips + Panels               │
│                  │                                          │
│  Upload Zone     │                                          │
│  (always visible)│                                          │
│                  ├──────────────────────────────────────────┤
│                  │  [Document Filter (P2)] [Chat Input] [Send] │
└──────────────────┴──────────────────────────────────────────┘
```

### Feature Coverage Map

| Screen / Section | Stories | Priority |
|---|---|---|
| Document Library Sidebar | US-0.1, US-0.2, US-0.3, US-3.1, US-3.2 | P0–P1 |
| Chat Transcript | US-1.1, US-1.2, US-1.3, US-4.1 | P0–P1 |
| Citation Chips & Panel | US-2.1, US-2.2, US-2.3 | P0 |
| Chat Input Bar | US-1.1, US-6.2, US-8.3 | P0–P3 |
| Session Controls (Header) | US-4.2, US-4.3 | P1 |
| Confidence & Feedback | US-7.1, US-7.2 | P2 |
| Document Filter | US-6.1, US-6.2 | P2 |
| Copy / Export Utilities | US-8.1, US-8.2, US-8.3 | P3 |
| **LLM Settings Modal** (Screen-05) | **US-9.1, US-9.2, US-9.3, US-9.4, US-9.5** | **P1 (Phase 5)** |

---

## Navigation Map (all screens)

| Screen | Route / Trigger | Reached from | Nav element |
|--------|----------------|--------------|-------------|
| Main Layout (Screen-00) | `/` | — (app shell) | Direct URL / page load |
| LLM Settings Modal (Screen-05) | Overlay — no URL change | App header (all screens) | Header: `⚙` icon button (top-right) |

*Modal / overlay screens are reached from the app shell; they do not change the URL. All other screens trace back to the main layout.*

---

*Chunk files: 00-overview.md · Flow-00 through Flow-04 · Screen-00 · Screen-05 · Y0-patterns.md · Y1-responsive.md · Y2-accessibility.md*
*Updated 2026-08-20: Screen-05 (LLM Settings Modal, Phase 5 / F9) added.*
---

## User Flows

### Flow 00: Document Upload & Ingestion

**User Stories:** US-0.1 · US-0.2 · US-0.3
**Feature Ref:** F0, F3
**Personas:** Maya Patel (batch research PDFs), Daniel Torres (single contract, time pressure), Jordan Kim (drag-drop keyboard-first)

**Trigger:** User arrives with documents to analyze. Either empty-state first visit or mid-session addition.

```
[User Arrives at App]
       │
       ▼
[Empty State — Upload Zone prominent]
       │
       ├── Drag files onto zone ──────────────────────────────────────┐
       │                                                               │
       └── Click "Browse files" (file picker fallback) ───────────────┘
                                                                       │
                                                    ┌──────────────────▼──────────────────┐
                                                    │  Client-side validation (instant)    │
                                                    │  - extension: .pdf/.txt/.docx?       │
                                                    │  - size: ≤ 50 MB?                    │
                                                    │  - session count: < 20?              │
                                                    │  - session size: < 200 MB?           │
                                                    │  - non-empty file?                   │
                                                    └──────┬────────────────┬──────────────┘
                                                           │ PASS           │ FAIL
                                                           ▼                ▼
                                              [Upload Card appears]  [Inline error below
                                              status: uploading      drop zone — specific
                                              spinner visible]       rejection reason]
                                                           │
                                                           ▼
                                              [POST /api/documents/upload]
                                                           │
                                              ┌────────────▼─────────────┐
                                              │   Backend validates again  │
                                              │   202 Accepted → doc_id   │
                                              └────────────┬─────────────┘
                                                           │
                                                           ▼
                                              [Status: uploading → indexing]
                                              [Poll every 2s: GET /api/documents/{id}/status]
                                                           │
                                              ┌────────────┴─────────────┐
                                              │ ready                    │ error
                                              ▼                          ▼
                                   [Green checkmark ✓]        [Red error badge]
                                   [Chat input ENABLED]       [Specific reason shown]
                                   [Status: "Ready"]          [Retry affordance]
                                   [Document count updates]
```

**Multiple files in one drop:**
- Each file gets its own upload card immediately
- Validation runs per-file: rejected files show errors; valid files proceed independently
- A rejected file does NOT block other valid files in the same batch (US-0.2)

**Steps (detailed):**

1. **Drag-over feedback:** Drop zone border animates to accent color, background tints. If drag leaves window, zone resets to default immediately.
2. **Drop/select:** Upload cards appear in the Document Library sidebar — one per file — showing filename, size, and an `uploading` spinner.
3. **Client validation (instant, pre-upload):** Unsupported type → "Supported formats: PDF, TXT, DOCX". Over 50 MB → "File must be under 50MB". Session full → "Session storage limit of 200MB reached" / "Maximum 20 documents per session". Empty file → "Uploaded file contains no data".
4. **Server acceptance (202):** Card transitions from `uploading` to `indexing`. Badge shows animated blue "Indexing…" with pulse animation.
5. **Polling (every 2s):** Status badge updates in place. No page refresh needed.
6. **Ready:** Card shows green "Ready ✓". Chat input unlocks if at least one document is ready.
7. **Error:** Card shows red "Error" badge with specific reason (e.g., "PDF appears to be image-only; OCR not supported in v1"). Retry button visible.

**Exit points:**
- At least one document `ready` → proceed to Flow 01 (Ask a Question)
- All documents errored → remain in upload flow, retry or upload different files
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
---

### Flow 03: Session Management (Clear Chat / New Session / Delete Document)

**User Stories:** US-3.2 · US-4.2 · US-4.3
**Feature Ref:** F3, F4
**Personas:** Maya (clear chat, keep docs), Daniel (delete superseded contract), Jordan (new session for fresh task)

---

#### Sub-flow 3A: Delete a Document

**Trigger:** User wants to remove a document from the session index (e.g., superseded contract, wrong file uploaded).

```
[Document Library Sidebar — document card visible]
[Each card has: 🗑️ trash icon button (aria-label: "Delete [filename]")]
       │
       ▼  [User clicks/activates 🗑️ on document card]
       │
       ▼
┌─────────────────────────────────────────────────────┐
│  Confirmation Modal                                  │
│                                                     │
│  Delete "contract-v2.pdf"?                          │
│  This will remove it from the document index.       │
│                                                     │
│  [Cancel]                    [Delete]               │
└─────────────────────────────────────────────────────┘
       │                              │
       ▼ Cancel                       ▼ Delete
  [Modal closes]            [Delete button → spinner]
  [No action]               [DELETE /api/documents/{id}]
                                      │
                         ┌────────────┴────────────┐
                         │ 204 Success             │ Error
                         ▼                         ▼
              [Card removed from library] [Red inline error on card:
              [Count/size summary updates] "Delete failed. Try again."]
              │                           [Retry affordance]
              ▼
   [Was last "ready" document?]
              │
     ┌────────┴────────┐
     │ Yes             │ No
     ▼                 ▼
  [Chat input       [Chat input stays
   disabled]         enabled]
  [Prompt: "Upload   [Session continues
   a document to     normally]
   start asking"]
```

---

#### Sub-flow 3B: Clear Chat History

**Trigger:** User wants fresh questions about the same document set without re-uploading.

```
[App Header → "Clear Chat" button]
       │
       ▼
┌────────────────────────────────────────────────────┐
│  Confirmation Modal                                │
│                                                   │
│  Clear conversation?                              │
│  Documents remain uploaded.                       │
│                                                   │
│  [Cancel]               [Clear]                   │
└────────────────────────────────────────────────────┘
       │                         │
       ▼ Cancel            ▼ Clear
  [Modal closes]    [DELETE /api/chat/history]
  [No action]              │
                    ┌──────┴──────┐
                    │ 204         │ Error
                    ▼             ▼
           [Chat view cleared]  [Toast error:
           [Empty state shown]   "Failed to clear chat.
           [Documents & library  Try again."]
            unchanged]
```

---

#### Sub-flow 3C: Start a New Session

**Trigger:** User wants to begin an entirely new research task — fresh documents AND fresh chat.

```
[App Header → "New Session" button (visually distinct from "Clear Chat")]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│  Confirmation Modal                                    │
│                                                       │
│  Start a new session?                                 │
│  All documents and chat history will be cleared.      │
│                                                       │
│  [Cancel]                   [Start New Session]       │
└────────────────────────────────────────────────────────┘
       │                              │
       ▼ Cancel                       ▼ Confirm
  [Modal closes]            [POST /api/session/reset]
  [No action]                         │
                             ┌────────┴────────┐
                             │ Success         │ Error
                             ▼                 ▼
                  [Library cleared]      [Toast error]
                  [Chat cleared]
                  [New session cookie set]
                  [Onboarding empty state shown]
```

**Key UX distinction (US-4.3):** "Clear Chat" and "New Session" are visually differentiated — different button weights, colors, or placement — so users cannot accidentally wipe their documents when they only meant to clear the chat. Suggested: "Clear Chat" is a secondary text button; "New Session" is a muted/ghost button with a warning-adjacent treatment.
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
---

## Screen Designs

### Screen 00: Main Layout — Desktop (≥ 1024px)

**Purpose:** The primary application shell. Contains all features accessible at all times. Two-column split panel.
**User Stories:** US-0.1 · US-1.1 · US-3.1 · US-4.1 · US-5.1 · US-5.2

#### Layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│  HEADER                                                                    │
│  🤖 RAG Chatbot                    [Clear Chat]  [New Session]  [Export ↓] │
├──────────────────────────┬─────────────────────────────────────────────────┤
│  DOCUMENT LIBRARY        │  CHAT AREA                                      │
│  (~280px, fixed)         │  (remaining width, flex)                        │
│                          │                                                 │
│  ┌────────────────────┐  │  ┌──────────────────────────────────────────┐  │
│  │ 📂 Documents       │  │  │  [Empty state OR message transcript]     │  │
│  │ 2 docs · 3.4 MB    │  │  │                                          │  │
│  └────────────────────┘  │  │                                          │  │
│                          │  │  ┌────────────────────────────────────┐  │  │
│  ┌────────────────────┐  │  │  │ [USER BUBBLE - right aligned]      │  │  │
│  │ 📄 contract.pdf    │  │  │  │ "What does clause 9.2 say?"        │  │  │
│  │ PDF · 2.1 MB       │  │  │  │                          just now  │  │  │
│  │ ✅ Ready           │  │  │  └────────────────────────────────────┘  │  │
│  │           [🗑️]    │  │  │                                          │  │
│  └────────────────────┘  │  │  🤖 ┌──────────────────────────────────┐  │  │
│                          │  │     │ [ASSISTANT BUBBLE - left aligned] │  │  │
│  ┌────────────────────┐  │  │     │ "Section 9.2 states: The         │  │  │
│  │ 📝 notes.txt       │  │  │     │  indemnification cap shall not   │  │  │
│  │ TXT · 1.3 MB       │  │  │     │  exceed..."                      │  │  │
│  │ 🔵 Indexing…       │  │  │     │                        2 min ago │  │  │
│  │           [🗑️]    │  │  │     └──────────────────────────────────┘  │  │
│  └────────────────────┘  │  │     [📄 contract.pdf — p. 34]            │  │
│                          │  │                                          │  │
│  ┌────────────────────┐  │  └──────────────────────────────────────────┘  │
│  │                    │  │                                                 │
│  │   UPLOAD ZONE      │  ├─────────────────────────────────────────────────┤
│  │                    │  │  CHAT INPUT BAR                                 │
│  │  ⬆ Drag & drop    │  │                                                 │
│  │  or Browse files   │  │  [All documents ▼] [P2 filter]                 │
│  │                    │  │  ┌───────────────────────────────────┐  [Send] │
│  │  PDF  TXT  DOCX    │  │  │ Ask a question about your docs…  │         │
│  │  Max 50MB per file │  │  └───────────────────────────────────┘         │
│  └────────────────────┘  │                                                 │
└──────────────────────────┴─────────────────────────────────────────────────┘
```

#### Information Hierarchy

| Priority | Content | Placement |
|---|---|---|
| Primary | Chat transcript (question + answer) | Main content area, center |
| Primary | Chat input | Pinned to bottom of content area |
| Secondary | Document library with status | Left sidebar, always visible |
| Secondary | Upload zone | Bottom of sidebar, always accessible |
| Tertiary | Session controls (clear, new session, export) | Header, right side |
| Tertiary | Document count + storage summary | Sidebar header |

#### States

| State | Appearance | User Feedback |
|---|---|---|
| Default / No documents | Upload zone prominent, chat area shows onboarding empty state | "Upload a document to get started" |
| Uploading | Per-file card with spinner, gray "Uploading" badge | File card visible, progress implied by spinner |
| Indexing | Per-file card with animated blue "Indexing…" badge | Pulse animation on badge |
| Ready | Green "Ready ✓" badge, chat input enabled | Input placeholder changes to "Ask a question…" |
| Error (doc) | Red "Error" badge + specific reason + Retry link | Specific error reason on card |
| Loading (query) | Thinking dots in assistant position, chat input disabled | Animated dots; input shows "Processing…" |
| Streaming | Tokens append to assistant bubble live | Bubble text grows word-by-word |
| Empty chat (post-clear) | Empty state with upload call-to-action | "Upload a document and ask your first question" |

#### Interactive Elements

| Element | Type | Behavior |
|---|---|---|
| Upload drop zone | Drop target + file input | Drag-over → accent border; drop → upload starts; click → file picker |
| Browse files link | `<input type="file" multiple>` | Opens OS file picker; keyboard accessible via Enter on zone |
| Document card trash icon | Icon button (aria-label: "Delete [filename]") | Click → confirmation modal |
| Chat input | Auto-resize textarea | Enter → submit; Shift+Enter → newline |
| Send button | Primary button | Click → submit; disabled while querying |
| Citation chip | Toggle button | Enter/click → expands citation panel |
| Clear Chat | Secondary text button | Opens confirmation modal |
| New Session | Ghost/muted button | Opens confirmation modal (destructive warning) |
| Export | Dropdown/button | Opens format selector modal |
---

## Screen Designs

### Screen 05: LLM Settings Modal

**Purpose:** Lets the user configure their LLM provider, model, and API key from the UI without editing server configuration files. The modal is a centered overlay; the raw API key is never displayed after it has been saved.
**User Stories:** US-9.1 · US-9.2 · US-9.3 · US-9.4 · US-9.5
**Feature Ref:** F9
**Phase:** 5

---

#### Trigger

A `⚙` gear icon button sits in the **top-right area of the app header**, after the Export control. It is always visible regardless of document or chat state — including when no API key has been configured (which is precisely when first-time users need it most).

```
┌────────────────────────────────────────────────────────────────────────────┐
│  🤖 RAG Chatbot            [Clear Chat]  [New Session]  [Export ↓]  [⚙]  │
└────────────────────────────────────────────────────────────────────────────┘
```

- **Element type:** `<button>` with `aria-label="Open LLM settings"` and `aria-haspopup="dialog"`
- **Keyboard:** Tab-reachable; Enter / Space opens the modal
- **Tooltip:** "LLM Settings" on hover / focus (200 ms delay)

---

#### Navigation Map Entry

| Screen | Route / Trigger | Reached from | Nav element |
|--------|----------------|--------------|-------------|
| LLM Settings Modal | `⚙` gear button click | App header (all screens) | Header: "⚙" icon button (top-right) |

The modal is a layer over the current screen — it does not change the URL. Focus is trapped inside the modal while it is open. Closing the modal returns focus to the gear icon.

---

#### Modal Layout

The modal is a **centered overlay** (480 px wide, ~400 px tall) on a dark semi-transparent backdrop. It uses the surface colour token (`--color-surface: #1a1d27`) for its background and `--color-accent: #6c63ff` for the primary action.

```
╔══════════════════════════════════════════════════════════╗
║  LLM Settings                                       [✕]  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Provider                                                ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  OpenAI                                         ▾  │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  Model                                                   ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  gpt-4o                                            │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  API Key                                                 ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  ••••••••••••••••••••••••••••••              [👁]  │  ║
║  └────────────────────────────────────────────────────┘  ║
║  ✅ Key saved · sk-...XXXX                  ← muted green║
║                                                          ║
║                                                          ║
║  [    Cancel    ]                  [  Save Settings  ]  ║
╚══════════════════════════════════════════════════════════╝
```

**Backdrop:** `background: rgba(0,0,0,0.6); backdrop-filter: blur(4px)` covering the full viewport behind the modal.

**Modal card:** `background: var(--color-surface); border: 1px solid rgba(108,99,255,0.25); border-radius: 12px; box-shadow: var(--shadow-deep)` (deep shadow from design token).

**Modal header:** Left-aligned title "LLM Settings" in bold (`font-weight: 700`). Right-aligned `✕` close button with `aria-label="Close settings"`.

---

#### Form Fields

| Field | Type | Label | Default / Pre-fill | Notes |
|-------|------|-------|--------------------|-------|
| Provider | `<select>` | "Provider" | Current `provider` from `GET /api/settings` | Options: "OpenAI", "Anthropic" |
| Model | `<input type="text">` | "Model" | Current `model` from `GET /api/settings` | Placeholder: `e.g. gpt-4o` |
| API Key | `<input type="password">` | "API Key" | Always blank on open | Placeholder varies by `has_key` (see below) |

**API Key placeholder logic:**

- `has_key: false` → placeholder text: `"Paste your API key"`
- `has_key: true` → placeholder text: `"Enter new key to replace current"`

**Key badge** (shown only when `has_key: true`): A small inline element rendered below the API Key input field.

```
  ✅  Key saved · sk-...XXXX
```

- Colour: muted green (`#4ade80` at 80% opacity on the dark surface)
- Font size: 12px / `text-sm`
- Icon: `✅` or a small lock icon; `aria-hidden="true"`

**Reveal toggle:** An eye icon `[👁]` inside the API Key input (right-inset) toggles `type="password"` ↔ `type="text"` so the user can verify what they typed. Label: `aria-label="Show API key"` / `"Hide API key"`.

---

#### Save Button Enable/Disable Logic

| `has_key` state | API Key field | Save button |
|-----------------|---------------|-------------|
| `false` (no key saved) | Empty | **Disabled** — tooltip: "Enter an API key to enable saving" |
| `false` | Non-empty | Enabled |
| `true` (key exists) | Empty | **Enabled** — existing key will be kept; only provider/model updated |
| `true` | Non-empty | Enabled — new key replaces existing |

---

#### Information Hierarchy

| Priority | Content | Placement |
|----------|---------|-----------|
| Primary | Provider select + Model input | Top of form — most commonly edited |
| Primary | API Key input | Below model — security-sensitive; password type |
| Secondary | Key badge (`sk-...XXXX`) | Below API Key field, only when key exists |
| Secondary | Save Settings button | Bottom-right — primary accent colour |
| Tertiary | Cancel button | Bottom-left — secondary/ghost style |
| Tertiary | Close (✕) button | Modal header, top-right |

---

#### States

| State | Appearance | User Feedback |
|-------|------------|---------------|
| **Default — no key** | Fields empty / default-value pre-filled; Save disabled | Placeholder: "Paste your API key"; Save button dimmed |
| **Default — key exists** | Provider + model pre-filled; key badge visible; API Key field blank with "Enter new key…" placeholder; Save enabled | Badge shows `sk-...XXXX` |
| **Loading (on open)** | Modal skeleton — fields shimmer while `GET /api/settings` resolves | Fields replaced with skeleton bars (~120 ms) |
| **Dirty / editing** | User has changed one or more fields | No special indicator — standard browser focus outline + glow |
| **Saving** | Save button shows inline spinner `⟳`; label changes to "Saving…"; all form fields disabled; Cancel also disabled | Button: `[⟳ Saving…]` — accent colour preserved |
| **Success** | Modal closes; toast appears top-right | Toast: `"Settings saved successfully"` — green, auto-dismisses after 4 s |
| **Error — field-level** | Inline red message under the failing field; modal stays open | e.g., `"An API key is required when no key is currently saved."` below API Key field |
| **Error — server** | Inline red message below the button row; modal stays open; Save re-enabled | e.g., `"Server encryption configuration error; contact administrator."` |
| **Empty (no settings ever set)** | All fields at defaults: Provider = OpenAI, Model = `gpt-4o`, no badge | Prompt visible in placeholder text |

---

#### Saving State Wireframe Detail

```
╔══════════════════════════════════════════════════════════╗
║  LLM Settings                                       [✕]  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Provider                                                ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  OpenAI                                         ▾  │  ║  ← disabled
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  Model                                                   ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  gpt-4o                                            │  ║  ← disabled
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  API Key                                                 ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  ••••••••••••••••••••••••••••••              [👁]  │  ║  ← disabled
║  └────────────────────────────────────────────────────┘  ║
║  ✅ Key saved · sk-...XXXX                               ║
║                                                          ║
║  [    Cancel    ]                  [  ⟳ Saving…   ]  ║
╚══════════════════════════════════════════════════════════╝
```

---

#### Error State Wireframe Detail

```
╔══════════════════════════════════════════════════════════╗
║  LLM Settings                                       [✕]  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Provider                                                ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  OpenAI                                         ▾  │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  Model                                                   ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  gpt-4o                                            │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  API Key                                                 ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │                                              [👁]  │  ║  ← red border
║  └────────────────────────────────────────────────────┘  ║
║  ⚠ An API key is required when no key is currently saved.║  ← red, 12px
║                                                          ║
║  [    Cancel    ]                  [  Save Settings  ]  ║
╚══════════════════════════════════════════════════════════╝
```

Field-level error styling: `border: 1px solid #f87171; box-shadow: 0 0 0 3px rgba(248,113,113,0.2)`. Error text: `color: #f87171; font-size: 12px; margin-top: 4px`.

---

#### Interactive Elements

| Element | Type | Behavior |
|---------|------|----------|
| Gear icon `⚙` (header) | `<button>` | Click / Enter → opens modal; calls `GET /api/settings` |
| ✕ Close button | `<button>` | Click / Enter → closes modal without saving; focus returns to gear icon |
| Provider `<select>` | Dropdown | Selecting "OpenAI" / "Anthropic" updates local form state; no immediate API call |
| Model `<input>` | Text input | Free text; trimmed on save; glow on focus |
| API Key `<input type="password">` | Password input | Always blank on open; glow on focus; eye toggle for reveal |
| Eye toggle `[👁]` | Icon button inside input | Toggles `type` between `password` and `text`; `aria-label` updates accordingly |
| Cancel button | Secondary / ghost button | Discards all changes; closes modal; no API call |
| Save Settings button | Primary accent button | Sends `PUT /api/settings`; disabled per logic table above |
| Dark backdrop | Click target | Click outside the modal card → same as Cancel |
| Escape key | Keyboard shortcut | Closes modal without saving (same as Cancel) |

---

#### User Journey Integration

**Entry points:**
1. User clicks `⚙` in the app header → modal opens
2. System shows `LLM_UNAVAILABLE` error in chat (no key configured) → inline link "Open Settings" in the error message → same modal opens

**Exit points:**
1. **Save success** → modal closes → toast "Settings saved successfully" top-right (4 s) → returns to previous screen state
2. **Cancel / Escape / backdrop click** → modal closes → no changes persisted → returns to previous screen state
3. **Error** → modal stays open → user corrects field → re-submits

**Adjacent workflows:**
- If the user saves a key for the first time and no documents are ready, the chat input remains disabled (per F0 rules). Settings panel does not change document state.
- If the user saves a new key while a query is streaming, the new key applies to the **next** query only — the in-flight stream is not interrupted.

---

#### Responsive Considerations

| Viewport | Behaviour |
|----------|-----------|
| Desktop (≥ 1024 px) | Centered overlay, 480 px wide, as designed above |
| Tablet (768 px – 1023 px) | Same centered overlay; modal width 90 vw (max 480 px) |
| Mobile (< 768 px) | Modal slides up from the bottom as a bottom sheet; full width; rounded top corners; handle bar at top; internally scrollable if content overflows |

Mobile bottom-sheet wireframe:
```
╔══════════════════════════════════╗
║        ──── (handle bar)         ║
║  LLM Settings              [✕]  ║
╠══════════════════════════════════╣
║  Provider                        ║
║  [  OpenAI              ▾  ]    ║
║  Model                           ║
║  [  gpt-4o                  ]   ║
║  API Key                         ║
║  [  ••••••••••••••••    [👁] ]  ║
║  ✅ Key saved · sk-...XXXX      ║
║                                  ║
║  [Cancel]    [Save Settings]    ║
╚══════════════════════════════════╝
```

---

#### Accessibility Notes

- Modal uses `role="dialog"` and `aria-modal="true"`; `aria-labelledby` points to the "LLM Settings" heading.
- **Focus trap:** On open, focus moves to the first focusable field (Provider select). Tab cycles within the modal; Shift+Tab reverses. Focus never leaves the modal while it is open.
- **Focus restore:** On close (any method), focus returns to the `⚙` gear icon that opened the modal.
- **Escape key** closes the modal (same behaviour as Cancel).
- **Save button disabled state:** `aria-disabled="true"` + a tooltip (`title` or `aria-describedby`) explains why: "Enter an API key to enable saving".
- **Error announcements:** Field-level errors are linked to their input via `aria-describedby`; the error container uses `role="alert"` so screen readers announce it immediately on injection.
- **API Key reveal toggle:** `aria-label` is dynamic — "Show API key" when masked, "Hide API key" when revealed.
- **Key badge:** The `✅` icon has `aria-hidden="true"`; the badge text ("Key saved · sk-...XXXX") is the accessible label.
- **Colour contrast:** All text on `--color-surface: #1a1d27` background meets WCAG AA ≥ 4.5:1. Error red `#f87171` on surface: passes AA for large text; inline error uses 12px so it is paired with a warning icon to avoid relying on colour alone.
- **`prefers-reduced-motion`:** Modal entrance animation (fade + scale) is disabled; the backdrop blur still applies as it is not motion-based.
