---
phase: 02-core-mvp-ui
verified: 2026-07-17T21:40:02Z
status: gaps_found
score: 5/7 criteria verified
gaps:
  - truth: "User can watch the progress bar advance through all ingestion stages (UPLOADING→PARSING→CHUNKING→EMBEDDING→INDEXING→READY)"
    status: partial
    reason: >
      FileProgressBar has stage labels defined for all 7 statuses but UploadZone's internal
      InFlightFile state only ever transitions UPLOADING→READY (or FAILED). The onUpload()
      callback in useDocuments resolves immediately after the HTTP POST completes and
      startSSETracking() is called fire-and-forget, so UploadZone marks the bar READY before
      any ingestion SSE events arrive. DocumentCard in the panel shows a generic "Processing"
      badge for all intermediate stages but names no individual stage. No UI surface
      displays PARSING/CHUNKING/EMBEDDING/INDEXING as named progress steps.
    artifacts:
      - path: "frontend/src/components/upload/UploadZone.tsx"
        issue: "processFiles() sets InFlightFile status to READY immediately after onUpload() resolves (line 94); never sets PARSING/CHUNKING/EMBEDDING/INDEXING"
      - path: "frontend/src/components/upload/FileProgressBar.tsx"
        issue: "Stage labels for PARSING/CHUNKING/EMBEDDING/INDEXING are defined but unreachable from UploadZone usage (DEAD CODE in this context)"
      - path: "frontend/src/components/documents/DocumentCard.tsx"
        issue: "StatusBadge collapses all PROCESSING_STATUSES into a single generic 'Processing' label — individual stage names are not surfaced"
    missing:
      - "Either: (a) pass onStatusUpdate callback from DocumentPanel into UploadZone so SSE status updates drive InFlightFile.status, or (b) replace the InFlightFile progress bar with a view driven by the Document state from useDocuments, showing named stages as they arrive via SSE"

  - truth: "All error states surface human-readable messages with recovery paths — no blank screens, no silent failures; the NetworkBanner triggers on network loss"
    status: partial
    reason: >
      Inline error handling is comprehensive (ApiError with NETWORK_ERROR code, error bubbles in
      chat, inline file errors in UploadZone). However two specific recovery paths are broken:
      (1) The NetworkBanner component is rendered but networkError state is permanently false —
      setNetworkError is voided with a comment ("used via closure passed to children if needed")
      and no hook, event listener, or child component ever calls it. The banner can never appear.
      (2) The "Try again" retry button on assistant error bubbles passes message.content (which
      equals "__ERROR__<error text>") as the query to sendMessage() — instead of the preceding
      user message's original query. This sends the error string to the API.
    artifacts:
      - path: "frontend/src/App.tsx"
        issue: "Line 84: `void setNetworkError;` — setter is intentionally suppressed; no offline event listener or child callback sets it; NetworkBanner is permanently invisible"
      - path: "frontend/src/components/chat/MessageBubble.tsx"
        issue: "Line 89: `onClick={() => onRetry(message.content)}` — message.content for error bubbles is '__ERROR__<error text>', not the user's original query; retry sends garbage to the API"
    missing:
      - "Wire setNetworkError: add a window 'offline'/'online' event listener in App.tsx (or a dedicated useNetworkStatus hook), or pass setNetworkError down to useChat/useDocuments hooks to trigger on ApiError(0, 'NETWORK_ERROR')"
      - "Fix retry in MessageBubble: the retry button should receive the original user query string, not message.content. Options: (a) pass the preceding user message's content as a prop, or (b) store the last query in useChat and expose it, or (c) pass originalQuery as a separate prop to MessageBubble for error bubbles"
---

# Phase 02 — Core MVP UI Verification Report

**Phase Goal:** A fully built React frontend wired end-to-end to the Phase 1 backend. Every P0 and P1 feature is complete and usable in a browser — upload documents, watch ingestion progress, ask questions, stream answers, read cited sources, manage the document library, and scroll session history.

