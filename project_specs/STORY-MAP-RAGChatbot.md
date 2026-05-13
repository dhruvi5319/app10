# Story Map: RAG Chatbot

| Field | Value |
|---|---|
| **Product Name** | RAG Chatbot |
| **Project Acronym** | RAGChatbot |
| **Version** | 1.0 |
| **Date** | 2026-05-13 |
| **Related Personas** | PERSONAS-RAGChatbot.md v1.0 |
| **Related JTBD** | JTBD-RAGChatbot.md v1.0 |
| **Related Journeys** | JOURNEYS-RAGChatbot.md v1.0 |
| **Related User Stories** | UserStories-RAGChatbot.md v1.0 |
| **Related PRD** | PRD-RAGChatbot.md v1.0 |
| **Status** | Draft |

---

## Overview

This Story Map organizes the 23 user stories from UserStories-RAGChatbot.md into a two-dimensional grid:

- **X-axis (columns):** The five unified journey stages shared across all six persona journeys (JRN-01.1, JRN-01.2, JRN-02.1, JRN-02.2, JRN-03.1, JRN-03.2).
- **Y-axis (rows):** Stories grouped by persona and epic, placed at the stage where they primarily deliver value.
- **NaC column:** Natural Acceptance Criteria derived from the intersection of a specific JTBD outcome and the journey stage context. NaC are NOT invented — each traces to a named JTBD-ID and the source JTBD hiring criterion or success measure.
- **Release column:** Increment grouping driven by (1) priority tier (P0 → R1, P1 → R2, P2 → R3, P3 → R4) and (2) journey completeness — R1 delivers a minimal but complete end-to-end path through all five stages for all three personas.

### Unified Journey Stages

| Stage # | Stage Name | Description |
|---|---|---|
| **S1** | Arrive & Orient | Land on the app, see empty state, understand the upload CTA |
| **S2** | Upload & Ingest | Drop documents, watch per-document status cycle to Ready |
| **S3** | Query | Type a natural-language question, submit, receive streamed answer |
| **S4** | Verify Citation | Expand citation panel, read verbatim source passage, confirm provenance |
| **S5** | Act & Export | Copy answer + citation, export transcript, manage session state |

### NaC Concept

> A **Natural Acceptance Criterion (NaC)** bridges a JTBD job outcome to a testable behavior by contextualizing it within a specific journey stage:
> `JTBD Outcome → Journey Stage Context → Testable Criterion`
>
> Example: JTBD-01.1 says "Minimize time to find a data point." Placed in the **Query** stage, the NaC becomes: *"Given uploaded documents are Ready, when the user submits a factual question, then a cited answer appears within 8 seconds."*

---

## Story Map Matrix

> **Reading the map:** Stories are organized by persona row within each stage column. The Release column groups stories into delivery increments. NaC in each cell traces to the JTBD derivation table below.

### Stage S1: Arrive & Orient

| SM-ID | Persona | Epic | Story | NaC (derived from JTBD) | Release |
|---|---|---|---|---|---|
| SM-5.1 | PER-01 Maya | Epic 5 (F5) | **US-5.1** — Use the Application Across All Device Sizes | JTBD-01.1 → S1: App loads without layout breakage on Maya's laptop within 100ms skeleton render; empty state makes upload CTA immediately visible | R2 |
| SM-5.2 | PER-03 Jordan | Epic 5 (F5) | **US-5.2** — Navigate and Use the Application Entirely by Keyboard | JTBD-03.3 → S1: All interactive elements are reachable via Tab from page load; focus ring is visible on first Tab press; no mouse required to reach the upload zone | R2 |

> *Note: S1 has minimal dedicated stories — the empty state and initial UI are part of US-5.1 and US-5.2. The Arrive & Orient experience is gated on the responsive/accessible UI being in place.*

---

### Stage S2: Upload & Ingest

| SM-ID | Persona | Epic | Story | NaC (derived from JTBD) | Release |
|---|---|---|---|---|---|
| SM-0.1 | PER-01 Maya | Epic 0 (F0) | **US-0.1** — Drag-and-Drop File Upload | JTBD-01.1 → S2: Given a batch of PDF research reports, when Maya drags them onto the upload zone, then all files begin uploading immediately and show per-file status cards — no file-picker navigation required | R1 |
| SM-0.2 | PER-02 Daniel | Epic 0 (F0) | **US-0.2** — File Validation and Size Limits | JTBD-02.1 → S2: Given a rejected file (wrong format or too large), when Daniel drops it, then a specific inline error appears on that card within 1 second and valid files in the same batch still upload successfully | R1 |
| SM-0.3 | PER-03 Jordan | Epic 0 (F0) | **US-0.3** — Asynchronous Ingestion Status Tracking | JTBD-03.1 → S2: Given a 50-page PDF has been dropped, when ingestion runs, then the status chip transitions Uploading → Indexing → Ready within 30 seconds and the chat input enables on the first Ready document | R1 |
| SM-3.1 | PER-01 Maya | Epic 3 (F3) | **US-3.1** — View and Track All Session Documents | JTBD-01.3 → S2: Given 5 research PDFs are uploading, when Maya checks the document library, then each file shows its own status badge (filename, type, size, state) so she can confirm all 5 are indexed before querying | R2 |
| SM-3.2 | PER-02 Daniel | Epic 3 (F3) | **US-3.2** — Delete a Document from the Session | JTBD-02.3 → S2: Given a superseded contract version is in the library, when Daniel clicks Delete and confirms, then the document card disappears and the vector index purge completes synchronously before the 204 response | R2 |

