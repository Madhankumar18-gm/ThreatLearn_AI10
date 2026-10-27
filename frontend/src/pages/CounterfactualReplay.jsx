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
  GitCompare,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Zap,
  Thermometer,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Play
} from 'lucide-react';
import { api } from '../services/api';

export default function CounterfactualReplay({
  currentRun,
  targetEventId,
  setTargetEventId,
  setActiveTab
}) {
  const [replayResult, setReplayResult] = useState(null);
  const [isReplaying, setIsReplaying] = useState(false);
  const [error, setError] = useState(null);

  // Automatically select first event if none selected
  useEffect(() => {
    if (currentRun && currentRun.events && currentRun.events.length > 0) {
      if (!targetEventId || !currentRun.events.find((e) => e.event_id === targetEventId)) {
        // Prefer an attack event if available
        const atkEvent = currentRun.events.find(
          (e) => e.auth_status === 'unauthorized' || e.auth_status === 'spoofed'
        );
        setTargetEventId(atkEvent ? atkEvent.event_id : currentRun.events[0].event_id);
      }
    }
  }, [currentRun, targetEventId, setTargetEventId]);

  if (!currentRun) {
    return (
      <div className="w-full py-24 text-center space-y-5 bg-white rounded-2xl border border-[#D7E1ED] p-12 shadow-xs">
        <div className="w-18 h-18 rounded-2xl bg-slate-100 border border-[#D7E1ED] flex items-center justify-center mx-auto text-[#52647A]">
          <GitCompare className="w-9 h-9 text-[#52647A]" />
        </div>
        <h3 className="text-xl font-bold text-[#172033] font-mono">No Active Incident Loaded</h3>
        <p className="text-sm text-[#52647A] max-w-lg mx-auto">
          Please run a simulation from the Scenario Lab or Incident Analysis to execute counterfactual replay comparisons.
        </p>
        <button
          onClick={() => setActiveTab('scenario-lab')}
          className="px-6 py-3.5 bg-[#0891B2] hover:bg-cyan-700 text-white font-bold text-sm rounded-xl uppercase tracking-wider shadow-sm transition-all cursor-pointer"
        >
          Open Scenario Lab
        </button>
      </div>
    );
  }

  const handleExecuteReplay = async () => {
    if (!targetEventId) return;
    setIsReplaying(true);
    setError(null);
    try {
      const res = await api.runCounterfactual(currentRun.run_id, targetEventId);
      setReplayResult(res);
    } catch (err) {
      console.error('Counterfactual replay failed', err);
      setError(err.message || 'Counterfactual replay failed');
    } finally {
      setIsReplaying(false);
    }
  };

  const events = currentRun.events || [];

  return (
    <div className="w-full space-y-8 pb-12 animate-page-enter">
      {/* Title & Concept Explanation (Full Width) */}
      <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-8 shadow-xs space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="font-mono text-sm font-bold text-[#0891B2] bg-[#E6FAFF] px-3 py-1 rounded-md border border-[#0891B2]/30">
                Incident: {currentRun.run_id} ({currentRun.scenario_id})
              </span>
              <span className="text-xs sm:text-sm font-mono px-3 py-1 rounded-md bg-slate-100 text-[#52647A] border border-[#D7E1ED] font-semibold">
                Random Seed: {currentRun.seed}
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold font-mono text-[#172033] flex items-center gap-2.5">
              <GitCompare className="w-7 h-7 text-[#0891B2]" />
              Deterministic Counterfactual Replay (Features F22, F32)
            </h2>
            <p className="text-sm sm:text-base text-[#52647A] max-w-4xl leading-relaxed">
              Strict controlled experiment: Reruns the session using the <strong>exact same initial conditions and random seed</strong>, with <strong>only the selected event removed</strong>.
            </p>
          </div>

          {/* Event Picker & Trigger Button */}
          <div className="flex flex-col sm:flex-row items-center gap-3.5 shrink-0">
            <select
              value={targetEventId || ''}
              onChange={(e) => setTargetEventId(e.target.value)}
              className="w-full sm:w-80 px-4 py-3 bg-white border border-[#D7E1ED] rounded-xl text-xs sm:text-sm font-mono text-[#172033] focus:outline-none focus:border-[#0891B2] focus:ring-1 focus:ring-[#0891B2] shadow-xs"
            >
              {events.map((ev) => (
                <option key={ev.event_id} value={ev.event_id}>
                  {ev.event_id} [{ev.auth_status}] {ev.event_type} (t={ev.timestamp}s)
                </option>
              ))}
            </select>

            <button
              onClick={handleExecuteReplay}
              disabled={isReplaying || !targetEventId}
              className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-[#0891B2] hover:bg-cyan-700 disabled:bg-slate-200 disabled:text-slate-400 text-white font-bold text-sm uppercase tracking-wider flex items-center justify-center gap-2.5 shadow-sm hover:shadow transition-all cursor-pointer"
            >
              {isReplaying ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Replaying...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white text-white" />
                  Execute Counterfactual Replay
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm font-mono">
            Error: {error}
          </div>
        )}
      </div>

      {/* Replay Results Section */}
      {replayResult && (
        <div className="space-y-8">
          {/* Proof Attribution Banner (Full Width) */}
          <div
            className={`w-full rounded-2xl p-6 sm:p-7 border shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6 ${
              replayResult.effect_attribution === 'DISAPPEARED'
                ? 'bg-emerald-50 border-emerald-300'
                : replayResult.effect_attribution === 'DECREASED'
                ? 'bg-amber-50 border-amber-300'
                : 'bg-slate-50 border-[#D7E1ED]'
            }`}
          >
            <div className="space-y-2">
              <div className="flex items-center gap-3 flex-wrap">
                <span className="text-xs uppercase font-mono font-bold text-[#52647A]">
                  Causal Attribution Verdict:
                </span>
                <span
                  className={`px-3.5 py-1 rounded-full text-xs sm:text-sm font-mono font-bold tracking-wider border ${
                    replayResult.effect_attribution === 'DISAPPEARED'
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : replayResult.effect_attribution === 'DECREASED'
                      ? 'bg-amber-100 text-amber-800 border-amber-300'
                      : 'bg-slate-200 text-slate-800 border-slate-300'
                  }`}
                >
                  EFFECT {replayResult.effect_attribution}
                </span>
                {replayResult.is_causally_proven && (
                  <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-[#E6FAFF] text-[#0891B2] border border-[#0891B2]/40">
                    CAUSALITY PROVEN
                  </span>
                )}
              </div>
              <p className="text-sm sm:text-base text-[#172033] leading-relaxed font-mono">
                {replayResult.summary}
              </p>
            </div>

            <div className="text-right text-xs sm:text-sm font-mono text-[#52647A] shrink-0">
              Omitted Event: <span className="text-[#0891B2] font-bold text-sm sm:text-base">{replayResult.target_event_id}</span>
            </div>
          </div>

          {/* Delta Metrics Cards (4 Large Columns across full viewport) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 text-center space-y-2 shadow-xs">
              <span className="text-xs text-[#52647A] font-mono uppercase block font-bold">
                Peak Temperature Delta (ΔT)
              </span>
              <span className={`text-3xl lg:text-4xl font-bold font-mono ${replayResult.peak_temp_diff > 0 ? 'text-rose-600' : 'text-[#172033]'}`}>
                {replayResult.peak_temp_diff > 0 ? `-${replayResult.peak_temp_diff}` : replayResult.peak_temp_diff} °C
              </span>
              <span className="text-xs text-[#52647A] block">
                Lower in counterfactual run
              </span>
            </div>

            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 text-center space-y-2 shadow-xs">
              <span className="text-xs text-[#52647A] font-mono uppercase block font-bold">
                Peak Current Delta (ΔI)
              </span>
              <span className={`text-3xl lg:text-4xl font-bold font-mono ${replayResult.peak_current_diff > 0 ? 'text-[#0891B2]' : 'text-[#172033]'}`}>
                {replayResult.peak_current_diff > 0 ? `-${replayResult.peak_current_diff}` : replayResult.peak_current_diff} A
              </span>
              <span className="text-xs text-[#52647A] block">
                Overcurrent avoided
              </span>
            </div>

            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 text-center space-y-2 shadow-xs">
              <span className="text-xs text-[#52647A] font-mono uppercase block font-bold">
                Final SoC Delta
              </span>
              <span className="text-3xl lg:text-4xl font-bold font-mono text-blue-600">
                {replayResult.final_soc_diff > 0 ? `-${replayResult.final_soc_diff}` : replayResult.final_soc_diff} %
              </span>
              <span className="text-xs text-[#52647A] block">
                Energy differential
              </span>
            </div>

            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 text-center space-y-2 shadow-xs">
              <span className="text-xs text-[#52647A] font-mono uppercase block font-bold">
                Seed Consistency
              </span>
              <span className="text-3xl lg:text-4xl font-bold font-mono text-emerald-600">
                {replayResult.seed_used}
              </span>
              <span className="text-xs text-emerald-700 block flex items-center justify-center gap-1 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Exact Controlled Replay
              </span>
            </div>
          </div>

          {/* Overlay Comparison Charts (Full Width, 2 Columns) */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            {/* Chart 1: Temperature Overlay */}
            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-7 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-[#EDF2F7] pb-3">
                <div>
                  <h4 className="text-base font-bold text-[#172033] font-mono uppercase flex items-center gap-2">
                    <Thermometer className="w-5 h-5 text-rose-500" />
                    Temperature Overlay: Original vs Replay (°C)
                  </h4>
                  <p className="text-xs text-[#52647A] mt-0.5">
                    Solid line = with cyber event. Dashed line = without event.
                  </p>
                </div>
                <span className="text-xs font-mono text-[#52647A]">Unit: °C</span>
              </div>

              <div className="h-80 sm:h-96 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={replayResult.overlay_data} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="timestamp" stroke="#64748B" tick={{ fontSize: 12 }} />
                    <YAxis domain={['auto', 'auto']} stroke="#64748B" tick={{ fontSize: 12 }} />
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
                    <Line
                      type="monotone"
                      dataKey="original_temperature"
                      name="Original (With Cyber Event)"
                      stroke="#E11D48"
                      strokeWidth={2.8}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="replay_temperature"
                      name="Replay (Without Cyber Event)"
                      stroke="#047857"
                      strokeWidth={2.8}
                      strokeDasharray="5 3"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Current Overlay */}
            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-7 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-[#EDF2F7] pb-3">
                <div>
                  <h4 className="text-base font-bold text-[#172033] font-mono uppercase flex items-center gap-2">
                    <Zap className="w-5 h-5 text-[#0891B2]" />
                    Charging Current Overlay: Original vs Replay (A)
                  </h4>
                  <p className="text-xs text-[#52647A] mt-0.5">
                    Verifies whether overcurrent was driven exclusively by the omitted cyber event.
                  </p>
                </div>
                <span className="text-xs font-mono text-[#52647A]">Unit: Amperes</span>
              </div>

              <div className="h-80 sm:h-96 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={replayResult.overlay_data} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
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
                      label={{ value: 'Warning (120A)', fill: '#D97706', fontSize: 11 }}
                    />
                    <Line
                      type="stepAfter"
                      dataKey="original_current"
                      name="Original Current (A)"
                      stroke="#0891B2"
                      strokeWidth={2.8}
                      dot={false}
                    />
                    <Line
                      type="stepAfter"
                      dataKey="replay_current"
                      name="Replay Current (A)"
                      stroke="#B45309"
                      strokeWidth={2.4}
                      strokeDasharray="5 3"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Scientific Disclaimer (Feature F48) */}
          <div className="w-full p-6 rounded-2xl bg-[#F8FAFC] border border-[#D7E1ED] flex items-start gap-4">
            <HelpCircle className="w-6 h-6 text-[#52647A] shrink-0 mt-0.5" />
            <div className="space-y-1.5">
              <span className="text-sm font-mono font-bold text-[#172033] block">
                Scientific Limitations & Honesty Policy (Feature F48):
              </span>
              <p className="text-xs sm:text-sm text-[#52647A] leading-relaxed">
                {replayResult.limitations}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
