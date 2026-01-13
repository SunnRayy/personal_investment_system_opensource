/**
 * API Client for WealthOS React SPA
 *
 * A robust, type-safe API client that connects to the Flask backend.
 * Handles authentication, error handling, and request/response logging.
 */

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';
const IS_DEV = import.meta.env.DEV;

// Error types
export interface ApiError {
  status: number;
  message: string;
  component?: string;
  timestamp: string;
}

// Result type for all API calls
export type ApiResult<T> =
  | { success: true; data: T }
  | { success: false; error: ApiError };

// Request options
interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  timeout?: number;
}

/**
 * Log API requests in development mode
 */
function logRequest(method: string, url: string, status?: number, duration?: number): void {
  if (!IS_DEV) return;

  const statusColor = status && status >= 200 && status < 300 ? '\x1b[32m' : '\x1b[31m';
  const resetColor = '\x1b[0m';

  if (status !== undefined && duration !== undefined) {
    console.log(
      `API: ${method} ${url} -> ${statusColor}${status}${resetColor} (${duration.toFixed(0)}ms)`
    );
  } else {
    console.log(`API: ${method} ${url} -> pending...`);
  }
}

/**
 * Create an ApiError from various error sources
 */
function createApiError(status: number, message: string, component?: string): ApiError {
  return {
    status,
    message,
    component,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Core fetch wrapper with authentication and error handling
 */
async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<ApiResult<T>> {
  const {
    method = 'GET',
    body,
    headers = {},
    timeout = 30000,
  } = options;

  const url = `${API_BASE_URL}${endpoint}`;
  const startTime = performance.now();

  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    logRequest(method, endpoint);

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
      credentials: 'include', // Include cookies for Flask session auth
    });

    clearTimeout(timeoutId);
    const duration = performance.now() - startTime;
    logRequest(method, endpoint, response.status, duration);

    // Parse response body
    const contentType = response.headers.get('content-type');
    let data: unknown;

    if (contentType?.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    // Handle non-2xx responses
    if (!response.ok) {
      const errorMessage =
        typeof data === 'object' && data !== null && 'error' in data
          ? String((data as { error: unknown }).error)
          : typeof data === 'object' && data !== null && 'message' in data
            ? String((data as { message: unknown }).message)
            : `HTTP ${response.status}: ${response.statusText}`;

      const component =
        typeof data === 'object' && data !== null && 'component' in data
          ? String((data as { component: unknown }).component)
          : undefined;

      return {
        success: false,
        error: createApiError(response.status, errorMessage, component),
      };
    }

    return { success: true, data: data as T };

  } catch (error) {
    clearTimeout(timeoutId);
    const duration = performance.now() - startTime;

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        logRequest(method, endpoint, 408, duration);
        return {
          success: false,
          error: createApiError(408, `Request timeout after ${timeout}ms`),
        };
      }

      // Network error (server not running, CORS, etc.)
      logRequest(method, endpoint, 0, duration);
      return {
        success: false,
        error: createApiError(0, `Network error: ${error.message}`),
      };
    }

    return {
      success: false,
      error: createApiError(500, 'Unknown error occurred'),
    };
  }
}

// HTTP method convenience functions
export const api = {
  get: <T>(endpoint: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(endpoint, { ...options, method: 'POST', body }),

  put: <T>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(endpoint, { ...options, method: 'PUT', body }),

  delete: <T>(endpoint: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
};

export default api;
