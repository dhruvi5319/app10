# Persona Document: RAG Chatbot

| Field | Value |
|---|---|
| **Product Name** | RAG Chatbot |
| **Project Acronym** | RAGChatbot |
| **Version** | 1.0 |
| **Date** | 2026-05-13 |
| **Related PRD** | PRD-RAGChatbot.md v1.0 |
| **Status** | Draft |

---

## Persona Summary

| ID | Name | Role | Primary Goal |
|---|---|---|---|
| PER-01 | Maya Patel | Research Analyst | Extract precise answers from dense research papers and reports without wading through hundreds of pages |
| PER-02 | Daniel Torres | Legal & Contracts Professional | Verify specific clauses and obligations across multiple contract documents with full traceability |
| PER-03 | Jordan Kim | Technical Knowledge Worker | Quickly locate answers from internal manuals, specs, or documentation to unblock day-to-day decisions |

---

## PER-01: Maya Patel — Research Analyst

**Role & Context:**
Maya is a mid-level research analyst at a market research firm, responsible for synthesizing findings from academic papers, industry reports, and government data releases. She regularly works with 5–15 documents per project cycle, many exceeding 80 pages, and must produce accurate summaries and citations for her team's deliverables. She works from a laptop at her desk, uses a browser for most tasks, and is comfortable with modern web tools but not with developer-facing interfaces. Maya's manager holds her accountable for citation accuracy — a misquoted source in a client report is a serious professional risk.

**Goals:**
- Find specific data points, statistics, or conclusions in large research documents without reading them end-to-end (F1, F2)
- Verify that every answer she acts on is traceable to the exact passage in the source document (F2)
- Work across multiple related reports in a single session without losing context (F6, F3)
- Quickly export or copy Q&A results into her drafts and slide decks (F8)

**Pain Points** *(traced to PRD Section 2)*:
- General-purpose AI tools (ChatGPT, Copilot) blend document content with training data, making it impossible to trust whether a statistic came from *her* report or the model's prior knowledge — **Hallucination risk**
- Manually scanning 80-page PDFs to find a single data point costs 30–60 minutes per query — **Manual search burden**
- No chat tool she has tried shows exactly which paragraph an answer came from, forcing her to re-read the document to verify — **No source traceability**
- Multi-turn conversations about the same document set lose context between sessions — **Context loss**

**Technical Expertise:** Intermediate — fluent with web applications, spreadsheet tools, and cloud storage; avoids command-line or developer tools; expects consumer-grade UX polish.

**Top Tasks:**
1. Upload a batch of research PDFs and confirm they've been indexed successfully (F0, F3) — *daily, critical*
2. Ask targeted factual questions ("What growth rate does the 2024 report cite for EV adoption?") and review the cited passage (F1, F2) — *daily, critical*
3. Cross-reference an answer across multiple uploaded reports to spot contradictions (F6) — *several times per week, high*
4. Copy a cited answer directly into a client deliverable draft (F8) — *daily, medium*
5. Delete stale reports from the session library to keep context clean (F3) — *as needed, low*

**Success Criteria:**
- Finds a specific answer and verifies its source passage in under 3 minutes (vs. current 30–60 min manual search)
- Zero answers adopted into deliverables that later turn out to be hallucinated or misattributed
- Completes a 5-document research session without needing to re-read any source document manually
- Task completion: uploads first document and receives a cited answer in under 5 minutes on first use (PRD Section 7 usability target)

---

## PER-02: Daniel Torres — Legal & Contracts Professional

**Role & Context:**
Daniel is a contracts manager at a mid-size professional services firm, responsible for reviewing vendor agreements, NDAs, SOWs, and compliance documents. He is not a licensed attorney but works closely with legal counsel and must locate specific clauses, deadlines, and obligations quickly — often under time pressure during negotiations or audits. He works on a desktop with dual monitors and handles 20–40 documents per quarter. Precision is non-negotiable: an overlooked liability clause or a missed renewal deadline has direct financial consequences. Daniel is proficient with Word, PDF readers, and enterprise document tools, but distrusts any AI output he cannot verify against the actual document.

