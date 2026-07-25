import { useAnalysisStatus } from '@/hooks/useAnalysis';
import { Card } from '@/components/ui/card';
import { 
  ResponsiveContainer, CartesianGrid, Tooltip, AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis
} from 'recharts';
import { DollarSign, Package, TrendingUp } from 'lucide-react';

const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#6366f1'];

export function BiDashboard({ jobId }: { jobId: string }) {
  const { data: analysisData } = useAnalysisStatus(jobId);

  if (!analysisData || !analysisData.is_complete) return null;

  const dynamic = analysisData.execution_results?.dynamic_charts;
  const widgets = dynamic?.widgets || [];
  
  if (widgets.length === 0) {
    return (
      <div className="p-6 text-center text-neutral-500 bg-white rounded-xl border border-neutral-200 shadow-sm">
        No dynamic widgets generated for this dataset.
      </div>
    );
  }

  // Separate KPIs and Charts
  const kpiWidgets = widgets.filter((w: any) => w.widget_type === 'kpi');
  const chartWidgets = widgets.filter((w: any) => w.widget_type === 'chart');

  // Find corresponding chart data
  const getChartData = (title: string) => {
    if (dynamic?.donut_chart?.title === title) return { type: 'donut', data: dynamic.donut_chart.data, title };
    if (dynamic?.bar_chart?.title === title) return { type: 'bar', data: dynamic.bar_chart.data, title };
    if (dynamic?.line_chart?.title === title) return { type: 'line', data: dynamic.line_chart.data, title };
    return null;
  };

  return (
    <Card className="border-neutral-800 bg-[#f8f9fa] text-neutral-900 p-6 shadow-xl space-y-6">
      {/* Top Header Row */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-neutral-200">
        <div>
          <h1 className="text-2xl font-bold text-neutral-800 tracking-tight">
            {analysisData.execution_results?.data_profile?.dataset_name || "Dataset"} Business Dashboard
          </h1>
          <p className="text-neutral-500 text-xs">PAGE 1</p>
        </div>
      </div>

      {/* Dynamic KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {kpiWidgets.map((widget: any, idx: number) => {
          const kpiVal = dynamic?.kpis?.find((k: any) => k.label === widget.data_binding_key);
          return (
            <div key={idx} className="bg-white p-6 rounded-xl border border-neutral-200 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400 block mb-1">{widget.data_binding_key}</span>
                <p className="text-3xl font-extrabold text-neutral-800">{kpiVal ? kpiVal.value : "N/A"}</p>
              </div>
              <div className="bg-blue-50 p-3 rounded-lg">
                {idx === 0 ? <DollarSign className="w-6 h-6 text-blue-600" /> : idx === 1 ? <TrendingUp className="w-6 h-6 text-emerald-600" /> : <Package className="w-6 h-6 text-indigo-600" />}
              </div>
            </div>
          );
        })}
      </div>

      {/* Dynamic Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {chartWidgets.map((widget: any, idx: number) => {
          const chartInfo = getChartData(widget.data_binding_key);
          if (!chartInfo) return null;

          return (
            <div key={idx} className={`bg-white p-4 rounded-xl border border-neutral-200 shadow-sm ${widget.size === 12 ? 'col-span-1 md:col-span-2' : ''}`}>
              <h3 className="text-xs font-bold text-neutral-500 uppercase tracking-wider mb-3">
                {chartInfo.title}
              </h3>
              <div className="h-56">
                {chartInfo.type === 'line' && (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartInfo.data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id={`color-${idx}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00c6ff" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#0072ff" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="#f1f1f1" strokeDasharray="3 3" />
                      <XAxis dataKey="name" stroke="#888" fontSize={8} />
                      <YAxis stroke="#888" fontSize={10} />
                      <Tooltip />
                      <Area type="monotone" dataKey="value" stroke="#0072ff" fillOpacity={1} fill={`url(#color-${idx})`} strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                )}

                {chartInfo.type === 'bar' && (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartInfo.data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid stroke="#f1f1f1" strokeDasharray="3 3" />
                      <XAxis dataKey="name" stroke="#888" fontSize={9} />
                      <YAxis stroke="#888" fontSize={10} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#0088FE" radius={[4, 4, 0, 0]} barSize={24} />
                    </BarChart>
                  </ResponsiveContainer>
                )}

                {chartInfo.type === 'donut' && (
                  <div className="flex flex-col md:flex-row items-center justify-between gap-4 h-full">
                    <div className="h-44 w-full md:w-1/2">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={chartInfo.data}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={65}
                            paddingAngle={3}
                            dataKey="value"
                          >
                            {chartInfo.data.map((_: any, index: number) => (
                              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value) => Number(value).toLocaleString()} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[10px] w-full md:w-1/2">
                      {chartInfo.data.map((entry: any, index: number) => (
                        <div key={index} className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: colors[index % colors.length] }}></span>
                          <span className="text-neutral-600 font-medium truncate">{entry.name}</span>
                          <span className="text-neutral-400 font-bold ml-auto">{entry.percentage || ''}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
