/**
 * Centralized HTTP client with error handling.
 * All API calls should use this utility.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * API error structure from backend.
 */
export interface ApiError {
  detail: string;
  code?: string;
}

/**
 * Custom error class for API errors.
 */
export class HttpError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
    this.code = code;
  }
}

/**
 * Request options extending fetch options.
 */
interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  timeout?: number;
}

/**
 * Centralized fetch wrapper with error handling.
 *
 * @param endpoint - API endpoint (relative to API_URL)
 * @param options - Request options
 * @returns Promise resolving to JSON response
 * @throws HttpError on non-2xx responses
 */
export async function fetchJSON<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, timeout = 30000, ...fetchOptions } = options;

  const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorCode: string | undefined;

      try {
        const errorBody: ApiError = await response.json();
        errorMessage = errorBody.detail || errorMessage;
        errorCode = errorBody.code;
      } catch {
        // JSON parsing failed, use status text
      }

      throw new HttpError(errorMessage, response.status, errorCode);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof HttpError) {
      throw error;
    }

    if (error instanceof Error && error.name === 'AbortError') {
      throw new HttpError('Request timed out', 408, 'TIMEOUT');
    }

    throw new HttpError(
      error instanceof Error ? error.message : 'Network error',
      0,
      'NETWORK_ERROR'
    );
  }
}

/**
 * GET request helper.
 */
export function get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
  return fetchJSON<T>(endpoint, { ...options, method: 'GET' });
}

/**
 * POST request helper.
 */
export function post<T>(
  endpoint: string,
  body?: unknown,
  options?: RequestOptions
): Promise<T> {
  return fetchJSON<T>(endpoint, { ...options, method: 'POST', body });
}

/**
 * PUT request helper.
 */
export function put<T>(
  endpoint: string,
  body?: unknown,
  options?: RequestOptions
): Promise<T> {
  return fetchJSON<T>(endpoint, { ...options, method: 'PUT', body });
}

/**
 * DELETE request helper.
 */
export function del<T>(endpoint: string, options?: RequestOptions): Promise<T> {
  return fetchJSON<T>(endpoint, { ...options, method: 'DELETE' });
}
