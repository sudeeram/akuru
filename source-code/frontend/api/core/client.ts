import { csrfToken } from './csrf';
import { ApiError, apiErrorMessage } from './errors';

export type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
};

/** Shared JSON client for the authenticated, same-origin FastAPI boundary. */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? 'GET';
  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  const csrf = csrfToken();
  if (method !== 'GET' && csrf) headers['X-CSRF-Token'] = csrf;

  const response = await fetch(`/api/v1/${path}`, {
    method,
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const raw = response.status === 204 ? '' : await response.text();
  let data: unknown = {};
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch {
      data = { detail: 'The server returned an unreadable response.' };
    }
  }
  if (!response.ok) throw new ApiError(apiErrorMessage(data), response.status);
  return data as T;
}

/** Compatibility helper for concise GET/POST calls; domain modules use request<T> directly. */
export function api<T = unknown>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: body === undefined ? 'GET' : 'POST', body });
}
