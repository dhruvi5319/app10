# User Stories: RAG Chatbot

**Project:** RAGChatbot  
**Version:** 1.0  
**Date:** 2026-05-13  
**Status:** Draft  
**Based on:** PRD-RAGChatbot.md v1.0 · FRD-RAGChatbot.md v1.0 · PERSONAS-RAGChatbot.md v1.0

---

## Personas

| ID | Name | Role |
|---|---|---|
| PER-01 | Maya Patel | Research Analyst |
| PER-02 | Daniel Torres | Legal & Contracts Professional |
| PER-03 | Jordan Kim | Technical Knowledge Worker |

---

## Priority Definitions

| Priority | Label | Meaning |
|---|---|---|
| **P0** | Critical — MVP Blocker | Must ship; product does not function without this |
| **P1** | High — MVP Completer | Required for a complete, usable v1 product |
| **P2** | Medium — Post-MVP | High-value enhancement targeted for v1.1 |
| **P3** | Low — Backlog | Convenience feature; not on MVP critical path |

---

## Epic 0: Document Upload & Ingestion (F0)

*Users upload PDF, TXT, and DOCX files via drag-and-drop or file picker. The backend parses, chunks, embeds, and indexes them asynchronously. No chat functionality is available until at least one document is ready.*

---

### US-0.1: Drag-and-Drop File Upload
**As a** Maya Patel (Research Analyst), **I want to** drag document files directly onto the upload area, **so that** I can start indexing research papers quickly without navigating a file picker.

**Acceptance Criteria:**
- [ ] An upload drop zone is visible on the main page at all times
- [ ] Dragging a file over the drop zone highlights the zone with a visual accent border and tinted background
- [ ] Dragging off the window or releasing outside the zone returns the drop zone to its default state
- [ ] Dropping a valid file (PDF, TXT, DOCX) begins the upload immediately and shows a per-file upload card with filename, size, and an uploading spinner
- [ ] Dropping an unsupported file type shows an inline error below the drop zone without submitting the file
- [ ] Multiple files can be dropped simultaneously (up to 20 per session)
- [ ] A file picker fallback (`<input type="file">`) is available for users who cannot drag-and-drop

**Priority:** P0 | **Feature Ref:** F0

---

### US-0.2: File Validation and Size Limits
**As a** Daniel Torres (Legal & Contracts Professional), **I want to** receive immediate, clear feedback if a file I upload is invalid or too large, **so that** I know exactly why a document was rejected and how to fix it.

**Acceptance Criteria:**
- [ ] Files with extensions other than `.pdf`, `.txt`, or `.docx` (case-insensitive) are rejected client-side with the message "Supported formats: PDF, TXT, DOCX" before any upload begins
- [ ] Files exceeding 50 MB are rejected with the message "File must be under 50MB"
- [ ] If the session's cumulative upload size would exceed 200 MB, the upload is rejected with "Session storage limit of 200MB reached"
- [ ] If adding the file would exceed 20 documents in the session, the upload is rejected with "Maximum 20 documents per session"
- [ ] Empty files (0 bytes) are rejected with "Uploaded file contains no data"
- [ ] Rejection of one file in a batch does not prevent other valid files in the same drop from uploading
- [ ] Each rejected file displays its specific error reason in the per-file upload card

**Priority:** P0 | **Feature Ref:** F0

---

### US-0.3: Asynchronous Ingestion Status Tracking
**As a** Jordan Kim (Technical Knowledge Worker), **I want to** see real-time status updates as my document is being parsed and indexed, **so that** I know exactly when it is ready to query and can identify failures immediately.

**Acceptance Criteria:**
- [ ] After upload acceptance, the document card shows status `uploading`, then transitions to `indexing`, then to `ready` or `error` as processing completes
- [ ] The frontend polls the status endpoint every 2 seconds and updates the card without requiring a page refresh
- [ ] When status reaches `ready`, the document card displays a green checkmark and the chat input becomes enabled
- [ ] When status reaches `error`, the document card displays a red error badge with the specific failure reason (e.g., "Could not extract text from this file" for a corrupt PDF, or "PDF appears to be image-only; OCR not supported in v1" for a scanned PDF)
- [ ] An error document card offers a retry-upload affordance
- [ ] The chat input remains disabled until at least one document has `ready` status
- [ ] Processing a 50-page PDF completes (reaches `ready` or `error`) within 30 seconds

