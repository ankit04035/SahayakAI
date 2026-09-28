import { apiRequest, setCsrfToken } from './client';

export interface AuthUser {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

interface AuthResponse {
  user: AuthUser;
  csrf_token: string;
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  const user = await apiRequest<AuthUser>('/auth/me');
  if (!user) return null;
  const csrf = await apiRequest<{ csrf_token: string }>('/auth/csrf');
  setCsrfToken(csrf.csrf_token);
  return user;
}

export async function registerAccount(payload: { name: string; email: string; password: string }): Promise<AuthUser> {
  const response = await apiRequest<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  setCsrfToken(response.csrf_token);
  return response.user;
}

export async function loginAccount(payload: { email: string; password: string }): Promise<AuthUser> {
  const response = await apiRequest<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  setCsrfToken(response.csrf_token);
  return response.user;
}

export async function logoutAccount(): Promise<void> {
  try {
    await apiRequest<void>('/auth/logout', { method: 'POST' });
  } finally {
    setCsrfToken(null);
  }
}
