import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  GitCompare, ArrowRight, ShieldCheck, AlertTriangle, 
  CheckCircle, RefreshCw, BarChart2, ShieldAlert, Cpu
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  Legend, CartesianGrid 
} from 'recharts';

export default function IncidentComparison() {
  const [runs, setRuns] = useState([]);
  const [runIdA, setRunIdA] = useState('');
  const [runIdB, setRunIdB] = useState('');
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [runAData, setRunAData] = useState(null);
  const [runBData, setRunBData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadRuns();
  }, []);

  const loadRuns = async () => {
    try {
      setLoading(true);
      const fetchedRuns = await api.getRuns(30);
      setRuns(fetchedRuns);
      if (fetchedRuns.length >= 2) {
        setRunIdA(fetchedRuns[0].run_id);
        setRunIdB(fetchedRuns[1].run_id);
      }
    } catch (err) {
      setError(err.message || 'Failed to load stored incident runs');
    } finally {
      setLoading(false);
    }
  };

  const executeComparison = async () => {
    if (!runIdA || !runIdB) return;
    try {
      setComparing(true);
      setError(null);
      const [compRes, detailedA, detailedB] = await Promise.all([
        api.compareRuns(runIdA, runIdB),
        api.getRun(runIdA),
        api.getRun(runIdB)
      ]);
      setComparisonResult(compRes);
      setRunAData(detailedA);
      setRunBData(detailedB);
    } catch (err) {
      setError(err.message || 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  // Combine telemetry for aligned charts
  const combinedChartData = React.useMemo(() => {
    if (!runAData || !runBData) return [];
    const telemA = runAData.telemetry || [];
    const telemB = runBData.telemetry || [];
    const maxLen = Math.max(telemA.length, telemB.length);

    const merged = [];
    for (let i = 0; i < maxLen; i++) {
      const sliceA = telemA[i];
      const sliceB = telemB[i];
      const t = sliceA ? sliceA.timestamp : (sliceB ? sliceB.timestamp : i);
      merged.push({
        timestamp: t,
        temp_a: sliceA?.battery_temperature,
        temp_b: sliceB?.battery_temperature,
        current_a: sliceA?.charging_current,
        current_b: sliceB?.charging_current,
      });
    }
    return merged;
  }, [runAData, runBData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-cyan-600 font-medium">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Loading Incident Runs...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-[#DCE5EF] rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-50 text-cyan-700 border border-cyan-200">
            Feature F38
          </span>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            Side-by-Side Run Comparator
          </span>
        </div>
        <h1 className="text-2xl font-bold text-[#172033]">
          Incident Comparison & Differential Analysis
        </h1>
        <p className="text-sm text-[#64748B] mt-1 max-w-3xl">
          Select any two saved incidents or simulation runs to compare physical trajectories, 
          causal attribution, peak thermal margins, and mitigation efficacy side by side.
        </p>

        {/* Run Selectors */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 mt-6 items-end">
          <div className="md:col-span-5">
            <label className="text-xs font-bold uppercase tracking-wider text-[#64748B] mb-1.5 block">
              Reference Incident (Run A)
            </label>
            <select
              value={runIdA}
              onChange={(e) => setRunIdA(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-[#DCE5EF] rounded-lg text-sm text-[#172033] font-medium focus:outline-hidden focus:ring-2 focus:ring-[#0891B2]"
            >
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} &middot; {r.scenario_name} (Peak: {r.peak_temperature}°C)
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-2 flex items-center justify-center pb-2">
            <span className="p-2 rounded-full bg-slate-100 text-slate-500">
              <GitCompare className="w-5 h-5" />
            </span>
          </div>

          <div className="md:col-span-5">
            <label className="text-xs font-bold uppercase tracking-wider text-[#64748B] mb-1.5 block">
              Comparative Incident (Run B)
            </label>
            <select
              value={runIdB}
              onChange={(e) => setRunIdB(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-[#DCE5EF] rounded-lg text-sm text-[#172033] font-medium focus:outline-hidden focus:ring-2 focus:ring-[#0891B2]"
            >
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} &middot; {r.scenario_name} (Peak: {r.peak_temperature}°C)
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={executeComparison}
            disabled={comparing || !runIdA || !runIdB || runIdA === runIdB}
            className="flex items-center gap-2 px-6 py-2.5 bg-[#0891B2] hover:bg-[#0e7490] text-white rounded-lg font-medium text-sm transition-colors shadow-sm disabled:opacity-50"
          >
            <GitCompare className={`w-4 h-4 ${comparing ? 'animate-spin' : ''}`} />
            {comparing ? 'Comparing Runs...' : 'Compare Selected Runs'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Comparison Results */}
      {comparisonResult && (
        <>
          {/* Compatibility Banner */}
          <div className={`p-4 rounded-xl border flex items-start gap-3 ${
            comparisonResult.is_compatible 
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900' 
              : 'bg-amber-50 border-amber-200 text-amber-900'
          }`}>
            {comparisonResult.is_compatible ? (
              <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <span className="font-bold text-sm block">
                {comparisonResult.is_compatible ? 'Compatible Incident Comparison' : 'Comparison Configuration Warning'}
              </span>
              <p className="text-xs mt-0.5 opacity-90">
                {comparisonResult.summary_verdict}
              </p>
              {comparisonResult.compatibility_warnings.length > 0 && (
                <ul className="mt-2 space-y-1 text-xs list-disc list-inside">
                  {comparisonResult.compatibility_warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Side-by-Side Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Run A Card */}
            <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3 border-b border-[#DCE5EF] pb-3">
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-600">
                    Incident Run A
                  </span>
                  <h3 className="text-lg font-bold text-[#172033]">
                    {comparisonResult.run_a_id}
                  </h3>
                </div>
                <span className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs font-semibold rounded-md">
                  {comparisonResult.scenario_a_id}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                  <span className="text-[#64748B] block">Peak Temperature</span>
                  <span className="text-base font-bold text-[#172033] block mt-0.5">
                    {comparisonResult.run_a_summary.peak_temperature} °C
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                  <span className="text-[#64748B] block">Peak Current</span>
                  <span className="text-base font-bold text-[#172033] block mt-0.5">
                    {comparisonResult.run_a_summary.peak_current} A
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                  <span className="text-[#64748B] block">Classification</span>
                  <span className="text-base font-bold text-[#172033] block mt-0.5">
                    {comparisonResult.run_a_summary.classification}
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                  <span className="text-[#64748B] block">Hardware Contactor</span>
                  <span className={`text-base font-bold block mt-0.5 ${
                    comparisonResult.run_a_summary.tripped ? 'text-rose-600' : 'text-emerald-600'
                  }`}>
                    {comparisonResult.run_a_summary.tripped ? 'TRIPPED (FAULT)' : 'CLOSED (HEALTHY)'}
                  </span>
                </div>
              </div>
            </div>

            {/* Run B Card */}
            <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3 border-b border-[#DCE5EF] pb-3">
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-blue-600">
                    Incident Run B
                  </span>
                  <h3 className="text-lg font-bold text-[#172033]">
                    {comparisonResult.run_b_id}
                  </h3>
                </div>
                <span className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs font-semibold rounded-md">
                  {comparisonResult.scenario_b_id}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                  <span className="text-[#64748B] block">Peak Temperature</span>
                  <span className="text-base font-bold text-[#172033] block mt-0.5">
                    {comparisonResult.run_b_summary.peak_temperature} °C
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                  <span className="text-[#64748B] block">Peak Current</span>
                  <span className="text-base font-bold text-[#172033] block mt-0.5">
                    {comparisonResult.run_b_summary.peak_current} A
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                  <span className="text-[#64748B] block">Classification</span>
                  <span className="text-base font-bold text-[#172033] block mt-0.5">
                    {comparisonResult.run_b_summary.classification}
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAFC] rounded-lg">
                  <span className="text-[#64748B] block">Hardware Contactor</span>
                  <span className={`text-base font-bold block mt-0.5 ${
                    comparisonResult.run_b_summary.tripped ? 'text-rose-600' : 'text-emerald-600'
                  }`}>
                    {comparisonResult.run_b_summary.tripped ? 'TRIPPED (FAULT)' : 'CLOSED (HEALTHY)'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Differential Metrics Table */}
          <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
            <h3 className="text-base font-bold text-[#172033] mb-4">
              Physical & Safety Metric Differentials (&Delta; Run B - Run A)
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#DCE5EF] text-[#64748B] font-bold uppercase tracking-wider">
                    <th className="pb-3">Metric Parameter</th>
                    <th className="pb-3">Run A</th>
                    <th className="pb-3">Run B</th>
                    <th className="pb-3">&Delta; Absolute Difference</th>
                    <th className="pb-3">% Delta</th>
                    <th className="pb-3">Better Safety Margin</th>
                    <th className="pb-3">Analytical Interpretation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DCE5EF]">
                  {comparisonResult.metric_deltas.map((d, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50">
                      <td className="py-3 font-semibold text-[#172033]">{d.metric_name}</td>
                      <td className="py-3 text-slate-700">{d.run_a_value} {d.unit}</td>
                      <td className="py-3 text-slate-700">{d.run_b_value} {d.unit}</td>
                      <td className="py-3 font-mono font-bold">
                        <span className={d.absolute_delta < 0 ? 'text-emerald-600' : d.absolute_delta > 0 ? 'text-rose-600' : 'text-slate-600'}>
                          {d.absolute_delta > 0 ? `+${d.absolute_delta}` : d.absolute_delta} {d.unit}
                        </span>
                      </td>
                      <td className="py-3 font-mono text-slate-700">
                        {d.percentage_change > 0 ? `+${d.percentage_change}%` : `${d.percentage_change}%`}
                      </td>
                      <td className="py-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          d.better_run === comparisonResult.run_b_id ? 'bg-blue-100 text-blue-800' :
                          d.better_run === comparisonResult.run_a_id ? 'bg-cyan-100 text-cyan-800' : 'bg-slate-100 text-slate-700'
                        }`}>
                          {d.better_run || 'Equal'}
                        </span>
                      </td>
                      <td className="py-3 text-[#64748B]">{d.interpretation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Aligned Overlaid Comparison Charts */}
          {combinedChartData.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-bold text-[#172033] mb-3 flex items-center justify-between">
                  <span>Battery Temperature Trajectory Overlay</span>
                  <span className="text-xs text-[#64748B] font-normal">°C over Time</span>
                </h3>
                <div className="h-60 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={combinedChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="timestamp" unit="s" stroke="#94A3B8" fontSize={11} />
                      <YAxis unit="°C" stroke="#94A3B8" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: '8px', fontSize: '12px' }} />
                      <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px' }} />
                      <Line type="monotone" dataKey="temp_a" stroke="#0891B2" strokeWidth={2} dot={false} name={`Run A (${comparisonResult.run_a_id})`} />
                      <Line type="monotone" dataKey="temp_b" stroke="#2563EB" strokeWidth={2} dot={false} name={`Run B (${comparisonResult.run_b_id})`} strokeDasharray="4 4" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-bold text-[#172033] mb-3 flex items-center justify-between">
                  <span>Delivered Charging Current Overlay</span>
                  <span className="text-xs text-[#64748B] font-normal">Amperes over Time</span>
                </h3>
                <div className="h-60 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={combinedChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="timestamp" unit="s" stroke="#94A3B8" fontSize={11} />
                      <YAxis unit="A" stroke="#94A3B8" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: '8px', fontSize: '12px' }} />
                      <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px' }} />
                      <Line type="monotone" dataKey="current_a" stroke="#0891B2" strokeWidth={2} dot={false} name={`Run A (${comparisonResult.run_a_id})`} />
                      <Line type="monotone" dataKey="current_b" stroke="#2563EB" strokeWidth={2} dot={false} name={`Run B (${comparisonResult.run_b_id})`} strokeDasharray="4 4" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