**Priority:** P0 | **Feature Ref:** F0

---

## Epic 1: RAG-Powered Question Answering (F1)

*Users ask natural language questions and receive answers generated exclusively from uploaded documents. Answers are streamed in real time; when no relevant content is found, a standardized fallback response is returned instead of a hallucinated answer.*

---

### US-1.1: Submit a Question via Chat Input
**As a** Jordan Kim (Technical Knowledge Worker), **I want to** type a question and submit it with Enter or the Send button, **so that** I can query my documents efficiently using keyboard-first interaction.

**Acceptance Criteria:**
- [ ] A chat input field and Send button are displayed in the main chat area
- [ ] Pressing Enter submits the query; pressing Shift+Enter inserts a newline without submitting
- [ ] Submitting an empty or whitespace-only query shows the inline error "Please enter a question" and does not send a request
- [ ] Queries longer than 2000 characters show the inline error "Question must be under 2000 characters" and cannot be submitted
- [ ] The chat input is disabled and shows "Upload a document to start asking questions" when no document has `ready` status
- [ ] While a query is being processed, the input is disabled and shows a loading state to prevent duplicate submissions
- [ ] The user's message appears in the chat transcript immediately (optimistic) after submission

**Priority:** P0 | **Feature Ref:** F1

---

### US-1.2: Receive a Streamed, Document-Grounded Answer
**As a** Maya Patel (Research Analyst), **I want to** see the answer appear word-by-word as it is generated, **so that** I get fast perceived response times and can start reading while generation completes.

**Acceptance Criteria:**
- [ ] A "thinking" indicator (animated dots) appears in the assistant bubble position immediately after query submission
- [ ] Answer tokens stream progressively into the assistant bubble as they arrive via SSE; the bubble grows as text is added
- [ ] The full answer is rendered in the assistant bubble on completion; the thinking indicator is removed
- [ ] The answer contains only information derived from the uploaded documents — no external knowledge is used
- [ ] The LLM system prompt enforces strict grounding: explicit instruction to answer only from provided excerpts, explicit prohibition on outside knowledge, and explicit instruction to state when information is absent
- [ ] End-to-end answer latency (P95) is under 8 seconds from query submission to complete answer
- [ ] If the LLM stream is interrupted by a network error, an error message appears in the assistant bubble with a retry prompt

**Priority:** P0 | **Feature Ref:** F1

---

### US-1.3: Receive a "Not Found" Fallback Instead of a Hallucinated Answer
**As a** Daniel Torres (Legal & Contracts Professional), **I want to** receive an explicit "not found" response when my uploaded documents don't contain information about my query, **so that** I never act on a fabricated clause or fact.

**Acceptance Criteria:**
- [ ] When no retrieved chunk has a similarity score ≥ 0.30, the system returns the standardized fallback: "The uploaded documents do not contain information about this topic."
- [ ] The fallback response is displayed in the assistant bubble with no citation chips
- [ ] The fallback response is stored in the session chat history like any other assistant message
- [ ] The system never generates a plausible-sounding but unsupported answer when context is absent
- [ ] The `confidence` field on the fallback message is `"low"` and the response is returned as a complete (non-streaming) message

**Priority:** P0 | **Feature Ref:** F1

---

## Epic 2: Source Citations (F2)

*Every assistant answer includes citation chips identifying the source document and passage. Users can expand citations to read the exact source text, building trust and enabling manual verification.*

---

### US-2.1: View Source Citations Below Each Answer
**As a** Maya Patel (Research Analyst), **I want to** see citation chips beneath each answer showing which document it came from, **so that** I can verify the source of every fact before including it in a client deliverable.

