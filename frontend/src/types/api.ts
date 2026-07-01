export interface Session {
  session_id: string;
  created_at: string;
  document_count: number;
}

export type DocumentStatus =
  | 'UPLOADING'
  | 'PARSING'
  | 'CHUNKING'
  | 'EMBEDDING'
  | 'INDEXING'
  | 'READY'
  | 'FAILED';

export interface Document {
  doc_id: string;
  session_id: string;
  filename: string;
  file_type: 'pdf' | 'txt' | 'docx';
  file_size_bytes: number;
  status: DocumentStatus;
  chunk_count: number | null;
  page_count: number | null;
  error_message: string | null;
  uploaded_at: string;
  ready_at: string | null;
}

export interface DocumentListResponse {
  session_id: string;
  document_count: number;
  total_size_bytes: number;
  documents: Document[];
}

export interface ProgressEvent {
  doc_id: string;
  status: DocumentStatus;
  progress_pct: number;
  message: string;
}

export interface Citation {
  chunk_id: string;
  doc_id: string;
  filename: string;
  page_number: number | null;
  chunk_index: number;
  excerpt: string;
  similarity_score: number;
}

export interface Message {
  message_id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  is_refusal: boolean | null;
  retrieved_chunks: Citation[] | null;
  created_at: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  message_count: number;
  messages: Message[];
}

export interface QueryInitResponse {
  message_id: string;
}

export interface SSETokenEvent {
  type: 'token';
  delta: string;
}

export interface SSEDoneEvent {
  type: 'done';
  message: Message;
}

export interface SSEErrorEvent {
  type: 'error';
  error_code: string;
  message: string;
}

export type SSEEvent = SSETokenEvent | SSEDoneEvent | SSEErrorEvent;

export interface ApiErrorShape {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}
