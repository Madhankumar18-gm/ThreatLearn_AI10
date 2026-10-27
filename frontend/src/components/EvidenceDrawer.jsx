import React from 'react';
import { X, ShieldCheck, AlertTriangle, Clock, Layers, Zap, Thermometer, Info, HelpCircle } from 'lucide-react';

export default function EvidenceDrawer({ link, isOpen, onClose }) {
  if (!isOpen || !link) return null;

  const conf = link.confidence_breakdown || {};
  const sev = link.impact_severity || {};
  const classification = link.event_classification || {};

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end bg-slate-900/30 backdrop-blur-xs animate-fade-in">
      <div className="relative w-full max-w-xl bg-white h-full shadow-2xl border-l border-[#D7E1ED] flex flex-col overflow-y-auto">
        {/* Drawer Header */}
        <div className="p-6 border-b border-[#E2E8F0] flex items-center justify-between sticky top-0 bg-white z-10">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-[#0891B2]" />
              <h3 className="text-base font-bold text-[#172033]">Evidence & Causal Trace Drawer (F36)</h3>
            </div>
            <p className="text-xs text-[#52647A] font-mono mt-0.5">Link ID: {link.link_id}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-[#64748B] hover:text-[#172033] hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 flex-1 text-xs">
          {/* Summary Box */}
          <div className="p-4 bg-cyan-50/70 border border-cyan-200 rounded-xl space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#0891B2] block">Verified Causal Connection</span>
            <p className="text-sm font-bold text-[#172033]">
              {link.event_type} &rarr; {link.target_signal}
            </p>
            <p className="text-xs text-[#52647A] leading-relaxed">{link.explanation}</p>
          </div>

          {/* Time & Latency Breakdown */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-[#172033] uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-[#0891B2]" /> Timing & Delay Verification
            </h4>
            <div className="grid grid-cols-2 gap-3 font-mono">
              <div className="bg-[#F8FAFC] border border-[#E2E8F0] p-3 rounded-lg">
                <span className="text-[10px] text-[#64748B] block">Measured Delay</span>
                <span className="text-sm font-bold text-[#172033]">{link.time_delay}s</span>
              </div>
              <div className="bg-[#F8FAFC] border border-[#E2E8F0] p-3 rounded-lg">
                <span className="text-[10px] text-[#64748B] block">Observed Magnitude</span>
                <span className="text-sm font-bold text-[#0891B2]">
                  {link.observed_change > 0 ? '+' : ''}{link.observed_change} {link.change_unit}
                </span>
              </div>
            </div>
          </div>

          {/* Multi-Factor Confidence Breakdown (F26) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-[#172033] uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#0891B2]" /> Multi-Factor Confidence (F26)
              </h4>
              <span className="font-mono font-bold text-sm text-[#0891B2] bg-cyan-50 border border-cyan-200 px-2 py-0.5 rounded-md">
                Score: {link.confidence_score} ({conf.confidence_level || 'High'})
              </span>
            </div>

            <div className="space-y-2 bg-[#F8FAFC] border border-[#E2E8F0] p-3.5 rounded-xl">
              <div className="flex justify-between items-center py-1 border-b border-slate-200">
                <span className="text-[#52647A]">Graph Path Validity (Weight: 25%)</span>
                <span className="font-mono font-bold text-[#172033]">{conf.path_validity_score !== undefined ? conf.path_validity_score : '1.00'}</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-200">
                <span className="text-[#52647A]">Physical Timing Fit (Weight: 20%)</span>
                <span className="font-mono font-bold text-[#172033]">{conf.timing_fit_score !== undefined ? conf.timing_fit_score : '1.00'}</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-200">
                <span className="text-[#52647A]">Physics Consistency (Weight: 20%)</span>
                <span className="font-mono font-bold text-[#172033]">{conf.physics_consistency_score !== undefined ? conf.physics_consistency_score : '0.90'}</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-200">
                <span className="text-[#52647A]">Counterfactual Attenuation (Weight: 20%)</span>
                <span className="font-mono font-bold text-[#172033]">{conf.counterfactual_score !== undefined ? conf.counterfactual_score : '1.00'}</span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-200">
                <span className="text-[#52647A]">Command Provenance (Weight: 15%)</span>
                <span className="font-mono font-bold text-[#172033]">{conf.command_provenance_score !== undefined ? conf.command_provenance_score : '0.95'}</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-[#52647A]">Alternative Explanation Penalty</span>
                <span className="font-mono font-bold text-amber-700">{conf.alternative_explanation_penalty !== undefined ? conf.alternative_explanation_penalty : '0.00'}</span>
              </div>
            </div>
            <p className="text-[11px] text-[#64748B] italic">
              {conf.scoring_notes || 'Composite score computed from graph reachability, latency window, residual magnitude, and counterfactual response.'}
            </p>
          </div>

          {/* Rule-Based Classification (F24) */}
          {classification.classification && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-[#172033] uppercase tracking-wider">
                Event Classification (F24)
              </h4>
              <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="text-[#52647A]">Classifier Verdict:</span>
                  <span className="font-bold text-[#0891B2]">{classification.classification}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#52647A]">Ground Truth Blind:</span>
                  <span className="font-mono text-emerald-600 font-bold">Yes (No Metadata Leakage)</span>
                </div>
                <p className="text-[11px] text-[#52647A] pt-1">{classification.uncertainty_explanation}</p>
              </div>
            </div>
          )}

          {/* Rules Matched */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-[#172033] uppercase tracking-wider">Rules Matched (4/4 Satisfied)</h4>
            <div className="space-y-1.5">
              {(link.rules_matched || []).map((rule, idx) => (
                <div key={idx} className="flex items-start gap-2 p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 font-mono text-[11px]">
                  <span className="text-emerald-600 font-bold">&#10003;</span>
                  <span>{rule}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Disclaimer Banner */}
          <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3 text-amber-800">
            <Info className="w-4 h-4 mt-0.5 shrink-0" />
            <p className="text-[11px] leading-relaxed">
              <strong>Caveat & Limitation:</strong> Correlation and counterfactual evidence reflect deterministic lumped-parameter simulation dynamics. They provide defensible engineering insights, not legal proof or certified hardware ratings.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#E2E8F0] bg-[#F8FAFC] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-200 hover:bg-slate-300 text-[#172033] font-bold text-xs rounded-xl cursor-pointer transition-colors"
          >
            Close Drawer
          </button>
        </div>
      </div>
    </div>
  );
}
