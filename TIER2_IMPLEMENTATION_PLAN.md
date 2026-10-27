# THREATLENS TIER 2 IMPLEMENTATION PLAN
**Cybersecurity & Cyber-Physical Impact Analysis Platform**  
*Sustainathon 2026 | Problem AI-10*

---

## 1. Executive Summary & Audit Findings

### Genuine Working Tier 1 Capabilities:
- **EV Charger State Machine (F06):** Valid transitions (`IDLE` → `AUTHORIZED` → `CHARGING` → `FAULT`), hardware max clamping (150A), dynamic BMS feedback limits, and hardware safety breaker cutoff.
- **Battery & Thermal Physics Digital Twin (F07, F08):** Lumped thermal capacity with convective cooling ($C_{th} \cdot \frac{dT}{dt} = I^2 R - \frac{T - T_{amb}}{R_{th}} \cdot \kappa_{cooling}$), dynamic terminal voltage with IR drop, and Coulombic integration for SoC.
- **Scenario Library (F01):** 28 deterministic scenarios spanning all 8 primary families with ground-truth links.
- **Seeded Determinism (F03):** Seeded NumPy RNG guaranteeing bitwise reproducibility.
- **Dependency Graph & Causal Correlation (F20, F21, F29):** NetworkX directed causal topology, physical channel compatibility, plausible delay windows, noise margins, and grounded evidence labels (`Observed`, `Inferred`, `Uncertain`).
- **Deterministic Counterfactual Replay (F22, F32):** Single-event excision under identical seed, calculating $\Delta T$, $\Delta I$, and attribution verdicts (`DISAPPEARED`, `DECREASED`, `UNCHANGED`).
- **SQLite Persistence (F51):** Full runs, telemetry, correlation links, and counterfactual comparisons persisted across restarts.
- **Light Cyber UI & Full Viewport:** Full-width layout, large typography, and Recharts multi-signal charts.

### Missing Tier 2 Scope to Implement:
1. **Scenario Builder (F02):** UI & API to build, validate, save, and rerun custom scenarios with custom events, timing, noise, and mitigations.
2. **Deterministic Noise & Clock-Skew Controls (F04):** Configurable measurement noise, cyber timestamp offset, telemetry timestamp offset, and measurement jitter.
3. **Scenario Import & Export (F05):** JSON export/import with validation, schema versioning, safe ID assignment, and downloadable example.
4. **Sensor Fault Injection (F11):** Temperature drift, stuck readings, spikes, temporary dropouts.
5. **CAN-Style Simulated Events (F13):** Synthetic in-vehicle spoofed readings (`CAN_SPOOF_TEMPERATURE`, `CAN_SPOOF_CURRENT`).
6. **CSV and Log Import Wizard (F17):** File upload, preview, column mapping, validation, and execution through analysis engine.
7. **Timestamp Alignment (F19):** Configurable clock offset, marker estimation, aligned timestamps display, uncertainty bounds.
8. **Physics Consistency Checker (F23):** Residual = Reported - Predicted. Tracking over time, sensor quality flags, implausible change detection.
9. **Rule-Based Event Classification (F24):** Explainable classifier (`Attack-like`, `Sensor fault`, `Benign high-power`, `Uncertain`) without leaking ground truth.
10. **Confidence Breakdown (F26):** Multi-factor scoring (path validity, timing fit, physics consistency, counterfactual effect, command provenance, alternative explanation penalty).
11. **Impact Severity Scoring (F27):** Multidimensional severity (`Low`, `Medium`, `High`, `Critical`) independent of causal confidence.
12. **Animated Propagation Graph (F33):** Backend-driven graph with interactive nodes, timeline order animation, and causal path highlighting.
13. **Replay Slider (F34):** Play, pause, scrub, jump, speed adjustment (0.5x–5x) on stored telemetry without regeneration.
14. **Impact Map (F35):** Component-level state change time, signals, event IDs, severity.
15. **Evidence Drawer (F36):** Traceable side-panel with telemetry, residuals, path, matched rules, confidence breakdown, and caveats.
16. **Mitigation Toggles & Defense Lab (F39, F40):** Active mitigations (authorization checks, allowed-command list, current cap, rate limiting, sensor cross-checking, thermal lockout) and before/after effectiveness reporting.
17. **Investigator Guidance (F41):** Evidence-grounded investigative checklist with recommendations and rationale.
18. **Evaluation Scorecard & Held-Out Testing (F44, F45, F46):** Benchmark dashboard (precision, recall, false-link rate, classification accuracy, detection latency vs physical delay) comparing against 60s spike baseline with tuning vs held-out splits.
19. **Docker Compose Packaging (F52):** Offline containerized configuration with persistent volume and health checks.

