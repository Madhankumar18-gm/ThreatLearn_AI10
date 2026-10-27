# THREATLENS TIER 3 IMPLEMENTATION PLAN
**Cybersecurity & Cyber-Physical Impact Analysis Platform**  
*Sustainathon 2026 | Problem AI-10*

---

## 1. Initial Audit & Baseline Verification

### Current State (Verified 2026-10-26):
- **Tier 1 Functionality:** 22/22 tests passing (deterministic simulation, state machine, thermal model, causal graph, counterfactual replay, persistence).
- **Tier 2 Functionality:** 11/11 tests passing (custom scenario builder, deterministic noise, clock skew, sensor fault injection, CAN spoofing, CSV ingestion wizard, physics consistency checker, rule-based event classifier, confidence & severity scoring, defense lab, and benchmark scorecard).
- **Frontend State:** Built cleanly in 2.54s with 0 errors. Light SOC theme, responsive layout, ReplaySlider, AnimatedPropagationGraph, ImpactMap, EvidenceDrawer.
- **Docker State:** `Dockerfile.backend`, `Dockerfile.frontend`, `nginx.conf`, and `docker-compose.yml` configured and verified.

---

## 2. Tier 3 Scope & Feature Mapping

| Feature ID | Name | Description & Architecture |
|---|---|---|
| **F09** | **Grid Feeder Digital Twin** | Simplified model of 400V/480V distribution feeder. Calculates total fleet active power demand ($P_{total} = \sum P_i$), feeder loading ratio ($\rho = P_{total}/P_{capacity}$), voltage sag ($V_{sag} = V_{nominal} \cdot (1 - \alpha \rho - \beta \rho^2)$), and warning/critical thresholds (>80%, >95%). |
| **F10** | **Multi-Charger Fleet Simulation** | Simulates 10 to 50 concurrent chargers (`CHG-01` to `CHG-50`) with independent state machines, battery SoC, pack temperature, and telemetry. Evaluates aggregate feeder impact and supports coordinated attacks. |
| **F14** | **Event Taxonomy & MITRE ATT&CK for ICS** | Verified mapping of internal event types to MITRE ATT&CK for ICS (e.g., `T0855`, `T0836`, `T0816`, `T0838`, `T0843`). Distinguishes verified external mappings from unmapped/uncertain entries. |
| **F18** | **Public Dataset Adapter** | Offline-compatible adapter interface for public CAN/automotive/EV datasets, preserving provenance, mapping schemas, and running synthetic demo mode when offline. |
| **F25** | **Masked-Attack Detection** | Discrepancy detector identifying when physical variables diverge from sensor-reported values (e.g. frozen sensor hiding overheating), generating evidence IDs and alternative non-attack explanations. |
| **F28** | **Anomaly Detection Assistant** | Scikit-learn Isolation Forest assistant fitted on nominal rolling features without ground-truth leakage. Produces interpretable feature anomalies without independently declaring attacks. |
| **F37** | **Fleet & Grid Visualization** | Dedicated Fleet & Grid dashboard visualizing 10–50 chargers, feeder loading gauge, voltage sag curve, active events, and individual charger inspection. |
| **F38** | **Incident Comparison** | Side-by-side run comparison of two simulation runs (telemetry, peak values, causal links, counterfactuals, defenses, and compatibility warnings). |
| **F42** | **Incident Report Export (PDF & MD)** | Downloadable Markdown and professional ReportLab PDF containing executive summary, timeline, telemetry, physics residuals, links, and investigator checklist. |
| **F43** | **Evidence-Grounded Narrative** | Deterministic, template-based narrative generator strictly using "Observed", "Inferred", and "Uncertain" language with exact evidence IDs. |
| **F47** | **Ablation Analysis** | Evaluation tool systematically testing performance deltas when disabling graph, rules, physics consistency, counterfactual proof, or anomaly assistant. |

---

## 3. Implementation Sequence & File Plan

### Stage 1: Grid Feeder & Fleet Simulation Engine (F09, F10)
- `backend/app/simulation/grid_feeder.py`: Feeder digital twin model.
- `backend/app/simulation/fleet_simulator.py`: Fleet engine (10–50 chargers) with aggregate loading.
- `backend/app/schemas/fleet.py`: Fleet schemas and predefined scenarios.

### Stage 2: Event Taxonomy & MITRE ATT&CK for ICS (F14)
- `backend/app/core/taxonomy.py`: Structured taxonomy with authoritative MITRE ATT&CK for ICS technique IDs, URLs, and confidence tags.

### Stage 3: Masked-Attack Detection & Anomaly Assistant (F25, F28)
- `backend/app/analysis/masked_attack.py`: Discrepancy detection between physics state and reported sensors.
- `backend/app/analysis/anomaly_detector.py`: Isolation Forest assistant with feature explainability.

### Stage 4: Incident Comparison & Reporting (F38, F42, F43)
- `backend/app/analysis/incident_comparison.py`: Side-by-side run comparator.
- `backend/app/analysis/narrative.py`: Grounded narrative generator.
- `backend/app/reports/report_generator.py`: PDF (ReportLab) & Markdown exporter.

### Stage 5: Ablation Analysis & Public Dataset Adapter (F18, F47)
- `backend/app/analysis/ablation.py`: Component ablation testing suite.
- `backend/app/ingestion/public_dataset_adapter.py`: Automotive/CAN dataset adapter.

### Stage 6: Database & API Endpoints
- `backend/app/database/models.py` & `repository.py`: Fleet runs, report records, ablation results.
- `backend/app/api/routes.py`: REST endpoints for fleet, comparison, reports, and ablation.

### Stage 7: Frontend Dashboards & Visualizations (F37, F38, F42, F47)
- `frontend/src/pages/FleetGrid.jsx`: Fleet & Grid monitoring dashboard.
- `frontend/src/pages/IncidentComparison.jsx`: Side-by-side run comparator.
- `frontend/src/pages/IncidentReports.jsx`: PDF/Markdown report viewer and exporter.
- `frontend/src/pages/AblationStudio.jsx`: Component ablation experiment runner.
- `frontend/src/components/Header.jsx`: Updated navigation tabs.

### Stage 8: Automated Tests & Verification
- `backend/tests/test_tier3.py`: Comprehensive test suite verifying all 20 acceptance criteria.
- Full regression test run (`pytest`).
- Production build verification (`npm run build`).