**Acceptance Criteria:**
- [ ] After the `done` event is received, one or more citation chips appear below the completed answer bubble
- [ ] Each citation chip displays the source document name (truncated to 30 characters with ellipsis if longer) and the page reference where available (e.g., "contract.pdf — p. 4")
- [ ] For TXT files or when page extraction is unsupported, page number is omitted from the chip label
- [ ] Multiple citation chips are displayed when the answer draws from multiple passages
- [ ] Citation chips are visually distinct from the answer text (muted/secondary styling)
- [ ] No citation chips are rendered for fallback (low-confidence) responses

**Priority:** P0 | **Feature Ref:** F2

---

### US-2.2: Expand a Citation to Read the Source Passage
**As a** Daniel Torres (Legal & Contracts Professional), **I want to** click a citation chip and read the exact verbatim passage that was used to generate the answer, **so that** I can confirm the answer is accurately grounded in the contract language.

**Acceptance Criteria:**
- [ ] Clicking a citation chip expands an inline citation panel below the chip showing the full `chunk_text` in a visually distinct read-only area (blockquote or bordered card)
- [ ] Clicking the same chip again (or a close button within the panel) collapses the citation panel
- [ ] Only one citation panel may be expanded at a time per message; expanding a new one collapses any previously open panel
- [ ] The citation panel is read-only — no editing affordance is provided on the source text
- [ ] The citation panel is accessible by keyboard (Enter/Space to toggle on focused chip)

**Priority:** P0 | **Feature Ref:** F2

---

### US-2.3: Trust Citation Accuracy
**As a** Jordan Kim (Technical Knowledge Worker), **I want to** trust that cited passages exactly match what the model used to generate the answer, **so that** I can rely on citations to verify technical specs without re-reading the source document.

**Acceptance Criteria:**
- [ ] Each citation's `chunk_text` is the verbatim text from the vector index entry used in the LLM prompt — no paraphrasing or modification
- [ ] The `document_name` in each citation matches the original uploaded filename exactly
- [ ] `similarity` scores in citations are floats in [0.0, 1.0]; only chunks above the session's confidence threshold appear as citations
- [ ] A maximum of 10 citations may appear per answer; if more than 10 qualifying chunks exist, the top 10 by similarity score are used
- [ ] If a chunk's `chunk_text` is empty, that citation is silently omitted from the array (backend logs a warning)

**Priority:** P0 | **Feature Ref:** F2

---

## Epic 3: Document Library Management (F3)

*Users can view all documents in their session, track ingestion status, and delete documents. Deletion removes the document from the vector index immediately, ensuring it cannot influence future answers.*

---

### US-3.1: View and Track All Session Documents
**As a** Maya Patel (Research Analyst), **I want to** see all my uploaded documents in a library panel with their ingestion status, **so that** I can confirm which documents are ready to query before starting my research session.

**Acceptance Criteria:**
- [ ] A document library sidebar/panel is visible in the main layout at all times
- [ ] Each document is shown as a card with: filename, file type icon (visually distinct per type), human-readable size, and a status badge
- [ ] Status badge colors convey state: gray for `uploading`, animated blue for `indexing`, green for `ready`, red for `error`
- [ ] Status badges include a text label ("Ready", "Indexing", "Error") and do not rely on color alone for meaning
- [ ] The library shows a document count and total storage summary (e.g., "3 documents · 4.2 MB")
- [ ] Status refreshes automatically via polling (every 3 seconds while any document is `uploading` or `indexing`) without requiring a page reload
- [ ] When no documents are uploaded, the library shows an empty state with a call-to-action to upload documents

**Priority:** P1 | **Feature Ref:** F3

---

### US-3.2: Delete a Document from the Session
**As a** Daniel Torres (Legal & Contracts Professional), **I want to** delete a superseded contract document from my session, **so that** it can no longer influence answers and my session context stays accurate.

