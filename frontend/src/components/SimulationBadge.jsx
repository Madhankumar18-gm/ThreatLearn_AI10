import React from 'react';
import { ShieldAlert } from 'lucide-react';

export default function SimulationBadge({ className = '' }) {
  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border border-amber-300 bg-amber-50 text-amber-800 text-xs font-mono font-medium tracking-wide shadow-sm select-none ${className}`}
      title="Safe-by-Design simulation environment. All telemetry and events are synthetic model computations; no live electrical or physical exploits."
    >
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
      </span>
      <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
      <span className="font-semibold uppercase tracking-wider text-[11px]">Simulation Mode</span>
      <span className="hidden sm:inline text-amber-700/80 border-l border-amber-300 pl-2 text-[10px] font-sans">
        Synthetic Testbed
      </span>
    </div>
  );
}
