---
phase: 02-core-mvp-ui
plan: "08"
subsystem: ui
tags: [react, typescript, chat, markdown, streaming, sse]

requires:
  - phase: 02-core-mvp-ui
    provides: T07 useChat hook with SSE streaming, messages state, sendMessage, clearMessages

provides:
  - ChatPanel component wiring useChat to full chat UI
  - MessageThread with auto-scroll (150px threshold)
  - MessageBubble with ReactMarkdown, streaming cursor, error handling
  - TypingIndicator with CSS keyframe dots animation
  - ChatInput with Enter-to-send, Shift+Enter newline, auto-grow, guard message
  - ClearChatDialog modal with spinner confirmation

affects:
  - T09 (CitationSection already imported by MessageBubble — ensure interface matches)
  - T11 (Integration wiring — ChatPanel is the primary chat entry point)

tech-stack:
  added: []
  patterns:
    - "Error bubble retry pattern: MessageThread extracts prior user query and curries it into onRetry closure before passing to MessageBubble"
    - "Streaming bubble: same MessageBubble renders with isStreaming=true + streamingContent + appended ▍ cursor"
    - "Auto-scroll: isNearBottomRef tracks scroll position; only auto-scrolls when within 150px of bottom"

key-files:
  created: []
  modified:
    - frontend/src/components/chat/MessageBubble.tsx
    - frontend/src/components/chat/MessageThread.tsx

key-decisions:
  - "onRetry callback in MessageBubble changed to () => void — query curried by MessageThread from prior user message"
  - "All 6 components were pre-scaffolded and spec-compliant; only the retry bug required a fix"

patterns-established:
  - "Error bubble: content prefixed with __ERROR__, extracted by isErrorMessage/extractErrorText from useChat"
  - "Streaming: placeholder assistant message replaced by final message on SSE done event"

duration: 8min
completed: 2026-07-17
---

# Phase 2 Plan 08: Chat Interface Components Summary

**Six chat UI components verified and fixed: ReactMarkdown streaming with ▍ cursor, 150px auto-scroll threshold, Enter/Shift+Enter textarea, guard message, ClearChatDialog — plus a retry bug fix where error bubbles now re-send the correct prior user query**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-07-17T18:37:00Z
- **Completed:** 2026-07-17T18:45:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Verified all 6 chat components (ChatPanel, MessageThread, MessageBubble, TypingIndicator, ChatInput, ClearChatDialog) fully meet the T08 spec
- Fixed a correctness bug in error bubble "Try again" retry — was passing `__ERROR__<error text>` as the query; now correctly finds and passes the preceding user message content
- Confirmed: ReactMarkdown+remarkGfm for assistant messages, streaming cursor `▍`, auto-scroll within 150px of bottom, Enter-to-send/Shift+Enter-for-newline, guard message when `!hasReadyDocument`, spinner on ClearChatDialog confirm
- Build passes with 0 TypeScript and 0 Vite errors

## Task Commits

1. **T08: Chat Interface Components** - `5b49f8e` (feat)

## Files Created/Modified
- `frontend/src/components/chat/MessageThread.tsx` — Added `isErrorMessage` import, extracted prior user query from messages array before currying into `onRetry` closure for error bubbles
- `frontend/src/components/chat/MessageBubble.tsx` — Changed `onRetry` type from `(query: string) => void` to `() => void`; caller now provides the query

## Decisions Made
- Changed `onRetry` in `MessageBubble` to be a zero-argument callback: the query lookup responsibility moved to `MessageThread` where the full messages array is available, making `MessageBubble` simpler and avoiding passing incorrect error-prefix content as a query

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed error bubble retry passing `__ERROR__` content as query**
- **Found during:** T08 spec verification
- **Issue:** `MessageBubble` called `onRetry(message.content)` where `message.content` is an error assistant message starting with `__ERROR__Failed to send...` — this string would be sent as the user query instead of the original question
- **Fix:** `MessageThread` now finds the nearest preceding user message (`.reverse().find(m => m.role === 'user')`) and builds a closure `() => onRetry(priorUserQuery)` before passing to `MessageBubble`. `MessageBubble.onRetry` type simplified to `() => void`
- **Files modified:** `frontend/src/components/chat/MessageThread.tsx`, `frontend/src/components/chat/MessageBubble.tsx`
- **Verification:** `npm run build` passes with 0 errors (TypeScript validates the changed signatures)
- **Committed in:** 5b49f8e

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Bug fix only — no scope change. Retry now correctly re-sends the user's original question.

## Known Stubs

None found. All 6 components implement real behavior. No TODOs, FIXMEs, or hardcoded stubs detected.

## Issues Encountered

None — the pre-scaffolded components were structurally complete. Only the retry bug required intervention.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- T08 complete; `CitationSection` is already imported by `MessageBubble` (from T09 scaffold) — T09 should verify CitationCard and CitationSection meet spec
- Ready for T09 — Citation Components

## Self-Check: PASSED

- `frontend/src/components/chat/MessageBubble.tsx` — FOUND
- `frontend/src/components/chat/MessageThread.tsx` — FOUND
- Commit 5b49f8e — FOUND (`git log --oneline` confirms)
- Build check: `npm run build` → exit 0 ✓
- Known Stubs section present, no blocking stubs ✓

---
*Phase: 02-core-mvp-ui*
*Completed: 2026-07-17*
