import { Database, Upload, Eye, Trash2, FileText } from 'lucide-react'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { formatBytes, formatDate, formatNumber } from '@/utils/format'
import type { Dataset } from '@/types/dashboard'

const MOCK_DATASETS: Dataset[] = [
  {
    id: '1',
    name: 'Customer Churn Q3 2025',
    description: 'Historical customer behavior data for churn prediction.',
    sizeBytes: 84 * 1024 * 1024,
    rowCount: 84_000,
    columnCount: 32,
    format: 'parquet',
    status: 'completed',
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    tags: ['churn', 'classification', 'production'],
  },
  {
    id: '2',
    name: 'Transaction Fraud Dataset',
    description: 'Labelled financial transactions for fraud detection models.',
    sizeBytes: 220 * 1024 * 1024,
    rowCount: 520_000,
    columnCount: 48,
    format: 'csv',
    status: 'completed',
    createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    tags: ['fraud', 'anomaly-detection', 'finance'],
  },
  {
    id: '3',
    name: 'Product Recommendation Logs',
    description: 'Clickstream and purchase history for collaborative filtering.',
    sizeBytes: 1.4 * 1024 * 1024 * 1024,
    rowCount: 4_200_000,
    columnCount: 18,
    format: 'parquet',
    status: 'running',
    createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date().toISOString(),
    tags: ['recommender', 'nlp', 'e-commerce'],
  },
  {
    id: '4',
    name: 'Sensor IoT Time Series',
    description: 'Multi-variate sensor readings for predictive maintenance.',
    sizeBytes: 540 * 1024 * 1024,
    rowCount: 12_000_000,
    columnCount: 64,
    format: 'hdf5',
    status: 'pending',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    tags: ['iot', 'time-series', 'anomaly'],
  },
]

const FORMAT_COLORS: Record<string, string> = {
  csv: 'text-emerald-400',
  parquet: 'text-blue-400',
  json: 'text-amber-400',
  hdf5: 'text-violet-400',
  avro: 'text-pink-400',
}

export default function DatasetsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Datasets"
        description="Manage your training data and ingestion pipelines"
      >
        <Button id="upload-dataset-btn" variant="gradient">
          <Upload className="h-4 w-4" />
          Upload Dataset
        </Button>
      </PageHeader>

      {/* Summary strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total Datasets', value: MOCK_DATASETS.length.toString() },
          { label: 'Total Storage', value: formatBytes(MOCK_DATASETS.reduce((a, d) => a + d.sizeBytes, 0)) },
          { label: 'Total Rows', value: formatNumber(MOCK_DATASETS.reduce((a, d) => a + d.rowCount, 0)) },
          { label: 'Formats', value: new Set(MOCK_DATASETS.map(d => d.format)).size.toString() },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-lg border border-border bg-card p-4 text-center">
            <p className="text-2xl font-bold text-foreground">{value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Dataset grid */}
      <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
        {MOCK_DATASETS.map((dataset) => (
          <Card key={dataset.id} className="group">
            <CardContent className="p-5">
              <div className="flex items-start gap-3 mb-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-500/10">
                  <Database className="h-5 w-5 text-violet-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-sm truncate">{dataset.name}</p>
                    <Badge
                      variant={
                        dataset.status === 'completed' ? 'success' :
                        dataset.status === 'running' ? 'running' :
                        dataset.status === 'failed' ? 'destructive' : 'warning'
                      }
                    >
                      {dataset.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{dataset.description}</p>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2 py-3 border-y border-border text-center">
                <div>
                  <p className="text-sm font-semibold">{formatNumber(dataset.rowCount)}</p>
                  <p className="text-xs text-muted-foreground">rows</p>
                </div>
                <div>
                  <p className="text-sm font-semibold">{dataset.columnCount}</p>
                  <p className="text-xs text-muted-foreground">columns</p>
                </div>
                <div>
                  <p className={`text-sm font-semibold uppercase ${FORMAT_COLORS[dataset.format] ?? 'text-foreground'}`}>
                    {dataset.format}
                  </p>
                  <p className="text-xs text-muted-foreground">{formatBytes(dataset.sizeBytes)}</p>
                </div>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1.5 mt-3">
                {dataset.tags.map((tag) => (
                  <span key={tag} className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-secondary text-secondary-foreground">
                    {tag}
                  </span>
                ))}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
                <p className="text-xs text-muted-foreground">Created {formatDate(dataset.createdAt)}</p>
                <div className="flex gap-1">
                  <Button id={`view-dataset-${dataset.id}`} variant="ghost" size="icon-sm">
                    <Eye className="h-3.5 w-3.5" />
                  </Button>
                  <Button id={`schema-dataset-${dataset.id}`} variant="ghost" size="icon-sm">
                    <FileText className="h-3.5 w-3.5" />
                  </Button>
                  <Button id={`delete-dataset-${dataset.id}`} variant="ghost" size="icon-sm" className="text-destructive hover:text-destructive">
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
