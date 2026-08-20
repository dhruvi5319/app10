---

## Screen Designs

### Screen 05: LLM Settings Modal

**Purpose:** Lets the user configure their LLM provider, model, and API key from the UI without editing server configuration files. The modal is a centered overlay; the raw API key is never displayed after it has been saved.
**User Stories:** US-9.1 · US-9.2 · US-9.3 · US-9.4 · US-9.5
**Feature Ref:** F9
**Phase:** 5

---

#### Trigger

A `⚙` gear icon button sits in the **top-right area of the app header**, after the Export control. It is always visible regardless of document or chat state — including when no API key has been configured (which is precisely when first-time users need it most).

```
┌────────────────────────────────────────────────────────────────────────────┐
│  🤖 RAG Chatbot            [Clear Chat]  [New Session]  [Export ↓]  [⚙]  │
└────────────────────────────────────────────────────────────────────────────┘
```

- **Element type:** `<button>` with `aria-label="Open LLM settings"` and `aria-haspopup="dialog"`
- **Keyboard:** Tab-reachable; Enter / Space opens the modal
- **Tooltip:** "LLM Settings" on hover / focus (200 ms delay)

---

#### Navigation Map Entry

| Screen | Route / Trigger | Reached from | Nav element |
|--------|----------------|--------------|-------------|
| LLM Settings Modal | `⚙` gear button click | App header (all screens) | Header: "⚙" icon button (top-right) |

The modal is a layer over the current screen — it does not change the URL. Focus is trapped inside the modal while it is open. Closing the modal returns focus to the gear icon.

---

#### Modal Layout

The modal is a **centered overlay** (480 px wide, ~400 px tall) on a dark semi-transparent backdrop. It uses the surface colour token (`--color-surface: #1a1d27`) for its background and `--color-accent: #6c63ff` for the primary action.

```
╔══════════════════════════════════════════════════════════╗
║  LLM Settings                                       [✕]  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Provider                                                ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  OpenAI                                         ▾  │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  Model                                                   ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  gpt-4o                                            │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  API Key                                                 ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  ••••••••••••••••••••••••••••••              [👁]  │  ║
║  └────────────────────────────────────────────────────┘  ║
║  ✅ Key saved · sk-...XXXX                  ← muted green║
║                                                          ║
║                                                          ║
║  [    Cancel    ]                  [  Save Settings  ]  ║
╚══════════════════════════════════════════════════════════╝
```

**Backdrop:** `background: rgba(0,0,0,0.6); backdrop-filter: blur(4px)` covering the full viewport behind the modal.

**Modal card:** `background: var(--color-surface); border: 1px solid rgba(108,99,255,0.25); border-radius: 12px; box-shadow: var(--shadow-deep)` (deep shadow from design token).

**Modal header:** Left-aligned title "LLM Settings" in bold (`font-weight: 700`). Right-aligned `✕` close button with `aria-label="Close settings"`.

---

#### Form Fields

| Field | Type | Label | Default / Pre-fill | Notes |
|-------|------|-------|--------------------|-------|
| Provider | `<select>` | "Provider" | Current `provider` from `GET /api/settings` | Options: "OpenAI", "Anthropic" |
| Model | `<input type="text">` | "Model" | Current `model` from `GET /api/settings` | Placeholder: `e.g. gpt-4o` |
| API Key | `<input type="password">` | "API Key" | Always blank on open | Placeholder varies by `has_key` (see below) |

**API Key placeholder logic:**

- `has_key: false` → placeholder text: `"Paste your API key"`
- `has_key: true` → placeholder text: `"Enter new key to replace current"`

**Key badge** (shown only when `has_key: true`): A small inline element rendered below the API Key input field.

```
  ✅  Key saved · sk-...XXXX
```

- Colour: muted green (`#4ade80` at 80% opacity on the dark surface)
- Font size: 12px / `text-sm`
- Icon: `✅` or a small lock icon; `aria-hidden="true"`

**Reveal toggle:** An eye icon `[👁]` inside the API Key input (right-inset) toggles `type="password"` ↔ `type="text"` so the user can verify what they typed. Label: `aria-label="Show API key"` / `"Hide API key"`.

---

