import { useAnalysisStatus } from '@/hooks/useAnalysis';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Sparkles, CheckCircle2, ChevronRight } from 'lucide-react';

export function PipelineResultsCard({ jobId }: { jobId: string }) {
  const { data } = useAnalysisStatus(jobId);
  
  if (!data || !data.is_complete) return null;
  
  const cleaning = data.execution_results?.cleaning;
  const feature_eng = data.execution_results?.feature_engineering;
  const training = data.execution_results?.model_training;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Cleaning Results */}
      <Card className="border-neutral-800 bg-neutral-900/50 backdrop-blur-md shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-md font-semibold text-neutral-100 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            Data Cleaning
          </CardTitle>
          <CardDescription>Actions taken by Data Cleaning Agent</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {cleaning?.steps?.map((step: string, idx: number) => (
            <div key={idx} className="flex items-start gap-2 text-sm text-neutral-300">
              <ChevronRight className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
              <span>{step}</span>
            </div>
          ))}
          {!cleaning && <p className="text-neutral-500 text-sm">No cleaning steps documented.</p>}
        </CardContent>
      </Card>

      {/* Preprocessing & Feature Engineering */}
      <Card className="border-neutral-800 bg-neutral-900/50 backdrop-blur-md shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-md font-semibold text-neutral-100 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-500" />
            Preprocessing & ETL
          </CardTitle>
          <CardDescription>Feature transformations applied</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {feature_eng?.transformations?.map((trans: any, idx: number) => (
            <div key={idx} className="border-b border-neutral-800 pb-3 last:border-0 last:pb-0">
              <div className="flex justify-between items-center text-sm font-medium text-indigo-400">
                <span>{trans.transformation}</span>
                <span className="text-xs text-neutral-500 bg-neutral-950 px-2 py-0.5 rounded border border-neutral-800">
                  {trans.column}
                </span>
              </div>
              <p className="text-xs text-neutral-400 mt-1">{trans.reasoning}</p>
            </div>
          ))}
          {!feature_eng && <p className="text-neutral-500 text-sm">No preprocessing steps documented.</p>}
        </CardContent>
      </Card>

      {/* Model Training & Evaluation */}
      <Card className="border-neutral-800 bg-neutral-900/50 backdrop-blur-md shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-md font-semibold text-neutral-100 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-blue-500" />
            Model Selection & Training
          </CardTitle>
          <CardDescription>Best performing model evaluation</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {training ? (
            <>
              <div>
                <span className="text-xs text-neutral-500 uppercase tracking-wider block mb-1">Winning Model</span>
                <p className="text-sm font-semibold text-blue-400">{training.model}</p>
              </div>
              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-neutral-800">
                <div className="bg-neutral-950 p-2 rounded border border-neutral-800 text-center">
                  <span className="text-[10px] text-neutral-500 block uppercase">Accuracy</span>
                  <span className="text-sm font-bold text-emerald-400">{(training.accuracy * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-neutral-950 p-2 rounded border border-neutral-800 text-center">
                  <span className="text-[10px] text-neutral-500 block uppercase">F1-Score</span>
                  <span className="text-sm font-bold text-emerald-400">{(training.f1_score * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-neutral-950 p-2 rounded border border-neutral-800 text-center">
                  <span className="text-[10px] text-neutral-500 block uppercase">ROC AUC</span>
                  <span className="text-sm font-bold text-emerald-400">{(training.roc_auc * 100).toFixed(1)}%</span>
                </div>
              </div>
            </>
          ) : (
            <p className="text-neutral-500 text-sm">No training metrics documented.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
