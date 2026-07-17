---
phase: 2
status: issues_found
blockers: 2
warnings: 3
files_reviewed: 8
files_reviewed_list:
  - frontend/.env
  - frontend/.env.example
  - frontend/src/hooks/useDocuments.ts
  - frontend/src/components/upload/UploadZone.tsx
  - frontend/src/components/documents/DocumentCard.tsx
  - frontend/src/components/documents/DocumentPanel.tsx
  - frontend/src/components/documents/DeleteConfirmDialog.tsx
  - frontend/src/components/upload/FileProgressBar.tsx
reviewed_at: 2026-07-17T18:35:00Z
iteration: 3
---

# Phase 2 Code Review — Iteration 3 (Gap-closure plans 09 and 10)

## BLOCKERs

### B1: Progress bar shows READY immediately after HTTP POST, then regresses to PARSING/CHUNKING/EMBEDDING

- **File:** `frontend/src/components/upload/UploadZone.tsx:99–105` (interacting with `frontend/src/hooks/useDocuments.ts:192–235`)
- **Category:** bug / integration
- **Evidence:**

  `uploadFile()` in `useDocuments.ts` resolves **immediately after the HTTP POST** (line 215), before any SSE stage events arrive. `startSSETracking(docId, onStageUpdate)` is called fire-and-forget (line 231, no `await`). The returned promise therefore settles the moment the upload response is received.

  `processFiles` in `UploadZone.tsx` then runs lines 100–105 synchronously upon `await onUpload(...)` resolution:
  ```ts
  // line 100–102: fires right after HTTP POST, before any SSE event
  setInFlightFiles((prev) =>
    prev.map((f) => (f.id === fileId ? { ...f, status: 'READY', progress_pct: 100 } : f)),
  );
  // line 103–105: scheduled removal at T+2000ms
  setTimeout(() => {
    setInFlightFiles((prev) => prev.filter((f) => f.id !== fileId));
  }, 2000);
  ```

  Backend processing (PARSING → CHUNKING → EMBEDDING → INDEXING → READY) is always sequential and **starts after** the HTTP POST ACKs. SSE events therefore **always arrive after** the READY marking above. The `onStageUpdate` callback then fires in sequence:
  - `onStageUpdate('PARSING', 0)` → overrides READY → bar shows "Parsing…"
  - `onStageUpdate('CHUNKING', 0)` → bar shows "Chunking…"
  - `onStageUpdate('EMBEDDING', pct)` → bar shows "Embedding (N%)…"
  - `onStageUpdate('INDEXING', 0)` → bar shows "Indexing…"
  - `onStageUpdate('READY', 100)` → bar shows "Ready ✓"

  The visual progression is: **UPLOADING → READY → PARSING → CHUNKING → EMBEDDING → INDEXING → READY** — the opposite of the intended sequential display. The READY flash is deterministic (not a timing race), because it is structurally impossible for any SSE event to arrive before the HTTP POST response that triggers `uploadFile` resolution.

  Additional secondary bug: if SSE processing takes longer than 2000ms (realistic for large PDFs), the `setTimeout` at line 103 removes the inFlightFiles entry while SSE is still mid-stream. Subsequent `onStageUpdate` calls call `setInFlightFiles(prev => prev.map(...))` on an entry that no longer exists — the callbacks silently no-op and the progress bar disappears from the UI before the document is actually ready.

  This directly breaks VERIFICATION truth #1: *"FileProgressBar shows PARSING, CHUNKING, EMBEDDING, INDEXING stage labels **sequentially** as the backend processes the document (not just UPLOADING then READY)"* — which is the primary goal of plan 10.

- **Fix direction:** Do not mark the inFlightFiles entry as READY from the `processFiles` catch-success path. Instead, let the `onStageUpdate` callback own the terminal transition: add a guard in `processFiles` so it only marks READY if no `onStageUpdate` callback was provided (backwards compat), or have `onUpload` return a promise that does not resolve until the SSE terminal event fires (propagate a secondary promise through the callback). Alternatively, suppress the `onStageUpdate` callbacks from overriding a status that is already terminal — but the cleanest fix is to remove the immediate READY set from `processFiles` and rely solely on `onStageUpdate('READY')` to mark completion.

**Resolution:** fixed (5d981a7) — removed the immediate `READY`/`setTimeout` from `processFiles`; moved the 2-second removal timeout into the `onStageUpdate` callback triggered only when `status === 'READY' || status === 'FAILED'`. SSE/polling is now the sole authority for terminal transitions. Also eliminates the secondary bug where the 2s timeout removed the entry before SSE completed.

---

### B2: Trash button not disabled during 300 ms `isDeleting` fade — double-delete API call possible

