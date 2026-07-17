---
phase: 2
status: clean
blockers: 0
warnings: 0
files_reviewed: 34
files_reviewed_list:
  - frontend/src/api/client.ts
  - frontend/src/api/sessions.ts
  - frontend/src/api/documents.ts
  - frontend/src/api/chat.ts
  - frontend/src/types/api.ts
  - frontend/src/hooks/useSession.ts
  - frontend/src/hooks/useDocuments.ts
  - frontend/src/hooks/useChat.ts
  - frontend/src/hooks/useToast.ts
  - frontend/src/hooks/useFocusTrap.ts
  - frontend/src/App.tsx
  - frontend/src/components/layout/AppLayout.tsx
  - frontend/src/components/chat/ChatPanel.tsx
  - frontend/src/components/chat/MessageThread.tsx
  - frontend/src/components/chat/MessageBubble.tsx
  - frontend/src/components/chat/ChatInput.tsx
  - frontend/src/components/chat/ClearChatDialog.tsx
  - frontend/src/components/chat/TypingIndicator.tsx
  - frontend/src/components/documents/DocumentPanel.tsx
  - frontend/src/components/documents/DocumentCard.tsx
  - frontend/src/components/documents/DeleteConfirmDialog.tsx
  - frontend/src/components/upload/UploadZone.tsx
  - frontend/src/components/upload/FileProgressBar.tsx
  - frontend/src/components/citations/CitationSection.tsx
  - frontend/src/components/citations/CitationCard.tsx
  - frontend/src/components/feedback/NetworkBanner.tsx
  - frontend/src/components/feedback/ToastContainer.tsx
  - frontend/src/components/feedback/Toast.tsx
  - frontend/src/context/ToastContext.tsx
  - frontend/src/utils/constants.ts
  - frontend/src/utils/formatters.ts
  - frontend/src/styles/globals.css
  - frontend/src/main.tsx
  - backend/app/routers/sessions.py   # read to verify error shape (cross-file seam)
reviewed_at: 2026-07-17T17:50:00Z
iteration: 2
---

# Phase 2 Code Review

## Iteration 2 — Re-review Summary

All four findings from iteration 1 (B1, W1, W2, W3) are **confirmed fixed**. No
regressions introduced by the fixes. No new BLOCKERs or WARNINGs found.

### B1 — RESOLVED ✓
**Fix commit:** b76deb2

**Verification:**  
`frontend/src/api/client.ts` line 59 now reads:
```ts
const payload = body?.detail && typeof body.detail === 'object' ? body.detail : body;
errorCode    = payload.error_code ?? errorCode;
errorMessage = payload.message ?? errorMessage;
```
- The `typeof body.detail === 'object'` guard correctly handles: FastAPI HTTPException
  (detail is dict → unwrap), pydantic validation errors (detail is array → falls back to
  `body`, yields `UNKNOWN_ERROR` which is acceptable since those are programmer errors, not
  user-facing), and plain string details (falls back to `body`).
- The null-body edge case (`response.json()` returns null → `payload.error_code` throws)
  is caught by the surrounding `try/catch` that falls back to the HTTP status-line default
  — same behavior as before, no regression.
- `tsc --noEmit` passes with zero errors.

### W1 — RESOLVED ✓
**Fix commit:** d1892e2

**Verification:**  
`frontend/src/App.tsx` retains the single `.skip-link` anchor (lines 94–101). A grep for
`skip-link` across `App.tsx` and `AppLayout.tsx` confirms it appears only in `App.tsx` —
the duplicate block that was previously at `AppLayout.tsx:140–147` is gone. The skip-link
is now the first focusable element in DOM order, before `AppLayout`.

### W2 — RESOLVED ✓
**Fix commit:** e90e797

**Verification:**  
Both dialog overlay `div` elements no longer carry `aria-hidden`. Confirmed by grep
returning zero matches for `aria-hidden` in `ClearChatDialog.tsx` and
`DeleteConfirmDialog.tsx`. The `aria-hidden="true"` that remains in `AppLayout.tsx` (line
144) is on the `.drawer-backdrop` — a purely visual overlay with no interactive or
semantic content — which is the correct and intended use of `aria-hidden`.

### W3 — RESOLVED ✓
**Fix commit:** b3d3099

