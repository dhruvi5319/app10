# Phase 2 Plan: Core MVP UI & Session

**Phase goal:** A fully built React frontend wired end-to-end to the Phase 1 backend. Every P0 and P1 feature is complete and usable in a browser by a real user — upload documents, watch ingestion progress, ask questions, stream answers, read cited sources, manage the document library, and scroll session history — with no developer tooling required.

**Source documents:** FRD F00 (frontend half), F01 (frontend half), F02 (rendering), F03, F04, F05, ROADMAP Phase 2

**Depends on:** Phase 1 backend fully operational (all REST/SSE endpoints live on `http://localhost:8000`)

---

## Target Directory Layout

```
frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── main.tsx                     # React 18 createRoot entry point
│   ├── App.tsx                      # Root component: session init + layout
│   ├── api/
│   │   ├── client.ts                # Base fetch wrapper: session_id injection, error normalisation
│   │   ├── sessions.ts              # createSession(), getSession()
│   │   ├── documents.ts             # uploadDocument(), getDocumentStatus(), listDocuments(), deleteDocument()
│   │   └── chat.ts                  # sendQuery(), streamChat(), getHistory(), clearHistory()
│   ├── components/
│   │   ├── layout/
│   │   │   └── AppLayout.tsx        # Two-column shell: DocumentPanel + ChatPanel
│   │   ├── upload/
│   │   │   ├── UploadZone.tsx       # Drag-and-drop + click-to-browse zone
│   │   │   └── FileProgressBar.tsx  # Per-file stage progress bar
│   │   ├── documents/
│   │   │   ├── DocumentPanel.tsx    # Sidebar wrapper: header, list, empty state
│   │   │   ├── DocumentCard.tsx     # Single document card with status badge + delete
│   │   │   └── DeleteConfirmDialog.tsx  # Confirmation modal for document deletion
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx        # Chat panel wrapper: thread + input bar
│   │   │   ├── MessageThread.tsx    # Scrollable message list with auto-scroll
│   │   │   ├── MessageBubble.tsx    # User/assistant bubble with timestamp + markdown
│   │   │   ├── TypingIndicator.tsx  # Animated ellipsis while LLM is streaming
│   │   │   ├── ChatInput.tsx        # Textarea + send button + guard message
│   │   │   └── ClearChatDialog.tsx  # Confirmation modal for clearing history
│   │   ├── citations/
│   │   │   ├── CitationSection.tsx  # Collapsible "Sources (N)" container
│   │   │   └── CitationCard.tsx     # Single source card: filename, page, excerpt
│   │   └── feedback/
│   │       ├── Toast.tsx            # Toast notification (auto-dismiss / persist)
│   │       ├── ToastContainer.tsx   # Fixed-position toast stack
│   │       └── NetworkBanner.tsx    # Persistent network-error banner
│   ├── hooks/
│   │   ├── useSession.ts            # Initialise/reuse session_id in sessionStorage
│   │   ├── useDocuments.ts          # Document list state, upload, delete, polling
│   │   ├── useChat.ts               # Chat history state, send query, SSE stream
│   │   └── useToast.ts              # Toast queue management
│   ├── types/
│   │   └── api.ts                   # TypeScript interfaces mirroring API response shapes
│   ├── utils/
│   │   ├── formatters.ts            # formatRelativeTime(), formatFileSize(), truncateFilename()
│   │   └── constants.ts             # MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS, POLLING_INTERVAL_MS
│   └── styles/
│       ├── globals.css              # CSS reset + design tokens (colours, spacing, typography)
│       └── components.css           # Shared component utility classes
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── .env.example                     # VITE_API_BASE_URL=http://localhost:8000
```

---

## Tasks

---

### T01 — Project Scaffold & API Client

**What it delivers:** The frontend skeleton every other task builds on: Vite + React 18 + TypeScript project, design tokens, shared TypeScript types, and the API client module that injects `session_id` and normalises errors for every backend call.

**Files:**

| File | Content |
|------|---------|
| `frontend/package.json` | Dependencies (see list below) |
| `frontend/vite.config.ts` | Vite config: port 3000, proxy `/api` → `http://localhost:8000` |
| `frontend/tsconfig.json` | Strict TypeScript config, path aliases `@/*` → `src/*` |
| `frontend/index.html` | HTML shell; mounts `#root`; loads `src/main.tsx` |
| `frontend/src/main.tsx` | `createRoot(document.getElementById('root')).render(<App />)` |
| `frontend/src/types/api.ts` | All TypeScript interfaces (see below) |
| `frontend/src/utils/constants.ts` | `MAX_FILE_SIZE_BYTES`, `ALLOWED_EXTENSIONS`, `POLLING_INTERVAL_MS = 1500` |
| `frontend/src/utils/formatters.ts` | `formatRelativeTime()`, `formatFileSize()`, `truncateFilename(name, max=30)` |
| `frontend/src/styles/globals.css` | CSS reset + design tokens |
| `frontend/.env.example` | `VITE_API_BASE_URL=http://localhost:8000` |
| `frontend/src/api/client.ts` | `apiFetch()` base wrapper |

