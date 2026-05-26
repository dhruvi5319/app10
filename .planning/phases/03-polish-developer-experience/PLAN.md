# Phase 3 Plan: Polish & Developer Experience

**Phase goal:** The application is production-quality: it works correctly on mobile and tablet viewports, meets WCAG 2.1 AA accessibility standards, and is fully configurable by a developer via `.env` without touching application code. Jordan (technical evaluator) can tune every pipeline parameter; Maya can use the product on her phone or tablet.

**Source documents:** FRD F06 (responsive layout + accessibility), F07 (configurable RAG pipeline), ROADMAP Phase 3

**Depends on:** Phase 2 — all React components exist in their final form; all backend pipeline parameters already in code but hard-coded or minimally validated.

---

## Scope Summary

Phase 3 has two independent work streams that can proceed in parallel:

| Stream | What | Files touched |
|--------|------|---------------|
| **F07 — Backend Config** | Harden `Settings`, add full startup validation, structured log, `.env.example` | `backend/app/config.py`, `backend/.env.example`, all service files (read-through) |
| **F06 — Frontend Polish** | Responsive breakpoints, accessibility ARIA + keyboard nav, focus traps, skip link | All `frontend/src/components/**` + `globals.css` |

These streams are independent — F07 touches only backend Python; F06 touches only frontend React. They can be planned and executed in parallel waves.

---

## Target Changes (Delta from Phase 2)

### Backend changes (F07)

```
backend/
├── app/
│   └── config.py          # MODIFIED: full Pydantic BaseSettings with validation, startup log
└── .env.example           # MODIFIED: all 17 parameters documented with defaults + comments
```

### Frontend changes (F06)

```
frontend/src/
├── styles/
│   └── globals.css                  # MODIFIED: breakpoint variables, rem sizing, contrast tokens
├── components/
│   ├── layout/
│   │   └── AppLayout.tsx            # MODIFIED: tablet/mobile breakpoints, drawer state
│   ├── documents/
│   │   ├── DocumentPanel.tsx        # MODIFIED: tablet icon-strip, mobile bottom-drawer
│   │   ├── DocumentCard.tsx         # MODIFIED: touch targets ≥ 44px, aria-labels
│   │   └── DeleteConfirmDialog.tsx  # MODIFIED: focus trap, focus restore
│   ├── upload/
│   │   └── UploadZone.tsx           # MODIFIED: touch fallback, role/aria-label
│   ├── chat/
│   │   ├── ChatPanel.tsx            # MODIFIED: role="main", aria-label
│   │   ├── MessageThread.tsx        # MODIFIED: role="log" aria-live="polite"
│   │   ├── MessageBubble.tsx        # MODIFIED: rem font sizes, semantic structure
│   │   ├── TypingIndicator.tsx      # MODIFIED: role="status" aria-label
│   │   ├── ChatInput.tsx            # MODIFIED: keyboard shortcuts documented, aria
│   │   └── ClearChatDialog.tsx      # MODIFIED: focus trap, focus restore
│   └── feedback/
│       └── Toast.tsx                # MODIFIED: role="alert" or role="status"
├── App.tsx                          # MODIFIED: skip link as first DOM element
└── index.html                       # MODIFIED: <html lang="en">, viewport meta
```

---

## Tasks

---

### T01 — Harden Backend `config.py` (F07 full implementation)

**What it delivers:** The complete Pydantic `BaseSettings` with all 17 configurable parameters, startup validation (required keys, range checks, path writability), auto-correction for out-of-range values, sanitised startup INFO log, and a fully documented `.env.example`.

**Files:**

| File | Content |
|------|---------|
| `backend/app/config.py` | Full `Settings(BaseSettings)` with validators + `log_startup_config()` |
| `backend/.env.example` | All 17 parameters with comments and defaults |

**`config.py` complete `Settings` model:**

