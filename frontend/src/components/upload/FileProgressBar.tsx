import { truncateFilename } from '@/utils/formatters';
import type { DocumentStatus } from '@/types/api';

interface FileProgressBarProps {
  filename: string;
  status: DocumentStatus;
  progress_pct: number;
  error_message?: string | null;
  onRetry?: () => void;
}

const STAGE_LABELS: Record<DocumentStatus, string> = {
  UPLOADING: 'Uploading…',
  PARSING: 'Parsing…',
  CHUNKING: 'Chunking…',
  EMBEDDING: 'Embedding…',
  INDEXING: 'Indexing…',
  READY: 'Ready ✓',
  FAILED: 'Failed',
};

export default function FileProgressBar({
  filename,
  status,
  progress_pct,
  error_message,
  onRetry,
}: FileProgressBarProps) {
  const isTerminal = status === 'READY' || status === 'FAILED';
  const isEmbedding = status === 'EMBEDDING';

  const barColor =
    status === 'READY'
      ? 'var(--color-success)'
      : status === 'FAILED'
        ? 'var(--color-error)'
        : 'var(--color-accent)';

  return (
    <div
      style={{
        padding: '8px 10px',
        background: 'var(--color-surface-2)',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--color-border)',
        marginBottom: 6,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 4,
        }}
      >
        <span
          style={{
            fontSize: '0.8rem',
            color: 'var(--color-text-primary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
          title={filename}
        >
          {truncateFilename(filename)}
        </span>
        <span
          style={{
            fontSize: '0.75rem',
            color:
              status === 'READY'
                ? 'var(--color-success)'
                : status === 'FAILED'
                  ? 'var(--color-error)'
                  : 'var(--color-text-muted)',
            whiteSpace: 'nowrap',
            marginLeft: 8,
          }}
        >
          {isEmbedding
            ? `Embedding (${Math.round(progress_pct)}%)…`
            : STAGE_LABELS[status]}
        </span>
      </div>

      {/* Progress bar */}
      <div
        style={{
          height: 4,
          background: 'var(--color-border)',
          borderRadius: 2,
          overflow: 'hidden',
        }}
      >
        {isTerminal ? (
          <div
            style={{
              height: '100%',
              width: '100%',
              background: barColor,
              borderRadius: 2,
            }}
          />
        ) : isEmbedding ? (
          <div
            style={{
              height: '100%',
              width: `${progress_pct}%`,
              background: barColor,
              borderRadius: 2,
              transition: 'width 0.3s ease',
            }}
          />
        ) : (
          <div
            style={{
              height: '100%',
              background: barColor,
              borderRadius: 2,
              animation: 'indeterminate 1.5s ease-in-out infinite',
            }}
          />
        )}
      </div>

      {/* Error message + retry */}
      {status === 'FAILED' && (
        <div
          style={{
            marginTop: 6,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 8,
          }}
        >
          <span
            style={{
              fontSize: '0.75rem',
              color: 'var(--color-error)',
              flex: 1,
            }}
          >
            {error_message ?? 'Processing failed.'}
          </span>
          {onRetry && (
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem', padding: '2px 8px' }}
              onClick={onRetry}
            >
              Retry
            </button>
          )}
        </div>
      )}

      <style>{`
        @keyframes indeterminate {
          0% { margin-left: -40%; width: 40%; }
          50% { margin-left: 60%; width: 40%; }
          100% { margin-left: 100%; width: 40%; }
        }
      `}</style>
    </div>
  );
}
