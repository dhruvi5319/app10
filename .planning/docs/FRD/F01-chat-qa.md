
---

## F01: Chat Interface & Question Answering

**Priority:** P0 — Critical, MVP  
**PRD Reference:** §6 F1

**Description:** The primary user interaction surface is a chat interface where users type natural-language questions and receive answers generated exclusively from content in their uploaded documents. On each query, the backend embeds the question, retrieves the top-k most similar chunks from the session's vector store, constructs a strictly-grounded prompt, calls the LLM, and returns the response along with source metadata for citation (see F02). If the answer cannot be found in the uploaded documents, the system explicitly says so rather than hallucinating.

---

### Terminology

- **Query:** A natural-language question submitted by the user in the chat input field.
- **Query Embedding:** The vector representation of the user's question, used to perform cosine-similarity search against chunk embeddings.
- **Retrieval:** The process of finding the top-k chunks most semantically similar to the query embedding.
- **Context Window:** The set of retrieved chunk texts assembled into a prompt sent to the LLM.
- **Grounding Prompt:** A system prompt instructing the LLM to answer only from the provided context and to refuse if the answer is absent.
- **Refusal Response:** A structured response the LLM returns when the answer cannot be found in the uploaded documents. Must never substitute external knowledge.
- **Streaming:** Token-by-token LLM response delivery to the frontend via Server-Sent Events (SSE), enabling the typing-indicator effect.
- **Message:** A single user query or assistant response in the conversation thread, stored in the session's chat history.

---

### Sub-features

- **F01-A:** Chat message thread UI (scrollable, user right / assistant left)
- **F01-B:** Message input bar with send button and Enter key shortcut
- **F01-C:** Typing / loading indicator during LLM generation
- **F01-D:** Markdown rendering of assistant responses
- **F01-E:** Query embedding and vector store retrieval
- **F01-F:** Grounded LLM prompt construction and answer generation
- **F01-G:** Refusal response when answer is absent from documents
- **F01-H:** Response streaming to frontend (SSE)

---

### Process

1. **User** types a question in the chat input bar and presses Enter or clicks the Send button.
2. **Frontend** validates the query is non-empty (trims whitespace) and that at least one document is in `READY` status. If no documents are ready, displays a contextual prompt (see F05 §Validation).
3. **Frontend** disables the send button and displays a typing indicator (animated ellipsis or spinner).
4. **Frontend** appends the user message to the chat thread (right-aligned) and sends `POST /api/chat/query` with `{session_id, query, chat_history_ref}`.
5. **Backend** validates `session_id` exists and `query` is non-empty (1–2000 characters).
6. **Backend** generates an embedding of the query using the same embedding model used during ingestion.
7. **Backend** queries the vector store collection `session_{session_id}` for the top-k most similar chunks (default `k=5`, configurable — see F07).
8. **Backend** assembles a context block from the retrieved chunks, formatted as:
   ```
   [Source: {filename}, Page {page_number}, Chunk {chunk_index}]
   {chunk_text}
   ```
9. **Backend** constructs a prompt using the grounding template:
   - **System:** "You are a document assistant. Answer the user's question using ONLY the provided document excerpts. If the answer is not present in the excerpts, respond with: 'I could not find an answer to your question in the uploaded documents.' Do NOT use any external knowledge."
   - **User:** The assembled context block, followed by the user's question.
   - **Chat history:** Last N exchanges appended for conversational context (N configurable; default 10 turns).
10. **Backend** calls the LLM API with streaming enabled. Streams token chunks back to the frontend via SSE (`GET /api/chat/stream/{message_id}`).
11. **Frontend** renders each streaming token in the assistant bubble as it arrives; auto-scrolls the thread to the bottom.
12. **Backend** aggregates the full response, records the message (query + answer + retrieved chunk IDs) in the session's chat history.
13. **Backend** sends a final SSE event containing the full message object including citation data (see F02).
14. **Frontend** re-enables the send button; renders the final answer with citations below the message bubble (see F02 §Process).