---

### Stage S3: Query

| SM-ID | Persona | Epic | Story | NaC (derived from JTBD) | Release |
|---|---|---|---|---|---|
| SM-1.1 | PER-03 Jordan | Epic 1 (F1) | **US-1.1** — Submit a Question via Chat Input | JTBD-03.3 → S3: Given the user is on the chat page with a Ready document, when they press Enter after typing a question, then the query submits without any mouse click; Enter-to-submit works on every query in the session | R1 |
| SM-1.2 | PER-01 Maya | Epic 1 (F1) | **US-1.2** — Receive a Streamed, Document-Grounded Answer | JTBD-01.1 → S3: Given uploaded documents are indexed, when Maya submits a factual question, then the answer begins streaming within 8 seconds (P95), contains only information from her uploaded PDFs, and shows a "thinking" indicator during generation | R1 |
| SM-1.3 | PER-02 Daniel | Epic 1 (F1) | **US-1.3** — Receive a "Not Found" Fallback Instead of a Hallucinated Answer | JTBD-02.2 → S3: Given a queried clause does not exist in any uploaded contract, when Daniel submits the question, then the system returns the explicit fallback "The uploaded documents do not contain information about this topic" with no citation chips and no fabricated clause language | R1 |
| SM-6.1 | PER-01 Maya | Epic 6 (F6) | **US-6.1** — Ask Questions Across All Uploaded Documents Simultaneously | JTBD-01.3 → S3: Given 5 reports are Ready, when Maya asks a cross-cutting question, then retrieval searches all 5 simultaneously and the answer cites passages from each contributing document by name, with a "From N documents" label above the citation chips | R3 |
| SM-6.2 | PER-02 Daniel | Epic 6 (F6) | **US-6.2** — Filter a Query to a Specific Document | JTBD-02.3 → S3: Given 3 contracts are loaded, when Daniel selects a document filter and submits a question, then retrieval is restricted to that contract and a "Searching: [filename]" indicator is visible in the chat input area | R3 |
| SM-7.1 | PER-02 Daniel | Epic 7 (F7) | **US-7.1** — See a Confidence Signal on Each Answer | JTBD-02.2 → S3: Given an answer with a top chunk similarity < 0.60, when the answer renders, then an amber "Low confidence" badge and a rephrasing suggestion appear alongside the answer — Daniel knows to proceed with caution before acting on it | R3 |
| SM-7.2 | PER-01 Maya | Epic 7 (F7) | **US-7.2** — Rate an Answer with Thumbs Up or Down | JTBD-01.2 → S3: Given an assistant message is displayed, when Maya activates a thumbs-down (keyboard focusable), then feedback is submitted and the selected icon shows an active state — feedback cannot be re-submitted | R3 |

---

### Stage S4: Verify Citation

| SM-ID | Persona | Epic | Story | NaC (derived from JTBD) | Release |
|---|---|---|---|---|---|
| SM-2.1 | PER-01 Maya | Epic 2 (F2) | **US-2.1** — View Source Citations Below Each Answer | JTBD-01.2 → S4: Given an answer has been received, when the streaming completes, then one or more citation chips appear below the answer bubble showing document name and page reference — chips render with no citation for "not found" fallback responses | R1 |
| SM-2.2 | PER-02 Daniel | Epic 2 (F2) | **US-2.2** — Expand a Citation to Read the Source Passage | JTBD-02.1 → S4: Given a citation chip is displayed, when Daniel clicks (or presses Enter on) the chip, then a read-only blockquote expands inline showing the verbatim `chunk_text` — not a paraphrase — with the document name clearly labeled | R1 |
| SM-2.3 | PER-03 Jordan | Epic 2 (F2) | **US-2.3** — Trust Citation Accuracy | JTBD-03.1 → S4: Given a citation is expanded, when Jordan reads the `chunk_text`, then it is the exact verbatim text from the vector index entry used in the LLM prompt; `document_name` matches the uploaded filename; similarity score is in [0.0, 1.0] | R1 |

