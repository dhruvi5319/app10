
---

## F06: Responsive & Accessible UI

**Priority:** P2 — Medium, Post-MVP polish  
**PRD Reference:** §6 F6

**Description:** The application is fully functional and visually polished across desktop (≥ 1024 px), tablet (600–1023 px), and mobile (< 600 px) viewports. The layout adapts gracefully to each breakpoint without sacrificing core functionality. Accessibility is implemented to WCAG 2.1 AA standards, ensuring the application is usable with keyboard navigation, screen readers, and browser font-scaling preferences.

---

### Terminology

- **Breakpoint:** A viewport width threshold at which the layout changes. Three tiers: Mobile (< 600 px), Tablet (600–1023 px), Desktop (≥ 1024 px).
- **WCAG AA:** Web Content Accessibility Guidelines 2.1 Level AA — the target compliance level for colour contrast, keyboard access, and screen reader support.
- **Touch Target:** A tappable UI element sized ≥ 44 × 44 px per WCAG 2.5.5 to be reliably tappable on touchscreens.
- **Drawer:** A mobile UI pattern where the Document Panel slides in from the left or bottom on a toggle, overlaying the chat.
- **Focus State:** A visible keyboard-focus indicator (outline or ring) on interactive elements, required for keyboard navigation.
- **ARIA Label:** An `aria-label` or `aria-labelledby` attribute providing a text description of an element to screen readers where a visible label is absent.
- **Skip Link:** A hidden-until-focused link at the top of the page that jumps keyboard focus directly to the main content area.

---

### Sub-features

- **F06-A:** Desktop layout — side-by-side Document Panel (left) and Chat (right)
- **F06-B:** Tablet layout — collapsible Document Panel, chat takes full width when panel closed
- **F06-C:** Mobile layout — Document Panel as a bottom drawer, chat occupies full viewport
- **F06-D:** Touch-friendly tap targets (≥ 44 × 44 px) for all interactive elements
- **F06-E:** WCAG AA colour contrast for all text and UI controls
- **F06-F:** Full keyboard navigation with visible focus states
- **F06-G:** ARIA labels on icon buttons and interactive components
- **F06-H:** Semantic HTML structure (landmarks, headings hierarchy)
- **F06-I:** Font scaling support (rem-based sizing; adapts to browser text size settings)
- **F06-J:** Skip navigation link for keyboard/screen reader users

---

### Process

#### Layout Adaptation

1. **CSS breakpoints** are defined at 600 px (mobile/tablet boundary) and 1024 px (tablet/desktop boundary).
2. **Desktop (≥ 1024 px):** Document Panel occupies a fixed 280 px left column; Chat panel fills remaining width. Both are always visible.
3. **Tablet (600–1023 px):** Document Panel is collapsed by default (icon-strip only, 48 px wide). A toggle button expands it to full 280 px as an overlay or side-by-side. Chat fills full width when panel is collapsed.
4. **Mobile (< 600 px):** Document Panel is hidden by default. A "Documents" FAB (floating action button) or bottom bar toggle opens it as a bottom drawer at 60% viewport height with a drag-to-dismiss handle. Chat occupies the full viewport.
5. The upload drag-and-drop zone gracefully degrades to tap-to-upload on touch devices (no drag events available on mobile).

#### Accessibility

6. All interactive elements (buttons, inputs, upload zone) must be focusable via Tab key and operable via keyboard (Enter/Space for buttons, Enter for form submission).
7. A **skip link** ("Skip to main content") is rendered as the first focusable element in the DOM, hidden visually until focused, linking to the chat input area.
8. All icon-only buttons (delete, collapse, send) must have an `aria-label` attribute describing their action.
9. The upload zone must have `role="button"` or `role="region"` with an `aria-label="File upload area"`.
10. Chat message thread must use `role="log"` with `aria-live="polite"` so screen readers announce new messages without interrupting ongoing reading.
11. Typing indicator must have `role="status"` and `aria-label="Assistant is typing"`.
12. Colour contrast for body text must be ≥ 4.5:1 against background (WCAG AA). UI controls must be ≥ 3:1.
13. All font sizes must be defined in `rem` units; setting the browser's minimum font size must scale the UI proportionally.
14. Modal/dialog components (delete confirmation, clear chat confirmation) must trap focus within the dialog while open and restore focus to the triggering element on close.

---

### Inputs

No runtime API inputs. F06 is entirely a frontend implementation concern specified for the UI layer.

---

### Outputs

- A layout that passes WCAG 2.1 AA automated checks (e.g., axe-core or Lighthouse accessibility audit score ≥ 90).
- A responsive design that renders correctly at 320 px (minimum mobile width), 768 px (tablet), and 1440 px (large desktop).

---

### Validation Rules

- Every interactive element must be reachable by Tab key and operable by keyboard.
- No element may have `tabindex="-1"` unless it is legitimately hidden or non-interactive.
- Colour contrast ratio must meet ≥ 4.5:1 for normal text, ≥ 3:1 for large text and UI components.
- Touch targets must be ≥ 44 × 44 px on mobile breakpoints.
- `aria-label` must be provided for all icon-only buttons; must describe the action, not the icon (e.g., `aria-label="Delete document"`, not `aria-label="trash icon"`).
- The `role="log"` chat container must have `aria-live="polite"` (not `assertive`) to avoid interrupting screen reader output.
- Focus must not become trapped outside of modals; modals must implement a focus trap while open.
- The application must not use colour alone as the only means of conveying information (e.g., status badges must include text labels in addition to colour).

---

### Error States

*F06 has no runtime error states.* Implementation failures are caught during QA/testing phases (accessibility audit failures, layout overflow at specific viewports). These are tracked as defects, not runtime errors.

---

### API Surface (this feature)

None — F06 is a frontend layout and accessibility concern.

---

### Schema Surface (this feature)

- Panel collapsed/expanded state may be stored in `localStorage` (`key: rag_panel_collapsed`, value: `"true"` | `"false"`).
- No server-side schema required.