**Acceptance Criteria:**
- [ ] Each document card has a delete (trash icon) button
- [ ] Clicking the delete button shows a confirmation prompt: "Delete [filename]? This will remove it from the document index." with Cancel and Delete buttons
- [ ] Clicking Cancel closes the prompt with no action taken
- [ ] Clicking Delete sends the delete request; the button is disabled and shows a spinner while the request is in progress
- [ ] On successful deletion (204 response), the document card is removed from the library and the document count updates immediately
- [ ] Vector index purge is synchronous: the backend removes all chunks for the deleted document before returning 204, ensuring no future answers can reference it
- [ ] Deleting a document in `uploading` or `indexing` state is permitted; the in-progress background task is cancelled
- [ ] If the deleted document was the last `ready` document, the chat input is disabled and a prompt to upload documents is shown
- [ ] On delete failure, a red inline error appears on the document card: "Delete failed. Try again."

**Priority:** P1 | **Feature Ref:** F3

---

## Epic 4: Session-Scoped Chat History (F4)

*All questions and answers within a session are preserved as a scrollable transcript. Users can clear the chat or start a new session. History is not persisted across browser sessions (v1 scope).*

---

### US-4.1: View and Scroll Through Chat History
**As a** Jordan Kim (Technical Knowledge Worker), **I want to** scroll back through earlier questions and answers in the current session, **so that** I can review previous findings without re-asking the same questions.

**Acceptance Criteria:**
- [ ] The chat view displays the full session transcript in a vertically scrollable container in ascending chronological order
- [ ] User messages are right-aligned in a distinct bubble style; assistant messages are left-aligned with a bot icon
- [ ] Each message displays a relative timestamp (e.g., "just now", "2 min ago") that shows the absolute ISO time on hover
- [ ] The view auto-scrolls to the latest message when a new message is appended, but only if the user was already at (or within 100px of) the bottom — manual scroll position is preserved if the user is reading history
- [ ] Chat history is restored from the server on page reconnect within the same session lifetime
- [ ] When no messages exist, an onboarding empty state is displayed prompting the user to upload a document and ask a question

**Priority:** P1 | **Feature Ref:** F4

---

### US-4.2: Clear Chat History
**As a** Maya Patel (Research Analyst), **I want to** clear the chat transcript while keeping my uploaded documents, **so that** I can start a fresh set of questions about the same document set without re-uploading.

**Acceptance Criteria:**
- [ ] A "Clear Chat" button is available in the chat interface
- [ ] Clicking "Clear Chat" shows a confirmation: "Clear conversation? Documents remain uploaded." with Cancel and Clear buttons
- [ ] Clicking Cancel closes the confirmation with no action
- [ ] Clicking Clear sends `DELETE /api/chat/history`; on 204 success, the chat view is cleared and the empty state is shown
- [ ] All uploaded documents and their vector index entries remain intact after clearing chat
- [ ] The document library is unchanged after a Clear Chat action

**Priority:** P1 | **Feature Ref:** F4

---

### US-4.3: Start a New Session
**As a** Jordan Kim (Technical Knowledge Worker), **I want to** start a completely fresh session that clears both documents and chat history, **so that** I can begin an entirely new research task without stale context.

**Acceptance Criteria:**
- [ ] A "New Session" action is available and visually distinct from "Clear Chat"
- [ ] Clicking "New Session" shows a confirmation: "Start a new session? All documents and chat history will be cleared."
- [ ] Clicking Cancel closes the confirmation with no action
- [ ] Clicking confirm sends `POST /api/session/reset`; on success, the entire document library and chat transcript are cleared, a new session cookie is set, and the onboarding empty state is displayed
- [ ] The vector index for the old session is fully purged on the server before the new session is created

**Priority:** P1 | **Feature Ref:** F4

---

## Epic 5: Premium Responsive UI (F5)

*The React frontend is polished, accessible, and fully responsive from mobile to desktop. The layout, animations, and interaction patterns meet WCAG 2.1 AA standards and feel premium across all supported viewports.*

---

### US-5.1: Use the Application Across All Device Sizes
**As a** Maya Patel (Research Analyst), **I want to** use the chatbot on my laptop or a tablet without any layout issues, **so that** I can work flexibly across devices.

