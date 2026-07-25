import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import type { AxiosError } from 'axios'
import { useAuthStore } from '@/store/authStore'
import { login as loginApi, logout as logoutApi, register as registerApi } from '@/api/auth'
import type { LoginCredentials, RegisterCredentials } from '@/types/auth'

type ApiErrorBody = {
  detail?: string
  message?: string
}

function getErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<ApiErrorBody>
  return axiosError.response?.data?.detail ?? axiosError.response?.data?.message ?? fallback
}

/**
 * Provides auth state and login/logout/register mutations
 * with automatic navigation and toast feedback.
 */
export function useAuth() {
  const navigate = useNavigate()
  const { user, isAuthenticated, setAuth, clearAuth } = useAuthStore()

  // ── Login ──
  const loginMutation = useMutation({
    mutationFn: (credentials: LoginCredentials) => loginApi(credentials),
    onSuccess: (data) => {
      setAuth(data.user, data.tokens.accessToken, data.tokens.refreshToken)
      toast.success(`Welcome back, ${data.user.name}!`)
      navigate('/', { replace: true })
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Invalid email or password.'))
    },
  })

  // ── Register ──
  const registerMutation = useMutation({
    mutationFn: (credentials: RegisterCredentials) => registerApi(credentials),
    onSuccess: (data) => {
      setAuth(data.user, data.tokens.accessToken, data.tokens.refreshToken)
      toast.success('Account created! Welcome aboard.')
      navigate('/', { replace: true })
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Registration failed. Please try again.'))
    },
  })

  // ── Logout ──
  const handleLogout = useCallback(async () => {
    try {
      await logoutApi()
    } catch {
      // Silently ignore — still clear local state
    } finally {
      clearAuth()
      navigate('/login', { replace: true })
      toast.success('You have been signed out.')
    }
  }, [clearAuth, navigate])

  return {
    user,
    isAuthenticated,
    login: loginMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    register: registerMutation.mutate,
    isRegistering: registerMutation.isPending,
    logout: handleLogout,
  }
}