#### Save Button Enable/Disable Logic

| `has_key` state | API Key field | Save button |
|-----------------|---------------|-------------|
| `false` (no key saved) | Empty | **Disabled** — tooltip: "Enter an API key to enable saving" |
| `false` | Non-empty | Enabled |
| `true` (key exists) | Empty | **Enabled** — existing key will be kept; only provider/model updated |
| `true` | Non-empty | Enabled — new key replaces existing |

---

#### Information Hierarchy

| Priority | Content | Placement |
|----------|---------|-----------|
| Primary | Provider select + Model input | Top of form — most commonly edited |
| Primary | API Key input | Below model — security-sensitive; password type |
| Secondary | Key badge (`sk-...XXXX`) | Below API Key field, only when key exists |
| Secondary | Save Settings button | Bottom-right — primary accent colour |
| Tertiary | Cancel button | Bottom-left — secondary/ghost style |
| Tertiary | Close (✕) button | Modal header, top-right |

---

#### States

| State | Appearance | User Feedback |
|-------|------------|---------------|
| **Default — no key** | Fields empty / default-value pre-filled; Save disabled | Placeholder: "Paste your API key"; Save button dimmed |
| **Default — key exists** | Provider + model pre-filled; key badge visible; API Key field blank with "Enter new key…" placeholder; Save enabled | Badge shows `sk-...XXXX` |
| **Loading (on open)** | Modal skeleton — fields shimmer while `GET /api/settings` resolves | Fields replaced with skeleton bars (~120 ms) |
| **Dirty / editing** | User has changed one or more fields | No special indicator — standard browser focus outline + glow |
| **Saving** | Save button shows inline spinner `⟳`; label changes to "Saving…"; all form fields disabled; Cancel also disabled | Button: `[⟳ Saving…]` — accent colour preserved |
| **Success** | Modal closes; toast appears top-right | Toast: `"Settings saved successfully"` — green, auto-dismisses after 4 s |
| **Error — field-level** | Inline red message under the failing field; modal stays open | e.g., `"An API key is required when no key is currently saved."` below API Key field |
| **Error — server** | Inline red message below the button row; modal stays open; Save re-enabled | e.g., `"Server encryption configuration error; contact administrator."` |
| **Empty (no settings ever set)** | All fields at defaults: Provider = OpenAI, Model = `gpt-4o`, no badge | Prompt visible in placeholder text |

---

#### Saving State Wireframe Detail

```
╔══════════════════════════════════════════════════════════╗
║  LLM Settings                                       [✕]  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Provider                                                ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  OpenAI                                         ▾  │  ║  ← disabled
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  Model                                                   ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  gpt-4o                                            │  ║  ← disabled
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  API Key                                                 ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  ••••••••••••••••••••••••••••••              [👁]  │  ║  ← disabled
║  └────────────────────────────────────────────────────┘  ║
║  ✅ Key saved · sk-...XXXX                               ║
║                                                          ║
║  [    Cancel    ]                  [  ⟳ Saving…   ]  ║
╚══════════════════════════════════════════════════════════╝
```

---

#### Error State Wireframe Detail

```
╔══════════════════════════════════════════════════════════╗
║  LLM Settings                                       [✕]  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Provider                                                ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  OpenAI                                         ▾  │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  Model                                                   ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │  gpt-4o                                            │  ║
║  └────────────────────────────────────────────────────┘  ║
║                                                          ║
║  API Key                                                 ║
║  ┌────────────────────────────────────────────────────┐  ║
║  │                                              [👁]  │  ║  ← red border
║  └────────────────────────────────────────────────────┘  ║
║  ⚠ An API key is required when no key is currently saved.║  ← red, 12px
║                                                          ║
║  [    Cancel    ]                  [  Save Settings  ]  ║
╚══════════════════════════════════════════════════════════╝
```

Field-level error styling: `border: 1px solid #f87171; box-shadow: 0 0 0 3px rgba(248,113,113,0.2)`. Error text: `color: #f87171; font-size: 12px; margin-top: 4px`.

---

#### Interactive Elements

