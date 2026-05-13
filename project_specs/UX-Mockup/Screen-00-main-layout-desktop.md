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
