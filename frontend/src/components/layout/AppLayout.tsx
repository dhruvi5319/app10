interface AppLayoutProps {
  sessionId: string;
  children?: React.ReactNode;
}

/**
 * Two-column desktop shell:
 * - Left aside: 280px fixed-width Document Panel
 * - Right main: flex-1 Chat Panel
 *
 * DocumentPanel and ChatPanel are rendered here.
 * Both panels are independently scrollable via overflow-y: auto.
 */
export default function AppLayout({ sessionId, children }: AppLayoutProps) {
  // DocumentPanel and ChatPanel will be imported once T06 and T08 are complete.
  // They are imported lazily below to avoid circular dependency issues during development.
  // In T11 these will be replaced with direct named imports.
  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        background: 'var(--color-bg)',
      }}
    >
      <aside
        style={{
          width: '280px',
          flexShrink: 0,
          borderRight: '1px solid var(--color-border)',
          overflowY: 'auto',
          background: 'var(--color-surface)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* DocumentPanel will be inserted here in T06/T11 */}
        <div style={{ padding: '16px', color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
          Document Panel — {sessionId.slice(0, 8)}…
        </div>
        {children}
      </aside>
      <main
        style={{
          flex: 1,
          minWidth: 0,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* ChatPanel will be inserted here in T08/T11 */}
        <div style={{ padding: '16px', color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
          Chat Panel — {sessionId.slice(0, 8)}…
        </div>
      </main>
    </div>
  );
}
