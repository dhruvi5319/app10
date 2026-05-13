# User Journey Maps: RAG Chatbot

| Field | Value |
|---|---|
| **Product Name** | RAG Chatbot |
| **Project Acronym** | RAGChatbot |
| **Version** | 1.0 |
| **Date** | 2026-05-13 |
| **Related Personas** | PERSONAS-RAGChatbot.md v1.0 |
| **Related JTBD** | JTBD-RAGChatbot.md v1.0 |
| **Related PRD** | PRD-RAGChatbot.md v1.0 |
| **Status** | Draft |

---

## Journey Index

| JRN-ID | Persona | Scenario | Key JTBD(s) | Stages |
|---|---|---|---|---|
| JRN-01.1 | PER-01 Maya Patel | Research PDF batch upload and targeted data point retrieval | JTBD-01.1, JTBD-01.2 | 5 |
| JRN-01.2 | PER-01 Maya Patel | Cross-document comparison and export to client deliverable | JTBD-01.3, JTBD-01.4 | 5 |
| JRN-02.1 | PER-02 Daniel Torres | Clause location under negotiation time pressure | JTBD-02.1, JTBD-02.2 | 5 |
| JRN-02.2 | PER-02 Daniel Torres | Multi-contract obligation comparison for procurement decision | JTBD-02.3 | 4 |
| JRN-03.1 | PER-03 Jordan Kim | Technical spec lookup to unblock a time-sensitive coding decision | JTBD-03.1, JTBD-03.3 | 5 |
| JRN-03.2 | PER-03 Jordan Kim | Multi-document iterative session across API doc, ADR, and requirements spec | JTBD-03.2, JTBD-03.3 | 5 |

---

## PER-01: Maya Patel — Research Analyst

---

### JRN-01.1: Research PDF Batch Upload and Targeted Data Point Retrieval

**Persona:** PER-01 (Maya Patel — Research Analyst)

**Scenario:** Maya has just received a client brief requesting EV adoption statistics. She has a folder of five industry reports — each 60–100 pages — and needs to extract three specific data points and verify their source passages before noon. She opens the RAG Chatbot, uploads her report batch, and runs targeted factual queries against the indexed content.

**Related Jobs:** JTBD-01.1, JTBD-01.2

---

#### Journey Stages

| Stage | Action | Touchpoint | Thinking | Feeling | Pain Point | Opportunity |
|---|---|---|---|---|---|---|
| **1. Arrive & Orient** | Opens browser, navigates to the app, lands on the empty-state home screen | App home / empty state (F5) | "Let me get these reports in and find that EV growth stat before the standup." | Purposeful, slight time pressure | Has been burned by ChatGPT citing wrong figures before — instinctively cautious | Clear empty-state copy ("Upload a document to start") reassures her she's in the right place immediately |
| **2. Upload** | Drags five PDFs from her Downloads folder onto the upload zone; watches status indicators cycle from "Processing" to "Ready" | Upload zone (F0), Document library sidebar (F3) | "Is it reading all five? I need all of them indexed, not just the first one." | Focused, mildly anxious waiting for status | No visible per-document progress — unclear if a 90-page PDF is still processing or stuck | Per-document status chip (Indexing → Ready ✓) with estimated time remaining eliminates uncertainty |
| **3. Query** | Types "What EV adoption growth rate does the 2024 industry report cite?" and presses Enter | Chat input (F1, F5) | "Am I asking this the right way? Will it pull from my files or make something up?" | Cautious, curious | Past experience with AI tools giving plausible but fabricated statistics — needs a reason to trust this one | Answer appears within 8 s with a visible "Searching your 5 documents…" indicator that makes clear it's not guessing |
| **4. Verify Citation** | Reads the answer, then expands the citation panel to view the raw source passage and confirm document name + page reference | Source citation panel (F2), Chat bubble (F1) | "Is this exactly what the PDF says? I need to confirm before I put this in the deck." | Cautious → relieved when text matches | Without a direct quote and page number, she cannot act on the answer | Expandable citation block shows verbatim passage in a muted, read-only box — she can visually compare answer to source in the same screen |
| **5. Copy & Use** | Clicks "Copy answer + citation" and pastes into her draft slide deck | Copy utility (F8), external slide app | "I need the citation text too, not just the answer — I've had to retype page numbers before." | Relieved, efficient | Two-step copy (answer then citation separately) forces manual reformatting | Single "Copy with citation" action puts clean answer + source reference on clipboard, ready to paste |