| Element | Type | Behavior |
|---------|------|----------|
| Gear icon `⚙` (header) | `<button>` | Click / Enter → opens modal; calls `GET /api/settings` |
| ✕ Close button | `<button>` | Click / Enter → closes modal without saving; focus returns to gear icon |
| Provider `<select>` | Dropdown | Selecting "OpenAI" / "Anthropic" updates local form state; no immediate API call |
| Model `<input>` | Text input | Free text; trimmed on save; glow on focus |
| API Key `<input type="password">` | Password input | Always blank on open; glow on focus; eye toggle for reveal |
| Eye toggle `[👁]` | Icon button inside input | Toggles `type` between `password` and `text`; `aria-label` updates accordingly |
| Cancel button | Secondary / ghost button | Discards all changes; closes modal; no API call |
| Save Settings button | Primary accent button | Sends `PUT /api/settings`; disabled per logic table above |
| Dark backdrop | Click target | Click outside the modal card → same as Cancel |
| Escape key | Keyboard shortcut | Closes modal without saving (same as Cancel) |

---

#### User Journey Integration

**Entry points:**
1. User clicks `⚙` in the app header → modal opens
2. System shows `LLM_UNAVAILABLE` error in chat (no key configured) → inline link "Open Settings" in the error message → same modal opens

**Exit points:**
1. **Save success** → modal closes → toast "Settings saved successfully" top-right (4 s) → returns to previous screen state
2. **Cancel / Escape / backdrop click** → modal closes → no changes persisted → returns to previous screen state
3. **Error** → modal stays open → user corrects field → re-submits

**Adjacent workflows:**
- If the user saves a key for the first time and no documents are ready, the chat input remains disabled (per F0 rules). Settings panel does not change document state.
- If the user saves a new key while a query is streaming, the new key applies to the **next** query only — the in-flight stream is not interrupted.

---

#### Responsive Considerations

| Viewport | Behaviour |
|----------|-----------|
| Desktop (≥ 1024 px) | Centered overlay, 480 px wide, as designed above |
| Tablet (768 px – 1023 px) | Same centered overlay; modal width 90 vw (max 480 px) |
| Mobile (< 768 px) | Modal slides up from the bottom as a bottom sheet; full width; rounded top corners; handle bar at top; internally scrollable if content overflows |

Mobile bottom-sheet wireframe:
```
╔══════════════════════════════════╗
║        ──── (handle bar)         ║
║  LLM Settings              [✕]  ║
╠══════════════════════════════════╣
║  Provider                        ║
║  [  OpenAI              ▾  ]    ║
║  Model                           ║
║  [  gpt-4o                  ]   ║
║  API Key                         ║
║  [  ••••••••••••••••    [👁] ]  ║
║  ✅ Key saved · sk-...XXXX      ║
║                                  ║
║  [Cancel]    [Save Settings]    ║
╚══════════════════════════════════╝
```

---

#### Accessibility Notes

- Modal uses `role="dialog"` and `aria-modal="true"`; `aria-labelledby` points to the "LLM Settings" heading.
- **Focus trap:** On open, focus moves to the first focusable field (Provider select). Tab cycles within the modal; Shift+Tab reverses. Focus never leaves the modal while it is open.
- **Focus restore:** On close (any method), focus returns to the `⚙` gear icon that opened the modal.
- **Escape key** closes the modal (same behaviour as Cancel).
- **Save button disabled state:** `aria-disabled="true"` + a tooltip (`title` or `aria-describedby`) explains why: "Enter an API key to enable saving".
- **Error announcements:** Field-level errors are linked to their input via `aria-describedby`; the error container uses `role="alert"` so screen readers announce it immediately on injection.
- **API Key reveal toggle:** `aria-label` is dynamic — "Show API key" when masked, "Hide API key" when revealed.
- **Key badge:** The `✅` icon has `aria-hidden="true"`; the badge text ("Key saved · sk-...XXXX") is the accessible label.
- **Colour contrast:** All text on `--color-surface: #1a1d27` background meets WCAG AA ≥ 4.5:1. Error red `#f87171` on surface: passes AA for large text; inline error uses 12px so it is paired with a warning icon to avoid relying on colour alone.
- **`prefers-reduced-motion`:** Modal entrance animation (fade + scale) is disabled; the backdrop blur still applies as it is not motion-based.
