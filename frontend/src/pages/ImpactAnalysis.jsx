import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Layers,
  ArrowRight,
  ShieldAlert,
  HelpCircle,
  CheckCircle2,
  AlertCircle,
  GitCompare,
  ExternalLink,
  ShieldCheck
} from 'lucide-react';
import { api } from '../services/api';
import DependencyGraphView from '../components/DependencyGraphView';

export default function ImpactAnalysis({
  currentRun,
  setActiveTab,
  onSelectEventForReplay
}) {
  const [links, setLinks] = useState([]);
  const [selectedLink, setSelectedLink] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadLinks() {
      if (!currentRun) return;
      setLoading(true);
      try {
        const data = await api.getRunLinks(currentRun.run_id);
        setLinks(data || []);
        if (data && data.length > 0) {
          setSelectedLink(data[0]);
        }
      } catch (err) {
        console.error('Failed to load correlation links', err);
      } finally {
        setLoading(false);
      }
    }
    loadLinks();
  }, [currentRun]);

  if (!currentRun) {
    return (
      <div className="w-full py-24 text-center space-y-5 bg-white rounded-2xl border border-[#D7E1ED] p-12 shadow-xs">
        <div className="w-18 h-18 rounded-2xl bg-slate-100 border border-[#D7E1ED] flex items-center justify-center mx-auto text-[#52647A]">
          <Cpu className="w-9 h-9 text-[#52647A]" />
        </div>
        <h3 className="text-xl font-bold text-[#172033] font-mono">No Active Incident Loaded</h3>
        <p className="text-sm text-[#52647A] max-w-lg mx-auto">
          Please run a simulation to inspect component dependencies and rule-based causal correlation links.
        </p>
        <button
          onClick={() => setActiveTab('scenario-lab')}
          className="px-6 py-3.5 bg-[#0891B2] hover:bg-cyan-700 text-white font-bold text-sm rounded-xl uppercase tracking-wider shadow-sm transition-all cursor-pointer"
        >
          Open Scenario Lab
        </button>
      </div>
    );
  }

  const getEvidenceBadge = (label) => {
    if (label === 'Observed') {
      return (
        <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200">
          Observed
        </span>
      );
    }
    if (label === 'Inferred') {
      return (
        <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200">
          Inferred
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-slate-100 text-slate-700 border border-slate-300">
        Uncertain
      </span>
    );
  };

  return (
    <div className="w-full space-y-8 pb-12 animate-page-enter">
      {/* Page Title & Incident Info (Full Viewport Width) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl sm:text-4xl font-bold font-mono text-[#172033] flex items-center gap-3">
            <Cpu className="w-8 h-8 text-[#0891B2]" />
            Causal Impact Analysis (Features F20, F21, F29)
          </h2>
          <p className="text-sm sm:text-base text-[#52647A] mt-1">
            Grounded rule-based correlation engine. Temporal precedence alone is never treated as proof of causation.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <span className="text-sm font-mono text-[#52647A]">Active Incident:</span>
          <span className="text-sm font-mono font-bold text-[#0891B2] bg-[#E6FAFF] px-3.5 py-1.5 rounded-lg border border-[#0891B2]/30">
            {currentRun.run_id} ({currentRun.scenario_id})
          </span>
        </div>
      </div>

      {/* Component Dependency Graph */}
      <DependencyGraphView highlightedPath={selectedLink?.dependency_path || []} />

      {/* Correlated Event-to-Impact Links Table & Deep Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Links Table (7 cols) */}
        <div className="lg:col-span-7 bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-7 space-y-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-[#EDF2F7] pb-4">
            <div>
              <h3 className="text-base sm:text-lg font-bold text-[#172033] font-mono flex items-center gap-2.5">
                <Layers className="w-5 h-5 text-[#0891B2]" />
                Correlated Event-to-Impact Links ({links.length})
              </h3>
              <p className="text-xs sm:text-sm text-[#52647A] mt-0.5">
                Filtered by graph path existence, signal compatibility, physical delay, and noise margin.
              </p>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12 text-sm font-mono text-[#52647A]">
              Evaluating causal correlation rules...
            </div>
          ) : links.length === 0 ? (
            <div className="text-center py-12 text-sm font-mono text-[#52647A] bg-[#F8FAFC] rounded-xl p-8 border border-[#D7E1ED]">
              No causal links detected exceeding noise threshold for this scenario run.
            </div>
          ) : (
            <div className="overflow-x-auto border border-[#D7E1ED] rounded-xl">
              <table className="w-full text-left text-xs sm:text-sm text-[#172033]">
                <thead className="bg-[#F8FAFC] text-[#52647A] font-mono uppercase text-xs border-b border-[#D7E1ED]">
                  <tr>
                    <th className="py-3.5 px-4">Event ID</th>
                    <th className="py-3.5 px-4">Event Type</th>
                    <th className="py-3.5 px-4">Target Signal</th>
                    <th className="py-3.5 px-4">Delay</th>
                    <th className="py-3.5 px-4">Delta (Δ)</th>
                    <th className="py-3.5 px-4">Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#D7E1ED] font-mono">
                  {links.map((link) => {
                    const isSelected = selectedLink?.link_id === link.link_id;
                    return (
                      <tr
                        key={link.link_id}
                        onClick={() => setSelectedLink(link)}
                        className={`transition-colors cursor-pointer ${
                          isSelected
                            ? 'bg-[#E6FAFF] text-[#172033] font-semibold border-l-4 border-l-[#0891B2]'
                            : 'hover:bg-[#F8FAFC] text-[#172033]'
                        }`}
                      >
                        <td className="py-3.5 px-4 font-bold text-[#0891B2]">{link.event_id}</td>
                        <td className="py-3.5 px-4 font-sans font-medium">{link.event_type}</td>
                        <td className="py-3.5 px-4 text-[#52647A]">{link.target_signal}</td>
                        <td className="py-3.5 px-4 text-[#52647A]">{link.time_delay}s</td>
                        <td className="py-3.5 px-4 font-bold text-amber-700">
                          {link.observed_change > 0 ? `+${link.observed_change}` : link.observed_change} {link.change_unit}
                        </td>
                        <td className="py-3.5 px-4">{getEvidenceBadge(link.evidence_label)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right: Selected Link Deep Inspector & Evidence Explainability (5 cols) */}
        <div className="lg:col-span-5 bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-7 space-y-6 shadow-xs">
          {selectedLink ? (
            <>
              <div className="border-b border-[#EDF2F7] pb-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-mono font-bold text-[#0891B2]">
                    Link: {selectedLink.link_id}
                  </span>
                  {getEvidenceBadge(selectedLink.evidence_label)}
                </div>
                <h4 className="text-lg font-bold text-[#172033] font-mono">
                  {selectedLink.event_id} → {selectedLink.target_signal}
                </h4>
                <div className="flex items-center gap-3 text-xs sm:text-sm text-[#52647A]">
                  <span>Confidence Score:</span>
                  <span className="font-mono font-bold text-[#172033]">
                    {(selectedLink.confidence_score * 100).toFixed(0)}%
                  </span>
                  <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#0891B2] rounded-full"
                      style={{ width: `${selectedLink.confidence_score * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Verified Graph Path */}
              <div className="space-y-2">
                <span className="text-xs sm:text-sm font-semibold text-[#172033] font-mono block">
                  Verified Directed Path (Feature F20):
                </span>
                <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#D7E1ED] text-xs sm:text-sm font-mono text-[#172033] break-words flex flex-wrap items-center gap-2">
                  {selectedLink.dependency_path.map((node, i) => (
                    <React.Fragment key={node}>
                      <span className="bg-white px-2.5 py-1 rounded-md border border-[#D7E1ED] text-[#172033] font-medium shadow-2xs">
                        {node}
                      </span>
                      {i < selectedLink.dependency_path.length - 1 && (
                        <span className="text-[#0891B2] font-bold">→</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Rules Matched */}
              <div className="space-y-2">
                <span className="text-xs sm:text-sm font-semibold text-[#172033] font-mono block">
                  Rule Evaluation Proof (Feature F21):
                </span>
                <div className="space-y-2">
                  {selectedLink.rules_matched.map((rule, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs sm:text-sm font-mono text-emerald-900 flex items-start gap-2.5"
                    >
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                      <span>{rule}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Physics Explanation */}
              <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#D7E1ED] space-y-1.5">
                <span className="text-xs sm:text-sm font-mono text-[#0891B2] font-bold block">
                  Causal Explanation:
                </span>
                <p className="text-xs sm:text-sm text-[#172033] leading-relaxed">
                  {selectedLink.explanation}
                </p>
              </div>

              {/* Uncertainty Notes */}
              {selectedLink.uncertainty_notes && (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-1.5">
                  <span className="text-xs sm:text-sm font-mono text-amber-800 font-bold flex items-center gap-1.5">
                    <HelpCircle className="w-4 h-4 text-amber-600" />
                    Uncertainty & Verification Notes:
                  </span>
                  <p className="text-xs sm:text-sm text-amber-900 leading-relaxed font-sans">
                    {selectedLink.uncertainty_notes}
                  </p>
                </div>
              )}

              {/* Prove Causality Trigger Button */}
              <button
                onClick={() => onSelectEventForReplay(selectedLink.event_id)}
                className="w-full py-3.5 rounded-xl bg-[#0891B2] hover:bg-cyan-700 text-white font-bold text-sm uppercase tracking-wider flex items-center justify-center gap-2.5 shadow-sm hover:shadow transition-all cursor-pointer"
              >
                <GitCompare className="w-5 h-5" />
                Prove Causality with Counterfactual Replay
              </button>
            </>
          ) : (
            <div className="text-center py-24 text-sm font-mono text-[#52647A]">
              Select a correlation link from the table to view rule satisfaction details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
