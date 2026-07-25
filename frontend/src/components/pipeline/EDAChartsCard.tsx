import { useAnalysisReport, useAnalysisStatus } from '@/hooks/useAnalysis';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart2, Loader2 } from 'lucide-react';
// Note: In a real project, we'd add 'react-markdown' to package.json. If it's missing, it will crash.
// For safety without npm install, we can just render text.

export function EDAChartsCard({ jobId }: { jobId: string }) {
  const { data: statusData } = useAnalysisStatus(jobId);
  const isComplete = statusData?.is_complete || false;
  
  const { data: reportData, isLoading } = useAnalysisReport(jobId, isComplete);

  if (!isComplete) return null;

  if (isLoading) {
    return (
      <Card className="border-neutral-800 bg-neutral-900/50 flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </Card>
    );
  }

  const markdown = reportData?.markdown_report || "No insights generated.";

  return (
    <Card className="border-neutral-800 bg-neutral-900/50 backdrop-blur-md shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-blue-500" />
          Data Insights & EDA
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* We use a prose class if tailwind typography was installed, otherwise manual styles */}
        <div className="prose prose-invert max-w-none prose-headings:text-neutral-100 prose-p:text-neutral-300">
          <pre className="whitespace-pre-wrap font-sans text-sm">{markdown}</pre>
        </div>
      </CardContent>
    </Card>
  );
}
