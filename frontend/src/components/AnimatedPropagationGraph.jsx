import React, { useState, useEffect } from 'react';
import { Layers, ArrowRight, Zap, CheckCircle2, ShieldAlert, Cpu } from 'lucide-react';

export default function AnimatedPropagationGraph({ links = [], activeEventId = null }) {
  const [activeStep, setActiveStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // Selected or primary link
  const selectedLink = links.find((l) => l.event_id === activeEventId) || links[0] || null;
  const path = selectedLink ? selectedLink.dependency_path : [];

  // Reset step on link change
  useEffect(() => {
    setActiveStep(path.length > 0 ? path.length - 1 : 0);
  }, [selectedLink]);

  // Step-by-step animation along the causal path
  useEffect(() => {
    let interval = null;
    if (isPlaying && path.length > 0) {
      interval = setInterval(() => {
        setActiveStep((prev) => {
          if (prev >= path.length - 1) {
            setIsPlaying(false);
            return path.length - 1;
          }
          return prev + 1;
        });
      }, 700);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, path]);

  const COMPONENT_DETAILS = {
    csms_backend: { name: 'CSMS Backend', layer: 'Cyber Protocol', icon: '🌐', desc: 'Central server sending OCPP charging setpoints.' },
    evse_controller: { name: 'EVSE Controller', layer: 'Controller Hardware', icon: '⚡', desc: 'Embedded charger unit regulating power electronic PWM.' },
    power_converter: { name: 'Power Converter', layer: 'Power Electronics', icon: '🔌', desc: 'AC/DC or DC/DC converter delivering charging current.' },
    battery_pack: { name: 'Battery Pack', layer: 'Electrochemical Physical', icon: '🔋', desc: 'Lithium-ion cells subject to Joule heating and IR drop.' },
    cooling_system: { name: 'Cooling Loop', layer: 'Thermal Actuation', icon: '❄️', desc: 'Liquid cooling pump and radiator loop.' },
    temperature_sensor: { name: 'Thermal Sensor', layer: 'Instrumentation', icon: '🌡️', desc: 'Thermistor sensor probe monitoring cell temperatures.' },
    can_bus: { name: 'Vehicle CAN Bus', layer: 'In-Vehicle Network', icon: '🚗', desc: 'Differential bus conveying powertrain telemetry and requests.' },
  };

  return (
    <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E2E8F0] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-[#0891B2]" />
            <h3 className="text-base font-bold text-[#172033]">Animated Causal Propagation Graph (F33)</h3>
          </div>
          <p className="text-xs text-[#52647A] mt-0.5">
            Illuminates verified topological dependency paths from cyber entry to physical actuator response.
          </p>
        </div>

        {path.length > 0 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setActiveStep(0);
                setIsPlaying(true);
              }}
              className="px-3.5 py-1.5 bg-[#0891B2] hover:bg-cyan-700 text-white font-bold text-xs rounded-lg uppercase tracking-wider cursor-pointer shadow-xs transition-all"
            >
              Animate Propagation
            </button>
            <span className="text-xs font-mono text-[#52647A] bg-[#F8FAFC] border border-[#D7E1ED] px-2.5 py-1 rounded-md">
              Step {activeStep + 1} of {path.length}
            </span>
          </div>
        )}
      </div>

      {/* Path Breadcrumb / Sequence */}
      {path.length === 0 ? (
        <div className="py-12 text-center text-sm text-[#52647A]">
          No causal propagation path available for this event.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Visual Node Flow */}
          <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4 py-4">
            {path.map((nodeId, idx) => {
              const nodeInfo = COMPONENT_DETAILS[nodeId] || { name: nodeId, layer: 'Component', icon: '⚙️' };
              const isPassed = idx <= activeStep;
              const isCurrent = idx === activeStep;

              return (
                <React.Fragment key={nodeId}>
                  <div
                    onClick={() => setActiveStep(idx)}
                    className={`relative p-4 rounded-xl border transition-all cursor-pointer min-w-[140px] text-center ${
                      isCurrent
                        ? 'bg-cyan-50 border-[#0891B2] shadow-md ring-2 ring-[#0891B2]/30 scale-105'
                        : isPassed
                        ? 'bg-white border-cyan-300 shadow-xs'
                        : 'bg-slate-50 border-slate-200 opacity-60'
                    }`}
                  >
                    <div className="text-2xl mb-1">{nodeInfo.icon}</div>
                    <span className="text-xs font-bold text-[#172033] block truncate">{nodeInfo.name}</span>
                    <span className="text-[10px] text-[#64748B] block uppercase tracking-wider">{nodeInfo.layer}</span>
                    {isCurrent && (
                      <span className="absolute -top-2 -right-2 px-1.5 py-0.5 bg-[#0891B2] text-white text-[9px] font-bold rounded-full uppercase">
                        Active
                      </span>
                    )}
                  </div>

                  {idx < path.length - 1 && (
                    <div className="flex items-center text-[#94A3B8]">
                      <ArrowRight className={`w-5 h-5 transition-colors ${idx < activeStep ? 'text-[#0891B2]' : 'text-slate-300'}`} />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Active Step Explanatory Card */}
          {path[activeStep] && (
            <div className="p-4 bg-slate-50 border border-[#D7E1ED] rounded-xl flex items-start gap-4">
              <div className="p-2 bg-white rounded-lg border border-[#D7E1ED] text-xl shadow-xs">
                {COMPONENT_DETAILS[path[activeStep]]?.icon || '⚙️'}
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-bold text-[#172033]">
                    Stage {activeStep + 1}: {COMPONENT_DETAILS[path[activeStep]]?.name || path[activeStep]}
                  </h4>
                  <span className="px-2 py-0.5 text-[10px] font-bold bg-cyan-100 text-[#0891B2] rounded-full uppercase tracking-wider">
                    {COMPONENT_DETAILS[path[activeStep]]?.layer || 'System Layer'}
                  </span>
                </div>
                <p className="text-xs text-[#52647A] leading-relaxed">
                  {COMPONENT_DETAILS[path[activeStep]]?.desc || 'Physical-cyber coupling node involved in transmission.'}
                </p>
                {selectedLink && (
                  <p className="text-[11px] font-mono text-[#0891B2] pt-1">
                    Causal Delay to Response: {selectedLink.time_delay}s | Measured Signal Change: {selectedLink.observed_change > 0 ? '+' : ''}{selectedLink.observed_change} {selectedLink.change_unit}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
