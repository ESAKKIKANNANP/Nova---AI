import axios from 'axios';

const API_BASE_URL = '/api/v1';

export interface AnalysisStatus {
  job_id: string;
  current_node: string | null;
  is_complete: boolean;
  error_message: string | null;
  execution_results: Record<string, any>;
}

export interface AnalysisReport {
  job_id: string;
  markdown_report: string;
  artifacts: any[];
}

// ─── Datasets ─────────────────────────────────────────────────────────

export const uploadDataset = async (
  file: File,
  projectId: string
): Promise<{ dataset_id: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('project_id', projectId);

  const response = await axios.post(`${API_BASE_URL}/datasets/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return { dataset_id: response.data.id };
};

// ─── Analysis ─────────────────────────────────────────────────────────

export const triggerAnalysis = async (datasetId: string, projectId: string, userGoal: string) => {
  const response = await axios.post(`${API_BASE_URL}/analyze`, {
    dataset_id: datasetId,
    project_id: projectId,
    user_goal: userGoal,
  });
  return response.data;
};

export const getAnalysisStatus = async (jobId: string): Promise<AnalysisStatus> => {
  const response = await axios.get(`${API_BASE_URL}/analyze/${jobId}/status`);
  return response.data;
};

export const getAnalysisReport = async (jobId: string): Promise<AnalysisReport> => {
  const response = await axios.get(`${API_BASE_URL}/analyze/${jobId}/report`);
  return response.data;
};

export const predictLive = async (jobId: string, features: Record<string, number>): Promise<{ prediction: number }> => {
  const response = await axios.post(`${API_BASE_URL}/analyze/${jobId}/predict`, features);
  return response.data;
};
