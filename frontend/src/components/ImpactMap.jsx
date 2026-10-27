import React from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, Clock, Zap, Thermometer, Radio } from 'lucide-react';

export default function ImpactMap({ currentRun, links = [] }) {
  if (!currentRun) return null;

  const telemetry = currentRun.telemetry || [];
  const events = currentRun.events || [];

  // Compute component impact states
  const peakTemp = currentRun.peak_temperature || 25.0;
  const peakCurrent = currentRun.peak_current || 0.0;
  const faultTriggered = currentRun.fault_triggered || false;

  const components = [
    {
      id: 'csms_backend',
      name: 'CSMS Backend',
      layer: 'Cyber Protocol',
      firstDeviation: events[0] ? `${events[0].timestamp.toFixed(1)}s` : 'None',
      peakValue: `${events.length} commands`,
      status: events.some((e) => e.auth_status === 'unauthorized' || e.auth_status === 'spoofed') ? 'Compromised' : 'Nominal',
      severity: events.some((e) => e.auth_status === 'unauthorized') ? 'High' : 'Low',
      eventRef: events[0]?.event_id || 'N/A'
    },
    {
      id: 'evse_controller',
      name: 'EVSE Controller',
      layer: 'Controller Hardware',
      firstDeviation: events.find((e) => e.event_type.includes('CURRENT') || e.event_type.includes('TRANSACTION')) ? `${events[0]?.timestamp || 5.0}s` : 'None',
      peakValue: `${peakCurrent.toFixed(1)} A target`,
      status: faultTriggered ? 'Tripped (FAULT)' : peakCurrent > 120.0 ? 'Overdrive' : 'Active',
      severity: faultTriggered ? 'Critical' : peakCurrent > 120.0 ? 'High' : 'Low',
      eventRef: events.find((e) => e.target === 'evse_controller' || e.component_id === 'evse_controller')?.event_id || 'EV-01'
    },
    {
      id: 'power_converter',
      name: 'Power Converter',
      layer: 'Power Electronics',
      firstDeviation: peakCurrent > 0 ? `${(events[0]?.timestamp || 5.0) + 1.0}s` : 'None',
      peakValue: `${peakCurrent.toFixed(1)} A actual`,
      status: peakCurrent > 130 ? 'Thermal Stress' : 'Operational',
      severity: peakCurrent > 130 ? 'High' : peakCurrent > 80 ? 'Medium' : 'Low',
      eventRef: 'PWM-GATE'
    },
    {
      id: 'battery_pack',
      name: 'Battery Pack',
      layer: 'Physical / Thermal',
      firstDeviation: peakTemp > 28.0 ? '12.0s' : 'None',
      peakValue: `${peakTemp.toFixed(1)}°C`,
      status: peakTemp >= 60.0 ? 'Critical Thermal Overheat' : peakTemp >= 45.0 ? 'Caution Range' : 'Nominal',
      severity: peakTemp >= 60.0 ? 'Critical' : peakTemp >= 45.0 ? 'High' : 'Low',
      eventRef: links.find((l) => l.target_signal.includes('temp'))?.event_id || 'HEAT-ACCUM'
    },
    {
      id: 'cooling_system',
      name: 'Cooling Loop',
      layer: 'Thermal Actuator',
      firstDeviation: events.some((e) => e.event_type.includes('COOLING')) ? '20.0s' : 'Nominal',
      peakValue: events.some((e) => e.event_type === 'DISABLE_COOLING') ? '0 W (Disabled)' : 'Active (Dissipating)',
      status: events.some((e) => e.event_type === 'DISABLE_COOLING') ? 'Suppressed' : 'Cooling Nominal',
      severity: events.some((e) => e.event_type === 'DISABLE_COOLING') ? 'High' : 'Low',
      eventRef: events.find((e) => e.event_type.includes('COOLING'))?.event_id || 'PUMP-01'
    },
    {
      id: 'temperature_sensor',
      name: 'Temperature Sensor',
      layer: 'Instrumentation',
      firstDeviation: events.some((e) => e.event_type.includes('SENSOR') || e.event_type.includes('CAN_SPOOF')) ? '15.0s' : 'None',
      peakValue: telemetry.some((s) => Math.abs(s.temperature_residual || 0) > 3.0) ? 'Residual Flagged' : 'Coherent',
      status: telemetry.some((s) => s.sensor_quality === 'fault') ? 'Fault / Drift' : 'Good Quality',
      severity: telemetry.some((s) => s.sensor_quality === 'fault') ? 'Medium' : 'Low',
      eventRef: 'ADC-CHANNEL-0'
    }
  ];

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'Critical':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'High':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'Medium':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      default:
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
  };

  return (
    <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E2E8F0] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-[#0891B2]" />
            <h3 className="text-base font-bold text-[#172033]">Component-Level Impact & State Map (F35)</h3>
          </div>
          <p className="text-xs text-[#52647A] mt-0.5">
            Chronological component state progression, onset of physical deviation, and severity categorization.
          </p>
        </div>

        <span className="text-xs font-mono font-bold px-3 py-1 bg-slate-100 text-[#172033] rounded-lg border border-[#D7E1ED]">
          6 Key Components Monitored
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[#D7E1ED] bg-[#F8FAFC] text-[#64748B] uppercase tracking-wider font-semibold">
              <th className="py-3 px-4">Component</th>
              <th className="py-3 px-4">Architecture Layer</th>
              <th className="py-3 px-4">Onset Deviation</th>
              <th className="py-3 px-4">Peak Reading</th>
              <th className="py-3 px-4">Operational State</th>
              <th className="py-3 px-4">Attributed Event</th>
              <th className="py-3 px-4 text-right">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0]">
            {components.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                <td className="py-3 px-4 font-bold text-[#172033]">{c.name}</td>
                <td className="py-3 px-4 text-[#52647A] font-mono">{c.layer}</td>
                <td className="py-3 px-4 text-[#172033] font-mono">{c.firstDeviation}</td>
                <td className="py-3 px-4 font-bold text-[#0891B2] font-mono">{c.peakValue}</td>
                <td className="py-3 px-4 text-[#172033]">{c.status}</td>
                <td className="py-3 px-4 font-mono text-[#52647A]">{c.eventRef}</td>
                <td className="py-3 px-4 text-right">
                  <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${getSeverityBadge(c.severity)}`}>
                    {c.severity}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
