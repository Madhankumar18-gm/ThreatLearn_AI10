import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  Sliders, Database, CheckCircle, AlertTriangle, RefreshCw, 
  BarChart2, FileCheck, Layers, ArrowDownRight, ExternalLink
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, Legend, LineChart, Line 
} from 'recharts';

export default function AblationStudio() {
  const [activeTab, setActiveTab] = useState('ablation'); // 'ablation' | 'dataset'
  const [ablationData, setAblationData] = useState(null);
  const [datasetReport, setDatasetReport] = useState(null);
  const [provenance, setProvenance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAblationSuite();
    loadDatasetProvenance();
  }, []);

  const loadAblationSuite = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getAblationAnalysis();
      setAblationData(res);
    } catch (err) {
      setError(err.message || 'Failed to load ablation analysis');
    } finally {
      setLoading(false);
    }
  };

  const loadDatasetProvenance = async () => {
    try {
      const prov = await api.getDatasetProvenance();
      setProvenance(prov);
    } catch {
      // ignore
    }
  };

  const runDatasetDemo = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getDatasetDemo();
      setDatasetReport(res);
    } catch (err) {
      setError(err.message || 'Failed to run public dataset demo');
    } finally {
      setLoading(false);
    }
  };

  const chartData = React.useMemo(() => {
    if (!ablationData) return [];
    return ablationData.experiments.map(e => ({
      name: e.configuration_name.replace('Without ', '-'),
      precision: Math.round(e.precision * 100),
      recall: Math.round(e.recall * 100),
      accuracy: Math.round(e.classification_accuracy * 100),
      false_links: Math.round(e.false_link_rate * 100)
    }));
  }, [ablationData]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-white border border-[#DCE5EF] rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-50 text-cyan-700 border border-cyan-200">
                Features F18, F47
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                Scientific Verification
              </span>
            </div>
            <h1 className="text-2xl font-bold text-[#172033]">
              Ablation Analysis & Public Dataset Studio
            </h1>
            <p className="text-sm text-[#64748B] mt-1 max-w-3xl">
              Empirically quantify the contribution of each analysis component and validate schema mapping 
              against documented public automotive battery datasets.
            </p>
          </div>

          {/* Tab Switcher */}
          <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200 self-start md:self-auto">
            <button
              onClick={() => setActiveTab('ablation')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-xs font-bold transition-all ${
                activeTab === 'ablation'
                  ? 'bg-white text-cyan-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sliders className="w-4 h-4" />
              Pipeline Ablation (F47)
            </button>
            <button
              onClick={() => setActiveTab('dataset')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-xs font-bold transition-all ${
                activeTab === 'dataset'
                  ? 'bg-white text-cyan-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Database className="w-4 h-4" />
              Public Dataset (F18)
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* TAB 1: PIPELINE ABLATION (F47) */}
      {activeTab === 'ablation' && (
        <div className="space-y-6">
          {/* Summary Insight Box */}
          {ablationData && (
            <div className="bg-cyan-50/60 border border-cyan-200 rounded-xl p-5 shadow-xs flex items-start gap-3">
              <BarChart2 className="w-5 h-5 text-cyan-700 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-bold text-cyan-950">Empirical Component Contribution</h3>
                <p className="text-xs text-cyan-900 mt-1 leading-relaxed">
                  {ablationData.summary_insight}
                </p>
              </div>
            </div>
          )}

          {/* Ablation Chart */}
          {chartData.length > 0 && (
            <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
              <h3 className="text-sm font-bold text-[#172033] mb-1">
                Precision & Accuracy Degradation Under Component Removal
              </h3>
              <p className="text-xs text-[#64748B] mb-4">
                Comparison of Link Precision, Classification Accuracy, and False-Link Rate across the 6 pipeline variants.
              </p>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                    <XAxis dataKey="name" stroke="#94A3B8" fontSize={10} interval={0} angle={-15} textAnchor="end" />
                    <YAxis unit="%" domain={[0, 100]} stroke="#94A3B8" fontSize={11} />
                    <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: '8px', fontSize: '12px' }} />
                    <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px' }} />
                    <Bar dataKey="precision" fill="#0891B2" name="Link Precision (%)" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="accuracy" fill="#2563EB" name="Classification Accuracy (%)" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="false_links" fill="#DC2626" name="False-Link Rate (%)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Ablation Matrix Table */}
          {ablationData && (
            <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold text-[#172033]">
                  Ablation Performance Matrix ({ablationData.experiments.length} Configurations Tested)
                </h3>
                <button
                  onClick={loadAblationSuite}
                  disabled={loading}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-md flex items-center gap-1.5 transition-colors"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                  Re-evaluate Matrix
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[#DCE5EF] text-[#64748B] font-bold uppercase tracking-wider">
                      <th className="pb-3">Configuration</th>
                      <th className="pb-3">Disabled Component</th>
                      <th className="pb-3">Precision</th>
                      <th className="pb-3">Recall</th>
                      <th className="pb-3">F1-Score</th>
                      <th className="pb-3">False-Link Rate</th>
                      <th className="pb-3">Accuracy</th>
                      <th className="pb-3">Latency (ms)</th>
                      <th className="pb-3">CF Agreement</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#DCE5EF]">
                    {ablationData.experiments.map((e) => {
                      const isBaseline = e.disabled_component.includes('Baseline');
                      return (
                        <tr key={e.experiment_id} className={`hover:bg-slate-50/50 ${isBaseline ? 'bg-cyan-50/20 font-medium' : ''}`}>
                          <td className="py-3 font-semibold text-[#172033]">
                            {e.configuration_name}
                            {isBaseline && <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-cyan-100 text-cyan-800">Standard</span>}
                          </td>
                          <td className="py-3 text-slate-600">{e.disabled_component}</td>
                          <td className="py-3 font-mono font-bold text-slate-800">
                            {(e.precision * 100).toFixed(1)}%
                          </td>
                          <td className="py-3 font-mono text-slate-700">
                            {(e.recall * 100).toFixed(1)}%
                          </td>
                          <td className="py-3 font-mono text-slate-700">
                            {e.f1_score.toFixed(3)}
                          </td>
                          <td className="py-3 font-mono">
                            <span className={e.false_link_rate > 0.20 ? 'text-rose-600 font-bold' : 'text-slate-700'}>
                              {(e.false_link_rate * 100).toFixed(1)}%
                            </span>
                          </td>
                          <td className="py-3 font-mono text-slate-800">
                            {(e.classification_accuracy * 100).toFixed(1)}%
                          </td>
                          <td className="py-3 font-mono text-slate-600">
                            {e.average_latency_ms.toFixed(1)} ms
                          </td>
                          <td className="py-3 font-mono text-slate-700">
                            {(e.counterfactual_agreement * 100).toFixed(0)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: PUBLIC DATASET ADAPTER (F18) */}
      {activeTab === 'dataset' && (
        <div className="space-y-6">
          {/* Provenance Card */}
          {provenance && (
            <div className="bg-white border border-[#DCE5EF] rounded-xl p-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 border-b border-[#DCE5EF] pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-cyan-600">
                    Dataset Provenance & Legal Licensing
                  </span>
                  <h2 className="text-lg font-bold text-[#172033] mt-0.5">
                    {provenance.dataset_name}
                  </h2>
                </div>
                <span className="px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-full self-start">
                  {provenance.verification_status}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-3 bg-[#F8FAFC] border border-[#DCE5EF] rounded-lg space-y-1">
                  <span className="text-[#64748B] font-semibold block">Source Organization:</span>
                  <span className="text-[#172033] font-medium">{provenance.source_organization} ({provenance.release_year})</span>
                </div>
                <div className="p-3 bg-[#F8FAFC] border border-[#DCE5EF] rounded-lg space-y-1">
                  <span className="text-[#64748B] font-semibold block">License:</span>
                  <span className="text-[#172033] font-medium">{provenance.license_type}</span>
                </div>
                <div className="p-3 bg-[#F8FAFC] border border-[#DCE5EF] rounded-lg space-y-1 md:col-span-2">
                  <span className="text-[#64748B] font-semibold block">Relevance to ThreatLens:</span>
                  <span className="text-slate-700">{provenance.relevance_to_threatlens}</span>
                </div>
                <div className="p-3 bg-amber-50/50 border border-amber-200 rounded-lg space-y-1 md:col-span-2">
                  <span className="text-amber-900 font-semibold block">Known Limitations & Boundaries:</span>
                  <span className="text-amber-800">{provenance.known_limitations}</span>
                </div>
              </div>

              <div className="mt-5 flex justify-end">
                <button
                  onClick={runDatasetDemo}
                  disabled={loading}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[#0891B2] hover:bg-[#0e7490] text-white rounded-lg font-medium text-xs transition-colors shadow-sm disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                  {loading ? 'Processing Dataset...' : 'Run Synthetic Dataset Ingestion Demo'}
                </button>
              </div>
            </div>
          )}

          {/* Dataset Adapter Report */}
          {datasetReport && (
            <div className="space-y-6">
              <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <FileCheck className="w-5 h-5 text-emerald-600" />
                  <h3 className="text-base font-bold text-[#172033]">
                    Adapter Ingestion Report ({datasetReport.report.total_records} Records Processed)
                  </h3>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-4">
                  <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                    <span className="text-[#64748B] block">Valid Slices</span>
                    <span className="text-base font-bold text-emerald-600 block mt-0.5">
                      {datasetReport.report.time_slices_generated}
                    </span>
                  </div>
                  <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                    <span className="text-[#64748B] block">Timestamp Span</span>
                    <span className="text-base font-bold text-slate-800 block mt-0.5">
                      {datasetReport.report.valid_timestamp_range_seconds} s
                    </span>
                  </div>
                  <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                    <span className="text-[#64748B] block">Mapped Aliases</span>
                    <span className="text-base font-bold text-cyan-600 block mt-0.5">
                      {Object.keys(datasetReport.report.mapped_columns).length} Columns
                    </span>
                  </div>
                  <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                    <span className="text-[#64748B] block">Missing Fields</span>
                    <span className="text-base font-bold text-slate-700 block mt-0.5">
                      {datasetReport.report.missing_required_fields.length === 0 ? 'None (Clean)' : datasetReport.report.missing_required_fields.join(', ')}
                    </span>
                  </div>
                </div>

                {/* Column Mapping Table */}
                <h4 className="text-xs font-bold text-[#172033] mb-2 uppercase tracking-wider">
                  Canonical Column Aliases Resolved
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                  {Object.entries(datasetReport.report.mapped_columns).map(([canon, orig]) => (
                    <div key={canon} className="p-2 bg-slate-50 border border-slate-200 rounded flex items-center justify-between">
                      <span className="text-[#64748B]">{canon}:</span>
                      <span className="font-mono font-bold text-cyan-700">{orig}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Imported Time-Series Chart */}
              {datasetReport.time_slices.length > 0 && (
                <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
                  <h3 className="text-sm font-bold text-[#172033] mb-3">
                    Imported Empirical Telemetry Trajectory (Current vs Temperature)
                  </h3>
                  <div className="h-60 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={datasetReport.time_slices}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                        <XAxis dataKey="timestamp" unit="s" stroke="#94A3B8" fontSize={11} />
                        <YAxis yAxisId="curr" unit="A" stroke="#0891B2" fontSize={11} />
                        <YAxis yAxisId="temp" orientation="right" unit="°C" stroke="#2563EB" fontSize={11} />
                        <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: '8px', fontSize: '12px' }} />
                        <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px' }} />
                        <Line yAxisId="curr" type="monotone" dataKey="charging_current" stroke="#0891B2" strokeWidth={2} dot={false} name="DC Charging Current (A)" />
                        <Line yAxisId="temp" type="monotone" dataKey="battery_temperature" stroke="#2563EB" strokeWidth={2} dot={false} name="Battery Temperature (°C)" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