```python
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging, os, sys

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.0

    # Embedding
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Pipeline tuning
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5
    CHAT_HISTORY_TURNS: int = 10

    # Limits
    MAX_FILE_SIZE_MB: int = 20
    MAX_DOCS_PER_SESSION: int = 10

    # Storage
    VECTOR_STORE: str = "chromadb"
    VECTOR_STORE_PATH: str = "./data/chroma"
    UPLOADS_DIR: str = "./uploads"
    DATABASE_URL: str = "rag_chatbot.db"

    # Server
    LOG_LEVEL: str = "INFO"
```

**Validators to implement (all in `config.py`):**

| Validator | Mode | Behaviour |
|-----------|------|-----------|
| `validate_llm_provider` | `field_validator('LLM_PROVIDER')` | Not in `{'openai','anthropic'}` → `ValueError` with exact FRD message |
| `validate_vector_store` | `field_validator('VECTOR_STORE')` | Not in `{'chromadb','faiss'}` → `ValueError` with exact FRD message |
| `clamp_top_k` | `field_validator('TOP_K')` | Outside 1–20 → clamp + `logging.warning(f"TOP_K={v} out of range [1, 20]; using {clamped}.")` |
| `clamp_temperature` | `field_validator('LLM_TEMPERATURE')` | Outside 0.0–2.0 → clamp + WARNING |
| `clamp_file_size` | `field_validator('MAX_FILE_SIZE_MB')` | Outside 1–100 → clamp + WARNING |
| `clamp_chunk_size` | `field_validator('CHUNK_SIZE')` | Outside 100–2000 → clamp + WARNING |
| `fix_chunk_overlap` | `model_validator(mode='after')` | `CHUNK_OVERLAP >= CHUNK_SIZE` → set `CHUNK_OVERLAP = CHUNK_SIZE // 10` + WARNING |
| `validate_api_keys` | `model_validator(mode='after')` | `LLM_PROVIDER='openai'` and `OPENAI_API_KEY==''` → `ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")`; same for anthropic |
| `validate_paths` | `model_validator(mode='after')` | For `VECTOR_STORE_PATH` and `UPLOADS_DIR`: `os.makedirs(path, exist_ok=True)`; test writability with `os.access(path, os.W_OK)`; fail with `ValueError` if not writable |

**`log_startup_config(settings: Settings) -> None`:**

```python
def log_startup_config(settings: Settings) -> None:
    def redact(key: str) -> str:
        if not key or len(key) < 4:
            return "****"
        return f"...{key[-4:]}"

    logger = logging.getLogger("config")
    logger.info(
        f"[CONFIG] LLM Provider: {settings.LLM_PROVIDER} | "
        f"Model: {settings.LLM_MODEL} | "
        f"Embedding: {settings.EMBEDDING_MODEL}"
    )
    logger.info(
        f"[CONFIG] Chunk Size: {settings.CHUNK_SIZE} | "
        f"Overlap: {settings.CHUNK_OVERLAP} | "
        f"Top-k: {settings.TOP_K} | "
        f"Max Docs: {settings.MAX_DOCS_PER_SESSION} | "
        f"Max File MB: {settings.MAX_FILE_SIZE_MB}"
    )
    logger.info(
        f"[CONFIG] Vector Store: {settings.VECTOR_STORE} | "
        f"Storage: {settings.VECTOR_STORE_PATH}"
    )
    if settings.OPENAI_API_KEY:
        logger.info(f"[CONFIG] OpenAI API Key: {redact(settings.OPENAI_API_KEY)}")
    if settings.ANTHROPIC_API_KEY:
        logger.info(f"[CONFIG] Anthropic API Key: {redact(settings.ANTHROPIC_API_KEY)}")
```

**Startup integration (`main.py` lifespan):**

```python
# In lifespan context manager, after init_db():
settings = get_settings()
log_startup_config(settings)
```

**`ValidationError` → startup exit integration:**

```python
# In create_app() or module-level before app creation:
try:
    settings = get_settings()
except ValidationError as e:
    for err in e.errors():
        logging.critical(f"[CONFIG ERROR] {err['msg']}")
    sys.exit(1)
```

**`.env.example` full content:**

