import { useMutation, useQuery } from '@tanstack/react-query';
import { 
  uploadDataset, 
  triggerAnalysis, 
  getAnalysisStatus, 
  getAnalysisReport,
  predictLive
} from '@/api/analysisApi';

export function useUploadDataset() {
  return useMutation({
    mutationFn: ({ file, projectId }: { file: File; projectId: string }) => uploadDataset(file, projectId),
  });
}

export function useTriggerAnalysis() {
  return useMutation({
    mutationFn: ({ datasetId, projectId, goal }: { datasetId: string; projectId: string; goal: string }) =>
      triggerAnalysis(datasetId, projectId, goal),
  });
}

export function useAnalysisStatus(jobId: string | null) {
  return useQuery({
    queryKey: ['analysisStatus', jobId],
    queryFn: () => getAnalysisStatus(jobId!),
    enabled: !!jobId,
    // Poll every 2 seconds if not complete and no error
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.is_complete || data.error_message)) return false;
      return 2000;
    },
  });
}

export function useAnalysisReport(jobId: string | null, isComplete: boolean) {
  return useQuery({
    queryKey: ['analysisReport', jobId],
    queryFn: () => getAnalysisReport(jobId!),
    enabled: !!jobId && isComplete,
  });
}

export function usePredictLive() {
  return useMutation({
    mutationFn: ({ jobId, features }: { jobId: string; features: Record<string, number> }) =>
      predictLive(jobId, features),
  });
}