---

#### Key Moments

- **Decision Point — Stage 2 (Upload):** If any document shows an error status or silently fails to index, Maya cannot trust that all her sources were searched. A missed document = a missed data point = a wrong answer in a client deck. This is a go/no-go moment for the session.
- **Risk of Abandonment — Stage 3 (Query):** If the first answer arrives without a clear citation or shows signs of hallucination (vague, unattributable stat), Maya will stop using the tool and revert to manual PDF scanning. The first answer is the trust-building moment.
- **Delight Opportunity — Stage 4 (Verify):** When Maya expands the citation and sees the exact verbatim passage from the report — clearly labeled with document name and page number — that moment replaces 30 minutes of manual scanning. This is the product's highest-value instant.

#### Success Outcome

Maya locates a specific data point and verifies its source passage in under 3 minutes, with zero risk of misattribution — directly satisfying JTBD-01.1 success measure ("< 3 min vs. 30–60 min manual scan") and JTBD-01.2 success measure ("zero hallucinated deliverable answers").

#### Feature Touchpoints

| Stage | Features |
|---|---|
| Arrive & Orient | F5 (Premium Responsive UI) |
| Upload | F0 (Document Upload & Ingestion), F3 (Document Library Management) |
| Query | F1 (RAG-Powered QA), F5 (Premium Responsive UI) |
| Verify Citation | F2 (Source Citations), F1 |
| Copy & Use | F8 (Export & Copy Utilities), F2 |

---

### JRN-01.2: Cross-Document Comparison and Export to Client Deliverable

**Persona:** PER-01 (Maya Patel — Research Analyst)

**Scenario:** Maya is working on a synthesis section of a market report comparing EV adoption figures across five industry sources from different years. She needs to identify whether reports agree or contradict each other on a key data point, then transfer her findings — with citations — into a Google Slides deck for her manager's review.

**Related Jobs:** JTBD-01.3, JTBD-01.4

---

#### Journey Stages

| Stage | Action | Touchpoint | Thinking | Feeling | Pain Point | Opportunity |
|---|---|---|---|---|---|---|
| **1. Session Setup** | Confirms all five reports are indexed in the document library sidebar; notes which are "Ready" | Document library sidebar (F3), App home (F5) | "I need all five in scope for this query — not just the most recently uploaded one." | Organized, methodical | No easy way to confirm a multi-document session is fully ready in other tools she has used | Document library shows file name, type, and status at a glance — she can verify completeness before asking anything |
| **2. Cross-Document Query** | Types "What EV adoption growth rates do the uploaded reports cite and do they agree?" and submits | Chat input (F1), Multi-doc retrieval engine (F6) | "Will it actually pull from all five, or just the top hit?" | Curious, slightly skeptical | Tools she's used before either only retrieve from one document or return a blended, unsourced summary | Answer attributes each data point to a named source file ("Report A cites 18%; Report C cites 12%") — contradiction is immediately visible |
| **3. Review Multi-Source Answer** | Reads the answer comparing figures, expands citations for two contradicting reports to read the raw passages | Source citation panel (F2), Multi-source answer (F6) | "Report A and C disagree — I need to verify both quotes before I write this up." | Alert, engaged | Two different cited passages require two expand actions — manageable but could cascade with more docs | Inline per-source citation chips allow expanding each source independently without navigating away from the answer |
| **4. Iterate with Follow-up** | Asks a follow-up: "Which report was published most recently?" and reads the session history to contextualize the earlier answer | Chat history (F4), Chat input (F1) | "I remember the earlier answer said 18% — I need to tie that to the 2024 publication." | Focused, efficient | Without scrollable chat history, she'd have to re-ask the first question | Scrollable chat transcript keeps all Q&A visible — she can reference the earlier cited answer without re-querying |
| **5. Export Session** | Clicks "Export transcript" to download Markdown; opens file, copies the two cited answers into her slide deck | Export utility (F8), external slide app | "I just need the two key answers with citations — the full export gives me more than I need, but it's quicker than copying manually." | Satisfied, slightly impatient | Markdown formatting may include artifacts that need cleaning before pasting into slides | Clean export with no extra whitespace or markdown noise; ideally a "copy this answer + citation" shortcut for single-answer exports |

