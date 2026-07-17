import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '@/types/api';
import { formatRelativeTime } from '@/utils/formatters';
import { isErrorMessage, extractErrorText } from '@/hooks/useChat';
import CitationSection from '@/components/citations/CitationSection';

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
  streamingContent?: string;
  /** Called when user clicks "Try again". The caller is responsible for
   *  providing the correct query (i.e. the preceding user message content). */
  onRetry?: () => void;
}

export default function MessageBubble({
  message,
  isStreaming = false,
  streamingContent,
  onRetry,
}: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isError = !isUser && isErrorMessage(message.content);
  const errorText = isError ? extractErrorText(message.content) : '';

  const displayContent =
    isStreaming && streamingContent !== undefined
      ? streamingContent
      : message.content;

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 16,
        paddingLeft: isUser ? '20%' : 4,
        paddingRight: isUser ? 4 : '20%',
      }}
    >
      <div
        style={{
          maxWidth: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start',
        }}
      >
        {/* Bubble */}
        <div
          style={{
            background: isError
              ? 'rgba(229, 83, 75, 0.12)'
              : isUser
                ? 'var(--color-user-bubble)'
                : 'var(--color-assistant-bubble)',
            border: isError
              ? '1px solid rgba(229, 83, 75, 0.3)'
              : '1px solid var(--color-border)',
            borderRadius: isUser
              ? 'var(--radius-lg) var(--radius-lg) 4px var(--radius-lg)'
              : 'var(--radius-lg) var(--radius-lg) var(--radius-lg) 4px',
            padding: '12px 16px',
            color: 'var(--color-text-primary)',
            lineHeight: 1.65,
            wordBreak: 'break-word',
          }}
        >
          {isUser ? (
            <p style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: '0.9rem' }}>
              {message.content}
            </p>
          ) : isError ? (
            <div>
              <p style={{ margin: 0, color: 'var(--color-error)', fontSize: '0.9rem' }}>
                {errorText}
              </p>
              {onRetry && (
                <button
                  style={{
                    marginTop: 8,
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-accent)',
                    cursor: 'pointer',
                    padding: 0,
                    fontSize: '0.85rem',
                    textDecoration: 'underline',
                  }}
                  onClick={() => onRetry()}
                >
                  Try again
                </button>
              )}
            </div>
          ) : (
            <div className="markdown-body" style={{ fontSize: '0.9rem' }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {isStreaming ? `${displayContent}▍` : displayContent}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <span
          style={{
            fontSize: '0.7rem',
            color: 'var(--color-text-muted)',
            marginTop: 4,
            paddingLeft: isUser ? 0 : 4,
            paddingRight: isUser ? 4 : 0,
          }}
        >
          {formatRelativeTime(message.created_at)}
        </span>

        {/* Citations — only for non-streaming, non-error assistant messages */}
        {!isUser && !isError && !isStreaming && (
          <div style={{ width: '100%', paddingLeft: 4 }}>
            <CitationSection
              retrieved_chunks={message.retrieved_chunks}
              is_refusal={message.is_refusal}
            />
          </div>
        )}
      </div>
    </div>
  );
}