**Pinned dependencies (`package.json`):**
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.4.5",
    "vite": "^5.2.11"
  }
}
```

**`types/api.ts` interfaces:**

```typescript
export interface Session {
  session_id: string;
  created_at: string;
  document_count: number;
}

export type DocumentStatus =
  | 'UPLOADING' | 'PARSING' | 'CHUNKING'
  | 'EMBEDDING' | 'INDEXING' | 'READY' | 'FAILED';

export interface Document {
  doc_id: string;
  session_id: string;
  filename: string;
  file_type: 'pdf' | 'txt' | 'docx';
  file_size_bytes: number;
  status: DocumentStatus;
  chunk_count: number | null;
  page_count: number | null;
  error_message: string | null;
  uploaded_at: string;
  ready_at: string | null;
}

export interface DocumentListResponse {
  session_id: string;
  document_count: number;
  total_size_bytes: number;
  documents: Document[];
}

export interface ProgressEvent {
  doc_id: string;
  status: DocumentStatus;
  progress_pct: number;
  message: string;
}

export interface Citation {
  chunk_id: string;
  doc_id: string;
  filename: string;
  page_number: number | null;
  chunk_index: number;
  excerpt: string;
  similarity_score: number;
}

export interface Message {
  message_id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  is_refusal: boolean | null;
  retrieved_chunks: Citation[] | null;
  created_at: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  message_count: number;
  messages: Message[];
}

export interface QueryInitResponse {
  message_id: string;
}

export interface SSETokenEvent {
  type: 'token';
  delta: string;
}

export interface SSEDoneEvent {
  type: 'done';
  message: Message;
}

export interface SSEErrorEvent {
  type: 'error';
  error_code: string;
  message: string;
}

export type SSEEvent = SSETokenEvent | SSEDoneEvent | SSEErrorEvent;

export interface ApiError {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}
```

**`api/client.ts` spec:**

```typescript
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export class ApiError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly errorCode: string,
    message: string,
  ) { super(message); }
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  // Prepends BASE_URL; sets Content-Type if not multipart
  // On 4xx/5xx: reads JSON body, throws ApiError(status, error_code, message)
  // On network failure (TypeError): throws ApiError(0, 'NETWORK_ERROR', ...)
}
```

**CSS design tokens (`styles/globals.css`):**
```css
:root {
  --color-bg: #0f1117;
  --color-surface: #1a1d26;
  --color-surface-2: #22263a;
  --color-border: #2e3350;
  --color-accent: #6c63ff;
  --color-accent-hover: #7b74ff;
  --color-text-primary: #e8eaf0;
  --color-text-secondary: #8b90a0;
  --color-text-muted: #5a5f72;
  --color-success: #34c98b;
  --color-warning: #f5a623;
  --color-error: #e5534b;
  --color-user-bubble: #2d3250;
  --color-assistant-bubble: #1e2235;
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --shadow-card: 0 2px 8px rgba(0,0,0,0.3);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--color-bg); color: var(--color-text-primary);
       font-family: var(--font-sans); line-height: 1.6; }
```

**Acceptance criteria:**
- [ ] `npm install` completes without errors
- [ ] `npm run dev` starts on port 3000; browser shows blank React app without errors
- [ ] `apiFetch('/api/sessions', { method: 'POST' })` returns a parsed JSON object (backend must be running)
- [ ] `ApiError` is thrown on a 404 response with correct `statusCode` and `errorCode`
- [ ] All TypeScript interfaces in `types/api.ts` compile without errors

---

### T02 — Session Hook & Initialisation

**What it delivers:** The `useSession` hook that creates or reuses a `session_id` on app load, then hydrates the initial document list and chat history. This is the root data initialisation that all other hooks depend on.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/api/sessions.ts` | `createSession()`, `getSession()` |
| `frontend/src/hooks/useSession.ts` | Session init hook |
| `frontend/src/App.tsx` | Root component that calls `useSession` and renders layout |

**`api/sessions.ts` spec:**
```typescript
export async function createSession(): Promise<Session> {
  return apiFetch<Session>('/api/sessions', { method: 'POST' });
}

export async function getSession(sessionId: string): Promise<Session> {
  return apiFetch<Session>(`/api/sessions/${sessionId}`);
}
```

