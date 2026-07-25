import { Bot, Play, Square, RefreshCw, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import type { Agent } from '@/types/dashboard'

const MOCK_AGENTS: Agent[] = [
  {
    id: '1',
    name: 'Feature Engineering Alpha',
    type: 'feature_engineering',
    status: 'running',
    tasksCompleted: 128,
    lastActive: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    description: 'Automated feature selection, encoding, and scaling for tabular datasets.',
    model: 'gemini-1.5-pro',
  },
  {
    id: '2',
    name: 'Data Ingestion Bot',
    type: 'data_ingestion',
    status: 'running',
    tasksCompleted: 64,
    lastActive: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    description: 'Handles multi-source data ingestion from S3, GCS, and REST APIs.',
    model: 'gemini-1.5-flash',
  },
  {
    id: '3',
    name: 'Model Training Orchestrator',
    type: 'model_training',
    status: 'completed',
    tasksCompleted: 340,
    lastActive: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    description: 'Runs hyperparameter search and trains ensemble models in parallel.',
    model: 'gemini-1.5-pro',
  },
  {
    id: '4',
    name: 'Evaluation Agent',
    type: 'evaluation',
    status: 'idle',
    tasksCompleted: 210,
    lastActive: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    description: 'Computes metrics, generates reports, and flags model drift.',
    model: 'gemini-1.5-flash',
  },
  {
    id: '5',
    name: 'Deployment Pipeline',
    type: 'deployment',
    status: 'pending',
    tasksCompleted: 18,
    lastActive: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    description: 'Packages and prepares models for local or external serving endpoints.',
    model: 'gemini-1.5-pro',
  },
  {
    id: '6',
    name: 'Monitoring Agent',
    type: 'monitoring',
    status: 'failed',
    tasksCompleted: 99,
    lastActive: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    description: 'Monitors live model performance and triggers retraining alerts.',
    model: 'gemini-1.5-flash',
  },
]

function statusVariant(status: Agent['status']) {
  switch (status) {
    case 'running': return 'running'
    case 'completed': return 'success'
    case 'failed': return 'destructive'
    case 'pending': return 'warning'
    default: return 'secondary'
  }
}

export default function AgentsPage() {
  const [agents, setAgents] = useState(MOCK_AGENTS)

  const counts = useMemo(
    () => [
      { label: 'Running', count: agents.filter(a => a.status === 'running').length, color: 'text-blue-400' },
      { label: 'Completed', count: agents.filter(a => a.status === 'completed').length, color: 'text-emerald-400' },
      { label: 'Pending', count: agents.filter(a => a.status === 'pending').length, color: 'text-amber-400' },
      { label: 'Failed', count: agents.filter(a => a.status === 'failed').length, color: 'text-red-400' },
    ],
    [agents]
  )

  const updateAgentStatus = (id: string, status: Agent['status']) => {
    setAgents((current) =>
      current.map((agent) =>
        agent.id === id
          ? { ...agent, status, lastActive: new Date().toISOString() }
          : agent
      )
    )
  }

  const handleStart = (agent: Agent) => {
    updateAgentStatus(agent.id, 'running')
    toast.success(`${agent.name} started in local mode.`)
  }

  const handleStop = (agent: Agent) => {
    updateAgentStatus(agent.id, 'idle')
    toast.success(`${agent.name} stopped.`)
  }

  const handleRestart = (agent: Agent) => {
    updateAgentStatus(agent.id, 'running')
    toast.success(`${agent.name} restarted.`)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Agents"
        description="Manage and monitor your autonomous AI agents"
      >
        <Button id="new-agent-btn" variant="gradient">
          <Plus className="h-4 w-4" />
          New Agent
        </Button>
      </PageHeader>

      {/* Summary strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {counts.map(({ label, count, color }) => (
          <div key={label} className="rounded-lg border border-border bg-card p-4 text-center">
            <p className={`text-2xl font-bold ${color}`}>{count}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Agent Cards */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
        {agents.map((agent) => (
          <Card key={agent.id} className="flex flex-col">
            <CardContent className="p-5 flex flex-col gap-4 flex-1">
              {/* Header */}
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-500/10">
                  <Bot className="h-5 w-5 text-blue-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-sm truncate">{agent.name}</p>
                    <Badge variant={statusVariant(agent.status)} className="shrink-0 capitalize">
                      {agent.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground capitalize mt-0.5">
                    {agent.type.replace(/_/g, ' ')}
                  </p>
                </div>
              </div>

              {/* Description */}
              <p className="text-xs text-muted-foreground leading-relaxed flex-1">
                {agent.description}
              </p>

              {/* Progress (only for running) */}
              {agent.status === 'running' && (
                <div>
                  <div className="flex justify-between text-xs text-muted-foreground mb-1.5">
                    <span>In progress</span>
                    <span>64%</span>
                  </div>
                  <Progress value={64} className="h-1.5" />
                </div>
              )}

              {/* Meta */}
              <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border">
                <span>{agent.tasksCompleted} tasks completed</span>
                <span className="text-primary/70 font-medium">{agent.model}</span>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                {agent.status === 'running' ? (
                  <Button
                    id={`stop-agent-${agent.id}`}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleStop(agent)}
                  >
                    <Square className="h-3.5 w-3.5" />
                    Stop
                  </Button>
                ) : (
                  <Button
                    id={`start-agent-${agent.id}`}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleStart(agent)}
                  >
                    <Play className="h-3.5 w-3.5" />
                    Start
                  </Button>
                )}
                <Button
                  id={`restart-agent-${agent.id}`}
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => handleRestart(agent)}
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
