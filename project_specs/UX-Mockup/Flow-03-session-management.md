---

### Flow 03: Session Management (Clear Chat / New Session / Delete Document)

**User Stories:** US-3.2 · US-4.2 · US-4.3
**Feature Ref:** F3, F4
**Personas:** Maya (clear chat, keep docs), Daniel (delete superseded contract), Jordan (new session for fresh task)

---

#### Sub-flow 3A: Delete a Document

**Trigger:** User wants to remove a document from the session index (e.g., superseded contract, wrong file uploaded).

```
[Document Library Sidebar — document card visible]
[Each card has: 🗑️ trash icon button (aria-label: "Delete [filename]")]
       │
       ▼  [User clicks/activates 🗑️ on document card]
       │
       ▼
┌─────────────────────────────────────────────────────┐
│  Confirmation Modal                                  │
│                                                     │
│  Delete "contract-v2.pdf"?                          │
│  This will remove it from the document index.       │
│                                                     │
│  [Cancel]                    [Delete]               │
└─────────────────────────────────────────────────────┘
       │                              │
       ▼ Cancel                       ▼ Delete
  [Modal closes]            [Delete button → spinner]
  [No action]               [DELETE /api/documents/{id}]
                                      │
                         ┌────────────┴────────────┐
                         │ 204 Success             │ Error
                         ▼                         ▼
              [Card removed from library] [Red inline error on card:
              [Count/size summary updates] "Delete failed. Try again."]
              │                           [Retry affordance]
              ▼
   [Was last "ready" document?]
              │
     ┌────────┴────────┐
     │ Yes             │ No
     ▼                 ▼
  [Chat input       [Chat input stays
   disabled]         enabled]
  [Prompt: "Upload   [Session continues
   a document to     normally]
   start asking"]
```

---

#### Sub-flow 3B: Clear Chat History

**Trigger:** User wants fresh questions about the same document set without re-uploading.

```
[App Header → "Clear Chat" button]
       │
       ▼
┌────────────────────────────────────────────────────┐
│  Confirmation Modal                                │
│                                                   │
│  Clear conversation?                              │
│  Documents remain uploaded.                       │
│                                                   │
│  [Cancel]               [Clear]                   │
└────────────────────────────────────────────────────┘
       │                         │
       ▼ Cancel            ▼ Clear
  [Modal closes]    [DELETE /api/chat/history]
  [No action]              │
                    ┌──────┴──────┐
                    │ 204         │ Error
                    ▼             ▼
           [Chat view cleared]  [Toast error:
           [Empty state shown]   "Failed to clear chat.
           [Documents & library  Try again."]
            unchanged]
```

---

#### Sub-flow 3C: Start a New Session

**Trigger:** User wants to begin an entirely new research task — fresh documents AND fresh chat.

```
[App Header → "New Session" button (visually distinct from "Clear Chat")]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│  Confirmation Modal                                    │
│                                                       │
│  Start a new session?                                 │
│  All documents and chat history will be cleared.      │
│                                                       │
│  [Cancel]                   [Start New Session]       │
└────────────────────────────────────────────────────────┘
       │                              │
       ▼ Cancel                       ▼ Confirm
  [Modal closes]            [POST /api/session/reset]
  [No action]                         │
                             ┌────────┴────────┐
                             │ Success         │ Error
                             ▼                 ▼
                  [Library cleared]      [Toast error]
                  [Chat cleared]
                  [New session cookie set]
                  [Onboarding empty state shown]
```

**Key UX distinction (US-4.3):** "Clear Chat" and "New Session" are visually differentiated — different button weights, colors, or placement — so users cannot accidentally wipe their documents when they only meant to clear the chat. Suggested: "Clear Chat" is a secondary text button; "New Session" is a muted/ghost button with a warning-adjacent treatment.
