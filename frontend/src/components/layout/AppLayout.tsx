import { useState, useCallback } from 'react';
import DocumentPanel from '@/components/documents/DocumentPanel';
import ChatPanel from '@/components/chat/ChatPanel';

interface AppLayoutProps {
  sessionId: string;
}

/**
 * Two-column desktop shell:
 * - Left aside: 280px fixed-width Document Panel (independently scrollable)
 * - Right main: flex-1 Chat Panel (independently scrollable)
 *
 * hasReadyDocument is derived from DocumentPanel's useDocuments state
 * and piped into ChatPanel to gate the send button.
 */
export default function AppLayout({ sessionId }: AppLayoutProps) {
  const [hasReadyDocument, setHasReadyDocument] = useState(false);

  const handleHasReadyDocumentChange = useCallback((hasReady: boolean) => {
    setHasReadyDocument(hasReady);
  }, []);

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        background: 'var(--color-bg)',
      }}
    >
      <aside
        style={{
          width: '280px',
          flexShrink: 0,
          borderRight: '1px solid var(--color-border)',
          overflowY: 'auto',
          background: 'var(--color-surface)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <DocumentPanel
          sessionId={sessionId}
          onHasReadyDocumentChange={handleHasReadyDocumentChange}
        />
      </aside>

      <main
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
    </div>
  );
}