**Goals:**
- Locate specific clauses (indemnification, termination, SLA thresholds) in lengthy contracts without manual ctrl-F searches across 50+ pages (F1, F2)
- Confirm every extracted clause with a direct quote and page reference before acting on it (F2)
- Compare how the same obligation is worded across multiple vendor contracts in one session (F6, F3)
- Trust that the chatbot will explicitly say "not found" rather than generate a plausible-but-wrong answer (F7, F1 fallback)

**Pain Points** *(traced to PRD Section 2)*:
- General AI chatbots fabricate clause language when a contract doesn't contain what he's looking for — **Hallucination risk** — the exact failure mode that would expose his firm to legal liability
- ctrl-F search misses paraphrased or context-dependent obligations buried in exhibit language — **Manual search burden**
- Tools that surface an answer without a direct quote are useless for audit trails — **No source traceability**
- Re-uploading the same contract set to start a new chat wastes time and kills flow — **Context loss**

**Technical Expertise:** Intermediate-advanced — power user of Microsoft Office, Adobe Acrobat, and enterprise SaaS tools; comfortable with structured workflows; expects reliability and predictability over novelty.

**Top Tasks:**
1. Upload a set of vendor contracts (PDF/DOCX) and confirm all are indexed and ready (F0, F3) — *per contract review cycle, critical*
2. Query for a specific clause type and read the verbatim cited passage to verify it (F1, F2) — *multiple times per document, critical*
3. Ask whether a particular obligation appears in any of the uploaded contracts and see which documents contain it (F6) — *per negotiation session, high*
4. Manage session document library — add new contract versions, remove superseded ones (F3) — *as needed, medium*
5. Note when the chatbot is uncertain and decide whether to manually review the source (F7) — *as needed, medium*

**Success Criteria:**
- Locates and verifies a clause with exact quoted text in under 2 minutes (vs. current 15–25 min manual review)
- Produces a written summary of 5 key obligations across 3 contracts in under 20 minutes
- Zero instances of acting on an AI-generated clause that does not exist verbatim in the document
- Explicitly receives "not found" responses (not hallucinated alternatives) when a clause is absent from all uploaded documents

---

## PER-03: Jordan Kim — Technical Knowledge Worker

**Role & Context:**
Jordan is a software engineer or technical team lead who frequently needs to extract answers from internal technical documentation, API specs, architecture decision records, product manuals, or vendor datasheets. Their documents live across Confluence, PDFs, and Word docs — rarely well-indexed, often outdated, and always too long to read in full when a deadline is pressing. Jordan typically uploads a handful of technical documents at the start of a task and interrogates them conversationally to get unblocked fast. They are highly tech-savvy, care about response quality and accuracy, and will notice immediately if an answer contradicts the source document. They use keyboard shortcuts habitually and prefer minimal friction in tool interactions.

**Goals:**
- Ask natural language questions about a technical spec or manual and get a precise, document-backed answer without digging through 200-page documentation (F1, F2)
- Keep a multi-document session active while iterating on a problem — referencing an API doc, an architecture guide, and a requirements spec simultaneously (F6, F3, F4)
- Verify that answers haven't drifted beyond what the document actually says — especially important for API behavior and system constraints (F2, F7)
- Interact efficiently via keyboard (Enter to submit, tab navigation) with minimal mouse use (F5)

**Pain Points** *(traced to PRD Section 2)*:
- LLMs answering from training data give outdated API behavior descriptions that contradict the version-specific doc in front of them — **Hallucination risk**
- Ctrl-F through a 200-page PDF to find a config parameter wastes 10–15 minutes per lookup — **Manual search burden**
- Answers without source references require Jordan to re-read the doc to confirm — doubles the time — **No source traceability**
- Losing chat context when switching between document sets mid-session breaks flow — **Context loss**

