/**
 * ThreatLens API Service
 * Handles all communication with the FastAPI backend for Tier 1 & Tier 2 features.
 */

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Service health
  getHealth: () => request('/health'),

  // Scenarios
  getScenarios: (family) => {
    const q = family && family !== 'All' ? `?family=${encodeURIComponent(family)}` : '';
    return request(`/scenarios${q}`);
  },
  getScenario: (scenarioId) => request(`/scenarios/${scenarioId}`),
  
  // Custom Scenario Builder (F02)
  createCustomScenario: (scenarioData) => request('/scenarios/custom', {
    method: 'POST',
    body: JSON.stringify(scenarioData)
  }),

  // Scenario Import & Export (F05)
  exportScenario: (scenarioId) => request(`/scenarios/${scenarioId}/export`),
  importScenario: (jsonPayload) => request('/scenarios/import', {
    method: 'POST',
    body: JSON.stringify(jsonPayload)
  }),

  // Simulation Runs (F03, F04, F39)
  runSimulation: (scenarioId, seed = null, omittedEventId = null, overrides = {}) => {
    const payload = { 
      scenario_id: scenarioId,
      ...overrides 
    };
    if (seed !== null && seed !== undefined && seed !== '') {
      payload.seed = parseInt(seed, 10);
    }
    if (omittedEventId) {
      payload.omitted_event_id = omittedEventId;
    }
    return request('/runs', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Incident Runs History & Correlation
  getRuns: (limit = 50) => request(`/runs?limit=${limit}`),
  getRun: (runId) => request(`/runs/${runId}`),
  getRunLinks: (runId) => request(`/runs/${runId}/links`),

  // Counterfactual Replay (F22, F32)
  runCounterfactual: (runId, targetEventId) => {
    return request(`/runs/${runId}/counterfactual`, {
      method: 'POST',
      body: JSON.stringify({ target_event_id: targetEventId }),
    });
  },

  // CSV Ingestion Wizard (F17)
  previewCSV: (filename, content) => request('/ingest/preview', {
    method: 'POST',
    body: JSON.stringify({ filename, content })
  }),
  commitIngestion: (commitData) => request('/ingest/commit', {
    method: 'POST',
    body: JSON.stringify(commitData)
  }),

  // Time Alignment (F19)
  alignTimestamps: (alignData) => request('/align', {
    method: 'POST',
    body: JSON.stringify(alignData)
  }),

  // Defense Lab Comparison (F39, F40)
  compareDefenses: (comparisonData) => request('/defense/compare', {
    method: 'POST',
    body: JSON.stringify(comparisonData)
  }),

  // Investigator Guidance (F41)
  getRunGuidance: (runId) => request(`/runs/${runId}/guidance`),

  // Benchmark Evaluation Scorecard (F44, F45, F46)
  getEvaluationBenchmark: (split = 'tuning', seed = 42) => {
    return request(`/evaluation/benchmark?split=${encodeURIComponent(split)}&seed=${seed}`);
  },

  // Dependency Graph (F20)
  getGraph: () => request('/graph'),

  // ==========================================
  // TIER 3 ADVANCED API METHODS
  // ==========================================

  // Fleet & Grid Feeder (F09, F10, F37)
  getFleetScenarios: () => request('/fleet/scenarios'),
  runFleetSimulation: (scenario, seed = null) => {
    const q = seed !== null && seed !== undefined && seed !== '' ? `?seed=${seed}` : '';
    return request(`/fleet/run${q}`, {
      method: 'POST',
      body: JSON.stringify(scenario)
    });
  },

  // Event Taxonomy & MITRE ATT&CK for ICS (F14)
  getTaxonomy: () => request('/taxonomy'),
  getEventTaxonomy: (eventType) => request(`/taxonomy/${encodeURIComponent(eventType)}`),

  // Masked-Attack Detection (F25)
  getMaskedAttacks: (runId) => request(`/runs/${runId}/masked-attacks`),

  // Isolation Forest Anomaly Assistant (F28)
  getAnomalyAssistant: (runId) => request(`/runs/${runId}/anomaly-assistant`),

  // Incident Comparison (F38)
  compareRuns: (runIdA, runIdB) => request('/runs/compare', {
    method: 'POST',
    body: JSON.stringify({ run_a_id: runIdA, run_b_id: runIdB })
  }),

  // Reports & Evidence-Grounded Narratives (F42, F43)
  getRunNarrative: (runId) => request(`/runs/${runId}/narrative`),
  
  downloadMarkdownReport: async (runId) => {
    const response = await fetch(`${BASE_URL}/runs/${runId}/report/markdown`);
    if (!response.ok) throw new Error("Failed to export Markdown report.");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ThreatLens_Report_${runId}.md`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  downloadPdfReport: async (runId) => {
    const response = await fetch(`${BASE_URL}/runs/${runId}/report/pdf`);
    if (!response.ok) throw new Error("Failed to export PDF report.");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ThreatLens_Report_${runId}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  // Ablation Analysis (F47)
  getAblationAnalysis: () => request('/evaluation/ablation'),

  // Public Dataset Adapter (F18)
  getDatasetProvenance: () => request('/dataset/provenance'),
  getDatasetDemo: () => request('/dataset/demo'),
  importCustomDataset: (records) => request('/dataset/import', {
    method: 'POST',
    body: JSON.stringify(records)
  }),

  // ==========================================
  // THREATLENS OCPP GATEWAY API
  // ==========================================
  getGatewayStatus: () => request('/gateway/status'),
  startGateway: (params) => request('/gateway/start', {
    method: 'POST',
    body: JSON.stringify(params || {})
  }),
  stopGateway: () => request('/gateway/stop', {
    method: 'POST'
  }),
  updateGatewayConfig: (configUpdates) => request('/gateway/config', {
    method: 'POST',
    body: JSON.stringify(configUpdates)
  }),
  getGatewayInterventions: (limit = 100, decision = null, rule = null) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit);
    if (decision) params.append('decision', decision);
    if (rule) params.append('rule', rule);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request(`/gateway/interventions${qs}`);
  },
  clearGatewayInterventions: () => request('/gateway/interventions', {
    method: 'DELETE'
  }),
  getGatewayScenarios: () => request('/gateway/scenarios'),
  runGatewayScenario: (scenarioId, chargerId = 'CP_DEMO_01') => request('/gateway/test-scenario', {
    method: 'POST',
    body: JSON.stringify({ scenario_id: scenarioId, charger_id: chargerId })
  }),
};
