import React, { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp,
  Activity,
  Zap,
  Shield,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Cpu,
  Clock,
  Layers,
  FileText,
  Download,
  RefreshCw,
  GitCompare,
  ArrowRight,
  Info,
  Server,
  Thermometer,
  Gauge
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Legend,
  BarChart,
  Bar
} from 'recharts';
import { api } from '../services/api';

export default function ImpactAnalysis({
  currentRun,
  setCurrentRun,
  setActiveTab,
  targetEventId
}) {
  const [runsList, setRunsList] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(currentRun?.run_id || '');
  const [baselineRunId, setBaselineRunId] = useState('');
  const [comparisonRunId, setComparisonRunId] = useState('');
  const [report, setReport] = useState(null);
  const [comparisonReport, setComparisonReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedStage, setSelectedStage] = useState(null);
  const [activeChartTab, setActiveChartTab] = useState('grid'); // 'grid', 'charger', 'timeline'

  // Load available simulation runs
  useEffect(() => {
    async function fetchRuns() {
      try {
        const runs = await api.getRuns(30);
        setRunsList(runs || []);
        if (!selectedRunId && runs && runs.length > 0) {
          setSelectedRunId(runs[0].run_id);
        }
      } catch (err) {
        console.error('Failed to load incident runs', err);
      }
    }
    fetchRuns();
  }, []);

  // Update selectedRunId if currentRun changes externally
  useEffect(() => {
    if (currentRun?.run_id && currentRun.run_id !== selectedRunId) {
      setSelectedRunId(currentRun.run_id);
    }
  }, [currentRun]);

  // Load Impact Analysis Report whenever selectedRunId or baselineRunId changes
  useEffect(() => {
    async function loadAnalysis() {
      if (!selectedRunId) return;
      setLoading(true);
      setError(null);
      try {
        const data = await api.getImpactAnalysis(selectedRunId, baselineRunId || null);
        setReport(data);
        if (data?.impact_chain?.length > 0 && !selectedStage) {
          setSelectedStage(data.impact_chain[0]);
        }
      } catch (err) {
        console.error('Failed to compute impact analysis', err);
        setError(err.message || 'Failed to compute impact analysis');
      } finally {
        setLoading(false);
      }
    }
    loadAnalysis();
  }, [selectedRunId, baselineRunId]);

  // Load comparison report if comparisonRunId is selected
  useEffect(() => {
    async function loadComparison() {
      if (!comparisonRunId) {
        setComparisonReport(null);
        return;
      }
      try {
        const data = await api.getImpactAnalysis(comparisonRunId, null);
        setComparisonReport(data);
      } catch (err) {
        console.error('Failed to compute comparison analysis', err);
      }
    }
    loadComparison();
  }, [comparisonRunId]);

  // Handle changing active run
  const handleSelectRun = async (runId) => {
    setSelectedRunId(runId);
    try {
      const fullRun = await api.getRun(runId);
      if (setCurrentRun) {
        setCurrentRun(fullRun);
      }
    } catch {
      // ignore
    }
  };

  // Export Markdown Report
  const handleExportMarkdown = () => {
    if (!report) return;
    const qm = report.quantitative_metrics;
    const asm = report.assessment;

    const mdContent = `# ThreatLens Cyber-Physical Impact Analysis Report
**Incident Run ID:** \`${report.run_id}\`  
**Scenario:** ${report.scenario_name} (\`${report.scenario_id}\`)  
**Attack Family:** ${report.scenario_family}  
**Attack Type:** ${report.attack_type}  
**Target EVSE:** ${report.target_charger_id}  
**Distribution Feeder:** ${report.affected_group}  
**Generated At:** ${new Date().toISOString()}  

---

## 1. Executive Summary & Impact Assessment
- **Severity Rating:** **${asm.severity_level}**
- **Severity Rationale:** ${asm.severity_rationale}
- **What Happened:** ${asm.what_happened}
- **Physical Changes:** ${asm.physical_changes}
- **Mitigation Applied:** ${asm.mitigation_applied}
- **Uncertainties & Caveats:** ${asm.uncertainties_and_limitations}

---

## 2. Quantitative Impact Metrics
| Metric | Observed Value | Engineering Unit | Reference / Limit |
|---|---|---|---|
| **Baseline Fleet Demand** | ${qm.baseline_fleet_demand_kw !== null ? qm.baseline_fleet_demand_kw : 'Unavailable'} | kW | Nominal Pre-Attack |
| **Attack Peak Fleet Demand** | ${qm.attack_peak_fleet_demand_kw} | kW | Peak Load Drawn |
| **Absolute Demand Change (Δ)** | ${qm.demand_change_kw !== null ? `${qm.demand_change_kw > 0 ? '+' : ''}${qm.demand_change_kw}` : 'Unavailable'} | kW | Attack - Baseline |
| **Percentage Demand Change** | ${qm.demand_change_pct !== null ? `${qm.demand_change_pct > 0 ? '+' : ''}${qm.demand_change_pct}%` : 'Unavailable'} | % | Relative Increase |
| **Feeder Loading** | ${qm.feeder_loading_pct}% | % | Capacity: ${qm.feeder_capacity_kw} kW |
| **Minimum Feeder Voltage** | ${qm.min_feeder_voltage_v} | V | Nominal: ${qm.feeder_nominal_voltage_v} V |
| **Voltage Deviation (ΔV)** | ${qm.voltage_deviation_v > 0 ? '+' : ''}${qm.voltage_deviation_v} | V | V_min - V_nom |
| **Voltage Brownout Violations** | ${qm.voltage_threshold_violations_count} | count | Threshold < 360V (0.90 p.u.) |
| **Target Charger Peak Current** | ${qm.target_charger_peak_current_a} | A | Hardware Breaker Limit: 150A |
| **Target Charger Peak Temperature**| ${qm.target_charger_peak_temp_c} | °C | Thermal Warning: 45°C, Trip: 55°C |
| **Time to Detection** | ${qm.time_to_detection_s !== null ? `${qm.time_to_detection_s}s` : 'Unavailable'} | seconds | Attack to Threshold Breach |
| **Time to Mitigation** | ${qm.time_to_mitigation_s !== null ? `${qm.time_to_mitigation_s}s` : 'Unavailable'} | seconds | Detection to Gateway/Defense |

---

## 3. Cyber-to-Physical Impact Chain
${report.impact_chain.map((st) => `
### Stage ${st.stage_order}: ${st.stage_name}
- **Observed Event:** ${st.observed_event}
- **Timestamp:** ${st.timestamp_s !== null ? `${st.timestamp_s}s` : 'Unavailable'}
- **Evidence Source:** ${st.evidence_source}
- **Grounding Classification:** ${st.evidence_type} (${st.status})
`).join('\n')}

---

## 4. Correlated Gateway Interventions
${report.gateway_interventions.length > 0 ? report.gateway_interventions.map((gw, idx) => `
- **[${gw.decision}]** Rule \`${gw.rule_id}\` on \`${gw.action}\` (${gw.charge_point_id}) at ${gw.timestamp}s:
  - Reason: ${gw.reason}
  - Setpoint: ${gw.original_limit !== null ? `${gw.original_limit}A` : 'N/A'} -> ${gw.modified_limit !== null ? `${gw.modified_limit}A` : 'N/A'}
  - Correlation: ${gw.correlation_type}
`).join('\n') : '_No active gateway interventions correlated with this run._'}

