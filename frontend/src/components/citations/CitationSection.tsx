import { useState } from 'react';
import type { Citation } from '@/types/api';
import CitationCard from './CitationCard';

interface CitationSectionProps {
  retrieved_chunks: Citation[] | null;
  is_refusal: boolean | null;
}

function ChevronDownIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{
        transform: expanded ? 'rotate(180deg)' : 'none',
        transition: 'transform 0.2s ease',
        flexShrink: 0,
      }}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

export default function CitationSection({
  retrieved_chunks,
  is_refusal,
}: CitationSectionProps) {
  const [expanded, setExpanded] = useState(false);

  // Don't render for refusals or empty/null chunks
  if (is_refusal === true || !retrieved_chunks || retrieved_chunks.length === 0) {
    return null;
  }

  const count = retrieved_chunks.length;

  return (
    <div
      style={{
        marginTop: 10,
        borderTop: '1px solid var(--color-border)',
        paddingTop: 8,
      }}
    >
      {/* Toggle header */}
      <button
        onClick={() => setExpanded((prev) => !prev)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '4px 0',
          color: 'var(--color-text-secondary)',
          fontSize: '0.8rem',
          fontWeight: 500,
          width: '100%',
          textAlign: 'left',
        }}
        aria-expanded={expanded}
      >
        <ChevronDownIcon expanded={expanded} />
        <span>
          Sources ({count})
        </span>
      </button>

      {/* Expanded citation cards */}
      {expanded && (
        <div style={{ marginTop: 8 }}>
          {retrieved_chunks.map((citation) => (
            <CitationCard key={citation.chunk_id} citation={citation} />
          ))}
        </div>
      )}
    </div>
  );
}
