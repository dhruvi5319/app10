---
phase: 02-core-mvp-ui
verified: 2026-07-17T17:44:00Z
status: gaps_found
score: 5/7 must-haves verified
re_verification: false
gaps:
  - truth: "User drags PDF, watches progress bar advance UPLOADING→PARSING→CHUNKING→EMBEDDING→INDEXING→READY, document appears with green Ready badge"
    status: partial
    reason: "FileProgressBar has all 7 stage labels implemented but UploadZone only ever feeds it UPLOADING then READY (skipping the 5 intermediate stages). uploadFile() resolves after the HTTP POST completes — before backend processing — so UploadZone marks the in-flight entry as READY while the document is still PARSING/CHUNKING/EMBEDDING/INDEXING. Intermediate stages are visible only in DocumentCard's Processing badge, not in the FileProgressBar stage labels. Additionally, FileProgressBar shows 'Ready ✓' while the document is still processing, which is misleading."
    artifacts:
      - path: "frontend/src/components/upload/UploadZone.tsx"
        issue: "inFlightFiles status transitions only UPLOADING→READY (line 85, 94); never set to PARSING/CHUNKING/EMBEDDING/INDEXING because onUpload resolves after POST, not after SSE terminal status"
      - path: "frontend/src/hooks/useDocuments.ts"
        issue: "uploadFile() (line 184-226) resolves after startSSETracking(docId) is called (line 222), before SSE delivers any stage updates. Stage updates go to documents[] state (DocumentCard), not back to UploadZone's inFlightFiles"
    missing:
      - "Wire SSE stage updates from useDocuments back to UploadZone's inFlightFiles so FileProgressBar shows PARSING/CHUNKING/EMBEDDING/INDEXING labels as they arrive"
      - "OR: keep uploadFile() awaiting terminal status before resolving, so UploadZone stays in-flight through all stages"
      - "OR: make DocumentCard show a full progress bar with stage labels instead of a generic Processing badge"

  - truth: "Delete document → card disappears with fade-out animation"
    status: partial
    reason: "DocumentCard has `transition: 'opacity 0.3s ease'` set (line 114) but deletion removes the card from state synchronously. There is no opacity-to-0 step before removal — no AnimatePresence, no setTimeout with opacity=0 before filter, no CSS exit animation. The card disappears instantly from DOM. The transition property is present but is never triggered by the delete flow."
    artifacts:
      - path: "frontend/src/components/documents/DocumentCard.tsx"
        issue: "Has `transition: 'opacity 0.3s ease'` (line 114) but the transition is only useful for hover/active state changes, not DOM removal. Actual deletion removes the card instantly."
      - path: "frontend/src/hooks/useDocuments.ts"
        issue: "deleteDocument() (line 229-263) calls setDocuments(prev => prev.filter(...)) synchronously on success — no delay or opacity-fade step before removal"
    missing:
      - "Add a fade-out step before removal: set a 'deleting' flag on the card → CSS opacity:0 → setTimeout 300ms → then remove from state"
      - "OR: use a library like react-transition-group or framer-motion AnimatePresence to animate exit"
human_verification:
  - test: "Upload journey end-to-end stage labels"
    expected: "FileProgressBar shows 'Parsing…', 'Chunking…', 'Embedding (N%)…', 'Indexing…' labels sequentially as backend processes the document"
    why_human: "Cannot observe SSE stage delivery without a running backend and real browser"
  - test: "Q&A with streaming token-by-token delivery"
    expected: "User sees typing indicator then text appearing character by character with streaming cursor ▍"
    why_human: "SSE streaming behavior requires live browser session with running backend"
  - test: "Citation section expand/collapse"
    expected: "Clicking 'Sources (N)' reveals CitationCards; clicking again collapses"
    why_human: "Interactive UI behavior requires real browser"
  - test: "Network failure banner persistence and Retry"
    expected: "Killing the backend shows persistent red banner; Retry button reloads page"
    why_human: "Requires simulating network failure in a live environment"
---

# Phase 2: Core MVP UI Verification Report

