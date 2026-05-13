
---

## F01: Chat Interface & Question Answering

**Priority:** P0 — Critical MVP  
**PRD Reference:** §6 F1

**Description:** This feature provides the core interaction loop of the product: a chat UI where the user types natural language questions and receives answers grounded exclusively in their uploaded documents. The backend embeds the question, retrieves the top-k most relevant chunks from the vector store, constructs a strictly grounded LLM prompt, and streams or returns the generated answer. If no relevant context exists in the uploaded documents, the system explicitly refuses to answer rather than hallucinating.

---

### Terminology

- **User Turn:** A single user message in the chat thread.
- **Assistant Turn:** A single system-generated response in the chat thread.
- **Query Embedding:** The float vector produced by passing the user's question through the embedding model — used to search the vector store.
- **Retrieved Chunks:** The top-k chunks returned by the vector store's cosine similarity search against the query embedding.
- **Context Window:** The assembled block of retrieved chunk texts passed to the LLM as context.
- **Grounding Prompt:** The system prompt template that instructs the LLM to answer only from the provided context and to refuse if the answer is not present.
- **Refusal Response:** A canned system message returned when the LLM determines the answer cannot be found in the provided chunks (e.g., "I could not find an answer to your question in the uploaded documents.").
- **Streaming:** Optional token-by-token delivery of the LLM response to the frontend via SSE, reducing perceived latency.
- **Message ID:** A UUID assigned to each chat turn (both user and assistant) for citation and history tracking.

---

### Sub-features

- **F01.1 — Chat Message Input Bar:** A text area and send button at the bottom of the chat panel.
- **F01.2 — Message Thread Display:** A scrollable list of user and assistant messages with visual distinction (right vs. left aligned bubbles).
- **F01.3 — Markdown Rendering:** Render assistant message content as Markdown (bold, italic, code blocks, ordered/unordered lists, headings).
- **F01.4 — Query Embedding:** Embed the user's question using the configured embedding model.
- **F01.5 — Vector Store Retrieval:** Cosine similarity search for top-k chunks matching the question embedding.
- **F01.6 — Grounded LLM Prompt Construction:** Assemble system prompt + retrieved context + chat history (last N turns) + user question.
- **F01.7 — LLM Answer Generation:** Call the configured LLM API and receive a grounded answer with citation metadata.
- **F01.8 — Typing / Loading Indicator:** Show an animated typing indicator in the assistant bubble while the LLM generates.
- **F01.9 — Refusal Handling:** Surface explicit "not found in documents" message when LLM cannot answer from context.
- **F01.10 — Empty Query Guard:** Disable the send button and prevent submission when the input is blank or whitespace-only.

---

### Process

1. User types a question into the chat input bar.
2. **Client-side guard (F01.10):** If input is empty or whitespace-only, the send button remains disabled. No request is sent.
3. User presses Enter or clicks the send button.
4. Frontend immediately appends the user message to the thread (optimistic UI) with a timestamp and a generated `message_id`.
5. Frontend disables the input bar and displays the typing indicator in the assistant message slot.
6. Frontend sends `POST /api/chat/query` with `{ session_id, question, message_id }`.
7. **Backend validation:**
   - Verify `session_id` is valid UUID and exists in the session store.
   - Verify `question` is non-empty string after strip, ≤ 2000 characters.
   - Verify at least 1 document is indexed in this session. If none, return `NO_DOCUMENTS_INDEXED` error.
8. **Query embedding (F01.4):** Call embedding model with `question` text. Receive float vector.
9. **Retrieval (F01.5):** Query vector store for this session's collection, retrieve top-k chunks (default k=5) by cosine similarity. Include metadata: `document_id`, `filename`, `chunk_index`, `page_number`, `text`.
10. **Prompt construction (F01.6):**
    - System prompt: "You are a document Q&A assistant. Answer the user's question using ONLY the context provided below. If the answer cannot be found in the context, respond with exactly: 'I could not find an answer to your question in the uploaded documents.' Do not use any knowledge outside the provided context."
    - Context block: concatenated retrieved chunk texts, each labeled with `[Source: {filename}, chunk {chunk_index}]`.
    - History: last `CHAT_HISTORY_WINDOW` turns (default 6 — 3 user + 3 assistant) from the session's chat history.
    - User question appended last.
11. **LLM call (F01.7):** Send assembled prompt to the configured LLM with `temperature=TEMPERATURE` (default 0.2), `max_tokens=1500`. Include citation extraction instruction in system prompt.
12. **Response handling:**
    - If LLM returns a response containing the refusal phrase → mark response type `refusal`.
    - Otherwise → mark response type `answer`.
    - Extract citation references from the response (see F02 for citation structure).
13. Store both user turn and assistant turn in session chat history.
14. Return `{ message_id, answer_text, citations, response_type, retrieved_chunks }` to frontend.
15. Frontend removes typing indicator, appends assistant message to thread, auto-scrolls to bottom.
16. Frontend re-enables input bar and sets focus.

---

### Inputs

