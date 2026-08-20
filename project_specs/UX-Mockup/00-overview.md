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