**`useSession` spec:**
```typescript
export function useSession(): {
  sessionId: string | null;
  loading: boolean;
  error: string | null;
}
// On mount:
//   1. Check sessionStorage.getItem('session_id')
//   2. If found: call getSession(id); if 404 → create new; else reuse
//   3. If not found: call createSession(); store id in sessionStorage
// Sets sessionId in state; loading=true while pending; error=message on failure
```

**`App.tsx` spec:**
- Calls `useSession()` — shows a centered loading spinner while `loading === true`
- Shows a full-screen error message if `error !== null` ("Failed to start session. Please refresh.")
- When `sessionId` is available: renders `<AppLayout sessionId={sessionId} />`

**Acceptance criteria:**
- [ ] On first load (empty sessionStorage): `POST /api/sessions` is called once; `session_id` stored in sessionStorage
- [ ] On second load (sessionStorage has id): `GET /api/sessions/{id}` is called; no new session created
- [ ] If stored session returns 404: a new session is created and old id replaced
- [ ] `loading` is `true` during the fetch and `false` after
- [ ] App renders without error if backend is unreachable (shows error state, not crash)

---

### T03 — Application Layout

**What it delivers:** The two-column desktop shell: fixed-width Document Panel on the left (280 px) and the Chat Panel filling the rest. Clean, dark-themed layout with no responsive breakpoints yet (Phase 3 handles mobile/tablet).

**Files:**

| File | Content |
|------|---------|
| `frontend/src/components/layout/AppLayout.tsx` | Two-column shell |

**`AppLayout.tsx` spec:**
```tsx
// Props: { sessionId: string }
// Layout:
//   <div style="display:flex; height:100vh; overflow:hidden">
//     <aside style="width:280px; flex-shrink:0; border-right:1px solid var(--color-border); overflow-y:auto">
//       <DocumentPanel sessionId={sessionId} />
//     </aside>
//     <main style="flex:1; min-width:0; display:flex; flex-direction:column">
//       <ChatPanel sessionId={sessionId} />
//     </main>
//   </div>
```

**Acceptance criteria:**
- [ ] Document Panel is always 280 px wide at desktop viewport (≥ 1024 px)
- [ ] Chat Panel fills remaining width
- [ ] No horizontal scrollbar on the page at 1440 px viewport
- [ ] Both panels are independently scrollable

---

### T04 — Document API Module & `useDocuments` Hook

**What it delivers:** All document API calls and the `useDocuments` hook that manages the document list state, upload dispatch, polling for PROCESSING documents, and delete.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/api/documents.ts` | All document API functions |
| `frontend/src/hooks/useDocuments.ts` | Document list state management |

**`api/documents.ts` spec:**

```typescript
export async function listDocuments(sessionId: string): Promise<DocumentListResponse> {
  return apiFetch<DocumentListResponse>(`/api/documents?session_id=${sessionId}`);
}

export async function uploadDocument(
  sessionId: string,
  file: File,
): Promise<{ doc_id: string; filename: string; status: string }> {
  const form = new FormData();
  form.append('file', file);
  form.append('session_id', sessionId);
  return apiFetch('/api/documents/upload', { method: 'POST', body: form });
}

export async function getDocumentStatus(docId: string): Promise<Document> {
  return apiFetch<Document>(`/api/documents/${docId}/status`);
}

export async function deleteDocument(docId: string): Promise<void> {
  await apiFetch(`/api/documents/${docId}`, { method: 'DELETE' });
}

export function openUploadStream(docId: string): EventSource {
  return new EventSource(
    `${import.meta.env.VITE_API_BASE_URL ?? ''}/api/documents/upload/stream?doc_id=${docId}`
  );
}
```

**`useDocuments` hook spec:**

```typescript
export function useDocuments(sessionId: string): {
  documents: Document[];
  totalSizeBytes: number;
  uploadFile: (file: File) => Promise<void>;
  deleteDocument: (docId: string) => Promise<void>;
  refreshDocuments: () => Promise<void>;
}
```

- On mount: calls `listDocuments(sessionId)` and sets state
- `uploadFile(file)`:
  1. Client-side validation: size > `MAX_FILE_SIZE_BYTES` → throw with `FILE_TOO_LARGE`; extension not in `ALLOWED_EXTENSIONS` → throw with `INVALID_FILE_TYPE`
  2. Call `uploadDocument(sessionId, file)` → get `doc_id`
  3. Add optimistic document entry to state with `status: 'UPLOADING'`
  4. Open SSE stream via `openUploadStream(doc_id)` — on each event: update document status in state
  5. On READY or FAILED: close SSE; update final state
  6. Fallback: if SSE unavailable, poll `getDocumentStatus(doc_id)` every `POLLING_INTERVAL_MS` until terminal status
- `deleteDocument(docId)`:
  1. Call `deleteDocument(docId)` API
  2. Remove document from state array on success
- Any `ApiError` thrown propagates to the caller; hook does not catch globally

**Acceptance criteria:**
- [ ] `uploadFile()` with valid file: document appears in state immediately as UPLOADING; transitions to READY after SSE completes
- [ ] `uploadFile()` with file > 20 MB: throws before calling API with `FILE_TOO_LARGE` error code
- [ ] `uploadFile()` with `.exe` file: throws before calling API with `INVALID_FILE_TYPE`
- [ ] `deleteDocument()` removes the document from state
- [ ] Multiple concurrent uploads are each tracked independently in state

---

### T05 — Upload Zone Component

**What it delivers:** The drag-and-drop + click-to-browse upload zone with per-file progress bars and inline error display, wired to the `useDocuments` hook.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/components/upload/UploadZone.tsx` | Drop zone + file picker |
| `frontend/src/components/upload/FileProgressBar.tsx` | Per-file animated stage bar |

