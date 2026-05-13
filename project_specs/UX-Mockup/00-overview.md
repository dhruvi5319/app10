# UX Mockup: RAG Chatbot

**Project:** RAGChatbot
**Generated:** 2026-05-13
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

### Layout Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  App Header: Logo · Session Controls (Clear Chat, New Session, Export)  │
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

---

*Chunk files: 00-overview.md · Flow-00 through Flow-04 · Screen-00 through Screen-05 · Y0-patterns.md · Y1-responsive.md · Y2-accessibility.md*
