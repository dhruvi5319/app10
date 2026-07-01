export default function TypingIndicator() {
  return (
    <div
      role="status"
      aria-label="Assistant is typing"
      style={{
        display: 'flex',
        justifyContent: 'flex-start',
        marginBottom: 12,
        paddingLeft: 4,
      }}
    >
      <div
        style={{
          background: 'var(--color-assistant-bubble)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          borderBottomLeftRadius: 4,
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          minHeight: 44,
        }}
      >
        <span className="typing-dot" style={{ animationDelay: '0ms' }} />
        <span className="typing-dot" style={{ animationDelay: '200ms' }} />
        <span className="typing-dot" style={{ animationDelay: '400ms' }} />

        <style>{`
          .typing-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--color-text-muted);
            display: inline-block;
            animation: typingFade 1.2s ease-in-out infinite;
          }
          @keyframes typingFade {
            0%, 60%, 100% { opacity: 0.2; transform: scale(0.9); }
            30% { opacity: 1; transform: scale(1.15); }
          }
        `}</style>
      </div>
    </div>
  );
}
