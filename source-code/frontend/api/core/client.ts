import { csrfToken } from './csrf';
import { ApiError, apiErrorMessage } from './errors';

const connectionMessage =
  'We could not reach AKURU. Check your connection and try again.';

let sessionGeneration = 0;

export type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
};

/** Shared JSON client for the authenticated, same-origin FastAPI boundary. */
export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const generation = sessionGeneration;
  const method = options.method ?? 'GET';
  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  const csrf = csrfToken();
  if (method !== 'GET' && csrf) headers['X-CSRF-Token'] = csrf;

  let response: Response;
  try {
    response = await fetch(`/api/v1/${path}`, {
      method,
      headers,
      cache: ['auth/me', 'state'].includes(path) ? 'no-store' : undefined,
      body:
        options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch (error) {
    if (error instanceof TypeError) throw new ApiError(connectionMessage, 0);
    throw error;
  }
  if (response.ok && ['auth/login', 'auth/logout'].includes(path))
    sessionGeneration++;
  // Handle expired sessions before reading the response body: a broken body
  // must not hide a confirmed 401 behind a network/parsing error.
  if (response.status === 401 && path !== 'auth/login') {
    // The state observer distinguishes an initial signed-out probe from an
    // authenticated refresh; invalid login credentials stay on the login form.
    if (
      path !== 'state' &&
      generation === sessionGeneration &&
      typeof window !== 'undefined'
    )
      window.dispatchEvent(new Event('akuru:unauthorized'));
    throw new ApiError('Please sign in again to continue.', 401);
  }
  let raw: string;
  try {
    raw = response.status === 204 ? '' : await response.text();
  } catch (error) {
    if (error instanceof TypeError) throw new ApiError(connectionMessage, 0);
    throw error;
  }
  let data: unknown = {};
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch {
      data = { detail: 'The server returned an unreadable response.' };
    }
  }
  if (!response.ok) {
    throw new ApiError(apiErrorMessage(data), response.status);
  }
  return data as T;
}

/** Compatibility helper for concise GET/POST calls; domain modules use request<T> directly. */
export function api<T = unknown>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: body === undefined ? 'GET' : 'POST',
    body,
  });
}
