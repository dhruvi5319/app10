import { createContext, useContext, ReactNode } from 'react';
import { useToast, type ToastVariant, type ToastItem } from '@/hooks/useToast';
import ToastContainer from '@/components/feedback/ToastContainer';

interface ToastContextValue {
  addToast: (message: string, variant: ToastVariant, persist?: boolean) => void;
  dismissToast: (id: string) => void;
  toasts: ToastItem[];
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const { toasts, addToast, dismissToast } = useToast();

  return (
    <ToastContext.Provider value={{ addToast, dismissToast, toasts }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
}

export function useToastContext(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToastContext must be used within a <ToastProvider>');
  }
  return ctx;
}
