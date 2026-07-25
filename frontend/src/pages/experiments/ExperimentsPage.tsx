import { FlaskConical, Plus, TrendingUp, Clock } from 'lucide-react'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { formatDate, formatPercent } from '@/utils/format'
import type { Experiment } from '@/types/dashboard'

const MOCK_EXPERIMENTS: Experiment[] = [
  {
    id: '1',
    name: 'XGBoost Churn Prediction v3',
    description: 'Grid search over learning rate and max depth with early stopping.',
    status: 'completed',
    algorithm: 'XGBoost',
    datasetId: 'd1',
    datasetName: 'Customer Churn Q3 2025',
    metrics: { accuracy: 0.912, f1Score: 0.887, precision: 0.901, recall: 0.874, auc: 0.943 },
    hyperparameters: { learning_rate: 0.05, max_depth: 6, n_estimators: 500, subsample: 0.8 },
    startedAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    completedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    duration: 7200,
    tags: ['xgboost', 'classification', 'grid-search'],
  },
  {
    id: '2',
    name: 'Fraud Detection Ensemble',
    description: 'Stacked ensemble of Random Forest, LightGBM, and logistic regression.',
    status: 'running',
    algorithm: 'Ensemble',
    datasetId: 'd2',
    datasetName: 'Transaction Fraud Dataset',
    metrics: { accuracy: 0.961, f1Score: 0.923 },
    hyperparameters: { n_estimators: 300, stack_method: 'predict_proba' },
    startedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    tags: ['ensemble', 'fraud', 'lightgbm'],
  },
  {
    id: '3',
    name: 'Neural Net Recommender',
    description: 'Two-tower embedding model with negative sampling.',
    status: 'failed',
    algorithm: 'Neural Network',
    datasetId: 'd3',
    datasetName: 'Product Recommendation Logs',
    metrics: {},
    hyperparameters: { epochs: 50, embedding_dim: 128, batch_size: 2048 },
    startedAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    completedAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    tags: ['neural-net', 'recommender', 'cuda-oom'],
  },
  {
    id: '4',
    name: 'LSTM Predictive Maintenance',
    description: 'Sequence model on IoT sensor windows for anomaly detection.',
    status: 'pending',
    algorithm: 'LSTM',
    datasetId: 'd4',
    datasetName: 'Sensor IoT Time Series',
    metrics: {},
    hyperparameters: { sequence_length: 128, hidden_size: 256, num_layers: 3 },
    startedAt: new Date().toISOString(),
    tags: ['lstm', 'time-series', 'iot'],
  },
]

function MetricPill({ label, value }: { label: string; value?: number }) {
  if (value === undefined) return null
  return (
    <div className="flex flex-col items-center rounded-lg bg-muted/50 px-3 py-2">
      <p className="text-xs font-bold text-foreground">{formatPercent(value)}</p>
      <p className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</p>
    </div>
  )
}

export default function ExperimentsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Experiments"
        description="Track and compare model training runs"
      >
        <Button id="new-experiment-btn" variant="gradient">
          <Plus className="h-4 w-4" />
          New Experiment
        </Button>
      </PageHeader>

      <div className="space-y-4">
        {MOCK_EXPERIMENTS.map((exp) => (
          <Card key={exp.id}>
            <CardContent className="p-5">
              <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                {/* Icon */}
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/10">
                  <FlaskConical className="h-5 w-5 text-amber-400" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 space-y-3">
                  {/* Title row */}
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-sm">{exp.name}</h3>
                    <Badge
                      variant={
                        exp.status === 'completed' ? 'success' :
                        exp.status === 'running' ? 'running' :
                        exp.status === 'failed' ? 'destructive' : 'warning'
                      }
                    >
                      {exp.status}
                    </Badge>
                    <Badge variant="secondary">{exp.algorithm}</Badge>
                  </div>

                  <p className="text-xs text-muted-foreground">{exp.description}</p>

                  {/* Running progress */}
                  {exp.status === 'running' && (
                    <div>
                      <div className="flex justify-between text-xs text-muted-foreground mb-1.5">
                        <span>Training in progress…</span>
                        <span>47%</span>
                      </div>
                      <Progress value={47} className="h-1.5" indicatorClassName="bg-blue-500" />
                    </div>
                  )}

                  {/* Metrics */}
                  {Object.keys(exp.metrics).length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      <MetricPill label="Accuracy" value={exp.metrics.accuracy} />
                      <MetricPill label="F1" value={exp.metrics.f1Score} />
                      <MetricPill label="Precision" value={exp.metrics.precision} />
                      <MetricPill label="Recall" value={exp.metrics.recall} />
                      <MetricPill label="AUC" value={exp.metrics.auc} />
                    </div>
                  )}

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1.5">
                    {exp.tags.map((t) => (
                      <span key={t} className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-secondary text-secondary-foreground">
                        {t}
                      </span>
                    ))}
                  </div>

                  {/* Footer meta */}
                  <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-border text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      Started {formatDate(exp.startedAt)}
                    </span>
                    <span className="flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" />
                      Dataset: {exp.datasetName}
                    </span>
                    {exp.duration && (
                      <span>Duration: {Math.round(exp.duration / 60)}m</span>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