```dotenv
# ─── LLM Provider ───────────────────────────────────────────────────────────
# Supported: openai, anthropic
LLM_PROVIDER=openai

# Required when LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Required when LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# LLM model name (any valid model ID for the selected provider)
LLM_MODEL=gpt-4o

# LLM temperature: 0.0 (deterministic) to 2.0 (creative). Range clamped automatically.
LLM_TEMPERATURE=0.0

# ─── Embedding ──────────────────────────────────────────────────────────────
# Supported: openai, sentence-transformers
EMBEDDING_PROVIDER=openai

# Embedding model (any valid model ID for the selected embedding provider)
EMBEDDING_MODEL=text-embedding-3-small

# ─── RAG Pipeline Tuning ────────────────────────────────────────────────────
# Maximum tokens per chunk (100–2000, clamped automatically)
CHUNK_SIZE=500

# Token overlap between consecutive chunks (0–500, must be < CHUNK_SIZE)
CHUNK_OVERLAP=50

# Number of chunks retrieved per query (1–20, clamped automatically)
TOP_K=5

# Number of prior conversation turns included in LLM context (0–50)
CHAT_HISTORY_TURNS=10

# ─── Limits ─────────────────────────────────────────────────────────────────
# Maximum file size per upload in MB (1–100, clamped automatically)
MAX_FILE_SIZE_MB=20

# Maximum documents per session (1–50)
MAX_DOCS_PER_SESSION=10

# ─── Storage ─────────────────────────────────────────────────────────────────
# Vector store backend. Supported: chromadb, faiss
VECTOR_STORE=chromadb

# Directory for vector store persistence (must be writable)
VECTOR_STORE_PATH=./data/chroma

# Directory for raw uploaded files (must be writable)
UPLOADS_DIR=./uploads

# SQLite database filename
DATABASE_URL=rag_chatbot.db

# ─── Server ──────────────────────────────────────────────────────────────────
# Logging level. Supported: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

**Acceptance criteria:**
- [ ] `get_settings()` with a valid `.env` resolves all parameters correctly
- [ ] `LLM_PROVIDER=badvalue` → startup fails with `CRITICAL` log and `sys.exit(1)`
- [ ] `OPENAI_API_KEY` missing with `LLM_PROVIDER=openai` → startup exits with `CRITICAL`
- [ ] `TOP_K=99` → clamped to 20 + WARNING logged; server starts normally
- [ ] `CHUNK_OVERLAP=600`, `CHUNK_SIZE=500` → overlap auto-corrected to 50 + WARNING
- [ ] `log_startup_config()` outputs 3 INFO lines; API keys shown as `...XXXX` (last 4 only)
- [ ] `VECTOR_STORE_PATH=/nonexistent/readonly` → startup fails with `CRITICAL`
- [ ] Server starts with no `.env` (only `OPENAI_API_KEY` in environment) using all defaults

---

### T02 — Responsive Layout: Tablet Breakpoint (F06-B)

**What it delivers:** Tablet layout (600–1023 px): Document Panel collapses to 48 px icon strip by default; toggle expands to full 280 px overlay; chat fills full width when panel is collapsed. CSS-only breakpoints, no JavaScript resize listeners.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/components/layout/AppLayout.tsx` | Tablet breakpoint state + CSS variables |
| `frontend/src/styles/globals.css` | `@media` breakpoint definitions |

**CSS breakpoints to add (`globals.css`):**

```css
/* Breakpoint variables — update layout via CSS custom properties */
:root {
  --panel-width: 280px;
  --panel-collapsed-width: 48px;
}

/* Tablet: 600px–1023px */
@media (max-width: 1023px) and (min-width: 600px) {
  /* Document panel collapses to icon strip by default unless .panel-expanded */
  .doc-panel { width: var(--panel-collapsed-width); }
  .doc-panel.panel-expanded { width: var(--panel-width); position: absolute; z-index: 100; height: 100%; }
  .doc-panel .panel-content { display: none; }
  .doc-panel.panel-expanded .panel-content { display: flex; }
}

/* Mobile: < 600px */
@media (max-width: 599px) {
  .doc-panel { display: none; }
  .doc-panel.drawer-open {
    display: flex; flex-direction: column;
    position: fixed; bottom: 0; left: 0; right: 0;
    height: 60vh; z-index: 200;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    background: var(--color-surface);
  }
}
```

