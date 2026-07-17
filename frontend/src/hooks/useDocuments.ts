import { useState, useEffect, useCallback, useRef } from 'react';
import type { Document, DocumentStatus, ProgressEvent } from '@/types/api';
import {
  listDocuments,
  uploadDocument,
  getDocumentStatus,
  deleteDocument as deleteDocumentApi,
  openUploadStream,
} from '@/api/documents';
import { ApiError } from '@/api/client';
import {
  MAX_FILE_SIZE_BYTES,
  ALLOWED_EXTENSIONS,
  POLLING_INTERVAL_MS,
} from '@/utils/constants';

/** Terminal document statuses — no more transitions expected */
const TERMINAL_STATUSES: DocumentStatus[] = ['READY', 'FAILED'];

/** Creates an optimistic document entry while uploading */
function createOptimisticDoc(
  docId: string,
  sessionId: string,
  file: File,
): Document {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? 'txt';
  const fileType = (['pdf', 'txt', 'docx'] as const).includes(
    ext as 'pdf' | 'txt' | 'docx',
  )
    ? (ext as 'pdf' | 'txt' | 'docx')
    : 'txt';

  return {
    doc_id: docId,
    session_id: sessionId,
    filename: file.name,
    file_type: fileType,
    file_size_bytes: file.size,
    status: 'UPLOADING',
    chunk_count: null,
    page_count: null,
    error_message: null,
    uploaded_at: new Date().toISOString(),
    ready_at: null,
  };
}

