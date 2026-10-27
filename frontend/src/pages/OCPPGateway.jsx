import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Play,
  Square,
  RotateCcw,
  Sliders,
  Cpu,
  Zap,
  Activity,
  Clock,
  ArrowRight,
  RefreshCw,
  X,
  Radio,
  FileCheck,
  Flame,
  Terminal,
} from 'lucide-react';
import { api } from '../services/api';

export default function OCPPGateway() {
  const [status, setStatus] = useState(null);
  const [interventions, setInterventions] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isStartingStopping, setIsStartingStopping] = useState(false);
  const [runningScenarioId, setRunningScenarioId] = useState(null);
  const [lastScenarioResult, setLastScenarioResult] = useState(null);
  const [errorBanner, setErrorBanner] = useState(null);
  const [successBanner, setSuccessBanner] = useState(null);

  // Filters & Modal
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [selectedIntervention, setSelectedIntervention] = useState(null);
  const [showConfigDrawer, setShowConfigDrawer] = useState(false);

  // Policy Form State
  const [policyForm, setPolicyForm] = useState({
    current_cap_enabled: true,
    current_cap_value: 100.0,
    rate_limiting_enabled: true,
    min_command_interval_seconds: 5.0,
    auth_validation_enabled: true,
    thermal_lockout_enabled: true,
    thermal_lockout_threshold_c: 45.0,
  });

  // Fetch status and interventions
  const fetchGatewayData = useCallback(async () => {
    try {
      const [statusData, interData, scenData] = await Promise.all([
        api.getGatewayStatus(),
        api.getGatewayInterventions(100),
        api.getGatewayScenarios(),
      ]);
      setStatus(statusData);
      setInterventions(interData.interventions || []);
      setScenarios(scenData || []);
      if (statusData.policy) {
        setPolicyForm((prev) => ({ ...prev, ...statusData.policy }));
      }
    } catch (err) {
      console.error('Failed to fetch gateway status', err);
      setErrorBanner('Could not connect to Gateway API: ' + (err.message || String(err)));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGatewayData();
    const interval = setInterval(fetchGatewayData, 3000);
    return () => clearInterval(interval);
  }, [fetchGatewayData]);

  // Handler: Start Gateway
  const handleStartGateway = async () => {
    setIsStartingStopping(true);
    setErrorBanner(null);
    try {
      const newStatus = await api.startGateway({ charger_port: 9000, csms_port: 9001 });
      setStatus(newStatus);
      setSuccessBanner('ThreatLens OCPP Gateway started on port 9000 (Charger) ↔ port 9001 (CSMS).');
      fetchGatewayData();
    } catch (err) {
      setErrorBanner('Failed to start Gateway: ' + (err.message || String(err)));
    } finally {
      setIsStartingStopping(false);
    }
  };

  // Handler: Stop Gateway
  const handleStopGateway = async () => {
    setIsStartingStopping(true);
    setErrorBanner(null);
    try {
      const newStatus = await api.stopGateway();
      setStatus(newStatus);
      setSuccessBanner('Gateway service stopped cleanly.');
      fetchGatewayData();
    } catch (err) {
      setErrorBanner('Failed to stop Gateway: ' + (err.message || String(err)));
    } finally {
      setIsStartingStopping(false);
    }
  };

  // Handler: Save Policy Configuration
  const handleSavePolicy = async () => {
    setErrorBanner(null);
    try {
      const updated = await api.updateGatewayConfig(policyForm);
      setStatus(updated);
      setSuccessBanner('Gateway safety policy settings updated successfully.');
      setShowConfigDrawer(false);
    } catch (err) {
      setErrorBanner('Failed to update policy: ' + (err.message || String(err)));
    }
  };

  // Handler: Run Scenario
  const handleRunScenario = async (scenarioId) => {
    setRunningScenarioId(scenarioId);
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const result = await api.runGatewayScenario(scenarioId);
      setLastScenarioResult(result);
      if (result.verification_passed) {
        setSuccessBanner(`Scenario '${result.scenario_name}' completed: Verified successfully.`);
      } else {
        setErrorBanner(`Scenario '${result.scenario_name}' finished with failures: ${result.summary}`);
      }
      fetchGatewayData();
    } catch (err) {
      setErrorBanner('Scenario execution failed: ' + (err.message || String(err)));
    } finally {
      setRunningScenarioId(null);
    }
  };

  // Handler: Clear Interventions
  const handleClearInterventions = async () => {
    try {
      await api.clearGatewayInterventions();
      setInterventions([]);
      setSuccessBanner('Intervention logs reset.');
      fetchGatewayData();
    } catch (err) {
      setErrorBanner('Failed to clear logs: ' + (err.message || String(err)));
    }
  };

  // Filtered interventions
  const filteredInterventions = interventions.filter((item) => {
    if (decisionFilter === 'ALL') return true;
    return item.decision === decisionFilter;
  });

  return (
    <div className="w-full space-y-8 animate-page-enter">
      {/* Alert Banners */}
      {errorBanner && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-900 text-sm font-mono flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="w-5 h-5 text-red-600 shrink-0" />
            <span>{errorBanner}</span>
          </div>
          <button onClick={() => setErrorBanner(null)} className="text-red-500 hover:text-red-800 font-bold ml-4 cursor-pointer">
            ✕
          </button>
        </div>
      )}

      {successBanner && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-sm font-mono flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{successBanner}</span>
          </div>
          <button onClick={() => setSuccessBanner(null)} className="text-emerald-500 hover:text-emerald-800 font-bold ml-4 cursor-pointer">
            ✕
          </button>
        </div>
      )}

      {/* Top Hero / Control Banner */}
      <div className="bg-white rounded-2xl border border-[#D7E1ED] p-6 shadow-xs">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-600 to-blue-600 flex items-center justify-center shadow-md shadow-cyan-600/20">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-extrabold tracking-tight text-[#172033] font-mono">
                    OCPP 1.6-J Security Gateway
                  </h1>
                  {status?.is_running ? (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-mono font-bold border border-emerald-200">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                      GATEWAY RUNNING
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-mono font-bold border border-slate-300">
                      <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                      GATEWAY STOPPED
                    </span>
                  )}
                </div>
                <p className="text-sm text-[#52647A] font-medium">
                  Deterministic ALLOW / CLAMP / BLOCK Policy Engine & In-Flight Frame Interception
                </p>
              </div>
            </div>

            {/* Loopback Ports & Uplink Status */}
            <div className="flex flex-wrap items-center gap-2 pt-2 text-xs font-mono text-[#52647A]">
              <span className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-[#172033]">
                Charger Port: <strong className="text-cyan-700 font-bold">ws://127.0.0.1:{status?.charger_port || 9000}</strong>
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              <span className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-[#172033]">
                CSMS Target: <strong className="text-blue-700 font-bold">ws://127.0.0.1:{status?.csms_port || 9001}</strong>
              </span>
              <span className="px-2.5 py-1 rounded-md bg-cyan-50 border border-cyan-200 text-cyan-800">
                Protocol: <strong>ocpp1.6 (Strict JSON)</strong>
              </span>
              <span className="px-2.5 py-1 rounded-md bg-amber-50 border border-amber-200 text-amber-800">
                ML Usage: <strong>Zero (100% Deterministic Rules)</strong>
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 shrink-0">
            {status?.is_running ? (
              <button
                onClick={handleStopGateway}
                disabled={isStartingStopping}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-sm font-mono font-bold transition-all shadow-xs cursor-pointer disabled:opacity-50"
              >
                <Square className="w-4 h-4 text-rose-600 fill-current" />
                <span>Stop Gateway</span>
              </button>
            ) : (
              <button
                onClick={handleStartGateway}
                disabled={isStartingStopping}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white text-sm font-mono font-bold transition-all shadow-md shadow-cyan-600/20 cursor-pointer disabled:opacity-50"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>Start Gateway</span>
              </button>
            )}

            <button
              onClick={() => setShowConfigDrawer(!showConfigDrawer)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 text-[#172033] hover:bg-slate-200 border border-slate-200 text-sm font-mono font-bold transition-all cursor-pointer"
            >
              <Sliders className="w-4 h-4 text-cyan-600" />
              <span>Safety Policies</span>
            </button>

            <button
              onClick={fetchGatewayData}
              title="Refresh Telemetry"
              className="p-2.5 rounded-xl bg-slate-100 text-slate-600 hover:text-[#172033] hover:bg-slate-200 border border-slate-200 cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Mandatory Cyber-Physical Software Simulation Disclaimer Box */}
        <div className="mt-5 p-3.5 rounded-xl bg-amber-50/80 border border-amber-200/80 text-amber-900 text-xs font-mono flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <strong>RESEARCH PROTOTYPE & SOFTWARE SIMULATION NOTICE:</strong>{' '}
            {status?.disclaimer ||
              'ThreatLens OCPP Security Gateway is a research prototype and cyber-physical software simulation; it does not certify physical electrical breaker safety or hardware contactor compliance.'}
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Total Messages */}
        <div className="bg-white rounded-xl border border-[#D7E1ED] p-4 shadow-2xs">
          <div className="text-xs font-mono text-[#52647A] uppercase tracking-wider">Total Evaluated</div>
          <div className="text-2xl font-bold font-mono text-[#172033] mt-1">
            {status?.metrics?.total_messages || 0}
          </div>
          <div className="text-[11px] font-mono text-slate-500 mt-1 flex items-center gap-1">
            <Activity className="w-3 h-3 text-cyan-600" /> Inbound / Outbound
          </div>
        </div>

        {/* ALLOW Count */}
        <div className="bg-white rounded-xl border border-emerald-200 p-4 shadow-2xs bg-emerald-50/30">
          <div className="text-xs font-mono text-emerald-800 uppercase tracking-wider font-bold">ALLOWED</div>
          <div className="text-2xl font-bold font-mono text-emerald-700 mt-1">
            {status?.metrics?.allowed || 0}
          </div>
          <div className="text-[11px] font-mono text-emerald-600 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Pass-Through Valid
          </div>
        </div>

        {/* CLAMP Count */}
        <div className="bg-white rounded-xl border border-amber-200 p-4 shadow-2xs bg-amber-50/30">
          <div className="text-xs font-mono text-amber-800 uppercase tracking-wider font-bold">CLAMPED</div>
          <div className="text-2xl font-bold font-mono text-amber-700 mt-1">
            {status?.metrics?.clamped || 0}
          </div>
          <div className="text-[11px] font-mono text-amber-600 mt-1 flex items-center gap-1">
            <Zap className="w-3 h-3" /> Capped to Safe Limit
          </div>
        </div>

        {/* BLOCK Count */}
        <div className="bg-white rounded-xl border border-rose-200 p-4 shadow-2xs bg-rose-50/30">
          <div className="text-xs font-mono text-rose-800 uppercase tracking-wider font-bold">BLOCKED</div>
          <div className="text-2xl font-bold font-mono text-rose-700 mt-1">
            {status?.metrics?.blocked || 0}
          </div>
          <div className="text-[11px] font-mono text-rose-600 mt-1 flex items-center gap-1">
            <ShieldAlert className="w-3 h-3" /> Security & Violations
          </div>
        </div>

        {/* Audit Queue Health */}
        <div className="bg-white rounded-xl border border-[#D7E1ED] p-4 shadow-2xs col-span-2 md:col-span-1">
          <div className="text-xs font-mono text-[#52647A] uppercase tracking-wider">Audit Ring-Buffer</div>
          <div className="text-2xl font-bold font-mono text-[#172033] mt-1">
            {status?.audit?.queue_depth || 0} <span className="text-xs font-normal text-slate-400">/ 1000</span>
          </div>
          <div className="text-[11px] font-mono text-slate-500 mt-1">
            Dropped Events: <strong className="text-rose-600">{status?.audit?.dropped_events || 0}</strong>
          </div>
        </div>
      </div>

      {/* Policy Tuning Panel (Collapsible) */}
      {showConfigDrawer && (
        <div className="bg-white rounded-2xl border border-cyan-200 p-6 shadow-md shadow-cyan-900/5 animate-page-enter">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-cyan-600" />
              <h2 className="text-lg font-bold font-mono text-[#172033]">Deterministic Safety Policy Configuration</h2>
            </div>
            <button
              onClick={() => setShowConfigDrawer(false)}
              className="text-slate-400 hover:text-slate-600 text-sm font-bold cursor-pointer"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 pt-5">
            {/* Rule R-01: Current Cap */}
            <div className="space-y-3 p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-[#172033]">R-01: Current Ceiling</span>
                <input
                  type="checkbox"
                  checked={policyForm.current_cap_enabled}
                  onChange={(e) => setPolicyForm({ ...policyForm, current_cap_enabled: e.target.checked })}
                  className="rounded text-cyan-600 cursor-pointer"
                />
              </div>
              <div>
                <label className="text-[11px] font-mono text-slate-500">Safe Cap Limit (Amperes)</label>
                <input
                  type="number"
                  min="20"
                  max="200"
                  value={policyForm.current_cap_value}
                  onChange={(e) => setPolicyForm({ ...policyForm, current_cap_value: parseFloat(e.target.value) || 0 })}
                  className="w-full mt-1 px-3 py-1.5 rounded-lg border border-slate-300 font-mono text-sm bg-white"
                />
              </div>
              <p className="text-[11px] font-mono text-slate-500">
                Hardware max: <strong>150.0 A</strong>. Setpoints above {policyForm.current_cap_value}A are clamped.
              </p>
            </div>

            {/* Rule R-02: Rate Limiting */}
            <div className="space-y-3 p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-[#172033]">R-02: Command Flutter</span>
                <input
                  type="checkbox"
                  checked={policyForm.rate_limiting_enabled}
                  onChange={(e) => setPolicyForm({ ...policyForm, rate_limiting_enabled: e.target.checked })}
                  className="rounded text-cyan-600 cursor-pointer"
                />
              </div>
              <div>
                <label className="text-[11px] font-mono text-slate-500">Min Interval (Seconds)</label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  max="30"
                  value={policyForm.min_command_interval_seconds}
                  onChange={(e) => setPolicyForm({ ...policyForm, min_command_interval_seconds: parseFloat(e.target.value) || 0 })}
                  className="w-full mt-1 px-3 py-1.5 rounded-lg border border-slate-300 font-mono text-sm bg-white"
                />
              </div>
              <p className="text-[11px] font-mono text-slate-500">
                Rejects SetChargingProfile commands arriving faster than {policyForm.min_command_interval_seconds}s.
              </p>
            </div>

            {/* Rule R-03: Authorization */}
            <div className="space-y-3 p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-[#172033]">R-03: Auth Validation</span>
                <input
                  type="checkbox"
                  checked={policyForm.auth_validation_enabled}
                  onChange={(e) => setPolicyForm({ ...policyForm, auth_validation_enabled: e.target.checked })}
                  className="rounded text-cyan-600 cursor-pointer"
                />
              </div>
              <p className="text-xs font-mono text-slate-600 pt-1">
                Rejects rogue, expired, or unauthenticated tokens during RemoteStartTransaction.
              </p>
              <div className="text-[11px] font-mono text-cyan-700 bg-cyan-50 px-2 py-1 rounded border border-cyan-100">
                Blocks rogue idTags: ROGUE*, UNAUTH*
              </div>
            </div>

            {/* Rule R-04: Thermal Lockout */}
            <div className="space-y-3 p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-[#172033]">R-04: Thermal Lockout</span>
                <input
                  type="checkbox"
                  checked={policyForm.thermal_lockout_enabled}
                  onChange={(e) => setPolicyForm({ ...policyForm, thermal_lockout_enabled: e.target.checked })}
                  className="rounded text-cyan-600 cursor-pointer"
                />
              </div>
              <div>
                <label className="text-[11px] font-mono text-slate-500">Lockout Temp (°C)</label>
                <input
                  type="number"
                  min="35"
                  max="80"
                  value={policyForm.thermal_lockout_threshold_c}
                  onChange={(e) => setPolicyForm({ ...policyForm, thermal_lockout_threshold_c: parseFloat(e.target.value) || 0 })}
                  className="w-full mt-1 px-3 py-1.5 rounded-lg border border-slate-300 font-mono text-sm bg-white"
                />
              </div>
              <p className="text-[11px] font-mono text-slate-500">
                Halts new transaction starts when EVSE temperature reaches {policyForm.thermal_lockout_threshold_c}°C.
              </p>
            </div>
          </div>

          <div className="mt-5 flex justify-end">
            <button
              onClick={handleSavePolicy}
              className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-700 text-white text-xs font-mono font-bold transition-all shadow-sm cursor-pointer"
            >
              Save Policy Parameters
            </button>
          </div>
        </div>
      )}

      {/* Repeatable Scenarios Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold font-mono text-[#172033] flex items-center gap-2">
              <Terminal className="w-5 h-5 text-cyan-600" />
              Repeatable Local Mock Scenarios
            </h2>
            <p className="text-xs text-[#52647A] font-mono">
              Execute deterministic OCPP attack profiles and baseline workflows through the local testbench.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {scenarios.map((scen) => {
            const isRunning = runningScenarioId === scen.id;
            const isBenign = scen.id === 'benign_charging';
            return (
              <div
                key={scen.id}
                className="bg-white rounded-xl border border-[#D7E1ED] p-4 flex flex-col justify-between shadow-2xs hover:border-cyan-400 transition-all"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold border ${
                        isBenign
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-rose-50 text-rose-700 border-rose-200'
                      }`}
                    >
                      {scen.category}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 font-bold">
                      {scen.expected_decisions.join('/')}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm text-[#172033] font-mono">{scen.name}</h3>
                  <p className="text-xs text-[#52647A] leading-relaxed line-clamp-3">{scen.description}</p>
                </div>

                <div className="pt-4 mt-3 border-t border-slate-100 space-y-2">
                  <div className="text-[10px] font-mono text-slate-500">
                    Rule: <strong className="text-cyan-700">{scen.mitigation_rule}</strong>
                  </div>
                  <button
                    onClick={() => handleRunScenario(scen.id)}
                    disabled={isRunning || runningScenarioId !== null}
                    className={`w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                      isRunning
                        ? 'bg-cyan-100 text-cyan-800'
                        : isBenign
                        ? 'bg-slate-100 hover:bg-slate-200 text-[#172033] border border-slate-200'
                        : 'bg-cyan-50 hover:bg-cyan-100 text-cyan-800 border border-cyan-200'
                    }`}
                  >
                    {isRunning ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-700" />
                        <span>Running...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 fill-current" />
                        <span>Run Scenario</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Last Executed Scenario Outcome Banner */}
        {lastScenarioResult && (
          <div className="p-4 rounded-xl bg-white border border-[#D7E1ED] shadow-xs space-y-2 animate-page-enter">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-cyan-600" />
                <span className="text-xs font-mono font-bold text-[#172033]">
                  Scenario Result: {lastScenarioResult.scenario_name}
                </span>
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                    lastScenarioResult.verification_passed
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {lastScenarioResult.status}
                </span>
              </div>
              <span className="text-xs font-mono text-slate-500">
                Duration: {lastScenarioResult.execution_time_seconds}s
              </span>
            </div>
            <p className="text-xs font-mono text-slate-700 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-200">
              {lastScenarioResult.summary}
            </p>
          </div>
        )}
      </div>

      {/* Live Interventions Feed */}
      <div className="bg-white rounded-2xl border border-[#D7E1ED] p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-lg font-bold font-mono text-[#172033] flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-600" />
              Gateway Intervention & Activity Feed
            </h2>
            <p className="text-xs text-[#52647A] font-mono">
              Real-time audit log of deterministic ALLOW, CLAMP, and BLOCK decisions.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Filter pills */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-mono">
              {['ALL', 'ALLOW', 'CLAMP', 'BLOCK'].map((f) => (
                <button
                  key={f}
                  onClick={() => setDecisionFilter(f)}
                  className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                    decisionFilter === f ? 'bg-white text-cyan-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>

            <button
              onClick={handleClearInterventions}
              className="p-1.5 text-xs font-mono text-slate-500 hover:text-rose-600 border border-slate-200 rounded-lg cursor-pointer"
              title="Clear Event Log"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Interventions Table */}
        {filteredInterventions.length === 0 ? (
          <div className="text-center py-12 text-slate-400 font-mono text-sm">
            No gateway intervention records match the selected filter.
            <div className="text-xs text-slate-400 mt-1">Run a scenario above to observe live decisions.</div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 text-[11px] uppercase tracking-wider bg-slate-50/50">
                  <th className="py-2.5 px-3">Time</th>
                  <th className="py-2.5 px-3">Charge Point</th>
                  <th className="py-2.5 px-3">Action</th>
                  <th className="py-2.5 px-3">Direction</th>
                  <th className="py-2.5 px-3">Decision</th>
                  <th className="py-2.5 px-3">Policy Rule</th>
                  <th className="py-2.5 px-3">Setpoint Delta</th>
                  <th className="py-2.5 px-3">Reason</th>
                  <th className="py-2.5 px-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredInterventions.map((evt, idx) => {
                  const dateStr = new Date(evt.timestamp * 1000).toLocaleTimeString();
                  const isBlock = evt.decision === 'BLOCK';
                  const isClamp = evt.decision === 'CLAMP';
                  const isAllow = evt.decision === 'ALLOW';

                  return (
                    <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-2.5 px-3 text-slate-500">{dateStr}</td>
                      <td className="py-2.5 px-3 font-bold text-slate-800">{evt.charge_point_id}</td>
                      <td className="py-2.5 px-3 font-semibold text-cyan-800">{evt.action}</td>
                      <td className="py-2.5 px-3 text-slate-500">
                        {evt.direction === 'CSMS_TO_CHARGER' ? (
                          <span className="text-blue-600 font-medium">CSMS → EVSE</span>
                        ) : (
                          <span className="text-emerald-600 font-medium">EVSE → CSMS</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${
                            isAllow
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : isClamp
                              ? 'bg-amber-50 text-amber-800 border-amber-200'
                              : 'bg-rose-50 text-rose-700 border-rose-200'
                          }`}
                        >
                          {evt.decision}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-bold text-slate-700">{evt.rule_id}</td>
                      <td className="py-2.5 px-3 font-mono">
                        {isClamp && evt.original_limit !== null ? (
                          <span className="text-amber-800 font-bold">
                            {evt.original_limit}A → <strong className="text-emerald-700">{evt.modified_limit}A</strong>
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-600 max-w-xs truncate" title={evt.reason}>
                        {evt.reason}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <button
                          onClick={() => setSelectedIntervention(evt)}
                          className="px-2 py-1 text-[11px] font-mono text-cyan-700 hover:text-cyan-900 bg-cyan-50 hover:bg-cyan-100 rounded border border-cyan-200 cursor-pointer"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* JSON Inspection Modal */}
      {selectedIntervention && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyan-600" />
                <h3 className="font-mono font-bold text-base text-[#172033]">
                  Intervention Record: [{selectedIntervention.unique_id}]
                </h3>
              </div>
              <button
                onClick={() => setSelectedIntervention(null)}
                className="text-slate-400 hover:text-slate-600 font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div>
                  <span className="text-slate-500">Action:</span> <strong>{selectedIntervention.action}</strong>
                </div>
                <div>
                  <span className="text-slate-500">Decision:</span>{' '}
                  <strong className="text-cyan-700">{selectedIntervention.decision}</strong>
                </div>
                <div>
                  <span className="text-slate-500">Rule Triggered:</span>{' '}
                  <strong>{selectedIntervention.rule_id}</strong>
                </div>
                <div>
                  <span className="text-slate-500">Direction:</span>{' '}
                  <strong>{selectedIntervention.direction}</strong>
                </div>
              </div>

              <div>
                <span className="text-slate-500 block mb-1">Reason:</span>
                <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 leading-relaxed">
                  {selectedIntervention.reason}
                </div>
              </div>

              <div>
                <span className="text-slate-500 block mb-1">Full Record JSON:</span>
                <pre className="p-3 bg-slate-900 text-cyan-300 rounded-xl overflow-x-auto text-[11px] max-h-60">
                  {JSON.stringify(selectedIntervention, null, 2)}
                </pre>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedIntervention(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 text-[#172033] hover:bg-slate-200 font-mono text-xs font-bold cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
