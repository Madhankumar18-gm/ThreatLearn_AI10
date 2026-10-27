import React, { useState, useEffect } from 'react';
import {
  Search,
  Play,
  Clock,
  Layers,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Shield,
  Activity,
  Download
} from 'lucide-react';
import { api } from '../services/api';

const FAMILIES = [
  'All',
  'Normal operation',
  'Attack',
  'Sensor fault',
  'Benign high-power event',
  'Delayed attack',
  'Masked attack',
  'Fleet attack',
  'Defended attack',
  'Custom'
];

const SIMULATION_STAGES = [
  'Initializing scenario & parameters',
  'Running digital twin state machine',
  'Generating physics telemetry',
  'Analysing dependency paths',
  'Evaluating cyber-physical impact chain',
  'Rendering evidence & proof'
];

export default function ScenarioLab({ onRunSimulation, isSimulating }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedFamily, setSelectedFamily] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [customSeed, setCustomSeed] = useState('');
  const [loading, setLoading] = useState(true);
  const [currentStageIdx, setCurrentStageIdx] = useState(0);

  useEffect(() => {
    async function loadScenarios() {
      try {
        const data = await api.getScenarios();
        setScenarios(data);
        if (data.length > 0) {
          setSelectedScenario(data[0]);
          setCustomSeed(data[0].default_seed);
        }
      } catch (err) {
        console.error('Failed to load scenarios', err);
      } finally {
        setLoading(false);
      }
    }
    loadScenarios();
  }, []);

  // Multi-stage progress indicator animation during simulation
  useEffect(() => {
    let interval;
    if (isSimulating) {
      setCurrentStageIdx(0);
      interval = setInterval(() => {
        setCurrentStageIdx((prev) => (prev < SIMULATION_STAGES.length - 1 ? prev + 1 : prev));
      }, 300);
    } else {
      setCurrentStageIdx(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isSimulating]);

  const handleSelectScenario = (sc) => {
    setSelectedScenario(sc);
    setCustomSeed(sc.default_seed);
  };

  const filteredScenarios = scenarios.filter((s) => {
    const matchesFamily = selectedFamily === 'All' || s.family === selectedFamily;
    const matchesSearch =
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.scenario_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFamily && matchesSearch;
  });

  const handleRun = () => {
    if (!selectedScenario) return;
    const seed = customSeed !== '' ? parseInt(customSeed, 10) : selectedScenario.default_seed;
    onRunSimulation(selectedScenario.scenario_id, seed);
  };

  const getFamilyBadge = (family) => {
    if (family === 'Attack' || family === 'Delayed attack' || family === 'Masked attack') {
      return 'bg-red-50 text-red-700 border-red-200';
    }
    if (family === 'Sensor fault') {
      return 'bg-amber-50 text-amber-700 border-amber-200';
    }
    if (family === 'Defended attack') {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
    return 'bg-blue-50 text-blue-700 border-blue-200';
  };

  return (
    <div className="w-full space-y-8 pb-12 animate-page-enter">
      {/* Header and Filter Row (Full Viewport Width) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h2 className="text-3xl sm:text-4xl font-bold font-mono text-[#172033] flex items-center gap-3">
            <Layers className="w-8 h-8 text-[#0891B2]" />
            Deterministic Scenario Library (Feature F01)
          </h2>
          <p className="text-sm sm:text-base text-[#52647A] mt-1.5">
            28 benchmark scenarios spanning 8 operational, fault, and adversarial families. Select any scenario to test or replay.
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-96">
          <Search className="w-5 h-5 text-[#52647A] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search scenario ID or title..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-3 bg-white border border-[#D7E1ED] rounded-xl text-sm sm:text-base text-[#172033] placeholder-[#94A3B8] focus:outline-none focus:border-[#0891B2] focus:ring-1 focus:ring-[#0891B2] font-mono shadow-xs"
          />
        </div>
      </div>

      {/* Family Filter Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
        {FAMILIES.map((fam) => (
          <button
            key={fam}
            onClick={() => setSelectedFamily(fam)}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold whitespace-nowrap transition-all duration-150 cursor-pointer shadow-2xs ${
              selectedFamily === fam
                ? 'bg-[#0891B2] text-white shadow-sm'
                : 'bg-white hover:bg-slate-50 text-[#52647A] hover:text-[#172033] border border-[#D7E1ED]'
            }`}
          >
            {fam}
          </button>
        ))}
      </div>

      {/* Multi-Stage Simulation Progress Banner */}
      {isSimulating && (
        <div className="w-full bg-[#E6FAFF] border-2 border-[#0891B2] rounded-2xl p-6 shadow-md animate-page-enter">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-[#0891B2]/20 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 border-3 border-[#0891B2] border-t-transparent rounded-full animate-spin"></div>
              <div>
                <span className="font-mono text-base font-bold text-[#0891B2] uppercase block">
                  Executing Controlled Simulation
                </span>
                <span className="text-sm font-semibold text-[#172033]">
                  Scenario: {selectedScenario?.scenario_id} — {selectedScenario?.name}
                </span>
              </div>
            </div>
            <span className="text-xs font-mono font-bold text-[#0891B2] bg-white px-3 py-1 rounded-md border border-[#0891B2]/30">
              Deterministic Seed: {customSeed || selectedScenario?.default_seed}
            </span>
          </div>

          {/* 6 Simulation Stages */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-4">
            {SIMULATION_STAGES.map((stage, idx) => {
              const isDone = idx < currentStageIdx;
              const isCurrent = idx === currentStageIdx;
              return (
                <div
                  key={stage}
                  className={`p-3 rounded-xl border text-xs font-mono transition-all ${
                    isDone
                      ? 'bg-emerald-50 border-emerald-300 text-emerald-800 font-semibold'
                      : isCurrent
                      ? 'bg-white border-[#0891B2] text-[#0891B2] font-bold shadow-xs'
                      : 'bg-white/50 border-[#D7E1ED] text-[#94A3B8]'
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    {isDone ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    ) : isCurrent ? (
                      <span className="w-2.5 h-2.5 rounded-full bg-[#0891B2] animate-ping shrink-0" />
                    ) : (
                      <span className="w-2.5 h-2.5 rounded-full bg-slate-300 shrink-0" />
                    )}
                    <span className="text-[10px] uppercase">Step {idx + 1}</span>
                  </div>
                  <div className="leading-tight">{stage}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Grid: Scenario Selector on Left (5 cols) & Deep Details on Right (7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: List of Scenarios */}
        <div className="lg:col-span-5 space-y-3.5 max-h-[820px] overflow-y-auto pr-1">
          {loading ? (
            <div className="text-center py-16 text-sm font-mono text-[#52647A] bg-white rounded-2xl border border-[#D7E1ED] p-8">
              Loading scenario repository from backend...
            </div>
          ) : filteredScenarios.length === 0 ? (
            <div className="text-center py-16 text-sm font-mono text-[#52647A] bg-white rounded-2xl border border-[#D7E1ED] p-8">
              No scenarios match "{searchQuery}" in {selectedFamily} family.
            </div>
          ) : (
            filteredScenarios.map((sc) => {
              const isSelected = selectedScenario?.scenario_id === sc.scenario_id;
              return (
                <div
                  key={sc.scenario_id}
                  onClick={() => handleSelectScenario(sc)}
                  className={`p-5 rounded-2xl border transition-all cursor-pointer shadow-xs ${
                    isSelected
                      ? 'bg-[#E6FAFF] border-[#0891B2] shadow-sm transform translate-x-1'
                      : 'bg-white hover:bg-slate-50/90 border-[#D7E1ED]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="font-mono text-xs font-bold text-[#0891B2]">
                      {sc.scenario_id}
                    </span>
                    <span className={`px-2.5 py-0.5 rounded-md text-xs font-mono font-bold border ${getFamilyBadge(sc.family)}`}>
                      {sc.family}
                    </span>
                  </div>

                  <h4 className="text-base sm:text-lg font-bold text-[#172033] leading-snug">
                    {sc.name}
                  </h4>

                  <p className="text-xs sm:text-sm text-[#52647A] line-clamp-2 mt-1.5 leading-relaxed">
                    {sc.description}
                  </p>

                  <div className="flex items-center justify-between text-xs text-[#52647A] font-mono mt-3 pt-2.5 border-t border-[#EDF2F7]">
                    <span>Duration: <strong className="text-[#172033]">{sc.duration_seconds}s</strong></span>
                    <span>Default Seed: <strong className="text-[#172033]">{sc.default_seed}</strong></span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Column: Selected Scenario Deep Inspector & Execution Controls */}
        <div className="lg:col-span-7 bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-8 space-y-6 shadow-xs">
          {selectedScenario ? (
            <>
              {/* Header */}
              <div className="space-y-2 border-b border-[#EDF2F7] pb-5">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-mono text-xs sm:text-sm font-bold text-[#0891B2] bg-[#E6FAFF] px-3 py-1 rounded-md border border-[#0891B2]/30">
                    {selectedScenario.scenario_id}
                  </span>
                  <span className={`px-3 py-1 rounded-md text-xs sm:text-sm font-mono font-bold border ${getFamilyBadge(selectedScenario.family)}`}>
                    {selectedScenario.family} Family
                  </span>
                  <span className="text-xs sm:text-sm font-mono text-[#52647A]">
                    Duration: <strong className="text-[#172033]">{selectedScenario.duration_seconds}s</strong>
                  </span>
                </div>

                <h3 className="text-2xl sm:text-3xl font-bold font-mono text-[#172033]">
                  {selectedScenario.name}
                </h3>

                <p className="text-sm sm:text-base text-[#52647A] leading-relaxed">
                  {selectedScenario.description}
                </p>
              </div>

              {/* Execution Controls: Seed Selection + Run Simulation Button */}
              <div className="p-5 rounded-2xl bg-[#F8FAFC] border border-[#D7E1ED] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs sm:text-sm font-bold font-mono text-[#172033] uppercase tracking-wide block">
                    Random Seed (Feature F03 Determinism):
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={customSeed}
                      onChange={(e) => setCustomSeed(e.target.value)}
                      placeholder={selectedScenario.default_seed.toString()}
                      className="w-36 px-3.5 py-2.5 bg-white border border-[#D7E1ED] rounded-xl text-base font-mono font-bold text-[#172033] focus:outline-none focus:border-[#0891B2] shadow-2xs"
                    />
                    <button
                      onClick={() => setCustomSeed(selectedScenario.default_seed)}
                      className="px-3 py-2 text-xs font-mono text-[#52647A] hover:text-[#172033] bg-white border border-[#D7E1ED] rounded-xl hover:bg-slate-100 transition-colors shadow-2xs"
                      title="Reset to scenario default seed"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  </div>
                  <span className="text-xs text-[#52647A]">
                    Identical seed guarantees bitwise identical floating-point telemetry output.
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={async () => {
                      try {
                        const exportData = await api.exportScenario(selectedScenario.scenario_id);
                        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `${selectedScenario.scenario_id}.json`;
                        a.click();
                        URL.revokeObjectURL(url);
                      } catch (err) {
                        alert(`Export failed: ${err.message}`);
                      }
                    }}
                    className="px-4 py-4 rounded-xl bg-white border border-[#D7E1ED] hover:bg-slate-100 text-[#172033] font-bold text-sm flex items-center justify-center gap-2 shadow-2xs cursor-pointer transition-all shrink-0"
                    title="Export Scenario to versioned JSON (F05)"
                  >
                    <Download className="w-4 h-4 text-[#0891B2]" /> Export JSON
                  </button>

                  <button
                    onClick={handleRun}
                    disabled={isSimulating}
                    className="px-8 py-4 rounded-xl bg-[#0891B2] hover:bg-cyan-700 disabled:bg-slate-300 disabled:text-slate-500 text-white font-bold text-base uppercase tracking-wider flex items-center justify-center gap-3 shadow-sm hover:shadow-md cursor-pointer transition-all shrink-0"
                  >
                    <Play className="w-5 h-5 fill-white" />
                    {isSimulating ? 'Simulating...' : 'Run Simulation'}
                  </button>
                </div>
              </div>

              {/* Expected Effects & Limitations */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-white border border-[#D7E1ED] space-y-1.5">
                  <span className="text-xs font-mono font-bold text-[#0891B2] block uppercase tracking-wide">
                    Expected Physical Effects:
                  </span>
                  <p className="text-xs sm:text-sm text-[#172033] leading-relaxed">
                    {selectedScenario.expected_effects}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-white border border-[#D7E1ED] space-y-1.5">
                  <span className="text-xs font-mono font-bold text-amber-700 block uppercase tracking-wide flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Safety & Limitations Notes:
                  </span>
                  <p className="text-xs sm:text-sm text-[#52647A] leading-relaxed">
                    {selectedScenario.safety_limitations}
                  </p>
                </div>
              </div>

              {/* Scheduled Simulated Cyber/Fault Events Table */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm sm:text-base font-bold font-mono text-[#172033] flex items-center gap-2">
                    <Clock className="w-4 h-4 text-[#0891B2]" />
                    Scheduled Simulated Events ({selectedScenario.events?.length || 0})
                  </h4>
                  <span className="text-xs font-mono text-[#52647A]">OCPP & Physical Control Protocol</span>
                </div>

                <div className="overflow-x-auto border border-[#D7E1ED] rounded-xl">
                  <table className="w-full text-left text-xs sm:text-sm font-mono text-[#172033]">
                    <thead className="bg-[#F8FAFC] text-[#52647A] uppercase text-xs border-b border-[#D7E1ED]">
                      <tr>
                        <th className="py-3 px-3.5">Time</th>
                        <th className="py-3 px-3.5">Event ID</th>
                        <th className="py-3 px-3.5">Component</th>
                        <th className="py-3 px-3.5">Event Type</th>
                        <th className="py-3 px-3.5">Source</th>
                        <th className="py-3 px-3.5">Auth Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#D7E1ED]">
                      {selectedScenario.events?.map((ev) => {
                        const isUnauthorized = ev.auth_status === 'unauthorized' || ev.auth_status === 'spoofed';
                        return (
                          <tr key={ev.event_id} className="hover:bg-slate-50 transition-colors">
                            <td className="py-3 px-3.5 font-bold text-[#0891B2]">t={ev.timestamp}s</td>
                            <td className="py-3 px-3.5 font-bold text-[#172033]">{ev.event_id}</td>
                            <td className="py-3 px-3.5 text-[#52647A]">{ev.component_id}</td>
                            <td className="py-3 px-3.5 font-sans font-medium text-[#172033]">{ev.event_type}</td>
                            <td className="py-3 px-3.5 text-[#52647A]">{ev.source}</td>
                            <td className="py-3 px-3.5">
                              {isUnauthorized ? (
                                <span className="px-2 py-0.5 rounded bg-red-100 text-red-800 border border-red-200 text-xs font-bold">
                                  {ev.auth_status}
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold">
                                  {ev.auth_status}
                                </span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-24 text-sm font-mono text-[#52647A]">
              Select a scenario from the library on the left to inspect its parameters and run simulation.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
