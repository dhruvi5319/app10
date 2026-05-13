# Personas Document
## RAG Chatbot

| Field | Value |
|-------|-------|
| **Product** | RAG Chatbot |
| **Version** | 1.0 |
| **Date** | 2026-05-13 |
| **Status** | Active |
| **Related PRD** | PRD.md (v1.0) |
| **Derived From** | PRD §4 Target Users, §2 Problem Statement, §6 Features |

---

## Persona Summary

| ID | Name | Role | Primary Goal |
|----|------|------|--------------|
| PER-01 | Maya Okafor | Legal & Policy Analyst | Extract precise, citable answers from contract and regulatory documents without reading them cover-to-cover |
| PER-02 | Ethan Reyes | Research Scientist | Query dense academic papers and lab reports to surface specific data points and cross-document findings |
| PER-03 | Jordan Kim | Full-Stack Developer / Technical Evaluator | Evaluate and tune the RAG pipeline for accuracy, latency, and grounding compliance |

---

## PER-01: Maya Okafor

**Role:** Legal & Policy Analyst  
**Org Context:** Mid-size consulting firm; supports 4–6 client engagements simultaneously

---

**Role & Context**

Maya is a legal and policy analyst at a consulting firm, responsible for reviewing contracts, regulatory filings, compliance guidelines, and government policy documents on behalf of her clients. Her caseload routinely includes 20–40-page contracts and 100+-page policy documents, and she is often asked to answer very specific questions — "Does this agreement allow subcontracting?" or "What does Section 7 say about termination clauses?" — within hours. She works primarily on a laptop using a web browser, toggling between her firm's document management system, email, and general-purpose tools. She has no programming background and expects products to work immediately without setup. When a document Q&A tool gives her a wrong answer with no citation, she has no way to verify it and cannot risk presenting incorrect information to a client.

**Goals**

- Get a precise, citable answer to a document-specific question within seconds rather than scanning through dozens of pages (F1, F2)
- Trust that every answer is drawn exclusively from the document she uploaded — not from an AI's general knowledge (F1, F2)
- Quickly upload a new contract or policy PDF and start asking questions with minimal friction (F0)
- Manage multiple documents in one session to compare terms across contracts or cross-reference policy sections (F3)
- Scroll back through earlier Q&A exchanges within a session to reconstruct her research trail (F4)

**Pain Points**

- Manually reading 80-page documents to find a single clause wastes 1–3 hours per engagement (PRD §2: Information overload)
- General-purpose AI chatbots give confident but unreliable answers — she cannot present those to clients without verification (PRD §2: Hallucination risk)
- Current tools provide no citation or source passage, forcing her to manually confirm every AI-generated answer in the original document (PRD §2: Lack of traceability)
- Many document Q&A tools require IT setup, API keys, or technical configuration she cannot do herself (PRD §2: High-friction workflows)

**Technical Expertise**

Low-to-Intermediate — comfortable with web applications, cloud file storage (Google Drive, SharePoint), and email. Not comfortable with command-line tools, developer configuration, or API key management. Expects the product to work in a browser with zero setup on her end.

**Top Tasks**

1. Upload a PDF contract or policy document via drag-and-drop (daily, critical — F0)
2. Ask a precise natural-language question about a specific clause, date, obligation, or term (daily, critical — F1)
3. Expand a source citation to read the verbatim passage that supports an answer before using it in client deliverables (daily, critical — F2)
4. Remove a superseded document from the session when starting a new matter (as-needed, medium — F3)
5. Scroll back through earlier questions in the same session to reference a prior answer (as-needed, medium — F4)

**Success Criteria**

- Can upload a 50-page PDF and receive an accurate, cited answer to a clause-level question in under 30 seconds
- Every answer she presents to a client is traceable to a verbatim passage in the source document
- Zero hallucinated responses — if information is not in the document, the system explicitly says so
- Completes a full document review Q&A session without any setup steps or technical intervention

---

## PER-02: Ethan Reyes

**Role:** Research Scientist  
**Org Context:** University research lab; doctoral candidate / postdoc managing a literature review corpus

---

**Role & Context**

