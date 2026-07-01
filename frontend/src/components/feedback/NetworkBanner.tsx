interface NetworkBannerProps {
  visible: boolean;
  onRetry: () => void;
}

export default function NetworkBanner({ visible, onRetry }: NetworkBannerProps) {
  if (!visible) return null;

  return (
    <div
      style={{
        position: 'sticky',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        background: 'var(--color-error)',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 12,
        padding: '10px 16px',
        fontSize: '0.875rem',
        fontWeight: 500,
      }}
      role="alert"
      aria-live="assertive"
    >
      <span>⚠️ Connection lost. Check your network.</span>
      <button
        onClick={onRetry}
        style={{
          background: 'rgba(255,255,255,0.2)',
          border: '1px solid rgba(255,255,255,0.4)',
          borderRadius: 'var(--radius-sm)',
          color: 'white',
          cursor: 'pointer',
          padding: '4px 12px',
          fontSize: '0.85rem',
          fontWeight: 600,
        }}
      >
        Retry
      </button>
    </div>
  );
}