**`AppLayout.tsx` tablet behaviour:**

```tsx
// Panel toggle state: isPanelExpanded (default: false on tablet)
// On viewport ≥ 1024px: always expanded (CSS handles it), toggle hidden
// On tablet (600-1023px): show toggle button (chevron-right / chevron-left icon)
//   toggle sets isPanelExpanded; CSS class .panel-expanded controls width
// Persist isPanelExpanded in localStorage key 'doc_panel_tablet_expanded'
//
// Toggle button: positioned at right edge of icon-strip
//   aria-label={isPanelExpanded ? "Collapse document panel" : "Expand document panel"}
```

**Acceptance criteria:**
- [ ] At 768 px viewport: Document Panel renders as 48 px icon strip (icons only, no text)
- [ ] Clicking toggle at 768 px: panel expands to 280 px as overlay over chat
- [ ] Chat fills full width when panel is in collapsed icon-strip state
- [ ] At 1440 px: both panels always visible; toggle button hidden
- [ ] Panel expanded state persisted in `localStorage` between navigations

---

### T03 — Responsive Layout: Mobile Breakpoint (F06-C)

**What it delivers:** Mobile layout (< 600 px): Document Panel hidden by default; "Documents" floating action button (FAB) opens it as a bottom drawer at 60% viewport height with a drag-to-dismiss handle. Touch-friendly upload (tap-to-upload, no drag needed). All touch targets ≥ 44 × 44 px.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/components/layout/AppLayout.tsx` | Mobile drawer state |
| `frontend/src/components/documents/DocumentPanel.tsx` | Bottom drawer + drag-to-dismiss handle |
| `frontend/src/components/upload/UploadZone.tsx` | Touch tap-to-upload fallback |
| `frontend/src/styles/globals.css` | Mobile utilities (FAB, drawer, touch targets) |

**`AppLayout.tsx` mobile behaviour:**

```tsx
// isDrawerOpen: boolean state (default: false)
//
// On mobile (< 600px):
//   - Render <ChatPanel> at full viewport width
//   - Render FAB button: bottom-right corner, 56×56px, "Documents" label + icon
//     onClick: setIsDrawerOpen(true)
//     aria-label="Open document library"
//   - When isDrawerOpen: render <DocumentPanel> with className="drawer-open"
//     + backdrop overlay (click backdrop → close drawer)
//   - Drag-to-dismiss: touch swipe down > 100px → close drawer
```

**Touch target enforcement (`globals.css`):**

```css
/* All buttons and interactive elements on mobile */
@media (max-width: 599px) {
  button, [role="button"], input[type="file"] + label {
    min-height: 44px;
    min-width: 44px;
  }
  /* FAB */
  .fab-documents {
    position: fixed; bottom: 24px; right: 24px;
    width: 56px; height: 56px; border-radius: 50%;
    background: var(--color-accent);
    box-shadow: var(--shadow-card);
    display: flex; align-items: center; justify-content: center;
    z-index: 150;
  }
}
```

**Bottom drawer drag-to-dismiss:**

```tsx
// DocumentPanel gets a drag handle at top:
//   <div className="drawer-handle" aria-label="Drag to close" />
// CSS: 4px wide pill, centred, 24px from top
//
// Touch event handlers on the drawer:
//   onTouchStart: record startY
//   onTouchMove: if (currentY - startY > 100) trigger close
//   onTouchEnd: reset
```

**`UploadZone.tsx` touch fallback:**

```tsx
// Detect touch device: 'ontouchstart' in window
// On touch device:
//   - DragOver/DragLeave/Drop handlers still present (for hybrid devices)
//   - Hidden file input click is the primary interaction
//   - Zone label: "Tap to browse files" (instead of "Drag files here or click to browse")
//   - Drag-and-drop instruction text hidden on mobile
```

**Acceptance criteria:**
- [ ] At 320 px viewport: Document Panel is not visible; FAB is present in bottom-right
- [ ] Tapping FAB: bottom drawer slides up to 60% viewport height
- [ ] Tapping backdrop or swiping drawer down > 100 px: drawer closes
- [ ] Upload zone at 320 px shows "Tap to browse" label; tapping opens file picker
- [ ] All buttons at 320 px are ≥ 44 × 44 px (verifiable via DevTools computed size)
- [ ] Chat input is usable at 320 px without horizontal scrolling

---

### T04 — Accessibility: ARIA, Keyboard Nav, Focus Management (F06-F through F06-J)

**What it delivers:** Full WCAG 2.1 AA compliance for keyboard navigation, screen reader support, focus trapping in modals, skip navigation link, semantic HTML landmarks, and `rem`-based font sizing. Zero axe-core critical violations.

**Files:**

| File | What changes |
|------|-------------|
| `frontend/index.html` | Add `<html lang="en">`, correct viewport meta |
| `frontend/src/App.tsx` | Skip link as first DOM element |
| `frontend/src/components/layout/AppLayout.tsx` | `<main>`, `<aside>` landmarks + `aria-label` |
| `frontend/src/components/upload/UploadZone.tsx` | `role="button"`, `aria-label`, keyboard activation |
| `frontend/src/components/chat/MessageThread.tsx` | `role="log"` + `aria-live="polite"` |
| `frontend/src/components/chat/TypingIndicator.tsx` | `role="status"` + `aria-label="Assistant is typing"` |
| `frontend/src/components/chat/ChatInput.tsx` | `aria-label` on textarea + button |
| `frontend/src/components/chat/ChatPanel.tsx` | Toolbar accessible labels |
| `frontend/src/components/documents/DocumentCard.tsx` | `aria-label` on icon buttons, status meaning |
| `frontend/src/components/documents/DeleteConfirmDialog.tsx` | Focus trap + restore |
| `frontend/src/components/chat/ClearChatDialog.tsx` | Focus trap + restore |
| `frontend/src/components/feedback/Toast.tsx` | `role="alert"` or `role="status"` |
| `frontend/src/styles/globals.css` | Focus ring, rem units, contrast |

**Skip link implementation (`App.tsx`):**

```tsx
// First DOM child inside <body> (before all other content):
<a
  href="#chat-input"
  className="skip-link"
  onFocus={(e) => e.currentTarget.classList.add('skip-link-visible')}
  onBlur={(e) => e.currentTarget.classList.remove('skip-link-visible')}