- **File:** `frontend/src/components/documents/DocumentCard.tsx:180–196`
- **Category:** bug
- **Evidence:**

  The delete button's `disabled` prop is gated on `isProcessing` (doc status) only:
  ```tsx
  // line 183
  disabled={isProcessing}
  ```
  `isDeleting` is not checked. During the 300 ms opacity-fade window (after user confirms, before `onDelete` fires), the card is still mounted and the trash button is fully clickable.

  Attack path:
  1. User clicks trash → dialog opens.
  2. User clicks Confirm → `handleDeleteConfirm` starts:
     - `setShowDeleteDialog(false)` — dialog dismissed.
     - `setIsDeleting(true)` — card begins fading.
     - `await 300ms` — card is at opacity ~0.5, still in DOM.
  3. During the 300 ms wait, user clicks the (still-enabled) trash button.
  4. `setShowDeleteDialog(true)` — dialog re-opens.
  5. User clicks Confirm again → second `handleDeleteConfirm` starts concurrently:
     - `setIsDeleting(true)` (no-op, already true).
     - `await 300ms`.
     - `await onDelete(doc.doc_id)` ← **second DELETE call to the same doc_id**.
  6. First `handleDeleteConfirm` resolves: `await onDelete(doc.doc_id)` → succeeds (HTTP 204), document removed from state.
  7. Second `handleDeleteConfirm` resolves: `await onDelete(doc.doc_id)` → backend returns **HTTP 404** (already deleted). `useDocuments.deleteDocument` throws `ApiError(404, ...)`.
  8. `handleDeleteConfirm` has **no try-catch**: the rejection is unhandled.

  The unhandled async rejection propagates to the React error boundary (if one exists) or is swallowed silently, depending on the host environment. Either way, the second delete is a spurious 404-error-generating API call that was preventable.

- **Fix direction:** Add `isDeleting` to the `disabled` condition on the trash button: `disabled={isProcessing || isDeleting}`. Optionally also update `aria-label` and `title` to reflect the deleting state.

**Resolution:** fixed (e47221b) — `disabled={isProcessing || isDeleting}` added; `aria-label`, `title`, and icon colour updated to reflect the deleting state.

---

## WARNINGs

### W1: `onStageUpdate` called with terminal statuses in SSE path but not in polling path — asymmetric behavior

- **File:** `frontend/src/hooks/useDocuments.ts:157` (SSE) vs `frontend/src/hooks/useDocuments.ts:120–122` (polling)
- **Evidence:**
  SSE path (line 157) calls `onStageUpdate` for **all** statuses including `READY`/`FAILED`:
  ```ts
  onStageUpdate?.(data.status, data.progress_pct ?? 0);  // no terminal guard
  ```
  Polling path (lines 120–122) only calls it for non-terminal statuses:
  ```ts
  if (!TERMINAL_STATUSES.includes(doc.status)) {
    onStageUpdate?.(doc.status, 0);
  }
  ```
  In the SSE path the `READY` call on `onStageUpdate` is the one that should eventually mark the inFlightFiles entry as ready (once B1 is fixed). In the polling path that signal is never sent, so the polling-path upload would also need the direct processFiles READY set (or a terminal signal from the polling path) to function. Fixing B1 will need to account for both paths symmetrically.

**Resolution:** fixed (3dab703) — removed the `!TERMINAL_STATUSES.includes(doc.status)` guard from the polling path so `onStageUpdate` is called unconditionally for all statuses, mirroring the SSE path. The READY signal now propagates through polling as well, triggering the inFlightFiles removal scheduled in the B1 fix.

---

### W2: `VITE_API_BASE_URL=` (empty) in committed `.env` silently breaks any non-proxy production deployment

- **File:** `frontend/.env:1`
- **Evidence:**
  With `VITE_API_BASE_URL=`, `apiFetch` builds relative paths (`/api/...`). Relative paths work only when the frontend and backend share the same origin, or a reverse proxy (nginx/caddy) routes `/api/*` to the backend. The `.env` file is committed to the repository. A developer copying the repo and running `npm run build` for a production deploy where the backend is on a different host will get a silently broken app — all API calls will hit the frontend origin's `/api/...` and return 404 without any build-time warning.

  The `.env.example` comment ("Set to absolute URL only for standalone deploys") documents the intent, but `.env` itself has no comment. Because `VITE_API_BASE_URL` is declared as `readonly VITE_API_BASE_URL: string` in `vite-env.d.ts` (never undefined), the `?? ''` fallbacks in `client.ts`, `documents.ts`, and `chat.ts` are redundant (not a bug, but dead code).

  The Vite proxy is in the `server` block only — it does not affect production builds. `npm run build` succeeds with no warnings even when `VITE_API_BASE_URL` is empty.