---

### Stage S5: Act & Export

| SM-ID | Persona | Epic | Story | NaC (derived from JTBD) | Release |
|---|---|---|---|---|---|
| SM-4.1 | PER-03 Jordan | Epic 4 (F4) | **US-4.1** — View and Scroll Through Chat History | JTBD-03.2 → S5: Given 10+ Q&A exchanges are in the session, when Jordan scrolls up in the chat, then all prior questions and answers with their citations are visible and unchanged — no refresh required, no pagination, auto-scroll only triggers when the user is at the bottom | R2 |
| SM-4.2 | PER-01 Maya | Epic 4 (F4) | **US-4.2** — Clear Chat History | JTBD-01.3 → S5: Given Maya wants to start a fresh question set on the same documents, when she clicks Clear Chat and confirms, then the transcript clears and the empty state shows while all uploaded documents and their vector index entries remain intact | R2 |
| SM-4.3 | PER-03 Jordan | Epic 4 (F4) | **US-4.3** — Start a New Session | JTBD-03.2 → S5: Given a session is complete, when Jordan confirms New Session, then the entire document library and chat transcript are cleared, the vector index for the old session is purged, and a new session cookie is set before the empty state renders | R2 |
| SM-8.1 | PER-01 Maya | Epic 8 (F8) | **US-8.1** — Copy an Answer to the Clipboard | JTBD-01.4 → S5: Given a cited answer is displayed, when Maya clicks the copy icon (or activates it by keyboard), then the answer text is placed on the clipboard in a clean paste-ready format — a "Copied!" tooltip confirms success within 2 seconds | R4 |
| SM-8.2 | PER-02 Daniel | Epic 8 (F8) | **US-8.2** — Copy a Source Citation Passage | JTBD-01.4 → S5: Given an expanded citation panel is open, when Daniel clicks the citation copy icon, then the verbatim `chunk_text` (not the generated answer) is copied to the clipboard — ready to paste into an audit note without reformatting | R4 |
| SM-8.3 | PER-03 Jordan | Epic 8 (F8) | **US-8.3** — Export the Full Chat Transcript | JTBD-03.3 → S5: Given a session has 10+ messages, when Jordan clicks Export Transcript and selects Markdown, then a `.md` file downloads containing all messages in chronological order with timestamps, speaker labels, and formatted citation text truncated to 500 characters | R4 |

---

## NaC Derivation Table

Full traceability chain: **JTBD-ID → Job Outcome → Journey Stage → NaC → Story**