---

### Inputs

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `session_id` | string (UUID) | Yes | Active session with ≥ 1 `READY` document |
| `query` | string | Yes | 1–2000 characters; non-empty after trimming |
| `include_history` | boolean | No | Default `true`; sends last N chat turns as context |

---

### Outputs

**Success (200 OK) — final message object:**
```json
{
  "message_id": "uuid-v4",
  "session_id": "uuid-v4",
  "role": "assistant",
  "content": "The contract was signed on March 15, 2024.",
  "is_refusal": false,
  "retrieved_chunks": [
    {
      "chunk_id": "doc-uuid:0",
      "doc_id": "doc-uuid",
      "filename": "contract.pdf",
      "page_number": 3,
      "chunk_index": 0,
      "excerpt": "...The parties agreed to sign on March 15, 2024..."
    }
  ],
  "created_at": "2026-05-13T10:01:00Z"
}
```

**Refusal response (answer not in documents):**
```json
{
  "message_id": "uuid-v4",
  "role": "assistant",
  "content": "I could not find an answer to your question in the uploaded documents.",
  "is_refusal": true,
  "retrieved_chunks": [],
  "created_at": "2026-05-13T10:01:00Z"
}
```

**SSE stream event (during generation):**
```
data: {"type": "token", "delta": "The contract"}
data: {"type": "token", "delta": " was signed"}
data: {"type": "done", "message": { ...full message object... }}
```

---

### Validation Rules

- `query` must be 1–2000 characters after whitespace trimming; reject empty or whitespace-only queries.
- `session_id` must correspond to an active session.
- At least one document with status `READY` must exist in the session before submitting a query. Surface a specific message if this condition is not met (see F05).
- Query embedding must succeed before retrieval; if the embedding API is unavailable, return `503` immediately.
- Retrieved chunks must belong to the same `session_id` (enforced via collection namespacing).
- LLM response must not be empty; if empty string is returned, treat as `LLM_EMPTY_RESPONSE` error.
- Chat history included in the prompt must not exceed the LLM's context window limit; truncate oldest turns first if needed.

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|----------|-------------|------------|---------|
| Empty query submitted | 422 | `EMPTY_QUERY` | "Please enter a question before sending." |
| Query exceeds 2000 characters | 422 | `QUERY_TOO_LONG` | "Question must be 2000 characters or fewer." |
| No ready documents in session | 422 | `NO_DOCUMENTS_READY` | "Please upload and process at least one document before asking a question." |
| Session not found | 404 | `SESSION_NOT_FOUND` | "Session not found. Please refresh the page." |
| Embedding API failure | 503 | `EMBEDDING_UNAVAILABLE` | "Could not process your question. Please try again." |
| LLM API rate limit | 429 | `LLM_RATE_LIMIT` | "The AI service is busy. Please wait a moment and try again." |
| LLM API unavailable | 503 | `LLM_UNAVAILABLE` | "The AI service is currently unavailable. Please check your configuration." |
| LLM returns empty response | 500 | `LLM_EMPTY_RESPONSE` | "The AI did not return a response. Please try again." |
| Vector store retrieval failure | 500 | `RETRIEVAL_FAILURE` | "Could not search your documents. Please try again." |
| Context window exceeded | 500 | `CONTEXT_TOO_LARGE` | "The conversation history is too long. Please clear the chat and try again." |

---

### API Surface (this feature)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/query` | Submit a query; returns message_id immediately |
| `GET` | `/api/chat/stream/{message_id}` | SSE stream of LLM tokens |
| `GET` | `/api/chat/history/{session_id}` | Retrieve full chat history for session |

Full request/response schemas → `Y1-api.md §Chat`

---

### Schema Surface (this feature)

Uses tables/collections:
- `messages` — stores each user and assistant message, linked to session
- `retrieved_chunks` — join table linking message to chunk IDs used for generation
- ChromaDB collection `session_{session_id}` — queried during retrieval

Full DDL → `Y0-schema.md §Chat`
