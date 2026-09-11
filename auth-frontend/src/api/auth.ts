const API_BASE_URL = process.env.REACT_APP_API_BASE_URL ?? 'http://localhost:8000';

export interface RegisterRequest {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface RegisterResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  user: {
    id: string;
    fullName: string;
    email: string;
    isActive: boolean;
    createdAt: string;
  };
}

export interface MeResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface RefreshResponse {
  accessToken: string;
  tokenType: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  accessToken?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    try {
      const errorData: ApiError = await response.json();
      if (errorData.error?.message) {
        errorMessage = errorData.error.message;
      }
    } catch {
      // ignore parse errors; use the default message
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  return request<RegisterResponse>('POST', '/auth/register', {
    full_name: data.fullName,
    email: data.email,
    password: data.password,
    confirm_password: data.confirmPassword,
  });
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  return request<LoginResponse>('POST', '/auth/login', {
    email: data.email,
    password: data.password,
    remember_me: data.rememberMe ?? false,
  });
}

export async function me(accessToken: string): Promise<MeResponse> {
  return request<MeResponse>('GET', '/auth/me', undefined, accessToken);
}

export async function logout(accessToken: string): Promise<void> {
  return request<void>('POST', '/auth/logout', undefined, accessToken);
}

export async function refresh(): Promise<RefreshResponse> {
  return request<RefreshResponse>('POST', '/auth/refresh');
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<void> {
  return request<void>('POST', '/auth/forgot-password', {
    email: data.email,
  });
}

export async function resetPassword(data: ResetPasswordRequest): Promise<void> {
  return request<void>('POST', '/auth/reset-password', {
    token: data.token,
    password: data.password,
    confirm_password: data.confirmPassword,
  });
}