| NaC-ID | JTBD-ID | Job Outcome (from JTBD success measure) | Journey Stage | Natural Acceptance Criterion | Story |
|---|---|---|---|---|---|
| NaC-01 | JTBD-01.1 | Data point found with source in < 3 min | S2: Upload & Ingest | Given a batch of PDFs, when dropped onto the upload zone, then all files show per-file status cards immediately — drag-and-drop requires no file picker | US-0.1 |
| NaC-02 | JTBD-01.1 | Data point found with source in < 3 min | S3: Query | Given documents are Ready, when a factual question is submitted, then a streamed answer appears within 8 s (P95), grounded exclusively in uploaded content | US-1.2 |
| NaC-03 | JTBD-03.1 | First cited answer within 60 s of upload | S2: Upload & Ingest | Given a 50-page PDF is dropped, when ingestion runs, then status reaches Ready within 30 s and chat input enables automatically | US-0.3 |
| NaC-04 | JTBD-02.1 | Clause located verbatim in < 2 min | S2: Upload & Ingest | Given a rejected file, when dropped in a batch, then a specific inline error appears on that card and valid files in the batch still proceed | US-0.2 |
| NaC-05 | JTBD-02.1 | Clause located verbatim in < 2 min | S4: Verify Citation | Given a citation chip is displayed, when clicked (or Enter pressed), then verbatim `chunk_text` expands inline in a read-only blockquote with document name | US-2.2 |
| NaC-06 | JTBD-01.2 | Zero hallucinated answers in deliverables | S4: Verify Citation | Given an answer streams to completion, when done event fires, then citation chips appear below the bubble showing document name + page reference; no chips on fallback | US-2.1 |
| NaC-07 | JTBD-03.1 | First cited answer within 60 s of upload | S4: Verify Citation | Given a citation is expanded, when Jordan reads the chunk_text, then it is verbatim from the vector index entry; document_name matches the uploaded filename exactly | US-2.3 |
| NaC-08 | JTBD-02.2 | Zero actions on absent clauses | S3: Query | Given a queried clause is absent from all uploaded documents, when Daniel submits the question, then the system returns the explicit "not found" fallback — no fabricated clause, no citation chips | US-1.3 |
| NaC-09 | JTBD-03.3 | 10+ questions via keyboard only | S3: Query | Given the user is on the chat page with a Ready document, when they press Enter after typing a question, then it submits without mouse interaction; Enter-to-submit holds for every query | US-1.1 |
| NaC-10 | JTBD-01.3 | 5-doc session without manual re-reads | S2: Upload & Ingest | Given 5 research PDFs are uploading, when Maya checks the document library, then each file shows its own status badge (filename, type, size, state) | US-3.1 |
| NaC-11 | JTBD-02.3 | 5 obligations across 3 contracts in < 20 min | S2: Upload & Ingest | Given a superseded contract is in the library, when Daniel clicks Delete and confirms, then the card disappears and the vector purge completes synchronously before 204 | US-3.2 |
| NaC-12 | JTBD-03.2 | 10+ questions in one session, no history loss | S5: Act & Export | Given 10+ exchanges exist, when Jordan scrolls up, then all prior Q&A and citations are visible and unchanged — no refresh, no pagination | US-4.1 |
| NaC-13 | JTBD-01.3 | 5-doc session without manual re-reads | S5: Act & Export | Given Maya wants a fresh question set on the same docs, when she confirms Clear Chat, then the transcript clears while documents and index entries remain intact | US-4.2 |
| NaC-14 | JTBD-03.2 | 10+ questions in one session, no history loss | S5: Act & Export | Given a session is complete, when Jordan confirms New Session, then the old index is purged, a new session cookie is set, and the empty state renders — all before the user can submit a new query | US-4.3 |
| NaC-15 | JTBD-03.3 | 10+ questions via keyboard only | S1: Arrive & Orient | Given app loads, when the user presses Tab, then all interactive elements are reachable; visible focus rings are present; upload zone is Tab-reachable with Enter opening the file picker | US-5.2 |
| NaC-16 | JTBD-01.1 | Data point found with source in < 3 min | S1: Arrive & Orient | Given app loads on a laptop/tablet viewport, when the layout renders, then no horizontal overflow occurs; skeleton loaders appear within 100ms; empty state CTA is immediately visible | US-5.1 |
| NaC-17 | JTBD-01.3 | 5-doc session without manual re-reads | S3: Query | Given 5 reports are Ready, when Maya submits a cross-cutting question, then retrieval spans all 5 simultaneously; the answer cites each source document by name; "From N documents" label appears | US-6.1 |
| NaC-18 | JTBD-02.3 | 5 obligations across 3 contracts in < 20 min | S3: Query | Given 3 contracts are loaded, when Daniel selects a document filter and queries, then only that contract is searched; "Searching: [filename]" indicator is visible in the input area | US-6.2 |
| NaC-19 | JTBD-02.2 | Zero actions on absent clauses | S3: Query | Given an answer's top chunk similarity < 0.60 but ≥ 0.30, when the answer renders, then an amber "Low confidence" badge and rephrasing suggestion appear alongside the answer | US-7.1 |
| NaC-20 | JTBD-01.2 | Zero hallucinated answers in deliverables | S3: Query | Given an assistant message is displayed, when Maya activates thumbs-down (keyboard focusable), then feedback is submitted and the icon shows active state; re-submission is blocked | US-7.2 |
| NaC-21 | JTBD-01.4 | Cited answer copied in < 30 sec | S5: Act & Export | Given a cited answer is visible, when Maya clicks the copy icon, then the answer text lands on the clipboard in clean paste-ready format; "Copied!" tooltip appears within 2 seconds | US-8.1 |
| NaC-22 | JTBD-01.4 | Cited answer copied in < 30 sec | S5: Act & Export | Given an expanded citation panel is open, when Daniel clicks the citation copy icon, then the verbatim chunk_text (not the generated answer) is placed on the clipboard | US-8.2 |
| NaC-23 | JTBD-03.3 | 10+ questions via keyboard only | S5: Act & Export | Given 10+ messages exist, when Jordan activates Export Transcript → Markdown (keyboard accessible), then a .md file downloads with all messages, timestamps, speaker labels, and citations | US-8.3 |

---

## Release Planning

### R1 — "RAG Core" (MVP Blockers — P0)
**Theme:** Establish the complete, trust-worthy RAG loop end-to-end for all three personas. A user can upload a document, ask a question, receive a grounded streamed answer, and verify the source passage — all in one session.

**Stories:** US-0.1, US-0.2, US-0.3, US-1.1, US-1.2, US-1.3, US-2.1, US-2.2, US-2.3

