import React, { useState } from 'react';
import { UploadCloud, Loader2 } from 'lucide-react';
import { useUploadDataset, useTriggerAnalysis } from '@/hooks/useAnalysis';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export function UploadDatasetCard({ onJobStarted }: { onJobStarted: (jobId: string) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [goal, setGoal] = useState('Analyze this dataset and give me insights');
  
  const uploadMutation = useUploadDataset();
  const triggerMutation = useTriggerAnalysis();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleStart = async () => {
    if (!file) {
      toast.error('Please select a file first.');
      return;
    }

    try {
      const projectId = crypto.randomUUID();
      // 1. Upload
      const uploadRes = await uploadMutation.mutateAsync({ file, projectId });
      const datasetId = uploadRes.dataset_id;
      
      // 2. Trigger Analysis
      const analysisRes = await triggerMutation.mutateAsync({ datasetId, projectId, goal });
      
      toast.success('Analysis started in the background!');
      onJobStarted(analysisRes.job_id || projectId);

    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || 'Failed to start analysis');
    }
  };

  const isPending = uploadMutation.isPending || triggerMutation.isPending;

  return (
    <Card className="max-w-2xl mx-auto shadow-sm border-neutral-800 bg-neutral-900/50 backdrop-blur-md">
      <CardHeader>
        <CardTitle className="text-xl">Start New Analysis</CardTitle>
        <CardDescription>Upload a CSV, Excel, or Parquet file to let the AI analyze it automatically.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        
        <div className="border-2 border-dashed border-neutral-700 rounded-xl p-10 flex flex-col items-center justify-center text-center transition-colors hover:border-blue-500/50 hover:bg-neutral-800/50 cursor-pointer relative">
          <input 
            type="file" 
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
            onChange={handleFileChange}
            disabled={isPending}
            accept=".csv,.xlsx,.parquet"
          />
          <UploadCloud className="w-12 h-12 text-neutral-400 mb-4" />
          {file ? (
            <p className="text-sm font-medium text-blue-400">{file.name}</p>
          ) : (
            <>
              <p className="text-sm font-medium text-neutral-200">Click or drag file to this area to upload</p>
              <p className="text-xs text-neutral-500 mt-2">Supports CSV, Excel, and Parquet</p>
            </>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-300">Analysis Goal</label>
          <input 
            type="text" 
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            disabled={isPending}
            className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 transition-shadow"
            placeholder="e.g. Predict customer churn..."
          />
        </div>

        <Button 
          onClick={handleStart} 
          disabled={!file || isPending}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white"
        >
          {isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            'Analyze Dataset'
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
