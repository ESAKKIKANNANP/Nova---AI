import { useState } from 'react';
import { UploadDatasetCard } from '@/components/pipeline/UploadDatasetCard';
import { AnalysisProgressCard } from '@/components/pipeline/AnalysisProgressCard';
import { DatasetProfileCard } from '@/components/pipeline/DatasetProfileCard';
import { PipelineResultsCard } from '@/components/pipeline/PipelineResultsCard';
import { ModelComparisonDashboard } from '@/components/pipeline/ModelComparisonDashboard';
import { BiDashboard } from '@/components/pipeline/BiDashboard';
import { EDAChartsCard } from '@/components/pipeline/EDAChartsCard';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Activity, BarChart3, Brain } from 'lucide-react';

export default function DashboardPage() {
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Autonomous Data Scientist</h1>
          <p className="text-neutral-400 mt-1">Upload a dataset and let AI uncover the insights.</p>
        </div>
        {activeJobId && (
          <div className="flex items-center gap-2 text-sm font-medium px-3 py-1.5 bg-blue-950/30 text-blue-400 rounded-full border border-blue-900/50">
            <Activity className="w-4 h-4 animate-pulse" />
            Session Active
          </div>
        )}
      </div>

      {!activeJobId ? (
        <div className="pt-10">
          <UploadDatasetCard onJobStarted={setActiveJobId} />
        </div>
      ) : (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Progress Tracker */}
          <AnalysisProgressCard jobId={activeJobId} />
          
          <Tabs defaultValue="ml-pipeline" className="space-y-6">
            <div className="flex justify-between items-center border-b border-neutral-800 pb-2">
              <TabsList className="bg-neutral-900 border border-neutral-800">
                <TabsTrigger value="ml-pipeline" className="flex items-center gap-2 text-xs">
                  <Brain className="w-3.5 h-3.5" />
                  AI & ML Pipeline
                </TabsTrigger>
                <TabsTrigger value="bi-dashboard" className="flex items-center gap-2 text-xs">
                  <BarChart3 className="w-3.5 h-3.5" />
                  BI Analytics Dashboard
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="ml-pipeline" className="space-y-6 mt-0">
              {/* Results Area */}
              <DatasetProfileCard jobId={activeJobId} />
              <PipelineResultsCard jobId={activeJobId} />
              
              {/* Model Comparison Dashboard */}
              <ModelComparisonDashboard jobId={activeJobId} />
              
              <EDAChartsCard jobId={activeJobId} />
            </TabsContent>

            <TabsContent value="bi-dashboard" className="mt-0">
              {/* PowerBI Replica Dashboard */}
              <BiDashboard jobId={activeJobId} />
            </TabsContent>
          </Tabs>
          
          {/* Reset button for demo purposes */}
          <div className="text-center pt-8">
            <button 
              onClick={() => setActiveJobId(null)}
              className="text-sm text-neutral-500 hover:text-neutral-300 underline underline-offset-4"
            >
              Start New Analysis
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