---

#### Key Moments

- **Decision Point — Stage 2 (Cross-Document Query):** If the answer fails to clearly attribute data points to individual source documents, Maya loses the ability to distinguish contradiction from consensus — the entire research purpose of the session collapses.
- **Risk of Abandonment — Stage 3 (Review):** If expanding citations reveals the raw passage doesn't match the stated figure (e.g., the answer paraphrased incorrectly), Maya's trust in the tool breaks. She will add a manual verification step to every future session — defeating the time savings.
- **Delight Opportunity — Stage 5 (Export):** A single-click "copy with citation" on each answer turns a 20-minute formatting task into a 30-second workflow. This is when the product pays back the time investment of the session.

#### Success Outcome

Maya completes a 5-document cross-reference session without manually re-reading any source document, and transfers cited findings to her deliverable in under 30 seconds per answer — satisfying JTBD-01.3 and JTBD-01.4 success measures.

#### Feature Touchpoints

| Stage | Features |
|---|---|
| Session Setup | F3 (Document Library Management), F5 |
| Cross-Document Query | F1 (RAG-Powered QA), F6 (Multi-Document Context Retrieval) |
| Review Multi-Source Answer | F2 (Source Citations), F6 |
| Iterate with Follow-up | F4 (Session-Scoped Chat History), F1 |
| Export Session | F8 (Export & Copy Utilities) |

---

## PER-02: Daniel Torres — Legal & Contracts Professional

---

### JRN-02.1: Clause Location Under Negotiation Time Pressure

**Persona:** PER-02 (Daniel Torres — Legal & Contracts Professional)

**Scenario:** Daniel is 20 minutes from a vendor negotiation call. The counterparty has raised a question about the indemnification cap in the service agreement. He needs to pull the exact clause text with page reference in the next 5 minutes — without delegating to counsel or spending 20 minutes scanning the 72-page PDF.

**Related Jobs:** JTBD-02.1, JTBD-02.2

---

#### Journey Stages

| Stage | Action | Touchpoint | Thinking | Feeling | Pain Point | Opportunity |
|---|---|---|---|---|---|---|
| **1. Upload Contract** | Drags the vendor's service agreement PDF onto the upload zone; watches it transition to "Ready" | Upload zone (F0), Document library (F3) | "I need this indexed fast — I only have a few minutes before the call." | Urgent, focused | Upload + indexing for a 72-page document may feel slow when the clock is ticking | Ingestion progress bar with ETA ("~18 seconds remaining") makes the wait tolerable; fast indexing (< 30 s target per PRD) is essential here |
| **2. Query for Clause** | Types "What does the indemnification clause say and where is it in the document?" and submits | Chat input (F1, F5) | "I need the actual clause language, not a paraphrase. If this tool makes something up, I'm walking into the call with wrong information." | High-stakes, tense | He distrusts AI tools that paraphrase or summarize clauses — he has been burned before | Answer returns verbatim clause text — not a summary — within 8 seconds; clear label "Verbatim passage from document" signals this is a direct quote |
| **3. Verify Verbatim Text** | Expands citation panel, reads the raw passage, confirms document name and page number match his expectation | Source citation panel (F2), Chat bubble (F1) | "Page 34, Section 9.2 — that matches what I remembered. Now I can cite this in the call." | Relieved, confident | If citation shows a paraphrase instead of verbatim text, he has to abandon the tool and search manually | Citation block shows read-only verbatim source text in a visually distinct style — he can screenshot or copy the page reference for the call |
| **4. "Not Found" Test** | Asks "Does this contract contain a data breach notification clause?" — a clause he suspects is absent | Chat input (F1), Confidence layer (F7) | "I half-expect this isn't in the contract — but I need to be certain before I tell the counterparty it's not there." | Cautious, deliberate | General AI chatbots fabricate plausible clause language when the clause is absent — the exact failure mode that exposes him to liability | System returns explicit "Not found in your uploaded documents" message — not a fabricated clause — with confirmation of which document was searched |
| **5. Act on Results** | Copies the indemnification clause text and page reference for use during the call; notes the absence of the breach clause | Copy utility (F8), External notes app | "I have what I need. Indemnification is on page 34, and there is no breach notification clause — I can state that with confidence." | Confident, prepared | Copying only the answer text misses the page number he needs — requires two actions | Copy action captures clause text + section/page reference in a single action, paste-ready for his call notes |

