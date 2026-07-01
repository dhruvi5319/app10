import { useState, useRef, KeyboardEvent, FormEvent } from 'react';

interface ChatInputProps {
  onSend: (query: string) => void;
  disabled: boolean;
  hasReadyDocument: boolean;
}

function SendIcon({ spinning }: { spinning: boolean }) {
  if (spinning) {
    return <span className="spinner" style={{ width: 16, height: 16 }} />;
  }
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

export default function ChatInput({
  onSend,
  disabled,
  hasReadyDocument,
}: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isEmpty = value.trim().length === 0;
  const canSend = !isEmpty && !disabled && hasReadyDocument;

  const handleSend = () => {
    if (!canSend) return;
    const query = value.trim();
    setValue('');
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    onSend(query);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    // Shift+Enter inserts newline naturally — do nothing
  };

  const handleInput = (e: FormEvent<HTMLTextAreaElement>) => {
    const ta = e.currentTarget;
    // Auto-grow up to ~5 lines (5 * ~24px line height = 120px)
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
    setValue(ta.value);
  };

  return (
    <div
      style={{
        borderTop: '1px solid var(--color-border)',
        padding: '12px 16px',
        flexShrink: 0,
        background: 'var(--color-surface)',
      }}
    >
      {/* Guard message */}
      {!hasReadyDocument && (
        <div
          style={{
            marginBottom: 8,
            padding: '6px 12px',
            background: 'rgba(245, 166, 35, 0.1)',
            border: '1px solid rgba(245, 166, 35, 0.25)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.8rem',
            color: 'var(--color-warning)',
            textAlign: 'center',
          }}
        >
          Upload a document first to start asking questions.
        </div>
      )}

      {/* Input row */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          alignItems: 'flex-end',
        }}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          onChange={() => {}} // Controlled via onInput
          placeholder="Ask a question about your documents…"
          disabled={disabled || !hasReadyDocument}
          rows={1}
          style={{
            flex: 1,
            resize: 'none',
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            color: 'var(--color-text-primary)',
            fontSize: '0.9rem',
            lineHeight: 1.5,
            outline: 'none',
            transition: 'border-color 0.15s ease',
            minHeight: 44,
            maxHeight: 120,
            overflowY: 'auto',
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-accent)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-border)';
          }}
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={!canSend}
          title={
            !hasReadyDocument
              ? 'Upload a document first'
              : isEmpty
                ? 'Type a message first'
                : disabled
                  ? 'Waiting for response…'
                  : 'Send message'
          }
          style={{
            padding: '10px 14px',
            flexShrink: 0,
            height: 44,
            minWidth: 44,
          }}
        >
          <SendIcon spinning={disabled && !isEmpty} />
        </button>
      </div>

      <p
        style={{
          marginTop: 6,
          fontSize: '0.7rem',
          color: 'var(--color-text-muted)',
          textAlign: 'center',
        }}
      >
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  );
}
