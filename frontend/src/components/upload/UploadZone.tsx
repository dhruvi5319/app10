import { useState, useRef, useCallback, useEffect, DragEvent, ChangeEvent } from 'react';
import { ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '@/utils/constants';
import { ApiError } from '@/api/client';
import FileProgressBar from './FileProgressBar';
import type { DocumentStatus } from '@/types/api';

interface UploadZoneProps {
  onUpload: (file: File) => Promise<void>;
  disabled?: boolean;
}

interface InFlightFile {
  id: string; // unique key (Date.now + filename)
  file: File;
  status: DocumentStatus;
  progress_pct: number;
  error_message?: string;
}

function CloudUploadIcon() {
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
    >
      <polyline points="16 16 12 12 8 16" />
      <line x1="12" y1="12" x2="12" y2="21" />
      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
    </svg>
  );
}

export default function UploadZone({ onUpload, disabled = false }: UploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [inFlightFiles, setInFlightFiles] = useState<InFlightFile[]>([]);
  const [errors, setErrors] = useState<Array<{ id: string; message: string }>>([]);
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Detect touch device on mount
  useEffect(() => {
    setIsTouchDevice('ontouchstart' in window || navigator.maxTouchPoints > 0);
  }, []);

  const dismissError = useCallback((id: string) => {
    setErrors((prev) => prev.filter((e) => e.id !== id));
  }, []);

  const addError = useCallback((id: string, message: string) => {
    setErrors((prev) => [...prev, { id, message }]);
  }, []);

  const validateFile = useCallback((file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext as '.pdf' | '.txt' | '.docx')) {
      return `"${file.name}" is not a supported file type. Allowed: PDF, DOCX, TXT.`;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `"${file.name}" exceeds the ${MAX_FILE_SIZE_MB} MB limit.`;
    }
    return null;
  }, []);

  const processFiles = useCallback(
    async (files: File[]) => {
      for (const file of files) {
        const errorMsg = validateFile(file);
        const fileId = `${Date.now()}-${file.name}`;

        if (errorMsg) {
          addError(fileId, errorMsg);
          continue;
        }

        // Add to in-flight tracker
        const entry: InFlightFile = {
          id: fileId,
          file,
          status: 'UPLOADING',
          progress_pct: 0,
        };
        setInFlightFiles((prev) => [...prev, entry]);

        try {
          await onUpload(file);
          // Mark as completed — remove from in-flight after brief delay
          setInFlightFiles((prev) =>
            prev.map((f) => (f.id === fileId ? { ...f, status: 'READY', progress_pct: 100 } : f)),
          );
          setTimeout(() => {
            setInFlightFiles((prev) => prev.filter((f) => f.id !== fileId));
          }, 2000);
        } catch (err) {
          const message =
            err instanceof ApiError
              ? err.message
              : err instanceof Error
                ? err.message
                : 'Upload failed.';
          // Show the error inside the FileProgressBar (which already includes a Retry
          // button). Do NOT also call addError — that would display the same message
          // twice (once in FileProgressBar, once in the inline errors list).
          setInFlightFiles((prev) =>
            prev.map((f) =>
              f.id === fileId ? { ...f, status: 'FAILED', error_message: message } : f,
            ),
          );
        }
      }
    },
    [onUpload, validateFile],
  );

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragOver(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      if (disabled) return;

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        processFiles(files);
      }
    },
    [disabled, processFiles],
  );

  const handleFileChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files ?? []);
      if (files.length > 0) {
        processFiles(files);
      }
      // Reset input so the same file can be selected again
      if (inputRef.current) inputRef.current.value = '';
    },
    [processFiles],
  );

  const handleClick = useCallback(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.click();
    }
  }, [disabled]);

  const handleRetry = useCallback(
    (entry: InFlightFile) => {
      setInFlightFiles((prev) => prev.filter((f) => f.id !== entry.id));
      processFiles([entry.file]);
    },
    [processFiles],
  );

  const borderColor = isDragOver
    ? 'var(--color-accent)'
    : 'var(--color-border)';

  const bgColor = isDragOver
    ? 'rgba(108, 99, 255, 0.08)'
    : 'transparent';

  const uploadLabel = isTouchDevice
    ? 'File upload area. Tap to browse files.'
    : 'File upload area. Press Enter or Space to browse files.';

  return (
    <div>
      {/* Drop zone */}
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label={disabled ? 'Upload disabled' : uploadLabel}
        title={disabled ? 'Start a session first' : undefined}
        onClick={handleClick}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') handleClick();
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${borderColor}`,
          borderRadius: 'var(--radius-md)',
          padding: '20px 16px',
          textAlign: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          transition: 'border-color 0.15s ease, background-color 0.15s ease',
          backgroundColor: bgColor,
          opacity: disabled ? 0.5 : 1,
        }}
      >
        <div style={{ color: 'var(--color-text-muted)', marginBottom: 8 }}>
          <CloudUploadIcon />
        </div>
        {isTouchDevice ? (
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: 4 }}>
            <strong style={{ color: 'var(--color-text-primary)' }}>Tap to browse files</strong>
          </p>
        ) : (
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: 4 }}>
            <strong style={{ color: 'var(--color-text-primary)' }}>Drag files here</strong> or{' '}
            <span style={{ color: 'var(--color-accent)', textDecoration: 'underline' }}>
              click to browse
            </span>
          </p>
        )}
        <p className="drag-instruction" style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
          Supports PDF, DOCX, TXT — up to {MAX_FILE_SIZE_MB} MB each
        </p>
      </div>

      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt,.docx"
        multiple
        style={{ display: 'none' }}
        onChange={handleFileChange}
        disabled={disabled}
      />

      {/* In-flight progress bars */}
      {inFlightFiles.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {inFlightFiles.map((entry) => (
            <FileProgressBar
              key={entry.id}
              filename={entry.file.name}
              status={entry.status}
              progress_pct={entry.progress_pct}
              error_message={entry.error_message}
              onRetry={entry.status === 'FAILED' ? () => handleRetry(entry) : undefined}
            />
          ))}
        </div>
      )}

      {/* Inline errors */}
      {errors.map((err) => (
        <div
          key={err.id}
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8,
            marginTop: 6,
            padding: '6px 10px',
            background: 'rgba(229, 83, 75, 0.1)',
            border: '1px solid rgba(229, 83, 75, 0.3)',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <span
            style={{
              flex: 1,
              fontSize: '0.78rem',
              color: 'var(--color-error)',
              lineHeight: 1.4,
            }}
          >
            {err.message}
          </span>
          <button
            onClick={() => dismissError(err.id)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--color-error)',
              fontSize: '1rem',
              lineHeight: 1,
              padding: 0,
              flexShrink: 0,
            }}
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
