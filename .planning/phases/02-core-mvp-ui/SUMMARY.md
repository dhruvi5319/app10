---
phase: 02-core-mvp-ui
plan: 11
subsystem: ui
tags: [react, typescript, vite, sse, pdf-rag, chat, documents, toast, streaming]

# Dependency graph
requires:
  - phase: 01-foundation-rag-pipeline
    provides: REST and SSE endpoints on localhost:8000 (sessions, documents, chat)
provides:
  - Complete React 18 frontend with Vite + TypeScript
  - Upload workflow with SSE progress tracking and polling fallback
  - Document library panel with status badges and delete confirmation
  - Streaming chat interface with markdown rendering and citations
  - Toast notification system and network error banner
  - Full E2E data flow from session init to streaming LLM response with citations
affects: [03-responsive-polish, 04-production-deploy]

# Tech tracking
tech-stack:
  added:
    - react@18.3.1
    - react-dom@18.3.1
    - react-markdown@9.0.1
    - remark-gfm@4.0.0
    - vite@5.2.11
    - typescript@5.4.5
    - "@vitejs/plugin-react@4.3.1"
  patterns:
    - Custom hooks for all data-fetching (useSession, useDocuments, useChat, useToast)
    - ToastContext provider pattern for cross-component toast dispatch
    - Callback-based prop drilling for network error and hasReadyDocument propagation
    - SSE streaming with polling fallback for document progress
    - Optimistic UI for uploads and chat messages
    - Error sentinel prefix pattern (__ERROR__) for error bubbles in message thread

key-files:
  created:
    - frontend/src/App.tsx
    - frontend/src/main.tsx
    - frontend/src/api/client.ts
    - frontend/src/api/sessions.ts
    - frontend/src/api/documents.ts
    - frontend/src/api/chat.ts
    - frontend/src/hooks/useSession.ts
    - frontend/src/hooks/useDocuments.ts
    - frontend/src/hooks/useChat.ts
    - frontend/src/hooks/useToast.ts
    - frontend/src/hooks/useFocusTrap.ts
    - frontend/src/context/ToastContext.tsx
    - frontend/src/components/layout/AppLayout.tsx
    - frontend/src/components/upload/UploadZone.tsx
    - frontend/src/components/upload/FileProgressBar.tsx
    - frontend/src/components/documents/DocumentPanel.tsx
    - frontend/src/components/documents/DocumentCard.tsx
    - frontend/src/components/documents/DeleteConfirmDialog.tsx
    - frontend/src/components/chat/ChatPanel.tsx
    - frontend/src/components/chat/MessageThread.tsx
    - frontend/src/components/chat/MessageBubble.tsx
    - frontend/src/components/chat/TypingIndicator.tsx
    - frontend/src/components/chat/ChatInput.tsx
    - frontend/src/components/chat/ClearChatDialog.tsx
    - frontend/src/components/citations/CitationSection.tsx
    - frontend/src/components/citations/CitationCard.tsx
    - frontend/src/components/feedback/Toast.tsx
    - frontend/src/components/feedback/ToastContainer.tsx
    - frontend/src/components/feedback/NetworkBanner.tsx
    - frontend/src/types/api.ts
    - frontend/src/utils/constants.ts
    - frontend/src/utils/formatters.ts
    - frontend/src/styles/globals.css
    - frontend/src/styles/components.css
  modified:
    - frontend/src/App.tsx (T02, T11 integration)
    - frontend/src/hooks/useChat.ts (T11: onLlmError callback)
    - frontend/src/components/chat/ChatPanel.tsx (T11: toast wiring)

key-decisions:
  - "ToastContext renders ToastContainer internally (via ToastProvider), not explicitly in App.tsx — cleaner encapsulation"
  - "hasReadyDocument flows via callback: DocumentPanel.onHasReadyDocumentChange → AppLayout state → ChatPanel prop"
  - "onNetworkError callback propagated through AppLayout → DocumentPanel/ChatPanel → useDocuments/useChat hooks"
  - "LLM errors fire both an error bubble in MessageThread AND a toast via useToastContext (wired in T11)"
  - "SSE progress tracking with polling fallback for document upload progress"
  - "Error sentinel prefix __ERROR__ distinguishes error bubbles from normal messages in thread"
  - "useChat accepts _hasReadyDocument (unused) — guard is enforced in ChatInput, not hook"

