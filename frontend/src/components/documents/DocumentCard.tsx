import { useState } from 'react';
import type { Document } from '@/types/api';
import { truncateFilename, formatRelativeTime } from '@/utils/formatters';
import DeleteConfirmDialog from './DeleteConfirmDialog';

interface DocumentCardProps {
  document: Document;
  onDelete: (docId: string) => Promise<void>;
}

const PROCESSING_STATUSES = new Set([
  'UPLOADING',
  'PARSING',
  'CHUNKING',
  'EMBEDDING',
  'INDEXING',
]);

function FileTypeIcon({ type }: { type: Document['file_type'] }) {
  const colors: Record<Document['file_type'], string> = {
    pdf: '#e5534b',
    docx: '#4a90e2',
    txt: '#34c98b',
  };
  const labels: Record<Document['file_type'], string> = {
    pdf: 'PDF',
    docx: 'DOC',
    txt: 'TXT',
  };

  return (
    <div
      style={{
        width: 36,
        height: 36,
        borderRadius: 6,
        background: `${colors[type]}22`,
        border: `1px solid ${colors[type]}44`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '0.6rem',
        fontWeight: 700,
        color: colors[type],
        flexShrink: 0,
        letterSpacing: '0.02em',
      }}
    >
      {labels[type]}
    </div>
  );
}

function TrashIcon() {
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
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6M14 11v6" />
      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </svg>
  );
}

function StatusBadge({ status }: { status: Document['status'] }) {
  if (status === 'READY') {
    return <span className="badge badge-ready">Ready</span>;
  }

  if (PROCESSING_STATUSES.has(status)) {
    return (
      <span className="badge badge-processing">
        <span className="spinner" style={{ width: 8, height: 8, borderWidth: 1.5 }} />
        Processing
      </span>
    );
  }

  if (status === 'FAILED') {
    return <span className="badge badge-failed">Failed</span>;
  }

  return null;
}

export default function DocumentCard({ document: doc, onDelete }: DocumentCardProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const isProcessing = PROCESSING_STATUSES.has(doc.status);

  const handleDeleteConfirm = async () => {
    await onDelete(doc.doc_id);
    setShowDeleteDialog(false);
  };

  return (
    <>
      <div
        className="card"
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 10,
          padding: '10px 12px',
          marginBottom: 6,
          transition: 'opacity 0.3s ease',
        }}
      >
        <FileTypeIcon type={doc.file_type} />

        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              marginBottom: 2,
            }}
          >
            <span
              style={{
                fontSize: '0.875rem',
                fontWeight: 500,
                color: 'var(--color-text-primary)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={doc.filename}
            >
              {truncateFilename(doc.filename)}
            </span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              flexWrap: 'wrap',
            }}
          >
            <StatusBadge status={doc.status} />
            <span
              style={{
                fontSize: '0.72rem',
                color: 'var(--color-text-muted)',
              }}
            >
              {formatRelativeTime(doc.uploaded_at)}
            </span>
          </div>

          {doc.status === 'FAILED' && doc.error_message && (
            <p
              style={{
                fontSize: '0.72rem',
                color: 'var(--color-error)',
                marginTop: 4,
                lineHeight: 1.3,
              }}
            >
              {doc.error_message}
            </p>
          )}
        </div>

        <button
          className="btn-ghost"
          onClick={() => setShowDeleteDialog(true)}
          disabled={isProcessing}
          aria-label={isProcessing ? `Cannot delete ${doc.filename} while processing` : `Delete ${doc.filename}`}
          title={isProcessing ? 'Cannot delete while processing' : `Delete ${doc.filename}`}
          style={{
            padding: 6,
            borderRadius: 'var(--radius-sm)',
            color: isProcessing
              ? 'var(--color-text-muted)'
              : 'var(--color-text-secondary)',
            flexShrink: 0,
          }}
        >
          <TrashIcon />
        </button>
      </div>

      <DeleteConfirmDialog
        filename={doc.filename}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setShowDeleteDialog(false)}
        open={showDeleteDialog}
      />
    </>
  );
}