**Acceptance Criteria:**
- [ ] On desktop (≥ 1024px): a persistent sidebar (~280px) shows the document library; the main chat area occupies the remaining width; both scroll independently
- [ ] On tablet (768px–1023px): the sidebar collapses to an icon strip; tapping the document icon expands a full-height drawer overlay
- [ ] On mobile (< 768px): single-column layout with the document library accessible via a bottom sheet or top tab; chat takes full screen width
- [ ] No horizontal overflow or layout breakage at 320px, 768px, 1024px, or 1440px viewport widths
- [ ] Upload progress, document cards, and chat bubbles render correctly at all breakpoints
- [ ] Skeleton loaders appear within 100ms of a network request start; no blank screen flash
- [ ] All animations respect the `prefers-reduced-motion` media query — all animations are disabled when motion reduction is preferred

**Priority:** P1 | **Feature Ref:** F5

---

### US-5.2: Navigate and Use the Application Entirely by Keyboard
**As a** Jordan Kim (Technical Knowledge Worker), **I want to** navigate and interact with the application using only the keyboard, **so that** I can work at full speed without reaching for the mouse.

**Acceptance Criteria:**
- [ ] Tab order follows a logical flow: Upload zone → Document library items → Chat input → Send button → Clear Chat → New Session
- [ ] Pressing Enter on the upload zone opens the file picker
- [ ] Pressing Enter in the chat input submits the query; Shift+Enter inserts a newline
- [ ] Pressing Escape closes open modals, citation panels, and drawer overlays
- [ ] All interactive elements (buttons, chips, inputs) have a visible focus ring
- [ ] Icon-only buttons (trash, copy, thumbs) have `aria-label` attributes providing an accessible name
- [ ] All color pairs meet WCAG AA contrast ratios (≥ 4.5:1 for normal text, ≥ 3:1 for large text)
- [ ] Dynamic content updates (new messages, status changes) are announced via `aria-live="polite"` ARIA live regions
- [ ] An automated axe-core audit returns zero WCAG AA violations

**Priority:** P1 | **Feature Ref:** F5

---

## Epic 6: Multi-Document Context Retrieval (F6)

*When multiple documents are uploaded, retrieval searches all of them simultaneously. Citations identify which document each passage came from. An optional document filter restricts a query to a specific document.*

---

### US-6.1: Ask Questions Across All Uploaded Documents Simultaneously
**As a** Maya Patel (Research Analyst), **I want to** ask a question and get an answer that draws from all my uploaded research reports at once, **so that** I can find cross-document insights without issuing separate queries per document.

**Acceptance Criteria:**
- [ ] When multiple documents are `ready`, a query searches the full session vector index spanning all documents by default — no user configuration required
- [ ] The citations on the answer clearly identify which document each passage originated from (via `document_name` and `document_id`)
- [ ] When citations reference 2 or more distinct documents, a "From N documents" label is displayed above the citation chips
- [ ] The ranking of retrieved chunks is purely by cosine similarity — no document-level bias is applied
- [ ] With only one document in the session, behavior is identical to single-document retrieval

**Priority:** P2 | **Feature Ref:** F6

---

### US-6.2: Filter a Query to a Specific Document
**As a** Daniel Torres (Legal & Contracts Professional), **I want to** optionally restrict my question to a specific contract document, **so that** I can interrogate one agreement in isolation without results from other uploaded contracts interfering.

**Acceptance Criteria:**
- [ ] A document filter control (dropdown or chip selector) is available above the chat input listing all `ready` documents
- [ ] Selecting a document sets an active filter; subsequent queries retrieve chunks only from that document
- [ ] A visual indicator in the chat input area shows when a filter is active (e.g., "Searching: contract.pdf")
- [ ] Clearing the filter returns to full cross-document retrieval
- [ ] If the filtered document has no indexed content, the system returns an error: "Document has no indexed content"
- [ ] If the specified document is not yet `ready`, the system returns: "Document is still being indexed; please wait"