Ethan is a research scientist in a computational biology lab, currently writing his doctoral thesis. He manages a corpus of 30–50 academic papers and internal lab reports in PDF format, and he regularly needs to answer methodological questions — "What normalization method did Chen et al. use?" or "Which of these papers defines signal-to-noise ratio above 3.5?" — without re-reading each paper in full. He works at a desktop workstation with multiple browser tabs open, often alongside a reference manager (Zotero) and a writing tool. Ethan is technically literate: he understands how web applications work and can read API documentation, but he is not a software developer and does not run local servers. He has been burned by general LLMs confidently citing papers that either don't exist or don't say what the AI claimed, and he has zero tolerance for hallucination in scientific contexts.

**Goals**

- Upload a batch of research PDFs and ask cross-document questions to quickly surface specific data points, methods, or definitions (F0, F1)
- Trust that answers cite the exact paper and passage, so he can drop the citation directly into his thesis (F2)
- Upload up to 10 papers at once and manage which ones are active for a particular query session (F0, F3)
- Receive answers formatted in a way that includes key terms, numeric values, and structured lists where relevant — markdown rendering is essential (F1)
- Keep a running thread of questions and answers within a session so he can build a structured literature review incrementally (F4)

**Pain Points**

- Searching for a specific figure, definition, or method across 30 papers takes hours and breaks his writing flow (PRD §2: Information overload)
- General-purpose LLMs fabricate citations or misattribute findings — a fatal problem in scientific writing (PRD §2: Hallucination risk)
- Even when an AI gives a correct answer, he cannot determine which page or passage it came from, making proper academic citation impossible (PRD §2: Lack of traceability)
- He has tried developer-oriented RAG tools that require local setup — they are too time-consuming to configure for non-dev researchers (PRD §2: High-friction workflows)

**Technical Expertise**

Intermediate — comfortable with web applications, browser-based tools, and cloud storage. Understands concepts like vector search and embeddings at a high level but does not configure backends or run servers. Capable of reading structured error messages and retry prompts without confusion.

**Top Tasks**

1. Upload a batch of 5–10 research PDFs in a single drag-and-drop action (per session, critical — F0)
2. Ask a cross-document question ("Which of these papers uses CRISPR for gene editing?") and review the multi-citation answer (daily during literature review phase, critical — F1, F2)
3. Read the verbatim source excerpt in a citation card to verify the answer before including it in writing (daily, critical — F2)
4. Check the document panel to confirm a specific paper has been indexed before asking questions about it (as-needed, medium — F3)
5. Scroll back through the session thread to revisit an earlier finding without re-asking the question (as-needed, medium — F4)

**Success Criteria**

- Can upload 8 PDFs and receive a first cited answer within 45 seconds of session start
- Citations include page numbers and verbatim excerpts suitable for academic referencing
- The system refuses to answer (rather than hallucinating) when a question falls outside the uploaded papers
- Can build a complete 20-question literature review Q&A session without resetting the context

---

## PER-03: Jordan Kim

**Role:** Full-Stack Developer / Technical Evaluator  
**Org Context:** Independent developer or startup engineer evaluating the RAG Chatbot as a foundation for a client-facing product

---

**Role & Context**

Jordan is a full-stack developer exploring the RAG Chatbot as a technical foundation for a product they are building — a document Q&A feature embedded inside a SaaS application for one of their clients. Jordan runs the application locally, inspects network requests, reads server logs, and experiments with configuration parameters to understand retrieval quality, latency, and grounding behavior. They are evaluating whether the RAG pipeline can be tuned to meet their client's accuracy requirements before committing to building on top of it. Jordan works on a MacBook Pro with multiple terminal windows, VS Code, and a browser with DevTools open. They want to understand how the system behaves under edge cases: what happens when a question is asked with no documents uploaded, when a file is corrupt, when the top-k retrieval surface is insufficient.

**Goals**

- Validate that the RAG pipeline reliably grounds answers in uploaded documents and refuses out-of-document questions (F1, F7)
- Tune chunk size, overlap, top-k retrieval, and embedding model via configuration — without touching application code (F7)
- Observe the retrieval and citation behavior closely to assess whether the system surfaces the correct passages (F2)
- Stress-test the upload pipeline with various file formats, sizes, and edge cases to assess reliability (F0, F5)
- Confirm latency targets (< 5 seconds time-to-first-token, < 30 seconds for a 50-page PDF) are met in their target deployment environment (PRD §7)