**`UploadZone.tsx` spec:**

```tsx
// Props: { onUpload: (file: File) => Promise<void>; disabled?: boolean }
//
// Visual states:
//   default:  dashed border, cloud-upload icon, "Drag files here or click to browse"
//             "Supports PDF, DOCX, TXT — up to 20 MB each"
//   dragover: border turns accent colour, background lightens
//   uploading: progress bars shown per in-flight file (via FileProgressBar)
//   error:    inline error message per rejected file with ✕ dismiss
//
// Behaviour:
//   - onDrop / onDragOver / onDragLeave handlers on the zone div
//   - Hidden <input type="file" accept=".pdf,.txt,.docx" multiple> triggered by click
//   - For each dropped/selected file: call onUpload(file); catch error → display inline
//   - Guard: if disabled (no session): zone shows tooltip "Start a session first"
```

**`FileProgressBar.tsx` spec:**

```tsx
// Props: { filename: string; status: DocumentStatus; progress_pct: number; error_message?: string }
//
// Stage labels:   UPLOADING→"Uploading..." PARSING→"Parsing..." CHUNKING→"Chunking..."
//                 EMBEDDING→"Embedding ({pct}%)..." INDEXING→"Indexing..." READY→"Ready ✓"
//
// Visual:
//   - Filename (truncated if > 30 chars)
//   - Animated progress bar: indeterminate CSS animation for all stages except EMBEDDING
//     (EMBEDDING: filled bar at progress_pct width)
//   - Status: READY → green bar + checkmark; FAILED → red bar + error message + Retry button
//   - Retry button emits onRetry() callback; parent re-calls onUpload(file)
```

**Acceptance criteria:**
- [ ] Dragging a valid PDF onto the zone → calls `onUpload` with the File object
- [ ] Dragging an invalid file (wrong extension) → inline error shown, `onUpload` not called
- [ ] File > 20 MB → inline error "File exceeds the 20 MB limit." shown
- [ ] Progress bar advances through stage labels as SSE events arrive
- [ ] READY state shows green checkmark
- [ ] FAILED state shows red bar + error message + Retry button
- [ ] Multiple simultaneous files each get independent progress bars

---

### T06 — Document Panel Component