---

#### Key Moments

- **Decision Point — Stage 3 (Verify):** Daniel's threshold for trust is high. If the citation panel shows a summary instead of the verbatim contract language, he will reject the tool's output entirely and fall back to Ctrl-F in Adobe Acrobat.
- **Critical Risk — Stage 4 (Not Found):** If the system returns a plausible but fabricated clause when the obligation is absent, Daniel may act on it in a negotiation — creating direct legal and financial exposure for his firm. This is the product's highest-stakes failure mode.
- **Delight Opportunity — Stage 3 (Verify):** The moment Daniel reads the exact verbatim text with a page number — without opening the PDF — and it matches what he expected, the product has proved its value for legal-grade verification. This is the conversion moment for this persona.

#### Success Outcome

Daniel locates and verifies the indemnification clause with verbatim text in under 2 minutes, and receives explicit confirmation that the breach notification clause is absent — satisfying JTBD-02.1 and JTBD-02.2 success measures with zero risk of acting on hallucinated content.

#### Feature Touchpoints

| Stage | Features |
|---|---|
| Upload Contract | F0 (Document Upload & Ingestion), F3 |
| Query for Clause | F1 (RAG-Powered QA), F5 |
| Verify Verbatim Text | F2 (Source Citations), F1 |
| "Not Found" Test | F7 (Answer Confidence & Relevance Feedback), F1 |
| Act on Results | F8 (Export & Copy Utilities) |

---

### JRN-02.2: Multi-Contract Obligation Comparison for Procurement Decision

**Persona:** PER-02 (Daniel Torres — Legal & Contracts Professional)

**Scenario:** Daniel is evaluating three vendor contracts for a procurement decision. He needs to compare how each vendor's agreement handles limitation of liability — the wording differs across all three — and produce a written summary for the procurement committee in under 30 minutes. He uploads all three contracts and queries across them simultaneously.

**Related Jobs:** JTBD-02.3

---

#### Journey Stages

| Stage | Action | Touchpoint | Thinking | Feeling | Pain Point | Opportunity |
|---|---|---|---|---|---|---|
| **1. Upload Three Contracts** | Drags three vendor contract PDFs into the upload zone sequentially; confirms all three show "Ready" status in the sidebar | Upload zone (F0), Document library (F3) | "I need all three indexed and searchable before I start — I don't want to miss a contract that's still processing." | Methodical, watchful | No clear confirmation that a multi-document session is fully ready before querying — risk of querying with only 2 of 3 indexed | Document library shows a consolidated "All 3 documents ready" state or clear per-doc status, preventing premature querying |
| **2. Cross-Contract Query** | Types "What does each contract say about limitation of liability?" and submits | Chat input (F1), Multi-doc retrieval (F6) | "I need each vendor's exact wording, not a synthesized summary. Which contracts even have this clause?" | Alert, analytical | Tools that synthesize a blended answer without attributing to individual contracts are useless for his comparison work | Answer is structured per document: "Vendor A (Contract-A.pdf): '…'; Vendor B (Contract-B.pdf): '…'" — per-source attribution is the core value |
| **3. Expand & Verify Per Contract** | Expands citation for each of the three vendor clauses; reads verbatim text; notes substantive differences in caps and carve-outs | Source citation panel (F2), Multi-source answer (F6) | "Vendor B caps at 1× fees; Vendor C has no cap — that's a material difference I need in the summary." | Engaged, analytical | Expanding three separate citation panels requires multiple interactions — acceptable but could be simplified | Side-by-side or collapsible per-source citation blocks reduce navigation overhead in multi-contract comparisons |
| **4. Produce Summary** | Copies the three cited passages (with document names) and pastes into a comparison table in Word; exports session transcript for the audit trail | Copy utility (F8), Export (F8), external Word doc | "I need the exact wording in my comparison table — not my paraphrase of their paraphrase." | Satisfied, efficient | Copying three separate answers and citations requires three separate copy actions | Bulk "copy all answers in session" or "export with citations" produces a ready-to-use comparison draft |