**Phase Goal:** A fully built React frontend wired end-to-end to the Phase 1 backend. Every P0 and P1 feature complete and usable by a real user in a browser — upload documents, ask questions, read cited answers, manage document library, scroll session history — no developer tooling required.
**Verified:** 2026-07-17T17:44:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Gate Evidence (mandatory input)

| Gate | Result |
|------|--------|
| `gate_status` | **passed** |
| `boot_smoke` | skipped (no `.pivota/start-dev.sh`) |
| Build (`npm run build`) | ✓ pass — 314 modules, 341KB bundle, 0 errors |
| Tests (`pytest -x -q`) | ✓ pass — 37 passed |
| Code review iteration 2 | ✓ clean — 0 BLOCKERs, 0 WARNINGs |
| B1 (apiFetch FastAPI envelope) | ✓ resolved (b76deb2) |
| W1 (duplicate skip-link) | ✓ resolved (d1892e2) |
| W2 (dialog aria-hidden) | ✓ resolved (e90e797) |
| W3 (double upload error) | ✓ resolved (b3d3099) |

Gates are green. All four code review findings confirmed fixed in iteration 2. Build and tests verified fresh (re-run in this verification session).

---

## Spot-Check Results

| Check | Command | Result |
|-------|---------|--------|
| Build passes | `npm run build` | ✓ 314 modules, 341KB JS, 8.65KB CSS, 1.27s |
| TypeScript clean | `tsc --noEmit` | ✓ zero errors |
| Backend tests | `pytest -x -q` | ✓ 37 passed, 1 warning |
| Dist bundle exists | `ls dist/assets/` | ✓ JS + CSS bundles present |
| React 18 | `package.json` | ✓ react@^18.3.1, react-dom@^18.3.1 |
| Vite + TypeScript | `package.json` | ✓ vite@^5.2.11, typescript@^5.4.5 |

---

## Observable Truths Verification

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Upload journey with progress bar through all 6 stages | ⚠️ PARTIAL | FileProgressBar implements all stage labels; UploadZone only feeds UPLOADING→READY. Intermediate stages shown only as DocumentCard "Processing" badge, not as labeled progress bar. |
| 2 | Q&A with streaming (typing indicator → token-by-token) | ✓ VERIFIED | `useChat.ts`: SSE token events append to `streamingContent` (line 153); `TypingIndicator` shown when `queryInFlight && streamingContent === ''` (MessageThread:136); `streamingContent` passed to `MessageBubble` with `▍` cursor (line 100) |
| 3 | Citations: non-refusal → collapsed "Sources (N)" + CitationCard | ✓ VERIFIED | `CitationSection.tsx`: renders button "Sources ({count})" collapsed by default (line 54-76); `CitationCard` shows filename, page, excerpt; only renders when `is_refusal !== true && retrieved_chunks?.length > 0` |
| 4 | Grounding in UI: refusal → no citation section | ✓ VERIFIED | `CitationSection.tsx` line 39: `if (is_refusal === true \|\| !retrieved_chunks \|\| retrieved_chunks.length === 0) return null;` — refusal messages receive no citation section |
| 5 | Delete document → card disappears with fade-out | ⚠️ PARTIAL | Deletion functional (DocumentCard removed from state, API called). `transition: 'opacity 0.3s ease'` present but never triggered for exit — card disappears instantly, no animated fade-out. |
| 6 | Chat history scrollable; Clear Chat empties thread, not docs | ✓ VERIFIED | `useChat.clearMessages()` calls `clearHistory()` API + `setMessages([])` without touching documents state. `MessageThread` is scrollable with auto-scroll. `ChatPanel` shows "Clear Chat" button only when `messages.length > 0`. |
| 7 | Error handling: unsupported file, too large, LLM unavailable, network failure | ✓ VERIFIED | (a) Invalid ext → `addError()` in UploadZone (no API call, line 77); (b) Too large → same `addError()` path, no API call; (c) LLM error → `onLlmError()` → `addToast()` + `ERROR_PREFIX` bubble in thread; (d) NETWORK_ERROR → `onNetworkError()` → NetworkBanner with Retry |