**What it delivers:** The left-sidebar document library: panel header with count + storage summary, document cards with status badges, delete button with confirmation dialog, empty state, and collapse toggle wired to `localStorage`.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/components/documents/DocumentPanel.tsx` | Sidebar wrapper |
| `frontend/src/components/documents/DocumentCard.tsx` | Single document card |
| `frontend/src/components/documents/DeleteConfirmDialog.tsx` | Delete confirmation modal |

**`DocumentPanel.tsx` spec:**

```tsx
// Props: { sessionId: string }
// Uses useDocuments(sessionId)
//
// Header:
//   "Documents ({count} / 10)"   total storage in KB/MB (formatFileSize)
//   Collapse toggle button (chevron icon) — collapses to 48px icon strip
//   localStorage key: 'doc_panel_collapsed'
//
// Body:
//   if documents.length === 0:
//     Empty state: file-folder icon + "No documents uploaded yet."
//                  + "Drag a file here or click to upload."
//   else: <DocumentCard> per document
//
// Upload zone embedded at bottom of panel when not collapsed:
//   <UploadZone onUpload={uploadFile} />
```

**`DocumentCard.tsx` spec:**

```tsx
// Props: { document: Document; onDelete: (docId: string) => Promise<void> }
//
// Layout: horizontal card with:
//   Left: file-type icon (PDF=red, DOCX=blue, TXT=green coloured icon)
//   Middle: filename (truncated > 30 chars; title tooltip with full name)
//           status badge + relative timestamp
//   Right: delete icon button (trash icon, disabled when status is UPLOADING/PARSING/CHUNKING/EMBEDDING/INDEXING)
//
// Status badges:
//   READY     → green pill "Ready"
//   UPLOADING/PARSING/CHUNKING/EMBEDDING/INDEXING → yellow pill "Processing" + spinner
//   FAILED    → red pill "Failed" + error_message shown below filename
//
// Click delete → open <DeleteConfirmDialog>
```

**`DeleteConfirmDialog.tsx` spec:**

```tsx
// Props: { filename: string; onConfirm: () => Promise<void>; onCancel: () => void; open: boolean }
//
// Modal overlay (focus-trapped when open):
//   "Delete {filename}?"
//   "This will remove it from the current session and it cannot be undone."
//   [Cancel] [Delete] buttons
//   Delete button shows spinner while onConfirm() is in-flight
//   On success: modal closes; DocumentCard fades out
```

**Acceptance criteria:**
- [ ] Panel shows "Documents (0 / 10)" with empty state on a fresh session
- [ ] After upload, card appears with correct filename, file-type icon, status badge
- [ ] PROCESSING document's delete button is disabled
- [ ] Clicking delete opens confirmation modal; Cancel closes it without deleting
- [ ] Confirming delete removes card from panel; counter decrements
- [ ] Panel collapses to 48 px icon strip; state preserved across navigation via `localStorage`
- [ ] Filename > 30 chars is truncated with ellipsis; full name appears in tooltip

---

### T07 — Chat API Module & `useChat` Hook

**What it delivers:** All chat API calls and the `useChat` hook managing the message thread state, query dispatch, SSE token streaming, and history clear.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/api/chat.ts` | All chat API functions |
| `frontend/src/hooks/useChat.ts` | Chat state management |

**`api/chat.ts` spec:**

```typescript
export async function sendQuery(
  sessionId: string,
  query: string,
): Promise<QueryInitResponse> {
  return apiFetch<QueryInitResponse>('/api/chat/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, query, include_history: true }),
  });
}

export function openChatStream(messageId: string): EventSource {
  return new EventSource(
    `${import.meta.env.VITE_API_BASE_URL ?? ''}/api/chat/stream/${messageId}`
  );
}

export async function getHistory(sessionId: string): Promise<ChatHistoryResponse> {
  return apiFetch<ChatHistoryResponse>(`/api/chat/history/${sessionId}`);
}

export async function clearHistory(sessionId: string): Promise<void> {
  await apiFetch(`/api/chat/history/${sessionId}`, { method: 'DELETE' });
}
```

**`useChat` hook spec:**

```typescript
export function useChat(sessionId: string, hasReadyDocument: boolean): {
  messages: Message[];
  streamingContent: string;       // partial content while streaming
  queryInFlight: boolean;
  sendMessage: (query: string) => Promise<void>;
  clearMessages: () => Promise<void>;
}
```

- On mount: calls `getHistory(sessionId)` and hydrates `messages` state
- `sendMessage(query)`:
  1. Set `queryInFlight = true`; add user message optimistically
  2. Add placeholder assistant message with empty `content` and `streaming: true` flag
  3. Call `sendQuery(sessionId, query)` → get `message_id`
  4. Open `openChatStream(message_id)`:
     - On `token` event: append `delta` to `streamingContent` state
     - On `done` event: replace placeholder with final `Message`; close stream; `queryInFlight = false`
     - On `error` event: replace placeholder with error message; close stream; `queryInFlight = false`
  5. Any `ApiError` thrown: replace placeholder with error bubble content
- `clearMessages()`: calls `clearHistory(sessionId)`; resets `messages` to `[]`
- Auto-scroll: hook sets a `shouldScrollRef` flag on each new message; consumed by `MessageThread`

**Acceptance criteria:**
- [ ] `sendMessage('test')` → user message appears in thread immediately; typing indicator shows
- [ ] SSE `token` events → content builds up in real time in assistant bubble
- [ ] SSE `done` event → final message replaces streaming bubble; citations attached
- [ ] SSE `error` event → error bubble rendered; `queryInFlight` resets to `false`
- [ ] `clearMessages()` empties the thread and resets state
- [ ] History is hydrated on mount from `GET /api/chat/history`

---

### T08 — Chat Interface Components

