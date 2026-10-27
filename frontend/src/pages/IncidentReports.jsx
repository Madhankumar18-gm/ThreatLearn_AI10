import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  FileText, Download, CheckSquare, Square, ShieldAlert, 
  HelpCircle, CheckCircle, RefreshCw, AlertTriangle, Eye, ArrowRight
} from 'lucide-react';

export default function IncidentReports() {
  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [narrative, setNarrative] = useState(null);
  const [checkedActions, setCheckedActions] = useState({});
  const [error, setError] = useState(null);
  const [downloadingFormat, setDownloadingFormat] = useState(null);

  useEffect(() => {
    loadRuns();
  }, []);

  const loadRuns = async () => {
    try {
      setLoading(true);
      const fetchedRuns = await api.getRuns(30);
      setRuns(fetchedRuns);
      if (fetchedRuns.length > 0) {
        setSelectedRunId(fetchedRuns[0].run_id);
        fetchNarrative(fetchedRuns[0].run_id);
      }
    } catch (err) {
      setError(err.message || 'Failed to load incident runs');
    } finally {
      setLoading(false);
    }
  };

  const fetchNarrative = async (runId) => {
    if (!runId) return;
    try {
      setGenerating(true);
      setError(null);
      const nar = await api.getRunNarrative(runId);
      setNarrative(nar);
      setCheckedActions({});
    } catch (err) {
      setError(err.message || 'Failed to generate incident narrative');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (format) => {
    if (!selectedRunId) return;
    try {
      setDownloadingFormat(format);
      if (format === 'pdf') {
        await api.downloadPdfReport(selectedRunId);
      } else {
        await api.downloadMarkdownReport(selectedRunId);
      }
    } catch (err) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setDownloadingFormat(null);
    }
  };

  const toggleCheck = (idx) => {
    setCheckedActions(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-cyan-600 font-medium">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Loading Incident Reports...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-[#DCE5EF] rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-50 text-cyan-700 border border-cyan-200">
                Features F42, F43
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                Evidence-Grounded PDF / Markdown
              </span>
            </div>
            <h1 className="text-2xl font-bold text-[#172033]">
              Incident Reports & Grounded Narrative
            </h1>
            <p className="text-sm text-[#64748B] mt-1 max-w-3xl">
              Export verified, evidence-grounded reports using deterministic calibrated language 
              (Observed &middot; Inferred &middot; Uncertain). Never hallucinates real-world attribution.
            </p>
          </div>

          {/* Download Actions */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => handleDownload('markdown')}
              disabled={downloadingFormat !== null || !selectedRunId}
              className="flex items-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium text-xs transition-colors border border-slate-300 shadow-2xs disabled:opacity-50"
            >
              <Download className="w-4 h-4 text-slate-600" />
              {downloadingFormat === 'markdown' ? 'Exporting...' : 'Export Markdown (.md)'}
            </button>
            <button
              onClick={() => handleDownload('pdf')}
              disabled={downloadingFormat !== null || !selectedRunId}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#0891B2] hover:bg-[#0e7490] text-white rounded-lg font-medium text-xs transition-colors shadow-sm disabled:opacity-50"
            >
              <FileText className="w-4 h-4" />
              {downloadingFormat === 'pdf' ? 'Generating PDF...' : 'Download PDF Report (.pdf)'}
            </button>
          </div>
        </div>

        {/* Run Selector */}
        <div className="mt-6 border-t border-[#DCE5EF] pt-4">
          <label className="text-xs font-bold uppercase tracking-wider text-[#64748B] mb-1.5 block">
            Select Incident Run for Investigation Report
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <select
              value={selectedRunId}
              onChange={(e) => {
                setSelectedRunId(e.target.value);
                fetchNarrative(e.target.value);
              }}
              className="flex-1 px-3.5 py-2 bg-[#F8FAFC] border border-[#DCE5EF] rounded-lg text-sm text-[#172033] font-medium focus:outline-hidden focus:ring-2 focus:ring-[#0891B2]"
            >
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id} &middot; {r.scenario_name} (Peak: {r.peak_temperature}°C &middot; {r.classification || 'Run'})
                </option>
              ))}
            </select>
            <button
              onClick={() => fetchNarrative(selectedRunId)}
              disabled={generating}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition-colors border border-slate-300 flex items-center gap-1.5"
            >
              <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Generated Report Narrative Viewer */}
      {narrative && (
        <div className="space-y-6">
          {/* Executive Summary Card */}
          <div className="bg-white border border-[#DCE5EF] rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-600">
                Executive Finding
              </span>
              <span className="text-xs font-mono text-[#64748B]">
                Doc ID: {narrative.narrative_id}
              </span>
            </div>
            <h2 className="text-lg font-bold text-[#172033] mb-2">
              Incident Investigation: {narrative.run_id}
            </h2>
            <p className="text-sm text-slate-700 leading-relaxed bg-[#F8FAFC] p-4 rounded-lg border border-[#E2E8F0]">
              {narrative.executive_summary}
            </p>
          </div>

          {/* Calibrated Language Sections */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Section 1: Observed */}
            <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-emerald-700 font-bold text-sm border-b border-[#DCE5EF] pb-2">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                <span>1. OBSERVED (Direct Physical Measurements)</span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                {narrative.observations_section}
              </p>
            </div>

            {/* Section 2: Inferred */}
            <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-blue-700 font-bold text-sm border-b border-[#DCE5EF] pb-2">
                <Eye className="w-4 h-4 text-blue-600" />
                <span>2. INFERRED (Graph Path & Physics Rules)</span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                {narrative.inferred_causal_relationships}
              </p>
            </div>

            {/* Section 3: Uncertain */}
            <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-amber-700 font-bold text-sm border-b border-[#DCE5EF] pb-2">
                <HelpCircle className="w-4 h-4 text-amber-600" />
                <span>3. UNCERTAIN (Alternative Non-Attack Hypotheses)</span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                {narrative.uncertainties_and_alternatives}
              </p>
            </div>

            {/* Section 4: Counterfactual Proof */}
            <div className="bg-white border border-[#DCE5EF] rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-purple-700 font-bold text-sm border-b border-[#DCE5EF] pb-2">
                <ShieldAlert className="w-4 h-4 text-purple-600" />
                <span>4. COUNTERFACTUAL PROOF (&Delta; Excision Replay)</span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                {narrative.counterfactual_proof_statement}
              </p>
            </div>
          </div>

          {/* Investigator Action Checklist */}
          <div className="bg-white border border-[#DCE5EF] rounded-xl p-6 shadow-sm">
            <h3 className="text-base font-bold text-[#172033] mb-1 flex items-center gap-2">
              <CheckSquare className="w-5 h-5 text-cyan-600" />
              Investigator Verification Checklist
            </h3>
            <p className="text-xs text-[#64748B] mb-4">
              Ground-truth physical inspection steps required to confirm digital findings.
            </p>

            <div className="space-y-2.5">
              {narrative.recommended_investigative_actions.map((act, idx) => {
                const isDone = !!checkedActions[idx];
                return (
                  <div
                    key={idx}
                    onClick={() => toggleCheck(idx)}
                    className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                      isDone 
                        ? 'bg-emerald-50/50 border-emerald-200 text-emerald-900 line-through opacity-75' 
                        : 'bg-[#F8FAFC] border-[#DCE5EF] text-slate-800 hover:bg-white'
                    }`}
                  >
                    <button className="mt-0.5 text-cyan-700">
                      {isDone ? <CheckSquare className="w-4 h-4 text-emerald-600" /> : <Square className="w-4 h-4 text-slate-400" />}
                    </button>
                    <span className="text-xs font-medium leading-relaxed">
                      {act}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Evidence Registry */}
          <div className="bg-white border border-[#DCE5EF] rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-[#172033] mb-3">
              Referenced Evidence Registry Tokens ({narrative.referenced_evidence_ids.length} Logged)
            </h3>
            <div className="flex flex-wrap gap-2">
              {narrative.referenced_evidence_ids.map((eid, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-md text-[11px] font-mono font-medium bg-slate-100 text-slate-700 border border-slate-300"
                >
                  {eid}
                </span>
              ))}
            </div>
          </div>

          {/* Safety Disclaimer */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-slate-600 text-xs italic leading-relaxed">
            {narrative.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
}
