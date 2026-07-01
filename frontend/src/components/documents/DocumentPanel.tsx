import { useState, useEffect } from 'react';
import { useDocuments } from '@/hooks/useDocuments';
import { formatFileSize } from '@/utils/formatters';
import { MAX_DOCUMENTS_PER_SESSION } from '@/utils/constants';
import UploadZone from '@/components/upload/UploadZone';
import DocumentCard from './DocumentCard';

interface DocumentPanelProps {
  sessionId: string;
  onHasReadyDocumentChange?: (hasReady: boolean) => void;
  /** Called when user swipes/drags drawer down on mobile to close */
  onDrawerClose?: () => void;
}

const COLLAPSED_STORAGE_KEY = 'doc_panel_collapsed';

function ChevronIcon({ direction }: { direction: 'left' | 'right' }) {
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
      style={{
        transform: direction === 'right' ? 'rotate(180deg)' : 'none',
        transition: 'transform 0.2s ease',
      }}
    >
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}

function FolderIcon() {
  return (
    <svg
      width="40"
      height="40"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );
}

export default function DocumentPanel({
  sessionId,
  onHasReadyDocumentChange,
  onDrawerClose,
}: DocumentPanelProps) {
  const { documents, totalSizeBytes, uploadFile, deleteDocument } =
    useDocuments(sessionId);

  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(COLLAPSED_STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  });

  const hasReadyDocument = documents.some((d) => d.status === 'READY');

  // Notify parent of hasReadyDocument changes
  useEffect(() => {
    onHasReadyDocumentChange?.(hasReadyDocument);
  }, [hasReadyDocument, onHasReadyDocumentChange]);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(COLLAPSED_STORAGE_KEY, String(next));
      } catch {
        // localStorage unavailable — continue without persistence
      }
      return next;
    });
  };

  // ── Drag-to-dismiss (mobile bottom drawer) ────────────────────────────────
  const [touchStartY, setTouchStartY] = useState<number | null>(null);

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStartY(e.touches[0].clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (touchStartY === null) return;
    const delta = e.touches[0].clientY - touchStartY;
    if (delta > 100) {
      setTouchStartY(null);
      onDrawerClose?.();
    }
  };

  const handleTouchEnd = () => {
    setTouchStartY(null);
  };

  if (collapsed) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '12px 0',
          gap: 8,
        }}
      >
        <button
          className="btn-ghost"
          onClick={toggleCollapsed}
          aria-label="Expand document panel"
          style={{ padding: 8 }}
        >
          <ChevronIcon direction="right" />
        </button>
        <span
          aria-hidden="true"
          style={{
            fontSize: '0.65rem',
            color: 'var(--color-text-muted)',
            writingMode: 'vertical-lr',
            textOrientation: 'mixed',
            transform: 'rotate(180deg)',
            marginTop: 8,
          }}
        >
          Documents ({documents.length})
        </span>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Panel header */}
      <div
        style={{
          padding: '16px',
          borderBottom: '1px solid var(--color-border)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 4,
          }}
        >
          <h2
            id="doc-panel-heading"
            style={{
              fontSize: '0.875rem',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
            }}
          >
            Documents ({documents.length} / {MAX_DOCUMENTS_PER_SESSION})
          </h2>
          <button
            className="btn-ghost"
            onClick={toggleCollapsed}
            aria-label="Collapse document panel"
            style={{ padding: 4 }}
          >
            <ChevronIcon direction="left" />
          </button>
        </div>
        <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
          {formatFileSize(totalSizeBytes)} used
        </p>
      </div>

      {/* Document list */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px',
        }}
      >
        {documents.length === 0 ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '32px 16px',
              textAlign: 'center',
              color: 'var(--color-text-muted)',
            }}
          >
            <div style={{ marginBottom: 12, opacity: 0.5 }}>
              <FolderIcon />
            </div>
            <p style={{ fontSize: '0.875rem', marginBottom: 4, color: 'var(--color-text-secondary)' }}>
              No documents uploaded yet.
            </p>
            <p style={{ fontSize: '0.78rem' }}>Drag a file here or tap to upload.</p>
          </div>
        ) : (
          documents.map((doc) => (
            <DocumentCard
              key={doc.doc_id}
              document={doc}
              onDelete={deleteDocument}
            />
          ))
        )}
      </div>

      {/* Upload zone at bottom */}
      <div
        style={{
          padding: '12px',
          borderTop: '1px solid var(--color-border)',
          flexShrink: 0,
        }}
      >
        <UploadZone onUpload={uploadFile} />
      </div>
    </div>
  );
}