**Verification:**  
`UploadZone.tsx` `catch` block (lines 99–113) no longer calls `addError`. Only
`setInFlightFiles` with `status:'FAILED'` and `error_message` is called. The `addError`
function is still referenced at line 77 for client-side validation failures (no
`FileProgressBar` entry in that path), so the `addError` definition and its use in the
validation branch remain correct. The `processFiles` `useCallback` dependency array no
longer lists `addError` (line 117).

---

## Fresh-scan for new issues (iteration 2)

Files touched by fix commits: `frontend/src/api/client.ts`, `frontend/src/App.tsx`,
`frontend/src/components/layout/AppLayout.tsx`, `frontend/src/components/chat/ClearChatDialog.tsx`,
`frontend/src/components/documents/DeleteConfirmDialog.tsx`,
`frontend/src/components/upload/UploadZone.tsx`, `frontend/src/components/chat/ChatPanel.tsx`,
`frontend/src/components/chat/MessageThread.tsx`, `frontend/src/components/chat/MessageBubble.tsx`,
`frontend/src/hooks/useChat.ts`, `frontend/src/hooks/useDocuments.ts`,
`frontend/src/styles/globals.css`.

All were read in full. No new BLOCKERs or WARNINGs found. Notable items examined and
cleared:

- **`onLlmError` called twice on SSE `error` event:** The SSE `error` branch at
  `useChat.ts:168–188` calls `onLlmError(data.message)` and also sets the error bubble.
  `ChatPanel` passes `handleLlmError` as `onLlmError`, which calls `addToast`. The
  toast and the in-thread error bubble are distinct UI surfaces (one transient, one
  permanent), so dual notification is intentional and correct.

- **`MessageBubble.onRetry` signature change:** The prop changed from
  `(query: string) => void` to `() => void`; `MessageThread` now pre-binds the prior
  user query before passing it down. Call site at `MessageThread:127–129` correctly
  wraps `onRetry(priorUserQuery)` in a closure. No drift detected.

- **`processFiles` stale-closure risk after removing `addError` from deps:** `addError`
  is a `useCallback` with an empty dep array — it is stable across renders. Removing it
  from the `processFiles` dep array is safe and correct.

- **`btn-secondary` CSS class in `FileProgressBar.tsx`:** Used at line 151 (`className="btn btn-secondary"`). Class is defined in `frontend/src/styles/components.css:34`. No missing style.

- **`globals.css` additions from phase implementation (not fixer):** Newly added
  `@keyframes slideInRight`, `.spinner`, `.btn`, `.btn-primary`, `.btn-ghost`,
  `.btn-danger` blocks are all valid and consistent with their usage sites. No collision
  with `components.css` variants.

---

## BLOCKERs

_None._

## WARNINGs

_None._

---

## Iteration 1 Findings (archived)

### B1: `apiFetch` error-body parser reads fields that don't exist at the top level of FastAPI's error envelope

- **File:** `frontend/src/api/client.ts:55–56`
- **Category:** integration
- **Evidence:**

  The frontend parses API errors as:
  ```ts
  errorCode    = body.error_code ?? errorCode;          // line 55
  errorMessage = body.message ?? body.detail ?? errorMessage;  // line 56
  ```

  All backend routers (sessions, documents, chat) raise errors via:
  ```python
  raise HTTPException(
      status_code=4xx,
      detail=ErrorResponse(...).model_dump(),   # a plain dict
  )
  ```

  FastAPI's (Starlette's) default `HTTPException` handler wraps `detail` one level
  deeper, producing:
  ```json
  { "detail": { "error_code": "EMPTY_QUERY", "message": "Query cannot be empty" } }
  ```

  Verified empirically with FastAPI v0.139.2 (no custom `HTTPException` handler is
  registered in `backend/app/main.py`; only a generic `Exception` handler exists).

  As a result:
  - `body.error_code` → `undefined` → `errorCode` stays `'UNKNOWN_ERROR'` for every
    4xx/5xx response.
  - `body.message` → `undefined`.
  - `body.detail` → the nested dict object (not `null/undefined`), so the nullish
    coalescing short-circuits there and `errorMessage` is assigned **the dict object**.
  - When `new ApiError(..., errorMessage)` calls `super(message)`, the `Error`
    constructor stringifies the object to `'[object Object]'`.

  **Concrete failing path:**
  1. User sends a chat query with no ready documents → backend returns HTTP 422 with
     `{ "detail": { "error_code": "NO_DOCUMENTS_READY", "message": "No ready documents found..." } }`.
  2. `apiFetch` throws `ApiError(422, 'UNKNOWN_ERROR', '[object Object]')`.
  3. `useChat.sendMessage` catches it, calls `onLlmError('[object Object]')`.
  4. `ChatPanel` calls `addToast('[object Object]', 'error')`.
  5. User sees **"[object Object]"** in the error toast and error bubble — every time.

  The same corruption occurs for: upload errors (rate limit, file too large from server,
  parse failures), session errors propagated to `useSession.error`, and document-list
  failures.

  TypeScript does not flag this because `response.json()` returns `any`.