**Technical Expertise:** High — full-time developer comfortable with web apps, APIs, and developer tooling; expects responsive, snappy UX; values keyboard-first interaction and clean UI; will immediately identify if a response is hallucinated.

**Top Tasks:**
1. Drag-and-drop a PDF spec or DOCX manual and start querying within 30 seconds of upload (F0, F5) — *multiple times per day, critical*
2. Ask targeted technical questions ("What is the rate limit on the /v2/ingest endpoint?") and verify the cited passage (F1, F2) — *multiple times per day, critical*
3. Scroll back through the session chat to re-read earlier answers without re-asking (F4) — *frequently, high*
4. Add or remove specific document versions during a session (e.g., swap v2.1 spec for v2.3) (F3) — *as needed, medium*
5. Export or copy a Q&A exchange into a team Slack message or ticket description (F8) — *as needed, low*

**Success Criteria:**
- Uploads a document and receives a first cited answer in under 60 seconds
- Answers reflect the exact version of the documentation uploaded, not general training data behavior
- Can complete 10+ questions in a session without UI friction (keyboard-first, no extra clicks)
- Chat history stays intact throughout a multi-hour work session without page refresh (F4)

---

## Persona Relationships

| Interaction | PER-01 Maya | PER-02 Daniel | PER-03 Jordan |
|---|---|---|---|
| **PER-01 Maya** | — | Occasionally collaborates; Maya's research may inform contracts Daniel reviews | Rarely interact directly |
| **PER-02 Daniel** | Receives research reports Maya synthesizes | — | May request Jordan pull technical specs relevant to contract obligations |
| **PER-03 Jordan** | Rarely interact directly | Provides technical documentation to inform contract technical annexes | — |

> **Note:** All three personas use the product independently and in single-user sessions (v1 scope). They do not share document libraries or sessions. The relationship table reflects organizational context, not in-product collaboration.

---

## Feature-Persona Matrix

| Feature | Description | PER-01 Maya | PER-02 Daniel | PER-03 Jordan |
|---|---|---|---|---|
| **F0** | Document Upload & Ingestion | Primary | Primary | Primary |
| **F1** | RAG-Powered Question Answering | Primary | Primary | Primary |
| **F2** | Source Citations | Primary | Primary | Primary |
| **F3** | Document Library Management | Secondary | Primary | Primary |
| **F4** | Session-Scoped Chat History | Secondary | Secondary | Primary |
| **F5** | Premium Responsive UI | Secondary | Secondary | Primary |
| **F6** | Multi-Document Context Retrieval | Primary | Primary | Secondary |
| **F7** | Answer Confidence & Relevance Feedback | Secondary | Primary | Secondary |
| **F8** | Export & Copy Utilities | Primary | Secondary | Secondary |

**Key:**
- **Primary** — This feature directly serves this persona's top tasks or pain points
- **Secondary** — This feature provides supporting value to this persona

### Matrix Notes

- **F0, F1, F2** are foundational for all three personas — they constitute the RAG core value proposition that each persona requires.
- **F2 (Source Citations)** is especially critical for PER-02 Daniel, where citation accuracy is a professional and legal requirement, not just a convenience.
- **F6 (Multi-Document)** is a Primary driver for PER-01 and PER-02 who routinely work across document sets; PER-03 uses it but in a lighter capacity.
- **F7 (Confidence Feedback)** maps most strongly to PER-02, who needs explicit "not found" signals rather than hedged answers to avoid acting on absent clauses.
- **F8 (Export)** is most valued by PER-01, who copies Q&A results into client deliverables as a regular workflow step.
- **F5 (UI)** is a strong Primary for PER-03 given their keyboard-first interaction style and high expectations for responsiveness and polish.

---

*Document generated: 2026-05-13 | RAGChatbot PERSONAS v1.0*