patterns-established:
  - "Custom hook + callback pattern: hooks accept onNetworkError/onLlmError callbacks rather than calling context directly"
  - "Optimistic UI: add document/message to state immediately, update on SSE/API response"
  - "Terminal status check: READY/FAILED close SSE streams and polling intervals"

# Metrics
duration: 180min
completed: 2026-07-17
---

# Phase 2: Core MVP UI Summary

**React 18 + TypeScript frontend fully wired to Phase 1 backend: document upload with SSE progress, streaming RAG chat with markdown + citations, toast notifications, and network error banner**

## Performance

- **Duration:** ~180 min (across multiple sessions)
- **Started:** 2026-07-17T15:00:00Z
- **Completed:** 2026-07-17T20:10:00Z
- **Tasks:** 11 (T01–T11)
- **Files modified/created:** 34 source files

## Accomplishments

- Complete React 18 frontend scaffold with Vite + TypeScript, CSS design tokens, and `@/` path aliases
- API client layer (`apiFetch`) with session injection, error normalisation, and network failure detection
- Document library with drag-and-drop upload zone, SSE progress tracking (polling fallback), status badges, and delete confirmation
- Streaming chat interface: optimistic user messages, typing indicator, token-by-token SSE streaming, ReactMarkdown rendering with `remark-gfm`
- Citation section: collapsible "Sources (N)" with CitationCard per retrieved chunk (show more/less)
- Global feedback layer: toast queue (auto-dismiss + persist), ToastContext, NetworkBanner with Retry
- Full E2E integration: session → document upload → poll READY → send query → stream tokens → citations visible
- LLM errors shown as error bubble in thread AND auto-dismiss toast in top-right corner

## Task Commits

Each task was committed atomically:

1. **T01: Project Scaffold & API Client** - `bdc4b21` (feat)
2. **T02: Session Hook & Initialisation** - `1aa9d99` (feat)
3. **T03: Application Layout** - `f5b027d` (feat)
4. **T04: Document API Module & useDocuments Hook** - `d0b448d` (feat)
5. **T05: Upload Zone Component** - `30c06e6` (feat)
6. **T06: Document Panel Component** - `5a7c1c8` (feat)
7. **T07: Chat API Module & useChat Hook** - `b9c0950` (docs — pre-scaffolded)
8. **T08: Chat Interface Components** - `5b49f8e` (feat)
9. **T09: Citation Components** - `e074c89` (feat)
10. **T10: Feedback Components** - `7783180` (feat)
11. **T11: Integration & Wiring** - `afb598a` (feat)

## Files Created/Modified

### API Layer
- `frontend/src/api/client.ts` — `apiFetch()` with NETWORK_ERROR normalisation
- `frontend/src/api/sessions.ts` — `createSession()`, `getSession()`
- `frontend/src/api/documents.ts` — `listDocuments()`, `uploadDocument()`, `getDocumentStatus()`, `deleteDocument()`, `openUploadStream()`
- `frontend/src/api/chat.ts` — `sendQuery()`, `openChatStream()`, `getHistory()`, `clearHistory()`

### Hooks
- `frontend/src/hooks/useSession.ts` — session init with sessionStorage persistence
- `frontend/src/hooks/useDocuments.ts` — document list, upload with SSE/polling, delete
- `frontend/src/hooks/useChat.ts` — chat history, sendMessage with SSE streaming, clearMessages
- `frontend/src/hooks/useToast.ts` — toast queue with auto-dismiss timers
- `frontend/src/hooks/useFocusTrap.ts` — accessibility focus trap for modals

### Context
- `frontend/src/context/ToastContext.tsx` — ToastProvider + useToastContext

### Root Components
- `frontend/src/App.tsx` — session init, error/loading states, ToastProvider, NetworkBanner
- `frontend/src/components/layout/AppLayout.tsx` — two-column shell with hasReadyDocument propagation

### Document Components
- `frontend/src/components/documents/DocumentPanel.tsx`
- `frontend/src/components/documents/DocumentCard.tsx`
- `frontend/src/components/documents/DeleteConfirmDialog.tsx`
- `frontend/src/components/upload/UploadZone.tsx`
- `frontend/src/components/upload/FileProgressBar.tsx`

