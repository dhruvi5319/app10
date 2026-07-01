import { apiFetch } from './client';
import type { Session } from '@/types/api';

export async function createSession(): Promise<Session> {
  return apiFetch<Session>('/api/sessions', { method: 'POST' });
}

export async function getSession(sessionId: string): Promise<Session> {
  return apiFetch<Session>(`/api/sessions/${sessionId}`);
}