**Score: 5/7 truths verified** (2 partial gaps)

---

## Required Artifacts

| Artifact | Status | Notes |
|----------|--------|-------|
| `frontend/src/App.tsx` | ✓ VERIFIED | ToastProvider wraps AppInner; NetworkBanner wired to NETWORK_ERROR; skip-link present |
| `frontend/src/hooks/useSession.ts` | ✓ VERIFIED | sessionStorage GET-reuse / POST-fallback (lines 21-46); 404 → remove + create new |
| `frontend/src/hooks/useDocuments.ts` | ✓ VERIFIED | SSE upload tracking + polling fallback; cleanup on unmount; NETWORK_ERROR propagation |
| `frontend/src/hooks/useChat.ts` | ✓ VERIFIED | SSE token streaming; optimistic messages; error bubble + toast on LLM failure |
| `frontend/src/hooks/useToast.ts` | ✓ VERIFIED | Auto-dismiss (5s) + persist flag; timer cleanup in dismissToast |
| `frontend/src/api/client.ts` | ✓ VERIFIED | B1 fix confirmed: `body?.detail && typeof body.detail === 'object' ? body.detail : body` (line 59); NETWORK_ERROR on TypeError |
| `frontend/src/components/upload/UploadZone.tsx` | ⚠️ PARTIAL | Drag/drop/click works; client-side validation works; FileProgressBar shown; but only UPLOADING→READY stages fed to FileProgressBar |
| `frontend/src/components/upload/FileProgressBar.tsx` | ✓ VERIFIED | All 7 stage labels implemented (UPLOADING, PARSING, CHUNKING, EMBEDDING, INDEXING, READY, FAILED); EMBEDDING shows live progress_pct; indeterminate animation for other in-progress stages; Retry button on FAILED |
| `frontend/src/components/documents/DocumentPanel.tsx` | ✓ VERIFIED | Lists documents from useDocuments; hasReadyDocument notification via useEffect; UploadZone wired at bottom |
| `frontend/src/components/documents/DocumentCard.tsx` | ⚠️ PARTIAL | Status badges (green Ready, yellow Processing+spinner, red Failed) correct; delete dialog wired; transition CSS present; but no actual fade-out exit animation |
| `frontend/src/components/chat/ChatPanel.tsx` | ✓ VERIFIED | useChat wired with onNetworkError + handleLlmError; MessageThread + ChatInput rendered; Clear Chat dialog |
| `frontend/src/components/chat/MessageBubble.tsx` | ✓ VERIFIED | User/assistant/error bubble differentiation; streaming cursor ▍; CitationSection for non-error non-streaming assistant messages; onRetry with pre-bound priorUserQuery |
| `frontend/src/components/chat/ChatInput.tsx` | ✓ VERIFIED | `canSend = !isEmpty && !disabled && hasReadyDocument` (line 39); send button disabled; guard message shown when no ready doc |
| `frontend/src/components/citations/CitationSection.tsx` | ✓ VERIFIED | Collapsed by default; toggle with chevron; count shown; renders CitationCards when expanded; hidden for refusals |
| `frontend/src/components/citations/CitationCard.tsx` | ✓ VERIFIED | filename, page (null→'N/A'), chunk_index+1, excerpt; 800-char truncation with Show more/less; null excerpt guard |
| `frontend/src/components/feedback/NetworkBanner.tsx` | ✓ VERIFIED | Sticky top, role="alert", aria-live="assertive"; Retry button calls onRetry |
| `frontend/src/components/feedback/ToastContainer.tsx` | ✓ VERIFIED | Fixed position, zIndex 9999; renders Toast components; hidden when empty |
| `frontend/src/context/ToastContext.tsx` | ✓ VERIFIED | ToastProvider wraps children + renders ToastContainer; useToastContext throws if used outside provider |

---

## Key Link Verification