export function useDocuments(
  sessionId: string,
  onNetworkError?: () => void,
): {
  documents: Document[];
  totalSizeBytes: number;
  uploadFile: (file: File, onStageUpdate?: (status: DocumentStatus, progress_pct: number) => void) => Promise<void>;
  deleteDocument: (docId: string) => Promise<void>;
  refreshDocuments: () => Promise<void>;
} {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [totalSizeBytes, setTotalSizeBytes] = useState(0);

  // Track active SSE streams and polling intervals for cleanup
  const activeStreams = useRef<Map<string, EventSource>>(new Map());
  const activePolls = useRef<Map<string, ReturnType<typeof setInterval>>>(new Map());

  /** Fetch the full document list from the server */
  const refreshDocuments = useCallback(async () => {
    try {
      const response = await listDocuments(sessionId);
      setDocuments(response.documents);
      setTotalSizeBytes(response.total_size_bytes);
    } catch (err) {
      if (err instanceof ApiError && err.errorCode === 'NETWORK_ERROR') {
        onNetworkError?.();
      }
      throw err;
    }
  }, [sessionId, onNetworkError]);

  // Load documents on mount
  useEffect(() => {
    refreshDocuments().catch(() => {
      // Silently ignore initial load errors — error handling in consumers
    });

    return () => {
      // Cleanup all SSE streams and polls on unmount
      activeStreams.current.forEach((stream) => stream.close());
      activePolls.current.forEach((id) => clearInterval(id));
    };
  }, [refreshDocuments]);

  /** Update a single document's status in state */
  const updateDocumentStatus = useCallback(
    (docId: string, updates: Partial<Document>) => {
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.doc_id === docId ? { ...doc, ...updates } : doc,
        ),
      );
    },
    [],
  );

  /** Start polling for document status as fallback when SSE is unavailable */
  function startPolling(docId: string, onStageUpdate?: (status: DocumentStatus, progress_pct: number) => void) {
    if (activePolls.current.has(docId)) return;

    const intervalId = setInterval(async () => {
      try {
        const doc = await getDocumentStatus(docId);
        updateDocumentStatus(docId, {
          status: doc.status,
          chunk_count: doc.chunk_count,
          page_count: doc.page_count,
          error_message: doc.error_message,
          ready_at: doc.ready_at,
        });

        // Notify UploadZone of each stage so FileProgressBar can display it
        if (!TERMINAL_STATUSES.includes(doc.status)) {
          onStageUpdate?.(doc.status, 0);
        }

        if (TERMINAL_STATUSES.includes(doc.status)) {
          clearInterval(intervalId);
          activePolls.current.delete(docId);
        }
      } catch {
        // Ignore polling errors — will retry on next tick
      }
    }, POLLING_INTERVAL_MS);

    activePolls.current.set(docId, intervalId);
  }

  /** Track progress via SSE stream */
  function startSSETracking(docId: string, onStageUpdate?: (status: DocumentStatus, progress_pct: number) => void) {
    let stream: EventSource;
    try {
      stream = openUploadStream(docId);
    } catch {
      // SSE not available — fall back to polling
      startPolling(docId, onStageUpdate);
      return;
    }

    activeStreams.current.set(docId, stream);

    stream.onmessage = (event: MessageEvent<string>) => {
      try {
        const data = JSON.parse(event.data) as ProgressEvent;
        updateDocumentStatus(docId, {
          status: data.status,
        });

        // Notify UploadZone of each stage so FileProgressBar can display it
        onStageUpdate?.(data.status, data.progress_pct ?? 0);

        if (TERMINAL_STATUSES.includes(data.status)) {
          stream.close();
          activeStreams.current.delete(docId);

          // Fetch final state to get chunk_count, page_count, etc.
          getDocumentStatus(docId)
            .then((doc) => {
              updateDocumentStatus(docId, {
                status: doc.status,
                chunk_count: doc.chunk_count,
                page_count: doc.page_count,
                error_message: doc.error_message,
                ready_at: doc.ready_at,
              });
            })
            .catch(() => {
              // Ignore — state will be close enough
            });
        }
      } catch {
        // Ignore malformed SSE events
      }
    };

    stream.onerror = () => {
      stream.close();
      activeStreams.current.delete(docId);
      // Fall back to polling
      startPolling(docId, onStageUpdate);
    };
  }

  /** Validate and upload a file */
  const uploadFile = useCallback(
    async (file: File, onStageUpdate?: (status: DocumentStatus, progress_pct: number) => void) => {
      // Client-side validation
      if (file.size > MAX_FILE_SIZE_BYTES) {
        throw new ApiError(
          0,
          'FILE_TOO_LARGE',
          `File "${file.name}" exceeds the ${MAX_FILE_SIZE_BYTES / 1024 / 1024} MB limit.`,
        );
      }

      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!ALLOWED_EXTENSIONS.includes(ext as '.pdf' | '.txt' | '.docx')) {
        throw new ApiError(
          0,
          'INVALID_FILE_TYPE',
          `File type "${ext}" is not supported. Allowed types: ${ALLOWED_EXTENSIONS.join(', ')}.`,
        );
      }

      // Upload and get doc_id
      let result: { doc_id: string; filename: string; status: string };
      try {
        result = await uploadDocument(sessionId, file);
      } catch (err) {
        if (err instanceof ApiError && err.errorCode === 'NETWORK_ERROR') {
          onNetworkError?.();
        }
        throw err;
      }
      const docId = result.doc_id;

      // Add optimistic entry to state
      const optimisticDoc = createOptimisticDoc(docId, sessionId, file);
      setDocuments((prev) => [...prev, optimisticDoc]);
      setTotalSizeBytes((prev) => prev + file.size);

      // Track progress via SSE (with polling fallback); forward onStageUpdate so
      // UploadZone.inFlightFiles can reflect PARSING/CHUNKING/EMBEDDING/INDEXING
      startSSETracking(docId, onStageUpdate);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [sessionId, updateDocumentStatus, onNetworkError],
  );

  /** Delete a document */
  const deleteDocument = useCallback(
    async (docId: string) => {
      try {
        await deleteDocumentApi(docId);
      } catch (err) {
        if (err instanceof ApiError && err.errorCode === 'NETWORK_ERROR') {
          onNetworkError?.();
        }
        throw err;
      }

      // Remove from state on success
      setDocuments((prev) => {
        const doc = prev.find((d) => d.doc_id === docId);
        if (doc) {
          setTotalSizeBytes((total) =>
            Math.max(0, total - doc.file_size_bytes),
          );
        }
        return prev.filter((d) => d.doc_id !== docId);
      });

      // Clean up any active streams/polls for this doc
      const stream = activeStreams.current.get(docId);
      if (stream) {
        stream.close();
        activeStreams.current.delete(docId);
      }
      const poll = activePolls.current.get(docId);
      if (poll) {
        clearInterval(poll);
        activePolls.current.delete(docId);
      }
    },
    [onNetworkError],
  );

  return {
    documents,
    totalSizeBytes,
    uploadFile,
    deleteDocument,
    refreshDocuments,
  };
}
