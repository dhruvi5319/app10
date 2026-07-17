import { useRef, useEffect } from 'react';
import type { Message } from '@/types/api';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

interface MessageThreadProps {
  messages: Message[];
  streamingContent: string;
  queryInFlight: boolean;
  onRetry?: (query: string) => void;
}

function BotIcon() {
  return (
    <svg
      width="48"
      height="48"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <line x1="12" y1="7" x2="12" y2="11" />
      <line x1="8" y1="16" x2="8" y2="16" strokeWidth="2" />
      <line x1="16" y1="16" x2="16" y2="16" strokeWidth="2" />
    </svg>
  );
}

const NEAR_BOTTOM_THRESHOLD = 150;

export default function MessageThread({
  messages,
  streamingContent,
  queryInFlight,
  onRetry,
}: MessageThreadProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isNearBottomRef = useRef(true);

  // Track whether user is near bottom
  const handleScroll = () => {
    const container = containerRef.current;
    if (!container) return;
    const distFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;
    isNearBottomRef.current = distFromBottom <= NEAR_BOTTOM_THRESHOLD;
  };

  // Auto-scroll when messages or streaming content change
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (isNearBottomRef.current) {
      container.scrollTop = container.scrollHeight;
    }
  }, [messages.length, streamingContent, queryInFlight]);

  // Find streaming placeholder
  const streamingMessageId = queryInFlight
    ? [...messages].reverse().find((m) => m.role === 'assistant')?.message_id ?? null
    : null;

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {messages.length === 0 ? (
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
            color: 'var(--color-text-muted)',
          }}
        >
          <BotIcon />
          <p style={{ fontSize: '0.9rem', textAlign: 'center' }}>
            Ask a question about your uploaded documents.
          </p>
        </div>
      ) : (
        <>
          {messages.map((msg, idx) => {
            const isStreamingThis =
              queryInFlight &&
              msg.role === 'assistant' &&
              msg.message_id === streamingMessageId &&
              streamingContent !== '';

            // For error bubbles, find the preceding user message to retry with
            // the original query — not the __ERROR__ sentinel stored in content
            const retryQuery =
              onRetry && msg.role === 'assistant'
                ? [...messages].slice(0, idx).reverse().find((m) => m.role === 'user')?.content
                : undefined;

            return (
              <MessageBubble
                key={msg.message_id}
                message={msg}
                isStreaming={isStreamingThis}
                streamingContent={isStreamingThis ? streamingContent : undefined}
                onRetry={retryQuery !== undefined ? () => onRetry!(retryQuery) : undefined}
              />
            );
          })}

          {/* Typing indicator (before any streaming content arrives) */}
          {queryInFlight && streamingContent === '' && <TypingIndicator />}
        </>
      )}
    </div>
  );
}
