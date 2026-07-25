import { useAnalysisStatus } from '@/hooks/useAnalysis';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, Circle, Loader2, AlertTriangle } from 'lucide-react';

const PIPELINE_NODES = [
  { id: 'planner_node', label: 'Planning Workflow' },
  { id: 'analyzer_node', label: 'Profiling Dataset' },
  { id: 'cleaning_node', label: 'Cleaning Data' },
  { id: 'eda_node', label: 'Exploratory Data Analysis & Visualization' },
  { id: 'problem_detection_node', label: 'Detecting ML Problem' },
  { id: 'feature_node', label: 'Feature Engineering & Preprocessing' },
  { id: 'model_select_node', label: 'Model Selection & ETL' },
  { id: 'train_node', label: 'Model Training & Evaluation' },
  { id: 'report_node', label: 'Generating Final Report' }
];

export function AnalysisProgressCard({ jobId }: { jobId: string }) {
  const { data, isLoading, isError } = useAnalysisStatus(jobId);

  if (isLoading) return <Card className="p-6 text-center animate-pulse bg-neutral-900 border-neutral-800"><p className="text-neutral-400">Connecting to orchestration engine...</p></Card>;
  if (isError) return <Card className="p-6 text-center bg-red-950/20 border-red-900"><p className="text-red-400">Failed to load status.</p></Card>;

  const currentNode = data?.current_node || 'planner_node';
  const isComplete = data?.is_complete;
  const errorMsg = data?.error_message;

  // Calculate progress
  const currentIndex = PIPELINE_NODES.findIndex(n => n.id === currentNode);
  const progressPct = isComplete ? 100 : Math.max(5, ((currentIndex + 1) / PIPELINE_NODES.length) * 100);

  return (
    <Card className="max-w-3xl mx-auto border-neutral-800 bg-neutral-900/50 backdrop-blur-md shadow-lg overflow-hidden">
      <CardHeader className="border-b border-neutral-800/50 bg-neutral-950/30">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg text-neutral-100 flex items-center gap-2">
              {isComplete ? <CheckCircle2 className="w-5 h-5 text-emerald-500" /> : <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
              {isComplete ? 'Analysis Complete' : 'AI Agents at Work'}
            </CardTitle>
            <CardDescription className="mt-1">Job ID: {jobId}</CardDescription>
          </div>
          <div className="text-right">
            <span className="text-2xl font-semibold text-neutral-200">{Math.round(progressPct)}%</span>
          </div>
        </div>
        <Progress value={progressPct} className="h-2 mt-4 bg-neutral-800" indicatorClassName={isComplete ? "bg-emerald-500" : errorMsg ? "bg-red-500" : "bg-blue-500"} />
      </CardHeader>
      
      <CardContent className="p-6">
        {errorMsg ? (
          <div className="bg-red-950/30 border border-red-900/50 rounded-lg p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium text-red-400">Execution Failed</h4>
              <p className="text-xs text-red-300/80 mt-1">{errorMsg}</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {PIPELINE_NODES.map((node, idx) => {
              const isPast = isComplete || idx < currentIndex;
              const isCurrent = !isComplete && idx === currentIndex;
              
              return (
                <div key={node.id} className={`flex items-center gap-3 ${isPast ? 'opacity-50' : ''}`}>
                  {isPast ? (
                    <CheckCircle2 className="w-4 h-4 text-neutral-500" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                  ) : (
                    <Circle className="w-4 h-4 text-neutral-700" />
                  )}
                  <span className={`text-sm font-medium ${isCurrent ? 'text-blue-400' : 'text-neutral-400'}`}>
                    {node.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
