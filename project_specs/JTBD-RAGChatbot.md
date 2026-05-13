# Jobs-to-be-Done: RAG Chatbot

| Field | Value |
|---|---|
| **Product Name** | RAG Chatbot |
| **Project Acronym** | RAGChatbot |
| **Version** | 1.0 |
| **Date** | 2026-05-13 |
| **Related Personas** | PERSONAS-RAGChatbot.md v1.0 |
| **Related PRD** | PRD-RAGChatbot.md v1.0 |
| **Status** | Draft |

---

## JTBD Summary Table

| JTBD-ID | Persona | Job Statement (Summary) | Priority |
|---|---|---|---|
| JTBD-01.1 | PER-01 Maya Patel | Find a specific data point in a large research document without reading it end-to-end | P0 |
| JTBD-01.2 | PER-01 Maya Patel | Verify that every answer is traceable to an exact source passage before using it in a deliverable | P0 |
| JTBD-01.3 | PER-01 Maya Patel | Cross-reference findings across multiple research reports in a single working session | P2 |
| JTBD-01.4 | PER-01 Maya Patel | Transfer a cited Q&A result into an external deliverable without reformatting manually | P3 |
| JTBD-02.1 | PER-02 Daniel Torres | Locate a specific contract clause quickly without manually scanning dozens of pages | P0 |
| JTBD-02.2 | PER-02 Daniel Torres | Confirm an answer is grounded in the actual document — or be told explicitly it is absent | P0 |
| JTBD-02.3 | PER-02 Daniel Torres | Compare how the same obligation is worded across multiple vendor contracts in one session | P2 |
| JTBD-03.1 | PER-03 Jordan Kim | Get a precise, document-backed answer to a technical question without digging through lengthy specs | P0 |
| JTBD-03.2 | PER-03 Jordan Kim | Maintain a fluid, multi-document session while iterating on a technical problem | P1 |
| JTBD-03.3 | PER-03 Jordan Kim | Interact with the tool entirely via keyboard to stay in a flow state during deep work | P1 |

---

## PER-01: Maya Patel — Research Analyst

### JTBD-01.1: Targeted Data Point Retrieval

**Job Statement:**
When I receive a batch of research PDFs and need a specific statistic or conclusion for a client deliverable, I want to ask a natural language question and receive the answer with an exact source passage, so I can extract the data point in minutes rather than reading the entire document.

**Current Alternatives:**
- Ctrl-F searches on key terms across 80-page PDFs — frequently misses paraphrased content
- Reads sections manually until the relevant passage is found — 30–60 minutes per data point
- Uses ChatGPT to summarize the document, then cannot verify if the statistic is from *her* report or the model's training data

**Hiring Criteria:**
- Answers draw exclusively from uploaded documents — no blending with external knowledge
- Each answer includes the source document name and the specific passage used
- Returns a first answer within 8 seconds of submitting a question
- Supports PDF upload for documents up to at least 80 pages

**Success Measure:** Maya locates a specific data point and verifies its source passage in under 3 minutes (vs. current 30–60 min manual scan).

**Related Features:** F0, F1, F2
**Priority:** P0

---

### JTBD-01.2: Source-Verified Answer Before Use in Deliverable

**Job Statement:**
When I have an answer I plan to include in a client report, I want to expand the cited passage and confirm it matches what the document actually says, so I can protect my professional credibility and avoid publishing a misattributed statistic.

**Current Alternatives:**
- Re-opens the source PDF and manually locates the passage to cross-check the AI answer
- Relies on copy-paste from document and visual comparison — time-consuming and error-prone
- Adds a disclaimer in her draft noting the citation "needs verification" — then forgets to follow up

**Hiring Criteria:**
- Every answer exposes an expandable source citation showing the raw text from the document
- Citation clearly labels the document name and page or chunk reference
- Citation text is read-only and visually distinct from the generated answer
- System never presents a confident answer when no relevant content was found — it says so explicitly

**Success Measure:** Zero adopted deliverable answers later identified as hallucinated or misattributed across Maya's usage sessions.

**Related Features:** F2, F1, F7
**Priority:** P0

---

### JTBD-01.3: Cross-Document Research in a Single Session

**Job Statement:**
When I am comparing findings across three to five related industry reports, I want to ask a question that searches all uploaded documents simultaneously and see which report each part of the answer comes from, so I can identify contradictions or consensus across sources without switching tools.

**Current Alternatives:**
- Opens each PDF in a separate browser tab and searches independently — manually reconciles results in a notes document
- Uploads one document at a time to a chat tool, losing context between uploads
- Creates a manual comparison table in a spreadsheet — takes 1–2 hours for a 5-document set

