import { useState, useEffect, useRef } from 'react';
import { useFocusTrap } from '@/hooks/useFocusTrap';

interface DeleteConfirmDialogProps {
  filename: string;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
  open: boolean;
}

export default function DeleteConfirmDialog({
  filename,
  onConfirm,
  onCancel,
  open,
}: DeleteConfirmDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  // Focus trap: traps Tab inside dialog and restores focus on close
  useFocusTrap(dialogRef, open);

  // Trap Escape key
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isDeleting) onCancel();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, isDeleting, onCancel]);

  if (!open) return null;

  const handleConfirm = async () => {
    setIsDeleting(true);
    try {
      await onConfirm();
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div
      className="modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isDeleting) onCancel();
      }}
    >
      <div
        ref={dialogRef}
        className="modal-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-dialog-title"
      >
        <h2 className="modal-title" id="delete-dialog-title">
          Delete document?
        </h2>
        <p className="modal-body">
          <strong
            style={{
              color: 'var(--color-text-primary)',
              wordBreak: 'break-word',
            }}
          >
            {filename}
          </strong>{' '}
          will be removed from the current session and cannot be undone.
        </p>
        <div className="modal-actions">
          <button
            ref={cancelBtnRef}
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isDeleting}
            aria-label="Cancel delete"
          >
            Cancel
          </button>
          <button
            className="btn btn-danger"
            onClick={handleConfirm}
            disabled={isDeleting}
            style={{ minWidth: 90 }}
          >
            {isDeleting ? (
              <>
                <span className="spinner" />
                Deleting…
              </>
            ) : (
              'Delete'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
