import type { ResourceStatus } from './api'

// ─── Dashboard KPI Stats ─────────────────────────────────────────

export interface DashboardStats {
  activeAgents: number
  totalDatasets: number
  experimentsRun: number
  modelsDeployed: number
  activeAgentsDelta: number
  datasetsDelta: number
  experimentsDelta: number
  modelsDelta: number
}

// ─── Chart Data ──────────────────────────────────────────────────

export interface TimeSeriesPoint {
  date: string
  value: number
  secondaryValue?: number
}

export interface ChartData {
  accuracyOverTime: TimeSeriesPoint[]
  experimentsPerDay: TimeSeriesPoint[]
}

// ─── Agents ──────────────────────────────────────────────────────

export interface Agent {
  id: string
  name: string
  type: AgentType
  status: ResourceStatus
  tasksCompleted: number
  lastActive: string
  description: string
  model: string
}

export type AgentType =
  | 'data_ingestion'
  | 'feature_engineering'
  | 'model_training'
  | 'evaluation'
  | 'deployment'
  | 'monitoring'
  | 'orchestrator'

// ─── Datasets ────────────────────────────────────────────────────

export interface Dataset {
  id: string
  name: string
  description: string
  sizeBytes: number
  rowCount: number
  columnCount: number
  format: DatasetFormat
  status: ResourceStatus
  createdAt: string
  updatedAt: string
  tags: string[]
}

export type DatasetFormat = 'csv' | 'parquet' | 'json' | 'avro' | 'hdf5'

// ─── Experiments ─────────────────────────────────────────────────

export interface Experiment {
  id: string
  name: string
  description: string
  status: ResourceStatus
  algorithm: string
  datasetId: string
  datasetName: string
  metrics: ExperimentMetrics
  hyperparameters: Record<string, string | number | boolean>
  startedAt: string
  completedAt?: string
  duration?: number
  tags: string[]
}

export interface ExperimentMetrics {
  accuracy?: number
  f1Score?: number
  precision?: number
  recall?: number
  rmse?: number
  mae?: number
  auc?: number
  loss?: number
}

// ─── Models ──────────────────────────────────────────────────────

export interface MLModel {
  id: string
  name: string
  version: string
  algorithm: string
  experimentId: string
  status: ResourceStatus
  metrics: ExperimentMetrics
  artifactPath: string
  deployedAt?: string
  createdAt: string
  tags: string[]
}

// ─── Activity Feed ───────────────────────────────────────────────

export interface ActivityEvent {
  id: string
  type: ActivityEventType
  title: string
  description: string
  timestamp: string
  resourceId?: string
  resourceType?: string
  userId: string
  userName: string
}

export type ActivityEventType =
  | 'agent_started'
  | 'agent_completed'
  | 'agent_failed'
  | 'dataset_uploaded'
  | 'experiment_started'
  | 'experiment_completed'
  | 'model_deployed'
  | 'model_retrained'
