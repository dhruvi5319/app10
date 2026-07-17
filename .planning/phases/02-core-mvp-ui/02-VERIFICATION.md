---
phase: 02-core-mvp-ui
verified: 2026-07-17T21:30:00Z
status: human_needed
score: 7/7 must-haves verified
re_verification: true
  previous_status: gaps_found
  previous_score: 5/7
  gaps_closed:
    - "Truth #1: FileProgressBar SSE stage labels — onStageUpdate callback now wired from UploadZone.processFiles → useDocuments.uploadFile → startSSETracking/startPolling → back to UploadZone.inFlightFiles; READY authority transferred exclusively to SSE/polling callback"
    - "Truth #5: Delete fade-out — DocumentCard.handleDeleteConfirm now sets isDeleting=true (opacity:0) → awaits 300ms CSS transition → calls onDelete; trash button disabled during fade window"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Upload journey end-to-end stage labels"
    expected: "FileProgressBar shows 'Uploading…', 'Parsing…', 'Chunking…', 'Embedding (N%)…', 'Indexing…', then 'Ready ✓' labels sequentially as backend processes the document via SSE"
    why_human: "Cannot observe live SSE delivery from backend without a running server and real browser; the wiring is verified statically but the runtime label sequence requires observation"
  - test: "Q&A with streaming token-by-token delivery"
    expected: "User sees three-dot typing indicator then response text appears token by token with the ▍ cursor at the end; cursor disappears when stream ends"
    why_human: "SSE streaming behavior requires live browser session with running backend"
  - test: "Citation section expand/collapse"
    expected: "Clicking 'Sources (N)' reveals CitationCards with filename, page, excerpt; clicking again collapses; never shown for refusal responses"
    why_human: "Interactive UI toggle behavior requires real browser"
  - test: "Network failure banner persistence and Retry"
    expected: "Stopping the backend then performing any action (upload or send) causes a persistent red banner to appear; clicking Retry reloads the page"
    why_human: "Requires simulating real network failure in a live environment"
---

# Phase 2: Core MVP UI Verification Report

**Phase Goal:** A fully built React frontend wired end-to-end to the Phase 1 backend. Every P0 and P1 feature complete and usable by a real user in a browser — upload documents, ask questions, read cited answers, manage document library, scroll session history — no developer tooling required.
**Verified:** 2026-07-17T21:30:00Z
**Status:** human_needed (all automated checks pass; 4 items require live browser)
**Re-verification:** Yes — after gap closure (plans 02-09, 02-10 + code-review fixes)

---

## Re-verification Summary

| Item | Previous | Now | Change |
|------|----------|-----|--------|
| Truth #1: Upload stage labels | ⚠️ PARTIAL | ✓ VERIFIED | Gap closed |
| Truth #5: Delete fade-out | ⚠️ PARTIAL | ✓ VERIFIED | Gap closed |
| UAT gap: VITE_API_BASE_URL | ⚠️ PARTIAL | ✓ VERIFIED | Gap closed |
| Truths #2-4, #6-7 | ✓ VERIFIED | ✓ VERIFIED | No regression |
| Gate: build | ✓ pass | ✓ pass (re-run) | Stable |
| Gate: tests | ✓ pass (37) | ✓ pass (37, re-run) | Stable |
| Code review | clean (iter 2) | clean (iter 4) | Further improved |

---

## Gate Evidence (mandatory input)

All gate evidence from `02-GATE.md` and `02-REVIEW.md` is green. No unresolved failures.