---

## 2. Architecture & File Plan

```
backend/
├── app/
│   ├── analysis/
│   │   ├── classifier.py            # [NEW] Rule-based event classification (F24)
│   │   ├── confidence_severity.py   # [NEW] Confidence breakdown & impact severity (F26, F27)
│   │   ├── consistency_checker.py   # [NEW] Physics residual & digital twin prediction (F23)
│   │   ├── correlation_engine.py    # [EXTENDED] Integrate confidence, residuals, alignment
│   │   ├── counterfactual.py        # [MAINTAINED]
│   │   ├── dependency_graph.py      # [MAINTAINED]
│   │   ├── evaluation.py            # [NEW] Evaluation scorecard, benchmarks, held-out splits (F44, F45, F46)
│   │   └── investigator.py          # [NEW] Rule-based investigator checklist generator (F41)
│   ├── api/
│   │   └── routes.py                # [EXTENDED] New routes for builder, import/export, defense, evaluation
│   ├── core/
│   │   ├── config.py                # [EXTENDED] Defense & evaluation parameters
│   │   └── guard.py                 # [EXTENDED] Validation for custom scenarios, offsets, CSV rows
│   ├── database/
│   │   ├── models.py                # [EXTENDED] Tables for custom scenarios, defenses, imported datasets
│   │   └── repository.py            # [EXTENDED] Persistence helpers for Tier 2 entities
│   ├── ingestion/
│   │   ├── csv_importer.py          # [NEW] CSV parser, validator, column mapper (F17)
│   │   └── time_alignment.py        # [NEW] Clock offset & marker alignment (F19)
│   ├── scenarios/
│   │   ├── builder.py               # [NEW] Custom scenario validation and generation (F02)
│   │   ├── import_export.py         # [NEW] JSON scenario serialization & validation (F05)
│   │   └── library.py               # [EXTENDED] Add sensor drift, CAN spoof, and held-out scenarios
│   ├── schemas/
│   │   ├── analysis.py              # [EXTENDED] Confidence breakdown, residuals, severity, guidance
│   │   ├── defense.py               # [NEW] Mitigation toggles & effectiveness schemas (F39, F40)
│   │   ├── evaluation.py            # [NEW] Benchmark metrics & latency schemas (F44-F46)
│   │   ├── ingestion.py             # [NEW] CSV mapping & alignment schemas (F17, F19)
│   │   └── scenario.py              # [EXTENDED] Noise params, clock skew, defense flags
│   └── simulation/
│       ├── defenses.py              # [NEW] Active simulated mitigation engine (F39)
│       ├── simulator.py             # [EXTENDED] Deterministic noise, clock offsets, sensor drift/spikes
│       └── thermal_model.py         # [EXTENDED] Drift, spike, dropout, CAN sensor spoofing
```

```
frontend/src/
├── components/
│   ├── AnimatedPropagationGraph.jsx # [NEW] Step-by-step incident propagation graph (F33)
│   ├── EvidenceDrawer.jsx           # [NEW] Deep evidence & causal trace side-drawer (F36)
│   ├── ImpactMap.jsx                # [NEW] Component-level impact & state change map (F35)
│   ├── ReplaySlider.jsx             # [NEW] Interactive play/pause scrubber (F34)
│   └── Header.jsx                   # [EXTENDED] Navigation tabs for Defense Lab, Import, Evaluation
├── pages/
│   ├── DefenseLab.jsx               # [NEW] Mitigation toggles & before/after report (F39, F40)
│   ├── EvaluationScorecard.jsx      # [NEW] Benchmark precision/recall & held-out dashboard (F44, F45, F46)
│   ├── ImportWizard.jsx             # [NEW] CSV upload, column mapper, validator (F17, F19)
│   ├── ScenarioBuilder.jsx          # [NEW] Custom scenario creator with noise & defenses (F02, F04, F05)
│   ├── ScenarioLab.jsx              # [EXTENDED] Export/Import buttons, custom scenario list
│   └── IncidentAnalysis.jsx         # [EXTENDED] Integrated replay scrubber, residuals chart, evidence drawer
└── services/
    └── api.js                       # [EXTENDED] API client functions for Tier 2 endpoints
```

