export const MAX_FILE_SIZE_MB = 20;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.docx'] as const;
export type AllowedExtension = (typeof ALLOWED_EXTENSIONS)[number];

export const POLLING_INTERVAL_MS = 1500;

export const MAX_DOCUMENTS_PER_SESSION = 10;