| Gate | Result |
|------|--------|
| `gate_status` | **passed** |
| `boot_smoke` | skipped (no `.pivota/start-dev.sh`) — not blocking |
| Build — gap-closure wave | ✓ pass — 314 modules, 341KB, 0 errors |
| Build — final regression gate | ✓ pass — 314 modules, 341KB, 1.22s, 0 errors |
| Tests — gap-closure wave | ✓ pass — 37 passed, 1 warning |
| Tests — final regression gate | ✓ pass — 37 passed, 1 warning |
| Code review iteration 4 | ✓ clean — 0 BLOCKERs, 0 WARNINGs |
| B1 (processFiles premature READY) | ✓ resolved (commit 5d981a7) |
| B2 (trash button not disabled during fade) | ✓ resolved (commit e47221b) |
| W1 (polling path skipped READY signal) | ✓ resolved (commit 3dab703) |
| W3 (no try-catch restoring isDeleting) | ✓ resolved (commit e47221b) |
| W2 (VITE_API_BASE_URL doc concern) | ✓ emptied in `.env`/`.env.example` — proxy handles `/api` |
| Gap redrive: UAT gap | ✓ re-driven — `VITE_API_BASE_URL=` confirmed in both env files |
| Gap redrive: Truth #1 SSE stage labels | ✓ re-driven — `onStageUpdate` grep confirmed in both files |
| Gap redrive: Truth #5 delete fade | ✓ re-driven — `isDeleting` and `opacity: isDeleting ? 0 : 1` confirmed |

---

## Spot-Check Results (re-run in this verification session)

| Check | Command | Output |
|-------|---------|--------|
| Build | `npm run build` | ✓ 314 modules, 341.94KB JS, 8.65KB CSS, 1.42s, 0 errors |
| Backend tests | `pytest -x -q --tb=short` | ✓ 37 passed, 1 warning in 6.40s |
| VITE_API_BASE_URL empty | `grep '^VITE_API_BASE_URL' frontend/.env frontend/.env.example` | ✓ `VITE_API_BASE_URL=` (both files) |
| onStageUpdate in useDocuments | `grep 'onStageUpdate' useDocuments.ts` | ✓ 9 matches — callback threaded through uploadFile → startSSETracking → startPolling |
| onStageUpdate in UploadZone | `grep 'onStageUpdate' UploadZone.tsx` | ✓ prop declared; callback updates inFlightFiles at lines 93–96 |
| isDeleting in DocumentCard | `grep 'isDeleting' DocumentCard.tsx` | ✓ 7 matches — state, 300ms await, opacity, button disabled |
| opacity: isDeleting | `grep 'opacity: isDeleting'` | ✓ line 123: `opacity: isDeleting ? 0 : 1` |

---

## Observable Truths Verification

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User drags PDF, watches progress bar advance UPLOADING→PARSING→CHUNKING→EMBEDDING→INDEXING→READY | ✓ VERIFIED | `UploadZone.processFiles` passes `onStageUpdate` callback to `onUpload`; callback maps each stage to `setInFlightFiles` (lines 91–107); `useDocuments.uploadFile` threads callback through `startSSETracking` (line 231) and `startPolling` (line 122); both call `onStageUpdate?.(status, progress_pct)` on every event; READY authority is exclusively from SSE/polling (comment at lines 108–109 prevents premature READY); `FileProgressBar` receives live stage/progress_pct and renders all 7 labels |
| 2 | Q&A with streaming: typing indicator → token-by-token → ▍ cursor | ✓ VERIFIED | `useChat.ts`: SSE token events append to `streamingContent`; `TypingIndicator` shown when `queryInFlight && streamingContent === ''`; `streamingContent` passed to `MessageBubble` with `▍` cursor |
| 3 | Non-refusal answer → collapsed "Sources (N)" section with CitationCards | ✓ VERIFIED | `CitationSection.tsx`: renders collapsed by default; toggle button "Sources ({count})"; `CitationCard` shows filename, page, excerpt; only renders when `is_refusal !== true && retrieved_chunks?.length > 0` |
| 4 | Refusal answer → no citation section | ✓ VERIFIED | `CitationSection.tsx` line 39: `if (is_refusal === true \|\| !retrieved_chunks \|\| retrieved_chunks.length === 0) return null` |
| 5 | Delete document → card disappears with fade-out animation | ✓ VERIFIED | `DocumentCard.handleDeleteConfirm`: sets `isDeleting(true)` → `opacity: isDeleting ? 0 : 1` triggers CSS transition → `await setTimeout(300ms)` → calls `onDelete`; trash button `disabled={isProcessing \|\| isDeleting}` closes double-delete race; catch restores `isDeleting(false)` on error |
| 6 | Chat history scrollable; Clear Chat empties thread without touching documents | ✓ VERIFIED | `useChat.clearMessages()` calls `clearHistory()` API + `setMessages([])` without touching document state; `ChatPanel` shows Clear Chat only when `messages.length > 0`; `MessageThread` scrollable with auto-scroll |
| 7 | Error handling: unsupported file, too large, LLM unavailable, network failure | ✓ VERIFIED | (a) Invalid ext → `addError()` in UploadZone, no API call; (b) Too large → same path; (c) LLM error → `onLlmError()` → `addToast()` + ERROR_PREFIX bubble in thread; (d) NETWORK_ERROR → `onNetworkError()` → NetworkBanner with Retry |

