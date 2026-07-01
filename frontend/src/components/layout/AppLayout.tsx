import { useState, useCallback, useEffect } from 'react';
import DocumentPanel from '@/components/documents/DocumentPanel';
import ChatPanel from '@/components/chat/ChatPanel';

interface AppLayoutProps {
  sessionId: string;
}

const TABLET_EXPANDED_KEY = 'doc_panel_tablet_expanded';

function DocumentsIcon() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function ChevronLeftIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}

/**
 * Responsive two-column shell.
 *
 * Desktop (≥ 1024px): always shows both panels side-by-side.
 * Tablet (600–1023px): doc panel starts collapsed (icon strip, 48px);
 *   toggle button expands to 280px overlay. State persisted in localStorage.
 * Mobile (< 600px): doc panel hidden; FAB opens as bottom drawer with
 *   drag-to-dismiss (swipe down > 100px) and backdrop tap to close.
 */
export default function AppLayout({ sessionId }: AppLayoutProps) {
  const [hasReadyDocument, setHasReadyDocument] = useState(false);

  // Tablet: panel expanded toggle (persisted)
  const [isPanelExpanded, setIsPanelExpanded] = useState(() => {
    try {
      return localStorage.getItem(TABLET_EXPANDED_KEY) === 'true';
    } catch {
      return false;
    }
  });

  // Mobile: drawer open state
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleHasReadyDocumentChange = useCallback((hasReady: boolean) => {
    setHasReadyDocument(hasReady);
  }, []);

  const toggleTabletPanel = useCallback(() => {
    setIsPanelExpanded((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(TABLET_EXPANDED_KEY, String(next));
      } catch {
        // localStorage unavailable
      }
      return next;
    });
  }, []);

  const openDrawer = useCallback(() => setIsDrawerOpen(true), []);
  const closeDrawer = useCallback(() => setIsDrawerOpen(false), []);

  // Close drawer on Escape key
  useEffect(() => {
    if (!isDrawerOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeDrawer();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isDrawerOpen, closeDrawer]);

  // Build CSS class for the doc-panel aside
  const panelClasses = [
    'doc-panel',
    isPanelExpanded ? 'panel-expanded' : '',
    isDrawerOpen ? 'drawer-open' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        background: 'var(--color-bg)',
        position: 'relative',
      }}
    >
      {/* Skip link (first DOM element for keyboard users) */}
      <a
        href="#chat-input"
        className="skip-link"
        onFocus={(e) => e.currentTarget.classList.add('skip-link-visible')}
        onBlur={(e) => e.currentTarget.classList.remove('skip-link-visible')}
      >
        Skip to main content
      </a>

      {/* Mobile backdrop */}
      {isDrawerOpen && (
        <div
          className="drawer-backdrop"
          onClick={closeDrawer}
          aria-hidden="true"
        />
      )}

      {/* Document panel aside */}
      <aside
        aria-label="Document library"
        className={panelClasses}
        style={{
          flexShrink: 0,
          borderRight: '1px solid var(--color-border)',
          overflowY: 'auto',
          background: 'var(--color-surface)',
          display: 'flex',
          flexDirection: 'column',
          // Desktop: fixed 280px width (CSS media queries override on tablet/mobile)
          width: 'var(--panel-width)',
          transition: 'width 0.2s ease',
        }}
      >
        {/* Tablet toggle button (CSS hides on desktop / mobile) */}
        <button
          className="panel-toggle-btn"
          onClick={toggleTabletPanel}
          aria-label={isPanelExpanded ? 'Collapse document panel' : 'Expand document panel'}
          style={{ margin: '8px auto' }}
        >
          {isPanelExpanded ? <ChevronLeftIcon /> : <ChevronRightIcon />}
        </button>

        {/* Panel content wrapper — hidden on tablet when collapsed */}
        <div
          className="panel-content"
          style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}
        >
          {/* Drawer handle (visible only on mobile) */}
          <div className="drawer-handle" aria-hidden="true" />

          <DocumentPanel
            sessionId={sessionId}
            onHasReadyDocumentChange={handleHasReadyDocumentChange}
            onDrawerClose={closeDrawer}
          />
        </div>
      </aside>

      {/* Main chat area */}
      <main
        id="main-content"
        aria-label="Chat interface"
        style={{
          flex: 1,
          minWidth: 0,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <ChatPanel
          sessionId={sessionId}
          hasReadyDocument={hasReadyDocument}
        />
      </main>

      {/* Mobile FAB — Documents */}
      <button
        className="fab-documents"
        onClick={openDrawer}
        aria-label="Open document library"
        aria-expanded={isDrawerOpen}
      >
        <DocumentsIcon />
      </button>
    </div>
  );
}
