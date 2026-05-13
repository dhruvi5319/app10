
---

## F07: Configurable RAG Pipeline Settings

**Priority:** P2 — Medium, Developer experience  
**PRD Reference:** §6 F7

**Description:** Key RAG pipeline parameters are configurable via a `.env` file or environment variables, enabling operators and developers to tune the system without code changes. This includes LLM provider selection, API key injection, embedding model choice, chunking parameters (size and overlap), and retrieval top-k count. All configuration is read at server startup. Sensible defaults are defined for every parameter so the system works out-of-the-box with only an API key provided. The backend logs a sanitised configuration summary at startup.

---

### Terminology

- **Environment Variable:** A key-value pair set in the server's process environment, sourced from a `.env` file via `python-dotenv` or passed directly in the deployment environment.
- **Config Defaults:** Hard-coded fallback values used when a corresponding environment variable is absent.
- **Startup Config Log:** A log line (INFO level) emitted at server startup listing the resolved configuration values (with secrets redacted).
- **Provider:** The external LLM or embedding service vendor. Supported providers: `openai`, `anthropic`.
- **Top-k:** The number of document chunks retrieved per query to populate the LLM context window. Increasing top-k improves recall at the cost of larger prompts and slower LLM calls.
- **Chunk Size:** The maximum number of tokens per text chunk during ingestion. Smaller chunks increase retrieval precision; larger chunks preserve more context per chunk.
- **Chunk Overlap:** The number of tokens shared between consecutive chunks to prevent context loss at boundaries.

---

### Sub-features

- **F07-A:** Environment variable / `.env` file configuration at startup
- **F07-B:** Hard-coded defaults for all configurable parameters
- **F07-C:** Startup configuration validation (required keys present, values in range)
- **F07-D:** Sanitised startup log of resolved configuration
- **F07-E:** Runtime config accessible to all pipeline components (upload, chat, retrieval)

---

### Process

1. **Server starts.** `python-dotenv` loads `.env` from the project root (if present); environment variables override `.env` values.
2. **Backend** reads and resolves all configuration parameters (see Configuration Parameters table below) with defaults applied for absent variables.
3. **Backend** validates required parameters:
   - `OPENAI_API_KEY` must be present if `LLM_PROVIDER=openai` (default).
   - `ANTHROPIC_API_KEY` must be present if `LLM_PROVIDER=anthropic`.
   - Numeric parameters must be within valid ranges (see Validation Rules).
4. If a required API key is missing, **backend** logs a `CRITICAL` error and exits with a non-zero status code. The frontend, if running, will receive `503` responses for all LLM-dependent endpoints.
5. **Backend** emits a startup INFO log:
   ```
   [CONFIG] LLM Provider: openai | Model: gpt-4o | Embedding: text-embedding-3-small
   [CONFIG] Chunk Size: 500 | Overlap: 50 | Top-k: 5 | Max Docs: 10 | Max File MB: 20
   [CONFIG] Vector Store: chromadb | Storage: ./data/chroma
   [CONFIG] API Key: sk-...XXXX (redacted)
   ```
6. Resolved config is held in a global `Settings` singleton (e.g., via Pydantic `BaseSettings`) accessible by all backend modules.
7. No runtime mutation of config in v1 — changes require server restart.

---

### Configuration Parameters

