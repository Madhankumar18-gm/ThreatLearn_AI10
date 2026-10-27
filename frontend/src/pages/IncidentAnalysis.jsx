import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  Clock,
  Zap,
  Thermometer,
  ShieldAlert,
  ArrowRight,
  GitCompare,
  Layers,
  CheckCircle2,
  ListChecks,
  Eye,
  Sliders,
  Radio,
  FileSearch
} from 'lucide-react';
import { api } from '../services/api';
import ReplaySlider from '../components/ReplaySlider';
import AnimatedPropagationGraph from '../components/AnimatedPropagationGraph';
import ImpactMap from '../components/ImpactMap';
import EvidenceDrawer from '../components/EvidenceDrawer';

export default function IncidentAnalysis({
  currentRun,
  setActiveTab,
  onSelectEventForReplay
}) {
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [links, setLinks] = useState([]);
  const [guidance, setGuidance] = useState(null);
  const [inspectedLink, setInspectedLink] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [showGuidance, setShowGuidance] = useState(false);

  // Fetch correlation links and investigator guidance when run changes
  useEffect(() => {
    if (currentRun) {
      setCurrentTime(0);
      api.getRunLinks(currentRun.run_id)
        .then((data) => {
          setLinks(data || []);
          if (data && data.length > 0) {
            setSelectedEventId(data[0].event_id);
          }
        })
        .catch((err) => console.error('Failed to load correlation links', err));

      api.getRunGuidance(currentRun.run_id)
        .then((data) => setGuidance(data))
        .catch((err) => console.error('Failed to load guidance', err));
    }
  }, [currentRun]);

  if (!currentRun) {
    return (
      <div className="w-full py-24 text-center space-y-5 bg-white rounded-2xl border border-[#D7E1ED] p-12 shadow-xs">
        <Activity className="w-16 h-16 text-[#94A3B8] mx-auto" />
        <h3 className="text-xl font-bold text-[#172033] font-mono">No Active Incident Loaded</h3>
        <p className="text-sm text-[#52647A] max-w-lg mx-auto">
          Please run a simulation from the Scenario Lab or build a custom scenario to view high-resolution telemetry.
        </p>
        <button
          onClick={() => setActiveTab('scenario-lab')}
          className="px-6 py-3.5 bg-[#0891B2] hover:bg-cyan-700 text-white font-bold text-sm rounded-xl uppercase tracking-wider cursor-pointer shadow-sm transition-all"
        >
          Open Scenario Lab
        </button>
      </div>
    );
  }

  const telemetry = currentRun.telemetry || [];
  const events = currentRun.events || [];
  const crossings = currentRun.threshold_crossings || [];

  const handleOpenDrawer = (link) => {
    setInspectedLink(link);
    setIsDrawerOpen(true);
  };

  return (
    <div className="w-full space-y-8 pb-12 animate-page-enter">
      {/* Top Banner / Run Info */}
      <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-8 shadow-xs flex flex-wrap items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-mono text-sm font-bold text-[#0891B2] bg-[#E6FAFF] px-3 py-1 rounded-md border border-[#0891B2]/30">
              Run ID: {currentRun.run_id}
            </span>
            <span className="text-xs sm:text-sm font-mono px-3 py-1 rounded-md bg-slate-100 text-[#172033] border border-[#D7E1ED] font-semibold">
              {currentRun.scenario_family}
            </span>
            {currentRun.fault_triggered ? (
              <span className="text-xs sm:text-sm font-mono px-3 py-1 rounded-md bg-red-100 text-red-800 border border-red-200 font-bold">
                CRITICAL FAULT TRIP
              </span>
            ) : (
              <span className="text-xs sm:text-sm font-mono px-3 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
                NORMAL SYSTEM EXIT
              </span>
            )}
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold font-mono text-[#172033]">
            {currentRun.scenario_name}
          </h2>
          <p className="text-sm text-[#52647A]">
            Duration: <strong className="text-[#172033]">{currentRun.duration_seconds}s</strong> | Random Seed: <strong className="text-[#172033]">{currentRun.seed}</strong> | Telemetry Slices: <strong className="text-[#172033]">{telemetry.length}</strong>
          </p>
        </div>

        {/* Quick KPI Stat Pills */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="px-5 py-3 bg-[#F8FAFC] rounded-xl border border-[#D7E1ED] text-center min-w-[120px]">
            <span className="text-xs text-[#52647A] uppercase font-mono block font-bold">Peak Current</span>
            <span className="text-xl sm:text-2xl font-bold text-blue-700 font-mono">{currentRun.peak_current} A</span>
          </div>
          <div className="px-5 py-3 bg-[#F8FAFC] rounded-xl border border-[#D7E1ED] text-center min-w-[120px]">
            <span className="text-xs text-[#52647A] uppercase font-mono block font-bold">Peak Temp</span>
            <span className={`text-xl sm:text-2xl font-bold font-mono ${currentRun.peak_temperature >= 45 ? 'text-amber-700' : 'text-emerald-700'}`}>
              {currentRun.peak_temperature} °C
            </span>
          </div>
          <div className="px-5 py-3 bg-[#F8FAFC] rounded-xl border border-[#D7E1ED] text-center min-w-[120px]">
            <span className="text-xs text-[#52647A] uppercase font-mono block font-bold">Final SoC</span>
            <span className="text-xl sm:text-2xl font-bold text-[#0891B2] font-mono">{currentRun.final_soc} %</span>
          </div>
        </div>
      </div>

      {/* Feature F34: Interactive Replay Slider */}
      <ReplaySlider
        telemetry={telemetry}
        events={events}
        currentTime={currentTime}
        onTimeChange={setCurrentTime}
      />

      {/* Feature F33: Animated Propagation Graph */}
      <AnimatedPropagationGraph
        links={links}
        activeEventId={selectedEventId}
      />

      {/* Feature F35: Component-Level Impact & State Map */}
      <ImpactMap
        currentRun={currentRun}
        links={links}
      />

      {/* Feature F41: Rule-Based Investigator Guidance */}
      {guidance && (
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E2E8F0] pb-3">
            <div>
              <div className="flex items-center gap-2">
                <ListChecks className="w-5 h-5 text-[#0891B2]" />
                <h3 className="text-base font-bold text-[#172033]">Investigator Guidance Checklist (F41)</h3>
              </div>
              <p className="text-xs text-[#52647A] mt-0.5">{guidance.incident_summary}</p>
            </div>
            <button
              onClick={() => setShowGuidance(!showGuidance)}
              className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-[#172033] font-bold text-xs rounded-lg cursor-pointer transition-all border border-[#D7E1ED]"
            >
              {showGuidance ? 'Hide Steps' : `View ${guidance.suggested_steps?.length || 0} Priority Steps`}
            </button>
          </div>

          {showGuidance && (
            <div className="space-y-2.5 pt-1">
              {(guidance.suggested_steps || []).map((step) => (
                <div key={step.step_number} className="p-3.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl flex items-start gap-3 text-xs">
                  <span className="w-6 h-6 rounded-full bg-cyan-100 text-[#0891B2] font-mono font-bold flex items-center justify-center shrink-0">
                    {step.step_number}
                  </span>
                  <div className="space-y-1">
                    <p className="font-bold text-[#172033]">{step.recommendation}</p>
                    <p className="text-[#52647A]">{step.reason}</p>
                    <div className="flex items-center gap-3 pt-1 text-[11px] font-mono text-[#64748B]">
                      <span>Target: <strong className="text-[#172033]">{step.target_component || 'System'}</strong></span>
                      {step.supporting_evidence_id && (
                        <span>Evidence: <strong className="text-[#0891B2]">{step.supporting_evidence_id}</strong></span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Correlated Cyber-Physical Links Table with Evidence Drawer (F21, F29, F36) */}
      {links.length > 0 && (
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
            <div>
              <h3 className="text-base font-bold text-[#172033]">
                Correlated Cyber-Physical Links & Evidence ({links.length})
              </h3>
              <p className="text-xs text-[#52647A]">
                Validated causal paths matching graph connectivity, physical delays, and noise margins.
              </p>
            </div>
            <span className="text-xs font-mono font-bold px-3 py-1 bg-cyan-50 text-[#0891B2] rounded-md border border-cyan-200">
              Deterministic Proof
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#D7E1ED] bg-[#F8FAFC] text-[#64748B] uppercase tracking-wider font-semibold">
                  <th className="py-2.5 px-3">Link ID</th>
                  <th className="py-2.5 px-3">Event Type</th>
                  <th className="py-2.5 px-3">Target Signal</th>
                  <th className="py-2.5 px-3">Measured Delay</th>
                  <th className="py-2.5 px-3">Observed Delta</th>
                  <th className="py-2.5 px-3">Confidence</th>
                  <th className="py-2.5 px-3">Evidence Label</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0] font-mono">
                {links.map((link) => (
                  <tr key={link.link_id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-bold text-[#0891B2]">{link.link_id}</td>
                    <td className="py-2.5 px-3 text-[#172033] font-bold">{link.event_type}</td>
                    <td className="py-2.5 px-3 text-[#52647A]">{link.target_signal}</td>
                    <td className="py-2.5 px-3 text-[#172033]">{link.time_delay}s</td>
                    <td className="py-2.5 px-3 font-bold text-[#0891B2]">
                      {link.observed_change > 0 ? '+' : ''}{link.observed_change} {link.change_unit}
                    </td>
                    <td className="py-2.5 px-3 text-emerald-600 font-bold">{link.confidence_score}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        link.evidence_label === 'Observed'
                          ? 'bg-emerald-100 text-emerald-800'
                          : link.evidence_label === 'Inferred'
                          ? 'bg-cyan-100 text-[#0891B2]'
                          : 'bg-amber-100 text-amber-800'
                      }`}>
                        {link.evidence_label}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenDrawer(link)}
                          className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-[#172033] rounded font-sans font-bold flex items-center gap-1 cursor-pointer border border-[#D7E1ED]"
                        >
                          <Eye className="w-3.5 h-3.5 text-[#0891B2]" /> Inspect Evidence
                        </button>
                        <button
                          onClick={() => onSelectEventForReplay(link.event_id)}
                          className="px-2.5 py-1 bg-[#0891B2] hover:bg-cyan-700 text-white rounded font-sans font-bold flex items-center gap-1 cursor-pointer"
                        >
                          <GitCompare className="w-3.5 h-3.5" /> Replay
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* High-Resolution Telemetry Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Chart 1: Battery Temperature */}
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-7 space-y-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#EDF2F7] pb-3">
            <div>
              <h4 className="text-base font-bold text-[#172033] font-mono flex items-center gap-2">
                <Thermometer className="w-5 h-5 text-rose-500" />
                Physical Pack Temperature vs Sensor (°C)
              </h4>
              <p className="text-xs text-[#52647A] mt-0.5">
                Physical Joule heating model compared against reported sensor measurement
              </p>
            </div>
            <span className="text-xs font-mono font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded border border-amber-200">
              Trip Threshold: 60°C
            </span>
          </div>

          <div className="h-80 sm:h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetry} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="timestamp" stroke="#64748B" tick={{ fontSize: 12 }} />
                <YAxis domain={[20, 80]} stroke="#64748B" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#CBD5E1',
                    color: '#172033',
                    fontSize: '12px',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '13px', paddingTop: '10px' }} />
                <ReferenceLine
                  y={45.0}
                  stroke="#D97706"
                  strokeDasharray="4 4"
                  label={{ value: 'Warning (45°C)', fill: '#D97706', fontSize: 11 }}
                />
                <ReferenceLine
                  y={60.0}
                  stroke="#DC2626"
                  strokeDasharray="3 3"
                  label={{ value: 'Critical Trip (60°C)', fill: '#DC2626', fontSize: 11 }}
                />
                <Line
                  type="monotone"
                  dataKey="battery_temperature"
                  name="Physical Pack Temp (°C)"
                  stroke="#E11D48"
                  strokeWidth={2.8}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="sensor_temperature"
                  name="Sensor Reported Reading (°C)"
                  stroke="#0891B2"
                  strokeWidth={1.8}
                  strokeDasharray="3 3"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Charging Current (A) */}
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-7 space-y-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#EDF2F7] pb-3">
            <div>
              <h4 className="text-base font-bold text-[#172033] font-mono flex items-center gap-2">
                <Zap className="w-5 h-5 text-[#0891B2]" />
                Actual Output Current (A)
              </h4>
              <p className="text-xs text-[#52647A] mt-0.5">
                Current clamped by charger limits, BMS requests, and physical state transitions
              </p>
            </div>
            <span className="text-xs font-mono font-bold text-[#0891B2] bg-[#E6FAFF] px-2.5 py-1 rounded border border-[#0891B2]/30">
              Hardware Limit: 150A
            </span>
          </div>

          <div className="h-80 sm:h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetry} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="timestamp" stroke="#64748B" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 180]} stroke="#64748B" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#CBD5E1',
                    color: '#172033',
                    fontSize: '12px',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '13px', paddingTop: '10px' }} />
                <ReferenceLine
                  y={120.0}
                  stroke="#D97706"
                  strokeDasharray="4 4"
                  label={{ value: 'Warning Limit (120A)', fill: '#D97706', fontSize: 11 }}
                />
                <Line
                  type="stepAfter"
                  dataKey="charging_current"
                  name="Actual Current (A)"
                  stroke="#0891B2"
                  strokeWidth={2.8}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Physics Consistency Residual (F23) */}
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-7 space-y-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#EDF2F7] pb-3">
            <div>
              <h4 className="text-base font-bold text-[#172033] font-mono flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-500" />
                Digital Twin Physics Residual: Residual = Reported - Predicted (F23)
              </h4>
              <p className="text-xs text-[#52647A] mt-0.5">
                Divergence between reported telemetry and energy conservation observer
              </p>
            </div>
            <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded border border-[#D7E1ED]">
              Tolerance: ±3.0°C
            </span>
          </div>

          <div className="h-80 sm:h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetry} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="timestamp" stroke="#64748B" tick={{ fontSize: 12 }} />
                <YAxis domain={[-15, 25]} stroke="#64748B" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#CBD5E1',
                    color: '#172033',
                    fontSize: '12px',
                    borderRadius: '8px'
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '13px', paddingTop: '10px' }} />
                <ReferenceLine y={3.0} stroke="#D97706" strokeDasharray="3 3" label={{ value: '+3°C Tolerance', fill: '#D97706', fontSize: 10 }} />
                <ReferenceLine y={-3.0} stroke="#D97706" strokeDasharray="3 3" label={{ value: '-3°C Tolerance', fill: '#D97706', fontSize: 10 }} />
                <ReferenceLine y={0.0} stroke="#94A3B8" strokeWidth={1.5} />
                <Line
                  type="monotone"
                  dataKey="temperature_residual"
                  name="Thermal Residual (°C)"
                  stroke="#F59E0B"
                  strokeWidth={2.8}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Battery State of Charge (%) */}
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-7 space-y-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#EDF2F7] pb-3">
            <div>
              <h4 className="text-base font-bold text-[#172033] font-mono flex items-center gap-2">
                <Layers className="w-5 h-5 text-emerald-600" />
                Battery State of Charge (%)
              </h4>
              <p className="text-xs text-[#52647A] mt-0.5">
                Coulombic integration of charging current over 60 kWh pack capacity
              </p>
            </div>
            <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200">
              Capacity: 60 kWh
            </span>
          </div>

          <div className="h-80 sm:h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetry} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="timestamp" stroke="#64748B" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} stroke="#64748B" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#CBD5E1',
                    color: '#172033',
                    fontSize: '12px',
                    borderRadius: '8px'
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '13px', paddingTop: '10px' }} />
                <Line
                  type="monotone"
                  dataKey="state_of_charge"
                  name="State of Charge (%)"
                  stroke="#059669"
                  strokeWidth={2.8}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Feature F36: Evidence Drawer */}
      <EvidenceDrawer
        link={inspectedLink}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}
