const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export class ApiError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly errorCode: string,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Base fetch wrapper that:
 * - Prepends BASE_URL to all paths
 * - Sets Content-Type: application/json unless the body is FormData
 * - On 4xx/5xx: reads JSON body, throws ApiError(status, error_code, message)
 * - On network failure (TypeError): throws ApiError(0, 'NETWORK_ERROR', ...)
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const headers = new Headers(options.headers);

  // Only set Content-Type to JSON if not multipart/FormData
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    if (options.body && typeof options.body === 'string') {
      headers.set('Content-Type', 'application/json');
    }
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err) {
    // Network failure (no connection, DNS error, etc.)
    const message =
      err instanceof TypeError ? err.message : 'Network request failed';
    throw new ApiError(0, 'NETWORK_ERROR', message);
  }

  if (!response.ok) {
    let errorCode = 'UNKNOWN_ERROR';
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

    try {
      const body = await response.json();
      // FastAPI's default HTTPException handler wraps the detail one level deep:
      // { "detail": { "error_code": "...", "message": "..." } }
      // The generic Exception handler emits fields at the top level directly.
      // Unwrap the envelope when present; fall back to the body itself.
      const payload = body?.detail && typeof body.detail === 'object' ? body.detail : body;
      errorCode = payload.error_code ?? errorCode;
      errorMessage = payload.message ?? errorMessage;
    } catch {
      // Could not parse error body — use defaults
    }

    throw new ApiError(response.status, errorCode, errorMessage);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