**Hiring Criteria:**
- A single question retrieves relevant context from all documents currently in the session
- Each answer clearly attributes which source document contributed each piece of information
- Session supports at least 5 uploaded documents simultaneously
- Document library shows which files are indexed and ready to query

**Success Measure:** Maya completes a 5-document cross-reference session without needing to re-read any source document manually.

**Related Features:** F6, F3, F0
**Priority:** P2

---

### JTBD-01.4: Frictionless Transfer of Cited Q&A to External Deliverables

**Job Statement:**
When I have a cited answer ready to include in a slide deck or report draft, I want to copy the answer and its citation in a single action, so I can paste it into my deliverable without manually reformatting or re-typing source references.

**Current Alternatives:**
- Manually copies the answer text, then separately types or copies the citation — two steps, easy to mismatch
- Screenshots the chat window and pastes as an image — cannot be edited or updated
- Exports a transcript and then searches through it to find the relevant exchange

**Hiring Criteria:**
- A single copy action captures both the answer text and the source citation
- Export of full session transcript is available as plain text or Markdown
- Copied content is clean, ready-to-paste without markdown artifacts or extra whitespace

**Success Measure:** Maya transfers a cited answer into her draft in under 30 seconds without any reformatting step.

**Related Features:** F8, F2
**Priority:** P3

---

## PER-02: Daniel Torres — Legal & Contracts Professional

### JTBD-02.1: Precise Clause Location Under Time Pressure

**Job Statement:**
When I am preparing for a negotiation or audit and need to find a specific clause — indemnification, termination, SLA threshold — across a 50-plus page contract, I want to ask a targeted question and receive the verbatim clause text with a page reference, so I can act on accurate information in minutes rather than reading the full contract.

**Current Alternatives:**
- Ctrl-F searches on keyword terms — misses paraphrased or context-dependent obligations in exhibit language
- Manually reviews the full contract section by section — 15–25 minutes per clause lookup
- Delegates to a colleague or outside counsel for urgent clause pulls — creates a bottleneck and cost

**Hiring Criteria:**
- Answers quote the verbatim clause text, not a paraphrase
- Each answer includes the page number or section reference within the document
- Supports PDF and DOCX formats (the standard formats for contracts)
- Retrieves accurate answers even when obligation language is buried in exhibits or appendices
- Returns answer within 8 seconds of query submission

**Success Measure:** Daniel locates and verifies a specific clause with exact quoted text in under 2 minutes (vs. current 15–25 min manual review).

**Related Features:** F1, F2, F0
**Priority:** P0

---

### JTBD-02.2: Explicit Confirmation of Clause Absence

**Job Statement:**
When I ask whether a contract contains a particular obligation and that obligation does not exist in the document, I want the system to explicitly state "not found" rather than generate a plausible-sounding but fabricated answer, so I can trust the result and avoid acting on a clause that was never agreed to.

**Current Alternatives:**
- Uses general AI chatbots — receives confident-sounding answers that sometimes fabricate clause language, requiring manual verification to catch errors
- Treats all AI-generated clause text as unverified until manually confirmed in the source document
- Stops using AI tools for this task entirely after encountering a hallucinated result — reverts to full manual review

**Hiring Criteria:**
- System returns an explicit "not found" response when no relevant content exists in the uploaded documents
- System never generates a plausible answer when supporting content is absent from the index
- A low-confidence or weak-retrieval signal is surfaced visually so Daniel knows when to proceed with caution
- Responses include which documents were searched, even when nothing was found

**Success Measure:** Zero instances of Daniel acting on an AI-generated clause that does not exist verbatim in any uploaded document.

**Related Features:** F7, F1, F2
**Priority:** P0

---

### JTBD-02.3: Multi-Contract Obligation Comparison

**Job Statement:**
When I am reviewing three or more vendor contracts for a procurement decision, I want to ask whether a particular obligation appears across all uploaded contracts and see the exact wording from each, so I can identify differences in liability exposure without opening each contract separately.

**Current Alternatives:**
- Opens each contract in a separate PDF viewer, uses Ctrl-F in each, and manually records findings in a comparison table — takes 1–2 hours for 3 contracts
- Uploads one contract at a time to a chat tool and re-phrases the question for each — loses cross-document context and doubles the time
- Delegates comparison work to a paralegal — adds lead time and cost to the review cycle