**Priority:** P2 | **Feature Ref:** F6

---

## Epic 7: Answer Confidence & Relevance Feedback (F7)

*The system surfaces a confidence signal on each answer and allows users to rate answers with thumbs-up or thumbs-down. These signals help users decide whether to trust an answer or rephrase their question.*

---

### US-7.1: See a Confidence Signal on Each Answer
**As a** Daniel Torres (Legal & Contracts Professional), **I want to** see a confidence indicator alongside each answer, **so that** I know when to trust the response versus when to manually verify or rephrase my question.

**Acceptance Criteria:**
- [ ] Answers where the top retrieved chunk has similarity ≥ 0.60 display a subtle green "High confidence" badge
- [ ] Answers where the top retrieved chunk has similarity ≥ 0.30 but < 0.60 display an amber "Low confidence" badge
- [ ] Low-confidence answers also display an inline rephrasing suggestion: "Try rephrasing your question or uploading additional documents."
- [ ] Fallback responses (all chunks below 0.30) display no confidence badge; the answer text itself conveys the "not found" message
- [ ] Confidence badges are stored with the message and visible in chat history

**Priority:** P2 | **Feature Ref:** F7

---

### US-7.2: Rate an Answer with Thumbs Up or Down
**As a** Maya Patel (Research Analyst), **I want to** give a thumbs-up or thumbs-down on an answer, **so that** I can signal quality issues for future review and improvement.

**Acceptance Criteria:**
- [ ] Thumbs-up and thumbs-down icon buttons appear on each assistant message on hover or keyboard focus
- [ ] Clicking thumbs-up or thumbs-down submits feedback (`POST /api/chat/feedback` with `rating: "positive"` or `"negative"`)
- [ ] After submission, the selected icon displays a filled/active state; the unselected icon is hidden
- [ ] Feedback buttons become disabled after submission — ratings cannot be changed in v1
- [ ] Feedback can only be submitted once per message; a second attempt returns a 409 error (not surfaced to the user as a hard error)
- [ ] Feedback submission does not alter or re-generate the answer

**Priority:** P2 | **Feature Ref:** F7

---

## Epic 8: Export & Copy Utilities (F8)

*Users can copy individual answers or citation text to the clipboard, and export the full chat transcript as a plain text or Markdown file. These utilities support workflows that continue beyond the app.*

---

### US-8.1: Copy an Answer to the Clipboard
**As a** Maya Patel (Research Analyst), **I want to** copy an assistant answer with one click, **so that** I can paste it directly into a client deliverable draft without reformatting.

**Acceptance Criteria:**
- [ ] A copy icon button appears on each assistant message bubble on hover or keyboard focus
- [ ] Clicking the copy icon writes the answer text to the clipboard using the Clipboard API
- [ ] On successful copy, the icon briefly changes to a checkmark and a "Copied!" tooltip appears for 2 seconds
- [ ] If the Clipboard API is unavailable, the frontend falls back to `document.execCommand('copy')` silently; if that also fails, a soft message "Copy unavailable in this browser" is shown — no hard error
- [ ] No server call is made for copying individual answers

**Priority:** P3 | **Feature Ref:** F8

---

### US-8.2: Copy a Source Citation Passage
**As a** Daniel Torres (Legal & Contracts Professional), **I want to** copy the exact verbatim passage from a citation directly to my clipboard, **so that** I can paste the source text into an audit note or summary document.

**Acceptance Criteria:**
- [ ] A copy icon is available within each expanded citation panel header
- [ ] Clicking the icon copies the citation's `chunk_text` to the clipboard
- [ ] On success, the icon briefly changes to a checkmark with a "Copied!" tooltip for 2 seconds
- [ ] Same clipboard fallback behavior as US-8.1 applies

**Priority:** P3 | **Feature Ref:** F8

---

### US-8.3: Export the Full Chat Transcript
**As a** Jordan Kim (Technical Knowledge Worker), **I want to** download the full conversation transcript as a text or Markdown file, **so that** I can share findings with my team or include them in a ticket description.

