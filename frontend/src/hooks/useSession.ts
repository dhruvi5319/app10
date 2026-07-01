// Placeholder — will be implemented in T02
import { useState } from 'react';

export function useSession(): {
  sessionId: string | null;
  loading: boolean;
  error: string | null;
} {
  const [sessionId] = useState<string | null>(null);
  const [loading] = useState(false);
  const [error] = useState<string | null>(null);
  return { sessionId, loading, error };
}