**What it delivers:** The full chat UI: scrollable message thread with auto-scroll, user/assistant bubbles with markdown rendering, typing indicator, input bar with guard messages, and Clear Chat dialog.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/components/chat/ChatPanel.tsx` | Chat panel wrapper |
| `frontend/src/components/chat/MessageThread.tsx` | Scrollable message list |
| `frontend/src/components/chat/MessageBubble.tsx` | Single message with timestamp |
| `frontend/src/components/chat/TypingIndicator.tsx` | Animated ellipsis |
| `frontend/src/components/chat/ChatInput.tsx` | Textarea + send button |
| `frontend/src/components/chat/ClearChatDialog.tsx` | Confirmation modal |

**`ChatPanel.tsx` spec:**

```tsx
// Props: { sessionId: string; hasReadyDocument: boolean }
// Uses useChat(sessionId, hasReadyDocument)
//
// Layout: flex column, full height
//   header: "RAG Chatbot" title + "Clear Chat" button (hidden if messages.length === 0)
//   <MessageThread messages={messages} streamingContent={streamingContent} queryInFlight={queryInFlight} />
//   <ChatInput onSend={sendMessage} disabled={queryInFlight} hasReadyDocument={hasReadyDocument} />
//
// "Clear Chat" click → opens <ClearChatDialog>
```

**`MessageThread.tsx` spec:**

```tsx
// Props: { messages: Message[]; streamingContent: string; queryInFlight: boolean }
//
// Renders messages.map(msg => <MessageBubble key={msg.message_id} message={msg} />)
// If queryInFlight: append <TypingIndicator> after last message
//   (or show streaming assistant bubble if streamingContent is non-empty)
//
// Auto-scroll: useEffect watching messages.length and streamingContent
//   calls containerRef.current.scrollTop = containerRef.current.scrollHeight
//   only if user is near bottom (within 150px) — do not hijack scroll if user is reading up
//
// Empty state (messages.length === 0):
//   Centered: bot icon + "Ask a question about your uploaded documents."
```

**`MessageBubble.tsx` spec:**

```tsx
// Props: { message: Message; isStreaming?: boolean; streamingContent?: string }
//
// User messages (role === 'user'):
//   Right-aligned; background: var(--color-user-bubble)
//   Plain text (no markdown)
//
// Assistant messages (role === 'assistant'):
//   Left-aligned; background: var(--color-assistant-bubble)
//   Content rendered via <ReactMarkdown remarkPlugins={[remarkGfm]}>
//   If isStreaming: render streamingContent with a blinking cursor "▍"
//
// Below each bubble:
//   - Timestamp: formatRelativeTime(message.created_at), muted small font
//   - For assistant messages only: <CitationSection retrieved_chunks={message.retrieved_chunks} is_refusal={message.is_refusal} />
//
// Error bubble (content starts with "__ERROR__"):
//   Red-tinted background; message text + "Try again" link that re-emits same query
```

**`TypingIndicator.tsx` spec:**

```tsx
// Renders assistant bubble shell with animated ellipsis:
//   Three dots that fade in/out sequentially via CSS keyframes
// No content or citations
```

**`ChatInput.tsx` spec:**

```tsx
// Props: { onSend: (query: string) => void; disabled: boolean; hasReadyDocument: boolean }
//
// <textarea>:
//   placeholder: "Ask a question about your documents..."
//   Enter key → calls handleSend() (if not disabled)
//   Shift+Enter → inserts newline (do NOT submit)
//   Auto-grows in height up to 5 lines; resets to 1 line after submit
//
// Send button:
//   Disabled when: input empty/whitespace OR disabled prop is true OR !hasReadyDocument
//   Shows spinner icon when disabled due to query in-flight
//
// Guard message (shown above input bar when !hasReadyDocument):
//   "Upload a document first to start asking questions."
//   Auto-hides once hasReadyDocument becomes true
```

**`ClearChatDialog.tsx` spec:**

```tsx
// Props: { onConfirm: () => Promise<void>; onCancel: () => void; open: boolean }
// Modal: "Clear conversation?"
//         "Your uploaded documents will not be affected."
//         [Cancel] [Clear] — Clear shows spinner while in-flight
```

**Acceptance criteria:**
- [ ] User message appears right-aligned; assistant message left-aligned
- [ ] Markdown in assistant responses renders correctly (bold, code, lists)
- [ ] Typing indicator appears while `queryInFlight === true`
- [ ] Streaming content builds token by token in the assistant bubble with cursor
- [ ] Enter submits; Shift+Enter inserts newline
- [ ] Send button disabled when input is empty
- [ ] Guard message visible when no READY document; auto-hides when first document is READY
- [ ] Auto-scroll follows new messages unless user has scrolled up
- [ ] Clear Chat button opens dialog; confirm clears thread; cancel dismisses dialog

---

### T09 — Citation Components

**What it delivers:** The Source Citation UI: collapsible "Sources (N)" section below non-refusal assistant bubbles, one Citation Card per retrieved chunk, with verbatim excerpt and Show More toggle.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/components/citations/CitationSection.tsx` | Collapsible section container |
| `frontend/src/components/citations/CitationCard.tsx` | Single source card |

