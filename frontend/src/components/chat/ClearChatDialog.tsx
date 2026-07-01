import { useState, useEffect, useRef } from 'react';

interface ClearChatDialogProps {
  onConfirm: () => Promise<void>;
  onCancel: () => void;
  open: boolean;
}

export default function ClearChatDialog({
  onConfirm,
  onCancel,
  open,
}: ClearChatDialogProps) {
  const [isClearing, setIsClearing] = useState(false);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      setTimeout(() => cancelBtnRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isClearing) onCancel();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, isClearing, onCancel]);

  if (!open) return null;

  const handleConfirm = async () => {
    setIsClearing(true);
    try {
      await onConfirm();
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <div
      className="modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isClearing) onCancel();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="clear-dialog-title"
    >
      <div className="modal-dialog">
        <h2 className="modal-title" id="clear-dialog-title">
          Clear conversation?
        </h2>
        <p className="modal-body">
          Your uploaded documents will not be affected.
        </p>
        <div className="modal-actions">
          <button
            ref={cancelBtnRef}
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isClearing}
          >
            Cancel
          </button>
          <button
            className="btn btn-danger"
            onClick={handleConfirm}
            disabled={isClearing}
            style={{ minWidth: 80 }}
          >
            {isClearing ? (
              <>
                <span className="spinner" />
                Clearing…
              </>
            ) : (
              'Clear'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
