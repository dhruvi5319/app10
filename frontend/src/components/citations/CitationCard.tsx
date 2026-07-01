import { useState } from 'react';
import type { Citation } from '@/types/api';

interface CitationCardProps {
  citation: Citation;
}

const EXCERPT_TRUNCATE_LENGTH = 800;

export default function CitationCard({ citation }: CitationCardProps) {
  const [showFull, setShowFull] = useState(false);

  const { filename, page_number, chunk_index, excerpt } = citation;

  // Defensive: handle null/empty excerpt
  const hasExcerpt = excerpt && excerpt.trim().length > 0;
  const needsTruncation = hasExcerpt && excerpt.length > EXCERPT_TRUNCATE_LENGTH;

  if (!hasExcerpt) {
    console.warn('[CITATION_DATA_MISSING] Empty or null excerpt for chunk', citation.chunk_id);
  }

  const displayPage =
    page_number === null || page_number <= 0 ? 'N/A' : String(page_number);

  const displayExcerpt = needsTruncation && !showFull
    ? excerpt.slice(0, EXCERPT_TRUNCATE_LENGTH)
    : excerpt;

  return (
    <div
      style={{
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-sm)',
        padding: '10px 12px',
        marginBottom: 6,
        fontSize: '0.8rem',
      }}
    >
      {/* Header */}
      <div
        style={{
          fontWeight: 500,
          color: 'var(--color-text-secondary)',
          marginBottom: 6,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 4,
          alignItems: 'center',
        }}
      >
        <span>📄</span>
        <span style={{ color: 'var(--color-text-primary)' }}>{filename}</span>
        <span style={{ color: 'var(--color-text-muted)' }}>—</span>
        <span>page {displayPage}</span>
        <span style={{ color: 'var(--color-text-muted)' }}>—</span>
        <span>chunk {chunk_index + 1}</span>
      </div>

      {/* Excerpt */}
      <blockquote
        style={{
          margin: 0,
          paddingLeft: 10,
          borderLeft: '3px solid var(--color-border)',
          color: 'var(--color-text-secondary)',
          lineHeight: 1.55,
          fontStyle: 'normal',
        }}
      >
        {hasExcerpt ? (
          <>
            <span style={{ whiteSpace: 'pre-wrap' }}>{displayExcerpt}</span>
            {needsTruncation && !showFull && <span>…</span>}
          </>
        ) : (
          <em style={{ color: 'var(--color-text-muted)' }}>[Excerpt unavailable]</em>
        )}
      </blockquote>

      {/* Show more / Show less toggle */}
      {needsTruncation && (
        <button
          onClick={() => setShowFull((prev) => !prev)}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--color-accent)',
            padding: 0,
            marginTop: 6,
            fontSize: '0.78rem',
            textDecoration: 'underline',
          }}
        >
          {showFull ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  );
}