**Verified:** 2026-07-17T21:40:02Z
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | User drags PDF onto upload zone, watches progress bar advance through all stages, sees document appear as READY in Document Panel | ⚠️ PARTIAL | Upload HTTP POST tracked (UPLOADING→READY in FileProgressBar) but intermediate ingestion stages (PARSING→CHUNKING→EMBEDDING→INDEXING) are never shown in any progress bar. DocumentCard shows only a generic "Processing" badge. |
| 2 | User types question, presses Enter, sees typing indicator, reads streaming assistant response | ✓ VERIFIED | ChatInput handles Enter key → sendMessage → sendQuery API → openChatStream SSE → streamingContent updates → TypingIndicator shown when queryInFlight && streamingContent === '' → ReactMarkdown renders with cursor `▍` |
| 3 | Every non-refusal response shows collapsed "Sources (N)"; clicking reveals CitationCards with filename and verbatim excerpt | ✓ VERIFIED | CitationSection renders when is_refusal !== true && retrieved_chunks.length > 0; click toggles expanded; CitationCard shows filename + excerpt via `pre-wrap` span |
| 4 | Unanswerable question shows clear refusal message, no citation section | ✓ VERIFIED | CitationSection returns null when is_refusal === true (line 39); message.content displayed via ReactMarkdown; no special styling differentiates refusals (minor UX gap, not blocking) |
| 5 | User deletes document, confirms dialog, sees it disappear; subsequent questions reflect updated doc set | ✓ VERIFIED | DeleteConfirmDialog → onConfirm → deleteDocument API → setDocuments filters doc out; activeStreams/polls cleaned up; hasReadyDocument recomputed; full wiring confirmed |
| 6 | User can scroll prior Q&A and click "Clear Chat" to reset without losing documents | ✓ VERIFIED | MessageThread is scrollable (overflowY: auto); ClearChatDialog → clearHistory API → setMessages([]); DocumentPanel state is independent |
| 7 | All error states surface human-readable messages with recovery paths — no blank screens, no silent failures | ⚠️ PARTIAL | Inline errors are comprehensive (ApiError classes, error bubbles, file validation messages, ErrorScreen). Two recovery paths broken: NetworkBanner permanently invisible (setNetworkError never called); retry button sends `__ERROR__<text>` string as query instead of original user question |

**Score: 5/7 criteria verified**

---

## Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `frontend/src/App.tsx` | ✓ EXISTS & WIRED | Session lifecycle, ToastProvider wrapper, NetworkBanner, AppLayout |
| `frontend/src/main.tsx` | ✓ EXISTS & WIRED | StrictMode, createRoot, CSS imports |
| `frontend/src/api/client.ts` | ✓ EXISTS & WIRED | apiFetch with ApiError (status 0 = NETWORK_ERROR), 204 handling |
| `frontend/src/api/sessions.ts` | ✓ EXISTS & WIRED | createSession + getSession; used by useSession |
| `frontend/src/api/documents.ts` | ✓ EXISTS & WIRED | listDocuments, uploadDocument, getDocumentStatus, deleteDocument, openUploadStream (SSE) |
| `frontend/src/api/chat.ts` | ✓ EXISTS & WIRED | sendQuery, openChatStream (SSE), getHistory, clearHistory |
| `frontend/src/hooks/useSession.ts` | ✓ EXISTS & WIRED | sessionStorage persistence, 404 fallback to new session |
| `frontend/src/hooks/useDocuments.ts` | ✓ EXISTS & WIRED | SSE tracking + polling fallback; optimistic adds/removes; cleanup on unmount |
| `frontend/src/hooks/useChat.ts` | ✓ EXISTS & WIRED | Optimistic UI, SSE token streaming, 'done'/'error' event handling; isErrorMessage/extractErrorText exported |
| `frontend/src/hooks/useToast.ts` | ✓ EXISTS | Implemented with auto-dismiss timers and persist flag |
| `frontend/src/hooks/useFocusTrap.ts` | ✓ EXISTS & WIRED | Used by DeleteConfirmDialog and ClearChatDialog |
| `frontend/src/context/ToastContext.tsx` | ✓ EXISTS | ToastProvider wraps app; useToastContext exported — but **not consumed by any component** (see Key Links) |
| `frontend/src/components/layout/AppLayout.tsx` | ✓ EXISTS & WIRED | Two-column shell; tablet expand/collapse; mobile FAB + drawer; hasReadyDocument state lifted |
| `frontend/src/components/upload/UploadZone.tsx` | ✓ EXISTS & WIRED | Drag/drop + click-to-browse; file validation; inline errors; PARTIAL progress tracking |
| `frontend/src/components/upload/FileProgressBar.tsx` | ✓ EXISTS | Stage labels defined for all 7 statuses; PARTIAL — intermediate stages never reached from UploadZone |
| `frontend/src/components/documents/DocumentPanel.tsx` | ✓ EXISTS & WIRED | Lists documents from useDocuments; notifies parent of hasReadyDocument; renders UploadZone |
| `frontend/src/components/documents/DocumentCard.tsx` | ✓ EXISTS & WIRED | StatusBadge (Ready/Processing/Failed); delete trigger; PROCESSING stages collapsed to generic label |
| `frontend/src/components/documents/DeleteConfirmDialog.tsx` | ✓ EXISTS & WIRED | Modal with focus trap, Escape key, loading state |
| `frontend/src/components/chat/ChatPanel.tsx` | ✓ EXISTS & WIRED | Orchestrates useChat; passes onRetry to MessageThread |
| `frontend/src/components/chat/MessageThread.tsx` | ✓ EXISTS & WIRED | Scroll-to-bottom on new messages; streaming placeholder detection; TypingIndicator |
| `frontend/src/components/chat/MessageBubble.tsx` | ✓ EXISTS & WIRED | User/assistant/error rendering; ReactMarkdown; CitationSection; retry button (BROKEN — see gaps) |
| `frontend/src/components/chat/TypingIndicator.tsx` | ✓ EXISTS & WIRED | Shown when queryInFlight && streamingContent === '' |
| `frontend/src/components/chat/ChatInput.tsx` | ✓ EXISTS & WIRED | Enter-to-send; Shift+Enter newline; guard message when no ready document; auto-grow textarea |
| `frontend/src/components/chat/ClearChatDialog.tsx` | ✓ EXISTS & WIRED | Modal with focus trap, Escape key, loading state |
| `frontend/src/components/citations/CitationSection.tsx` | ✓ EXISTS & WIRED | Suppresses for refusals and empty chunks; collapsible Sources(N) |
| `frontend/src/components/citations/CitationCard.tsx` | ✓ EXISTS & WIRED | Filename + page + excerpt (verbatim, pre-wrap); truncation with show-more |
| `frontend/src/components/feedback/Toast.tsx` | ✓ EXISTS & WIRED | info/success/error variants; ARIA roles |
| `frontend/src/components/feedback/ToastContainer.tsx` | ✓ EXISTS & WIRED | Fixed position, renders Toast list |
| `frontend/src/components/feedback/NetworkBanner.tsx` | ✓ EXISTS but ORPHANED | Rendered in App.tsx with `visible={networkError}`, but networkError is always false |
| `frontend/src/types/api.ts` | ✓ EXISTS & WIRED | All types match API contracts; SSEEvent union type complete |
| `frontend/src/utils/constants.ts` | ✓ EXISTS & WIRED | MAX_FILE_SIZE_MB=20, POLLING_INTERVAL_MS=1500, MAX_DOCUMENTS_PER_SESSION=10 |
| `frontend/src/utils/formatters.ts` | ✓ EXISTS & WIRED | formatRelativeTime, formatFileSize, truncateFilename |

---

## Key Link Verification

### 1. UploadZone → DocumentPanel → useDocuments (upload pipeline)

```
UploadZone.onUpload(file)
  → DocumentPanel.uploadFile (from useDocuments)
    → uploadDocument() HTTP POST
    → setDocuments([...prev, optimisticDoc])  ← UPLOADING status added
    → startSSETracking(docId)                 ← fire-and-forget
      → SSE events update Document.status    ← PARSING/CHUNKING/etc.
```

**Gap:** UploadZone's `InFlightFile` state is **disconnected** from Document state. After `onUpload()` resolves, UploadZone marks the bar `READY` without receiving SSE updates. The FileProgressBar stage labels for intermediate statuses are **dead code** in this integration path.

### 2. ChatInput → useChat → SSE stream (chat pipeline)

```
ChatInput.handleSend(query)
  → ChatPanel.sendMessage(query)
    → useChat.sendMessage(query)
      → setMessages([...userMsg, placeholder])   ← optimistic
      → sendQuery(sessionId, query) HTTP POST     ← returns message_id
      → openChatStream(message_id) SSE
        → 'token': setStreamingContent(prev + delta)
        → 'done':  replace placeholder with data.message (incl. retrieved_chunks)
        → 'error': replace placeholder with __ERROR__<text>
```