**`CitationSection.tsx` spec:**

```tsx
// Props: { retrieved_chunks: Citation[] | null; is_refusal: boolean | null }
//
// Render nothing if is_refusal === true OR !retrieved_chunks || retrieved_chunks.length === 0
//
// Collapsed by default:
//   Header button: "Sources ({N})" + chevron-down icon
//   Click toggles expanded/collapsed
//
// When expanded:
//   One <CitationCard> per item in retrieved_chunks (preserve order — most relevant first)
//
// Visual separator: 1px border-top between answer body and citation section
// Typography: smaller font (0.8rem), secondary colour
```

**`CitationCard.tsx` spec:**

```tsx
// Props: { citation: Citation }
//
// Header: "📄 {filename} — page {page_number ?? 'N/A'} — chunk {chunk_index + 1}"
//         (page_number ≤ 0 or null → display 'N/A')
//
// Body: verbatim excerpt text in a grey card / blockquote
//   If excerpt.length > 800 chars:
//     Show first 800 chars + "… Show more" link
//     Click "Show more" → reveal full text; link changes to "Show less"
//   Full excerpt always available (no permanent truncation)
//
// Defensive rendering:
//   If citation.excerpt is empty/null: render "[Excerpt unavailable]" in italic
//   Frontend-only warning logged to console: CITATION_DATA_MISSING
```

**Acceptance criteria:**
- [ ] Citation section hidden when `is_refusal === true`
- [ ] Citation section hidden when `retrieved_chunks` is empty or null
- [ ] "Sources (3)" label shows correct count
- [ ] Clicking header toggles expand/collapse
- [ ] Each Citation Card shows filename, page (or N/A), chunk number, and excerpt text
- [ ] Excerpts > 800 chars show truncated text with "Show more" toggle
- [ ] `page_number = null` renders as "N/A" (not "null" or "0")

---

### T10 — Feedback Components (Toast & Network Banner)

**What it delivers:** The global feedback layer: toast notification system and persistent network error banner. Wired to `useToast` hook consumed by all other components.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/hooks/useToast.ts` | Toast queue management |
| `frontend/src/components/feedback/Toast.tsx` | Single toast component |
| `frontend/src/components/feedback/ToastContainer.tsx` | Fixed-position toast stack |
| `frontend/src/components/feedback/NetworkBanner.tsx` | Persistent network error bar |

**`useToast` hook spec:**

```typescript
type ToastVariant = 'info' | 'success' | 'error';

export interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
  persist: boolean;        // if true: requires manual dismiss; if false: auto-dismiss in 5s
}

export function useToast(): {
  toasts: ToastItem[];
  addToast: (message: string, variant: ToastVariant, persist?: boolean) => void;
  dismissToast: (id: string) => void;
}
// addToast generates a uuid id; if persist===false, schedules setTimeout to call dismissToast after 5000ms
```

**`ToastContainer.tsx` spec:**

```tsx
// Fixed position: top-right, z-index 9999, 16px margin
// Stacks toasts vertically (newest on top)
// Each <Toast> slides in from right (CSS transition)
// Dismiss button (✕) on each toast; error toasts without persist=false show it prominently
```

**`NetworkBanner.tsx` spec:**

```tsx
// Props: { visible: boolean; onRetry: () => void }
// Renders a sticky banner at top of viewport when visible:
//   "Connection lost. Check your network." + [Retry] button
// background: var(--color-error); full-width
// Hides when visible === false
```

**Network error detection integration:**
- `apiFetch()` in `client.ts` already throws `ApiError(0, 'NETWORK_ERROR', ...)` on network failure
- Each hook (`useDocuments`, `useChat`) catches `NETWORK_ERROR` and calls a `onNetworkError` callback
- `App.tsx` manages `networkError: boolean` state and passes to `NetworkBanner`

**Acceptance criteria:**
- [ ] `addToast('message', 'info')` → toast appears in top-right; auto-dismisses after 5s
- [ ] `addToast('error', 'error', true)` → toast persists until user clicks ✕
- [ ] Multiple toasts stack vertically
- [ ] Network error → `NetworkBanner` visible; Retry triggers callback; banner hides on success
- [ ] Toast slides in from right on appearance

---

### T11 — Integration & Wiring

**What it delivers:** All components wired together in `App.tsx` with proper prop flow, the `ToastContext` provider for cross-component toast dispatch, and verification that the full user journey works end-to-end.

**Files:**

| File | Content |
|------|---------|
| `frontend/src/App.tsx` | Finalised root: session init + full layout + context providers |

**`App.tsx` final structure:**

```tsx
// ToastContext provides addToast to all components
// NetworkError state managed here; passed to NetworkBanner
//
// Render tree:
//   <ToastProvider>
//     <NetworkBanner visible={networkError} onRetry={retryLastCall} />
//     <ToastContainer />
//     {loading && <LoadingScreen />}
//     {error && <ErrorScreen message={error} />}
//     {sessionId && <AppLayout sessionId={sessionId} />}
//   </ToastProvider>
```

**Full data flow:**

```
App.tsx
  ├── useSession → sessionId
  ├── AppLayout(sessionId)
  │   ├── DocumentPanel(sessionId)
  │   │   └── useDocuments(sessionId)
  │   │       ├── UploadZone → uploadFile()
  │   │       └── DocumentCard[] → deleteDocument()
  │   └── ChatPanel(sessionId, hasReadyDocument)
  │       └── useChat(sessionId, hasReadyDocument)
  │           ├── MessageThread
  │           │   └── MessageBubble → CitationSection → CitationCard[]
  │           ├── TypingIndicator (when queryInFlight)
  │           └── ChatInput → sendMessage()
  └── ToastContainer (floating, top-right)
