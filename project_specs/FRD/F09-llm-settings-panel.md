---

## F09: LLM Settings Panel

**Priority:** P1 — Phase 5  
**PRD Reference:** §5 F9

**Description:** A user-facing settings panel lets users configure their LLM provider, model name, and API key directly through the UI without editing `.env` files or restarting the server. The API key is encrypted at rest using Fernet symmetric encryption and is never returned in plain text after it has been saved — the GET endpoint returns a masked representation (e.g., `sk-...XXXX`). Settings are persisted in a dedicated `llm_settings` SQLite table and are applied at call time to all subsequent chat queries, overriding any `.env` value when a saved key exists. The app can boot without an API key in `.env` if a saved key is present in the database.

---

### Terminology

- **Fernet Encryption:** Symmetric authenticated encryption provided by the Python `cryptography` library. Uses AES-128-CBC with HMAC-SHA256. Keys are URL-safe base64-encoded 32-byte values.
- **SECRET_KEY:** The server-side environment variable (a valid Fernet key) used as the encryption/decryption key for stored API keys. Must be set at deployment time.
- **Encrypted Key:** The Fernet-encrypted ciphertext of the raw API key; stored in the `llm_settings.encrypted_key` column.
- **Masked Key:** A safe display representation of the stored key — all characters replaced except the final 4, prefixed with a provider-appropriate hint (e.g., `sk-...XXXX`). Never decrypted for display.
- **Settings Modal:** The frontend UI overlay triggered by the gear icon; contains provider, model, and API key fields.
- **Key Badge:** A secondary UI element shown next to the API key input when `has_key: true`; displays the masked key string (e.g., `Key saved (sk-...XXXX)`).

---

### Sub-Features