---

#### Key Moments

- **Decision Point — Stage 2 (Cross-Contract Query):** If the answer blends language from multiple contracts without clear per-document attribution, Daniel cannot determine which obligations belong to which vendor. The comparison is unusable.
- **Risk of Abandonment — Stage 1 (Upload):** If one contract shows an error or silent failure, Daniel will distrust the completeness of all subsequent answers. Clear, explicit status per document is a prerequisite for this persona.
- **Delight Opportunity — Stage 4 (Produce Summary):** When Daniel copies the three per-source citations into his comparison table in under 5 minutes — compared to 1–2 hours of manual review — the ROI of the tool is immediate and concrete.

#### Success Outcome

Daniel produces a written summary of the limitation-of-liability wording across three contracts in under 20 minutes, with each clause attributed to its source document by name — satisfying JTBD-02.3 success measure.

#### Feature Touchpoints

| Stage | Features |
|---|---|
| Upload Three Contracts | F0 (Document Upload & Ingestion), F3 (Document Library Management) |
| Cross-Contract Query | F1 (RAG-Powered QA), F6 (Multi-Document Context Retrieval) |
| Expand & Verify Per Contract | F2 (Source Citations), F6 |
| Produce Summary | F8 (Export & Copy Utilities) |

---

## PER-03: Jordan Kim — Technical Knowledge Worker

---

### JRN-03.1: Technical Spec Lookup to Unblock a Time-Sensitive Coding Decision

**Persona:** PER-03 (Jordan Kim — Technical Knowledge Worker)

**Scenario:** Jordan is mid-sprint on an API integration. Their team's client is hitting 429 errors and Jordan needs to find the exact rate limit for the `/v2/ingest` endpoint in the vendor API reference — a 200-page PDF. They have 10 minutes before a standup. They drag-drop the spec into the chatbot and start querying keyboard-only.

**Related Jobs:** JTBD-03.1, JTBD-03.3

---

#### Journey Stages

| Stage | Action | Touchpoint | Thinking | Feeling | Pain Point | Opportunity |
|---|---|---|---|---|---|---|
| **1. Upload Spec (Drag & Drop)** | Drag-drops the vendor API reference PDF onto the upload zone without touching the mouse for anything else; watches status | Upload zone (F0, F5), Document library (F3) | "30 seconds to indexed — I've used this before. If it takes longer, I'll just Ctrl-F in Acrobat instead." | Impatient, focused | Upload UX that requires mouse navigation through file pickers adds friction before the query even starts | Native drag-and-drop lands focus back on the chat input field automatically — keyboard flow resumes with zero mouse use |
| **2. Query via Keyboard** | Types the question ("What is the rate limit on the /v2/ingest endpoint?") and presses Enter to submit — no mouse click | Chat input (F1, F5), Enter-to-submit | "I don't want to reach for the mouse to click Send — that breaks my focus." | In flow, efficient | Tools that require a click to submit a query — or worse, a form button Tab-over — force an unnecessary context switch | Enter key submits; focus remains in input for the follow-up query immediately after the response renders |
| **3. Receive & Scan Answer** | Reads the cited answer: "100 requests per minute per API key (Section 4.2, Rate Limits)" | Chat bubble (F1), Source citation (F2) | "Is this the version-specific limit or the general one? I need to see the actual passage to be sure." | Alert, slightly skeptical | An LLM answering from training data about this API would give the previous version's limits — exactly wrong for the integration | Citation clearly states the document name ("vendor-api-v2.3.pdf") + section — Jordan sees it's from the exact version they uploaded, not general knowledge |
| **4. Expand Citation to Verify** | Tabs to the citation expand control, presses Enter to open it, reads the verbatim passage from Section 4.2 | Source citation panel (F2, F5), keyboard navigation | "100 req/min — confirmed. Good. Now I need the burst limit too." | Confident, relieved | Citation panel that requires mouse click to expand breaks keyboard-first flow | Citation expand is a Tab-reachable, Enter-activatable element — Jordan never touches the mouse |
| **5. Follow-up Query** | Types "Is there a burst limit mentioned in the same section?" and presses Enter; reads the answer and citation | Chat input (F1), Chat history (F4) | "Good — 200 req burst for 10s. I have everything I need. Let me send this to the team." | Satisfied, efficient | Having to re-scroll up to confirm the first answer while writing the follow-up breaks the read-compare loop | Two adjacent chat bubbles with their citations let Jordan compare rate limit and burst limit answers side by side without scrolling |

