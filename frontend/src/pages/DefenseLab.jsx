import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ShieldCheck, ShieldAlert, ArrowRight, Zap, Thermometer, CheckCircle2, AlertTriangle, Layers, Play } from 'lucide-react';

export default function DefenseLab({ scenarios = [] }) {
  const [selectedScenarioId, setSelectedScenarioId] = useState('SCN-ATK-01');
  const [seed, setSeed] = useState(201);

  // Defense toggles
  const [authValidation, setAuthValidation] = useState(true);
  const [commandWhitelist, setCommandWhitelist] = useState(false);
  const [currentCap, setCurrentCap] = useState(true);
  const [currentCapVal, setCurrentCapVal] = useState(100.0);
  const [rateLimiting, setRateLimiting] = useState(true);
  const [sensorCrosscheck, setSensorCrosscheck] = useState(false);
  const [thermalLockout, setThermalLockout] = useState(false);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Default scenario selection
  useEffect(() => {
    if (scenarios.length > 0 && !selectedScenarioId) {
      const atk = scenarios.find((s) => s.family === 'Attack') || scenarios[0];
      setSelectedScenarioId(atk.scenario_id);
    }
  }, [scenarios, selectedScenarioId]);

  const handleCompare = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const payload = {
        scenario_id: selectedScenarioId,
        seed: parseInt(seed, 10),
        defenses: {
          auth_validation_enabled: authValidation,
          command_whitelist_enabled: commandWhitelist,
          current_cap_enabled: currentCap,
          current_cap_value: parseFloat(currentCapVal),
          rate_limiting_enabled: rateLimiting,
          sensor_crosscheck_enabled: sensorCrosscheck,
          thermal_lockout_enabled: thermalLockout
        }
      };
      const res = await api.compareDefenses(payload);
      setResult(res);
    } catch (err) {
      setErrorMsg(err.message || 'Defense comparison failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full space-y-8 pb-12 animate-page-enter">
      {/* Top Banner */}
      <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-8 shadow-xs flex flex-wrap items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-[#0891B2]" />
            <h1 className="text-xl sm:text-2xl font-bold text-[#172033] tracking-tight">
              Defense Lab & Comparative Effectiveness (F39, F40)
            </h1>
          </div>
          <p className="text-sm text-[#52647A] mt-1 max-w-2xl leading-relaxed">
            Configure simulated cyber-physical mitigations and evaluate deterministic before/after comparative outcomes across identical scenarios and seeds.
          </p>
        </div>

        <button
          onClick={handleCompare}
          disabled={loading}
          className="px-6 py-3 bg-[#0891B2] hover:bg-cyan-700 text-white font-bold text-xs uppercase tracking-wider rounded-xl flex items-center gap-2 cursor-pointer shadow-sm transition-all"
        >
          <Play className="w-4 h-4 fill-white" />
          {loading ? 'Simulating Comparison...' : 'Run Comparative Analysis'}
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Scenario Selection */}
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-[#172033] uppercase tracking-wider border-b border-[#E2E8F0] pb-2">
            Target Scenario
          </h3>
          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-[#172033] block mb-1">Select Attack Scenario</label>
              <select
                value={selectedScenarioId}
                onChange={(e) => setSelectedScenarioId(e.target.value)}
                className="w-full px-3 py-2 bg-[#F8FAFC] border border-[#D7E1ED] rounded-lg font-mono text-[#172033]"
              >
                {scenarios.map((s) => (
                  <option key={s.scenario_id} value={s.scenario_id}>
                    {s.scenario_id} &mdash; {s.name} ({s.family})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="font-semibold text-[#172033] block mb-1">RNG Seed</label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                className="w-full px-3 py-2 bg-[#F8FAFC] border border-[#D7E1ED] rounded-lg font-mono text-[#172033]"
              />
            </div>
          </div>
        </div>

        {/* Defense Toggles (F39) */}
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4 lg:col-span-2">
          <h3 className="text-sm font-bold text-[#172033] uppercase tracking-wider border-b border-[#E2E8F0] pb-2">
            Active Mitigation Toggles
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <label className="flex items-start gap-3 p-3.5 rounded-xl border border-[#D7E1ED] bg-[#F8FAFC] cursor-pointer hover:bg-slate-100 transition-colors">
              <input
                type="checkbox"
                checked={authValidation}
                onChange={(e) => setAuthValidation(e.target.checked)}
                className="mt-0.5 accent-[#0891B2]"
              />
              <div>
                <span className="font-bold text-[#172033] block">Command Signature Validation</span>
                <span className="text-[11px] text-[#52647A]">Rejects simulated commands lacking verified cryptographic token.</span>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3.5 rounded-xl border border-[#D7E1ED] bg-[#F8FAFC] cursor-pointer hover:bg-slate-100 transition-colors">
              <input
                type="checkbox"
                checked={currentCap}
                onChange={(e) => setCurrentCap(e.target.checked)}
                className="mt-0.5 accent-[#0891B2]"
              />
              <div className="w-full">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-[#172033]">Current Cap Ceiling</span>
                  {currentCap && (
                    <input
                      type="number"
                      value={currentCapVal}
                      onChange={(e) => setCurrentCapVal(e.target.value)}
                      className="w-16 px-1.5 py-0.5 bg-white border border-slate-300 rounded font-mono text-[11px]"
                    />
                  )}
                </div>
                <span className="text-[11px] text-[#52647A]">Clamps requested currents to safe maximum limit.</span>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3.5 rounded-xl border border-[#D7E1ED] bg-[#F8FAFC] cursor-pointer hover:bg-slate-100 transition-colors">
              <input
                type="checkbox"
                checked={rateLimiting}
                onChange={(e) => setRateLimiting(e.target.checked)}
                className="mt-0.5 accent-[#0891B2]"
              />
              <div>
                <span className="font-bold text-[#172033] block">Command Rate Limiting</span>
                <span className="text-[11px] text-[#52647A]">Rejects rapid oscillations or repeated setpoint modifications.</span>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3.5 rounded-xl border border-[#D7E1ED] bg-[#F8FAFC] cursor-pointer hover:bg-slate-100 transition-colors">
              <input
                type="checkbox"
                checked={thermalLockout}
                onChange={(e) => setThermalLockout(e.target.checked)}
                className="mt-0.5 accent-[#0891B2]"
              />
              <div>
                <span className="font-bold text-[#172033] block">Thermal Protection Lockout</span>
                <span className="text-[11px] text-[#52647A]">Forces protective shutdown when cell temperatures enter caution zone.</span>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Comparative Effectiveness Report (F40) */}
      {result && (
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E2E8F0] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <h3 className="text-base font-bold text-[#172033]">Comparative Effectiveness Report (F40)</h3>
              </div>
              <p className="text-xs text-[#52647A] font-mono mt-0.5">
                Scenario: {result.scenario_id} &mdash; {result.scenario_name} (Seed: {result.seed_used})
              </p>
            </div>

            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              result.is_defense_effective ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'
            }`}>
              {result.is_defense_effective ? 'Defenses Effective' : 'No Improvement'}
            </span>
          </div>

          {/* Differential Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
              <span className="text-[10px] text-[#64748B] font-sans font-semibold block">Peak Temperature Delta</span>
              <div className="text-lg font-bold text-[#172033]">
                {result.baseline_peak_temp.toFixed(1)}°C &rarr; <span className="text-emerald-600">{result.defended_peak_temp.toFixed(1)}°C</span>
              </div>
              <span className="text-xs text-emerald-700 font-bold font-sans">
                -{result.temp_reduction_deg_c.toFixed(1)}°C ({result.percent_temp_improvement}%)
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
              <span className="text-[10px] text-[#64748B] font-sans font-semibold block">Peak Current Delta</span>
              <div className="text-lg font-bold text-[#172033]">
                {result.baseline_peak_current.toFixed(1)}A &rarr; <span className="text-emerald-600">{result.defended_peak_current.toFixed(1)}A</span>
              </div>
              <span className="text-xs text-emerald-700 font-bold font-sans">
                -{result.current_reduction_a.toFixed(1)} A reduced
              </span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
              <span className="text-[10px] text-[#64748B] font-sans font-semibold block">Breaker Tripping</span>
              <div className="text-lg font-bold">
                {result.baseline_fault_triggered ? (
                  <span className="text-red-600">TRIPPED</span>
                ) : (
                  <span className="text-slate-600">SAFE</span>
                )}{' '}
                &rarr;{' '}
                {result.defended_fault_triggered ? (
                  <span className="text-red-600">TRIPPED</span>
                ) : (
                  <span className="text-emerald-600">PREVENTED</span>
                )}
              </div>
              <span className="text-[10px] text-[#52647A] font-sans">Hardware safety status</span>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
              <span className="text-[10px] text-[#64748B] font-sans font-semibold block">Interventions</span>
              <div className="text-lg font-bold text-[#0891B2]">
                {result.interventions_triggered?.length || 0} Blocked
              </div>
              <span className="text-[10px] text-[#52647A] font-sans">Active defense actions</span>
            </div>
          </div>

          {/* Interventions Timeline Table */}
          {result.interventions_triggered?.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-[#172033] uppercase tracking-wider">
                Active Interventions Triggered
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[#D7E1ED] bg-[#F8FAFC] text-[#64748B] uppercase tracking-wider font-semibold">
                      <th className="py-2.5 px-3">Time</th>
                      <th className="py-2.5 px-3">Mitigation</th>
                      <th className="py-2.5 px-3">Action</th>
                      <th className="py-2.5 px-3">Target Event</th>
                      <th className="py-2.5 px-3">Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0] font-mono">
                    {result.interventions_triggered.map((inter, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="py-2.5 px-3 font-bold text-[#0891B2]">{inter.timestamp.toFixed(1)}s</td>
                        <td className="py-2.5 px-3 text-[#172033] font-sans font-bold">{inter.mitigation_name}</td>
                        <td className="py-2.5 px-3">
                          <span className="px-2 py-0.5 bg-cyan-100 text-[#0891B2] rounded text-[10px] font-bold">
                            {inter.action_taken}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-[#52647A]">{inter.target_event_id || 'N/A'}</td>
                        <td className="py-2.5 px-3 text-[#52647A] font-sans">{inter.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Summary Text */}
          <div className="p-4 bg-cyan-50 border border-cyan-200 rounded-xl text-xs text-cyan-900 leading-relaxed">
            {result.summary}
          </div>
        </div>
      )}
    </div>
  );
}