---

## 3. Implementation Phases & Order

1. **Stage 1 (Core & Modeling):**
   - Extend schemas: `ScenarioSchema` with noise, clock skew, mitigations; add `defense.py`, `ingestion.py`, `evaluation.py`.
   - Extend `ThermalModel` & `Simulator`: Implement temperature drift, stuck, spike, dropout, CAN spoof, and measurement noise controls ($t_{cyber\_offset}, t_{telem\_offset}$).
   - Implement `defenses.py`: Active simulated mitigations in the simulation step loop.

2. **Stage 2 (Builder & Import/Export):**
   - Implement `scenarios/builder.py` and `scenarios/import_export.py`.
   - Create endpoints: `POST /api/scenarios/custom`, `GET /api/scenarios/export/{id}`, `POST /api/scenarios/import`.
   - Update SQLite models and repository.

3. **Stage 3 (Ingestion & Time Alignment):**
   - Implement `ingestion/csv_importer.py` & `ingestion/time_alignment.py`.
   - Create endpoints: `POST /api/ingest/preview`, `POST /api/ingest/commit`, `POST /api/align`.

4. **Stage 4 (Advanced Analysis Engine):**
   - Implement `consistency_checker.py` (digital twin predictions and residuals).
   - Implement `classifier.py` (explainable rule-based categorization without ground-truth leakage).
   - Implement `confidence_severity.py` (confidence breakdown & impact severity).
   - Implement `investigator.py` (grounded investigative checklist).

5. **Stage 5 (Defense Lab & Evaluation Engine):**
   - Implement `evaluation.py` (precision, recall, false-link rate, detection latency vs physical delay, tuning vs held-out splits).
   - Endpoints: `POST /api/defense/compare`, `GET /api/evaluation/benchmark`.

6. **Stage 6 (Frontend Components & Visualizations):**
   - Build `ReplaySlider.jsx`, `AnimatedPropagationGraph.jsx`, `ImpactMap.jsx`, `EvidenceDrawer.jsx`.
   - Build `ScenarioBuilder.jsx`, `ImportWizard.jsx`, `DefenseLab.jsx`, `EvaluationScorecard.jsx`.
   - Update `Header.jsx`, `App.jsx`, and `IncidentAnalysis.jsx`.

7. **Stage 7 (Packaging & Offline Containerization):**
   - Create `Dockerfile` (frontend), `Dockerfile` (backend), and `docker-compose.yml`.

8. **Stage 8 (Testing & Verification):**
   - Write comprehensive automated pytest suite covering all 21 acceptance criteria.
   - Run `npm run build` and live integration checks.

---

## 4. Acceptance Criteria Checklist

- [ ] AC1: Scenario builder rejects invalid inputs (negative seed, duration out of range, unapproved events).
- [ ] AC2: Scenario export and import preserves valid definitions and rejects malformed JSON.
- [ ] AC3: Identical seed and noise configuration produces identical measurement noise.
- [ ] AC4: Clock offsets are applied, recorded, and displayed without altering physical ground-truth.
- [ ] AC5: Sensor faults alter reported telemetry without altering underlying physical model states.
- [ ] AC6: CAN spoofed readings are clearly distinguished from physical states.
- [ ] AC7: CSV import supports mapping, validation, and runs through the analysis pipeline without code execution.
- [ ] AC8: Physics residuals identify discrepancies between reported and expected thermal behavior.
- [ ] AC9: Classifier categorizes events without using ground truth as input.
- [ ] AC10: Confidence score includes multi-factor breakdown and alternative explanation penalties.
- [ ] AC11: Severity score reflects physical thresholds reached independently of causal confidence.
- [ ] AC12: Replay slider scrubs stored telemetry without random regeneration.
- [ ] AC13: Animated propagation graph reflects actual backend dependency data.
- [ ] AC14: Evidence drawer displays comprehensive provenance, residuals, and rules.
- [ ] AC15: Defense toggles alter simulation behavior and report before/after effectiveness.
- [ ] AC16: Investigator guidance produces grounded checklists.
- [ ] AC17: Evaluation scorecard calculates precision, recall, false-link rate against 60s spike baseline.
- [ ] AC18: Held-out evaluation set remains separate from tuning.
- [ ] AC19: Detection latency distinguishes computation time from physical delay.
- [ ] AC20: Docker Compose configuration runs locally and offline.
- [ ] AC21: All 22 Tier 1 regression tests continue to pass.