```

**`hasReadyDocument` derivation:**
```typescript
// In AppLayout or DocumentPanel: computed from useDocuments state
const hasReadyDocument = documents.some(d => d.status === 'READY');
// Passed down to ChatPanel → ChatInput (disables send when false)
```

**Acceptance criteria:**
- [ ] Full E2E journey works: upload PDF → wait for READY → type question → stream answer → see citations
- [ ] Error on upload → inline error in UploadZone; no toast
- [ ] LLM error → error bubble in chat thread + toast in top-right
- [ ] Network error during any call → NetworkBanner visible; Retry re-fires request
- [ ] Delete document → card removed; if last READY doc deleted, ChatInput guard message reappears
- [ ] Clear chat → thread emptied; documents unaffected
- [ ] Refresh page → new session; previous chat gone (by design)

---

## Task Dependency Graph

```
Wave 1: T01 (scaffold + types + API client)
         │
Wave 2: T02 (session hook) ─── T03 (layout shell)
         │                          │
Wave 3: T04 (documents API + hook)  │
         │                          │
Wave 4: T05 (upload zone) ──── T06 (doc panel)
         │                          │
         └────────── T07 (chat API + hook)
                          │
Wave 5:             T08 (chat UI components)
                          │
Wave 6:             T09 (citation components)
                          │
                    T10 (toast + network banner)
                          │
Wave 7:             T11 (integration wiring + E2E)
```

**Dependency notes:**
- T01 has no dependencies — all subsequent tasks import from `api/client.ts` and `types/api.ts`
- T02 and T03 both depend on T01; they can be implemented in parallel
- T04 depends on T01 (api client, types); T05 and T06 both depend on T04
- T07 depends on T01; T08 depends on T07
- T09 depends on T07 (Citation type from message response)
- T10 depends on T01 (ApiError type from client)
- T11 depends on all previous tasks; it is the integration task

---

## Phase Success Criteria

All of the following must be TRUE before Phase 2 is considered complete:

1. **Upload journey:** A user opens the app in a browser, drags a PDF onto the upload zone, watches the progress bar advance through `UPLOADING → PARSING → CHUNKING → EMBEDDING → INDEXING → READY`, and sees the document appear with a green "Ready" badge in the Document Panel — all within 30 seconds for a 50-page PDF.

2. **Q&A with streaming:** After uploading a document, the user types a question whose answer appears in the document, presses Enter, sees the typing indicator, and reads a streaming assistant response that builds token by token — the correct answer is returned without referencing external knowledge.

3. **Citations visible:** Every non-refusal assistant response shows a collapsed "Sources (N)" section; clicking it reveals at least one Citation Card with the source filename, page reference, and a verbatim excerpt from the document.

4. **Grounding enforced in UI:** When the user asks a question that cannot be answered from the uploaded documents, the assistant responds with a clear refusal message and no citation section is shown.

5. **Document management:** The user can click the delete icon on a document, confirm the dialog, and see the document card disappear from the panel with a fade-out — and a subsequent question that relied on that document now returns a refusal or sources from remaining documents only.

6. **Chat history:** The user can scroll back through all prior Q&A exchanges in the session thread; clicking "Clear Chat" empties the thread without removing any uploaded documents.

7. **Error handling:** All error states surface human-readable messages:
   - Unsupported file → inline error in upload zone (no API call made)
   - File too large → inline error in upload zone (no API call made)
   - LLM unavailable → error bubble in chat thread + auto-dismissing toast
   - Network failure → persistent network banner with Retry button
   - No blank screens, no silent failures, no raw HTTP codes visible
