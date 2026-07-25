import apiClient from './client'
import type { LoginCredentials, RegisterCredentials, AuthResponse } from '@/types/auth'
import type { ApiResponse } from '@/types/api'

// ─── Auth API Functions ───────────────────────────────────────────

/**
 * Authenticate with email and password. Returns tokens + user profile.
 */
export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const { data } = await apiClient.post<ApiResponse<AuthResponse>>('/auth/login', credentials)
  return data.data
}

/**
 * Create a new user account.
 */
export async function register(credentials: RegisterCredentials): Promise<AuthResponse> {
  const { data } = await apiClient.post<ApiResponse<AuthResponse>>('/auth/register', credentials)
  return data.data
}

/**
 * Invalidate the current session server-side.
 */
export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}

/**
 * Exchange a refresh token for a new access token.
 */
export async function refreshToken(refreshToken: string): Promise<{ accessToken: string }> {
  const { data } = await apiClient.post<ApiResponse<{ accessToken: string }>>('/auth/refresh', {
    refreshToken,
  })
  return data.data
}

/**
 * Fetch the currently authenticated user's profile.
 */
export async function getMe() {
  const { data } = await apiClient.get<ApiResponse<AuthResponse['user']>>('/auth/me')
  return data.data
}