- `llm_settings` SQLite table (single-row settings store; upsert on save)
- Fernet encryption/decryption utility (`encrypt_api_key` / `decrypt_api_key`)
- `GET /api/settings` — returns current provider, model, and masked key; raw key never returned
- `PUT /api/settings` — accepts provider, model, and raw API key; encrypts before writing; returns updated settings summary
- At-call-time key resolution: backend reads and decrypts stored key before each LLM/embedding call; overrides env var when DB setting exists
- App boots without `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in `.env` if `llm_settings` row exists
- Gear icon button in app header/sidebar opens the settings modal
- Settings modal: Provider select (OpenAI / Anthropic), Model text input, API Key password input
- Key badge shown next to API key field when `has_key: true`
- Save button state: disabled when API key field is empty AND `has_key: false`
- Success toast on save; inline field-level error on failure
- Modal closes on successful save or Cancel

---

### Process

#### Backend — Save Settings (`PUT /api/settings`)

1. Client sends `PUT /api/settings` with JSON body `{ provider, model, api_key }`.
2. Backend validates `provider` is one of `"openai"` or `"anthropic"`; returns 422 `SETTINGS_INVALID_PROVIDER` if not.
3. Backend validates `api_key` is a non-empty string; if empty **and** no existing row in `llm_settings` exists, returns 422 `SETTINGS_KEY_REQUIRED`. If empty **and** an existing row exists, the existing encrypted key is preserved (key omission = keep current key).
4. If `api_key` is non-empty, backend calls `encrypt_api_key(api_key, SECRET_KEY)` using Fernet; stores resulting ciphertext.
5. Backend upserts the `llm_settings` table (single row, `id = 1`): sets `provider`, `model`, `encrypted_key` (if new key provided), and `updated_at` to current UTC timestamp.
6. Backend returns `200 OK` with `{ success: true, provider, model }`. Raw key and ciphertext are not included.

#### Backend — Get Settings (`GET /api/settings`)

1. Client sends `GET /api/settings` with no body.
2. Backend queries `llm_settings` for `id = 1`.
3. If no row exists: returns `200 OK` with `{ has_key: false, provider: "openai", model: "gpt-4o", api_key_masked: "" }`.
4. If row exists: backend computes the masked key string from `encrypted_key` (decrypt to get raw key in memory; apply masking; do not log or return raw key).
   - **Masking rule:** Take the last 4 characters of the raw API key; prepend `sk-...` (for OpenAI) or `sk-ant-...` (for Anthropic). Example: raw key `sk-abc123XYZ` → masked `sk-...3XYZ`.
   - Raw key is discarded from memory immediately after masking.
5. Returns `200 OK` with `{ has_key: true, provider, model, api_key_masked }`.

#### Backend — At-Call-Time Key Resolution

When the backend is about to make an LLM or embedding API call:

1. Query `llm_settings` for `id = 1`.
2. If row exists and `encrypted_key` is non-null: call `decrypt_api_key(encrypted_key, SECRET_KEY)` to obtain the raw key in memory.
3. Inject the raw key into the LLM client as the API key for this call only; do not cache it in memory beyond the call.
4. If no row exists (or `encrypted_key` is null): fall back to `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` environment variables.
5. If neither source yields a key, the call fails with `LLM_UNAVAILABLE` (503) — surface an actionable message: "No API key configured. Open Settings to add your key."

#### Frontend — Open Settings Modal

1. User clicks the gear icon in the app header or sidebar.
2. Frontend calls `GET /api/settings`.
3. Modal renders with current `provider` and `model` pre-filled from the response.
4. API Key field renders as `<input type="password">` — always blank on open (never pre-filled with masked or raw key).
5. If `has_key: true`, a Key Badge is shown next to the API Key field: `"Key saved (sk-...XXXX)"` using the `api_key_masked` value from the response.
6. Save button is disabled if: API Key field is empty AND `has_key: false`.

#### Frontend — Save Settings

1. User fills in or updates fields and clicks Save.
2. Frontend sends `PUT /api/settings` with `{ provider, model, api_key }`. If API Key field is empty, `api_key` is sent as an empty string (backend interprets this as "keep current key").
3. On `200 OK`: display success toast "Settings saved"; close modal.
4. On `422 SETTINGS_KEY_REQUIRED`: display inline error below the API Key field: "An API key is required when no key is currently saved."
5. On `422 SETTINGS_INVALID_PROVIDER`: display inline error below the Provider field: "Invalid provider selected."
6. On any other error: display inline error below the Save button with the `message` field from the error response.
7. User clicks Cancel: modal closes without saving; no API call made.

---

### Inputs

**`GET /api/settings`:**
- No request body.
- Session cookie not required (settings are global, not session-scoped).

**`PUT /api/settings` request body (JSON):**

| Field | Type | Required | Notes |
|---|---|---|---|
| `provider` | string | Yes | `"openai"` or `"anthropic"` |
| `model` | string | Yes | LLM model name (e.g., `"gpt-4o"`, `"claude-3-5-sonnet-20241022"`); free-text, not validated against a list |
| `api_key` | string | Yes (field must be present) | Raw API key. Empty string = keep existing key. Non-empty = replace key. |

---

### Outputs

**`GET /api/settings` — no existing settings:**
```json
{
  "has_key": false,
  "provider": "openai",
  "model": "gpt-4o",
  "api_key_masked": ""
}
```

**`GET /api/settings` — settings exist:**
```json
{
  "has_key": true,
  "provider": "openai",
  "model": "gpt-4o",
  "api_key_masked": "sk-...XXXX"
}
```

**`PUT /api/settings` — success:**
```json
{
  "success": true,
  "provider": "openai",
  "model": "gpt-4o"
}
```

---

### Validation Rules

- `provider` must be exactly `"openai"` or `"anthropic"` (case-sensitive). Any other value → 422 `SETTINGS_INVALID_PROVIDER`.
- `model` must be a non-empty string after trimming whitespace. Blank model → 422 `SETTINGS_MODEL_REQUIRED`.
- `api_key` field must be present in the request body (even if empty string).
- `api_key` is an empty string AND no `llm_settings` row exists → 422 `SETTINGS_KEY_REQUIRED`.
- `api_key` is an empty string AND a `llm_settings` row with a non-null `encrypted_key` exists → existing key is preserved; no re-encryption occurs.
- `api_key` is a non-empty string → always encrypt and overwrite, regardless of whether a key already exists.
- `SECRET_KEY` must be a valid Fernet key (44-character URL-safe base64 string). If missing or malformed at startup, the backend must log a startup error and refuse to serve settings endpoints until corrected.
- Raw API key must never appear in application logs, error responses, or SSE streams.
- `llm_settings` table stores at most one row (`id = 1`); `PUT` is always an upsert.
- Settings are global (not session-scoped); one configuration applies to all sessions on the server.

---

### Error States

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| `api_key` empty, no existing key | 422 | `SETTINGS_KEY_REQUIRED` | "An API key is required when no key is currently saved" |
| `provider` not `openai` or `anthropic` | 422 | `SETTINGS_INVALID_PROVIDER` | "Provider must be 'openai' or 'anthropic'" |
| `model` is blank | 422 | `SETTINGS_MODEL_REQUIRED` | "Model name is required" |
| `SECRET_KEY` env var missing or invalid (runtime) | 500 | `ENCRYPTION_CONFIG_ERROR` | "Server encryption configuration error; contact administrator" |
| Fernet decryption fails (key mismatch / corruption) | 500 | `DECRYPTION_FAILED` | "Failed to decrypt stored API key; please re-enter your key" |
| LLM call with no key configured | 503 | `LLM_UNAVAILABLE` | "No API key configured. Open Settings to add your key." |

---

### API Surface (this feature)

See `Y1-api.md` §Settings for full request/response schemas.

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/settings` | Return current LLM provider, model, and masked key status |
| `PUT` | `/api/settings` | Save (or update) LLM provider, model, and API key (encrypted at rest) |

---

### Schema Surface (this feature)

New SQLite table `llm_settings`. See `Y0-schema.md` §LLMSettings for full DDL.

Key fields:
- `id` (INTEGER, PK) — always `1`; single-row table
- `provider` (TEXT) — `"openai"` or `"anthropic"`
- `model` (TEXT) — LLM model name string
- `encrypted_key` (TEXT) — Fernet ciphertext of the raw API key; null if no key has been saved
- `updated_at` (TEXT) — UTC ISO 8601 timestamp of last save
