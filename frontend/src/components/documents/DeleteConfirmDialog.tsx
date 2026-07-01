import { useState, useEffect, useRef } from 'react';

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

  // Focus cancel button when dialog opens
  useEffect(() => {
    if (open) {
      setTimeout(() => cancelBtnRef.current?.focus(), 50);
    }
  }, [open]);

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
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
    >
      <div className="modal-dialog">
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