**Pain Points**

- Many open-source RAG demos have hard-coded pipeline parameters, making evaluation and tuning impractical (PRD §2: High-friction workflows / F7)
- Retrieval quality is opaque — it is difficult to tell whether a wrong answer is a retrieval failure or an LLM grounding failure without seeing the retrieved chunks (PRD §2: Lack of traceability)
- Tools that handle errors silently make debugging difficult; Jordan needs clear error messages and server-side logs (F5)
- Hallucination in the LLM layer — even with RAG — is a hard risk to validate without systematic out-of-document testing (PRD §9 Risks)

**Technical Expertise**

High — proficient with Python, JavaScript/TypeScript, REST APIs, Docker, and terminal tools. Comfortable reading FastAPI server logs, inspecting ChromaDB state, and modifying `.env` configuration files. Understands embedding models, vector similarity search, and LLM prompt engineering at a practical level.

**Top Tasks**

1. Configure LLM provider, API key, embedding model, chunk size, and top-k via `.env` file before first run (setup, critical — F7)
2. Upload test documents across all supported formats (PDF, TXT, DOCX) and verify ingestion succeeds and fails gracefully for edge cases (evaluation, critical — F0, F5)
3. Ask a set of grounding-test questions — some answerable from documents, some not — to verify the refusal behavior and citation accuracy (evaluation, critical — F1, F2)
4. Inspect server startup logs to confirm configuration was picked up correctly and no secrets are exposed (setup/debug, medium — F7)
5. Measure upload-to-ready latency and time-to-first-token under representative load to validate NFRs (evaluation, medium — PRD §7)

**Success Criteria**

- All RAG pipeline parameters are configurable via `.env` with documented defaults — zero code changes required to tune the system
- Grounding compliance is 100%: every out-of-document question returns an explicit refusal, never a hallucinated answer
- Upload processing time for a 50-page PDF is consistently under 30 seconds in local deployment
- Server logs surface a clear configuration summary at startup and actionable error messages on failure
- The system handles corrupt, oversized, and unsupported files with clear error responses — no silent failures

---

## Persona Relationships

| Interaction | PER-01 Maya | PER-02 Ethan | PER-03 Jordan |
|-------------|-------------|--------------|---------------|
| **PER-01 Maya** | — | Both upload PDFs and rely on citations; Maya uses fewer documents per session | Maya is the end-user Jordan is building for; Jordan's pipeline tuning directly affects Maya's trust |
| **PER-02 Ethan** | Ethan uploads larger batches and needs cross-document queries; Maya focuses on single-document clause-level Q&A | — | Ethan represents the power-user accuracy bar Jordan needs to satisfy |
| **PER-03 Jordan** | Jordan configures and validates the system Maya will use | Jordan stress-tests the retrieval accuracy that Ethan depends on | — |

> In v1, these personas do not interact within the product (single-user session, no collaboration). The relationships describe how their needs inform each other at the product design level.

---

## Feature-Persona Matrix

| Feature | Description | PER-01 Maya | PER-02 Ethan | PER-03 Jordan |
|---------|-------------|:-----------:|:------------:|:-------------:|
| **F0** | Document Upload & Ingestion | Primary | Primary | Primary |
| **F1** | Chat Interface & Question Answering | Primary | Primary | Primary |
| **F2** | Source Citation & Passage Highlighting | Primary | Primary | Secondary |
| **F3** | Document Management Panel | Secondary | Primary | Secondary |
| **F4** | Session-Scoped Chat History | Secondary | Primary | None |
| **F5** | System Feedback & Error Handling | Primary | Secondary | Primary |
| **F6** | Responsive & Accessible UI | Primary | Secondary | None |
| **F7** | Configurable RAG Pipeline Settings | None | None | Primary |

**Key:** Primary — core to this persona's workflow; Secondary — used but not central; None — not relevant to this persona in v1

---

*Document generated: 2026-05-13*  
*Source: PRD.md v1.0 §2 Problem Statement, §4 Target Users, §6 Features, §7 NFRs, §8 Success Metrics*  
*Next downstream documents: UserStories, JTBD, UserJourneys*