- `question` (string, required): The user's natural language question. Max 2000 characters after trim.
- `session_id` (string/UUID, required): In `X-Session-ID` header. Identifies session context.
- `message_id` (string/UUID, optional): Client-generated ID for the user turn. Server generates one if not provided.
- `TOP_K` (integer, from config): Number of chunks to retrieve. Default: 5. Range: 1–20.
- `TEMPERATURE` (float, from config): LLM sampling temperature. Default: 0.2. Range: 0.0–1.0.
- `CHAT_HISTORY_WINDOW` (integer, from config): Number of prior turns to include in prompt. Default: 6. Range: 0–20.
- `LLM_MODEL` (string, from config): LLM model identifier. Default: `gpt-4o`.
- `MAX_TOKENS` (integer, from config): Max tokens in LLM response. Default: 1500. Range: 100–4000.

---

### Outputs

**On success (HTTP 200):**
```json
{
  "message_id": "uuid-string",
  "answer_text": "According to the contract, payment is due within 30 days of invoice receipt.",
  "response_type": "answer",
  "citations": [
    {
      "citation_id": "uuid",
      "document_id": "uuid",
      "filename": "contract.pdf",
      "chunk_index": 7,
      "page_number": 3,
      "excerpt": "Payment shall be made within thirty (30) days of the date of invoice receipt."
    }
  ],
  "retrieved_chunks": 5,
  "timestamp": "2026-05-13T10:31:00Z"
}
```

**On refusal (HTTP 200, response_type = "refusal"):**
```json
{
  "message_id": "uuid-string",
  "answer_text": "I could not find an answer to your question in the uploaded documents.",
  "response_type": "refusal",
  "citations": [],
  "retrieved_chunks": 5,
  "timestamp": "2026-05-13T10:31:05Z"
}
```

---

### Validation Rules

- `question` must not be empty or whitespace-only after `.strip()`.
- `question` must be ≤ 2000 characters.
- `session_id` must be a valid UUID v4 format and exist in the in-memory session store.
- At least 1 document must be indexed for the session before a query can be submitted. Return `NO_DOCUMENTS_INDEXED` otherwise.
- `TOP_K` must be between 1 and 20 (inclusive). Values outside this range are clamped to the nearest bound.
- `TEMPERATURE` must be between 0.0 and 1.0 (inclusive). Values outside are clamped.
- `MAX_TOKENS` must be between 100 and 4000 (inclusive). Values outside are clamped.
- The assembled context window (system prompt + context + history + question) must not exceed the LLM's context limit. If it does, truncate chat history turns (oldest first) until it fits. If still too large after removing all history, truncate retrieved chunks (lowest-similarity first).
- LLM response must not be empty. If empty, return `LLM_EMPTY_RESPONSE` error.

---

### Error States

| Scenario | HTTP Status | Error Code | User Message |
|----------|-------------|------------|-------------|
| Empty or whitespace question | 400 | `EMPTY_QUESTION` | "Please enter a question before sending." |
| Question exceeds 2000 characters | 400 | `QUESTION_TOO_LONG` | "Your question is too long. Please shorten it to 2000 characters or fewer." |
| No documents indexed in session | 400 | `NO_DOCUMENTS_INDEXED` | "No documents are uploaded yet. Please upload a document before asking questions." |
| Invalid or missing session ID | 400 | `INVALID_SESSION` | "Session not found. Refresh the page to start a new session." |
| Query embedding API failure | 503 | `EMBEDDING_UNAVAILABLE` | "Unable to process your question right now. Please try again." |
| Vector store query failure | 500 | `RETRIEVAL_FAILED` | "Failed to search documents. Please try again." |
| LLM API unavailable | 503 | `LLM_UNAVAILABLE` | "The AI service is temporarily unavailable. Please try again in a moment." |
| LLM API key invalid / quota exceeded | 401 | `LLM_AUTH_FAILED` | "AI service authentication failed. Please check the API key configuration." |
| LLM returns empty response | 500 | `LLM_EMPTY_RESPONSE` | "The AI returned an empty response. Please try rephrasing your question." |
| LLM timeout (>30 seconds) | 504 | `LLM_TIMEOUT` | "The AI took too long to respond. Please try again." |
| Context window overflow (unresolvable) | 500 | `CONTEXT_TOO_LARGE` | "Your question context is too large to process. Try a shorter question." |

---

### API Surface (this feature)

See `Y1-api.md` §Chat for full request/response schemas.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat/query` | Submit a question; receive answer + citations |
| `GET` | `/api/chat/history` | Retrieve full chat history for the session |

---

### Schema Surface (this feature)

Uses: `sessions`, `chat_messages` — see `Y0-schema.md` §Sessions and §Chat.

Key fields per chat message stored server-side:
- `message_id` (UUID)
- `session_id` (UUID)
- `role` (`user` | `assistant`)
- `content` (string)
- `response_type` (`answer` | `refusal` | null for user turns)
- `citations` (JSON array)
- `timestamp` (ISO 8601)

---