---

#### Key Moments

- **Decision Point — Stage 3 (Receive Answer):** Jordan will immediately spot if the answer reflects general API knowledge rather than the specific document version. An incorrect version reference means the tool is less useful than their LLM of choice — they'll abandon it.
- **Risk of Abandonment — Stage 2 (Query):** If pressing Enter doesn't submit (e.g., Enter creates a newline), Jordan will mentally write off the tool as a "mouse-required" tool and deprioritize it. This is a make-or-break keyboard UX moment.
- **Delight Opportunity — Stage 4 (Expand Citation):** When Jordan tabs to the citation, hits Enter, and reads the verbatim API section — entirely without a mouse — the product has proven itself as a genuinely keyboard-first tool. This is the emotional peak for this persona.

#### Success Outcome

Jordan uploads the API spec and receives a first cited answer within 60 seconds, grounded in the exact document version uploaded — not general training data — satisfying JTBD-03.1 success measure. All interactions are completed keyboard-only, satisfying JTBD-03.3.

#### Feature Touchpoints

| Stage | Features |
|---|---|
| Upload Spec | F0 (Document Upload & Ingestion), F5 (Premium Responsive UI) |
| Query via Keyboard | F1 (RAG-Powered QA), F5 |
| Receive & Scan Answer | F1, F2 (Source Citations) |
| Expand Citation | F2, F5 |
| Follow-up Query | F1, F4 (Session-Scoped Chat History) |

---

### JRN-03.2: Multi-Document Iterative Session Across API Doc, ADR, and Requirements Spec

**Persona:** PER-03 (Jordan Kim — Technical Knowledge Worker)

**Scenario:** Jordan is designing a new service integration. They need to reconcile three documents: the vendor API reference, an internal architecture decision record (ADR), and the product requirements spec. They upload all three and use the chatbot iteratively over a 2-hour work session to answer a series of architectural questions — referencing earlier answers as they go.

**Related Jobs:** JTBD-03.2, JTBD-03.3

---

#### Journey Stages

| Stage | Action | Touchpoint | Thinking | Feeling | Pain Point | Opportunity |
|---|---|---|---|---|---|---|
| **1. Load Multi-Document Session** | Uploads three documents (API ref, ADR, requirements spec); confirms all three show "Ready" in the document library | Upload zone (F0), Document library (F3, F5) | "I need all three searchable at once — if I have to query them separately I might as well open tabs." | Focused, methodical | Uploading three documents is three drag-and-drop interactions — acceptable, but the session setup cost must pay off quickly | Document library confirmation ("3 documents ready — your questions will search all of them") sets expectations correctly for cross-document queries |
| **2. First Cross-Document Query** | Asks "Does the ADR decision for async processing conflict with the rate limits in the API reference?" and reviews the multi-source answer | Chat input (F1), Multi-doc retrieval (F6) | "This is the question that would take me 30 minutes to answer manually by reading both docs side-by-side." | Curious, engaged | The answer might blend content from both documents without clear attribution — forcing manual cross-check | Answer cites ADR section and API reference section separately, showing the relevant excerpts; Jordan can see the conflict or alignment at a glance |
| **3. Iterative Follow-up Questions** | Asks 4–5 follow-up questions over the next 30 minutes; scrolls up to re-read earlier answers for context | Chat history (F4), Chat input (F1) | "I need to see what I found 20 minutes ago about the payload size limit — without re-asking." | In flow, productive | Chat history that doesn't persist, or that loses citations on scroll, forces re-queries and breaks concentration | Full chat history with all cited answers scrollable — no pagination, no refresh-required — keeps the entire session context available |
| **4. Mid-Session Document Swap** | Removes the v2.3 API reference from the library and uploads the v2.4 version that just became available | Document library delete + upload (F3, F0) | "I don't want the old version polluting future answers — but I don't want to lose my chat history either." | Careful, precise | Removing and re-adding a document in other tools clears the entire session state — destroying the conversation history | Document library supports add/remove of individual documents without resetting chat history — Jordan's prior answers remain visible |
| **5. Session Wrap & Copy** | Copies two key answers (with citations) to a Slack message to share architectural findings with the team | Copy utility (F8), Slack | "These two findings are the ones my team needs — I don't want to dump the whole transcript on them." | Satisfied, efficient | Exporting the full transcript produces too much noise for a Slack post; per-answer copy is the right granularity | Per-answer "Copy answer + citation" button (keyboard accessible) captures exactly what Jordan needs for their Slack message |

