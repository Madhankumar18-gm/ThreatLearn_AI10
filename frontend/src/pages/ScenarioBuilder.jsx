import React, { useState } from 'react';
import { api } from '../services/api';
import {
  Sliders,
  Plus,
  Trash2,
  Save,
  Play,
  Download,
  Upload,
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  Clock,
  Sparkles,
  Info
} from 'lucide-react';

export default function ScenarioBuilder({ onRunGenerated, setActiveTab }) {
  const [name, setName] = useState('Custom High Power Cyber-Physical Test');
  const [description, setDescription] = useState('Evaluates rapid thermal accumulation following an unauthorized current command override.');
  const [duration, setDuration] = useState(60.0);
  const [seed, setSeed] = useState(1042);
  const [sensorNoise, setSensorNoise] = useState(0.05);
  const [cyberOffset, setCyberOffset] = useState(0.0);
  const [telemetryOffset, setTelemetryOffset] = useState(0.0);

  // Defenses
  const [authValidation, setAuthValidation] = useState(false);
  const [commandWhitelist, setCommandWhitelist] = useState(false);
  const [currentCap, setCurrentCap] = useState(false);
  const [currentCapVal, setCurrentCapVal] = useState(100.0);
  const [rateLimiting, setRateLimiting] = useState(false);
  const [sensorCrosscheck, setSensorCrosscheck] = useState(false);
  const [thermalLockout, setThermalLockout] = useState(false);

  // Scheduled Events
  const [events, setEvents] = useState([
    {
      event_id: 'EVT-CUST-01',
      timestamp: 5.0,
      layer: 'cyber_protocol',
      component_id: 'csms_backend',
      event_type: 'START_TRANSACTION',
      source: 'csms',
      auth_status: 'authorized',
      details: { requested_current: 50.0 }
    },
    {
      event_id: 'EVT-CUST-02',
      timestamp: 18.0,
      layer: 'cyber_protocol',
      component_id: 'csms_backend',
      event_type: 'CHANGE_CURRENT_LIMIT',
      source: 'csms',
      auth_status: 'unauthorized',
      details: { requested_current: 140.0 }
    }
  ]);

  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const addEvent = () => {
    const newId = `EVT-CUST-${String(events.length + 1).padStart(2, '0')}`;
    setEvents([
      ...events,
      {
        event_id: newId,
        timestamp: Math.min(duration - 5, (events[events.length - 1]?.timestamp || 10) + 10),
        layer: 'cyber_protocol',
        component_id: 'csms_backend',
        event_type: 'CHANGE_CURRENT_LIMIT',
        source: 'csms',
        auth_status: 'authorized',
        details: { requested_current: 80.0 }
      }
    ]);
  };

  const removeEvent = (index) => {
    setEvents(events.filter((_, idx) => idx !== index));
  };

  const updateEvent = (index, field, value) => {
    const copy = [...events];
    if (field.startsWith('details.')) {
      const key = field.split('.')[1];
      copy[index].details = { ...copy[index].details, [key]: value };
    } else {
      copy[index][field] = value;
    }
    setEvents(copy);
  };

  const buildPayload = () => {
    return {
      name,
      family: 'Custom',
      description,
      duration_seconds: parseFloat(duration),
      default_seed: parseInt(seed, 10),
      components_involved: ['csms_backend', 'evse_controller', 'power_converter', 'battery_pack', 'cooling_system', 'temperature_sensor'],
      scheduled_events: events.map((e) => ({
        ...e,
        timestamp: parseFloat(e.timestamp),
        details: {
          ...e.details,
          ...(e.details.requested_current ? { requested_current: parseFloat(e.details.requested_current) } : {}),
          ...(e.details.drift_rate_c_per_sec ? { drift_rate_c_per_sec: parseFloat(e.details.drift_rate_c_per_sec) } : {}),
          ...(e.details.stuck_value ? { stuck_value: parseFloat(e.details.stuck_value) } : {}),
          ...(e.details.spike_value ? { spike_value: parseFloat(e.details.spike_value) } : {})
        }
      })),
      expected_physical_effects: 'Simulated custom cyber-physical response curve.',
      safety_limitations: 'Custom scenario for defensive testing research only.',
      sensor_noise_std: parseFloat(sensorNoise),
      cyber_timestamp_offset: parseFloat(cyberOffset),
      telemetry_timestamp_offset: parseFloat(telemetryOffset),
      defense_config: {
        auth_validation_enabled: authValidation,
        command_whitelist_enabled: commandWhitelist,
        current_cap_enabled: currentCap,
        current_cap_value: parseFloat(currentCapVal),
        rate_limiting_enabled: rateLimiting,
        sensor_crosscheck_enabled: sensorCrosscheck,
        thermal_lockout_enabled: thermalLockout
      }
    };
  };

  const handleSaveAndRun = async () => {
    setLoading(true);
    setStatusMsg(null);
    setErrorMsg(null);
    try {
      const payload = buildPayload();
      const customScn = await api.createCustomScenario(payload);
      setStatusMsg(`Created custom scenario: ${customScn.scenario_id}. Simulating...`);

      // Run simulation directly
      const runResult = await api.runSimulation(customScn.scenario_id, seed);
      setStatusMsg(`Simulation complete! Run ID: ${runResult.run_id}`);
      if (onRunGenerated) {
        onRunGenerated(runResult);
      }
      setTimeout(() => {
        setActiveTab('incident-analysis');
      }, 800);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to create and run scenario');
    } finally {
      setLoading(false);
    }
  };

  const handleExportJSON = () => {
    try {
      const payload = buildPayload();
      const exportEnvelope = {
        schema_version: '2.0.0',
        exported_at: new Date().toISOString(),
        scenario: {
          ...payload,
          scenario_id: `SCN-CUST-${Math.random().toString(16).substring(2, 8).toUpperCase()}`,
          is_custom: true,
          is_held_out: false
        }
      };
      const blob = new Blob([JSON.stringify(exportEnvelope, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `threatlens_${name.toLowerCase().replace(/[^a-z0-9]/g, '_')}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setErrorMsg(`Export error: ${err.message}`);
    }
  };

  const handleImportJSON = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const rawJson = JSON.parse(event.target.result);
        const imported = await api.importScenario(rawJson);
        setStatusMsg(`Successfully imported: ${imported.scenario.name} (${imported.scenario.scenario_id})`);
        setName(imported.scenario.name);
        setDescription(imported.scenario.description);
        setDuration(imported.scenario.duration_seconds);
        setSeed(imported.scenario.default_seed);
        setEvents(imported.scenario.scheduled_events || []);
        if (imported.scenario.defense_config) {
          setAuthValidation(imported.scenario.defense_config.auth_validation_enabled || false);
          setCurrentCap(imported.scenario.defense_config.current_cap_enabled || false);
          setRateLimiting(imported.scenario.defense_config.rate_limiting_enabled || false);
        }
      } catch (err) {
        setErrorMsg(`Import failed: ${err.message}`);
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="w-full space-y-8 pb-12 animate-page-enter">
      {/* Top Banner */}
      <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-8 shadow-xs flex flex-wrap items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <Sliders className="w-6 h-6 text-[#0891B2]" />
            <h1 className="text-xl sm:text-2xl font-bold text-[#172033] tracking-tight">
              Scenario Builder & Advanced Controls (F02, F04)
            </h1>
          </div>
          <p className="text-sm text-[#52647A] mt-1 max-w-2xl leading-relaxed">
            Construct custom simulation experiments with arbitrary setpoint sequences, deterministic noise injections, cyber clock offsets, and active simulated defenses.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-[#172033] font-bold text-xs rounded-xl flex items-center gap-2 cursor-pointer transition-all border border-[#D7E1ED]">
            <Upload className="w-4 h-4 text-[#0891B2]" /> Import JSON (F05)
            <input type="file" accept=".json" onChange={handleImportJSON} className="hidden" />
          </label>
          <button
            onClick={handleExportJSON}
            className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-[#172033] font-bold text-xs rounded-xl flex items-center gap-2 cursor-pointer transition-all border border-[#D7E1ED]"
          >
            <Download className="w-4 h-4 text-[#0891B2]" /> Export JSON
          </button>
          <button
            onClick={handleSaveAndRun}
            disabled={loading}
            className="px-6 py-2.5 bg-[#0891B2] hover:bg-cyan-700 text-white font-bold text-xs uppercase tracking-wider rounded-xl flex items-center gap-2 cursor-pointer shadow-sm transition-all"
          >
            <Play className="w-4 h-4 fill-white" />
            {loading ? 'Simulating...' : 'Save & Run Scenario'}
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Grid: Parameters + Events + Defenses */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Core Parameters & Noise */}
        <div className="space-y-6">
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-[#172033] uppercase tracking-wider border-b border-[#E2E8F0] pb-2">
              Scenario Metadata
            </h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-[#172033] block mb-1">Scenario Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-[#F8FAFC] border border-[#D7E1ED] rounded-lg text-[#172033] font-sans focus:outline-none focus:border-[#0891B2]"
                />
              </div>
              <div>
                <label className="font-semibold text-[#172033] block mb-1">Description</label>
                <textarea
                  rows="3"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-[#F8FAFC] border border-[#D7E1ED] rounded-lg text-[#172033] font-sans focus:outline-none focus:border-[#0891B2]"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-[#172033] block mb-1">Duration (s)</label>
                  <input
                    type="number"
                    min="10"
                    max="300"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    className="w-full px-3 py-2 bg-[#F8FAFC] border border-[#D7E1ED] rounded-lg font-mono text-[#172033]"
                  />
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
          </div>

          {/* Noise & Clock Offset Controls (F04) */}
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-[#172033] uppercase tracking-wider border-b border-[#E2E8F0] pb-2 flex items-center gap-2">
              <Clock className="w-4 h-4 text-[#0891B2]" /> Noise & Clock Skew (F04)
            </h3>
            <div className="space-y-4 text-xs">
              <div>
                <div className="flex justify-between font-semibold text-[#172033] mb-1">
                  <span>Measurement Noise (&sigma;)</span>
                  <span className="font-mono text-[#0891B2]">{sensorNoise}</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="0.5"
                  step="0.01"
                  value={sensorNoise}
                  onChange={(e) => setSensorNoise(parseFloat(e.target.value))}
                  className="w-full accent-[#0891B2]"
                />
              </div>
              <div>
                <div className="flex justify-between font-semibold text-[#172033] mb-1">
                  <span>Cyber Log Clock Offset (s)</span>
                  <span className="font-mono text-[#0891B2]">{cyberOffset > 0 ? `+${cyberOffset}` : cyberOffset}s</span>
                </div>
                <input
                  type="range"
                  min="-10.0"
                  max="10.0"
                  step="0.5"
                  value={cyberOffset}
                  onChange={(e) => setCyberOffset(parseFloat(e.target.value))}
                  className="w-full accent-[#0891B2]"
                />
              </div>
              <div>
                <div className="flex justify-between font-semibold text-[#172033] mb-1">
                  <span>Telemetry Timestamp Offset (s)</span>
                  <span className="font-mono text-[#0891B2]">{telemetryOffset > 0 ? `+${telemetryOffset}` : telemetryOffset}s</span>
                </div>
                <input
                  type="range"
                  min="-10.0"
                  max="10.0"
                  step="0.5"
                  value={telemetryOffset}
                  onChange={(e) => setTelemetryOffset(parseFloat(e.target.value))}
                  className="w-full accent-[#0891B2]"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Center Column: Scheduled Events Sequence */}
        <div className="space-y-4 lg:col-span-2">
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <div>
                <h3 className="text-sm font-bold text-[#172033] uppercase tracking-wider">
                  Scheduled Simulated Events ({events.length})
                </h3>
                <p className="text-xs text-[#52647A]">Define chronological cyber-physical commands and sensor injections.</p>
              </div>
              <button
                onClick={addEvent}
                className="px-3 py-1.5 bg-cyan-50 hover:bg-cyan-100 text-[#0891B2] font-bold text-xs rounded-lg flex items-center gap-1.5 border border-cyan-200 cursor-pointer"
              >
                <Plus className="w-4 h-4" /> Add Event
              </button>
            </div>

            <div className="space-y-3">
              {events.map((ev, idx) => (
                <div key={idx} className="p-4 bg-[#F8FAFC] border border-[#D7E1ED] rounded-xl space-y-3 text-xs">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-2">
                    <span className="font-mono font-bold text-[#0891B2]">#{idx + 1} — {ev.event_id}</span>
                    <button
                      onClick={() => removeEvent(idx)}
                      className="text-red-500 hover:text-red-700 p-1 cursor-pointer"
                      title="Remove event"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div>
                      <label className="text-[10px] text-[#64748B] block mb-1">Time (s)</label>
                      <input
                        type="number"
                        min="0"
                        max={duration}
                        value={ev.timestamp}
                        onChange={(e) => updateEvent(idx, 'timestamp', e.target.value)}
                        className="w-full px-2 py-1.5 bg-white border border-[#D7E1ED] rounded-md font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-[#64748B] block mb-1">Event Type</label>
                      <select
                        value={ev.event_type}
                        onChange={(e) => updateEvent(idx, 'event_type', e.target.value)}
                        className="w-full px-2 py-1.5 bg-white border border-[#D7E1ED] rounded-md font-mono"
                      >
                        <option value="START_TRANSACTION">START_TRANSACTION</option>
                        <option value="CHANGE_CURRENT_LIMIT">CHANGE_CURRENT_LIMIT</option>
                        <option value="STOP_TRANSACTION">STOP_TRANSACTION</option>
                        <option value="DISABLE_COOLING">DISABLE_COOLING</option>
                        <option value="SENSOR_DRIFT">SENSOR_DRIFT</option>
                        <option value="SENSOR_STUCK">SENSOR_STUCK</option>
                        <option value="SENSOR_SPIKE">SENSOR_SPIKE</option>
                        <option value="SENSOR_DROPOUT">SENSOR_DROPOUT</option>
                        <option value="CAN_SPOOF_CURRENT">CAN_SPOOF_CURRENT</option>
                        <option value="CAN_SPOOF_TEMPERATURE">CAN_SPOOF_TEMPERATURE</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] text-[#64748B] block mb-1">Auth Status</label>
                      <select
                        value={ev.auth_status}
                        onChange={(e) => updateEvent(idx, 'auth_status', e.target.value)}
                        className="w-full px-2 py-1.5 bg-white border border-[#D7E1ED] rounded-md"
                      >
                        <option value="authorized">Authorized</option>
                        <option value="unauthorized">Unauthorized</option>
                        <option value="spoofed">Spoofed</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] text-[#64748B] block mb-1">Setpoint / Param</label>
                      <input
                        type="number"
                        value={ev.details?.requested_current || ev.details?.drift_rate_c_per_sec || ev.details?.stuck_value || 0}
                        onChange={(e) => updateEvent(idx, 'details.requested_current', e.target.value)}
                        className="w-full px-2 py-1.5 bg-white border border-[#D7E1ED] rounded-md font-mono"
                        placeholder="Current (A)"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Simulated Defenses Configuration (F39) */}
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-[#172033] uppercase tracking-wider border-b border-[#E2E8F0] pb-2 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#0891B2]" /> Active Simulated Defenses & Mitigations (F39)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <label className="flex items-start gap-3 p-3 rounded-xl border border-[#D7E1ED] bg-[#F8FAFC] cursor-pointer hover:bg-slate-100 transition-colors">
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

              <label className="flex items-start gap-3 p-3 rounded-xl border border-[#D7E1ED] bg-[#F8FAFC] cursor-pointer hover:bg-slate-100 transition-colors">
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

              <label className="flex items-start gap-3 p-3 rounded-xl border border-[#D7E1ED] bg-[#F8FAFC] cursor-pointer hover:bg-slate-100 transition-colors">
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

              <label className="flex items-start gap-3 p-3 rounded-xl border border-[#D7E1ED] bg-[#F8FAFC] cursor-pointer hover:bg-slate-100 transition-colors">
                <input
                  type="checkbox"
                  checked={thermalLockout}
                  onChange={(e) => setThermalLockout(e.target.checked)}
                  className="mt-0.5 accent-[#0891B2]"
                />
                <div>
                  <span className="font-bold text-[#172033] block">Thermal Protection Lockout</span>
                  <span className="text-[11px] text-[#52647A]">Halts charging if pack temperature approaches 60°C.</span>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