---

> **Notice:** ${report.disclaimer}
`;

    const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ThreatLens_Impact_Analysis_${report.run_id}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Helper for evidence badge styling
  const getEvidenceBadge = (evidenceType) => {
    if (evidenceType === 'Direct Evidence') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-300">
          Direct Evidence
        </span>
      );
    }
    if (evidenceType === 'Calculated Metric') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-blue-50 text-blue-800 border border-blue-300">
          Calculated Metric
        </span>
      );
    }
    if (evidenceType === 'Inferred Relationship') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-50 text-amber-800 border border-amber-300">
          Inferred Relationship
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-slate-100 text-slate-700 border border-slate-300">
        Unverified Hypothesis
      </span>
    );
  };

  const getSeverityBadge = (level) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return <span className="px-3 py-1 rounded-full text-xs font-bold font-mono bg-red-100 text-red-800 border border-red-300 uppercase tracking-wide">CRITICAL IMPACT</span>;
      case 'HIGH':
        return <span className="px-3 py-1 rounded-full text-xs font-bold font-mono bg-amber-100 text-amber-800 border border-amber-300 uppercase tracking-wide">HIGH SEVERITY</span>;
      case 'MEDIUM':
        return <span className="px-3 py-1 rounded-full text-xs font-bold font-mono bg-blue-100 text-blue-800 border border-blue-300 uppercase tracking-wide">MEDIUM SEVERITY</span>;
      default:
        return <span className="px-3 py-1 rounded-full text-xs font-bold font-mono bg-emerald-100 text-emerald-800 border border-emerald-300 uppercase tracking-wide">LOW / NOMINAL</span>;
    }
  };

  if (!report && loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] space-y-4 bg-white rounded-2xl border border-[#D7E1ED] p-12">
        <RefreshCw className="w-8 h-8 text-[#0891B2] animate-spin" />
        <span className="text-base font-bold text-[#172033] font-mono">Computing Cyber-Physical Impact Propagation...</span>
        <p className="text-xs text-[#52647A]">Extracting telemetry slices, feeder impedances, and gateway audit logs.</p>
      </div>
    );
  }

  const qm = report?.quantitative_metrics;
  const asm = report?.assessment;

  return (
    <div className="w-full space-y-8 pb-16 animate-page-enter">
      {/* 1. Header & Incident Selection Strip */}
      <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-[#E6FAFF] text-[#0891B2] border border-[#0891B2]/30">
                Cyber-to-Grid Traceability
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-slate-100 text-slate-700 border border-[#D7E1ED]">
                Zero ML Deterministic Physics
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#172033] font-mono flex items-center gap-2.5">
              <TrendingUp className="w-7 h-7 text-[#0891B2]" />
              Cyber-Physical Impact Analysis
            </h1>
            <p className="text-sm text-[#52647A] mt-1 max-w-3xl">
              Trace how cyber setpoint manipulation and protocol commands propagate from EVSE electronics to fleet active power demand and substation feeder voltage sag.
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 self-start lg:self-center">
            <button
              onClick={handleExportMarkdown}
              disabled={!report}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-[#D7E1ED] hover:bg-slate-50 text-xs font-mono font-bold text-[#172033] shadow-xs cursor-pointer disabled:opacity-50"
            >
              <Download className="w-4 h-4 text-[#0891B2]" />
              Export Report (MD)
            </button>
            <button
              onClick={() => handleSelectRun(selectedRunId)}
              className="p-2 rounded-xl bg-white border border-[#D7E1ED] hover:bg-slate-50 text-[#52647A] hover:text-[#172033] shadow-xs cursor-pointer"
              title="Refresh Analysis"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#0891B2]' : ''}`} />
            </button>
          </div>
        </div>

        {/* Selection Controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-[#EDF2F7]">
          {/* Active Incident Selector */}
          <div>
            <label className="block text-xs font-mono font-bold text-[#52647A] uppercase mb-1.5">
              Select Active Incident Run:
            </label>
            <select
              value={selectedRunId}
              onChange={(e) => handleSelectRun(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#F8FAFC] border border-[#D7E1ED] text-xs font-mono font-bold text-[#172033] focus:outline-none focus:ring-2 focus:ring-[#0891B2]/30 cursor-pointer"
            >
              {runsList.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} - {r.scenario_name} ({r.scenario_family})
                </option>
              ))}
            </select>
          </div>

          {/* Optional Baseline Selector */}
          <div>
            <label className="block text-xs font-mono font-bold text-[#52647A] uppercase mb-1.5">
              Baseline Comparison Run (Optional):
            </label>
            <select
              value={baselineRunId}
              onChange={(e) => setBaselineRunId(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#F8FAFC] border border-[#D7E1ED] text-xs font-mono text-[#172033] focus:outline-none focus:ring-2 focus:ring-[#0891B2]/30 cursor-pointer"
            >
              <option value="">Default (Pre-Attack Telemetry Window)</option>
              {runsList
                .filter((r) => r.run_id !== selectedRunId)
                .map((r) => (
                  <option key={r.run_id} value={r.run_id}>
                    {r.run_id} - {r.scenario_name}
                  </option>
                ))}
            </select>
          </div>

          {/* Side-by-Side Comparator Run */}
          <div>
            <label className="block text-xs font-mono font-bold text-[#52647A] uppercase mb-1.5">
              Side-by-Side Dual Run Compare:
            </label>
            <select
              value={comparisonRunId}
              onChange={(e) => setComparisonRunId(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#F8FAFC] border border-[#D7E1ED] text-xs font-mono text-[#172033] focus:outline-none focus:ring-2 focus:ring-[#0891B2]/30 cursor-pointer"
            >
              <option value="">None (Single Run Analysis)</option>
              {runsList
                .filter((r) => r.run_id !== selectedRunId)
                .map((r) => (
                  <option key={r.run_id} value={r.run_id}>
                    {r.run_id} - {r.scenario_name}
                  </option>
                ))}
            </select>
          </div>
        </div>

        {/* Selected Incident Context Strip */}
        {report && (
          <div className="bg-[#F8FAFC] border border-[#D7E1ED] rounded-xl p-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-xs font-mono">
            <div>
              <span className="text-[#52647A] block text-[11px]">Incident ID</span>
              <span className="font-bold text-[#0891B2] truncate block mt-0.5">{report.run_id}</span>
            </div>
            <div>
              <span className="text-[#52647A] block text-[11px]">Attack Type</span>
              <span className="font-bold text-[#172033] truncate block mt-0.5">{report.attack_type}</span>
            </div>
            <div>
              <span className="text-[#52647A] block text-[11px]">Target EVSE</span>
              <span className="font-bold text-[#172033] block mt-0.5">{report.target_charger_id}</span>
            </div>
            <div>
              <span className="text-[#52647A] block text-[11px]">Attack Start (t)</span>
              <span className="font-bold text-red-700 block mt-0.5">
                {report.attack_timestamp_s !== null ? `${report.attack_timestamp_s}s` : 'Unavailable'}
              </span>
            </div>
            <div>
              <span className="text-[#52647A] block text-[11px]">Detection</span>
              <span className={`font-bold block mt-0.5 ${report.detection_status === 'Detected' ? 'text-amber-700' : 'text-[#52647A]'}`}>
                {report.detection_status}
              </span>
            </div>
            <div>
              <span className="text-[#52647A] block text-[11px]">Mitigation</span>
              <span className={`font-bold block mt-0.5 ${report.mitigation_status === 'Mitigated' ? 'text-emerald-700' : (report.mitigation_status === 'Fault Tripped' ? 'text-red-700' : 'text-[#52647A]')}`}>
                {report.mitigation_status}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 2. Quantitative Impact Metrics (Section 3.C) */}
      {qm && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
          {/* Metric 1: Fleet Peak Demand & Delta */}
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-[#52647A]">
              <span className="text-[11px] font-mono font-bold uppercase">Fleet Peak Demand</span>
              <Zap className="w-4 h-4 text-[#0891B2]" />
            </div>
            <div className="text-2xl font-extrabold font-mono text-[#172033]">
              {qm.attack_peak_fleet_demand_kw} <span className="text-xs font-semibold text-[#52647A]">kW</span>
            </div>
            <div className="text-[11px] font-mono pt-2 border-t border-[#EDF2F7]">
              {qm.baseline_fleet_demand_kw !== null ? (
                <div className="flex items-center justify-between">
                  <span className="text-[#52647A]">Δ from Base:</span>
                  <span className={`font-bold ${qm.demand_change_kw > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                    {qm.demand_change_kw > 0 ? '+' : ''}{qm.demand_change_kw} kW ({qm.demand_change_pct > 0 ? '+' : ''}{qm.demand_change_pct}%)
                  </span>
                </div>
              ) : (
                <span className="text-[#52647A] italic">Baseline comparison unavailable</span>
              )}
            </div>
          </div>

          {/* Metric 2: Feeder Loading */}
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-[#52647A]">
              <span className="text-[11px] font-mono font-bold uppercase">Feeder Loading</span>
              <Gauge className="w-4 h-4 text-blue-600" />
            </div>
            <div className="text-2xl font-extrabold font-mono text-[#172033]">
              {qm.feeder_loading_pct}%
            </div>
            {/* Progress bar */}
            <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  qm.feeder_loading_pct >= 95 ? 'bg-red-600' : (qm.feeder_loading_pct >= 80 ? 'bg-amber-500' : 'bg-[#0891B2]')
                }`}
                style={{ width: `${Math.min(100, qm.feeder_loading_pct)}%` }}
              />
            </div>
            <div className="text-[11px] font-mono text-[#52647A] pt-1">
              Cap: {qm.feeder_capacity_kw} kW (Warn: 80%, Crit: 95%)
            </div>
          </div>

          {/* Metric 3: Feeder Voltage Sag */}
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-[#52647A]">
              <span className="text-[11px] font-mono font-bold uppercase">Min Feeder Voltage</span>
              <Activity className="w-4 h-4 text-cyan-600" />
            </div>
            <div className={`text-2xl font-extrabold font-mono ${qm.min_feeder_voltage_v < 360 ? 'text-red-600' : 'text-[#172033]'}`}>
              {qm.min_feeder_voltage_v} <span className="text-xs font-semibold text-[#52647A]">V</span>
            </div>
            <div className="text-[11px] font-mono text-[#52647A] pt-2 border-t border-[#EDF2F7] flex items-center justify-between">
              <span>Dev (ΔV):</span>
              <span className={`font-bold ${qm.voltage_deviation_v < -20 ? 'text-amber-700' : 'text-[#172033]'}`}>
                {qm.voltage_deviation_v} V (Nom: {qm.feeder_nominal_voltage_v}V)
              </span>
            </div>
          </div>

          {/* Metric 4: Target Charger Extremes */}
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-[#52647A]">
              <span className="text-[11px] font-mono font-bold uppercase">Peak Current & Temp</span>
              <Thermometer className="w-4 h-4 text-amber-600" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-extrabold font-mono text-[#172033]">{qm.target_charger_peak_current_a}A</span>
              <span className={`text-lg font-bold font-mono ${qm.target_charger_peak_temp_c >= 45 ? 'text-amber-700' : 'text-[#52647A]'}`}>
                / {qm.target_charger_peak_temp_c}°C
              </span>
            </div>
            <div className="text-[11px] font-mono text-[#52647A] pt-2 border-t border-[#EDF2F7]">
              Thermal limit: 45°C (Caution) / 55°C (Trip)
            </div>
          </div>

          {/* Metric 5: Incident Timings */}
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-[#52647A]">
              <span className="text-[11px] font-mono font-bold uppercase">Response Latency</span>
              <Clock className="w-4 h-4 text-slate-600" />
            </div>
            <div className="text-base font-extrabold font-mono text-[#172033]">
              Det: {qm.time_to_detection_s !== null ? `${qm.time_to_detection_s}s` : 'N/A'}
            </div>
            <div className="text-[11px] font-mono text-[#52647A] pt-2 border-t border-[#EDF2F7] flex flex-col gap-0.5">
              <span>Mitigation: {qm.time_to_mitigation_s !== null ? `${qm.time_to_mitigation_s}s` : 'N/A'}</span>
              <span>Duration: {qm.attack_duration_s !== null ? `${qm.attack_duration_s}s` : 'N/A'}</span>
            </div>
          </div>

          {/* Metric 6: Affected Units & Status */}
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-[#52647A]">
              <span className="text-[11px] font-mono font-bold uppercase">Fleet Integrity</span>
              <Layers className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-base font-extrabold font-mono text-[#172033]">
              {qm.active_chargers_count} Active / {qm.affected_chargers_count} Target
            </div>
            <div className="text-[11px] font-mono pt-2 border-t border-[#EDF2F7] flex items-center justify-between">
              <span className="text-[#52647A]">Breaker Trips:</span>
              <span className={`font-bold ${qm.faulted_chargers_count > 0 ? 'text-red-700' : 'text-emerald-700'}`}>
                {qm.faulted_chargers_count} Faulted
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 3. Cyber-to-Physical Impact Chain (Section 3.B) */}
      {report?.impact_chain && (
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#EDF2F7] pb-4">
            <div>
              <h2 className="text-lg font-bold font-mono text-[#172033] flex items-center gap-2">
                <Cpu className="w-5 h-5 text-[#0891B2]" />
                Cyber-to-Physical Event Flow (6-Stage Impact Cascade)
              </h2>
              <p className="text-xs text-[#52647A] mt-0.5">
                Click any stage below to inspect verified telemetry records, protocol frames, and causal proof.
              </p>
            </div>
            <span className="text-xs font-mono text-[#52647A] bg-[#F8FAFC] px-3 py-1.5 rounded-lg border border-[#D7E1ED]">
              Grounded Event Flow
            </span>
          </div>

          {/* Stepper Pipeline Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-3">
            {report.impact_chain.map((stage) => {
              const isSelected = selectedStage?.stage_id === stage.stage_id;
              return (
                <div
                  key={stage.stage_id}
                  onClick={() => setSelectedStage(stage)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? 'bg-[#E6FAFF] border-[#0891B2] shadow-sm'
                      : 'bg-[#F8FAFC] border-[#D7E1ED] hover:border-cyan-400 hover:bg-white'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono font-bold text-[#0891B2]">
                        Stage {stage.stage_order}
                      </span>
                      {stage.timestamp_s !== null && (
                        <span className="text-[10px] font-mono text-[#52647A]">
                          t={stage.timestamp_s}s
                        </span>
                      )}
                    </div>
                    <h3 className="text-xs font-bold font-mono text-[#172033]">
                      {stage.stage_name.replace(/^[0-9]\.\s*/, '')}
                    </h3>
                    <p className="text-[11px] text-[#52647A] line-clamp-2 leading-relaxed">
                      {stage.observed_event}
                    </p>
                  </div>
                  <div className="pt-3 mt-3 border-t border-[#EDF2F7] flex items-center justify-between">
                    {getEvidenceBadge(stage.evidence_type)}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Stage Deep Inspector Drawer / Callout */}
          {selectedStage && (
            <div className="bg-[#F8FAFC] border border-[#D7E1ED] rounded-xl p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#EDF2F7] pb-3">
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-lg bg-[#0891B2] text-white flex items-center justify-center font-mono font-bold text-sm">
                    {selectedStage.stage_order}
                  </span>
                  <div>
                    <h4 className="text-sm font-bold font-mono text-[#172033]">
                      Stage {selectedStage.stage_order}: {selectedStage.stage_name}
                    </h4>
                    <span className="text-xs text-[#52647A]">
                      Evidence Source: <code className="text-[#0891B2] font-mono">{selectedStage.evidence_source}</code>
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getEvidenceBadge(selectedStage.evidence_type)}
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-white border border-[#D7E1ED] text-[#172033]">
                    {selectedStage.status}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                <div className="p-3.5 bg-white border border-[#D7E1ED] rounded-lg space-y-1">
                  <span className="text-[#52647A] font-bold block text-[11px]">Observed Physical / Cyber Telemetry</span>
                  <p className="text-[#172033] font-sans text-xs leading-relaxed">{selectedStage.observed_event}</p>
                </div>
                <div className="p-3.5 bg-white border border-[#D7E1ED] rounded-lg space-y-1">
                  <span className="text-[#52647A] font-bold block text-[11px]">Verified Supporting Parameters</span>
                  <pre className="text-[11px] text-[#0891B2] overflow-x-auto whitespace-pre-wrap font-mono">
                    {JSON.stringify(selectedStage.details, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="text-[11px] text-[#52647A] font-mono bg-blue-50/60 border border-blue-200/60 p-3 rounded-lg flex items-center gap-2">
                <Info className="w-4 h-4 text-blue-600 shrink-0" />
                <span>
                  <strong>Grounding Rule:</strong> Direct evidence indicates an empirically recorded telemetry packet or event log. Inferred relationships reflect physical circuit equations ($P=VI$, Joule heating $I^2R$, voltage sag $\Delta V$).
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 4. Visualizations: Demand, Voltage Sag, Thermal Extremes (Section 3.D) */}
      {report?.timeseries && report.timeseries.length > 0 && (
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#EDF2F7] pb-4">
            <div>
              <h2 className="text-lg font-bold font-mono text-[#172033] flex items-center gap-2">
                <Activity className="w-5 h-5 text-[#0891B2]" />
                Physical Telemetry Visualizations
              </h2>
              <p className="text-xs text-[#52647A] mt-0.5">
                Real time-series telemetry from the selected run showing fleet active power, feeder voltage, and target charger temperature.
              </p>
            </div>

            {/* Chart toggle tabs */}
            <div className="flex items-center gap-1 bg-[#F8FAFC] border border-[#D7E1ED] p-1 rounded-xl">
              <button
                onClick={() => setActiveChartTab('grid')}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-colors cursor-pointer ${
                  activeChartTab === 'grid' ? 'bg-[#0891B2] text-white shadow-xs' : 'text-[#52647A] hover:text-[#172033]'
                }`}
              >
                Feeder Power & Voltage
              </button>
              <button
                onClick={() => setActiveChartTab('charger')}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-colors cursor-pointer ${
                  activeChartTab === 'charger' ? 'bg-[#0891B2] text-white shadow-xs' : 'text-[#52647A] hover:text-[#172033]'
                }`}
              >
                Target EVSE Current & Temp
              </button>
            </div>
          </div>

          {/* Chart Content Area */}
          {activeChartTab === 'grid' ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Feeder Active Demand vs Capacity */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-[#172033]">Fleet Active Demand vs Rated Capacity</span>
                  <span className="text-[#52647A]">Feeder Capacity: {qm?.feeder_capacity_kw || 800} kW</span>
                </div>
                <div className="h-64 w-full bg-[#F8FAFC] border border-[#D7E1ED] rounded-xl p-3">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={report.timeseries}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#EDF2F7" />
                      <XAxis dataKey="timestamp" unit="s" stroke="#64748B" fontSize={11} />
                      <YAxis unit=" kW" stroke="#64748B" fontSize={11} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                      />
                      <ReferenceLine y={qm?.feeder_capacity_kw || 800} stroke="#DC2626" strokeDasharray="4 4" label={{ value: 'Capacity (800kW)', fill: '#DC2626', fontSize: 10 }} />
                      <ReferenceLine y={(qm?.feeder_capacity_kw || 800) * 0.8} stroke="#D97706" strokeDasharray="3 3" label={{ value: '80% Warn', fill: '#D97706', fontSize: 10 }} />
                      <Line type="monotone" dataKey="fleet_demand_kw" stroke="#0891B2" strokeWidth={2.5} dot={false} name="Fleet Demand (kW)" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Feeder Voltage Sag */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-[#172033]">Feeder Voltage Sag Response</span>
                  <span className="text-[#52647A]">Nominal: {qm?.feeder_nominal_voltage_v || 400} V</span>
                </div>
                <div className="h-64 w-full bg-[#F8FAFC] border border-[#D7E1ED] rounded-xl p-3">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={report.timeseries}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#EDF2F7" />
                      <XAxis dataKey="timestamp" unit="s" stroke="#64748B" fontSize={11} />
                      <YAxis domain={['auto', 'auto']} unit=" V" stroke="#64748B" fontSize={11} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                      />
                      <ReferenceLine y={qm?.feeder_nominal_voltage_v || 400} stroke="#64748B" strokeDasharray="3 3" label={{ value: 'Nominal 400V', fill: '#64748B', fontSize: 10 }} />
                      <ReferenceLine y={360} stroke="#DC2626" strokeDasharray="4 4" label={{ value: 'Brownout 360V', fill: '#DC2626', fontSize: 10 }} />
                      <Line type="monotone" dataKey="feeder_voltage_v" stroke="#2563EB" strokeWidth={2.5} dot={false} name="Feeder Voltage (V)" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-bold text-[#172033]">Target EVSE Current (A) & Battery Pack Temperature (°C)</span>
                <span className="text-[#52647A]">Dual Axis Physics Coupling (Joule Heating)</span>
              </div>
              <div className="h-72 w-full bg-[#F8FAFC] border border-[#D7E1ED] rounded-xl p-3">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={report.timeseries}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#EDF2F7" />
                    <XAxis dataKey="timestamp" unit="s" stroke="#64748B" fontSize={11} />
                    <YAxis yAxisId="current" unit=" A" stroke="#0891B2" fontSize={11} />
                    <YAxis yAxisId="temp" orientation="right" unit=" °C" stroke="#D97706" fontSize={11} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                    />
                    <Legend />
                    <ReferenceLine yAxisId="temp" y={45} stroke="#D97706" strokeDasharray="3 3" label={{ value: 'Caution 45°C', fill: '#D97706', fontSize: 10 }} />
                    <ReferenceLine yAxisId="temp" y={55} stroke="#DC2626" strokeDasharray="4 4" label={{ value: 'Thermal Trip 55°C', fill: '#DC2626', fontSize: 10 }} />
                    <Line yAxisId="current" type="monotone" dataKey="charger_current_a" stroke="#0891B2" strokeWidth={2} dot={false} name="Charger Current (A)" />
                    <Line yAxisId="temp" type="monotone" dataKey="battery_temp_c" stroke="#EA580C" strokeWidth={2.5} dot={false} name="Battery Temperature (°C)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 5. Impact Assessment & Severity Classification (Section 3.E) */}
      {asm && (
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#EDF2F7] pb-4">
            <div>
              <h2 className="text-lg font-bold font-mono text-[#172033] flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#0891B2]" />
                Evidence-Grounded Impact Assessment
              </h2>
              <p className="text-xs text-[#52647A] mt-0.5">
                Systematic engineering answers grounded in verified scenario records and state machine transitions.
              </p>
            </div>
            <div>{getSeverityBadge(asm.severity_level)}</div>
          </div>

          {/* Severity Rationale Banner */}
          <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#D7E1ED] flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs font-mono space-y-1">
              <span className="font-bold text-[#172033]">Severity Classification Rationale:</span>
              <p className="text-[#52647A] font-sans">{asm.severity_rationale}</p>
            </div>
          </div>

          {/* 6 Structured Assessment Questions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-4 rounded-xl bg-white border border-[#D7E1ED] space-y-1.5 shadow-2xs">
              <span className="text-[#0891B2] font-bold block text-[11px]">1. What happened?</span>
              <p className="text-[#172033] font-sans leading-relaxed">{asm.what_happened}</p>
            </div>

            <div className="p-4 rounded-xl bg-white border border-[#D7E1ED] space-y-1.5 shadow-2xs">
              <span className="text-[#0891B2] font-bold block text-[11px]">2. Which charger or fleet segment was affected?</span>
              <p className="text-[#172033] font-sans leading-relaxed">{asm.affected_segment}</p>
            </div>

            <div className="p-4 rounded-xl bg-white border border-[#D7E1ED] space-y-1.5 shadow-2xs">
              <span className="text-[#0891B2] font-bold block text-[11px]">3. What changed physically in the simulation?</span>
              <p className="text-[#172033] font-sans leading-relaxed">{asm.physical_changes}</p>
            </div>

            <div className="p-4 rounded-xl bg-white border border-[#D7E1ED] space-y-1.5 shadow-2xs">
              <span className="text-[#0891B2] font-bold block text-[11px]">4. Were any configured thresholds crossed?</span>
              <ul className="list-disc list-inside text-[#172033] font-sans space-y-1">
                {asm.thresholds_crossed.map((tc, i) => (
                  <li key={i} className="text-red-700 font-medium">{tc}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-white border border-[#D7E1ED] space-y-1.5 shadow-2xs">
              <span className="text-[#0891B2] font-bold block text-[11px]">5. Which gateway policy or mitigation was applied?</span>
              <p className="text-[#172033] font-sans leading-relaxed">{asm.mitigation_applied}</p>
            </div>

            <div className="p-4 rounded-xl bg-white border border-[#D7E1ED] space-y-1.5 shadow-2xs">
              <span className="text-[#0891B2] font-bold block text-[11px]">6. What remains uncertain or unverified?</span>
              <p className="text-[#52647A] font-sans leading-relaxed italic">{asm.uncertainties_and_limitations}</p>
            </div>
          </div>
        </div>
      )}

      {/* 6. Correlated Gateway Interventions Feed (Section 5) */}
      <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#EDF2F7] pb-4">
          <div>
            <h3 className="text-base font-bold font-mono text-[#172033] flex items-center gap-2">
              <Shield className="w-5 h-5 text-[#0891B2]" />
              Correlated OCPP Gateway Interventions ({report?.gateway_interventions?.length || 0})
            </h3>
            <p className="text-xs text-[#52647A] mt-0.5">
              Verified in-flight OCPP 1.6-J messages intercepted by the deterministic security gateway.
            </p>
          </div>
          <button
            onClick={() => setActiveTab('ocpp-gateway')}
            className="text-xs font-mono font-bold text-[#0891B2] hover:underline cursor-pointer flex items-center gap-1"
          >
            Open Live Gateway Dashboard →
          </button>
        </div>

        {report?.gateway_interventions && report.gateway_interventions.length > 0 ? (
          <div className="overflow-x-auto border border-[#D7E1ED] rounded-xl">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#F8FAFC] text-[#52647A] border-b border-[#D7E1ED]">
                <tr>
                  <th className="py-3 px-4">Time</th>
                  <th className="py-3 px-4">Charge Point</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Decision</th>
                  <th className="py-3 px-4">Rule</th>
                  <th className="py-3 px-4">Limits (Orig → Mod)</th>
                  <th className="py-3 px-4">Reason</th>
                  <th className="py-3 px-4">Correlation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D7E1ED]">
                {report.gateway_interventions.map((gw, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-3 px-4 text-[#52647A]">{gw.timestamp}s</td>
                    <td className="py-3 px-4 font-bold text-[#172033]">{gw.charge_point_id}</td>
                    <td className="py-3 px-4 text-[#0891B2] font-semibold">{gw.action}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        gw.decision === 'ALLOW' ? 'bg-emerald-100 text-emerald-800' : (
                          gw.decision === 'CLAMP' ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800'
                        )
                      }`}>
                        {gw.decision}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-700">{gw.rule_id}</td>
                    <td className="py-3 px-4 text-[#172033]">
                      {gw.original_limit !== null ? `${gw.original_limit}A` : 'N/A'} → {gw.modified_limit !== null ? `${gw.modified_limit}A` : 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-[#52647A] max-w-xs truncate" title={gw.reason}>
                      {gw.reason}
                    </td>
                    <td className="py-3 px-4 text-[11px] text-[#52647A]">
                      <span className="bg-slate-100 px-2 py-0.5 rounded border border-slate-200">{gw.correlation_type}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 bg-[#F8FAFC] border border-[#D7E1ED] rounded-xl text-xs font-mono text-[#52647A] space-y-1">
            <span className="font-bold text-[#172033] block">No Active Gateway Interventions Recorded</span>
            <span>Gateway was either bypassed, in transparent monitoring mode, or no setpoints exceeded safety thresholds.</span>
          </div>
        )}
      </div>

      {/* 7. Dual Incident Comparison View (Section 3.F) */}
      {comparisonReport && (
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-[#EDF2F7] pb-4">
            <h3 className="text-base font-bold font-mono text-[#172033] flex items-center gap-2">
              <GitCompare className="w-5 h-5 text-purple-600" />
              Side-by-Side Incident Delta Comparison: {report.run_id} vs {comparisonReport.run_id}
            </h3>
            <span className="text-xs font-mono text-[#52647A]">Dual Comparative Analytics</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
            {/* Peak Demand Delta */}
            <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#D7E1ED] space-y-1">
              <span className="text-[#52647A] block">Peak Active Demand Delta</span>
              <div className="text-lg font-bold text-[#172033]">
                {report.quantitative_metrics.attack_peak_fleet_demand_kw} kW vs {comparisonReport.quantitative_metrics.attack_peak_fleet_demand_kw} kW
              </div>
              <span className="text-cyan-700 font-bold block pt-1">
                Δ: {(report.quantitative_metrics.attack_peak_fleet_demand_kw - comparisonReport.quantitative_metrics.attack_peak_fleet_demand_kw).toFixed(1)} kW
              </span>
            </div>

            {/* Voltage Sag Delta */}
            <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#D7E1ED] space-y-1">
              <span className="text-[#52647A] block">Min Feeder Voltage Delta</span>
              <div className="text-lg font-bold text-[#172033]">
                {report.quantitative_metrics.min_feeder_voltage_v} V vs {comparisonReport.quantitative_metrics.min_feeder_voltage_v} V
              </div>
              <span className="text-blue-700 font-bold block pt-1">
                Δ: {(report.quantitative_metrics.min_feeder_voltage_v - comparisonReport.quantitative_metrics.min_feeder_voltage_v).toFixed(1)} V
              </span>
            </div>

            {/* Peak Temp Delta */}
            <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#D7E1ED] space-y-1">
              <span className="text-[#52647A] block">Target Battery Temp Delta</span>
              <div className="text-lg font-bold text-[#172033]">
                {report.quantitative_metrics.target_charger_peak_temp_c}°C vs {comparisonReport.quantitative_metrics.target_charger_peak_temp_c}°C
              </div>
              <span className="text-amber-700 font-bold block pt-1">
                Δ: {(report.quantitative_metrics.target_charger_peak_temp_c - comparisonReport.quantitative_metrics.target_charger_peak_temp_c).toFixed(1)}°C
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
