import { useState, useCallback, useRef } from 'react';

export type ToastVariant = 'info' | 'success' | 'error';

export interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
  persist: boolean; // if true: requires manual dismiss; if false: auto-dismiss in 5s
}

let _idCounter = 0;
function generateId(): string {
  _idCounter += 1;
  return `toast-${Date.now()}-${_idCounter}`;
}

export function useToast(): {
  toasts: ToastItem[];
  addToast: (message: string, variant: ToastVariant, persist?: boolean) => void;
  dismissToast: (id: string) => void;
} {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const addToast = useCallback(
    (message: string, variant: ToastVariant, persist = false) => {
      const id = generateId();
      const item: ToastItem = { id, message, variant, persist };

      setToasts((prev) => [item, ...prev]); // newest on top

      if (!persist) {
        const timer = setTimeout(() => {
          dismissToast(id);
        }, 5000);
        timersRef.current.set(id, timer);
      }
    },
    [dismissToast],
  );

  return { toasts, addToast, dismissToast };
}
