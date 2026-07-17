---
phase: 2
status: issues_found
blockers: 1
warnings: 3
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
reviewed_at: 2026-07-17T17:30:35Z
iteration: 1
---

# Phase 2 Code Review

## BLOCKERs

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

## WARNINGs

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
| `apiFetch` error shape ↔ FastAPI `HTTPException` default handler | **B1** — mismatch on `detail` envelope |
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
