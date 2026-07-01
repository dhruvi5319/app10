import type { ToastItem, ToastVariant } from '@/hooks/useToast';

interface ToastProps {
  toast: ToastItem;
  onDismiss: (id: string) => void;
}

const VARIANT_STYLES: Record<
  ToastVariant,
  { background: string; border: string; icon: string }
> = {
  info: {
    background: 'var(--color-surface)',
    border: 'var(--color-border)',
    icon: 'ℹ️',
  },
  success: {
    background: 'rgba(52, 201, 139, 0.1)',
    border: 'rgba(52, 201, 139, 0.3)',
    icon: '✓',
  },
  error: {
    background: 'rgba(229, 83, 75, 0.12)',
    border: 'rgba(229, 83, 75, 0.35)',
    icon: '✕',
  },
};

export default function Toast({ toast, onDismiss }: ToastProps) {
  const style = VARIANT_STYLES[toast.variant];

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 10,
        padding: '12px 14px',
        background: style.background,
        border: `1px solid ${style.border}`,
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
        minWidth: 260,
        maxWidth: 380,
        animation: 'slideInRight 0.2s ease',
        pointerEvents: 'all',
      }}
      role={toast.variant === 'error' ? 'alert' : 'status'}
      aria-live={toast.variant === 'error' ? 'assertive' : 'polite'}
    >
      <span
        style={{
          fontSize: '0.9rem',
          flexShrink: 0,
          marginTop: 1,
          color:
            toast.variant === 'success'
              ? 'var(--color-success)'
              : toast.variant === 'error'
                ? 'var(--color-error)'
                : 'var(--color-text-secondary)',
        }}
      >
        {style.icon}
      </span>

      <p
        style={{
          flex: 1,
          fontSize: '0.875rem',
          color: 'var(--color-text-primary)',
          lineHeight: 1.45,
          margin: 0,
        }}
      >
        {toast.message}
      </p>

      <button
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--color-text-muted)',
          fontSize: '1rem',
          lineHeight: 1,
          padding: '2px 0 0 0',
          flexShrink: 0,
        }}
      >
        ✕
      </button>
    </div>
  );
}
