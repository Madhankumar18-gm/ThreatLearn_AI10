import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, FastForward, SkipForward, SkipBack, Zap, Thermometer, Activity, ShieldCheck } from 'lucide-react';

export default function ReplaySlider({ telemetry = [], events = [], onTimeChange, currentTime = 0 }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const maxTime = telemetry.length > 0 ? telemetry[telemetry.length - 1].timestamp : 60;
  const timerRef = useRef(null);

  // Playback loop
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        onTimeChange((prev) => {
          if (prev >= maxTime) {
            setIsPlaying(false);
            return maxTime;
          }
          return Math.min(maxTime, Math.round((prev + 1) * 10) / 10);
        });
      }, 1000 / speed);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, speed, maxTime, onTimeChange]);

  // Find telemetry slice for current time
  const currentSlice = telemetry.find((s) => Math.abs(s.timestamp - currentTime) < 0.5) || telemetry[0] || {};
  const activeEvents = events.filter((e) => Math.abs(e.timestamp - currentTime) < 1.0);

  const handleSliderChange = (e) => {
    const val = parseFloat(e.target.value);
    onTimeChange(val);
  };

  const jumpToEvent = (evtTime) => {
    onTimeChange(evtTime);
  };

  return (
    <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E2E8F0] pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-50 rounded-lg text-[#0891B2]">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-[#172033] tracking-wide">Interactive Replay Scrubber (F34)</h4>
            <p className="text-xs text-[#52647A]">Scrub pre-computed deterministic telemetry without re-simulation.</p>
          </div>
        </div>

        {/* Playback Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onTimeChange((t) => Math.max(0, t - 1))}
            className="p-2 rounded-lg bg-[#F8FAFC] border border-[#D7E1ED] hover:bg-slate-100 text-[#172033] cursor-pointer"
            title="Step Back 1s"
          >
            <SkipBack className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`px-3.5 py-2 rounded-lg font-bold text-xs uppercase tracking-wider flex items-center gap-2 cursor-pointer transition-all ${
              isPlaying
                ? 'bg-amber-600 hover:bg-amber-700 text-white shadow-xs'
                : 'bg-[#0891B2] hover:bg-cyan-700 text-white shadow-xs'
            }`}
          >
            {isPlaying ? (
              <>
                <Pause className="w-4 h-4" /> Pause
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" /> Play Replay
              </>
            )}
          </button>

          <button
            onClick={() => onTimeChange((t) => Math.min(maxTime, t + 1))}
            className="p-2 rounded-lg bg-[#F8FAFC] border border-[#D7E1ED] hover:bg-slate-100 text-[#172033] cursor-pointer"
            title="Step Forward 1s"
          >
            <SkipForward className="w-4 h-4" />
          </button>

          <button
            onClick={() => {
              setIsPlaying(false);
              onTimeChange(0);
            }}
            className="p-2 rounded-lg bg-[#F8FAFC] border border-[#D7E1ED] hover:bg-slate-100 text-[#52647A] cursor-pointer"
            title="Reset to 0s"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          {/* Speed Selectors */}
          <div className="flex items-center gap-1 ml-2 bg-[#F8FAFC] border border-[#D7E1ED] rounded-lg p-0.5">
            {[0.5, 1, 2, 5].map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`px-2 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                  speed === s ? 'bg-[#0891B2] text-white shadow-xs' : 'text-[#52647A] hover:text-[#172033]'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Track & Time Markers */}
      <div className="space-y-2">
        <div className="flex justify-between items-center text-xs font-mono font-medium text-[#52647A]">
          <span>0.0s (Start)</span>
          <span className="text-base font-bold text-[#0891B2] bg-cyan-50 border border-cyan-200 px-3 py-0.5 rounded-full">
            t = {currentTime.toFixed(1)}s / {maxTime.toFixed(1)}s
          </span>
          <span>{maxTime.toFixed(1)}s (End)</span>
        </div>

        {/* Range Slider */}
        <div className="relative py-1">
          <input
            type="range"
            min="0"
            max={maxTime}
            step="1"
            value={currentTime}
            onChange={handleSliderChange}
            className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#0891B2]"
          />

          {/* Event Anchors on Track */}
          <div className="relative w-full h-3">
            {events.map((ev) => {
              const leftPercent = Math.min(100, Math.max(0, (ev.timestamp / maxTime) * 100));
              return (
                <button
                  key={ev.event_id}
                  onClick={() => jumpToEvent(ev.timestamp)}
                  style={{ left: `${leftPercent}%` }}
                  className="absolute top-0 -translate-x-1/2 w-2.5 h-2.5 bg-amber-500 rounded-full hover:scale-150 transition-transform cursor-pointer shadow-xs"
                  title={`Jump to ${ev.event_type} at ${ev.timestamp}s`}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* Instantaneous Values Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
        <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3">
          <span className="text-[11px] font-semibold text-[#64748B] uppercase tracking-wider block">Physical Temp</span>
          <span className="text-lg font-bold text-[#172033] font-mono">
            {currentSlice.battery_temperature !== undefined ? `${currentSlice.battery_temperature.toFixed(1)}°C` : '--'}
          </span>
        </div>

        <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3">
          <span className="text-[11px] font-semibold text-[#64748B] uppercase tracking-wider block">Sensor Reading</span>
          <span className="text-lg font-bold text-[#0891B2] font-mono">
            {currentSlice.sensor_temperature !== undefined ? `${currentSlice.sensor_temperature.toFixed(1)}°C` : `${(currentSlice.battery_temperature || 25).toFixed(1)}°C`}
          </span>
        </div>

        <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3">
          <span className="text-[11px] font-semibold text-[#64748B] uppercase tracking-wider block">Charging Current</span>
          <span className="text-lg font-bold text-[#2563EB] font-mono">
            {currentSlice.charging_current !== undefined ? `${currentSlice.charging_current.toFixed(1)} A` : '--'}
          </span>
        </div>

        <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3">
          <span className="text-[11px] font-semibold text-[#64748B] uppercase tracking-wider block">Twin Residual</span>
          <span className={`text-lg font-bold font-mono ${
            Math.abs(currentSlice.temperature_residual || 0) > 3.0 ? 'text-amber-600' : 'text-emerald-600'
          }`}>
            {currentSlice.temperature_residual !== undefined ? `${currentSlice.temperature_residual > 0 ? '+' : ''}${currentSlice.temperature_residual.toFixed(2)}°C` : '0.00°C'}
          </span>
        </div>

        <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3">
          <span className="text-[11px] font-semibold text-[#64748B] uppercase tracking-wider block">Charger State</span>
          <span className={`text-sm font-bold font-mono mt-1 inline-block ${
            currentSlice.charger_state === 'FAULT' ? 'text-red-600' : 'text-[#0891B2]'
          }`}>
            {currentSlice.charger_state || 'IDLE'}
          </span>
        </div>

        <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3">
          <span className="text-[11px] font-semibold text-[#64748B] uppercase tracking-wider block">Sensor Health</span>
          <span className={`text-sm font-bold font-mono mt-1 inline-block capitalize ${
            currentSlice.sensor_quality === 'fault' || currentSlice.sensor_quality === 'dropout'
              ? 'text-red-600'
              : currentSlice.sensor_quality === 'suspect'
              ? 'text-amber-600'
              : 'text-emerald-600'
          }`}>
            {currentSlice.sensor_quality || 'Good'}
          </span>
        </div>
      </div>

      {/* Active Events at this Timestamp */}
      {activeEvents.length > 0 && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between text-xs text-amber-900">
          <div className="flex items-center gap-2">
            <span className="font-bold uppercase tracking-wider px-2 py-0.5 bg-amber-200 rounded-md">Event Active</span>
            <span className="font-mono font-medium">{activeEvents[0].event_type} ({activeEvents[0].event_id})</span>
            <span className="text-amber-700 font-sans">— {activeEvents[0].description || JSON.stringify(activeEvents[0].details)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
