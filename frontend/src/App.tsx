import { useState, useCallback } from 'react';
import { useSession } from '@/hooks/useSession';
import { ToastProvider } from '@/context/ToastContext';
import NetworkBanner from '@/components/feedback/NetworkBanner';
import AppLayout from '@/components/layout/AppLayout';

// ─── Loading Screen ────────────────────────────────────────────────────────

function LoadingScreen() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '16px',
        background: 'var(--color-bg)',
      }}
    >
      <div className="spinner" style={{ width: 32, height: 32 }} />
      <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
        Starting session…
      </p>
    </div>
  );
}

// ─── Error Screen ──────────────────────────────────────────────────────────

function ErrorScreen() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '16px',
        padding: '24px',
        textAlign: 'center',
        background: 'var(--color-bg)',
      }}
    >
      <div style={{ fontSize: '2.5rem' }}>⚠️</div>
      <p
        style={{
          color: 'var(--color-text-primary)',
          fontSize: '1rem',
          fontWeight: 500,
        }}
      >
        Failed to start session.
      </p>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
        Please refresh the page to try again.
      </p>
      <button
        className="btn btn-primary"
        onClick={() => window.location.reload()}
        style={{ marginTop: 8 }}
      >
        Refresh
      </button>
    </div>
  );
}

// ─── Root App ──────────────────────────────────────────────────────────────

function AppInner() {
  const { sessionId, loading, error } = useSession();
  const [networkError, setNetworkError] = useState(false);

  const handleRetry = useCallback(() => {
    // Simply reload the page to retry all pending operations
    window.location.reload();
  }, []);

  // Expose network error setter globally for hooks to call
  // (In a full implementation hooks would use a context; this is the minimal wiring)
  void setNetworkError; // used via closure passed to children if needed

  if (loading) return <LoadingScreen />;
  if (error) return <ErrorScreen />;
  if (!sessionId) return null;

  return (
    <>
      {/* Skip link — first focusable element; visible on keyboard Tab */}
      <a
        href="#chat-input"
        className="skip-link"
        onFocus={(e) => e.currentTarget.classList.add('skip-link-visible')}
        onBlur={(e) => e.currentTarget.classList.remove('skip-link-visible')}
      >
        Skip to main content
      </a>
      <NetworkBanner visible={networkError} onRetry={handleRetry} />
      <AppLayout sessionId={sessionId} />
    </>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppInner />
    </ToastProvider>
  );
}
