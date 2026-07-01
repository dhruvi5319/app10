import { useState, useEffect } from 'react';
import { createSession, getSession } from '@/api/sessions';
import { ApiError } from '@/api/client';

const SESSION_STORAGE_KEY = 'session_id';

export function useSession(): {
  sessionId: string | null;
  loading: boolean;
  error: string | null;
} {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function initSession() {
      try {
        const storedId = sessionStorage.getItem(SESSION_STORAGE_KEY);

        if (storedId) {
          // Try to reuse existing session
          try {
            const session = await getSession(storedId);
            if (!cancelled) {
              setSessionId(session.session_id);
            }
            return;
          } catch (err) {
            // If 404, fall through to create a new session
            if (err instanceof ApiError && err.statusCode === 404) {
              sessionStorage.removeItem(SESSION_STORAGE_KEY);
              // Fall through to create new session
            } else {
              throw err;
            }
          }
        }

        // Create a new session
        const session = await createSession();
        if (!cancelled) {
          sessionStorage.setItem(SESSION_STORAGE_KEY, session.session_id);
          setSessionId(session.session_id);
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error ? err.message : 'Failed to start session';
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    initSession();

    return () => {
      cancelled = true;
    };
  }, []);

  return { sessionId, loading, error };
}