**Hiring Criteria:**
- A single query searches all uploaded contracts simultaneously
- Each answer citation identifies which contract (by file name) contributed each piece of text
- Session supports uploading and querying at least 5 contracts simultaneously
- Document library makes it clear which contracts are indexed and ready

**Success Measure:** Daniel produces a written summary of 5 key obligations across 3 contracts in under 20 minutes.

**Related Features:** F6, F3, F2
**Priority:** P2

---

## PER-03: Jordan Kim — Technical Knowledge Worker

### JTBD-03.1: Instant Answers from Technical Documentation

**Job Statement:**
When I am blocked on a technical decision and need a specific parameter, constraint, or behavior from a 200-page spec or API reference, I want to ask a natural language question and receive a precise, document-backed answer in under 60 seconds, so I can stay unblocked without reading through the entire document.

**Current Alternatives:**
- Ctrl-F searches across large PDFs for config parameters — 10–15 minutes per lookup, misses non-exact matches
- Uses an LLM trained on general data to answer API questions — receives outdated or version-incorrect behavior that contradicts the specific doc in hand
- Asks a senior colleague — creates a bottleneck in their day and adds latency to the decision

**Hiring Criteria:**
- Answers are strictly grounded in the uploaded document — no blending with general LLM training data about API behavior
- Every answer includes the source passage from the specific document version uploaded
- First answer is returned within 60 seconds of document upload (upload + index + query cycle)
- Supports PDF and DOCX formats; handles technical documents with code blocks and tables

**Success Measure:** Jordan uploads a technical spec and receives a first cited answer in under 60 seconds, with the answer reflecting the exact document version uploaded rather than general training data.

**Related Features:** F0, F1, F2
**Priority:** P0

---

### JTBD-03.2: Active Multi-Document Session for Iterative Problem-Solving

**Job Statement:**
When I am iterating on a technical problem and need to reference an API doc, an architecture decision record, and a requirements spec simultaneously, I want to keep all documents active in a single session and scroll back through earlier answers, so I can synthesize information across sources without losing context between lookups.

**Current Alternatives:**
- Opens each document in a separate browser tab and manually switches between them — loses conversational context
- Starts a new chat for each document — cannot cross-reference answers and loses prior question history
- Pastes relevant document excerpts directly into a chat prompt — tedious and limited by context window

**Hiring Criteria:**
- Session supports multiple documents active simultaneously with queries spanning all of them
- Full chat history is preserved and scrollable throughout the session without page refresh
- Ability to add or remove specific document versions mid-session (e.g., swap v2.1 spec for v2.3)
- Session stays intact across at least a full multi-hour work day without data loss

**Success Measure:** Jordan completes 10+ questions across 3 or more documents in a single session without loss of chat history or document context.

**Related Features:** F3, F4, F6
**Priority:** P1

---

### JTBD-03.3: Keyboard-First Interaction for Deep Work Flow

**Job Statement:**
When I am in a focused work session and interrogating a technical document through multiple rapid-fire questions, I want to submit questions with Enter, navigate the interface with Tab, and copy answers without reaching for the mouse, so I can maintain my flow state and minimize the friction of each lookup.

**Current Alternatives:**
- Uses tools that require mouse clicks to submit queries — breaks keyboard flow and adds latency per interaction
- Copies answers by triple-clicking and using Ctrl+C — inconsistent selection behavior with multi-paragraph answers
- Avoids certain tools entirely because of sluggish or unresponsive UIs that break concentration

**Hiring Criteria:**
- Enter key submits a question from the chat input without requiring a mouse click
- Full keyboard navigation via Tab key across all interactive elements (upload, input, copy, delete)
- Focus rings are visible and logically ordered
- UI loads and responds within 300ms for input interactions (typing, scrolling, navigation)
- Copy-to-clipboard action available without a mouse via keyboard shortcut or accessible focus target

**Success Measure:** Jordan completes 10 or more questions in a session using keyboard-only interaction with zero forced mouse actions.

**Related Features:** F5, F1, F8
**Priority:** P1

---

## Outcome-to-Feature Traceability

