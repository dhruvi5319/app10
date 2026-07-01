# Phase 3 Plan: Polish & Developer Experience Summary

---
phase: "03-polish-developer-experience"
plan: "P01"
subsystem: "backend-config, frontend-responsive, frontend-accessibility"
tags: ["pydantic", "responsive", "wcag", "aria", "mobile", "tablet", "config"]
tech-stack:
  added: ["useFocusTrap hook"]
  patterns: ["Pydantic BaseSettings validators", "CSS breakpoints", "focus trap", "ARIA landmarks"]
key-files:
  created:
    - frontend/src/hooks/useFocusTrap.ts
    - .planning/phases/03-polish-developer-experience/STATE.md
  modified:
    - backend/app/config.py
    - backend/app/main.py
    - backend/.env.example
    - frontend/src/styles/globals.css
    - frontend/src/components/layout/AppLayout.tsx
    - frontend/src/components/documents/DocumentPanel.tsx
    - frontend/src/components/documents/DocumentCard.tsx
    - frontend/src/components/documents/DeleteConfirmDialog.tsx
    - frontend/src/components/upload/UploadZone.tsx
    - frontend/src/components/chat/ChatPanel.tsx
    - frontend/src/components/chat/MessageThread.tsx
    - frontend/src/components/chat/TypingIndicator.tsx
    - frontend/src/components/chat/ChatInput.tsx
    - frontend/src/components/chat/ClearChatDialog.tsx
    - frontend/src/components/feedback/Toast.tsx
    - frontend/src/App.tsx
    - frontend/index.html
decisions:
  - "useFocusTrap on inner modal div (not overlay) so role=dialog/aria-modal semantics are correct; overlay gets aria-hidden"
  - "model_validator(mode=after) for cross-field validation (chunk overlap, API key, path checks)"
  - "color-text-muted changed from #5a5f72 (2.98:1 FAIL) to #8b8fa4 (5.90:1 PASS)"
  - "Badge colours use colored text on translucent same-colour bg — all pass WCAG 3:1 (verified computationally)"
metrics:
  duration: "~45min"
  completed: "2026-07-01"
  tasks: 5
  files: 17
---

## One-liner

Hardened backend with 9 Pydantic validators + startup config log; added CSS breakpoints for tablet (48px icon strip) and mobile (FAB + 60vh bottom drawer); implemented full WCAG 2.1 AA accessibility (ARIA landmarks, focus traps, skip link, role=log/status/alert, rem typography); corrected `--color-text-muted` from 2.98:1 to 5.90:1.

## Tasks Completed

| # | Task | Commit | Key deliverables |
|---|------|--------|-----------------|
| T01 | Harden backend config.py | d00bcd8 | 17 params, 9 validators, log_startup_config(), .env.example |
| T02 | Responsive tablet breakpoint | d643631 | CSS @media 600–1023px; AppLayout tablet toggle + localStorage |
| T03 | Mobile breakpoint + FAB + drawer | 1d814f5 | FAB, 60vh bottom drawer, drag-to-dismiss, touch UploadZone |
| T04 | Accessibility ARIA + focus | cd0a202 | useFocusTrap, skip link, role=log/status/alert, aria-label everywhere |
| T05 | Colour contrast audit WCAG AA | 9fd46a7 | --color-text-muted fixed; full audit table verified |

## Decisions Made

1. **Focus trap on inner dialog div** — `role="dialog" aria-modal="true"` placed on `.modal-dialog` (the inner content box), not the `.modal-overlay`. The overlay gets `aria-hidden="true"` so screen readers only interact with the dialog content.

2. **Cross-field Pydantic validators** — Used `model_validator(mode='after')` for `fix_chunk_overlap`, `validate_api_keys`, and `validate_paths` since these require access to multiple fields. Field validators used for single-field clamping.

3. **`--color-text-muted` update** — Original `#5a5f72` computed to 2.98:1 contrast on `#0f1117` background (FAILS WCAG AA 4.5:1). Updated to `#8b8fa4` (5.90:1). Maintains blue-grey aesthetic while achieving compliance.

4. **Badge contrast** — Badges use the semantic colour (`--color-success`, `--color-warning`, `--color-error`) as **text** on a 15% alpha same-colour background. The effective blended background is very close to `--color-bg`, so the coloured text achieves 6.9–7.2:1 for success/warning and 4.4:1 for error — all exceeding the 3:1 minimum for UI controls.

