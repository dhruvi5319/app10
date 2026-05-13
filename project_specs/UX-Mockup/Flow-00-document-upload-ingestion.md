---

## User Flows

### Flow 00: Document Upload & Ingestion

**User Stories:** US-0.1 · US-0.2 · US-0.3
**Feature Ref:** F0, F3
**Personas:** Maya Patel (batch research PDFs), Daniel Torres (single contract, time pressure), Jordan Kim (drag-drop keyboard-first)

**Trigger:** User arrives with documents to analyze. Either empty-state first visit or mid-session addition.

```
[User Arrives at App]
       │
       ▼
[Empty State — Upload Zone prominent]
       │
       ├── Drag files onto zone ──────────────────────────────────────┐
       │                                                               │
       └── Click "Browse files" (file picker fallback) ───────────────┘
                                                                       │
                                                    ┌──────────────────▼──────────────────┐
                                                    │  Client-side validation (instant)    │
                                                    │  - extension: .pdf/.txt/.docx?       │
                                                    │  - size: ≤ 50 MB?                    │
                                                    │  - session count: < 20?              │
                                                    │  - session size: < 200 MB?           │
                                                    │  - non-empty file?                   │
                                                    └──────┬────────────────┬──────────────┘
                                                           │ PASS           │ FAIL
                                                           ▼                ▼
                                              [Upload Card appears]  [Inline error below
                                              status: uploading      drop zone — specific
                                              spinner visible]       rejection reason]
                                                           │
                                                           ▼
                                              [POST /api/documents/upload]
                                                           │
                                              ┌────────────▼─────────────┐
                                              │   Backend validates again  │
                                              │   202 Accepted → doc_id   │
                                              └────────────┬─────────────┘
                                                           │
                                                           ▼
                                              [Status: uploading → indexing]
                                              [Poll every 2s: GET /api/documents/{id}/status]
                                                           │
                                              ┌────────────┴─────────────┐
                                              │ ready                    │ error
                                              ▼                          ▼
                                   [Green checkmark ✓]        [Red error badge]
                                   [Chat input ENABLED]       [Specific reason shown]
                                   [Status: "Ready"]          [Retry affordance]
                                   [Document count updates]
```

**Multiple files in one drop:**
- Each file gets its own upload card immediately
- Validation runs per-file: rejected files show errors; valid files proceed independently
- A rejected file does NOT block other valid files in the same batch (US-0.2)

**Steps (detailed):**

1. **Drag-over feedback:** Drop zone border animates to accent color, background tints. If drag leaves window, zone resets to default immediately.
2. **Drop/select:** Upload cards appear in the Document Library sidebar — one per file — showing filename, size, and an `uploading` spinner.
3. **Client validation (instant, pre-upload):** Unsupported type → "Supported formats: PDF, TXT, DOCX". Over 50 MB → "File must be under 50MB". Session full → "Session storage limit of 200MB reached" / "Maximum 20 documents per session". Empty file → "Uploaded file contains no data".
4. **Server acceptance (202):** Card transitions from `uploading` to `indexing`. Badge shows animated blue "Indexing…" with pulse animation.
5. **Polling (every 2s):** Status badge updates in place. No page refresh needed.
6. **Ready:** Card shows green "Ready ✓". Chat input unlocks if at least one document is ready.
7. **Error:** Card shows red "Error" badge with specific reason (e.g., "PDF appears to be image-only; OCR not supported in v1"). Retry button visible.

**Exit points:**
- At least one document `ready` → proceed to Flow 01 (Ask a Question)
- All documents errored → remain in upload flow, retry or upload different files