**Score: 7/7 truths verified**

---

## Required Artifacts

| Artifact | Status | Notes |
|----------|--------|-------|
| `frontend/src/App.tsx` | ✓ VERIFIED | ToastProvider wraps AppInner; NetworkBanner wired; skip-link present |
| `frontend/src/hooks/useSession.ts` | ✓ VERIFIED | sessionStorage GET-reuse / POST-fallback; 404 → remove + create new |
| `frontend/src/hooks/useDocuments.ts` | ✓ VERIFIED | SSE upload tracking with `onStageUpdate` callback; polling fallback with symmetric callback; cleanup on unmount; NETWORK_ERROR propagation |
| `frontend/src/hooks/useChat.ts` | ✓ VERIFIED | SSE token streaming; optimistic messages; error bubble + toast on LLM failure |
| `frontend/src/hooks/useToast.ts` | ✓ VERIFIED | Auto-dismiss (5s) + persist flag; timer cleanup |
| `frontend/src/api/client.ts` | ✓ VERIFIED | FastAPI envelope unwrap (`body.detail`); NETWORK_ERROR on TypeError |
| `frontend/src/components/upload/UploadZone.tsx` | ✓ VERIFIED | `onUpload` prop accepts `onStageUpdate` callback; callback updates `inFlightFiles` for every stage including PARSING/CHUNKING/EMBEDDING/INDEXING; READY exclusively from callback; no premature state mutation in success path |
| `frontend/src/components/upload/FileProgressBar.tsx` | ✓ VERIFIED | All 7 stage labels; EMBEDDING shows `progress_pct`; indeterminate animation for other in-progress; Retry on FAILED |
| `frontend/src/components/documents/DocumentPanel.tsx` | ✓ VERIFIED | `uploadFile` from `useDocuments` passed directly to `UploadZone` as `onUpload` — the callback signature is preserved end-to-end |
| `frontend/src/components/documents/DocumentCard.tsx` | ✓ VERIFIED | `isDeleting` state; 300ms await before `onDelete`; `opacity: isDeleting ? 0 : 1` drives CSS transition; trash button disabled during fade; catch restores on error |
| `frontend/src/components/chat/ChatPanel.tsx` | ✓ VERIFIED | `useChat` wired with `onNetworkError` + `handleLlmError`; MessageThread + ChatInput rendered; Clear Chat dialog |
| `frontend/src/components/chat/MessageBubble.tsx` | ✓ VERIFIED | User/assistant/error differentiation; streaming cursor ▍; CitationSection for non-error non-streaming assistant messages |
| `frontend/src/components/chat/ChatInput.tsx` | ✓ VERIFIED | `canSend = !isEmpty && !disabled && hasReadyDocument`; guard message when no ready doc |
| `frontend/src/components/citations/CitationSection.tsx` | ✓ VERIFIED | Collapsed by default; toggle; count shown; CitationCards when expanded; hidden for refusals |
| `frontend/src/components/citations/CitationCard.tsx` | ✓ VERIFIED | filename, page, chunk_index+1, excerpt; 800-char truncation with Show more/less |
| `frontend/src/components/feedback/NetworkBanner.tsx` | ✓ VERIFIED | Sticky top; role="alert"; aria-live="assertive"; Retry button |
| `frontend/src/components/feedback/ToastContainer.tsx` | ✓ VERIFIED | Fixed position; renders Toast components; hidden when empty |
| `frontend/src/context/ToastContext.tsx` | ✓ VERIFIED | ToastProvider wraps children + renders ToastContainer |