### Chat Components
- `frontend/src/components/chat/ChatPanel.tsx` — wires useChat + toast for LLM errors
- `frontend/src/components/chat/MessageThread.tsx`
- `frontend/src/components/chat/MessageBubble.tsx`
- `frontend/src/components/chat/TypingIndicator.tsx`
- `frontend/src/components/chat/ChatInput.tsx`
- `frontend/src/components/chat/ClearChatDialog.tsx`

### Citation Components
- `frontend/src/components/citations/CitationSection.tsx`
- `frontend/src/components/citations/CitationCard.tsx`

### Feedback Components
- `frontend/src/components/feedback/Toast.tsx`
- `frontend/src/components/feedback/ToastContainer.tsx`
- `frontend/src/components/feedback/NetworkBanner.tsx`

### Foundation
- `frontend/src/types/api.ts` — all TypeScript interfaces
- `frontend/src/utils/constants.ts` — file size limits, extensions, polling interval
- `frontend/src/utils/formatters.ts` — formatRelativeTime, formatFileSize, truncateFilename
- `frontend/src/styles/globals.css` — CSS design tokens + reset
- `frontend/src/styles/components.css` — shared component utility classes

## Decisions Made

- **ToastContext encapsulates ToastContainer**: `ToastProvider` renders `<ToastContainer>` internally, keeping App.tsx clean. Functionally identical to spec's explicit placement.
- **Callback-based error propagation**: `onNetworkError` and `onLlmError` flow as callbacks through the component tree rather than calling context directly inside hooks — keeps hooks decoupled from context.
- **`hasReadyDocument` via callback**: `DocumentPanel` computes `hasReadyDocument` from its document state and notifies `AppLayout` via `onHasReadyDocumentChange`. AppLayout holds the value as state and passes it to `ChatPanel`.
- **`_hasReadyDocument` in useChat**: Hook accepts but doesn't use the parameter (guard is in `ChatInput`). Underscore prefix makes intent explicit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] LLM error → toast wiring**
- **Found during:** T11 (Integration & Wiring audit)
- **Issue:** Plan spec requires "LLM error → error bubble in chat thread + toast in top-right". Error bubbles existed but no toast was fired on SSE error or sendQuery failure.
- **Fix:** Added `onLlmError?: (message: string) => void` to `useChat` signature; called on SSE error events and sendQuery failures. `ChatPanel` consumes `useToastContext().addToast()` and passes `handleLlmError` to `useChat`.
- **Files modified:** `frontend/src/hooks/useChat.ts`, `frontend/src/components/chat/ChatPanel.tsx`
- **Verification:** Build passes 0 errors; wiring confirmed via grep traces
- **Committed in:** `afb598a` (T11 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Critical for spec compliance. No scope creep — this was explicitly required in acceptance criteria.

## Issues Encountered

None - all tasks executed with clean builds at each step.

## Known Stubs

None found. All handlers implement real behavior:
- `apiFetch()` makes real HTTP calls with error normalisation
- `useDocuments` makes real SSE and REST calls
- `useChat` streams real SSE tokens
- Delete, upload, clear all call real API endpoints

## User Setup Required

None - no external service configuration required. Backend runs on `localhost:8000`, frontend proxies via Vite config.

## Next Phase Readiness

Phase 2 complete. The full MVP frontend is operational end-to-end:
- Upload PDF → READY in Document Panel → Stream question/answer → See citations
- All error states handled: inline upload errors, LLM error bubble + toast, network banner
- `npm run build` produces 0 TypeScript or Vite errors

Phase 3 (responsive polish) can proceed immediately. Phase 3 should address:
- Mobile/tablet responsive breakpoints (currently desktop-first only)
- Accessibility audit (ARIA, keyboard nav, focus trapping in dialogs)
- Performance: virtualization for large document/message lists

---
*Phase: 02-core-mvp-ui*
*Completed: 2026-07-17*

## Self-Check: PASSED

- [x] Key files exist: `frontend/src/App.tsx`, `frontend/src/context/ToastContext.tsx`, `frontend/src/hooks/useChat.ts`, `frontend/src/components/chat/ChatPanel.tsx`
- [x] Commit `afb598a` exists (T11 integration wiring)
- [x] Build: `npm run build` → exit 0 (TypeScript + Vite, 314 modules transformed)
- [x] No blocking stubs found
