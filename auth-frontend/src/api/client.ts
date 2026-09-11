import { ApiError } from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

let isRefreshing = false;
let refreshQueue: Array<(token: string | null) => void> = [];

function drainQueue(token: string | null): void {
  refreshQueue.forEach((resolve) => resolve(token));
  refreshQueue = [];
}

async function attemptSilentRefresh(): Promise<string | null> {
  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      return null;
    }
    const data = await response.json();
    const token: string | null = data?.access_token ?? null;
    return token;
  } catch {
    return null;
  }
}

function getAccessToken(): string | null {
  return sessionStorage.getItem('access_token');
}

export function setAccessToken(token: string | null): void {
  if (token === null) {
    sessionStorage.removeItem('access_token');
  } else {
    sessionStorage.setItem('access_token', token);
  }
}

type FetchOptions = RequestInit & {
  skipAuth?: boolean;
};

export async function apiFetch<T = unknown>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const { skipAuth = false, ...init } = options;

  const headers = new Headers(init.headers);

  if (!headers.has('Content-Type') && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (!skipAuth) {
    const token = getAccessToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  const url = `${BASE_URL}${path}`;

  let response = await fetch(url, {
    ...init,
    credentials: 'include',
    headers,
  });

  if (response.status === 401 && !skipAuth) {
    if (isRefreshing) {
      const newToken = await new Promise<string | null>((resolve) => {
        refreshQueue.push(resolve);
      });
      if (newToken) {
        headers.set('Authorization', `Bearer ${newToken}`);
        response = await fetch(url, {
          ...init,
          credentials: 'include',
          headers,
        });
      } else {
        const errorPayload = await safeJson(response);
        throw normaliseError(response.status, errorPayload);
      }
    } else {
      isRefreshing = true;
      const newToken = await attemptSilentRefresh();
      isRefreshing = false;
      setAccessToken(newToken);
      drainQueue(newToken);

      if (newToken) {
        headers.set('Authorization', `Bearer ${newToken}`);
        response = await fetch(url, {
          ...init,
          credentials: 'include',
          headers,
        });
      } else {
        const errorPayload = await safeJson(response);
        throw normaliseError(response.status, errorPayload);
      }
    }
  }

  if (!response.ok) {
    const errorPayload = await safeJson(response);
    throw normaliseError(response.status, errorPayload);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function normaliseError(status: number, payload: unknown): ApiError {
  const p = payload as Record<string, unknown> | null;
  const errorBlock = p?.error as Record<string, unknown> | undefined;

  const code =
    typeof errorBlock?.code === 'string'
      ? errorBlock.code
      : String(status);

  const message =
    typeof errorBlock?.message === 'string'
      ? errorBlock.message
      : 'An unexpected error occurred.';

  const details =
    errorBlock?.details !== undefined ? errorBlock.details : undefined;

  const err = new ApiError(message, code, status, details);
  return err;
}