| Story | Stage | Persona Served | JTBD Addressed |
|---|---|---|---|
| US-0.1 Drag-and-Drop Upload | S2 | PER-01 Primary | JTBD-01.1 |
| US-0.2 File Validation | S2 | PER-02 Primary | JTBD-02.1 |
| US-0.3 Ingestion Status Tracking | S2 | PER-03 Primary | JTBD-03.1 |
| US-1.1 Submit Question via Keyboard | S3 | PER-03 Primary | JTBD-03.3 |
| US-1.2 Streamed Document-Grounded Answer | S3 | PER-01 Primary | JTBD-01.1 |
| US-1.3 "Not Found" Fallback | S3 | PER-02 Primary | JTBD-02.2 |
| US-2.1 View Source Citations | S4 | PER-01 Primary | JTBD-01.2 |
| US-2.2 Expand Citation to Verbatim Passage | S4 | PER-02 Primary | JTBD-02.1 |
| US-2.3 Trust Citation Accuracy | S4 | PER-03 Primary | JTBD-03.1 |

**Persona Coverage:** All three personas served across all stages S1–S5 (S1 and S5 via basic defaults; core loop S2–S4 fully covered).

**JTBD Addressed:** JTBD-01.1, JTBD-01.2, JTBD-02.1, JTBD-02.2, JTBD-03.1, JTBD-03.3