- **Fix direction:** Change the parser to look one level deeper:
  ```ts
  const body = await response.json();
  const payload = body?.detail ?? body;          // unwrap FastAPI's envelope
  errorCode    = payload.error_code ?? errorCode;
  errorMessage = payload.message ?? errorMessage;
  ```
  Alternatively, add a custom FastAPI `HTTPException` handler in the backend that
  emits `ErrorResponse` fields at the top level (matching what the frontend already
  expects). Either side can fix it, but the frontend fix is the smallest change.

**Resolution:** fixed (b76deb2) — unwraps `body.detail` when it is an object (HTTPException path) before extracting `error_code`/`message`; falls back to `body` itself for the generic Exception handler path. `tsc --noEmit` clean; `npm run build` 0 errors; 37 backend tests pass.

---

### W1: Duplicate skip-link rendered once the app has a session

- **File:** `frontend/src/App.tsx:94–101` and `frontend/src/components/layout/AppLayout.tsx:140–147`
- **Evidence:**
  `AppInner` renders a `<a class="skip-link" href="#chat-input">` at line 94 of
  `App.tsx`. `AppLayout` (always rendered below `AppInner` when `sessionId` is set)
  renders a second identical skip-link at line 140 inside its flex container. A
  keyboard user pressing **Tab** on page load encounters two consecutive "Skip to main
  content" links, which is confusing and non-standard. The one inside AppLayout also
  appears after the drawer backdrop in DOM order, so its position in the tab sequence
  is wrong.

- **Fix direction:** Remove the skip-link from `App.tsx` (or from `AppLayout.tsx`)
  so only one exists per page.

**Resolution:** fixed (d1892e2) — removed the duplicate skip-link block (lines 139–147) from `AppLayout.tsx`; the authoritative skip-link in `App.tsx` (first DOM element before `AppLayout`) remains. `tsc --noEmit` clean.

---

### W2: Both modal overlays carry `aria-hidden="true"`, hiding the inner dialog from screen readers

- **File:** `frontend/src/components/chat/ClearChatDialog.tsx:48` and
  `frontend/src/components/documents/DeleteConfirmDialog.tsx:51`
- **Evidence:**
  ```tsx
  <div className="modal-overlay" aria-hidden="true">   {/* hides everything inside */}
    <div role="dialog" aria-modal="true" …>             {/* invisible to AT */}
  ```
  `aria-hidden="true"` on the parent removes the entire subtree from the accessibility
  tree. The `role="dialog"` and `aria-labelledby` on the inner `div` are therefore
  unreachable by screen readers. Users on AT cannot perceive or interact with either
  confirmation dialog, making a potentially destructive action (delete document, clear
  history) inaccessible.

- **Fix direction:** Remove `aria-hidden="true"` from the overlay `div`. If the intent
  was to hide the backdrop ornament itself, apply it only to an empty decoration
  element, not the outer wrapper that contains the dialog.

**Resolution:** fixed (e90e797) — removed `aria-hidden="true"` from the `.modal-overlay` div in both `ClearChatDialog.tsx` and `DeleteConfirmDialog.tsx`; the inner `role="dialog" aria-modal="true" aria-labelledby="..."` elements are now fully reachable by assistive technology. `tsc --noEmit` clean.

---

### W3: Failed-upload error is displayed twice simultaneously in `UploadZone`