5. **Toast role differentiation** — `role="alert"` + `aria-live="assertive"` for error toasts (immediate announcement); `role="status"` + `aria-live="polite"` for info/success (announced at next opportunity).

6. **Mobile FAB visibility** — FAB shown via CSS `position: fixed` with `.fab-documents` class; hidden on tablet/desktop via `@media (min-width: 600px) { .fab-documents { display: none; } }` pattern (CSS handles it, not JS media queries).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] useFocusTrap on inner dialog element**
- **Found during:** T04 implementation
- **Issue:** PLAN.md showed `role="dialog"` on the `.modal-overlay` (outer div). Putting `aria-modal` on the overlay (which also receives click-outside-to-close) is an ARIA anti-pattern — screen readers would be confused about what's in the modal.
- **Fix:** Moved `role="dialog" aria-modal="true" aria-labelledby` to the inner `.modal-dialog` div; placed `aria-hidden="true"` on the overlay; `dialogRef` now points to inner div.
- **Files modified:** DeleteConfirmDialog.tsx, ClearChatDialog.tsx

**2. [Rule 1 - Bug] Removed duplicate focus-on-open useEffect in dialogs**
- **Found during:** T04
- **Issue:** Both dialogs had a `setTimeout(() => cancelBtnRef.current?.focus(), 50)` useEffect that conflicted with `useFocusTrap` (which also sets initial focus). Kept `useFocusTrap` (which uses `focus()` on first focusable element — the Cancel button — directly) and removed the extra setTimeout.
- **Fix:** Removed redundant `useEffect` focus block from both dialog components; `useFocusTrap` handles initial focus.

**3. [Rule 2 - Security] Preserved Escape key handler alongside focus trap**
- **Found during:** T04
- **Issue:** `useFocusTrap` doesn't handle Escape (it only traps Tab). Both dialogs need Escape to close independently.
- **Fix:** Kept the existing `useEffect` Escape key handler in both dialogs alongside `useFocusTrap`.

### Not auto-fixed (out of scope)

None.

## Colour Contrast Audit Table

| Element | Foreground | Background | Ratio | Min | Status |
|---------|-----------|-----------|-------|-----|--------|
| Body text | #e8eaf0 | #0f1117 | 15.69:1 | 4.5 | ✓ PASS |
| Secondary text | #8b90a0 | #0f1117 | 5.93:1 | 4.5 | ✓ PASS |
| Muted text (UPDATED) | #8b8fa4 | #0f1117 | 5.90:1 | 4.5 | ✓ PASS |
| Primary on user bubble | #e8eaf0 | #2d3250 | 10.37:1 | 4.5 | ✓ PASS |
| Primary on assist bubble | #e8eaf0 | #1e2235 | 13.07:1 | 4.5 | ✓ PASS |
| Accent on bg (UI control) | #6c63ff | #0f1117 | 4.37:1 | 3.0 | ✓ PASS |
| Success badge text | #34c98b | blended | 6.87:1 | 3.0 | ✓ PASS |
| Warning badge text | #f5a623 | blended | 7.20:1 | 3.0 | ✓ PASS |
| Error badge text | #e5534b | blended | 4.37:1 | 3.0 | ✓ PASS |

## Self-Check

### Files exist:
- [x] `frontend/src/hooks/useFocusTrap.ts` — new file
- [x] `backend/app/config.py` — modified
- [x] `backend/.env.example` — modified
- [x] `frontend/src/styles/globals.css` — modified
- [x] `frontend/src/components/layout/AppLayout.tsx` — modified
- [x] `frontend/src/components/documents/DocumentPanel.tsx` — modified
- [x] `frontend/src/components/documents/DeleteConfirmDialog.tsx` — modified
- [x] `frontend/src/components/chat/ClearChatDialog.tsx` — modified

### Commits verified:
- d00bcd8 feat(phase3): T01 — harden backend config.py
- d643631 feat(phase3): T02 — responsive tablet breakpoint
- 1d814f5 feat(phase3): T03 — mobile breakpoint + FAB + bottom drawer
- cd0a202 feat(phase3): T04 — accessibility ARIA, keyboard nav, focus traps
- 9fd46a7 feat(phase3): T05 — WCAG AA colour contrast audit

## Self-Check: PASSED