---

#### Key Moments

- **Decision Point — Stage 4 (Document Swap):** If removing and re-uploading a document resets the chat history, Jordan loses the context of the entire 30-minute session. This is a catastrophic loss-of-state scenario that would make the tool unusable for iterative deep-work sessions.
- **Risk of Abandonment — Stage 3 (Iterative Follow-up):** If chat history doesn't scroll cleanly or earlier citations disappear on scroll-up, Jordan will start copy-pasting answers into a notes document as a workaround — defeating the session-based workflow entirely.
- **Delight Opportunity — Stage 2 (First Cross-Document Query):** When the first multi-document answer surfaces a genuine conflict between the ADR and the API spec — in seconds, with both source citations side by side — Jordan experiences the product's signature value: a research shortcut that previously didn't exist.

#### Success Outcome

Jordan completes 10+ questions across three documents in a single multi-hour session with full chat history preserved, a mid-session document swap with no context loss, and all interactions keyboard-accessible — satisfying JTBD-03.2 and JTBD-03.3 success measures.

#### Feature Touchpoints

| Stage | Features |
|---|---|
| Load Multi-Document Session | F0 (Document Upload & Ingestion), F3 (Document Library Management), F5 |
| First Cross-Document Query | F1 (RAG-Powered QA), F6 (Multi-Document Context Retrieval) |
| Iterative Follow-up Questions | F4 (Session-Scoped Chat History), F1 |
| Mid-Session Document Swap | F3, F0 |
| Session Wrap & Copy | F8 (Export & Copy Utilities), F5 |

---

## Cross-Journey Patterns

### Common Pain Points Across Personas

| Pattern | Appears In | Description | Shared Opportunity |
|---|---|---|---|
| **Hallucination distrust** | JRN-01.1, JRN-01.2, JRN-02.1, JRN-03.1 | All three personas have been burned by general AI tools generating plausible-but-wrong content. Every first interaction with a new tool carries this distrust. | The first answer must include a clearly labeled, verbatim citation. This single UX decision dissolves the primary adoption barrier for all three personas. |
| **Multi-document attribution** | JRN-01.2, JRN-02.2, JRN-03.2 | When queries span multiple documents, per-source attribution is not a nice-to-have — it is the entire point of the multi-document feature. Blended, unsourced answers are worse than useless. | Every multi-document answer must present per-source citations with document name, not a synthesized summary without attribution. |
| **Upload status anxiety** | JRN-01.1, JRN-02.2, JRN-03.2 | All three personas upload multiple documents before querying. Without clear per-document "Ready" status, they do not know whether their query is searching all intended sources. | A document library with explicit per-document ingestion status (and a session-level "all ready" confirmation) is a prerequisite for multi-document confidence. |
| **Citation as verification gate** | JRN-01.1, JRN-01.2, JRN-02.1, JRN-02.2, JRN-03.1 | Every persona treats the expandable citation as a mandatory verification step before acting on an answer. The citation is not supplementary — it is the workflow. | Citation expand must be fast (single click or keyboard action), present verbatim text (not a paraphrase), and include document name + location reference at minimum. |
| **Copy/export friction** | JRN-01.2, JRN-02.2, JRN-03.2 | All three personas need to transfer findings out of the tool (slides, Word, Slack). The copy-and-citation workflow must be a single atomic action to avoid reformatting overhead. | Per-answer "Copy answer + citation" as a first-class button (and keyboard shortcut) captures both the finding and its provenance in one interaction. |

