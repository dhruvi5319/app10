---

## F05: Premium Responsive UI

**Priority:** P1 — MVP Completer  
**PRD Reference:** §5 F5

**Description:** The React frontend is designed and implemented to a premium, polished standard — clean layout, smooth animations, accessible color contrast, and full responsiveness from desktop to mobile. The UI must feel professional and delightful without sacrificing usability. This feature defines the frontend UX specifications that cut across all other features and govern how they are rendered.

---

### Terminology

- **Split-Panel Layout:** The two-column desktop layout with the document library on the left and the chat area on the right.
- **Collapsed Sidebar:** On mobile/tablet viewports, the document library collapses into a drawer or tab rather than a persistent panel.
- **Drag-Over State:** Visual feedback applied to the upload drop zone when a file is held over it during a drag operation.
- **Skeleton Loader:** A placeholder UI element (gray animated bar) shown in place of content while data is loading.
- **Focus Ring:** A visible outline around the currently focused interactive element, required for keyboard navigation.
- **WCAG AA:** Web Content Accessibility Guidelines 2.1 Level AA — the minimum accessibility standard required.
- **Onboarding Empty State:** The first-run UI shown when no documents have been uploaded, guiding the user to start.

---

### Sub-Features

- **Layout:** Split-panel (sidebar + main chat) on desktop; collapsible drawer on mobile
- **Upload Zone:** Drag-and-drop area with drag-over highlight, animated border, and descriptive copy
- **Document Library:** Card-based list with status badges, file type icons, size display, delete button
- **Chat Bubbles:** Distinct styles for user (right-aligned, accent color) and assistant (left-aligned, neutral) messages
- **Citation Chips:** Compact pill elements below assistant messages; expandable inline panels
- **Loading States:** Thinking indicator (animated dots or typing animation) during LLM generation; skeleton loaders on initial data fetch
- **Animations:** Smooth message entrance slide-in; citation panel expand/collapse transition; upload progress bar animation
- **Accessibility:** WCAG 2.1 AA contrast ratios; full tab-order keyboard navigation; focus rings on all interactive elements; ARIA labels on icon-only buttons
- **Responsive Layout:** Adapts gracefully at 320px, 768px, 1024px, and 1440px breakpoints
- **Empty States:** Onboarding copy for no-documents state and no-messages state
- **Error States:** Inline error messages styled consistently (red/destructive variant)
- **Color Palette:** Semantic color tokens (primary, secondary, muted, destructive, success, warning)

---

### Process

*This feature describes layout and interaction specifications; it has no server-side process. Frontend rendering processes are described per-interaction below.*

**Page Load:**
1. App shell renders immediately with split-panel layout and skeleton placeholders.
2. Frontend fetches session data (`GET /api/documents`, `GET /api/chat/history`) in parallel.
3. Skeletons replaced with real content on data arrival; smooth fade-in transition.
4. If no documents: onboarding empty state shown in document library and chat area.

**Drag-and-Drop Upload:**
1. User drags file(s) over the drop zone → drop zone border animates to accent color, background tints.
2. User drops files → border returns to default; upload cards appear with progress spinners.
3. If user drags off the window → drop zone returns to default state immediately.

**Responsive Behavior:**
- ≥ 1024px (desktop): Persistent sidebar (left, ~280px) + main chat area (remaining width). Sidebar scrolls independently.
- 768px–1023px (tablet): Sidebar collapses to an icon-strip; tap on document icon expands a full-height drawer overlay.
- < 768px (mobile): Single-column layout. Document library accessible via a bottom sheet or top tab. Chat takes full screen width.

**Keyboard Navigation:**
- Tab order: Upload zone → Document library items → Chat input → Send button → Clear chat → New session.
- Enter on upload zone opens the file picker.
- Enter in chat input submits query (Shift+Enter inserts newline).
- Escape closes open modals, citation panels, and drawer overlays.

**Accessibility Requirements:**
- All color pairs must meet WCAG AA contrast ratio (≥ 4.5:1 for normal text, ≥ 3:1 for large text).
- All interactive elements must have accessible name via visible label or `aria-label`.
- Status badges must not rely on color alone — include text label (e.g., "Ready", "Error").
- Images and icons must have `alt` text or `aria-hidden` if decorative.
- Dynamic content updates (new messages, status changes) must use ARIA live regions (`aria-live="polite"`).

---

### Inputs

*Frontend-only feature; all inputs are user interactions (clicks, drags, keyboard) and API responses from other features.*

---

### Outputs

*Rendered React UI — no API responses produced by this feature directly.*

Key rendered components:
- `<AppLayout>`: Root split-panel layout
- `<DocumentLibrary>`: Sidebar document list with cards and status badges
- `<UploadZone>`: Drag-and-drop upload area
- `<ChatView>`: Scrollable message transcript
- `<MessageBubble>`: Individual user or assistant message
- `<CitationChip>` / `<CitationPanel>`: Citation display components
- `<ChatInput>`: Text input + send button
- `<LoadingIndicator>`: Thinking dots animation
- `<EmptyState>`: Onboarding or cleared-state UI
- `<ConfirmModal>`: Reusable confirmation dialog

---

### Validation Rules

- All breakpoints (320px, 768px, 1024px, 1440px) must be visually tested and free of horizontal overflow.
- No interactive element may be unreachable by keyboard alone.
- All WCAG AA contrast ratios must pass automated axe-core audit with zero violations.
- File type icons must be visually distinct (PDF ≠ TXT ≠ DOCX).
- Upload progress bar must visually complete and transition to "ready" state without a flash of empty state.
- Chat auto-scroll must not hijack manual scroll — see F04 §Validation Rules for scroll logic.
- Animations must respect `prefers-reduced-motion` media query — all animations disabled if user has motion reduction preference set.
- Loading skeletons must appear within 100ms of a network request start (no blank screen flash).

---

### Error States

| Scenario | UI Behavior |
|---|---|
| Network request fails | Inline error banner with "Retry" button; no full-page error screen |
| LLM stream interrupted | Error bubble in chat: "Answer generation failed. Please try again." with retry button |
| Upload rejected (client-side validation) | Red inline error below upload zone: specific reason (e.g., "Only PDF, TXT, and DOCX supported") |
| Delete fails | Red inline error on document card: "Delete failed. Try again." |
| Session expired | Toast notification: "Your session has expired. Starting a new session." — auto-reset |

---

### API Surface (this feature)

No new API endpoints. This feature consumes all endpoints from F00–F04 and F06–F08.

---

### Schema Surface (this feature)

No new schema entities. Frontend state managed in React component state and/or a lightweight state manager (e.g., Zustand or Redux Toolkit).

Frontend state shape (informational):
- `session`: `{ session_id, document_count, total_size_bytes }`
- `documents`: `Document[]` (mirroring server document records)
- `messages`: `Message[]` (mirroring server message records)
- `uiState`: `{ isUploading, isQuerying, sidebarOpen, activeModal, activeCitationPanel }`
