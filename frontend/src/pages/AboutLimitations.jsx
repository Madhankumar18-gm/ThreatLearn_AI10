import React from 'react';
import {
  HelpCircle,
  AlertTriangle,
  ShieldAlert,
  Cpu,
  Layers,
  Thermometer,
  Zap,
  CheckCircle2,
  FileText,
  Shield
} from 'lucide-react';
import SimulationBadge from '../components/SimulationBadge';

export default function AboutLimitations() {
  return (
    <div className="w-full space-y-8 pb-16 animate-page-enter">
      {/* Title (Full Width) */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-4">
          <h2 className="text-3xl sm:text-4xl font-bold font-mono text-[#172033] flex items-center gap-3">
            <HelpCircle className="w-8 h-8 text-[#0891B2]" />
            About ThreatLens & Scientific Limitations (Feature F48)
          </h2>
          <SimulationBadge />
        </div>
        <p className="text-sm sm:text-base text-[#52647A]">
          Transparent documentation of physical equations, illustrative parameters, safe-by-design guarantees, and scientific boundary conditions for ThreatLens.
        </p>
      </div>

      {/* Mandatory Limitations Callout Box (Feature F48) */}
      <div className="w-full rounded-2xl border-2 border-amber-300 bg-amber-50/80 p-7 sm:p-8 space-y-5 shadow-xs">
        <div className="flex items-center gap-3 text-amber-900 font-mono text-base sm:text-lg font-bold uppercase tracking-wider">
          <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0" />
          Mandatory Platform Limitations & Safety Disclaimers (Feature F48)
        </div>

        <ul className="space-y-3.5 text-sm sm:text-base text-amber-950 leading-relaxed font-sans list-disc list-inside">
          <li>
            <strong>Defensive Testing Only:</strong> ThreatLens is a simulation-based testing, forensic exploration, and analytical research tool. It is <strong>not</strong> a real-time electrical protection system, hardware interlock, or physical safety breaker.
          </li>
          <li>
            <strong>Simplified Physics Model:</strong> The physical thermal and battery models utilize lumped-capacitance differential equations and engineering approximations. They have <strong>not been established as laboratory-certified</strong> for production EV battery warranty validation.
          </li>
          <li>
            <strong>In-Model Counterfactual Proof:</strong> Counterfactual replay establishes proof of causality <strong>strictly within the boundaries of this mathematical simulation model</strong>. It does not constitute certified proof of physical hardware immunity against live electrical hazards.
          </li>
          <li>
            <strong>Real-World Deployment Prerequisites:</strong> Any transition from simulation testing to live charging station infrastructure requires real calibrated telemetry, hardware-in-the-loop (HIL) bench validation, formal safety engineering reviews, and adherence to electrical codes (NEC, IEC 61851, ISO 15118).
          </li>
        </ul>
      </div>

      {/* Mathematical Physical Equations (Full Width) */}
      <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-7 sm:p-8 space-y-6 shadow-xs">
        <h3 className="text-xl sm:text-2xl font-bold font-mono text-[#172033] flex items-center gap-3">
          <Thermometer className="w-6 h-6 text-[#0891B2]" />
          Governing Physical & Thermal Equations (Features F07, F08)
        </h3>

        {/* Thermal Equation */}
        <div className="space-y-3 bg-[#F8FAFC] rounded-xl p-5 sm:p-6 border border-[#D7E1ED] font-mono">
          <span className="text-xs sm:text-sm text-[#0891B2] font-bold block uppercase tracking-wide">
            1. Lumped Thermal Capacitance with Convective Cooling
          </span>
          <div className="py-3 text-center text-base sm:text-lg lg:text-xl text-[#172033] font-bold tracking-wider font-mono">
            C_thermal × (dT / dt) = I² × R_batt − ((T − T_ambient) / R_thermal) × κ_cooling
          </div>
          <div className="text-xs sm:text-sm text-[#52647A] space-y-1.5 font-sans border-t border-[#D7E1ED] pt-3">
            <p><strong>C_thermal</strong> = Lumped pack module heat capacity (2400.0 J/K calibrated baseline)</p>
            <p><strong>I² × R_batt</strong> = Internal Joule heating generation (Watts)</p>
            <p><strong>R_thermal</strong> = Thermal resistance to ambient / cooling interface (0.05 K/W)</p>
            <p><strong>κ_cooling</strong> = Cooling efficiency multiplier (1.0 = normal, 0.0 = total valve shutdown/failure)</p>
            <p><strong>Thresholds</strong> = 45.0°C (BMS Warning), 60.0°C (BMS Safety Cutoff Trip)</p>
          </div>
        </div>

        {/* Battery Electrical Equation */}
        <div className="space-y-3 bg-[#F8FAFC] rounded-xl p-5 sm:p-6 border border-[#D7E1ED] font-mono">
          <span className="text-xs sm:text-sm text-[#0891B2] font-bold block uppercase tracking-wide">
            2. Battery Electrical Terminal Voltage with IR Drop
          </span>
          <div className="py-3 text-center text-base sm:text-lg lg:text-xl text-[#172033] font-bold tracking-wider font-mono">
            V_terminal(t) = V_ocv(SoC) + I(t) × R_batt
          </div>
          <div className="text-xs sm:text-sm text-[#52647A] space-y-1.5 font-sans border-t border-[#D7E1ED] pt-3">
            <p><strong>V_ocv(SoC)</strong> = 350.0 + 70.0 × (SoC / 100) + 4.0 × sin(π × SoC / 100) Volts</p>
            <p><strong>R_batt</strong> = 0.035 Ω (nominal internal cell resistance)</p>
            <p><strong>SoC Integration</strong> = SoC(t) = SoC(0) + ∫ (I(t) × η_coulombic / (C_Ah × 3600)) dt × 100%</p>
          </div>
        </div>

        {/* State Machine */}
        <div className="space-y-3 bg-[#F8FAFC] rounded-xl p-5 sm:p-6 border border-[#D7E1ED] font-mono">
          <span className="text-xs sm:text-sm text-[#0891B2] font-bold block uppercase tracking-wide">
            3. EV Charger State Machine & Limits (Feature F06)
          </span>
          <p className="text-sm sm:text-base text-[#172033] font-sans leading-relaxed">
            States: <strong>IDLE</strong> → <strong>AUTHORIZED</strong> → <strong>CHARGING</strong> → <strong>FAULT</strong>. Actual output current is clamped by:
          </p>
          <div className="py-2 text-center text-base sm:text-lg text-[#0891B2] font-bold">
            I_actual = min(I_requested, I_hardware_max, I_bms_limit)
          </div>
          <p className="text-xs sm:text-sm text-[#52647A] font-sans">
            Under simulated BMS override attacks, the software limit is bypassed until pack temperature reaches the 60.0°C critical threshold, at which point an independent hardware breaker forces a transition to FAULT.
          </p>
        </div>
      </div>

      {/* Safe-by-Design Architecture (Feature F15) */}
      <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-7 sm:p-8 space-y-6 shadow-xs">
        <h3 className="text-xl sm:text-2xl font-bold font-mono text-[#172033] flex items-center gap-3">
          <ShieldAlert className="w-6 h-6 text-[#0891B2]" />
          Safe-by-Design Architecture & Whitelist (Feature F15)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm font-mono text-[#172033]">
          <div className="p-6 rounded-xl bg-[#F8FAFC] border border-[#D7E1ED] space-y-3">
            <span className="text-base text-[#0891B2] font-bold block">Whitelisted Simulated Event Types:</span>
            <ul className="space-y-2 text-sm text-[#52647A]">
              <li>• START_TRANSACTION / STOP_TRANSACTION</li>
              <li>• CHANGE_CURRENT_LIMIT / SET_CHARGING_PROFILE</li>
              <li>• BMS_OVERRIDE_ATTEMPT</li>
              <li>• COOLING_OVERRIDE</li>
              <li>• SENSOR_INJECT_FAULT</li>
              <li>• FIRMWARE_UPDATE</li>
              <li>• EMERGENCY_STOP</li>
              <li>• GRID_LIMIT_UPDATE</li>
            </ul>
          </div>

          <div className="p-6 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-3">
            <span className="text-base text-emerald-800 font-bold block">Enforced Safety Controls:</span>
            <ul className="space-y-2 text-sm text-emerald-950 font-sans">
              <li>• <strong>No Real Exploits:</strong> Zero shell execution, eval, or live socket connectivity.</li>
              <li>• <strong>Strict Range Validation:</strong> Rejects negative seeds and out-of-range durations.</li>
              <li>• <strong>Persistent Badge:</strong> Visual SIMULATION MODE banner across all screens.</li>
              <li>• <strong>Isolated Replay:</strong> Single-event subtraction with bitwise seed consistency.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
