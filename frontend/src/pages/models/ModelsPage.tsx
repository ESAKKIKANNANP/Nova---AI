import { BrainCircuit, Rocket, Archive, BarChart3, Plus } from 'lucide-react'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { formatDate, formatPercent } from '@/utils/format'
import type { MLModel } from '@/types/dashboard'

const MOCK_MODELS: MLModel[] = [
  {
    id: 'm1',
    name: 'Churn Predictor',
    version: 'v3.1',
    algorithm: 'XGBoost',
    experimentId: 'e1',
    status: 'completed',
    metrics: { accuracy: 0.912, f1Score: 0.887, auc: 0.943 },
    artifactPath: 's3://models/churn-predictor-v3.1.pkl',
    deployedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    createdAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
    tags: ['production', 'churn', 'xgboost'],
  },
  {
    id: 'm2',
    name: 'Fraud Detector',
    version: 'v2.1',
    algorithm: 'Ensemble',
    experimentId: 'e2',
    status: 'running',
    metrics: { accuracy: 0.961, f1Score: 0.923 },
    artifactPath: 's3://models/fraud-detector-v2.1.pkl',
    deployedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    tags: ['production', 'fraud', 'ensemble'],
  },
  {
    id: 'm3',
    name: 'Sentiment Classifier',
    version: 'v1.0',
    algorithm: 'BERT',
    experimentId: 'e5',
    status: 'idle',
    metrics: { accuracy: 0.884, f1Score: 0.871 },
    artifactPath: 's3://models/sentiment-v1.0.pt',
    createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    tags: ['staging', 'nlp', 'transformers'],
  },
  {
    id: 'm4',
    name: 'Price Forecaster',
    version: 'v4.0',
    algorithm: 'Prophet + XGBoost',
    experimentId: 'e8',
    status: 'idle',
    metrics: { rmse: 0.042, mae: 0.031 },
    artifactPath: 's3://models/price-forecast-v4.0.pkl',
    createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    tags: ['staging', 'forecasting', 'time-series'],
  },
]

export default function ModelsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Models"
        description="Manage trained model artifacts and deployments"
      >
        <Button id="register-model-btn" variant="gradient">
          <Plus className="h-4 w-4" />
          Register Model
        </Button>
      </PageHeader>

      <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
        {MOCK_MODELS.map((model) => (
          <Card key={model.id} className="group">
            <CardContent className="p-5 space-y-4">
              {/* Header */}
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10">
                  <BrainCircuit className="h-5 w-5 text-emerald-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-semibold text-sm">{model.name}</p>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      {model.version}
                    </Badge>
                    <Badge
                      variant={model.status === 'running' ? 'running' : model.status === 'completed' ? 'success' : 'secondary'}
                    >
                      {model.deployedAt ? 'deployed' : 'staging'}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{model.algorithm}</p>
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-2">
                {model.metrics.accuracy !== undefined && (
                  <div className="rounded-lg bg-muted/50 p-2 text-center">
                    <p className="text-sm font-bold">{formatPercent(model.metrics.accuracy)}</p>
                    <p className="text-[10px] text-muted-foreground">Accuracy</p>
                  </div>
                )}
                {model.metrics.f1Score !== undefined && (
                  <div className="rounded-lg bg-muted/50 p-2 text-center">
                    <p className="text-sm font-bold">{formatPercent(model.metrics.f1Score)}</p>
                    <p className="text-[10px] text-muted-foreground">F1 Score</p>
                  </div>
                )}
                {model.metrics.auc !== undefined && (
                  <div className="rounded-lg bg-muted/50 p-2 text-center">
                    <p className="text-sm font-bold">{formatPercent(model.metrics.auc)}</p>
                    <p className="text-[10px] text-muted-foreground">AUC</p>
                  </div>
                )}
                {model.metrics.rmse !== undefined && (
                  <div className="rounded-lg bg-muted/50 p-2 text-center">
                    <p className="text-sm font-bold">{model.metrics.rmse?.toFixed(3)}</p>
                    <p className="text-[10px] text-muted-foreground">RMSE</p>
                  </div>
                )}
                {model.metrics.mae !== undefined && (
                  <div className="rounded-lg bg-muted/50 p-2 text-center">
                    <p className="text-sm font-bold">{model.metrics.mae?.toFixed(3)}</p>
                    <p className="text-[10px] text-muted-foreground">MAE</p>
                  </div>
                )}
              </div>

              {/* Artifact path */}
              <p className="text-[10px] font-mono text-muted-foreground/70 truncate bg-muted/30 rounded px-2 py-1">
                {model.artifactPath}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-1.5">
                {model.tags.map((t) => (
                  <span key={t} className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-secondary text-secondary-foreground">
                    {t}
                  </span>
                ))}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-border">
                <p className="text-xs text-muted-foreground">
                  Created {formatDate(model.createdAt)}
                </p>
                <div className="flex gap-1.5">
                  <Button id={`metrics-model-${model.id}`} variant="outline" size="sm">
                    <BarChart3 className="h-3.5 w-3.5" />
                    Metrics
                  </Button>
                  {model.deployedAt ? (
                    <Button id={`archive-model-${model.id}`} variant="ghost" size="icon-sm">
                      <Archive className="h-3.5 w-3.5" />
                    </Button>
                  ) : (
                    <Button id={`deploy-model-${model.id}`} variant="gradient" size="sm">
                      <Rocket className="h-3.5 w-3.5" />
                      Deploy
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