**Status: WIRED ✓** — full chain verified end-to-end.

### 3. MessageBubble → CitationSection → CitationCard (citations pipeline)

```
useChat 'done' event → data.message.retrieved_chunks → MessageBubble.message.retrieved_chunks
  → CitationSection(retrieved_chunks, is_refusal)
    → if is_refusal || chunks empty → return null
    → else → render Sources(N) toggle → CitationCard per chunk
      → filename + page_number + excerpt (verbatim)
```

**Status: WIRED ✓**

### 4. NetworkBanner trigger (BROKEN)

```
App.tsx:
  const [networkError, setNetworkError] = useState(false);  ← always false
  void setNetworkError;  ← intentionally suppressed
  <NetworkBanner visible={networkError} .../>  ← never visible
```

**No offline event listener. No hook calls setNetworkError. Banner is permanently hidden.**

### 5. Toast system usage

```
ToastProvider (App.tsx)
  → ToastContext.Provider value={addToast, dismissToast, toasts}
  → ToastContainer renders toasts
```

`useToastContext` is exported and usable, but **no component in the app calls `addToast`**. Upload errors, document errors, and chat errors all display inline (error bubbles, UploadZone error list) rather than toasts. The toast system exists but is not wired to any error event.

### 6. Retry button in MessageBubble (BROKEN)

```
MessageBubble (assistant error bubble):
  message.content = "__ERROR__Connection to server lost..."
  onClick={() => onRetry(message.content)}
    → ChatPanel.handleRetry("__ERROR__Connection to server lost...")
      → sendMessage("__ERROR__Connection to server lost...")  ← wrong payload
```

