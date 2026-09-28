import { ApiErrorEnvelope } from '../types/api';

const DEFAULT_BASE_URL = '/api';
let csrfToken: string | null = null;

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

export function getBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (!envUrl) return DEFAULT_BASE_URL;
  let clean = envUrl.trim().replace(/\/+$/, '');
  if (!clean.endsWith('/api')) {
    clean += '/api';
  }
  return clean;
}

export class ApiError extends Error {
  status: number;
  errorCode: string;
  details?: any;

  constructor(status: number, errorCode: string, message: string, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errorCode = errorCode;
    this.details = details;
  }
}

export interface RequestOptions extends RequestInit {
  userId?: number;
}

export async function apiRequest<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const baseUrl = getBaseUrl();
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${normalizedEndpoint}`;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  const method = (options.method || 'GET').toUpperCase();

  // Authenticated screens provide the session's user ID explicitly.
  if (options.userId !== undefined) {
    headers['X-User-Id'] = String(options.userId);
  }

  // Set Content-Type only if body is NOT FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      let errorEnvelope: (ApiErrorEnvelope & { detail?: string }) | null = null;
      try {
        errorEnvelope = await response.json();
      } catch {
        // Fallback for non-JSON error
      }

      if (errorEnvelope && errorEnvelope.status === 'error') {
        throw new ApiError(
          response.status,
          errorEnvelope.error_code || `HTTP_${response.status}`,
          errorEnvelope.message || `Request failed with status ${response.status}`,
          errorEnvelope.details
        );
      }

      if (errorEnvelope && typeof errorEnvelope.detail === 'string') {
        throw new ApiError(response.status, `HTTP_${response.status}`, errorEnvelope.detail);
      }

      throw new ApiError(
        response.status,
        `HTTP_${response.status}`,
        `Server returned error ${response.status}: ${response.statusText}`
      );
    }

    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(500, 'NETWORK_ERROR', err instanceof Error ? err.message : 'Network request failed');
  }
}
