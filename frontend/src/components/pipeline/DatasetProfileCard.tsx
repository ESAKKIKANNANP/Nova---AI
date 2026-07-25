import { useAnalysisStatus } from '@/hooks/useAnalysis';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Database, Hash, TableProperties, AlertCircle } from 'lucide-react';

export function DatasetProfileCard({ jobId }: { jobId: string }) {
  const { data } = useAnalysisStatus(jobId);
  const profile = data?.execution_results?.data_profile;

  if (!profile) return null;

  return (
    <Card className="border-neutral-800 bg-neutral-900/50 backdrop-blur-md shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Database className="w-5 h-5 text-purple-500" />
          Dataset Profile
        </CardTitle>
        <CardDescription>Extracted statistics and metadata.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-neutral-400 mb-2">
              <Hash className="w-4 h-4" />
              <span className="text-xs font-medium uppercase tracking-wider">Rows</span>
            </div>
            <p className="text-2xl font-bold text-neutral-100">{profile.row_count?.toLocaleString() || '-'}</p>
          </div>

          <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-neutral-400 mb-2">
              <TableProperties className="w-4 h-4" />
              <span className="text-xs font-medium uppercase tracking-wider">Columns</span>
            </div>
            <p className="text-2xl font-bold text-neutral-100">{profile.columns?.length || '-'}</p>
          </div>

          <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-neutral-400 mb-2">
              <AlertCircle className="w-4 h-4" />
              <span className="text-xs font-medium uppercase tracking-wider">ML Task</span>
            </div>
            <p className="text-xl font-bold text-emerald-400 capitalize">{profile.problem_type || 'Unknown'}</p>
          </div>
          
          <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4 overflow-hidden">
            <div className="flex items-center gap-2 text-neutral-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Target Column</span>
            </div>
            <p className="text-lg font-semibold text-blue-400 truncate" title={profile.target_column || 'None Detected'}>
              {profile.target_column || 'None Detected'}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
