---
phase: 03-polish-developer-experience
verified: 2026-07-17T00:00:00Z
status: gaps_found
score: 3/6 criteria verified
gaps:
  - truth: "Starting with LLM_PROVIDER=openai but no OPENAI_API_KEY causes immediate CRITICAL log and sys.exit(1)"
    status: failed
    reason: "_validate_settings_at_startup() is defined in config.py but never called anywhere. The server will fail to start (ValidationError propagates in lifespan), but the CRITICAL log and sys.exit(1) are never executed."
    artifacts:
      - path: "backend/app/config.py"
        issue: "_validate_settings_at_startup() defined at line 188 but no call site exists anywhere in the codebase"
      - path: "backend/app/main.py"
        issue: "lifespan calls get_settings() with no try/except — ValidationError propagates as unhandled exception (uvicorn traceback), not CRITICAL log"
    missing:
      - "Call _validate_settings_at_startup() at module level in config.py (add `_validate_settings_at_startup()` after its definition)"
      - "OR wrap get_settings() in lifespan with try/except ValidationError → logging.critical + sys.exit(1)"

  - truth: "Startup log shows all 17 parameters when running with defaults only"
    status: failed
    reason: "log_startup_config() logs only 10 of 18 parameters unconditionally (plus 2 conditionally). Six parameters are never logged: LLM_TEMPERATURE, EMBEDDING_PROVIDER, CHAT_HISTORY_TURNS, UPLOADS_DIR, DATABASE_URL, LOG_LEVEL."
    artifacts:
      - path: "backend/app/config.py"
        issue: "log_startup_config() (lines 150–176) omits LLM_TEMPERATURE, EMBEDDING_PROVIDER, CHAT_HISTORY_TURNS, UPLOADS_DIR, DATABASE_URL, LOG_LEVEL from output"
    missing:
      - "Add LLM_TEMPERATURE, EMBEDDING_PROVIDER, CHAT_HISTORY_TURNS, UPLOADS_DIR, DATABASE_URL, LOG_LEVEL to log_startup_config()"

  - truth: "WCAG 2.1 AA — dialogs are accessible to screen readers"
    status: failed
    reason: "Both DeleteConfirmDialog and ClearChatDialog apply aria-hidden='true' to the modal-overlay div (the PARENT of the role='dialog' element). aria-hidden propagates to all descendants, making the dialog invisible to assistive technology. The useFocusTrap correctly traps keyboard focus but screen readers cannot perceive the dialog content at all."
    artifacts:
      - path: "frontend/src/components/documents/DeleteConfirmDialog.tsx"
        issue: "Line 51: modal-overlay div has aria-hidden='true'; child dialog at line 56 with role='dialog' is therefore also hidden from AT"
      - path: "frontend/src/components/chat/ClearChatDialog.tsx"
        issue: "Line 48: same pattern — modal-overlay aria-hidden='true' hides the child dialog from screen readers"
    missing:
      - "Remove aria-hidden='true' from the .modal-overlay div in both dialogs"
      - "role='dialog' + aria-modal='true' on the inner .modal-dialog is sufficient to scope AT — no aria-hidden on overlay needed"
human_verification:
  - test: "Mobile upload → cited answer on 320px viewport"
    expected: "FAB visible, tap opens 60vh drawer, UploadZone shows 'Tap to browse files', upload succeeds, READY badge appears, question input accepts text, Enter sends, cited answer arrives"
    why_human: "Requires real mobile browser or device emulation; touch events and CSS media queries cannot be verified programmatically"
  - test: "Keyboard-only full workflow"
    expected: "Tab reaches all interactive elements in logical order, Enter activates upload zone, focus never lost outside dialogs, dialogs trap Tab correctly and restore focus on close"
    why_human: "Requires live browser keyboard interaction to verify tab order and focus management"
  - test: "Lighthouse ≥ 90 accessibility score"
    expected: "Lighthouse accessibility audit returns ≥ 90; axe-core reports zero critical WCAG AA violations"
    why_human: "Requires running Lighthouse against a live served app; cannot be inferred from static code analysis. Note: the aria-hidden modal bug (Gap #3) would likely cause axe-core violations."
  - test: "Config pickup with anthropic provider"
    expected: "Starting backend with LLM_PROVIDER=anthropic, ANTHROPIC_API_KEY=sk-ant-xxx, CHUNK_SIZE=300, TOP_K=8, LLM_TEMPERATURE=0.2 shows all values in startup log"
    why_human: "Requires running the server with a specific .env to observe log output"