>
  Skip to main content
</a>
```

```css
/* globals.css */
.skip-link {
  position: absolute; top: -100px; left: 8px;
  background: var(--color-accent); color: white;
  padding: 8px 16px; border-radius: var(--radius-sm);
  text-decoration: none; z-index: 9999;
  transition: top 0.1s;
}
.skip-link-visible { top: 8px; }
```

**Landmark structure (`AppLayout.tsx`):**

```tsx
<div className="app-shell">
  <a href="#chat-input" className="skip-link">Skip to main content</a>
  <aside aria-label="Document library" className="doc-panel">
    <DocumentPanel sessionId={sessionId} />
  </aside>
  <main id="main-content" aria-label="Chat interface" className="chat-main">
    <ChatPanel sessionId={sessionId} hasReadyDocument={hasReadyDocument} />
  </main>
</div>
```

**ARIA additions per component:**

| Component | Attribute added | Value |
|-----------|----------------|-------|
| `UploadZone` | `role` | `"button"` |
| `UploadZone` | `tabIndex` | `0` |
| `UploadZone` | `aria-label` | `"File upload area. Press Enter or Space to browse files."` |
| `UploadZone` | `onKeyDown` | `Enter`/`Space` → trigger hidden input click |
| `MessageThread` | `role` | `"log"` |
| `MessageThread` | `aria-live` | `"polite"` |
| `MessageThread` | `aria-label` | `"Chat messages"` |
| `TypingIndicator` | `role` | `"status"` |
| `TypingIndicator` | `aria-label` | `"Assistant is typing"` |
| `ChatInput textarea` | `aria-label` | `"Message input"` |
| `ChatInput send button` | `aria-label` | `"Send message"` |
| `DocumentCard delete button` | `aria-label` | `"Delete {filename}"` (dynamic) |
| `Toast (info/success)` | `role` | `"status"` |
| `Toast (error)` | `role` | `"alert"` |
| `DeleteConfirmDialog` | `role` | `"dialog"` |
| `DeleteConfirmDialog` | `aria-modal` | `"true"` |
| `DeleteConfirmDialog` | `aria-labelledby` | id of heading |
| `ClearChatDialog` | `role` | `"dialog"` |
| `ClearChatDialog` | `aria-modal` | `"true"` |
| `ClearChatDialog` | `aria-labelledby` | id of heading |

**Focus trap hook for modals:**

```typescript
// src/hooks/useFocusTrap.ts
export function useFocusTrap(containerRef: RefObject<HTMLElement>, isActive: boolean): void {
  // When isActive: find all focusable elements in containerRef
  // Trap Tab (cycle forward) and Shift+Tab (cycle backward) within them
  // On activation: focus first element
  // On deactivation: restore focus to previously focused element (stored on activation)
}
```

Both `DeleteConfirmDialog` and `ClearChatDialog` call `useFocusTrap(dialogRef, open)`.

**`globals.css` rem sizing + focus ring:**

```css
/* Replace all px font sizes with rem equivalents */
/* Base: 1rem = browser default (typically 16px) */
body { font-size: 1rem; }
.message-content { font-size: 0.9375rem; }  /* 15px / 16 */
.citation-text { font-size: 0.8125rem; }     /* 13px / 16 */
.timestamp { font-size: 0.75rem; }            /* 12px / 16 */
.status-badge { font-size: 0.6875rem; }       /* 11px / 16 */

