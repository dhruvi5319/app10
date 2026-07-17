---
phase: 02-core-mvp-ui
plan: "09"
subsystem: ui
tags: [vite, env, proxy, cors, session-init, gap-closure]

# Dependency graph
requires:
  - phase: 02-core-mvp-ui
    provides: Frontend scaffold with Vite proxy config and apiFetch client
provides:
  - Empty VITE_API_BASE_URL in both frontend/.env and frontend/.env.example
  - apiFetch builds relative /api/... paths routed by Vite dev-server proxy
affects: [UAT-Test-1, session-init, all-downstream-UAT-tests]

# Tech tracking
tech-stack:
  added: []
  patterns: ["VITE_API_BASE_URL= (empty) → relative paths → Vite proxy routes to backend"]

key-files:
  created: []
  modified:
    - frontend/.env.example
    - frontend/.env

key-decisions:
  - "VITE_API_BASE_URL left empty so apiFetch uses relative /api/... paths via Vite proxy rather than absolute http://localhost:8000/... URLs that browser blocks as mixed-content/CORS"

patterns-established:
  - "Env template documents intent via comment: leave VITE_API_BASE_URL empty for proxy mode"

# Metrics
duration: 1min
completed: 2026-07-17
---

# Phase 02 Plan 09: Fix VITE_API_BASE_URL for Vite Proxy Routing Summary

**Both frontend env files updated: `VITE_API_BASE_URL=http://localhost:8000` → `VITE_API_BASE_URL=` (empty), making apiFetch build relative `/api/...` paths correctly routed through the Vite dev-server proxy to the FastAPI backend.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-07-17T20:16:42Z
- **Completed:** 2026-07-17T20:17:16Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Fixed root cause of UAT Test 1 failure: absolute `VITE_API_BASE_URL` was causing `apiFetch` to produce `http://localhost:8000/api/sessions` URLs that browsers block as mixed-content or cross-origin when served over HTTPS / non-localhost
- `frontend/.env.example` updated with comment explaining the empty-value intent (use Vite proxy in dev, set absolute URL only for standalone deploys)
- `frontend/.env` updated so the active dev environment immediately uses the correct relative path routing
- All 8 remaining UAT tests unblocked — every skipped test was waiting on session init (Test 1) to pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix VITE_API_BASE_URL in both env files** - `a9dd9f9` (fix)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `frontend/.env.example` — Changed `VITE_API_BASE_URL=http://localhost:8000` to commented explanation + `VITE_API_BASE_URL=`
- `frontend/.env` — Changed `VITE_API_BASE_URL=http://localhost:8000` to `VITE_API_BASE_URL=`

## Decisions Made

- Left `frontend/src/api/client.ts` and `frontend/vite.config.ts` untouched — both were already correct. The client already uses `?? ''` fallback; the Vite proxy already forwards `/api` to `http://localhost:8000`.
- Added explanatory comment in `.env.example` to document why the value is intentionally empty.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Gap 02-09 closed: session initialization will no longer produce mixed-content/CORS errors
- All UAT tests that were skipped due to Test 1 failure are now unblocked
- Ready for Phase 03 (responsive polish / production deploy) or re-running the UAT suite

---
*Phase: 02-core-mvp-ui*
*Completed: 2026-07-17*

## Self-Check: PASSED

- `frontend/.env.example` exists and contains `VITE_API_BASE_URL=` ✅
- `frontend/.env` exists and contains `VITE_API_BASE_URL=` ✅
- No `localhost:8000` in either file (non-comment lines) ✅
- Task commit `a9dd9f9` exists ✅
- No build step required (env-only change, no code compiled) ✅
- No blocking stubs found ✅