**Acceptance Criteria:**
- [ ] An "Export Transcript" button is accessible in the chat header or menu
- [ ] Clicking the button presents a format selection: "Plain Text (.txt)" or "Markdown (.md)"
- [ ] Selecting a format and clicking Download triggers a file download via `GET /api/chat/export?format=text|markdown`
- [ ] The downloaded file contains all messages in chronological order with timestamps, speaker labels, and formatted citations
- [ ] Citation text in the export is truncated to 500 characters with "..." if longer
- [ ] If the chat history is empty, the export file includes header metadata and the note "No messages in this session."
- [ ] Invalid format parameter values return 400 `INVALID_EXPORT_FORMAT`

**Priority:** P3 | **Feature Ref:** F8

---

## Story Index

| Story ID | Title | Persona | Priority | Feature Ref |
|---|---|---|---|---|
| US-0.1 | Drag-and-Drop File Upload | Maya Patel | P0 | F0 |
| US-0.2 | File Validation and Size Limits | Daniel Torres | P0 | F0 |
| US-0.3 | Asynchronous Ingestion Status Tracking | Jordan Kim | P0 | F0 |
| US-1.1 | Submit a Question via Chat Input | Jordan Kim | P0 | F1 |
| US-1.2 | Receive a Streamed, Document-Grounded Answer | Maya Patel | P0 | F1 |
| US-1.3 | Receive a "Not Found" Fallback Instead of a Hallucinated Answer | Daniel Torres | P0 | F1 |
| US-2.1 | View Source Citations Below Each Answer | Maya Patel | P0 | F2 |
| US-2.2 | Expand a Citation to Read the Source Passage | Daniel Torres | P0 | F2 |
| US-2.3 | Trust Citation Accuracy | Jordan Kim | P0 | F2 |
| US-3.1 | View and Track All Session Documents | Maya Patel | P1 | F3 |
| US-3.2 | Delete a Document from the Session | Daniel Torres | P1 | F3 |
| US-4.1 | View and Scroll Through Chat History | Jordan Kim | P1 | F4 |
| US-4.2 | Clear Chat History | Maya Patel | P1 | F4 |
| US-4.3 | Start a New Session | Jordan Kim | P1 | F4 |
| US-5.1 | Use the Application Across All Device Sizes | Maya Patel | P1 | F5 |
| US-5.2 | Navigate and Use the Application Entirely by Keyboard | Jordan Kim | P1 | F5 |
| US-6.1 | Ask Questions Across All Uploaded Documents Simultaneously | Maya Patel | P2 | F6 |
| US-6.2 | Filter a Query to a Specific Document | Daniel Torres | P2 | F6 |
| US-7.1 | See a Confidence Signal on Each Answer | Daniel Torres | P2 | F7 |
| US-7.2 | Rate an Answer with Thumbs Up or Down | Maya Patel | P2 | F7 |
| US-8.1 | Copy an Answer to the Clipboard | Maya Patel | P3 | F8 |
| US-8.2 | Copy a Source Citation Passage | Daniel Torres | P3 | F8 |
| US-8.3 | Export the Full Chat Transcript | Jordan Kim | P3 | F8 |

---

## Priority Summary

| Priority | Stories | Feature Coverage |
|---|---|---|
| **P0 — Critical (MVP Blockers)** | US-0.1, US-0.2, US-0.3, US-1.1, US-1.2, US-1.3, US-2.1, US-2.2, US-2.3 | F0, F1, F2 |
| **P1 — High (MVP Completers)** | US-3.1, US-3.2, US-4.1, US-4.2, US-4.3, US-5.1, US-5.2 | F3, F4, F5 |
| **P2 — Medium (Post-MVP v1.1)** | US-6.1, US-6.2, US-7.1, US-7.2 | F6, F7 |
| **P3 — Low (Backlog)** | US-8.1, US-8.2, US-8.3 | F8 |

---

*Document generated: 2026-05-13 | RAGChatbot UserStories v1.0*
