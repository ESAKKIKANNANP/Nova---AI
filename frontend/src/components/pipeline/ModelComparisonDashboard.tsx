import { useState, useEffect } from 'react';
import { useAnalysisStatus, usePredictLive } from '@/hooks/useAnalysis';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Trophy, ShieldCheck, PlayCircle, Sliders, Cpu } from 'lucide-react';

const colors = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#6366f1'];

export function ModelComparisonDashboard({ jobId }: { jobId: string }) {
  const { data } = useAnalysisStatus(jobId);
  const comparison = data?.execution_results?.model_comparison;
  const features = comparison?.features || [];
  
  const [inputs, setInputs] = useState<Record<string, number>>({});
  const [prediction, setPrediction] = useState<number | null>(null);
  const predictMutation = usePredictLive();

  useEffect(() => {
    if (features.length > 0) {
      const initialInputs: Record<string, number> = {};
      features.forEach((feat: string) => {
        initialInputs[feat] = 0.5;
      });
      setInputs(initialInputs);
    }
  }, [features]);

  useEffect(() => {
    if (Object.keys(inputs).length > 0) {
      const delayDebounce = setTimeout(() => {
        predictMutation.mutate({ jobId, features: inputs }, {
          onSuccess: (res) => {
            setPrediction(res.prediction);
          }
        });
      }, 300);
      return () => clearTimeout(delayDebounce);
    }
  }, [inputs]);

  if (!data || !data.is_complete) return null;
  if (!comparison || !comparison.models || comparison.models.length === 0) return null;

  const models = comparison.models;
  // Extract dynamic metric keys
  const firstModelKeys = Object.keys(models[0]);
  const metricKeys = firstModelKeys.filter(
    (key) => !['rank', 'name', 'latency_ms'].includes(key)
  );

  const displayMetricName = (key: string) => {
    if (key.toLowerCase() === 'r2') return 'R²';
    if (key.toLowerCase() === 'f1_score') return 'F1 Score';
    return key.charAt(0).toUpperCase() + key.slice(1);
  };

  const chartData = models.map((model: any) => {
    const entry: any = { name: model.name.split(' ')[0] };
    metricKeys.forEach((key) => {
      entry[displayMetricName(key)] = model[key];
    });
    return entry;
  });

  const displayMetricKeys = metricKeys.map(displayMetricName);
  const recommendation = comparison.recommendation;

  return (
    <div className="space-y-6">
      {/* Title block */}
      <div className="flex items-center gap-2 pb-2 border-b border-neutral-800">
        <Trophy className="w-6 h-6 text-yellow-500" />
        <h2 className="text-xl font-bold text-neutral-100">Model Leaderboard & Recommendation</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Model Chart & Table - Left 2 Columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* Comparison Chart */}
          <Card className="border-neutral-800 bg-neutral-900/50 backdrop-blur-md shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-md font-semibold text-neutral-100">Performance Comparison</CardTitle>
              <CardDescription>Visual comparison of metrics across top model candidates.</CardDescription>
            </CardHeader>
            <CardContent className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                  <XAxis dataKey="name" stroke="#737373" fontSize={11} />
                  <YAxis domain={[0, 1.0]} stroke="#737373" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#262626', borderRadius: '6px' }}
                    labelStyle={{ color: '#e5e5e5', fontWeight: 'bold' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  {displayMetricKeys.map((key, idx) => (
                    <Bar key={key} dataKey={key} fill={colors[idx % colors.length]} radius={[4, 4, 0, 0]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Leaderboard Table */}
          <Card className="border-neutral-800 bg-neutral-900/50 backdrop-blur-md shadow-sm overflow-hidden">
            <CardHeader className="pb-2">
              <CardTitle className="text-md font-semibold text-neutral-100 font-sans">Top Candidates</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="bg-neutral-950/50 border-y border-neutral-800 text-neutral-400 font-medium">
                      <th className="p-3 pl-4">Rank</th>
                      <th className="p-3">Model Name</th>
                      {displayMetricKeys.map((key) => (
                        <th key={key} className="p-3 text-center">{key}</th>
                      ))}
                      <th className="p-3 text-center">Inference Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-800">
                    {models.map((model: any) => (
                      <tr key={model.rank} className="hover:bg-neutral-950/30 transition-colors">
                        <td className="p-3 pl-4 font-bold text-neutral-300">
                          {model.rank === 1 ? (
                            <span className="flex items-center gap-1.5 text-yellow-500">
                              🥇 #1
                            </span>
                          ) : (
                            `#${model.rank}`
                          )}
                        </td>
                        <td className="p-3 font-medium text-neutral-200">{model.name}</td>
                        {metricKeys.map((key) => {
                          const val = model[key];
                          return (
                            <td key={key} className="p-3 text-center text-emerald-400 font-semibold">
                              {typeof val === 'number' ? (val <= 1.0 ? `${(val * 100).toFixed(1)}%` : val.toFixed(2)) : val}
                            </td>
                          );
                        })}
                        <td className="p-3 text-center text-neutral-400">{model.latency_ms} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* AI Suggestion Card - Right Column */}
        <div className="space-y-6">
          <Card className="border-neutral-800 bg-neutral-900/50 backdrop-blur-md shadow-sm h-full flex flex-col justify-between">
            <CardHeader className="pb-3 bg-neutral-950/30 border-b border-neutral-800/50">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Best Model Suggestion</span>
              </div>
              <CardTitle className="text-lg font-bold text-neutral-100 mt-2">{recommendation.model}</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 flex-grow space-y-4">
              <div>
                <span className="text-xs text-neutral-500 font-semibold uppercase block mb-1">Reasoning</span>
                <p className="text-xs text-neutral-300 leading-relaxed font-sans">{recommendation.reasoning}</p>
              </div>

              {recommendation.pros && (
                <div className="space-y-3">
                  <div>
                    <span className="text-xs text-emerald-500 font-semibold uppercase block mb-1">Pros</span>
                    <ul className="list-disc list-inside text-[11px] text-neutral-300 space-y-1">
                      {recommendation.pros.map((pro: string, idx: number) => (
                        <li key={idx}>{pro}</li>
                      ))}
                    </ul>
                  </div>
                  {recommendation.cons && (
                    <div>
                      <span className="text-xs text-red-400 font-semibold uppercase block mb-1">Cons</span>
                      <ul className="list-disc list-inside text-[11px] text-neutral-300 space-y-1">
                        {recommendation.cons.map((con: string, idx: number) => (
                          <li key={idx}>{con}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
            
            <div className="p-4 border-t border-neutral-800 bg-neutral-950/30">
              <button className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium py-2 px-4 rounded-lg text-sm transition-all shadow-md active:scale-95">
                <PlayCircle className="w-4 h-4" />
                Deploy Model to Production
              </button>
            </div>
          </Card>
        </div>
      </div>

      {/* Dynamic Model Playground */}
      {features.length > 0 && (
        <Card className="border-neutral-800 bg-neutral-900/40 backdrop-blur-md shadow-sm border-t border-t-blue-500/50">
          <CardHeader className="pb-3 border-b border-neutral-800/60">
            <div className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-blue-500" />
              <CardTitle className="text-md font-semibold text-neutral-100">Live Model Prediction Playground</CardTitle>
            </div>
            <CardDescription className="text-xs text-neutral-400">
              Drag the sliders or modify input values to see the model's prediction adjust in real-time.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Left/Middle Column: Sliders */}
            <div className="md:col-span-2 space-y-4 max-h-[300px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-neutral-800">
              {features.map((feat: string) => (
                <div key={feat} className="space-y-1 bg-neutral-950/20 p-2.5 rounded-lg border border-neutral-800/40">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-neutral-300 font-mono text-[11px] truncate max-w-[70%]">{feat}</span>
                    <span className="text-blue-400 font-mono">{inputs[feat]?.toFixed(3) || '0.000'}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={inputs[feat] ?? 0.5}
                      onChange={(e) => {
                        setInputs(prev => ({
                          ...prev,
                          [feat]: parseFloat(e.target.value)
                        }));
                      }}
                      className="flex-grow h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                    />
                    <input
                      type="number"
                      step="0.1"
                      value={inputs[feat] ?? 0.5}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value);
                        setInputs(prev => ({
                          ...prev,
                          [feat]: isNaN(val) ? 0.0 : val
                        }));
                      }}
                      className="w-16 bg-neutral-900 border border-neutral-800 rounded px-1.5 py-0.5 text-center text-xs font-mono text-neutral-200"
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Right Column: Prediction Gauge */}
            <div className="bg-neutral-950/50 rounded-xl border border-neutral-800/50 p-6 flex flex-col items-center justify-center text-center space-y-4">
              <div className="p-3 bg-blue-500/10 rounded-full border border-blue-500/20">
                <Cpu className="w-8 h-8 text-blue-400" />
              </div>
              <div>
                <span className="text-xs text-neutral-400 font-semibold uppercase block tracking-wider">Estimated Prediction</span>
                <div className="mt-2 text-3xl font-extrabold text-white font-mono tracking-tight transition-all duration-300">
                  {prediction !== null ? (
                    prediction % 1 === 0 ? prediction : prediction.toFixed(4)
                  ) : (
                    <span className="text-neutral-600">--</span>
                  )}
                </div>
              </div>
              {prediction !== null && (
                <div className="text-[11px] text-neutral-400 max-w-[80%]">
                  Predicted class or target output based on model inference.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