| Parameter | Env Variable | Default | Type | Valid Range / Options |
|-----------|-------------|---------|------|----------------------|
| LLM provider | `LLM_PROVIDER` | `openai` | string | `openai`, `anthropic` |
| OpenAI API key | `OPENAI_API_KEY` | — | string | Required if provider=openai |
| Anthropic API key | `ANTHROPIC_API_KEY` | — | string | Required if provider=anthropic |
| LLM model name | `LLM_MODEL` | `gpt-4o` | string | Any valid model ID for provider |
| Embedding provider | `EMBEDDING_PROVIDER` | `openai` | string | `openai`, `sentence-transformers` |
| Embedding model | `EMBEDDING_MODEL` | `text-embedding-3-small` | string | Any valid embedding model ID |
| Chunk size (tokens) | `CHUNK_SIZE` | `500` | integer | 100–2000 |
| Chunk overlap (tokens) | `CHUNK_OVERLAP` | `50` | integer | 0–500; must be < CHUNK_SIZE |
| Retrieval top-k | `TOP_K` | `5` | integer | 1–20 |
| Chat history turns | `CHAT_HISTORY_TURNS` | `10` | integer | 0–50 |
| Max file size (MB) | `MAX_FILE_SIZE_MB` | `20` | integer | 1–100 |
| Max docs per session | `MAX_DOCS_PER_SESSION` | `10` | integer | 1–50 |
| LLM temperature | `LLM_TEMPERATURE` | `0.0` | float | 0.0–2.0 |
| Vector store backend | `VECTOR_STORE` | `chromadb` | string | `chromadb`, `faiss` |
| Vector store path | `VECTOR_STORE_PATH` | `./data/chroma` | string | Valid filesystem path |
| Uploads directory | `UPLOADS_DIR` | `./uploads` | string | Valid filesystem path |
| Log level | `LOG_LEVEL` | `INFO` | string | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

### Inputs

No runtime API inputs. Configuration is read from the environment at server startup only.

---

### Outputs

- Resolved `Settings` object consumed by all backend modules.
- Startup log lines (INFO) confirming resolved configuration (secrets redacted).
- Server exits with code 1 and `CRITICAL` log if required keys are missing.

---

### Validation Rules

- `CHUNK_OVERLAP` must be strictly less than `CHUNK_SIZE`; if equal or greater, default `CHUNK_OVERLAP` to `CHUNK_SIZE // 10`.
- `TOP_K` must be in range 1–20; values outside this range must be clamped to the nearest boundary and logged as a WARNING.
- `LLM_TEMPERATURE` must be in range 0.0–2.0; values outside range must be clamped and logged as a WARNING.
- `MAX_FILE_SIZE_MB` must be in range 1–100; outside range → clamped + WARNING.
- `VECTOR_STORE_PATH` and `UPLOADS_DIR` must be writable by the server process; if not, startup fails with a `CRITICAL` error.
- API keys must not be logged in full; only the last 4 characters should appear in logs (e.g., `sk-...XXXX`).
- If `LLM_PROVIDER` is an unrecognised value, server must fail at startup with a clear error: "Unsupported LLM_PROVIDER: '{value}'. Supported: openai, anthropic."

---

### Error States

| Scenario | Startup Behaviour | Log Level | Message |
|----------|------------------|-----------|---------|
| Required API key missing | Server exits (code 1) | CRITICAL | "OPENAI_API_KEY is required when LLM_PROVIDER=openai" |
| Unrecognised LLM_PROVIDER | Server exits (code 1) | CRITICAL | "Unsupported LLM_PROVIDER: '{value}'. Supported: openai, anthropic" |
| VECTOR_STORE_PATH not writable | Server exits (code 1) | CRITICAL | "Cannot write to VECTOR_STORE_PATH: '{path}'. Check permissions." |
| Out-of-range numeric param | Param clamped to boundary | WARNING | "CHUNK_SIZE=3000 out of range [100, 2000]; using 2000." |
| CHUNK_OVERLAP ≥ CHUNK_SIZE | Overlap auto-corrected | WARNING | "CHUNK_OVERLAP must be < CHUNK_SIZE; defaulting to CHUNK_SIZE // 10." |
| Unrecognised VECTOR_STORE | Server exits (code 1) | CRITICAL | "Unsupported VECTOR_STORE: '{value}'. Supported: chromadb, faiss" |

---

### API Surface (this feature)

No runtime API endpoints for configuration in v1. Configuration is server-side only; no settings UI is provided to the frontend in v1.

---

### Schema Surface (this feature)

No database schema. Configuration is held in-process via the `Settings` singleton. The `.env` file is the on-disk artefact and must be listed in `.gitignore` to prevent accidental secret commits.
