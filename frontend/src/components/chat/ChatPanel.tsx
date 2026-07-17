import { useState, useCallback } from 'react';
import { useChat } from '@/hooks/useChat';
import { useToastContext } from '@/context/ToastContext';
import MessageThread from './MessageThread';
import ChatInput from './ChatInput';
import ClearChatDialog from './ClearChatDialog';

interface ChatPanelProps {
  sessionId: string;
  hasReadyDocument: boolean;
  /** Called when a network error is detected during any chat API call */
  onNetworkError?: () => void;
}

export default function ChatPanel({
  sessionId,
  hasReadyDocument,
  onNetworkError,
}: ChatPanelProps) {
  const { addToast } = useToastContext();

  const handleLlmError = useCallback(
    (message: string) => {
      addToast(message, 'error', false);
    },
    [addToast],
  );

  const { messages, streamingContent, queryInFlight, sendMessage, clearMessages } =
    useChat(sessionId, hasReadyDocument, onNetworkError, handleLlmError);

  const [showClearDialog, setShowClearDialog] = useState(false);

  const handleClearConfirm = async () => {
    await clearMessages();
    setShowClearDialog(false);
  };

  const handleRetry = (query: string) => {
    sendMessage(query).catch(() => {
      // Errors are surfaced as error bubbles in the thread
    });
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 20px',
          borderBottom: '1px solid var(--color-border)',
          flexShrink: 0,
          background: 'var(--color-surface)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '1.2rem' }}>🤖</span>
          <h1
            style={{
              fontSize: '1rem',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
            }}
          >
            RAG Chatbot
          </h1>
        </div>

        {messages.length > 0 && (
          <button
            className="btn btn-secondary"
            onClick={() => setShowClearDialog(true)}
            disabled={queryInFlight}
            aria-label="Clear chat history"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            Clear Chat
          </button>
        )}
      </div>

      {/* Message thread */}
      <MessageThread
        messages={messages}
        streamingContent={streamingContent}
        queryInFlight={queryInFlight}
        onRetry={handleRetry}
      />

      {/* Input bar */}
      <ChatInput
        onSend={(query) => {
          sendMessage(query).catch(() => {});
        }}
        disabled={queryInFlight}
        hasReadyDocument={hasReadyDocument}
      />

      {/* Clear chat confirmation dialog */}
      <ClearChatDialog
        onConfirm={handleClearConfirm}
        onCancel={() => setShowClearDialog(false)}
        open={showClearDialog}
      />
    </div>
  );
}
