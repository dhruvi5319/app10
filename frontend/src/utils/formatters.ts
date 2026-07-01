/**
 * Returns a human-readable relative time string.
 * e.g. "just now", "2 minutes ago", "3 hours ago", "yesterday"
 */
export function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);

  if (diffSeconds < 30) return 'just now';
  if (diffSeconds < 60) return `${diffSeconds} seconds ago`;

  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) {
    return diffMinutes === 1 ? '1 minute ago' : `${diffMinutes} minutes ago`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return diffHours === 1 ? '1 hour ago' : `${diffHours} hours ago`;
  }

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

/**
 * Formats a byte count into a human-readable file size string.
 * e.g. 1024 → "1.0 KB", 1048576 → "1.0 MB"
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

/**
 * Truncates a filename to max characters, preserving the extension.
 * e.g. truncateFilename("very-long-document-name.pdf", 20) → "very-long-docum….pdf"
 */
export function truncateFilename(name: string, max = 30): string {
  if (name.length <= max) return name;

  const lastDot = name.lastIndexOf('.');
  if (lastDot === -1 || lastDot === 0) {
    return name.slice(0, max - 1) + '…';
  }

  const ext = name.slice(lastDot); // e.g. ".pdf"
  const base = name.slice(0, lastDot);
  const availableBase = max - ext.length - 1; // -1 for ellipsis

  if (availableBase <= 0) {
    return name.slice(0, max - 1) + '…';
  }

  return base.slice(0, availableBase) + '…' + ext;
}