---

## Key Link Verification

| From | To | Via | Status | Notes |
|------|----|-----|--------|-------|
| `App.tsx` | `ToastProvider` | wraps entire AppInner | ✓ WIRED | |
| `App.tsx` | `NetworkBanner` | `visible={networkError}` | ✓ WIRED | |
| `AppLayout` | `DocumentPanel` | `onHasReadyDocumentChange` | ✓ WIRED | |
| `AppLayout` | `ChatPanel` | `hasReadyDocument={hasReadyDocument}` | ✓ WIRED | |
| `DocumentPanel` | `useDocuments` | `uploadFile`, `deleteDocument`, `documents` | ✓ WIRED | |
| `DocumentPanel` | `UploadZone` | `onUpload={uploadFile}` — callback signature preserved | ✓ WIRED | Key to Truth #1 fix |
| `UploadZone.processFiles` | `onUpload(file, onStageUpdate)` | callback updates `inFlightFiles` | ✓ WIRED | Confirmed lines 91–107 |
| `useDocuments.uploadFile` | `startSSETracking(docId, onStageUpdate)` | threads callback through | ✓ WIRED | Line 231 |
| `startSSETracking` | `onStageUpdate?.(data.status, data.progress_pct)` | every SSE event | ✓ WIRED | Line 157 |
| `startPolling` | `onStageUpdate?.(doc.status, 0)` | every poll tick, unconditionally | ✓ WIRED | Line 122 (W1 fix) |
| `DocumentCard.handleDeleteConfirm` | `isDeleting` → opacity → 300ms → `onDelete` | sequential await | ✓ WIRED | Lines 101–109 |
| `ChatPanel` | `useChat` | `onNetworkError`, `handleLlmError` | ✓ WIRED | |
| `ChatInput` | `hasReadyDocument` | gates `canSend` + `disabled` | ✓ WIRED | |
| `useChat.sendMessage` | SSE token stream | `streamingContent` state | ✓ WIRED | |
| `useSession` | `sessionStorage` | GET-reuse / POST-fallback | ✓ WIRED | |
| `apiFetch` | FastAPI error envelope | `body.detail` unwrap | ✓ WIRED | |
| `useChat` (NETWORK_ERROR) | `NetworkBanner` | `onNetworkError?.()` → `setNetworkError(true)` | ✓ WIRED | |
| `useDocuments` (NETWORK_ERROR) | `NetworkBanner` | `onNetworkError?.()` propagated | ✓ WIRED | |

---

## Anti-Patterns Scan

No blocking anti-patterns found. All `return null` / empty patterns are legitimate (refusal guard, closed-dialog guard, empty-state guard). All `onChange={() => {}}` patterns documented (real handler on `onInput`). `sendMessage(...).catch(() => {})` is intentional — errors surface as in-thread error bubbles.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

---

## Human Verification Required

### 1. Upload Stage Labels in FileProgressBar