/* Visible focus ring on ALL focusable elements */
*:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}
/* Suppress default focus ring only when focus-visible is supported */
*:focus:not(:focus-visible) { outline: none; }
```

**`index.html` fixes:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="description" content="RAG Chatbot — Ask questions about your documents" />
  <title>RAG Chatbot</title>
</head>
```

**Acceptance criteria:**
- [ ] Skip link appears when Tab is pressed from browser address bar; clicking it moves focus to `#chat-input`
- [ ] Tab key cycles through all interactive elements in DOM order without reaching dead ends
- [ ] Enter/Space on the upload zone opens the file picker
- [ ] Delete confirmation dialog: Tab is trapped inside while open; Escape closes dialog; focus returns to delete button
- [ ] `role="log"` + `aria-live="polite"` on MessageThread: screen reader announces new messages without interrupting
- [ ] All icon-only buttons have `aria-label` — no button has only an icon child with no label
- [ ] Font size scales when browser minimum font size is increased to 20 px (all layout remains intact)
- [ ] `<aside>` and `<main>` landmarks present in DOM (verifiable with browser accessibility tree)

---

### T05 — Colour Contrast & WCAG AA Verification (F06-E)

**What it delivers:** Audit of all colour token combinations in use, correction of any that fail WCAG AA contrast ratios (≥ 4.5:1 body text, ≥ 3:1 large text and UI controls), and a verified contrast table.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/styles/globals.css` | Updated colour tokens (if any fail audit) |

**Contrast audit table (verify each pair; update tokens if ratio < threshold):**

| Element | Foreground | Background | Min ratio | Target ratio |
|---------|------------|------------|-----------|-------------|
| Body text | `--color-text-primary` (#e8eaf0) | `--color-bg` (#0f1117) | 4.5:1 | ✓ ~14:1 |
| Secondary text | `--color-text-secondary` (#8b90a0) | `--color-bg` (#0f1117) | 4.5:1 | Verify |
| Muted text | `--color-text-muted` (#5a5f72) | `--color-bg` (#0f1117) | 4.5:1 | May need adjustment |
| User bubble text | `--color-text-primary` | `--color-user-bubble` (#2d3250) | 4.5:1 | Verify |
| Assistant bubble text | `--color-text-primary` | `--color-assistant-bubble` (#1e2235) | 4.5:1 | Verify |
| Accent on dark bg | `--color-accent` (#6c63ff) | `--color-bg` (#0f1117) | 3:1 (UI control) | Verify |
| Status badge text | white | `--color-success` (#34c98b) | 3:1 | Verify; green badges may need darker bg |
| Status badge text | white | `--color-error` (#e5534b) | 3:1 | Verify |
| Status badge text | white | `--color-warning` (#f5a623) | 3:1 | Verify; yellow often fails |

**Verification method:**
- Use browser DevTools → Accessibility → Contrast Ratio inspector on each token pair
- Or compute: relative luminance formula per WCAG 2.1 §1.4.3
- Any failing token: adjust lightness in HSL space until ratio passes, then update `globals.css`

**Status badge dual-encoding (colour + text, per F06 validation rule):**

```tsx
// DocumentCard.tsx — status badge must show BOTH colour AND text label:
// ✓ <span className="badge badge-ready">Ready</span>       (green pill + "Ready" text)
// ✗ <span className="badge badge-ready" aria-label="Ready" /> (colour only — INVALID)
```

**Acceptance criteria:**
- [ ] All foreground/background colour pairs in use achieve their minimum contrast ratio
- [ ] `--color-text-muted` on `--color-bg` achieves ≥ 4.5:1 (adjust if needed; muted text must still be readable)
- [ ] Warning badge (`--color-warning` yellow) background achieves ≥ 3:1 with white text, OR text colour changed to dark (#1a1a1a) for sufficient contrast
- [ ] Status badges show text label in addition to colour (no colour-only status indicators)
- [ ] Running Lighthouse accessibility audit on localhost returns score ≥ 90

---

## Task Dependency Graph

```
Wave 1 (parallel — independent work streams):
  T01 (backend config hardening)   T02 (tablet layout)
         │                                │
         │                         T03 (mobile layout)
         │                                │
         │                         T04 (ARIA + keyboard + focus)
         │                                │
         │                         T05 (contrast audit)
         └────────────────────────────────┘
                    (both complete)
