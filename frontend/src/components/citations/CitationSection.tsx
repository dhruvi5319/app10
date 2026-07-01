import type { Citation } from '@/types/api';

interface CitationSectionProps {
  retrieved_chunks: Citation[] | null;
  is_refusal: boolean | null;
}

// Stub — full implementation in T09
export default function CitationSection({
  retrieved_chunks,
  is_refusal,
}: CitationSectionProps) {
  if (is_refusal === true || !retrieved_chunks || retrieved_chunks.length === 0) {
    return null;
  }
  return (
    <div style={{ marginTop: 8, fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
      Sources ({retrieved_chunks.length}) — loading…
    </div>
  );
}