| From | To | Via | Status | Notes |
|------|----|-----|--------|-------|
| `App.tsx` | `ToastProvider` | wraps entire AppInner | ✓ WIRED | Line 110-113 |
| `App.tsx` | `NetworkBanner` | `visible={networkError}` | ✓ WIRED | Line 102 |
| `App.tsx` | `AppLayout` | `onNetworkError={handleNetworkError}` | ✓ WIRED | Line 103 |
| `AppLayout` | `DocumentPanel` | `onHasReadyDocumentChange` | ✓ WIRED | Line 184 |
| `AppLayout` | `ChatPanel` | `hasReadyDocument={hasReadyDocument}` | ✓ WIRED | Line 205 |
| `DocumentPanel` | `useDocuments` | `uploadFile`, `deleteDocument`, `documents` | ✓ WIRED | Line 65-66 |
| `DocumentPanel` → `AppLayout` | `hasReadyDocument` | `onHasReadyDocumentChange` useEffect | ✓ WIRED | Lines 76-81 |
| `ChatPanel` | `useChat` | `onNetworkError`, `handleLlmError` | ✓ WIRED | Line 29-30 |
| `ChatPanel` | `useToastContext` | `addToast` in `handleLlmError` | ✓ WIRED | Lines 20-27 |
| `ChatInput` | `hasReadyDocument` | gates `canSend` + `disabled` | ✓ WIRED | Lines 39, 111, 140 |
| `useDocuments.uploadFile` | SSE stage updates | `documents[]` state (NOT UploadZone inFlightFiles) | ⚠️ PARTIAL | Only reaches DocumentCard, not FileProgressBar |
| `useChat.sendMessage` | SSE token stream | `streamingContent` state | ✓ WIRED | Lines 128-211 |
| `useSession` | `sessionStorage` | GET-reuse / POST-fallback | ✓ WIRED | Lines 21-46 |
| `apiFetch` | FastAPI error envelope | `body.detail` unwrap (B1 fix) | ✓ WIRED | Line 59 |
| `useChat` (NETWORK_ERROR) | NetworkBanner | `onNetworkError?.()` → `setNetworkError(true)` | ✓ WIRED | Wave 6 fix confirmed |
| `useDocuments` (NETWORK_ERROR) | NetworkBanner | `onNetworkError?.()` propagated | ✓ WIRED | Lines 72-74, 209-211, 234-236 |

---

## Anti-Patterns Scan

No blocking anti-patterns found. All `return null` / `return <>` / `=> {}` patterns are legitimate:
- `return null` in CitationSection (correct: refusal guard), NetworkBanner (correct: hidden state), ToastContainer (correct: empty state), ClearChatDialog/DeleteConfirmDialog (correct: closed state), DocumentCard.StatusBadge (correct: unrecognized status), App.tsx (correct: awaiting session)
- `onChange={() => {}}` in ChatInput is documented ("Controlled via onInput") — `onInput` is the actual handler
- `sendMessage(query).catch(() => {})` in ChatPanel is intentional — errors surface as error bubbles

All grep matches for "placeholder" are code-level variable names (`placeholderIdRef`, `createAssistantPlaceholder`) not stub implementations.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

---

## Architecture Requirements Verification

| Requirement | Status | Evidence |
|-------------|--------|---------|
| Vite + React 18 + TypeScript at `frontend/` | ✓ | react@^18.3.1, vite@^5.2.11, ts@^5.4.5 in package.json |
| Session management via sessionStorage + GET-reuse/POST-fallback | ✓ | useSession.ts lines 21-46 |
| SSE streaming for upload progress | ✓ | useDocuments.startSSETracking; polling fallback |
| SSE streaming for chat tokens | ✓ | useChat.sendMessage opens EventSource for tokens |
| `hasReadyDocument` gates send button | ✓ | ChatInput `canSend` line 39; textarea `disabled` line 111 |
| ToastContext provider wraps app | ✓ | App.tsx lines 109-113 |
| NetworkBanner wired to NETWORK_ERROR from ApiError | ✓ | Wave 6 fix; confirmed in useChat:103-104, useDocuments:72-73, 209-210, 234-235 |

---

## Human Verification Required