- **Note:** The `.env.example` guidance is correct; the risk is documentation/operational, not a runtime error in the intended dev setup. Classified WARNING rather than BLOCKER because the dev proxy use case (the intended mode) works correctly.

**Resolution:** disputed — the dev setup (Vite proxy) works correctly; the risk is a documentation concern only. No code change made per scope rules (operational risk, not a runtime bug in the intended mode). New finding recorded for re-review if a production deployment scenario is added.

---

### W3: `handleDeleteConfirm` has no error handling around `onDelete` — API errors are silently swallowed or cause unhandled rejections

- **File:** `frontend/src/components/documents/DocumentCard.tsx:100–105`
- **Evidence:**
  ```ts
  const handleDeleteConfirm = async () => {
    setShowDeleteDialog(false);
    setIsDeleting(true);
    await new Promise((resolve) => setTimeout(resolve, 300));
    await onDelete(doc.doc_id);   // ← no try/catch
  };
  ```
  `handleDeleteConfirm` is passed as `onConfirm` to `DeleteConfirmDialog`, which wraps the call in `try/finally` (lines 38–42 of `DeleteConfirmDialog.tsx`) — the `finally` calls `setIsDeleting(false)` on the dialog's own local state. However, `DeleteConfirmDialog` was unmounted by `setShowDeleteDialog(false)` at step 1, so the `finally` fires on an unmounted component (React 18 no-op). The rejection from `onDelete` propagates out of `DeleteConfirmDialog.handleConfirm`, at which point there is no catch handler above it in the component tree (unless a React Error Boundary is mounted).

  The 300 ms delay added by plan 10 increases exposure: it adds a window during which the document could be externally deleted (session TTL, another tab, B2's double-delete scenario above), making a 404 from `onDelete` more likely than before the delay was introduced.

- **Fix direction:** Wrap the `await onDelete(doc.doc_id)` call in a try-catch inside `handleDeleteConfirm`. On error, reset `isDeleting` to `false` and surface the error (toast or inline message). This also recovers the card's opacity if the delete fails.

**Resolution:** fixed (e47221b) — `onDelete` wrapped in try-catch inside `handleDeleteConfirm`; on error, `setIsDeleting(false)` resets the card opacity so the user can retry. Bundled with B2 commit since both touch `DocumentCard.tsx`.

---

## Cross-file seams checked

| Seam | Result |
|---|---|
| `UploadZoneProps.onUpload` signature ↔ `uploadFile` signature in `useDocuments` return type | OK — both now `(file: File, onStageUpdate?: ...) => Promise<void>`; `DocumentPanel` passes `uploadFile` directly, TypeScript build passes |
| `onStageUpdate` callback parameter types ↔ `DocumentStatus` union and `progress_pct: number` | OK — types match across `useDocuments.ts`, `UploadZone.tsx`, `FileProgressBar.tsx` |
| `processFiles` READY set ↔ SSE `onStageUpdate(READY)` — sequencing | **B1** — processFiles READY always fires before SSE events |
| `isDeleting` (DocumentCard) ↔ trash button `disabled` prop | **B2** — isDeleting not included in disabled check |
| `handleDeleteConfirm` ↔ `DeleteConfirmDialog.onConfirm` contract | W3 — no error handling in `handleDeleteConfirm`; dialog's finally fires on unmounted component |
| `VITE_API_BASE_URL=` ↔ `apiFetch`, `openUploadStream`, `openChatStream` URL construction | W2 — dev proxy works; production non-proxy deployments silently broken |
| `onStageUpdate` terminal status behavior: SSE path vs polling path | W1 — asymmetric; SSE fires with READY, polling does not |
| `DocumentPanel` ↔ `UploadZone onUpload={uploadFile}` — optional second param compatibility | OK — existing call site `onUpload={uploadFile}` is type-compatible; `onStageUpdate` is optional |
| `DocumentPanel` ↔ `DocumentCard onDelete={deleteDocument}` | OK — signature unchanged |
| `FileProgressBar` receives `status: DocumentStatus` and `progress_pct: number` from `InFlightFile` | OK — `InFlightFile` shape and `FileProgressBar` props align |
| `tsc && vite build` | OK — exits 0, no TypeScript errors |

---

## Iteration 2 and Earlier Findings (archived)

All findings from iterations 1 and 2 (B1–W3 from those rounds) are confirmed resolved in the pre-existing codebase. The findings above (B1, B2, W1, W2, W3) are **new** findings introduced by gap-closure plans 09 and 10.