**Test:** Upload a PDF and observe the FileProgressBar inside UploadZone. Watch whether the text labels read "Uploading…", then "Parsing…", "Chunking…", "Embedding (N%)…", "Indexing…", then "Ready ✓" sequentially.
**Expected:** Each label appears as the backend emits the corresponding SSE event; Embedding shows a numeric percentage; the bar auto-removes ~2 seconds after READY.
**Why human:** Static analysis confirms the wiring (UploadZone callback → useDocuments → SSE/polling → inFlightFiles); runtime label delivery requires a live backend emitting SSE events and a browser observing them.

### 2. Q&A Streaming Token-by-Token

**Test:** Type a question about an uploaded PDF and press Enter.
**Expected:** Three-dot typing indicator (TypingIndicator) appears first; then response text builds one token at a time with `▍` cursor at the end; cursor disappears when the stream closes.
**Why human:** Requires live SSE delivery from running backend.

### 3. Citation Section Expand/Collapse

**Test:** Ask a question that returns a grounded (non-refusal) answer. Click "Sources (N)". Click again.
**Expected:** First click expands CitationCards showing filename, page, and excerpt. Second click collapses them. Refusal responses show no Sources section at all.
**Why human:** Interactive toggle behavior requires real browser.

### 4. Network Failure → Persistent Banner + Retry

**Test:** Stop the backend, then send a message or upload a file.
**Expected:** Red "Connection lost" banner appears at the top of the page, persists (does not auto-dismiss); clicking "Retry" reloads the page.
**Why human:** Requires simulating real network failure in a live environment.

---

## Regression Check

All 5 truths that were VERIFIED in the previous run were re-checked for regression:

| Truth | Regression? | Evidence |
|-------|-------------|---------|
| #2 Q&A streaming | None | `useChat.ts` unchanged; SSE token path intact |
| #3 Citations non-refusal | None | `CitationSection.tsx` unchanged |
| #4 Refusal guard | None | `CitationSection.tsx` line 39 guard intact |
| #6 Clear Chat / scroll | None | `useChat.clearMessages()` unchanged |
| #7 Error handling | None | All four error paths confirmed intact |

Build and tests re-run in this session: 314 modules, 0 errors; 37 passed, 1 warning. No regressions detected.

---

## Summary

All 7 must-have truths are now VERIFIED by static analysis and build/test gates. The two gaps from the previous verification (Truth #1 — FileProgressBar stage labels; Truth #5 — delete fade-out) have been closed by plans 02-09 and 02-10, with code-review findings B1/B2/W1/W3 resolved in iteration 4.

**Gap 1 closure (Truth #1):** `UploadZone.processFiles` now passes an `onStageUpdate` callback as the second argument to `onUpload`. `useDocuments.uploadFile` accepts this callback and threads it through `startSSETracking` (and `startPolling` as fallback). Every SSE event calls `onStageUpdate(status, progress_pct)`, which `UploadZone` maps to a `setInFlightFiles` update — making `FileProgressBar` display PARSING/CHUNKING/EMBEDDING/INDEXING labels as they arrive. READY is no longer set prematurely in the HTTP POST success path; the callback is the sole authority for terminal status.

**Gap 2 closure (Truth #5):** `DocumentCard.handleDeleteConfirm` sets `isDeleting(true)`, which drives `opacity: isDeleting ? 0 : 1` with `transition: 'opacity 0.3s ease'`. A 300ms `setTimeout` awaits the CSS transition before calling `onDelete`. The trash button is disabled during the fade window (`disabled={isProcessing || isDeleting}`) to prevent double-delete. On error, a catch block restores `isDeleting(false)` so the card reappears for retry.

**UAT gap closure:** `VITE_API_BASE_URL=` is empty in both `frontend/.env` and `frontend/.env.example`; Vite's proxy handles all `/api` routing without a hardcoded URL.

The phase is functionally complete and all automated verifications pass. Four behaviors require live browser observation to confirm end-to-end runtime delivery.

---

_Verified: 2026-07-17T21:30:00Z_
_Verifier: Claude (pivota_spec-verifier)_
