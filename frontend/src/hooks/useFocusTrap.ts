import { RefObject, useEffect, useRef } from 'react';

const FOCUSABLE_SELECTORS = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  '[contenteditable="true"]',
].join(', ');

/**
 * Traps keyboard focus within `containerRef` while `isActive` is true.
 *
 * Behaviour:
 * - On activation: focus moves to the first focusable element inside the container.
 * - Tab / Shift+Tab cycle within the container; wraps at boundaries.
 * - On deactivation: focus is restored to the element that was focused when the
 *   trap was activated (typically the trigger button).
 */
export function useFocusTrap(
  containerRef: RefObject<HTMLElement | null>,
  isActive: boolean,
): void {
  // Store the element that was focused before the trap activated
  const previouslyFocusedRef = useRef<Element | null>(null);

  useEffect(() => {
    if (!isActive) return;

    // Remember the element that had focus when the dialog opened
    previouslyFocusedRef.current = document.activeElement;

    const container = containerRef.current;
    if (!container) return;

    // Focus the first focusable element
    const focusable = Array.from(
      container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS),
    );
    if (focusable.length > 0) {
      focusable[0].focus();
    }

    // Trap Tab / Shift+Tab
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      const current = Array.from(
        container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS),
      );
      if (current.length === 0) {
        e.preventDefault();
        return;
      }

      const first = current[0];
      const last = current[current.length - 1];

      if (e.shiftKey) {
        // Shift+Tab: wrap backward
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        // Tab: wrap forward
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);

      // Restore focus to the previously focused element
      const prev = previouslyFocusedRef.current;
      if (prev && typeof (prev as HTMLElement).focus === 'function') {
        (prev as HTMLElement).focus();
      }
    };
  }, [isActive, containerRef]);
}