### 1. Upload Stage Labels in FileProgressBar
**Test:** Upload a document and observe whether the FileProgressBar (the animated bar inside UploadZone) shows the text labels "Parsing…", "Chunking…", "Embedding (N%)…", "Indexing…" during processing.
**Expected:** Labels advance one-by-one as backend processes the document.
**Why human:** Static analysis confirms UploadZone only passes UPLOADING→READY status to FileProgressBar; runtime behavior of the live SSE→UI wiring needs browser observation.

### 2. Delete fade-out animation
**Test:** Click delete on a DocumentCard, confirm in the dialog, and observe whether the card fades out smoothly or disappears instantly.
**Expected:** Card fades from opacity 1 to 0 over ~300ms before being removed from the list.
**Why human:** Cannot simulate DOM transition animations without a browser runtime.

### 3. Q&A streaming token-by-token
**Test:** Type a question about an uploaded PDF and press Enter; observe the typing indicator and subsequent streaming.
**Expected:** Three-dot typing indicator appears, then response text builds one token at a time with the `▍` cursor at the end.
**Why human:** Requires live SSE delivery from running backend.

### 4. Network failure → persistent banner + Retry
**Test:** Stop the backend, then perform any action (send message, upload file). Observe the UI.
**Expected:** Red "Connection lost" banner appears at top, persists; clicking Retry reloads the page.
**Why human:** Requires simulating real network failure.

---

## Gaps Summary

Two gaps prevent full goal achievement for success criteria #1 and #5:

**Gap 1 — FileProgressBar stage labels not wired (Success Criterion #1)**

The phase's core upload UX promise — "watches progress bar advance through UPLOADING → PARSING → CHUNKING → EMBEDDING → INDEXING → READY" — is not delivered. `FileProgressBar` has all stage labels implemented and ready, but `UploadZone.tsx` only ever feeds it two status values: `UPLOADING` (when file upload POST begins) and `READY` (immediately after the POST returns, before backend actually processes the document). This also creates a misleading moment where FileProgressBar shows "Ready ✓" while the document is still being parsed/chunked/embedded.

The SSE stage updates from the backend (PARSING, CHUNKING, EMBEDDING, INDEXING) correctly update `documents[]` state in `useDocuments`, which DocumentCard displays as a generic "Processing" badge — but that is a badge, not the labeled progress bar the spec requires.

**Root cause:** `uploadFile()` in `useDocuments` resolves/returns after starting SSE tracking (`startSSETracking`), but `UploadZone.processFiles()` transitions `inFlightFiles` to READY when `await onUpload(file)` resolves (line 94). There is no mechanism to relay subsequent SSE stage updates from `useDocuments` back into `UploadZone`'s `inFlightFiles`.

**Gap 2 — Delete card has no exit fade animation (Success Criterion #5)**

`deleteDocument()` removes the card from `documents[]` state synchronously via `setDocuments(prev => prev.filter(...))`. `DocumentCard` has `transition: 'opacity 0.3s ease'` in its inline style, but this CSS transition is only active for CSS property changes (e.g., hover), not DOM removal. No opacity-to-0 step is applied before removal, so the card vanishes instantly.

**Note:** Both gaps are UX/animation gaps, not functional gaps. The upload and delete operations themselves work correctly end-to-end; the missing pieces are intermediate visual feedback that the spec explicitly required.

---

## Summary

The Phase 2 React frontend is functionally complete and correctly wired to the backend. All core behaviors work: session management, document upload, chat with streaming, citations with refusal enforcement, error handling, and Clear Chat. The code review (iteration 2) found zero remaining blockers or warnings. Build and tests pass cleanly.

Two UX gaps remain against the explicit success criteria: the FileProgressBar never shows intermediate processing stage labels (PARSING/CHUNKING/EMBEDDING/INDEXING), and the delete card does not fade out before removal. These require targeted fixes to the `UploadZone`↔`useDocuments` stage-update wiring and the deletion animation flow.

---

_Verified: 2026-07-17T17:44:00Z_
_Verifier: Claude (pivota_spec-verifier)_