---

# Phase 03 — Verification Report

**Phase Goal:** The application is production-quality: it works correctly on mobile and tablet viewports, meets WCAG 2.1 AA accessibility standards, and is fully configurable by a developer via `.env` without touching application code.

**Verified:** 2026-07-17T00:00:00Z  
**Status:** `gaps_found`  
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Mobile upload → cited answer (320px viewport) | ✓ VERIFIED (code) | FAB present, drawer CSS defined, UploadZone touch detection, drag-to-dismiss. Needs human test for E2E. |
| 2 | Keyboard-only navigation | ⚠️ PARTIAL | Focus traps, skip links, ARIA labels all present. `aria-hidden='true'` on modal overlay hides dialogs from AT (see Gap #3). FAB invisible-but-tabbable on desktop. Needs human test. |
| 3 | Lighthouse ≥ 90 (WCAG AA) | ✗ FAILED | `aria-hidden='true'` on modal-overlay propagates to child `role="dialog"` — hides dialogs from screen readers, violating WCAG 4.1.2. No Lighthouse run possible without live app. |
| 4 | Config pickup without code changes | ✓ VERIFIED | Pydantic BaseSettings reads from `.env`; all 18 fields defined; validators for all tuneable params; `log_startup_config()` called in lifespan. |
| 5 | Defaults-only start shows all 17 params in log | ✗ FAILED | `log_startup_config()` only logs 10/18 params unconditionally. Missing: `LLM_TEMPERATURE`, `EMBEDDING_PROVIDER`, `CHAT_HISTORY_TURNS`, `UPLOADS_DIR`, `DATABASE_URL`, `LOG_LEVEL`. |
| 6 | Hard fail on missing key → CRITICAL + sys.exit(1) | ✗ FAILED | `_validate_settings_at_startup()` is defined but **never called**. Server will crash (ValidationError in lifespan), but without CRITICAL log or sys.exit(1). |

**Score: 3/6** truths verified (SC1 code-verified, SC4 code-verified; SC2 partially verified pending human test)

---

## Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `backend/app/config.py` | ✓ VERIFIED | 18-field Pydantic BaseSettings, 9 validators (5 field, 3 model), lru_cache singleton, log_startup_config |
| `backend/.env.example` | ✓ VERIFIED | All 17 uncommented params (ANTHROPIC_API_KEY commented as optional) with inline comments and defaults |
| `backend/app/main.py` | ✓ VERIFIED | Uses `get_settings()` + `log_startup_config()` in lifespan |
| `frontend/src/styles/globals.css` | ✓ VERIFIED | Mobile `<600px` breakpoint with FAB/drawer, tablet `600–1023px` with icon-strip, focus-visible outline, skip-link, rem typography, color tokens |
| `frontend/src/components/layout/AppLayout.tsx` | ✓ VERIFIED | Skip link, ARIA landmarks, tablet toggle+localStorage, mobile drawer+FAB, drawer backdrop, Escape-to-close |
| `frontend/src/components/documents/DocumentPanel.tsx` | ✓ VERIFIED | Touch drag-to-dismiss, localStorage collapse state, drawer handle |
| `frontend/src/components/documents/DocumentCard.tsx` | ✓ VERIFIED | ARIA labels on delete button, processing-aware disable state |
| `frontend/src/components/documents/DeleteConfirmDialog.tsx` | ⚠️ STUB (WCAG) | Focus trap ✓, Escape key ✓, role=dialog ✓ — BUT `aria-hidden='true'` on overlay parent hides dialog from AT |
| `frontend/src/components/upload/UploadZone.tsx` | ✓ VERIFIED | `role="button"`, ARIA label adapts to touch/desktop, keyboard Enter/Space activation |
| `frontend/src/components/chat/ChatPanel.tsx` | ✓ VERIFIED | Delegates to ChatInput, MessageThread, ClearChatDialog |
| `frontend/src/components/chat/MessageThread.tsx` | ✓ VERIFIED | `role="log"` + `aria-live="polite"` + `aria-label="Chat messages"` |
| `frontend/src/components/chat/TypingIndicator.tsx` | ✓ VERIFIED | `role="status"` + `aria-label="Assistant is typing"` |
| `frontend/src/components/chat/ChatInput.tsx` | ✓ VERIFIED | `id="chat-input"` matches skip-link target, `aria-label`, 44px minHeight, Enter-to-send |
| `frontend/src/components/chat/ClearChatDialog.tsx` | ⚠️ STUB (WCAG) | Same `aria-hidden='true'`-on-overlay anti-pattern as DeleteConfirmDialog |
| `frontend/src/components/feedback/Toast.tsx` | ✓ VERIFIED | `role="alert"` for errors, `role="status"` for info/success; `aria-live` differentiation |
| `frontend/src/hooks/useFocusTrap.ts` | ✓ VERIFIED | Traps Tab/Shift+Tab, focuses first element on open, restores focus on close |
| `frontend/src/App.tsx` | ⚠️ WARNING | Skip link duplicated — App.tsx renders one and AppLayout.tsx renders another; user hits two skip links when tabbing |
| `frontend/index.html` | ✓ VERIFIED | `lang="en"`, responsive viewport meta with `viewport-fit=cover` |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| AppLayout | DocumentPanel | `onDrawerClose` prop | ✓ WIRED | `closeDrawer` passed as `onDrawerClose`; drag-to-dismiss calls it |
| AppLayout → FAB | Drawer CSS | `.fab-documents` class | ⚠️ PARTIAL | FAB correctly styled at `<600px`; **no `display:none` rule exists for `≥600px`** — SUMMARY claims `@media (min-width: 600px) { .fab-documents { display: none; } }` exists but it does not; FAB is invisible (unstyled) but present in tab order on desktop |
| config.py → main.py | Startup validation | `_validate_settings_at_startup()` | ✗ NOT WIRED | Function defined but never called; lifespan calls `get_settings()` unguarded |
| config.py | log_startup_config | Called in lifespan | ✓ WIRED | `log_startup_config(settings)` called in `lifespan()` |
| DeleteConfirmDialog | useFocusTrap | `useFocusTrap(dialogRef, open)` | ✓ WIRED | Focus trap active on inner `.modal-dialog` div |
| ClearChatDialog | useFocusTrap | `useFocusTrap(dialogRef, open)` | ✓ WIRED | Same pattern as DeleteConfirmDialog |
| ChatInput textarea | skip-link target | `id="chat-input"` | ✓ WIRED | Skip link `href="#chat-input"` resolves to textarea |

---

## Gaps Summary

### Gap 1 (BLOCKER): `_validate_settings_at_startup()` never invoked — SC6 hard-fail behavior absent

**File:** `backend/app/config.py` line 188  
**Problem:** The function is defined with the correct `sys.exit(1)` logic and CRITICAL logging, but there is no call site. Grepping the entire backend codebase finds zero invocations. The PLAN specifies this should be called "in create_app() or module-level before app creation" — neither happens.

**Observed behavior when key is missing:** `get_settings()` in `lifespan()` raises `pydantic.ValidationError` → unhandled exception propagates → uvicorn logs a traceback and refuses to serve → server does not start. The server *won't* start, but the CRITICAL log and sys.exit(1) are not produced.

**Fix:** Add one line at module level in `config.py` after the function definition:
```python
_validate_settings_at_startup()
```

---

### Gap 2 (WARNING): Startup log omits 6 of 18 configuration parameters — SC5 "all 17 params" not satisfied

**File:** `backend/app/config.py` `log_startup_config()` (lines 150–176)  
**Parameters logged (10):** `LLM_PROVIDER`, `LLM_MODEL`, `EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `MAX_DOCS_PER_SESSION`, `MAX_FILE_SIZE_MB`, `VECTOR_STORE`, `VECTOR_STORE_PATH`  
**Parameters NOT logged (6):** `LLM_TEMPERATURE`, `EMBEDDING_PROVIDER`, `CHAT_HISTORY_TURNS`, `UPLOADS_DIR`, `DATABASE_URL`, `LOG_LEVEL`  
**API keys:** only logged if non-empty (correct for security), but this means with only OpenAI key set, only one conditional line appears.

**Fix:** Add a fourth logger.info line logging the missing six parameters.

---

### Gap 3 (BLOCKER for WCAG criterion): `aria-hidden="true"` on modal-overlay hides dialogs from screen readers — SC3 WCAG AA violated

**Files:** `DeleteConfirmDialog.tsx` line 51, `ClearChatDialog.tsx` line 48  
**Problem:** The pattern `<div className="modal-overlay" aria-hidden="true">...<div role="dialog" aria-modal="true">` is an ARIA anti-pattern. `aria-hidden="true"` propagates to ALL descendants per the ARIA specification; the `role="dialog"` element inside it is therefore hidden from assistive technology. Screen reader users cannot perceive the dialog at all, making it impossible for them to dismiss or interact with it. This violates WCAG 2.1 SC 4.1.2 (Name, Role, Value) and SC 1.3.1 (Info and Relationships).

The SUMMARY document's justification ("overlay gets aria-hidden so screen readers only interact with dialog content") inverts the correct ARIA semantics.

**Fix:** Remove `aria-hidden="true"` from both modal-overlay divs. The `role="dialog" aria-modal="true"` on the inner div is the correct mechanism. When `aria-modal="true"` is set, conforming screen readers already scope browsing to the dialog. The backdrop/overlay does not need `aria-hidden`.

---

### Gap 4 (WARNING): FAB button lacks `display:none` on tablet/desktop — SUMMARY claim is false

**File:** `frontend/src/styles/globals.css`  
**Problem:** The SUMMARY states "hidden on tablet/desktop via `@media (min-width: 600px) { .fab-documents { display: none; } }`" — this CSS rule **does not exist**. The `.fab-documents` class is only defined inside `@media (max-width: 599px)`. On desktop/tablet, the FAB renders as an unstyled (transparent, no-border) inline button sized ~22px (SVG content size). It is invisible visually but still reachable via keyboard Tab, which can be confusing for desktop keyboard users who encounter a nameless-seeming interactive element.

**Fix:** Add to `globals.css` above the mobile breakpoint:
```css
/* FAB visible only on mobile */
.fab-documents { display: none; }
@media (max-width: 599px) {
  .fab-documents { display: flex; ... }
}
```

---

### Gap 5 (WARNING): Duplicate skip links — App.tsx and AppLayout.tsx both render one

**Files:** `App.tsx` lines 100–107, `AppLayout.tsx` lines 139–146  
**Problem:** Both components render a `<a href="#chat-input" className="skip-link">Skip to main content</a>`. When AppLayout renders inside AppInner, the DOM contains two skip links. A keyboard user pressing Tab from the document root will encounter the skip link twice — confusing and redundant.

**Fix:** Remove the skip link from `AppLayout.tsx` (lines 138–146); it is already provided by `App.tsx` as the first focusable element.

---

## Human Verification Required

### 1. Mobile Upload → Cited Answer (End-to-End)

**Test:** Open app in Chrome DevTools at 320px wide viewport (iPhone SE). Locate the FAB (floating action button, bottom-right). Tap it. Verify the document panel opens as a 60vh bottom drawer. Tap "Tap to browse files" in the upload zone. Select a PDF. Wait for the READY badge to appear on the document card. Type a question in the chat input. Press Enter. Verify a cited answer appears with a "Sources" toggle.

**Expected:** Full Phase 2 functionality works at 320px. Touch targets are ≥44px. Drag-to-dismiss (swipe down 100px+) closes the drawer.

**Why human:** CSS media queries, touch events, FAB positioning, and drawer animation require a live mobile viewport.

---

### 2. Keyboard-Only Navigation (Full Workflow)

**Test:** Open app in desktop browser, focus document, use only Tab/Shift+Tab/Enter/Space/Escape.
- Tab: first stop should be "Skip to main content" link (if Gap #5 duplicate is fixed: only once)
- Tab to upload zone → Enter/Space opens file dialog
- After upload, Tab to chat textarea → type question → Enter sends
- After response, Tab to "Sources" button → Enter toggles citations
- Tab to delete button on a document card → Enter opens dialog → Tab between Cancel/Delete → Enter to confirm → focus should return to document panel

**Expected:** No keyboard traps (except inside modal dialogs), no lost focus, all interactive elements reachable in logical DOM order.

**Why human:** Tab order and focus management require a live browser to observe.

---

### 3. Lighthouse ≥ 90 Accessibility Score

**Test:** Serve the app (`npm run dev` + `uvicorn app.main:app`). Open Chrome DevTools → Lighthouse → Accessibility. Run audit. Also run `axe-core` extension.

**Expected:** Lighthouse ≥ 90. axe-core zero critical violations.

**Why human:** Requires live served app. Note: Gap #3 (`aria-hidden` on modal overlay) is expected to produce axe violations for the dialog accessibility if not fixed.

---

### 4. Config Pickup Confirmation

**Test:** Create `backend/.env` with `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=sk-ant-xxx`, `CHUNK_SIZE=300`, `TOP_K=8`, `LLM_TEMPERATURE=0.2`. Start backend. Check startup log.

**Expected:** Log shows `LLM Provider: anthropic`, `Chunk Size: 300`, `Top-k: 8`. No code changes needed.

**Why human:** Requires running server with custom .env to observe log output.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/app/config.py` | 188 | `_validate_settings_at_startup()` defined but never called | 🛑 Blocker | SC6 fails: CRITICAL log and sys.exit(1) never executed |
| `backend/app/config.py` | 150–176 | `log_startup_config()` omits 6 params | ⚠️ Warning | SC5 fails: "all 17 params" claim is false |
| `frontend/src/components/documents/DeleteConfirmDialog.tsx` | 51 | `aria-hidden="true"` on parent of `role="dialog"` | 🛑 Blocker (WCAG) | Dialog invisible to screen readers; WCAG 4.1.2 violation |
| `frontend/src/components/chat/ClearChatDialog.tsx` | 48 | Same `aria-hidden="true"` anti-pattern | 🛑 Blocker (WCAG) | Same violation |
| `frontend/src/styles/globals.css` | — | Missing `.fab-documents { display: none; }` global rule | ⚠️ Warning | SUMMARY claim false; FAB in tab order on desktop (invisible) |
| `frontend/src/App.tsx` + `AppLayout.tsx` | 102, 141 | Duplicate skip links | ⚠️ Warning | Two "Skip to main content" links encountered on first Tab |

---

## Overall Assessment

The phase achieves **mobile responsive layout** (SC1) and **developer config pickup** (SC4) solidly. The Pydantic `BaseSettings` with validators is well-implemented, `.env.example` is comprehensive, and mobile/tablet CSS breakpoints are correctly structured.

**Three gaps block full goal achievement:**

1. **SC6 (BLOCKER):** The startup hard-fail mechanism (`_validate_settings_at_startup()`) exists but is dead code — it's never invoked. One-line fix.

2. **SC5 (WARNING):** The startup log is incomplete — 6 of 18 parameters are missing, so the criterion "log shows all 17 parameters" is not met.

3. **SC3 (BLOCKER for WCAG):** Both confirmation dialogs use `aria-hidden="true"` on the modal overlay, which silences the dialog content from screen readers via attribute propagation. This is the opposite of the stated intent. The fix is to simply remove those two `aria-hidden` attributes.

Additionally, the FAB button missing a `display:none` global rule (contradicting the SUMMARY's claim) and the duplicate skip link are worth fixing before claiming WCAG AA compliance.

---

*Verified: 2026-07-17*  
*Verifier: Claude (pivota_spec-verifier)*