**Journey Completion:** R1 delivers a complete path through JRN-01.1 (Maya's batch upload + query + citation verify), JRN-02.1 (Daniel's clause lookup + not-found test), and JRN-03.1 (Jordan's keyboard-first spec lookup + citation expand).

---

### R2 — "Session Quality" (MVP Completers — P1)
**Theme:** Make the session experience complete and production-quality. Users can manage their document library, navigate the full chat history, use the app on any device, and work keyboard-first. R2 enables JRN-01.2 (Maya's cross-doc export) and JRN-03.2 (Jordan's multi-document iterative session).

**Stories:** US-3.1, US-3.2, US-4.1, US-4.2, US-4.3, US-5.1, US-5.2

| Story | Stage | Persona Served | JTBD Addressed |
|---|---|---|---|
| US-3.1 View and Track Session Documents | S2 | PER-01 Primary | JTBD-01.3 |
| US-3.2 Delete a Document | S2 | PER-02 Primary | JTBD-02.3 |
| US-4.1 View and Scroll Chat History | S5 | PER-03 Primary | JTBD-03.2 |
| US-4.2 Clear Chat History | S5 | PER-01 Primary | JTBD-01.3 |
| US-4.3 Start a New Session | S5 | PER-03 Primary | JTBD-03.2 |
| US-5.1 Responsive UI Across Device Sizes | S1 | PER-01 Primary | JTBD-01.1 |
| US-5.2 Full Keyboard Navigation | S1 | PER-03 Primary | JTBD-03.3 |

**Persona Coverage:** All three personas gain session management and polished UI/accessibility capabilities.

**JTBD Addressed:** JTBD-01.3, JTBD-02.3, JTBD-03.2, JTBD-03.3 (plus reinforcing JTBD-01.1 via responsive UI)

**Journey Completion:** R2 enables the full JRN-01.2 journey (document library confirmation → cross-doc query → review → iterate → export), JRN-02.2 (upload 3 contracts → verify each → produce summary), and JRN-03.2 (multi-document session → document swap → scroll history → copy findings).

---

### R3 — "Multi-Doc & Trust Signals" (Post-MVP v1.1 — P2)
**Theme:** Elevate the multi-document experience and surface trust signals that prevent misuse. These stories target the advanced use cases for Maya (cross-document research synthesis) and Daniel (procurement multi-contract comparison) while giving all users explicit confidence guidance.

**Stories:** US-6.1, US-6.2, US-7.1, US-7.2

| Story | Stage | Persona Served | JTBD Addressed |
|---|---|---|---|
| US-6.1 Query Across All Documents Simultaneously | S3 | PER-01 Primary, PER-02 Primary | JTBD-01.3, JTBD-02.3 |
| US-6.2 Filter a Query to a Specific Document | S3 | PER-02 Primary | JTBD-02.3 |
| US-7.1 Confidence Signal on Each Answer | S3 | PER-02 Primary | JTBD-02.2 |
| US-7.2 Rate an Answer with Thumbs Up/Down | S3 | PER-01 Secondary | JTBD-01.2 |

**Persona Coverage:** PER-01 and PER-02 gain the full multi-document retrieval experience. All personas benefit from confidence signals.

**JTBD Addressed:** JTBD-01.3, JTBD-02.2, JTBD-02.3

**Journey Completion:** R3 completes the advanced paths in JRN-01.2 (cross-document query with per-source attribution) and JRN-02.2 (per-contract citation expansion and comparison). It also fully satisfies JTBD-02.2's "explicit not-found" requirement at the UI layer through the confidence badge.

---

### R4 — "Workflow Convenience" (Backlog — P3)
**Theme:** Add the copy/export utilities that reduce friction when transferring findings to external tools (client decks, audit notes, team Slack messages). These are high-delight but not blocking any core journey.

**Stories:** US-8.1, US-8.2, US-8.3

| Story | Stage | Persona Served | JTBD Addressed |
|---|---|---|---|
| US-8.1 Copy an Answer to the Clipboard | S5 | PER-01 Primary | JTBD-01.4 |
| US-8.2 Copy a Source Citation Passage | S5 | PER-02 Secondary | JTBD-01.4 |
| US-8.3 Export the Full Chat Transcript | S5 | PER-03 Secondary | JTBD-03.3 |

**Persona Coverage:** PER-01 Maya gains the highest-value workflow accelerator (copy answer + citation for client deliverables). PER-02 gains audit-trail copy. PER-03 gains team sharing via transcript export.

**JTBD Addressed:** JTBD-01.4, JTBD-03.3 (keyboard-accessible copy/export)

**Journey Completion:** R4 fully satisfies the "Export Session" stage in JRN-01.2 and the "Session Wrap & Copy" stage in JRN-03.2, and the "Act on Results" stage in JRN-02.1.

---

## Coverage Analysis

### Persona Coverage by Release

| Persona | R1 (MVP Blockers) | R2 (MVP Completers) | R3 (v1.1) | R4 (Backlog) |
|---|---|---|---|---|
| **PER-01 Maya** | US-0.1, US-1.2, US-2.1 | US-3.1, US-4.2, US-5.1 | US-6.1, US-7.2 | US-8.1 |
| **PER-02 Daniel** | US-0.2, US-1.3, US-2.2 | US-3.2 | US-6.2, US-7.1 | US-8.2 |
| **PER-03 Jordan** | US-0.3, US-1.1, US-2.3 | US-4.1, US-4.3, US-5.2 | — | US-8.3 |

> All three personas are served in every release. No persona is left without coverage in R1 (the MVP).

### JTBD Coverage by Release

| JTBD-ID | Priority | Addressed In | Stories |
|---|---|---|---|
| JTBD-01.1 | P0 | R1, R2 | US-0.1, US-1.2, US-5.1 |
| JTBD-01.2 | P0 | R1, R3 | US-2.1, US-7.2 |
| JTBD-01.3 | P2 | R2, R3 | US-3.1, US-4.2, US-6.1 |
| JTBD-01.4 | P3 | R4 | US-8.1, US-8.2 |
| JTBD-02.1 | P0 | R1 | US-0.2, US-2.2 |
| JTBD-02.2 | P0 | R1, R3 | US-1.3, US-7.1 |
| JTBD-02.3 | P2 | R2, R3 | US-3.2, US-6.1, US-6.2 |
| JTBD-03.1 | P0 | R1 | US-0.3, US-2.3 |
| JTBD-03.2 | P1 | R2 | US-4.1, US-4.3 |
| JTBD-03.3 | P1 | R1, R2, R4 | US-1.1, US-5.2, US-8.3 |

### Journey Stage Coverage by Release

| Stage | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| **S1 Arrive & Orient** | *(basic defaults)* | US-5.1, US-5.2 | — | — |
| **S2 Upload & Ingest** | US-0.1, US-0.2, US-0.3 | US-3.1, US-3.2 | — | — |
| **S3 Query** | US-1.1, US-1.2, US-1.3 | — | US-6.1, US-6.2, US-7.1, US-7.2 | — |
| **S4 Verify Citation** | US-2.1, US-2.2, US-2.3 | — | — | — |
| **S5 Act & Export** | *(minimal)* | US-4.1, US-4.2, US-4.3 | — | US-8.1, US-8.2, US-8.3 |

### Gap Analysis

**Journey stages without R1 coverage:**
- **S1 (Arrive & Orient):** No dedicated R1 stories — the empty state and responsive layout are delivered in R2 (US-5.1, US-5.2). The R1 product is functional but relies on browser defaults for layout/accessibility. This is an acceptable R1 constraint given the single-user session-based MVP scope.
- **S5 (Act & Export):** R1 provides no copy or export utilities. Users can read answers but must manually select-and-copy text. The core R1 value loop (upload → query → verify) is complete without export. Export arrives in R4.

**JTBD without R1 stories:**
- **JTBD-01.3** (cross-document research) — addressed in R2 (library) and R3 (multi-doc retrieval). R1 supports single-document queries; cross-doc search is a P2 enhancement.
- **JTBD-01.4** (frictionless export) — addressed in R4. Not a blocker for the core value proposition.
- **JTBD-02.3** (multi-contract comparison) — addressed in R2 (delete/library) and R3 (multi-doc retrieval). R1 supports single-contract clause lookup.
- **JTBD-03.2** (multi-document session) — addressed in R2 (chat history, session management). R1 delivers within-session queries but not full session lifecycle management.

**Orphan stories:** None. All 23 stories (US-0.1 through US-8.3) are mapped to at least one journey stage and one release. ✅

**JTBD without any story:** None. All 10 JTBD outcomes have at least one derived NaC and at least one story. ✅

---

## NaC-to-Acceptance Criteria Alignment

This section verifies that each NaC is reflected in the UserStory acceptance criteria it references.

| NaC-ID | Story | NaC Criterion | AC Alignment |
|---|---|---|---|
| NaC-01 | US-0.1 | Drop zone visible; files upload immediately; per-file status cards show | AC: "Dropping a valid file begins upload immediately and shows a per-file upload card with filename, size, and spinner" ✅ |
| NaC-02 | US-1.2 | Answer streams within 8 s (P95); grounded in uploaded content only | AC: "End-to-end answer latency (P95) < 8 s"; "answer contains only information derived from uploaded documents" ✅ |
| NaC-03 | US-0.3 | 50-page PDF reaches Ready within 30 s; chat input enables on first Ready | AC: "Processing a 50-page PDF completes within 30 seconds"; "chat input becomes enabled when status reaches ready" ✅ |
| NaC-04 | US-0.2 | Inline error on rejected file; valid batch files still proceed | AC: "Rejection of one file in a batch does not prevent other valid files from uploading"; per-file error reason shown ✅ |
| NaC-05 | US-2.2 | Verbatim chunk_text expands in read-only blockquote on click or Enter | AC: "Clicking a citation chip expands an inline citation panel showing full chunk_text in a read-only area"; "accessible by keyboard (Enter/Space)" ✅ |
| NaC-06 | US-2.1 | Citation chips appear after done event; no chips on fallback responses | AC: "After done event, citation chips appear below the completed answer bubble"; "No citation chips rendered for fallback responses" ✅ |
| NaC-07 | US-2.3 | chunk_text is verbatim from vector index; document_name matches filename | AC: "chunk_text is the verbatim text from the vector index entry used in the LLM prompt"; "document_name matches original uploaded filename exactly" ✅ |
| NaC-08 | US-1.3 | Explicit "not found" message returned; no fabricated clause; no citation chips | AC: "System returns standardized fallback: 'The uploaded documents do not contain information about this topic'"; "never generates a plausible-sounding but unsupported answer" ✅ |
| NaC-09 | US-1.1 | Enter submits query without mouse click; holds for every query | AC: "Pressing Enter submits the query"; "Shift+Enter inserts a newline without submitting" ✅ |
| NaC-10 | US-3.1 | Each file shows status badge (filename, type, size, state) in library panel | AC: "Each document shown as a card with: filename, file type icon, human-readable size, and a status badge" ✅ |
| NaC-11 | US-3.2 | Delete card disappears; vector purge synchronous before 204 | AC: "Vector index purge is synchronous: backend removes all chunks before returning 204" ✅ |
| NaC-12 | US-4.1 | All prior Q&A visible on scroll-up; no refresh; no pagination | AC: "Full session transcript in vertically scrollable container"; "auto-scrolls only if user was at bottom"; "Chat history restored from server on page reconnect" ✅ |
| NaC-13 | US-4.2 | Transcript clears; documents and index entries remain intact | AC: "All uploaded documents and their vector index entries remain intact after clearing chat"; "document library is unchanged" ✅ |
| NaC-14 | US-4.3 | Old index purged; new session cookie set; empty state renders | AC: "Vector index for old session fully purged on server before new session is created"; "new session cookie is set" ✅ |
| NaC-15 | US-5.2 | Tab reaches all elements; Enter on upload zone opens file picker; visible focus rings | AC: "Tab order follows logical flow: Upload zone → Document library items → Chat input → ..."; "Pressing Enter on upload zone opens file picker"; "All interactive elements have a visible focus ring" ✅ |
| NaC-16 | US-5.1 | No horizontal overflow at any breakpoint; skeleton loaders in 100ms | AC: "No horizontal overflow or layout breakage at 320px, 768px, 1024px, or 1440px"; "Skeleton loaders appear within 100ms" ✅ |
| NaC-17 | US-6.1 | Query searches all Ready docs simultaneously; per-source attribution; "From N documents" label | AC: "query searches full session vector index spanning all documents"; "From N documents label displayed above citation chips" ✅ |
| NaC-18 | US-6.2 | Document filter restricts retrieval; "Searching: [filename]" indicator visible | AC: "Selecting a document sets active filter; subsequent queries retrieve chunks only from that document"; "visual indicator in chat input area" ✅ |
| NaC-19 | US-7.1 | Amber "Low confidence" badge + rephrasing suggestion on similarity ≥ 0.30 and < 0.60 | AC: "Answers where top chunk similarity ≥ 0.30 but < 0.60 display amber 'Low confidence' badge"; "Low-confidence answers also display inline rephrasing suggestion" ✅ |
| NaC-20 | US-7.2 | Thumbs-down keyboard-focusable; active state shown; re-submission blocked | AC: "Thumbs-up and thumbs-down icon buttons appear on keyboard focus"; "after submission, selected icon displays filled/active state"; "Feedback buttons become disabled after submission" ✅ |
| NaC-21 | US-8.1 | Answer text on clipboard in clean format; "Copied!" tooltip within 2 s | AC: "Clicking copy icon writes answer text to clipboard"; "'Copied!' tooltip appears for 2 seconds" ✅ |
| NaC-22 | US-8.2 | Verbatim chunk_text (not answer) placed on clipboard | AC: "Clicking icon copies citation's chunk_text to clipboard" ✅ |
| NaC-23 | US-8.3 | .md file downloads with all messages, timestamps, speaker labels, citations ≤ 500 chars | AC: "Downloaded file contains all messages in chronological order with timestamps, speaker labels, and formatted citations"; "Citation text truncated to 500 characters" ✅ |

> **All 23 NaC are fully aligned with their referenced UserStory acceptance criteria.** No gaps or mismatches detected.

---

## Story Map ID Index

| SM-ID | Story ID | Title | Stage | Release |
|---|---|---|---|---|
| SM-0.1 | US-0.1 | Drag-and-Drop File Upload | S2 | R1 |
| SM-0.2 | US-0.2 | File Validation and Size Limits | S2 | R1 |
| SM-0.3 | US-0.3 | Asynchronous Ingestion Status Tracking | S2 | R1 |
| SM-1.1 | US-1.1 | Submit a Question via Chat Input | S3 | R1 |
| SM-1.2 | US-1.2 | Receive a Streamed, Document-Grounded Answer | S3 | R1 |
| SM-1.3 | US-1.3 | Receive a "Not Found" Fallback | S3 | R1 |
| SM-2.1 | US-2.1 | View Source Citations Below Each Answer | S4 | R1 |
| SM-2.2 | US-2.2 | Expand a Citation to Read the Source Passage | S4 | R1 |
| SM-2.3 | US-2.3 | Trust Citation Accuracy | S4 | R1 |
| SM-3.1 | US-3.1 | View and Track All Session Documents | S2 | R2 |
| SM-3.2 | US-3.2 | Delete a Document from the Session | S2 | R2 |
| SM-4.1 | US-4.1 | View and Scroll Through Chat History | S5 | R2 |
| SM-4.2 | US-4.2 | Clear Chat History | S5 | R2 |
| SM-4.3 | US-4.3 | Start a New Session | S5 | R2 |
| SM-5.1 | US-5.1 | Use the Application Across All Device Sizes | S1 | R2 |
| SM-5.2 | US-5.2 | Navigate and Use the Application Entirely by Keyboard | S1 | R2 |
| SM-6.1 | US-6.1 | Ask Questions Across All Uploaded Documents Simultaneously | S3 | R3 |
| SM-6.2 | US-6.2 | Filter a Query to a Specific Document | S3 | R3 |
| SM-7.1 | US-7.1 | See a Confidence Signal on Each Answer | S3 | R3 |
| SM-7.2 | US-7.2 | Rate an Answer with Thumbs Up or Down | S3 | R3 |
| SM-8.1 | US-8.1 | Copy an Answer to the Clipboard | S5 | R4 |
| SM-8.2 | US-8.2 | Copy a Source Citation Passage | S5 | R4 |
| SM-8.3 | US-8.3 | Export the Full Chat Transcript | S5 | R4 |

---

## Validation Checklist

- [x] Every UserStory (US-0.1 through US-8.3) appears in the map — 23 of 23 stories mapped
- [x] Every mapped story has a NaC derived from a specific JTBD outcome
- [x] NaC Derivation Table (NaC-01 through NaC-23) has full JTBD → stage → criterion → story chains
- [x] Release planning groups R1–R4 are defined with themes and persona/JTBD coverage
- [x] Coverage analysis identifies gaps (S1/S5 R1 gaps) and confirms no orphan stories
- [x] NaC-to-Acceptance Criteria mapping verifies alignment for all 23 stories — all ✅
- [x] Each release (R1, R2) enables at least one complete journey (R1: JRN-01.1, JRN-02.1, JRN-03.1; R2: JRN-01.2, JRN-02.2, JRN-03.2)
- [x] No JTBD outcomes without derived NaC
- [x] No orphan stories (stories unmapped to journey stages)

---

*Document generated: 2026-05-13 | RAGChatbot STORY-MAP v1.0*
