# Phase 3 State

## Current Position
- **Phase:** 03-polish-developer-experience
- **Status:** In progress

## Task Progress

| Task | Name | Status | Commit |
|------|------|--------|--------|
| T01 | Harden backend config.py | in_progress | — |
| T02 | Responsive tablet breakpoint | pending | — |
| T03 | Responsive mobile breakpoint + FAB | pending | — |
| T04 | Accessibility ARIA + keyboard + focus | pending | — |
| T05 | Colour contrast audit + WCAG AA | pending | — |

## Decisions
- Pydantic `model_validator(mode='after')` used for cross-field validation (chunk overlap, API key checks, path writability)
- `_validate_settings_at_startup()` exported but not auto-called at import; validation happens naturally when `get_settings()` is first called in lifespan
- `log_startup_config()` extracted to `config.py` and called from `main.py` lifespan after DB init
