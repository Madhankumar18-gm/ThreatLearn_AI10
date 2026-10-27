import React, { useState } from 'react';
import { Layers, ArrowRight } from 'lucide-react';

const NODE_POSITIONS = {
  // Layer 0: Cyber Protocol
  csms_backend: { x: 50, y: 50, label: 'CSMS Backend', layer: 'Cyber Protocol', color: 'fill-blue-50 stroke-blue-500 text-blue-900' },
  // Layer 1: Controllers
  evse_controller: { x: 270, y: 50, label: 'EVSE Controller', layer: 'Controller Unit', color: 'fill-cyan-50 stroke-cyan-600 text-cyan-900' },
  bms: { x: 270, y: 220, label: 'BMS Controller', layer: 'Controller Unit', color: 'fill-cyan-50 stroke-cyan-600 text-cyan-900' },
  cooling_system: { x: 500, y: 360, label: 'Cooling System', layer: 'Hardware Fluid', color: 'fill-teal-50 stroke-teal-600 text-teal-900' },
  // Layer 2: Power Conversion & Grid
  power_converter: { x: 500, y: 50, label: 'Power Converter', layer: 'AC/DC Hardware', color: 'fill-indigo-50 stroke-indigo-500 text-indigo-900' },
  grid_interface: { x: 50, y: 220, label: 'Grid Feeder', layer: 'Grid Hardware', color: 'fill-slate-50 stroke-slate-400 text-slate-800' },
  // Layer 3: Physical Actuation Signals
  charging_current: { x: 740, y: 50, label: 'Charging Current (I)', layer: 'Physical Signal', color: 'fill-amber-50 stroke-amber-500 text-amber-900' },
  grid_load: { x: 500, y: 220, label: 'Grid Load (kW)', layer: 'Grid Signal', color: 'fill-slate-50 stroke-slate-400 text-slate-800' },
  battery_voltage: { x: 740, y: 190, label: 'Terminal Voltage (V)', layer: 'Physical Signal', color: 'fill-amber-50 stroke-amber-500 text-amber-900' },
  battery_soc: { x: 740, y: 320, label: 'State of Charge (%)', layer: 'Physical Signal', color: 'fill-amber-50 stroke-amber-500 text-amber-900' },
  // Layer 4: Joule Heating & Thermal
  battery_heating: { x: 970, y: 50, label: 'Joule Heating (I²R)', layer: 'Thermal Physics', color: 'fill-orange-50 stroke-orange-500 text-orange-900' },
  cooling_power: { x: 740, y: 440, label: 'Cooling Dissipation', layer: 'Thermal Physics', color: 'fill-teal-50 stroke-teal-600 text-teal-900' },
  battery_temperature: { x: 970, y: 230, label: 'Battery Temp (T)', layer: 'Physical Signal', color: 'fill-rose-50 stroke-rose-500 text-rose-900' },
  // Layer 5: Sensors & Protection
  temperature_sensor: { x: 970, y: 360, label: 'Thermistor ADC', layer: 'Sensor Hardware', color: 'fill-emerald-50 stroke-emerald-600 text-emerald-900' },
  sensor_temperature: { x: 970, y: 470, label: 'Sensor Telemetry', layer: 'Telemetry Data', color: 'fill-emerald-50 stroke-emerald-600 text-emerald-900' },
  bms_protection: { x: 500, y: 470, label: 'BMS Safety Breaker', layer: 'Protection Trip', color: 'fill-red-50 stroke-red-600 text-red-900' },
};

const EDGES = [
  { from: 'csms_backend', to: 'evse_controller' },
  { from: 'evse_controller', to: 'power_converter' },
  { from: 'evse_controller', to: 'cooling_system' },
  { from: 'power_converter', to: 'charging_current' },
  { from: 'charging_current', to: 'battery_heating' },
  { from: 'charging_current', to: 'battery_voltage' },
  { from: 'charging_current', to: 'battery_soc' },
  { from: 'charging_current', to: 'grid_load' },
  { from: 'battery_heating', to: 'battery_temperature' },
  { from: 'cooling_system', to: 'cooling_power' },
  { from: 'cooling_system', to: 'battery_temperature' },
  { from: 'cooling_power', to: 'battery_temperature' },
  { from: 'battery_temperature', to: 'bms_protection' },
  { from: 'battery_temperature', to: 'temperature_sensor' },
  { from: 'temperature_sensor', to: 'sensor_temperature' },
  { from: 'grid_interface', to: 'grid_load' },
  { from: 'bms', to: 'bms_protection' },
];

