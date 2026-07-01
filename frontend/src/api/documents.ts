import { apiFetch } from './client';
import type { Document, DocumentListResponse } from '@/types/api';

export async function listDocuments(sessionId: string): Promise<DocumentListResponse> {
  return apiFetch<DocumentListResponse>(`/api/documents?session_id=${sessionId}`);
}

export async function uploadDocument(
  sessionId: string,
  file: File,
): Promise<{ doc_id: string; filename: string; status: string }> {
  const form = new FormData();
  form.append('file', file);
  form.append('session_id', sessionId);
  return apiFetch('/api/documents/upload', { method: 'POST', body: form });
}

export async function getDocumentStatus(docId: string): Promise<Document> {
  return apiFetch<Document>(`/api/documents/${docId}/status`);
}

export async function deleteDocument(docId: string): Promise<void> {
  await apiFetch(`/api/documents/${docId}`, { method: 'DELETE' });
}

export function openUploadStream(docId: string): EventSource {
  return new EventSource(
    `${import.meta.env.VITE_API_BASE_URL ?? ''}/api/documents/upload/stream?doc_id=${docId}`,
  );
}
