import React, { useState } from 'react';
import { api } from '../services/api';
import { Upload, FileText, CheckCircle2, AlertTriangle, ArrowRight, Clock, Database, Sparkles, XCircle } from 'lucide-react';

export default function ImportWizard({ setActiveTab }) {
  const [fileContent, setFileContent] = useState('');
  const [fileName, setFileName] = useState('');
  const [preview, setPreview] = useState(null);
  const [clockOffset, setClockOffset] = useState(0.0);
  const [validationReport, setValidationReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const sampleCSV = `timestamp,component_id,signal,value,unit,quality
2026-10-26T09:00:00Z,evse_controller,charging_current,0.0,A,GOOD
2026-10-26T09:00:01Z,battery_pack,battery_temperature,24.5,C,GOOD
2026-10-26T09:00:02Z,battery_pack,battery_voltage,398.2,V,GOOD
2026-10-26T09:00:03Z,bms,state_of_charge,45.0,%,GOOD
2026-10-26T09:00:04Z,grid_meter,grid_load,15.2,kW,GOOD
2026-10-26T09:00:05Z,evse_controller,charging_current,32.0,A,GOOD
2026-10-26T09:00:06Z,power_converter,cooling_power,1.2,kW,GOOD
2026-10-26T09:00:07Z,battery_pack,battery_temperature,24.8,C,GOOD
2026-10-26T09:00:08Z,battery_pack,battery_voltage,400.1,V,GOOD
2026-10-26T09:00:09Z,grid_meter,grid_load,28.4,kW,GOOD
2026-10-26T09:00:10Z,evse_controller,charging_current,65.0,A,GOOD
2026-10-26T09:00:11Z,bms,state_of_charge,45.2,%,GOOD
2026-10-26T09:00:12Z,power_converter,cooling_power,2.0,kW,GOOD
2026-10-26T09:00:13Z,battery_pack,battery_temperature,25.3,C,GOOD
2026-10-26T09:00:14Z,battery_pack,battery_voltage,401.5,V,GOOD
2026-10-26T09:00:15Z,evse_controller,charging_current,80.0,A,GOOD
2026-10-26T09:00:16Z,grid_meter,grid_load,35.0,kW,GOOD
2026-10-26T09:00:17Z,battery_pack,battery_temperature,26.1,C,GOOD
2026-10-26T09:00:18Z,bms,state_of_charge,45.5,%,GOOD
2026-10-26T09:00:19Z,power_converter,cooling_power,2.8,kW,GOOD
2026-10-26T09:00:20Z,evse_controller,charging_current,100.0,A,GOOD
2026-10-26T09:00:21Z,battery_pack,battery_temperature,27.0,C,GOOD
2026-10-26T09:00:22Z,battery_pack,battery_voltage,402.8,V,GOOD
2026-10-26T09:00:23Z,grid_meter,grid_load,42.5,kW,GOOD
2026-10-26T09:00:24Z,bms,state_of_charge,45.9,%,GOOD
2026-10-26T09:00:25Z,power_converter,cooling_power,3.4,kW,GOOD
2026-10-26T09:00:26Z,evse_controller,charging_current,125.0,A,GOOD
2026-10-26T09:00:27Z,battery_pack,battery_temperature,28.2,C,GOOD
2026-10-26T09:00:28Z,battery_pack,battery_voltage,403.9,V,GOOD
2026-10-26T09:00:29Z,grid_meter,grid_load,50.8,kW,GOOD
2026-10-26T09:00:30Z,bms,state_of_charge,46.4,%,GOOD
2026-10-26T09:00:31Z,power_converter,cooling_power,4.1,kW,GOOD
2026-10-26T09:00:32Z,battery_pack,battery_temperature,29.5,C,GOOD
2026-10-26T09:00:33Z,evse_controller,charging_current,125.0,A,GOOD
2026-10-26T09:00:34Z,battery_pack,battery_voltage,404.2,V,GOOD
2026-10-26T09:00:35Z,bms,state_of_charge,47.0,%,GOOD
2026-10-26T09:00:36Z,power_converter,cooling_power,4.5,kW,GOOD
2026-10-26T09:00:37Z,battery_pack,battery_temperature,31.0,C,GOOD
2026-10-26T09:00:38Z,grid_meter,grid_load,50.2,kW,GOOD
2026-10-26T09:00:39Z,battery_pack,battery_temperature,32.8,C,GOOD`;

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = async (event) => {
      const text = event.target.result;
      setFileContent(text);
      await runPreview(file.name, text);
    };
    reader.readAsText(file);
  };

  const loadSample = async () => {
    setFileName('threatlens_sample_telemetry.csv');
    setFileContent(sampleCSV);
    await runPreview('threatlens_sample_telemetry.csv', sampleCSV);
  };

  const runPreview = async (name, content) => {
    setLoading(true);
    setErrorMsg(null);
    setValidationReport(null);
    try {
      const res = await api.previewCSV(name, content);
      setPreview(res);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to parse CSV preview');
    } finally {
      setLoading(false);
    }
  };

  const handleCommit = async () => {
    if (!preview) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const payload = {
        filename: fileName || 'threatlens_sample_telemetry.csv',
        data_type: preview.detected_data_type || 'telemetry',
        mapping: preview.inferred_mapping,
        raw_content: fileContent,
        rows: preview.sample_rows,
        clock_skew_offset: parseFloat(clockOffset || 0)
      };
      const report = await api.commitIngestion(payload);
      setValidationReport(report);
    } catch (err) {
      setErrorMsg(err.message || 'Validation and commit failed');
    } finally {
      setLoading(false);
    }
  };

  const formatAlignedTime = (row, tsCol, offsetNum) => {
    const raw = row[tsCol];
    if (!raw) return '0.00s';
    const s = String(raw).trim();
    if (s.includes('T') || s.includes('-') || s.includes(':')) {
      const parsedDate = Date.parse(s.endsWith('Z') ? s : s + 'Z');
      if (!isNaN(parsedDate)) {
        const baseStr = preview?.base_timestamp || preview?.sample_rows?.[0]?.[tsCol] || s;
        const baseDate = Date.parse(baseStr.endsWith('Z') ? baseStr : baseStr + 'Z');
        const elapsedSec = isNaN(baseDate) ? 0 : Math.max(0, (parsedDate - baseDate) / 1000);
        const alignedSec = (elapsedSec + offsetNum).toFixed(2);
        const alignedDate = new Date(parsedDate + offsetNum * 1000);
        const timePart = alignedDate.toISOString().substring(11, 19);
        return `${alignedSec}s (${timePart}Z)`;
      }
    }
    const num = parseFloat(s);
    if (!isNaN(num)) {
      return `${Math.max(0, num + offsetNum).toFixed(2)}s`;
    }
    return `${offsetNum.toFixed(2)}s`;
  };

  return (
    <div className="w-full space-y-8 pb-12 animate-page-enter">
      {/* Top Banner */}
      <div className="w-full bg-white border border-[#D7E1ED] rounded-2xl p-6 sm:p-8 shadow-xs flex flex-wrap items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <Upload className="w-6 h-6 text-[#0891B2]" />
            <h1 className="text-xl sm:text-2xl font-bold text-[#172033] tracking-tight">
              CSV & Telemetry Ingestion Wizard (F17, F19)
            </h1>
          </div>
          <p className="text-sm text-[#52647A] mt-1 max-w-2xl leading-relaxed">
            Upload external CSV logs, auto-map headers to the ThreatLens canonical format, apply timestamp alignment offsets, and validate schema consistency.
          </p>
        </div>

        <button
          onClick={loadSample}
          className="px-4 py-2.5 bg-cyan-50 hover:bg-cyan-100 text-[#0891B2] font-bold text-xs uppercase tracking-wider rounded-xl flex items-center gap-2 border border-cyan-200 cursor-pointer shadow-xs transition-all"
        >
          <Sparkles className="w-4 h-4" /> Load Sample Telemetry CSV (40 Rows)
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Upload Dropzone */}
      <div className="bg-white border-2 border-dashed border-[#D7E1ED] hover:border-[#0891B2] rounded-2xl p-8 text-center transition-all bg-[#F8FAFC]">
        <input
          type="file"
          accept=".csv,.txt"
          onChange={handleFileUpload}
          id="csv-file-input"
          className="hidden"
        />
        <label htmlFor="csv-file-input" className="cursor-pointer space-y-3 block">
          <FileText className="w-12 h-12 text-[#0891B2] mx-auto" />
          <div className="text-sm font-bold text-[#172033]">
            {fileName ? fileName : 'Click to upload or drag & drop CSV telemetry/log file'}
          </div>
          <p className="text-xs text-[#52647A]">
            Supports standard tabular logs with timestamp, component, signal, and value columns.
          </p>
        </label>
      </div>

      {/* Preview & Column Mapping Section */}
      {preview && (
        <div className="bg-white border border-[#D7E1ED] rounded-2xl p-6 shadow-xs space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E2E8F0] pb-4">
            <div>
              <h3 className="text-base font-bold text-[#172033]">Inferred Schema & Column Mapping</h3>
              <p className="text-xs text-[#52647A] font-mono mt-0.5">
                Total Rows: <span className="font-bold text-[#172033]">{preview.total_rows}</span> | Detected Stream: <span className="font-bold text-[#0891B2] uppercase">{preview.detected_data_type}</span> | Format: <span className="font-mono text-slate-700">{preview.time_format || 'standard'}</span>
              </p>
            </div>

            {/* Time Alignment Clock Offset (F19) */}
            <div className="flex items-center gap-3">
              <Clock className="w-4 h-4 text-[#0891B2]" />
              <label className="text-xs font-semibold text-[#172033]">Clock Skew Offset (s):</label>
              <input
                type="number"
                step="0.5"
                value={clockOffset}
                onChange={(e) => setClockOffset(e.target.value)}
                className="w-20 px-2 py-1 bg-[#F8FAFC] border border-[#D7E1ED] rounded-lg text-xs font-mono text-[#172033]"
              />
            </div>
          </div>

          {/* Mapping Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
            <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl">
              <span className="text-[10px] text-[#64748B] block font-semibold">Timestamp Column</span>
              <span className="font-mono font-bold text-[#0891B2]">{preview.inferred_mapping.timestamp_col}</span>
            </div>
            <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl">
              <span className="text-[10px] text-[#64748B] block font-semibold">Component Column</span>
              <span className="font-mono font-bold text-[#172033]">{preview.inferred_mapping.component_col || '(Optional)'}</span>
            </div>
            <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl">
              <span className="text-[10px] text-[#64748B] block font-semibold">Signal Column</span>
              <span className="font-mono font-bold text-[#172033]">{preview.inferred_mapping.signal_col || '(Optional)'}</span>
            </div>
            <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl">
              <span className="text-[10px] text-[#64748B] block font-semibold">Value Column</span>
              <span className="font-mono font-bold text-[#172033]">{preview.inferred_mapping.value_col || '(Optional)'}</span>
            </div>
            <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl">
              <span className="text-[10px] text-[#64748B] block font-semibold">Unit Column</span>
              <span className="font-mono font-bold text-[#172033]">{preview.inferred_mapping.unit_col || '(Optional)'}</span>
            </div>
            <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl">
              <span className="text-[10px] text-[#64748B] block font-semibold">Quality Column</span>
              <span className="font-mono font-bold text-[#0891B2]">{preview.inferred_mapping.quality_col || '(Optional)'}</span>
            </div>
          </div>

          {/* Sample Rows Table */}
          <div className="space-y-2">
            <div className="text-xs text-[#64748B] flex justify-between items-center">
              <span>Showing preview of first <strong>{preview.sample_rows.length}</strong> rows (out of <strong>{preview.total_rows}</strong> total records)</span>
              {preview.base_timestamp && (
                <span className="font-mono text-[11px] text-[#0891B2]">Base Time: {preview.base_timestamp}</span>
              )}
            </div>
            <div className="overflow-x-auto border border-[#E2E8F0] rounded-xl">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#D7E1ED] bg-[#F8FAFC] text-[#64748B] uppercase tracking-wider font-semibold">
                    {preview.headers.map((h) => (
                      <th key={h} className="py-2.5 px-3 font-mono">{h}</th>
                    ))}
                    <th className="py-2.5 px-3 font-mono text-[#0891B2]">Aligned Elapsed Time (F19)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {preview.sample_rows.map((row, idx) => {
                    const offsetNum = parseFloat(clockOffset || 0);
                    const formattedTime = formatAlignedTime(row, preview.inferred_mapping.timestamp_col, offsetNum);
                    return (
                      <tr key={idx} className="hover:bg-slate-50 font-mono">
                        {preview.headers.map((h) => (
                          <td key={h} className="py-2.5 px-3 text-[#172033]">{row[h]}</td>
                        ))}
                        <td className="py-2.5 px-3 font-bold text-[#0891B2]">{formattedTime}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Commit Button */}
          <div className="flex justify-end pt-2">
            <button
              onClick={handleCommit}
              disabled={loading}
              className="px-6 py-2.5 bg-[#0891B2] hover:bg-cyan-700 text-white font-bold text-xs uppercase tracking-wider rounded-xl flex items-center gap-2 cursor-pointer shadow-sm transition-all"
            >
              <Database className="w-4 h-4" />
              {loading ? 'Validating All Rows...' : `Validate & Commit All ${preview.total_rows} Rows`}
            </button>
          </div>
        </div>
      )}

      {/* Validation Report */}
      {validationReport && (
        <div className={`bg-white border ${validationReport.rejected_rows_count === 0 ? 'border-emerald-200 bg-emerald-50/20' : 'border-amber-200 bg-amber-50/20'} rounded-2xl p-6 shadow-xs space-y-4`}>
          <div className="flex items-center gap-2 text-emerald-800">
            {validationReport.rejected_rows_count === 0 ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-amber-600" />
            )}
            <h3 className="text-base font-bold text-[#172033]">Ingestion & Schema Validation Report</h3>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3 bg-white border border-[#D7E1ED] rounded-xl">
              <span className="text-[10px] text-[#64748B] block font-sans">Dataset ID</span>
              <span className="font-bold text-[#0891B2]">{validationReport.dataset_id}</span>
            </div>
            <div className="p-3 bg-white border border-[#D7E1ED] rounded-xl">
              <span className="text-[10px] text-[#64748B] block font-sans">Total Submitted</span>
              <span className="font-bold text-[#172033]">{validationReport.total_submitted}</span>
            </div>
            <div className="p-3 bg-white border border-[#D7E1ED] rounded-xl">
              <span className="text-[10px] text-[#64748B] block font-sans">Total Valid Rows</span>
              <span className="font-bold text-emerald-600">{validationReport.valid_rows_count}</span>
            </div>
            <div className="p-3 bg-white border border-[#D7E1ED] rounded-xl">
              <span className="text-[10px] text-[#64748B] block font-sans">Rejected Rows</span>
              <span className={`font-bold ${validationReport.rejected_rows_count > 0 ? 'text-red-600' : 'text-slate-700'}`}>
                {validationReport.rejected_rows_count}
              </span>
            </div>
          </div>

          <div className="p-3.5 bg-white border border-[#D7E1ED] rounded-xl text-xs font-mono flex flex-wrap items-center justify-between gap-2">
            <div>
              <span className="text-[10px] text-[#64748B] block font-sans uppercase font-semibold">Aligned Time Window</span>
              <span className="font-bold text-[#172033]">
                {validationReport.aligned_time_range?.readable_window || 
                 `${validationReport.aligned_time_range?.min_timestamp}s – ${validationReport.aligned_time_range?.max_timestamp}s`}
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-[#64748B] block font-sans uppercase font-semibold">Duration</span>
              <span className="font-bold text-[#0891B2]">
                {validationReport.aligned_time_range?.duration_seconds?.toFixed(2)}s
              </span>
            </div>
          </div>

          {/* Row-specific rejections list if any */}
          {validationReport.rejections && validationReport.rejections.length > 0 && (
            <div className="mt-4 p-4 bg-red-50/50 border border-red-200 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-red-800 text-xs font-bold">
                <XCircle className="w-4 h-4 text-red-600" />
                <span>Row-Specific Rejections ({validationReport.rejections.length}):</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-red-200 text-red-700 font-semibold font-mono">
                      <th className="py-1.5 px-2">Row #</th>
                      <th className="py-1.5 px-2">Column</th>
                      <th className="py-1.5 px-2">Raw Value</th>
                      <th className="py-1.5 px-2">Rejection Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-100 font-mono text-[11px]">
                    {validationReport.rejections.map((rej, rIdx) => (
                      <tr key={rIdx} className="text-red-900">
                        <td className="py-1.5 px-2 font-bold">{rej.row_index}</td>
                        <td className="py-1.5 px-2">{rej.column || '—'}</td>
                        <td className="py-1.5 px-2 text-slate-600 max-w-xs truncate">{rej.raw_value || '—'}</td>
                        <td className="py-1.5 px-2">{rej.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <p className="text-xs text-[#52647A]">
            Dataset successfully validated and prepared for cross-correlation against ThreatLens EV digital twin.
          </p>
        </div>
      )}
    </div>
  );
}
