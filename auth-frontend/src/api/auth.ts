const API_BASE = process.env.REACT_APP_API_URL ?? 'http://localhost:8000';

export interface UserDto {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirm_password: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };

  const accessToken = localStorage.getItem('access_token');
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers,
  });

  if (!response.ok) {
    let errorBody: ApiError;
    try {
      errorBody = await response.json();
    } catch {
      errorBody = {
        error: {
          code: 'UNKNOWN_ERROR',
          message: 'An unexpected error occurred.',
        },
      };
    }
    throw errorBody;
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export async function login(data: LoginRequest): Promise<AuthTokens> {
  const tokens = await request<AuthTokens>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  localStorage.setItem('access_token', tokens.access_token);
  return tokens;
}

export async function register(data: RegisterRequest): Promise<AuthTokens> {
  const tokens = await request<AuthTokens>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  localStorage.setItem('access_token', tokens.access_token);
  return tokens;
}

export async function forgotPassword(
  data: ForgotPasswordRequest,
): Promise<void> {
  await request<void>('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function resetPassword(
  data: ResetPasswordRequest,
): Promise<void> {
  await request<void>('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function me(): Promise<UserDto> {
  return request<UserDto>('/auth/me', {
    method: 'GET',
  });
}

export async function logout(): Promise<void> {
  try {
    await request<void>('/auth/logout', {
      method: 'POST',
    });
  } finally {
    localStorage.removeItem('access_token');
  }
}

export async function refresh(): Promise<AuthTokens> {
  const tokens = await request<AuthTokens>('/auth/refresh', {
    method: 'POST',
  });
  localStorage.setItem('access_token', tokens.access_token);
  return tokens;
}
