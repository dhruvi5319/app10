import { apiFetch } from './client';
import type { QueryInitResponse, ChatHistoryResponse } from '@/types/api';

export async function sendQuery(
  sessionId: string,
  query: string,
): Promise<QueryInitResponse> {
  return apiFetch<QueryInitResponse>('/api/chat/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      query,
      include_history: true,
    }),
  });
}

export function openChatStream(messageId: string): EventSource {
  return new EventSource(
    `${import.meta.env.VITE_API_BASE_URL ?? ''}/api/chat/stream/${messageId}`,
  );
}

export async function getHistory(sessionId: string): Promise<ChatHistoryResponse> {
  return apiFetch<ChatHistoryResponse>(`/api/chat/history/${sessionId}`);
}

export async function clearHistory(sessionId: string): Promise<void> {
  await apiFetch(`/api/chat/history/${sessionId}`, { method: 'DELETE' });
}