```

**Dependency notes:**
- T01 is entirely backend — no dependency on any frontend task; can proceed in parallel with T02–T05
- T02 must complete before T03 (mobile builds on the collapsed-panel pattern established in T02)
- T04 must run after T02 and T03 (ARIA is added to the responsive components)
- T05 must run after T04 (contrast audit is final; ensures colour adjustments don't break contrast)
- T01 has no downstream — Phase 3 backend work is self-contained

---

## Phase Success Criteria

All of the following must be TRUE before Phase 3 is considered complete:

1. **Mobile upload → answer:** A user on a 320 px viewport taps the Documents FAB, opens the drawer, taps to select and upload a PDF, waits for READY, then types a question in the chat input and receives a cited answer — all core Phase 2 functionality works on mobile.

2. **Keyboard-only navigation:** A keyboard-only user (no mouse) can Tab through all interactive elements — upload a file (Enter on zone), type a question (Tab to textarea, Enter to send), expand a citation (Tab to "Sources", Enter to toggle), delete a document (Tab to delete button, Enter to open dialog, Tab to confirm, Enter to confirm) — all without ever losing focus or reaching a keyboard trap (except inside confirmation dialogs, which trap correctly and release on close).

3. **Lighthouse ≥ 90:** Running the Lighthouse accessibility audit against the live app on `localhost:3000` returns an accessibility score ≥ 90 and axe-core reports zero critical WCAG AA violations.

4. **Config pickup:** A developer creates `.env` with `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=sk-ant-xxx`, `CHUNK_SIZE=300`, `TOP_K=8`, `LLM_TEMPERATURE=0.2`, restarts the backend, and observes the startup log confirming all values were picked up — without any code changes.

5. **Defaults-only start:** Starting the server with no `.env` and only `OPENAI_API_KEY` in the environment produces a working application with all defaults applied; the startup log shows all 17 parameters.

6. **Hard fail on missing key:** Starting the server with `LLM_PROVIDER=openai` but no `OPENAI_API_KEY` causes an immediate `CRITICAL` log and `sys.exit(1)` — the server does not start.
