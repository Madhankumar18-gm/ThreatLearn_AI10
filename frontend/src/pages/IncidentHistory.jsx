import React, { useState, useEffect } from 'react';
import {
  History,
  RotateCcw,
  Search,
  Database,
  ExternalLink,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';

export default function IncidentHistory({ onLoadRun, setActiveTab }) {
  const [runs, setRuns] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await api.getRuns(100);
      setRuns(data || []);
    } catch (err) {
      console.error('Failed to load incident history', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const filteredRuns = runs.filter((r) => {
    return (
      r.run_id.toLowerCase().includes(search.toLowerCase()) ||
      r.scenario_name.toLowerCase().includes(search.toLowerCase()) ||
      r.scenario_id.toLowerCase().includes(search.toLowerCase()) ||
      r.scenario_family.toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <div className="w-full space-y-8 pb-12 animate-page-enter">
      {/* Header (Full Width) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl sm:text-4xl font-bold font-mono text-[#172033] flex items-center gap-3">
              <History className="w-8 h-8 text-[#0891B2]" />
              Incident History (Feature F51)
            </h2>
            <span className="px-3 py-1 rounded-full text-xs font-mono bg-emerald-50 border border-emerald-200 text-emerald-800 font-bold flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" /> SQLite Persisted
            </span>
          </div>
          <p className="text-sm sm:text-base text-[#52647A] mt-1.5">
            Historical incidents survive backend restarts. All telemetry, cyber events, and counterfactuals are permanently stored.
          </p>
        </div>

        <div className="flex items-center gap-3.5">
          <div className="relative w-full md:w-80">
            <Search className="w-5 h-5 text-[#94A3B8] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search run ID or scenario..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-white border border-[#D7E1ED] rounded-xl text-sm sm:text-base font-mono text-[#172033] placeholder-[#94A3B8] focus:outline-none focus:border-[#0891B2] focus:ring-1 focus:ring-[#0891B2] shadow-xs"
            />
          </div>

          <button
            onClick={fetchRuns}
            className="p-3 rounded-xl bg-white hover:bg-slate-50 text-[#52647A] hover:text-[#172033] border border-[#D7E1ED] transition-colors cursor-pointer shadow-xs"
            title="Refresh history from SQLite"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Runs Table (Full Width) */}
      <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl overflow-hidden shadow-xs">
        {loading ? (
          <div className="text-center py-20 text-[#52647A] text-sm font-mono">
            Loading incident history from SQLite...
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="text-center py-20 text-[#52647A] text-sm font-mono">
            No incident records found. Run a simulation from the Scenario Lab to generate records.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm sm:text-base text-[#172033]">
              <thead className="bg-[#F8FAFC] text-[#52647A] font-mono uppercase text-xs border-b border-[#D7E1ED]">
                <tr>
                  <th className="py-4 px-5">Run ID</th>
                  <th className="py-4 px-5">Scenario ID & Title</th>
                  <th className="py-4 px-5">Family</th>
                  <th className="py-4 px-5">Seed</th>
                  <th className="py-4 px-5">Peak Current</th>
                  <th className="py-4 px-5">Peak Temp</th>
                  <th className="py-4 px-5">Protection Status</th>
                  <th className="py-4 px-5">Created (UTC)</th>
                  <th className="py-4 px-5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D7E1ED] font-mono">
                {filteredRuns.map((r) => (
                  <tr key={r.run_id} className="hover:bg-[#F8FAFC] transition-colors">
                    <td className="py-4 px-5 font-bold text-[#0891B2]">
                      {r.run_id}
                      {r.is_counterfactual && (
                        <span className="ml-2 px-2 py-0.5 rounded bg-amber-50 text-amber-800 text-xs border border-amber-200">
                          CF
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-5 text-[#172033] font-sans">
                      <span className="font-mono text-[#0891B2] mr-2 font-bold">{r.scenario_id}</span>
                      {r.scenario_name}
                    </td>
                    <td className="py-4 px-5 text-[#52647A]">{r.scenario_family}</td>
                    <td className="py-4 px-5 text-[#52647A]">{r.seed}</td>
                    <td className="py-4 px-5 text-[#0891B2] font-bold">{r.peak_current} A</td>
                    <td className="py-4 px-5 text-rose-600 font-bold">{r.peak_temperature} °C</td>
                    <td className="py-4 px-5">
                      {r.fault_triggered ? (
                        <span className="px-2.5 py-1 rounded-md bg-red-100 border border-red-200 text-red-800 text-xs font-bold">
                          FAULT TRIP
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold">
                          NORMAL
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-5 text-xs text-[#52647A]">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td className="py-4 px-5 text-right">
                      <button
                        onClick={() => onLoadRun(r.run_id)}
                        className="px-4 py-1.5 rounded-lg bg-[#E6FAFF] hover:bg-[#0891B2] text-[#0891B2] hover:text-white border border-[#0891B2]/30 text-xs sm:text-sm font-sans font-semibold transition-all cursor-pointer shadow-2xs"
                      >
                        Load Incident
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
