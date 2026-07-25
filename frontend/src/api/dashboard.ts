import apiClient from './client'
import type {
  DashboardStats,
  ChartData,
  Agent,
  Dataset,
  Experiment,
  MLModel,
  ActivityEvent,
} from '@/types/dashboard'
import type { ApiResponse, PaginatedResponse, QueryParams } from '@/types/api'

// ─── Dashboard API ───────────────────────────────────────────────

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<ApiResponse<DashboardStats>>('/dashboard/stats')
  return data.data
}

export async function getChartData(): Promise<ChartData> {
  const { data } = await apiClient.get<ApiResponse<ChartData>>('/dashboard/charts')
  return data.data
}

export async function getRecentActivity(limit = 10): Promise<ActivityEvent[]> {
  const { data } = await apiClient.get<ApiResponse<ActivityEvent[]>>('/dashboard/activity', {
    params: { limit },
  })
  return data.data
}

// ─── Agents API ──────────────────────────────────────────────────

export async function getAgents(params?: QueryParams): Promise<PaginatedResponse<Agent>> {
  const { data } = await apiClient.get<ApiResponse<PaginatedResponse<Agent>>>('/agents', { params })
  return data.data
}

export async function getAgent(id: string): Promise<Agent> {
  const { data } = await apiClient.get<ApiResponse<Agent>>(`/agents/${id}`)
  return data.data
}

// ─── Datasets API ────────────────────────────────────────────────

export async function getDatasets(params?: QueryParams): Promise<PaginatedResponse<Dataset>> {
  const { data } = await apiClient.get<ApiResponse<PaginatedResponse<Dataset>>>('/datasets', {
    params,
  })
  return data.data
}

// ─── Experiments API ─────────────────────────────────────────────

export async function getExperiments(params?: QueryParams): Promise<PaginatedResponse<Experiment>> {
  const { data } = await apiClient.get<ApiResponse<PaginatedResponse<Experiment>>>(
    '/experiments',
    { params }
  )
  return data.data
}

// ─── Models API ──────────────────────────────────────────────────

export async function getModels(params?: QueryParams): Promise<PaginatedResponse<MLModel>> {
  const { data } = await apiClient.get<ApiResponse<PaginatedResponse<MLModel>>>('/models', {
    params,
  })
  return data.data
}