| JTBD-ID | Feature ID(s) | Expected Outcome |
|---|---|---|
| JTBD-01.1 | F0, F1, F2 | Research analyst retrieves a specific data point with source passage in under 3 minutes |
| JTBD-01.2 | F2, F1, F7 | Zero deliverable answers later identified as hallucinated or misattributed |
| JTBD-01.3 | F6, F3, F0 | 5-document cross-reference session completed without manual re-reading of any source |
| JTBD-01.4 | F8, F2 | Cited answer transferred to external deliverable in under 30 seconds with no reformatting |
| JTBD-02.1 | F1, F2, F0 | Contracts professional locates and verifies a clause with exact quoted text in under 2 minutes |
| JTBD-02.2 | F7, F1, F2 | Zero instances of acting on an AI-generated clause absent from uploaded documents |
| JTBD-02.3 | F6, F3, F2 | Summary of 5 key obligations across 3 contracts produced in under 20 minutes |
| JTBD-03.1 | F0, F1, F2 | Technical worker receives first cited answer within 60 seconds of upload, grounded in specific document version |
| JTBD-03.2 | F3, F4, F6 | 10+ questions answered across 3 documents in a single session with no history or context loss |
| JTBD-03.3 | F5, F1, F8 | 10+ questions completed via keyboard-only interaction with zero forced mouse actions |

**Feature Coverage Check:**

| Feature | Covered By | Status |
|---|---|---|
| F0 — Document Upload & Ingestion | JTBD-01.1, JTBD-01.3, JTBD-02.1, JTBD-03.1 | ✅ |
| F1 — RAG-Powered Question Answering | JTBD-01.1, JTBD-01.2, JTBD-02.1, JTBD-02.2, JTBD-03.1, JTBD-03.3 | ✅ |
| F2 — Source Citations | JTBD-01.1, JTBD-01.2, JTBD-01.4, JTBD-02.1, JTBD-02.2, JTBD-02.3, JTBD-03.1 | ✅ |
| F3 — Document Library Management | JTBD-01.3, JTBD-02.3, JTBD-03.2 | ✅ |
| F4 — Session-Scoped Chat History | JTBD-03.2 | ✅ |
| F5 — Premium Responsive UI | JTBD-03.3 | ✅ |
| F6 — Multi-Document Context Retrieval | JTBD-01.3, JTBD-02.3, JTBD-03.2 | ✅ |
| F7 — Answer Confidence & Relevance Feedback | JTBD-01.2, JTBD-02.2 | ✅ |
| F8 — Export & Copy Utilities | JTBD-01.4, JTBD-03.3 | ✅ |

---

## NaC Preview

> *Candidate Natural Acceptance Criteria derived from job success measures. These will be refined and expanded in the STORY-MAP document.*

| JTBD-ID | Outcome | Candidate Natural Acceptance Criterion |
|---|---|---|
| JTBD-01.1 | Data point found with source in < 3 min | **Given** a user has uploaded a research PDF, **when** they ask a factual question, **then** a cited answer appears within 8 seconds and the citation links to the exact source passage |
| JTBD-01.2 | Zero hallucinated answers in deliverables | **Given** no relevant content exists for a query, **when** the system responds, **then** it returns an explicit "not found" message — never a fabricated answer |
| JTBD-01.3 | 5-doc session without manual re-reads | **Given** 5 documents are uploaded and indexed, **when** the user asks a cross-cutting question, **then** the answer cites passages from multiple documents and identifies each source by name |
| JTBD-01.4 | Cited answer copied in < 30 sec | **Given** a cited answer is displayed, **when** the user activates copy, **then** both the answer text and source citation are placed on the clipboard in a clean, paste-ready format |
| JTBD-02.1 | Clause located verbatim in < 2 min | **Given** a contract PDF is uploaded, **when** the user queries for a specific clause type, **then** the answer returns the verbatim clause text with document name and page/section reference |
| JTBD-02.2 | Zero actions on absent clauses | **Given** a queried clause does not appear in any uploaded document, **when** the system responds, **then** it explicitly states the clause was not found and does not generate alternative language |
| JTBD-02.3 | 5 obligations across 3 contracts in < 20 min | **Given** 3 contracts are uploaded, **when** the user queries for an obligation, **then** the answer identifies which contracts contain it and shows the relevant wording from each |
| JTBD-03.1 | First cited answer within 60 sec of upload | **Given** a technical document has been uploaded, **when** the user submits their first question, **then** a cited answer grounded exclusively in the uploaded document is returned within 60 seconds of upload completion |
| JTBD-03.2 | 10+ questions in one session, no history loss | **Given** a multi-document session is active, **when** the user scrolls up in the chat, **then** all prior questions and answers in the session are visible and unchanged |
| JTBD-03.3 | 10+ questions via keyboard only | **Given** the user is on the chat page, **when** they press Enter after typing a question, **then** the question is submitted without requiring a mouse click; all interactive elements are reachable via Tab |

---

*Document generated: 2026-05-13 | RAGChatbot JTBD v1.0*