The retry should pass the **original user query** (the preceding user message's content), not the error string from the assistant placeholder.

### 7. hasReadyDocument propagation

```
useDocuments.documents.some(d => d.status === 'READY')
  → DocumentPanel.hasReadyDocument
    → onHasReadyDocumentChange(hasReady)
      → AppLayout.setHasReadyDocument(hasReady)
        → ChatPanel.hasReadyDocument prop
          → ChatInput: disables input when false, shows guard message
          → useChat: _hasReadyDocument param (accepted but not used internally — guard is at UI layer)
```

**Status: WIRED ✓** — chat input correctly disabled until a document is READY.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `App.tsx` | 84 | `void setNetworkError;` — deliberate no-op, state never mutated | ⚠️ Warning | NetworkBanner permanently invisible; network failure recovery path missing |
| `MessageBubble.tsx` | 89 | `onRetry(message.content)` on error bubble passes `__ERROR__<text>` as query | 🛑 Blocker | Retry sends garbage to API; recovery path for chat errors is broken |
| `UploadZone.tsx` | 91–94 | `onUpload()` resolves → InFlightFile immediately set to READY; no SSE stage updates forwarded | ⚠️ Warning | Progress bar skips PARSING/CHUNKING/EMBEDDING/INDEXING stages; Criterion 1 partially unmet |
| `FileProgressBar.tsx` | 12–20 | Stage labels for PARSING/CHUNKING/EMBEDDING/INDEXING unreachable from UploadZone | ℹ️ Info | Dead code; component is future-ready but not exercised |
| `DocumentCard.tsx` | 80–87 | `StatusBadge` collapses 5 distinct pipeline stages into one generic "Processing" label | ⚠️ Warning | No per-stage progress visibility in the document panel |

---

## Gaps Summary

**Gap 1 — Progress Bar Stage Visibility (Criterion 1, Warning)**

The `FileProgressBar` component has stage labels for all 7 `DocumentStatus` values, but `UploadZone` never feeds intermediate statuses to it. When `onUpload(file)` is awaited in `processFiles()`, the call returns after the HTTP POST completes and `startSSETracking()` is called (fire-and-forget). The SSE events that carry `PARSING`, `CHUNKING`, `EMBEDDING`, `INDEXING` statuses update the `Document` objects in `useDocuments` state — which drives `DocumentCard` badges — but are never forwarded to `UploadZone`'s `InFlightFile` state. The user sees `Uploading…` → `Ready ✓` with no intermediate steps. DocumentCard shows "Processing" (generic) during the pipeline.

**Fix options:**
- (a) Extend `onUpload` to accept an `onStatusUpdate` callback, pass it down from `DocumentPanel`, and have `useDocuments.startSSETracking` call it with each status update.
- (b) Remove `InFlightFile` from UploadZone entirely; let `DocumentPanel` render a `FileProgressBar` per document that is currently non-READY, driven by the `Document` state.

**Gap 2 — NetworkBanner Never Triggers (Criterion 7, Warning)**

`NetworkBanner` is rendered in `App.tsx` with `visible={networkError}` but `networkError` is permanently `false`. The comment `// used via closure passed to children if needed` documents the incomplete wiring. The `ApiError(0, 'NETWORK_ERROR', ...)` thrown by `apiFetch` is caught by individual hooks (useChat, useDocuments) and shown as inline errors, but nothing surfaces the network-level outage as a banner.

**Fix options:**
- Add `window.addEventListener('offline', ...)` / `window.addEventListener('online', ...)` in App.tsx (or a `useNetworkStatus` hook).
- Or pass a `onNetworkError` callback into `useChat` and `useDocuments` to call when `ApiError.statusCode === 0`.

**Gap 3 — Retry Button Sends Error String as Query (Criterion 7, Blocker)**

`MessageBubble.tsx` line 89 calls `onRetry(message.content)` where `message` is the assistant error bubble with `content = "__ERROR__<error text>"`. This string is passed to `sendMessage()` and sent to the API as the chat query. The fix requires the retry button to pass the **original user query**, not the error bubble content.

**Fix options:**
- In `useChat.sendMessage`, store `query` in a `lastQueryRef` and expose it; pass it to ChatPanel for retry.
- Or in `MessageThread`, find the user message immediately preceding each error bubble and pass its content as the `originalQuery` prop to `MessageBubble`.
- Or restructure `MessageBubble` props to accept `originalQuery?: string` when `isError` is true.

---

## Human Verification Required

### 1. Visual Progress During Ingestion

**Test:** Upload a multi-page PDF and watch the document panel while the backend processes it.
**Expected:** The DocumentCard should show status transitions as the backend pipeline progresses. With the current code, only "Processing" is shown (no stage names).
**Why human:** Requires a live backend + SSE stream to observe real-time badge transitions.

### 2. Streaming Response Display

**Test:** Ask a question about an uploaded document; observe the text appearing character-by-character.
**Expected:** Text streams into the bubble with the `▍` cursor; TypingIndicator shows before first token; cursor disappears on completion.
**Why human:** Requires live LLM connection; cannot simulate in static analysis.

### 3. Citation Section Expand/Collapse

**Test:** After receiving an answer with sources, click "Sources (N)".
**Expected:** CitationCards expand with filename, page number, and excerpt text.
**Why human:** Requires backend to return non-null `retrieved_chunks` in the `done` SSE event.

### 4. Refusal Display

**Test:** Ask a question about content not in any uploaded document.
**Expected:** Clear refusal message visible; no "Sources" section appears.
**Why human:** Depends on LLM behavior and backend refusal classification.

### 5. Mobile Drawer Behavior

**Test:** View on a mobile viewport; tap the FAB; verify document panel opens as a bottom drawer; swipe down to dismiss.
**Expected:** Smooth animation; swipe-to-dismiss with > 100px threshold; backdrop tap closes drawer.
**Why human:** CSS media queries, touch events, and animation cannot be verified from static analysis.

### 6. Toast System Wiring (Smoke Check)

**Test:** Attempt to upload an unsupported file type (e.g., `.exe`).
**Expected:** Inline error appears in UploadZone. Verify whether a toast also fires (the toast system is wired but no code calls `addToast` for this case).
**Why human:** Verifies the inline-only error handling is acceptable UX or confirms toasts should be added for key error paths.

---

## Build & Type Check Results

```
TypeScript: tsc --noEmit → Exit code 0 (no errors)
Build artifacts: frontend/dist/assets/ → index-*.js + index-*.css (build passes)
```

---

_Verified: 2026-07-17T21:40:02Z_
_Verifier: Claude (pivota_spec-verifier) — static code analysis_
