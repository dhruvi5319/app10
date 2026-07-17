import { useState, useEffect, useCallback, useRef } from 'react';
import type { Message, SSEEvent } from '@/types/api';
import { sendQuery, openChatStream, getHistory, clearHistory } from '@/api/chat';
import { ApiError } from '@/api/client';

/** Sentinel prefix for error bubble content */
const ERROR_PREFIX = '__ERROR__';

/** Creates an optimistic user message for immediate display */
function createUserMessage(sessionId: string, content: string): Message {
  return {
    message_id: `user-optimistic-${Date.now()}`,
    session_id: sessionId,
    role: 'user',
    content,
    is_refusal: null,
    retrieved_chunks: null,
    created_at: new Date().toISOString(),
  };
}

/** Creates a placeholder assistant message while streaming */
function createAssistantPlaceholder(sessionId: string): Message {
  return {
    message_id: `assistant-streaming-${Date.now()}`,
    session_id: sessionId,
    role: 'assistant',
    content: '',
    is_refusal: null,
    retrieved_chunks: null,
    created_at: new Date().toISOString(),
  };
}

export function useChat(
  sessionId: string,
  _hasReadyDocument: boolean,
  onNetworkError?: () => void,
  onLlmError?: (message: string) => void,
): {
  messages: Message[];
  streamingContent: string;
  queryInFlight: boolean;
  sendMessage: (query: string) => Promise<void>;
  clearMessages: () => Promise<void>;
} {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [queryInFlight, setQueryInFlight] = useState(false);

  // Track the placeholder message_id during streaming
  const placeholderIdRef = useRef<string | null>(null);
  const activeStreamRef = useRef<EventSource | null>(null);

  // Scroll flag — consumed by MessageThread
  const shouldScrollRef = useRef(false);

  // Mark for scroll on new messages
  useEffect(() => {
    shouldScrollRef.current = true;
  }, [messages.length, streamingContent]);

  // Hydrate history on mount
  useEffect(() => {
    let cancelled = false;

    getHistory(sessionId)
      .then((response) => {
        if (!cancelled) {
          setMessages(response.messages);
        }
      })
      .catch(() => {
        // Ignore history load errors silently — empty thread is acceptable
      });

    return () => {
      cancelled = true;
      // Close any active stream on unmount
      activeStreamRef.current?.close();
    };
  }, [sessionId]);

  const sendMessage = useCallback(
    async (query: string) => {
      if (queryInFlight) return;

      setQueryInFlight(true);
      setStreamingContent('');

      const userMessage = createUserMessage(sessionId, query);
      const placeholder = createAssistantPlaceholder(sessionId);
      placeholderIdRef.current = placeholder.message_id;

      // Optimistic UI: add user + placeholder messages
      setMessages((prev) => [...prev, userMessage, placeholder]);

      let messageId: string;
      try {
        const response = await sendQuery(sessionId, query);
        messageId = response.message_id;
      } catch (err) {
        if (err instanceof ApiError && err.errorCode === 'NETWORK_ERROR') {
          onNetworkError?.();
        }
        const errorText =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Failed to send message.';

        // Notify caller of LLM/API error for toast display
        onLlmError?.(errorText);

        // Replace placeholder with error bubble
        setMessages((prev) =>
          prev.map((m) =>
            m.message_id === placeholderIdRef.current
              ? { ...m, content: `${ERROR_PREFIX}${errorText}` }
              : m,
          ),
        );
        setQueryInFlight(false);
        return;
      }

      // Open SSE stream for token delivery
      let stream: EventSource;
      try {
        stream = openChatStream(messageId);
        activeStreamRef.current = stream;
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.message_id === placeholderIdRef.current
              ? {
                  ...m,
                  content: `${ERROR_PREFIX}Failed to open response stream.`,
                }
              : m,
          ),
        );
        setQueryInFlight(false);
        return;
      }

      stream.onmessage = (event: MessageEvent<string>) => {
        try {
          const data = JSON.parse(event.data) as SSEEvent;

          if (data.type === 'token') {
            setStreamingContent((prev) => prev + data.delta);
          } else if (data.type === 'done') {
            // Replace placeholder with final message
            stream.close();
            activeStreamRef.current = null;

            setMessages((prev) => {
              const withoutPlaceholder = prev.filter(
                (m) => m.message_id !== placeholderIdRef.current,
              );
              return [...withoutPlaceholder, data.message];
            });
            setStreamingContent('');
            setQueryInFlight(false);
            placeholderIdRef.current = null;
          } else if (data.type === 'error') {
            stream.close();
            activeStreamRef.current = null;

            // Notify caller of LLM error for toast display
            onLlmError?.(data.message);

            setMessages((prev) =>
              prev.map((m) =>
                m.message_id === placeholderIdRef.current
                  ? {
                      ...m,
                      content: `${ERROR_PREFIX}${data.message}`,
                    }
                  : m,
              ),
            );
            setStreamingContent('');
            setQueryInFlight(false);
            placeholderIdRef.current = null;
          }
        } catch {
          // Ignore malformed SSE events
        }
      };

      stream.onerror = () => {
        stream.close();
        activeStreamRef.current = null;

        setMessages((prev) =>
          prev.map((m) =>
            m.message_id === placeholderIdRef.current
              ? {
                  ...m,
                  content: `${ERROR_PREFIX}Connection to server lost. Please try again.`,
                }
              : m,
          ),
        );
        setStreamingContent('');
        setQueryInFlight(false);
        placeholderIdRef.current = null;
      };
    },
    [sessionId, queryInFlight, onNetworkError, onLlmError],
  );

  const clearMessages = useCallback(async () => {
    try {
      await clearHistory(sessionId);
    } catch (err) {
      if (err instanceof ApiError && err.errorCode === 'NETWORK_ERROR') {
        onNetworkError?.();
      }
      throw err;
    }
    setMessages([]);
    setStreamingContent('');
  }, [sessionId, onNetworkError]);

  return {
    messages,
    streamingContent,
    queryInFlight,
    sendMessage,
    clearMessages,
  };
}

/** Helper to check if a message content is an error bubble */
export function isErrorMessage(content: string): boolean {
  return content.startsWith(ERROR_PREFIX);
}

/** Extract error text from error bubble content */
export function extractErrorText(content: string): string {
  return content.startsWith(ERROR_PREFIX) ? content.slice(ERROR_PREFIX.length) : content;
}
