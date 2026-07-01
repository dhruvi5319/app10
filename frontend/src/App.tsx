import { useSession } from '@/hooks/useSession';

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
      }}
    >
      <div className="spinner" style={{ width: 32, height: 32 }} />
      <p style={{ color: 'var(--color-text-secondary)' }}>Starting session…</p>
    </div>
  );
}

function ErrorScreen({ message }: { message: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '12px',
        padding: '24px',
        textAlign: 'center',
      }}
    >
      <p style={{ color: 'var(--color-error)', fontSize: '1.1rem' }}>
        {message}
      </p>
      <button
        className="btn btn-secondary"
        onClick={() => window.location.reload()}
      >
        Refresh
      </button>
    </div>
  );
}

export default function App() {
  const { sessionId, loading, error } = useSession();

  if (loading) return <LoadingScreen />;
  if (error) return <ErrorScreen message="Failed to start session. Please refresh." />;
  if (!sessionId) return null;

  return (
    <div style={{ height: '100%' }}>
      {/* AppLayout will be rendered here after T03 */}
      <p
        style={{
          padding: '24px',
          color: 'var(--color-text-secondary)',
          textAlign: 'center',
        }}
      >
        Session: {sessionId}
      </p>
    </div>
  );
}
