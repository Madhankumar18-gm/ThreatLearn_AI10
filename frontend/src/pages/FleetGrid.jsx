import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  Zap, Activity, ShieldAlert, Cpu, AlertTriangle, CheckCircle, 
  RefreshCw, Radio, Layers, Server, ArrowDownRight, Eye
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  ReferenceLine, CartesianGrid, Legend 
} from 'recharts';

export default function FleetGrid() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [fleetRun, setFleetRun] = useState(null);
  const [selectedCharger, setSelectedCharger] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadFleetScenarios();
  }, []);

  const loadFleetScenarios = async () => {
    try {
      setLoading(true);
      setError(null);
      const scns = await api.getFleetScenarios();
      setScenarios(scns);
      if (scns.length > 0) {
        setSelectedScenario(scns[0]);
        // Auto-run first scenario for instant preview
        executeFleetRun(scns[0]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load fleet scenarios');
    } finally {
      setLoading(false);
    }
  };

  const executeFleetRun = async (scenarioToRun = selectedScenario) => {
    if (!scenarioToRun) return;
    try {
      setSimulating(true);
      setError(null);
      const result = await api.runFleetSimulation(scenarioToRun);
      setFleetRun(result);
      if (result.time_slices.length > 0) {
        const lastSlice = result.time_slices[result.time_slices.length - 1];
        setSelectedCharger(lastSlice.chargers[0]);
      }
    } catch (err) {
      setError(err.message || 'Fleet simulation failed');
    } finally {
      setSimulating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-cyan-600 font-medium">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Loading Fleet & Grid Feeder Twin...</span>
        </div>
      </div>
    );
  }

  const latestSlice = fleetRun && fleetRun.time_slices.length > 0 
    ? fleetRun.time_slices[fleetRun.time_slices.length - 1] 
    : null;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white border border-[#DCE5EF] rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-50 text-cyan-700 border border-cyan-200">
                Features F09, F10, F37
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                10-50 Chargers Feeder Coupled
              </span>
            </div>
            <h1 className="text-2xl font-bold text-[#172033]">
              Fleet & Grid Feeder Digital Twin
            </h1>
            <p className="text-sm text-[#64748B] mt-1 max-w-3xl">
              Simulate 10 to 50 concurrent chargers, monitor aggregate active electrical demand, 
              feeder loading ratio, and distribution voltage sag under targeted or coordinated cyberattacks.
            </p>
          </div>

          <button
            onClick={() => executeFleetRun()}
            disabled={simulating}
            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[#0891B2] hover:bg-[#0e7490] text-white rounded-lg font-medium text-sm transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${simulating ? 'animate-spin' : ''}`} />
            {simulating ? 'Simulating Fleet...' : 'Re-run Fleet Simulation'}
          </button>
        </div>

        {/* Predefined Scenario Selector Tabs */}
        <div className="mt-6 border-t border-[#DCE5EF] pt-4">
          <label className="text-xs font-bold uppercase tracking-wider text-[#64748B] mb-2 block">
            Select Fleet Scenario
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {scenarios.map((s) => {
              const isSelected = selectedScenario?.fleet_scenario_id === s.fleet_scenario_id;
              const isAttack = s.fleet_scenario_id.includes('ATK') || s.fleet_scenario_id.includes('COORD') || s.fleet_scenario_id.includes('CSMS');
              const isDefended = s.fleet_scenario_id.includes('DEF');

              return (
                <button
                  key={s.fleet_scenario_id}
                  onClick={() => {
                    setSelectedScenario(s);
                    executeFleetRun(s);
                  }}
                  className={`text-left p-3 rounded-lg border transition-all ${
                    isSelected
                      ? 'border-[#0891B2] bg-cyan-50/50 shadow-xs ring-1 ring-[#0891B2]'
                      : 'border-[#DCE5EF] bg-[#F8FAFC] hover:bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-[#172033]">
                      {s.name}
                    </span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      isDefended ? 'bg-emerald-100 text-emerald-800' :
                      isAttack ? 'bg-rose-100 text-rose-800' : 'bg-slate-200 text-slate-700'
                    }`}>
                      {s.charger_count} EVSEs
                    </span>
                  </div>
                  <p className="text-[11px] text-[#64748B] line-clamp-2">
                    {s.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Feeder & Fleet KPI Cards */}
      {fleetRun && latestSlice && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <div className="bg-white border border-[#DCE5EF] rounded-xl p-4 shadow-sm">
            <span className="text-xs text-[#64748B] font-medium block">Peak Fleet Demand</span>
            <span className="text-2xl font-bold text-[#172033] mt-1 block">
              {fleetRun.peak_fleet_power_kw} <span className="text-sm font-normal text-[#64748B]">kW</span>
            </span>
            <span className="text-[11px] text-[#64748B] mt-1 block">
              Feeder Rating: {fleetRun.feeder_capacity_kw} kW
            </span>
          </div>

          <div className="bg-white border border-[#DCE5EF] rounded-xl p-4 shadow-sm">
            <span className="text-xs text-[#64748B] font-medium block">Peak Feeder Loading</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-2xl font-bold ${
                fleetRun.peak_feeder_loading_pct >= 95 ? 'text-rose-600' :
                fleetRun.peak_feeder_loading_pct >= 80 ? 'text-amber-600' : 'text-emerald-600'
              }`}>
                {fleetRun.peak_feeder_loading_pct}%
              </span>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                latestSlice.feeder_status === 'CRITICAL_OVERLOAD' ? 'bg-rose-100 text-rose-800' :
                latestSlice.feeder_status === 'WARNING' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
              }`}>
                {latestSlice.feeder_status}
              </span>
            </div>
            {/* Progress bar */}
            <div className="w-full bg-slate-100 h-1.5 rounded-full mt-2 overflow-hidden">
              <div 
                className={`h-full ${
                  fleetRun.peak_feeder_loading_pct >= 95 ? 'bg-rose-500' :
                  fleetRun.peak_feeder_loading_pct >= 80 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(100, fleetRun.peak_feeder_loading_pct)}%` }}
              />
            </div>
          </div>

          <div className="bg-white border border-[#DCE5EF] rounded-xl p-4 shadow-sm">
            <span className="text-xs text-[#64748B] font-medium block">Estimated Feeder Voltage</span>
            <span className={`text-2xl font-bold mt-1 block ${
              fleetRun.min_feeder_voltage_v < 360 ? 'text-rose-600' :
              fleetRun.min_feeder_voltage_v < 380 ? 'text-amber-600' : 'text-[#172033]'
            }`}>
              {latestSlice.feeder_voltage_v} <span className="text-sm font-normal text-[#64748B]">V</span>
            </span>
            <span className="text-[11px] text-[#64748B] mt-1 block">
              Min Voltage: {fleetRun.min_feeder_voltage_v} V (Nom: 400V)
            </span>
          </div>

          <div className="bg-white border border-[#DCE5EF] rounded-xl p-4 shadow-sm">
            <span className="text-xs text-[#64748B] font-medium block">Fleet Operating State</span>
            <div className="flex items-center gap-3 mt-1.5">
              <div>
                <span className="text-lg font-bold text-emerald-600">{latestSlice.active_chargers_count}</span>
                <span className="text-[10px] text-[#64748B] block">Active</span>
              </div>
              <div className="w-px h-6 bg-slate-200" />
              <div>
                <span className="text-lg font-bold text-rose-600">{latestSlice.faulted_chargers_count}</span>
                <span className="text-[10px] text-[#64748B] block">Faulted</span>
              </div>
              <div className="w-px h-6 bg-slate-200" />
              <div>
                <span className="text-lg font-bold text-slate-700">{fleetRun.charger_count}</span>
                <span className="text-[10px] text-[#64748B] block">Total</span>
              </div>
            </div>
          </div>

          <div className="bg-white border border-[#DCE5EF] rounded-xl p-4 shadow-sm">
            <span className="text-xs text-[#64748B] font-medium block">Affected Chargers</span>
            <span className={`text-2xl font-bold mt-1 block ${
              fleetRun.affected_chargers.length > 0 ? 'text-amber-600' : 'text-emerald-600'
            }`}>
              {fleetRun.affected_chargers.length}
            </span>
            <span className="text-[11px] text-[#64748B] mt-1 block truncate">
              {fleetRun.affected_chargers.length > 0 ? fleetRun.affected_chargers.join(', ') : 'None (All Normal)'}
            </span>
          </div>
        </div>
      )}

      {/* Telemetry Charts: Feeder Power and Voltage Sag */}
      {fleetRun && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
            <h3 className="text-sm font-bold text-[#172033] mb-1 flex items-center justify-between">
              <span>Feeder Total Active Demand vs Rated Capacity</span>
              <span className="text-xs font-normal text-[#64748B]">Capacity: {fleetRun.feeder_capacity_kw} kW</span>
            </h3>
            <div className="h-60 w-full mt-3">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={fleetRun.time_slices}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="timestamp" unit="s" stroke="#94A3B8" fontSize={11} />
                  <YAxis unit="kW" stroke="#94A3B8" fontSize={11} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: '8px', fontSize: '12px' }} 
                  />
                  <ReferenceLine y={fleetRun.feeder_capacity_kw} stroke="#DC2626" strokeDasharray="4 4" label={{ value: 'Capacity', fill: '#DC2626', fontSize: 10 }} />
                  <ReferenceLine y={fleetRun.feeder_capacity_kw * 0.8} stroke="#D97706" strokeDasharray="3 3" label={{ value: '80% Warn', fill: '#D97706', fontSize: 10 }} />
                  <Line type="monotone" dataKey="total_fleet_power_kw" stroke="#0891B2" strokeWidth={2.5} dot={false} name="Fleet Active Power (kW)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
            <h3 className="text-sm font-bold text-[#172033] mb-1 flex items-center justify-between">
              <span>Feeder Voltage Sag Response</span>
              <span className="text-xs font-normal text-[#64748B]">Nominal: 400.0 V</span>
            </h3>
            <div className="h-60 w-full mt-3">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={fleetRun.time_slices}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="timestamp" unit="s" stroke="#94A3B8" fontSize={11} />
                  <YAxis domain={[340, 410]} unit="V" stroke="#94A3B8" fontSize={11} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#CBD5E1', borderRadius: '8px', fontSize: '12px' }} 
                  />
                  <ReferenceLine y={400} stroke="#64748B" strokeDasharray="3 3" label={{ value: 'Nominal 400V', fill: '#64748B', fontSize: 10 }} />
                  <ReferenceLine y={360} stroke="#DC2626" strokeDasharray="4 4" label={{ value: 'Brownout Limit (360V)', fill: '#DC2626', fontSize: 10 }} />
                  <Line type="monotone" dataKey="feeder_voltage_v" stroke="#2563EB" strokeWidth={2.5} dot={false} name="Feeder Voltage (V)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Charger Fleet Interactive Status Matrix */}
      {latestSlice && (
        <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div>
              <h3 className="text-base font-bold text-[#172033] flex items-center gap-2">
                <Layers className="w-5 h-5 text-cyan-600" />
                Fleet Charger Matrix ({latestSlice.chargers.length} Simulated EVSE Units)
              </h3>
              <p className="text-xs text-[#64748B]">
                Click any charger card to inspect individual thermal, current, and SoC telemetry.
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                Charging
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
                Fault / Tripped
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
                Cyber Affected
              </span>
            </div>
          </div>

          {/* Grid of chargers */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
            {latestSlice.chargers.map((chg) => {
              const isSelected = selectedCharger?.charger_id === chg.charger_id;
              const isFault = chg.state === 'FAULT';
              const isAffected = chg.is_affected;

              return (
                <div
                  key={chg.charger_id}
                  onClick={() => setSelectedCharger(chg)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-[#0891B2] bg-cyan-50/40 ring-2 ring-[#0891B2]/30'
                      : isFault
                      ? 'border-rose-300 bg-rose-50/50 hover:border-rose-400'
                      : isAffected
                      ? 'border-amber-300 bg-amber-50/40 hover:border-amber-400'
                      : 'border-[#DCE5EF] bg-[#F8FAFC] hover:bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-xs text-[#172033]">
                      {chg.charger_id}
                    </span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                      isFault ? 'bg-rose-100 text-rose-800' :
                      chg.state === 'CHARGING' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'
                    }`}>
                      {chg.state}
                    </span>
                  </div>

                  <div className="space-y-1 text-[11px]">
                    <div className="flex justify-between text-[#64748B]">
                      <span>Current:</span>
                      <span className="font-semibold text-[#172033]">{chg.current_a} A</span>
                    </div>
                    <div className="flex justify-between text-[#64748B]">
                      <span>Power:</span>
                      <span className="font-semibold text-[#172033]">{chg.power_kw} kW</span>
                    </div>
                    <div className="flex justify-between text-[#64748B]">
                      <span>Temp:</span>
                      <span className={`font-semibold ${chg.battery_temp_c >= 50 ? 'text-rose-600' : 'text-[#172033]'}`}>
                        {chg.battery_temp_c}°C
                      </span>
                    </div>
                    <div className="flex justify-between text-[#64748B]">
                      <span>SoC:</span>
                      <span className="font-semibold text-[#172033]">{chg.battery_soc}%</span>
                    </div>
                  </div>

                  {isAffected && (
                    <div className="mt-2 pt-1.5 border-t border-amber-200 flex items-center gap-1 text-[10px] text-amber-800 font-medium">
                      <ShieldAlert className="w-3 h-3 text-amber-600" />
                      <span className="truncate">{chg.active_event || 'Targeted Event'}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Selected Charger Detail Card */}
      {selectedCharger && (
        <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div>
              <h3 className="text-base font-bold text-[#172033] flex items-center gap-2">
                <Eye className="w-5 h-5 text-cyan-600" />
                Charger Inspection: {selectedCharger.charger_id} ({selectedCharger.component_id})
              </h3>
              <p className="text-xs text-[#64748B]">
                Operating Status: {selectedCharger.state} &middot; Cooling: {selectedCharger.cooling_state} &middot; Voltage: {selectedCharger.voltage_v} V
              </p>
            </div>
            {selectedCharger.is_affected && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold rounded-lg">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                Active Cyber Target: {selectedCharger.active_event}
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 bg-[#F8FAFC] border border-[#DCE5EF] rounded-lg">
              <span className="text-xs text-[#64748B] block">Delivered Current</span>
              <span className="text-xl font-bold text-[#172033] mt-0.5 block">{selectedCharger.current_a} A</span>
            </div>
            <div className="p-3 bg-[#F8FAFC] border border-[#DCE5EF] rounded-lg">
              <span className="text-xs text-[#64748B] block">Pack Temperature</span>
              <span className="text-xl font-bold text-[#172033] mt-0.5 block">{selectedCharger.battery_temp_c} °C</span>
            </div>
            <div className="p-3 bg-[#F8FAFC] border border-[#DCE5EF] rounded-lg">
              <span className="text-xs text-[#64748B] block">State of Charge</span>
              <span className="text-xl font-bold text-[#172033] mt-0.5 block">{selectedCharger.battery_soc} %</span>
            </div>
            <div className="p-3 bg-[#F8FAFC] border border-[#DCE5EF] rounded-lg">
              <span className="text-xs text-[#64748B] block">Active Power</span>
              <span className="text-xl font-bold text-[#172033] mt-0.5 block">{selectedCharger.power_kw} kW</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