export default function DependencyGraphView({ highlightedPath = [] }) {
  const [selectedNode, setSelectedNode] = useState(null);

  const isEdgeHighlighted = (u, v) => {
    if (!highlightedPath || highlightedPath.length < 2) return false;
    for (let i = 0; i < highlightedPath.length - 1; i++) {
      if (highlightedPath[i] === u && highlightedPath[i + 1] === v) return true;
    }
    return false;
  };

  const isNodeHighlighted = (nodeId) => {
    return highlightedPath && highlightedPath.includes(nodeId);
  };

  return (
    <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-8 shadow-xs space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#EDF2F7]">
        <div>
          <h3 className="text-xl font-bold font-mono text-[#172033] flex items-center gap-2.5">
            <Layers className="w-5 h-5 text-[#0891B2]" />
            Component Causal Dependency Graph (Feature F20)
          </h3>
          <p className="text-sm text-[#52647A] mt-1">
            NetworkX directed causal topology. Candidate cyber-to-physical links require an admissible directed path in the graph.
          </p>
        </div>

        {highlightedPath && highlightedPath.length > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#E6FAFF] border border-[#0891B2]/40 text-xs sm:text-sm font-mono text-[#0891B2] shadow-2xs">
            <span className="font-bold">Active Causal Path:</span>
            {highlightedPath.map((p, idx) => (
              <React.Fragment key={p}>
                <span className="bg-white px-2 py-0.5 rounded text-xs font-semibold border border-[#0891B2]/20 text-[#172033]">
                  {p}
                </span>
                {idx < highlightedPath.length - 1 && <ArrowRight className="w-3.5 h-3.5 text-[#0891B2]" />}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* SVG Canvas with light styling and full container expansion */}
      <div className="relative overflow-x-auto w-full bg-[#F8FAFC] rounded-2xl p-5 border border-[#D7E1ED]">
        <svg viewBox="0 0 1160 560" className="w-full min-w-[1000px] h-auto select-none">
          <defs>
            <marker
              id="arrow-light"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#94A3B8" />
            </marker>
            <marker
              id="arrow-active-light"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#0891B2" />
            </marker>
          </defs>

          {/* Edges */}
          {EDGES.map((edge) => {
            const u = NODE_POSITIONS[edge.from];
            const v = NODE_POSITIONS[edge.to];
            if (!u || !v) return null;
            const highlighted = isEdgeHighlighted(edge.from, edge.to);

            return (
              <line
                key={`${edge.from}->${edge.to}`}
                x1={u.x + 72}
                y1={u.y + 24}
                x2={v.x + 72}
                y2={v.y + 24}
                stroke={highlighted ? '#0891B2' : '#CBD5E1'}
                strokeWidth={highlighted ? 3.5 : 1.8}
                strokeDasharray={highlighted ? 'none' : '4 3'}
                markerEnd={highlighted ? 'url(#arrow-active-light)' : 'url(#arrow-light)'}
                className={highlighted ? 'transition-all duration-300 drop-shadow-[0_2px_4px_rgba(8,145,178,0.25)]' : 'transition-colors'}
              />
            );
          })}

          {/* Nodes */}
          {Object.entries(NODE_POSITIONS).map(([id, node]) => {
            const highlighted = isNodeHighlighted(id);
            const isSelected = selectedNode === id;

            return (
              <g
                key={id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => setSelectedNode(id)}
                className="cursor-pointer group"
              >
                <rect
                  width="145"
                  height="48"
                  rx="10"
                  className={`transition-all duration-200 ${
                    highlighted
                      ? 'fill-[#E6FAFF] stroke-[#0891B2] stroke-[2.5] shadow-md'
                      : isSelected
                      ? 'fill-cyan-50 stroke-[#0891B2] stroke-[2]'
                      : `${node.color} stroke-[1.8] hover:stroke-cyan-500 hover:shadow-xs`
                  }`}
                />
                <text
                  x="72"
                  y="20"
                  textAnchor="middle"
                  className={`text-[12px] font-mono font-bold select-none ${
                    highlighted ? 'fill-[#0891B2]' : 'fill-[#172033]'
                  }`}
                >
                  {node.label}
                </text>
                <text
                  x="72"
                  y="36"
                  textAnchor="middle"
                  className="text-[10px] font-sans fill-[#52647A] select-none"
                >
                  {node.layer}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