- **File:** `frontend/src/components/upload/UploadZone.tsx:99–111`
- **Evidence:**
  When `onUpload` rejects, two things happen in sequence:
  ```ts
  setInFlightFiles((prev) =>
    prev.map((f) =>
      f.id === fileId ? { ...f, status: 'FAILED', error_message: message } : f,
    ),
  );           // FileProgressBar renders error_message text + Retry button  (line 106-109)
  addError(fileId, message);  // adds same message to the inline errors list (line 111)
  ```
  The `FileProgressBar` with `status='FAILED'` already renders the error message and
  a Retry button (lines 130–158 of `FileProgressBar.tsx`). The separate `errors` list
  below then renders the exact same message again with a dismiss `✕` button. A user
  sees the error text twice; dismissing via `✕` removes the lower copy but leaves the
  `FileProgressBar` entry with FAILED state and the error still visible.

- **Fix direction:** On upload failure, either populate `inFlightFiles` with FAILED
  state (showing the error inside `FileProgressBar`) **or** call `addError`, but not
  both. Whichever path is dropped, ensure a retry mechanism remains available.

**Resolution:** fixed (b3d3099) — removed the `addError(fileId, message)` call in the `catch` block; upload failures now only set `status:'FAILED'` + `error_message` on the `inFlightFiles` entry, which `FileProgressBar` renders with the Retry button. Client-side validation errors (no `FileProgressBar` entry) continue to use `addError` as before. Also removed `addError` from the `processFiles` `useCallback` dependency array. `tsc --noEmit` clean; `npm run build` 0 errors.

---

## Cross-file seams checked

| Seam | Result |
|---|---|
| `apiFetch` error shape ↔ FastAPI `HTTPException` default handler | **B1** — fixed (b76deb2) |
| `createSession` / `getSession` response shape ↔ `Session` type | OK — `session_id`, `created_at`, `document_count` match |
| `uploadDocument` return shape ↔ `{ doc_id, filename, status }` call site | OK |
| `sendQuery` → `QueryInitResponse.message_id` ↔ `openChatStream(messageId)` | OK |
| `getHistory` → `ChatHistoryResponse` ↔ `Message[]` hydration in `useChat` | OK |
| `SSEDoneEvent.message` type (`Message`) ↔ `setMessages` usage | OK |
| `Citation.page_number: number | null` ↔ `CitationCard` null-guard (`<= 0` → `'N/A'`) | OK |
| `Citation.excerpt: string` ↔ `CitationCard` null/empty guard (`hasExcerpt`) | OK — defensive guard present |
| `hasReadyDocument` propagation: `DocumentPanel` → `AppLayout` → `ChatPanel` → `ChatInput` | OK — `useEffect` in `DocumentPanel` notifies parent; `ChatInput` gates send |
| `useChat(_hasReadyDocument)` parameter ignored internally | OK — `hasReadyDocument` enforced at `ChatInput` layer; parameter is intentionally unused in hook |
| `useSession` 404 branch removes stored ID and falls through to create | OK — uses `statusCode === 404`, not `errorCode`, so unaffected by B1 |
| `useToast` timer cleanup on dismiss | OK — `timersRef` cleared in `dismissToast` |
| `useFocusTrap` focus restore on dialog close | OK — `previouslyFocusedRef` pattern correct |
| `EventSource` cleanup in `useChat` on unmount | OK — `activeStreamRef.current?.close()` in `useEffect` cleanup |
| `EventSource` cleanup in `useDocuments` on unmount | OK — `activeStreams`/`activePolls` Maps iterated in `useEffect` cleanup |
| `react-markdown` v9 XSS surface | OK — raw HTML stripped by default; no `rehype-raw` or `allowDangerousHtml` configured |
| `VITE_API_BASE_URL` used consistently across `client.ts`, `chat.ts`, `documents.ts` | OK — same env var, same fallback `''` |
| `MessageBubble.onRetry` signature `() => void` ↔ `MessageThread` call site | OK — `MessageThread` pre-binds `priorUserQuery` in closure before passing down (iteration 2) |
| `onLlmError` double-notification (toast + error bubble) | OK — intentional: toast is transient, error bubble is persistent; distinct UI surfaces |
| `btn-secondary` CSS class ↔ `FileProgressBar.tsx:151` usage | OK — defined in `components.css:34` |
