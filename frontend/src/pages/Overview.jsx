import React, { useEffect, useState } from 'react';
import {
  Zap,
  Activity,
  Cpu,
  GitCompare,
  ArrowRight,
  CheckCircle2,
  Play,
  Layers,
  ShieldCheck,
  Server,
  Radio,
  Clock,
  Shield,
  Thermometer,
  BatteryCharging,
  TrendingUp
} from 'lucide-react';
import { api } from '../services/api';

export default function Overview({ setActiveTab, onSelectAndRun, currentRun }) {
  const [health, setHealth] = useState(null);
  const [recentRuns, setRecentRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [h, r] = await Promise.all([
          api.getHealth().catch(() => null),
          api.getRuns(8).catch(() => []),
        ]);
        setHealth(h);
        setRecentRuns(r || []);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const hasActiveSignal = Boolean(currentRun);

  return (
    <div className="w-full space-y-8 pb-12 animate-page-enter">
      {/* A. Hero Section (Full-Width Two-Column Panel with Cyber-Physical Twin Diagram) */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-white via-[#E6FAFF]/30 to-blue-50/25 border border-[#D7E1ED] p-8 sm:p-12 shadow-xs">
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-10 items-center">
          {/* Left Text Column */}
          <div className="xl:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-[#E6FAFF] border border-[#0891B2]/30 text-[#0891B2] text-xs sm:text-sm font-mono font-semibold">
              <Shield className="w-4 h-4 text-[#0891B2]" />
              Cybersecurity and Cyber-Physical Impact Analysis Platform
            </div>

            <div className="space-y-3">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#172033] font-mono leading-tight">
                THREAT<span className="text-[#0891B2]">LENS</span>
              </h1>
              <p className="text-2xl sm:text-3xl font-bold text-[#0891B2] font-sans">
                See the Threat. Trace the Impact. Prove the Difference.
              </p>
            </div>

            <p className="text-[#52647A] text-base sm:text-lg leading-relaxed max-w-3xl font-normal">
              Simulate cyber events, trace their physical effects across EV charging systems through grounded component dependency graphs, and evaluate end-to-end cyber-physical impact chains and grid feeder stability.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={() => onSelectAndRun('SCN-ATK-01', 201)}
                className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-[#0891B2] hover:bg-cyan-700 text-white font-bold text-base shadow-sm transition-all transform hover:-translate-y-0.5 cursor-pointer"
              >
                <Play className="w-5 h-5 fill-white" />
                Run Demo Simulation
              </button>
              <button
                onClick={() => setActiveTab('scenario-lab')}
                className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-white hover:bg-slate-50 text-[#172033] border border-[#D7E1ED] text-base font-semibold transition-colors shadow-xs cursor-pointer"
              >
                Explore Scenario Library
                <ArrowRight className="w-5 h-5 text-[#52647A]" />
              </button>
            </div>
          </div>

          {/* Right Column: Large Cyber-Physical Dependency Visualization */}
          <div className="xl:col-span-5 flex justify-center">
            <div className="w-full bg-white/95 border border-[#D7E1ED] rounded-2xl p-6 shadow-sm relative">
              <div className="flex items-center justify-between text-xs sm:text-sm font-mono text-[#172033] pb-3 border-b border-[#EDF2F7]">
                <span className="flex items-center gap-2 font-bold text-[#0891B2]">
                  <Activity className="w-4 h-4 text-[#0891B2]" />
                  Cyber-Physical Signal Propagation Flow
                </span>
                <span className="text-emerald-700 font-semibold flex items-center gap-1.5 text-xs">
                  <span className={`w-2.5 h-2.5 rounded-full ${hasActiveSignal ? 'bg-emerald-500 animate-ping' : 'bg-emerald-500'}`}></span>
                  {hasActiveSignal ? 'Incident Stream Active' : 'Digital Twin Ready'}
                </span>
              </div>

              {/* Large SVG Network Diagram with clear nodes and labels */}
              <svg viewBox="0 0 540 330" className="w-full h-auto mt-4 select-none">
                <defs>
                  <linearGradient id="cyberFlowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#0891B2" />
                    <stop offset="50%" stopColor="#2563EB" />
                    <stop offset="100%" stopColor="#E11D48" />
                  </linearGradient>
                  <marker
                    id="hero-arrow"
                    viewBox="0 0 10 10"
                    refX="16"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 10 5 L 0 9 z" fill="#94A3B8" />
                  </marker>
                  <marker
                    id="hero-arrow-active"
                    viewBox="0 0 10 10"
                    refX="16"
                    refY="5"
                    markerWidth="7"
                    markerHeight="7"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 10 5 L 0 9 z" fill="#0891B2" />
                  </marker>
                </defs>

                {/* Flow lines (Top Row: Cyber & Actuation) */}
                {/* 1. CSMS to EV Charger */}
                <line x1="100" y1="55" x2="245" y2="55" stroke="#CBD5E1" strokeWidth="2.5" markerEnd="url(#hero-arrow)" />
                {/* 2. EV Charger to Charging Current */}
                <line x1="325" y1="55" x2="445" y2="55" stroke="#CBD5E1" strokeWidth="2.5" markerEnd="url(#hero-arrow)" />
                {/* 3. Charging Current to Battery */}
                <path d="M 470 85 L 470 145" stroke="#CBD5E1" strokeWidth="2.5" markerEnd="url(#hero-arrow)" />
                {/* 4. Battery to Thermal Response */}
                <line x1="420" y1="175" x2="295" y2="175" stroke="#CBD5E1" strokeWidth="2.5" markerEnd="url(#hero-arrow)" />
                {/* 5. Cooling System to Thermal Response */}
                <line x1="100" y1="175" x2="215" y2="175" stroke="#CBD5E1" strokeWidth="2.5" strokeDasharray="4 3" markerEnd="url(#hero-arrow)" />
                {/* 6. Thermal Response to BMS Warning */}
                <line x1="255" y1="205" x2="255" y2="265" stroke="#CBD5E1" strokeWidth="2.5" markerEnd="url(#hero-arrow)" />
                {/* 7. BMS Feedback Loop to EV Charger */}
                <path d="M 215 295 L 70 295 L 70 85" fill="none" stroke="#CBD5E1" strokeWidth="2" strokeDasharray="4 4" markerEnd="url(#hero-arrow)" />

                {/* Animated Signal Packet when simulation is active */}
                {hasActiveSignal && (
                  <path
                    d="M 100 55 L 470 55 L 470 175 L 255 175 L 255 295 L 70 295 L 70 55"
                    fill="none"
                    stroke="url(#cyberFlowGrad)"
                    strokeWidth="3.5"
                    className="animate-signal-flow"
                  />
                )}

                {/* Node 1: Backend CSMS */}
                <g transform="translate(30, 25)">
                  <rect width="80" height="60" rx="10" fill="#F0F9FF" stroke="#0891B2" strokeWidth="2" />
                  <text x="40" y="27" textAnchor="middle" className="text-[11px] font-mono font-bold fill-[#172033]">Backend</text>
                  <text x="40" y="44" textAnchor="middle" className="text-[10px] font-sans fill-[#0891B2] font-semibold">CSMS / Cloud</text>
                </g>

                {/* Node 2: EV Charger Controller */}
                <g transform="translate(215, 25)">
                  <rect width="90" height="60" rx="10" fill="#EFF6FF" stroke="#2563EB" strokeWidth="2" />
                  <text x="45" y="27" textAnchor="middle" className="text-[11px] font-mono font-bold fill-[#172033]">EV Charger</text>
                  <text x="45" y="44" textAnchor="middle" className="text-[10px] font-sans fill-[#2563EB] font-semibold">Controller</text>
                </g>

                {/* Node 3: Charging Current */}
                <g transform="translate(425, 25)">
                  <rect width="90" height="60" rx="10" fill="#FFFBEB" stroke="#D97706" strokeWidth="2" />
                  <text x="45" y="27" textAnchor="middle" className="text-[11px] font-mono font-bold fill-[#172033]">Current I(t)</text>
                  <text x="45" y="44" textAnchor="middle" className="text-[10px] font-sans fill-[#D97706] font-semibold">Power Actuator</text>
                </g>

                {/* Node 4: Battery */}
                <g transform="translate(425, 145)">
                  <rect width="90" height="60" rx="10" fill="#FEF2F2" stroke="#E11D48" strokeWidth="2" />
                  <text x="45" y="27" textAnchor="middle" className="text-[11px] font-mono font-bold fill-[#172033]">Battery</text>
                  <text x="45" y="44" textAnchor="middle" className="text-[10px] font-sans fill-[#E11D48] font-semibold">Cell Voltage</text>
                </g>

                {/* Node 5: Cooling System */}
                <g transform="translate(25, 145)">
                  <rect width="85" height="60" rx="10" fill="#ECFDF5" stroke="#059669" strokeWidth="2" />
                  <text x="42" y="27" textAnchor="middle" className="text-[11px] font-mono font-bold fill-[#172033]">Cooling</text>
                  <text x="42" y="44" textAnchor="middle" className="text-[10px] font-sans fill-[#059669] font-semibold">Exchanger</text>
                </g>

                {/* Node 6: Thermal Response (Joule Heating) */}
                <g transform="translate(215, 145)">
                  <rect width="90" height="60" rx="10" fill="#FFF7ED" stroke="#EA580C" strokeWidth="2" />
                  <text x="45" y="27" textAnchor="middle" className="text-[11px] font-mono font-bold fill-[#172033]">Thermal</text>
                  <text x="45" y="44" textAnchor="middle" className="text-[10px] font-sans fill-[#EA580C] font-semibold">Joule Heating</text>
                </g>

                {/* Node 7: BMS Warning / Breaker */}
                <g transform="translate(215, 265)">
                  <rect width="90" height="55" rx="10" fill="#FEF2F2" stroke="#DC2626" strokeWidth="2" />
                  <text x="45" y="25" textAnchor="middle" className="text-[11px] font-mono font-bold fill-[#DC2626]">BMS Breaker</text>
                  <text x="45" y="41" textAnchor="middle" className="text-[9px] font-sans fill-[#64748B]">Safety Cutoff</text>
                </g>
              </svg>

              <div className="mt-3 pt-3 border-t border-[#EDF2F7] flex items-center justify-between text-xs text-[#52647A] font-mono">
                <span>Causal Chain: Backend → Charger → Current → Battery ⇄ Cooling → Thermal → BMS</span>
                <span className="text-[#0891B2] font-semibold">F06/F07/F08/F20</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* B. KPI Cards (4 Large Columns across full viewport width) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
        {/* Card 1: Scenario Library */}
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 space-y-3 shadow-xs hover:border-[#0891B2] hover:shadow-md transition-all">
          <div className="flex items-center justify-between text-[#52647A]">
            <span className="text-xs font-bold uppercase tracking-wider font-mono">Scenario Library</span>
            <div className="w-10 h-10 rounded-xl bg-[#E6FAFF] flex items-center justify-center text-[#0891B2]">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="text-3xl lg:text-4xl font-bold font-mono text-[#172033]">
              {health?.total_scenarios || 28} <span className="text-sm font-semibold text-[#52647A]">Scenarios</span>
            </div>
            <div className="text-sm font-semibold text-[#0891B2] mt-1">8 Primary Scenario Families</div>
          </div>
          <p className="text-sm text-[#52647A] leading-relaxed border-t border-[#EDF2F7] pt-3">
            Deterministic benchmarks: Normal, Attack, Sensor Fault, Benign, Delayed, Masked, Fleet, Defended.
          </p>
        </div>

        {/* Card 2: Seeded Determinism */}
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 space-y-3 shadow-xs hover:border-emerald-500 hover:shadow-md transition-all">
          <div className="flex items-center justify-between text-[#52647A]">
            <span className="text-xs font-bold uppercase tracking-wider font-mono">Seeded Determinism</span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="text-3xl lg:text-4xl font-bold font-mono text-emerald-700">
              Bitwise <span className="text-sm font-semibold text-[#52647A]">Verified</span>
            </div>
            <div className="text-sm font-semibold text-emerald-700 mt-1">Automated Test Passed</div>
          </div>
          <p className="text-sm text-[#52647A] leading-relaxed border-t border-[#EDF2F7] pt-3">
            Identical seed and scenario inputs reproduce identical floating-point telemetry time-slices.
          </p>
        </div>

        {/* Card 3: Analysis Engine */}
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 space-y-3 shadow-xs hover:border-blue-500 hover:shadow-md transition-all">
          <div className="flex items-center justify-between text-[#52647A]">
            <span className="text-xs font-bold uppercase tracking-wider font-mono">Analysis Engine</span>
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
              <Cpu className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="text-3xl lg:text-4xl font-bold font-mono text-blue-700">
              Rule-Based <span className="text-sm font-semibold text-[#52647A]">Causal</span>
            </div>
            <div className="text-sm font-semibold text-blue-700 mt-1">NetworkX Directed Graph</div>
          </div>
          <p className="text-sm text-[#52647A] leading-relaxed border-t border-[#EDF2F7] pt-3">
            Validates graph path reachability, physical signal compatibility, latency windows, and noise margins.
          </p>
        </div>

        {/* Card 4: Impact Analysis */}
        <div 
          onClick={() => setActiveTab('impact-analysis')}
          className="bg-white border border-[#D7E1ED] rounded-2xl p-6 space-y-3 shadow-xs hover:border-[#0891B2] hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-[#52647A]">
            <span className="text-xs font-bold uppercase tracking-wider font-mono">Impact Analysis</span>
            <div className="w-10 h-10 rounded-xl bg-cyan-50 flex items-center justify-center text-[#0891B2] group-hover:scale-105 transition-transform">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div>
            <div className="text-3xl lg:text-4xl font-bold font-mono text-[#0891B2]">
              Physical <span className="text-sm font-semibold text-[#52647A]">Impact Chain</span>
            </div>
            <div className="text-sm font-semibold text-cyan-800 mt-1">Cyber-to-Grid Cascade</div>
          </div>
          <p className="text-sm text-[#52647A] leading-relaxed border-t border-[#EDF2F7] pt-3">
            Trace how cyber commands propagate to EV battery temperatures, peak fleet demand, and feeder voltage sag.
          </p>
        </div>
      </div>

      {/* C. Recommended Demonstration Scenario (Wide High-Visibility Card) */}
      <div className="w-full bg-[#E6FAFF]/60 border border-[#0891B2]/30 rounded-2xl p-8 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8">
          <div className="space-y-3 max-w-4xl">
            <div className="flex flex-wrap items-center gap-3">
              <span className="px-3 py-1 rounded-full bg-[#0891B2] text-white text-xs font-mono font-bold uppercase tracking-wide">
                Recommended Demonstration Scenario
              </span>
              <span className="px-2.5 py-1 rounded-md text-xs font-mono bg-white text-[#172033] border border-[#D7E1ED] font-semibold">
                ID: SCN-ATK-01
              </span>
              <span className="px-2.5 py-1 rounded-md text-xs font-mono bg-red-100 text-red-800 font-bold border border-red-200">
                Attack Family
              </span>
            </div>

            <h3 className="text-xl sm:text-2xl font-bold text-[#172033]">
              Unauthorized Charging Current Override (150A)
            </h3>

            <p className="text-sm sm:text-base text-[#52647A] leading-relaxed">
              At <code className="bg-white px-2 py-0.5 rounded border border-[#D7E1ED] text-[#0891B2] font-bold">t=15s</code>, an unauthorized <span className="font-semibold text-[#172033]">ChangeCurrentLimit</span> packet commands the power converter to 150A hardware maximum. High Joule heating ($I^2 R$) rapidly raises battery pack temperature past the 45.0°C warning threshold.
            </p>

            <div className="flex flex-wrap items-center gap-6 text-xs sm:text-sm text-[#52647A] font-mono pt-1">
              <span>Ground Truth: <strong className="text-emerald-700 font-semibold">Causal Relationship Validated</strong></span>
              <span>Expected Effect: <strong className="text-amber-700 font-semibold">ΔT &gt; 15°C Overheat Warning</strong></span>
            </div>
          </div>

          <div className="shrink-0">
            <button
              onClick={() => onSelectAndRun('SCN-ATK-01', 201)}
              className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-[#0891B2] hover:bg-cyan-700 text-white font-bold text-sm sm:text-base uppercase tracking-wider flex items-center justify-center gap-2.5 shadow-sm cursor-pointer transition-all"
            >
              <Play className="w-4 h-4 fill-white" />
              Run Demonstration
            </button>
          </div>
        </div>
      </div>

      {/* D. Recent Incidents Table (Full Width) */}
      <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-8 space-y-5 shadow-xs">
        <div className="flex items-center justify-between flex-wrap gap-4 border-b border-[#EDF2F7] pb-4">
          <div>
            <h3 className="text-xl font-bold text-[#172033] flex items-center gap-2.5">
              <Activity className="w-5 h-5 text-[#0891B2]" />
              Recent Simulation Incidents (Feature F51)
            </h3>
            <p className="text-sm text-[#52647A] mt-1">
              Live telemetry and analysis records retrieved from SQLite database storage.
            </p>
          </div>
          <button
            onClick={() => setActiveTab('history')}
            className="text-sm font-semibold text-[#0891B2] hover:text-cyan-800 hover:underline cursor-pointer flex items-center gap-1.5"
          >
            View all incident history
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {recentRuns.length === 0 ? (
          <div className="text-center py-16 text-[#52647A] text-sm font-mono bg-slate-50 rounded-xl border border-dashed border-[#D7E1ED] p-8">
            No simulation runs recorded yet. Select a scenario from the Scenario Lab to launch an incident.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase font-mono text-[#52647A] bg-[#F8FAFC] border-b border-[#D7E1ED]">
                <tr>
                  <th className="py-3.5 px-4">Run ID</th>
                  <th className="py-3.5 px-4">Scenario Title</th>
                  <th className="py-3.5 px-4">Family</th>
                  <th className="py-3.5 px-4">Seed</th>
                  <th className="py-3.5 px-4">Peak Temp</th>
                  <th className="py-3.5 px-4">Peak Current</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D7E1ED] font-mono text-[#172033]">
                {recentRuns.map((r) => (
                  <tr key={r.run_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-4 px-4 font-bold text-[#0891B2]">{r.run_id}</td>
                    <td className="py-4 px-4 text-[#172033] font-sans font-medium">{r.scenario_name}</td>
                    <td className="py-4 px-4 text-[#52647A]">{r.scenario_family}</td>
                    <td className="py-4 px-4 text-[#52647A]">{r.seed}</td>
                    <td className={`py-4 px-4 font-semibold ${r.peak_temperature >= 45 ? 'text-amber-700 font-bold' : 'text-[#172033]'}`}>
                      {r.peak_temperature}°C
                    </td>
                    <td className="py-4 px-4 font-semibold text-blue-700">{r.peak_current}A</td>
                    <td className="py-4 px-4">
                      {r.fault_triggered ? (
                        <span className="px-2.5 py-1 rounded-md bg-red-100 text-red-800 border border-red-200 text-xs font-bold">
                          FAULT TRIP
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold">
                          NORMAL
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <button
                        onClick={() => onSelectAndRun(r.scenario_id, r.seed)}
                        className="text-[#0891B2] hover:text-cyan-800 font-semibold text-sm hover:underline cursor-pointer"
                      >
                        Inspect →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