### Convergence Points

- **F0 + F3 (Upload + Library)** is the universal session entry point — all six journeys begin here. Investment in upload UX and status clarity has multiplicative impact.
- **F2 (Source Citations)** is the single feature that appears as a key moment in every journey for every persona — it is the product's core trust mechanism.
- **F1 (RAG QA)** is used in every stage across all journeys; latency and answer quality directly determine session success or abandonment.

### Divergence Points

- **F7 (Confidence / "Not Found")** is critical for PER-02 Daniel but secondary for Maya and Jordan — Daniel's use case (legal contract review) carries the highest cost of a false positive.
- **F5 (Keyboard Navigation)** is existentially important for PER-03 Jordan but merely a nice-to-have for Maya and Daniel.
- **F8 (Export)** is most workflow-critical for PER-01 Maya (copying to client deliverables is a daily task) and less urgent for Daniel and Jordan.

---

## Journey-to-JTBD Traceability

| JRN-ID | Stage | JTBD-ID | Expected Outcome |
|---|---|---|---|
| JRN-01.1 | Upload | JTBD-01.1 | All research PDFs indexed and searchable within session |
| JRN-01.1 | Query | JTBD-01.1 | Cited answer returned within 8 s, grounded exclusively in uploaded documents |
| JRN-01.1 | Verify Citation | JTBD-01.2 | Verbatim source passage with document name and page reference visible inline |
| JRN-01.1 | Copy & Use | JTBD-01.4 | Answer + citation copied in a single action, clean and paste-ready |
| JRN-01.2 | Cross-Document Query | JTBD-01.3 | Each data point attributed to its named source document |
| JRN-01.2 | Review Multi-Source Answer | JTBD-01.3 | Contradictions across sources are visible without opening any PDF |
| JRN-01.2 | Export Session | JTBD-01.4 | Cited answer transferred to external deliverable in under 30 seconds |
| JRN-02.1 | Query for Clause | JTBD-02.1 | Verbatim clause text returned with page/section reference within 8 s |
| JRN-02.1 | Verify Verbatim Text | JTBD-02.1 | Expandable citation shows read-only raw passage — not a paraphrase |
| JRN-02.1 | "Not Found" Test | JTBD-02.2 | Explicit "not found" response returned — no fabricated clause language generated |
| JRN-02.2 | Cross-Contract Query | JTBD-02.3 | Per-contract attribution identifies which vendor agreement contains each obligation |
| JRN-02.2 | Expand & Verify Per Contract | JTBD-02.3 | Three separate verbatim citations confirm wording differences across vendor contracts |
| JRN-03.1 | Upload Spec | JTBD-03.1 | Technical PDF indexed within 30 s; first query possible within 60 s of upload |
| JRN-03.1 | Query via Keyboard | JTBD-03.3 | Enter key submits query; no mouse interaction required |
| JRN-03.1 | Receive & Scan Answer | JTBD-03.1 | Answer cites specific document version uploaded — not general training-data knowledge |
| JRN-03.1 | Expand Citation | JTBD-03.3 | Citation expand is Tab-reachable and Enter-activatable — keyboard-only completion |
| JRN-03.2 | First Cross-Document Query | JTBD-03.2 | Multi-source answer cites ADR and API ref separately; conflict is immediately visible |
| JRN-03.2 | Iterative Follow-up Questions | JTBD-03.2 | Full chat history with citations scrollable throughout session — no refresh required |
| JRN-03.2 | Mid-Session Document Swap | JTBD-03.2 | Individual document removed/added without resetting chat history |
| JRN-03.2 | Session Wrap & Copy | JTBD-03.3 | Per-answer copy (keyboard accessible) captures answer + citation without mouse |

---

*Document generated: 2026-05-13 | RAGChatbot JOURNEYS v1.0*
