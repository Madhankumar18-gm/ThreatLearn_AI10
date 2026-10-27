import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Award, CheckCircle2, AlertTriangle, TrendingUp, Cpu, Clock, Layers, ShieldCheck, RefreshCw } from 'lucide-react';

export default function EvaluationScorecard() {
  const [split, setSplit] = useState('tuning');
  const [seed, setSeed] = useState(42);
  const [scorecard, setScorecard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchScorecard = async (splitName = split, seedVal = seed) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await api.getEvaluationBenchmark(splitName, seedVal);
      setScorecard(data);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to fetch evaluation benchmark');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScorecard(split, seed);
  }, [split]);

  return (
    <div className="w-full space-y-8 pb-12 animate-page-enter">
      {/* Top Banner */}
      <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-8 shadow-xs flex flex-wrap items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-6 h-6 text-[#0891B2]" />
            <h1 className="text-xl sm:text-2xl font-bold text-[#172033] tracking-tight">
              Evaluation Scorecard & Held-Out Benchmarks (F44, F45, F46)
            </h1>
          </div>
          <p className="text-sm text-[#52647A] mt-1 max-w-2xl leading-relaxed">
            Quantitative evaluation of causal attribution precision, recall, and false-link rates across tuning and held-out scenario splits compared to a naive 60-second spike heuristic baseline.
          </p>
        </div>

        {/* Split Switcher & Refresh */}
        <div className="flex items-center gap-3">
          <div className="flex bg-[#F8FAFC] border border-[#D7E1ED] rounded-xl p-1">
            <button
              onClick={() => setSplit('tuning')}
              className={`px-4 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${
                split === 'tuning' ? 'bg-[#0891B2] text-white shadow-xs' : 'text-[#52647A] hover:text-[#172033]'
              }`}
            >
              Tuning Split
            </button>
            <button
              onClick={() => setSplit('held_out')}
              className={`px-4 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${
                split === 'held_out' ? 'bg-[#0891B2] text-white shadow-xs' : 'text-[#52647A] hover:text-[#172033]'
              }`}
            >
              Held-Out Split (F45)
            </button>
          </div>

          <button
            onClick={() => fetchScorecard(split, seed)}
            disabled={loading}
            className="p-2.5 bg-slate-100 hover:bg-slate-200 border border-[#D7E1ED] rounded-xl text-[#172033] cursor-pointer"
            title="Re-run Benchmark Evaluation"
          >
            <RefreshCw className={`w-4 h-4 text-[#0891B2] ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {loading && !scorecard && (
        <div className="py-24 text-center text-sm text-[#52647A]">
          Evaluating benchmark scenarios across deterministic engine...
        </div>
      )}

      {scorecard && (
        <div className="space-y-8">
          {/* Core Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 font-mono">
            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs">
              <span className="text-[11px] font-sans font-semibold text-[#64748B] uppercase tracking-wider block">
                Precision
              </span>
              <span className="text-2xl font-bold text-emerald-600 block mt-1">
                {(scorecard.precision * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-[#52647A] font-sans">True links vs total linked</span>
            </div>

            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs">
              <span className="text-[11px] font-sans font-semibold text-[#64748B] uppercase tracking-wider block">
                Recall
              </span>
              <span className="text-2xl font-bold text-[#0891B2] block mt-1">
                {(scorecard.recall * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-[#52647A] font-sans">Coverage of true causes</span>
            </div>

            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs">
              <span className="text-[11px] font-sans font-semibold text-[#64748B] uppercase tracking-wider block">
                F1 Score
              </span>
              <span className="text-2xl font-bold text-[#172033] block mt-1">
                {scorecard.f1_score.toFixed(3)}
              </span>
              <span className="text-[10px] text-[#52647A] font-sans">Harmonic mean balance</span>
            </div>

            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs">
              <span className="text-[11px] font-sans font-semibold text-[#64748B] uppercase tracking-wider block">
                False Link Rate
              </span>
              <span className="text-2xl font-bold text-emerald-600 block mt-1">
                {(scorecard.false_link_rate * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-[#52647A] font-sans">Spurious link suppression</span>
            </div>

            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs">
              <span className="text-[11px] font-sans font-semibold text-[#64748B] uppercase tracking-wider block">
                Class Accuracy
              </span>
              <span className="text-2xl font-bold text-[#2563EB] block mt-1">
                {(scorecard.classification_accuracy * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-[#52647A] font-sans">Rule classifier (No leakage)</span>
            </div>

            <div className="bg-white border border-[#D7E1ED] rounded-2xl p-5 shadow-xs">
              <span className="text-[11px] font-sans font-semibold text-[#64748B] uppercase tracking-wider block">
                Replay Agreement
              </span>
              <span className="text-2xl font-bold text-[#0891B2] block mt-1">
                {(scorecard.counterfactual_agreement * 100).toFixed(0)}%
              </span>
              <span className="text-[10px] text-[#52647A] font-sans">Counterfactual validation</span>
            </div>
          </div>

          {/* Side-by-Side Comparison against Naive 60s Baseline */}
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
            <div className="border-b border-[#E2E8F0] pb-3">
              <h3 className="text-base font-bold text-[#172033]">
                Baseline Comparison: ThreatLens Multi-Factor Engine vs. Naive 60s Spike Heuristic (F46)
              </h3>
              <p className="text-xs text-[#52647A] mt-0.5">
                The baseline naively attributes any cyber event occurring within 60 seconds before an electrical spike, generating severe false-link rates.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#D7E1ED] bg-[#F8FAFC] text-[#64748B] uppercase tracking-wider font-semibold">
                    <th className="py-3 px-4">Metric</th>
                    <th className="py-3 px-4 text-[#0891B2]">ThreatLens Engine</th>
                    <th className="py-3 px-4 text-slate-500">60s Window Baseline</th>
                    <th className="py-3 px-4 text-emerald-600">Differential (&Delta;)</th>
                    <th className="py-3 px-4">Methodology Interpretation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {Object.entries(scorecard.baseline_comparison || {}).map(([metricKey, item]) => (
                    <tr key={metricKey} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-bold text-[#172033] capitalize">{metricKey.replace(/_/g, ' ')}</td>
                      <td className="py-3 px-4 font-mono font-bold text-[#0891B2]">{item.threatlens_value}</td>
                      <td className="py-3 px-4 font-mono text-slate-500">{item.baseline_60s_spike_value}</td>
                      <td className="py-3 px-4 font-mono font-bold text-emerald-600">
                        {item.differential > 0 ? `+${item.differential}` : item.differential}
                      </td>
                      <td className="py-3 px-4 text-[#52647A]">{item.interpretation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Latency Distinction (Physical Delay vs Software Execution Speed) */}
          <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-4">
            <div className="border-b border-[#E2E8F0] pb-3">
              <h3 className="text-base font-bold text-[#172033] flex items-center gap-2">
                <Clock className="w-5 h-5 text-[#0891B2]" /> Latency Distinction: Physical Heat Transfer vs. Software Runtime (F44)
              </h3>
              <p className="text-xs text-[#52647A] mt-0.5">
                ThreatLens enforces a rigorous operational distinction between physical event-to-damage propagation delays and algorithm computation speed.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <span className="text-[11px] font-sans font-semibold text-[#64748B] uppercase tracking-wider block">
                  Physical Response Delay (Thermal Conduction & Charging Ramp)
                </span>
                <span className="text-2xl font-bold text-[#172033]">
                  {scorecard.avg_physical_delay_seconds} seconds
                </span>
                <p className="text-[11px] text-[#52647A] font-sans">
                  Measured delay from cyber command execution to measurable temperature/current threshold crossing.
                </p>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <span className="text-[11px] font-sans font-semibold text-[#64748B] uppercase tracking-wider block">
                  Software Computation Latency (ThreatLens Graph & Correlation)
                </span>
                <span className="text-2xl font-bold text-[#0891B2]">
                  {scorecard.avg_software_computation_ms} ms (P95: {scorecard.p95_software_computation_ms} ms)
                </span>
                <p className="text-[11px] text-[#52647A] font-sans">
                  Execution time of graph traversal, physics residual computation, and confidence scoring.
                </p>
              </div>
            </div>

            <div className="p-3.5 bg-cyan-50 border border-cyan-200 rounded-xl text-xs text-cyan-900 leading-relaxed font-sans">
              <strong>Methodology Note:</strong> {scorecard.methodology_notes}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
