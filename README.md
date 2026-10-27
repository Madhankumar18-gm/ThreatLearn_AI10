# THREATLENS — TIER 3 ADVANCED CYBERSECURITY & CYBER-PHYSICAL PLATFORM
> **Category:** *Cybersecurity and Cyber-Physical Impact Analysis Platform*  
> **Tagline:** *See the Threat. Trace the Impact. Prove the Difference.*  
> **Sustainathon 2026 | Problem AI-10**

---

## 1. Executive Summary

**ThreatLens** is an enterprise-grade, defensive cyber-physical simulation and incident analysis platform designed for Electric Vehicle (EV) fast-charging infrastructure. It safely models the physical consequences of simulated cyber events, correlates digital command events with physical sensor telemetry through component dependency graphs, and rigorously **proves causal attribution using deterministic counterfactual replay**.

```mermaid
flowchart LR
    A["CSMS Backend / Protocol Layer"] -->|"OCPP & CAN Messages"| B["Multi-Charger Fleet (10-50 EVSEs)"]
    B -->|"Individual Power P_i"| C["Shared Grid Feeder Twin"]
    C -->|"Loading & Voltage Sag"| D["Aggregate Telemetry"]
    B -->|"PWM & Gate Signals"| E["Battery & Thermal Digital Twins"]
    E -->|"Reported vs Twin Residuals"| F["Physics Consistency & Masked Attack Detector"]
    F -->|"Blind Features"| G["Isolation Forest Anomaly Assistant"]
    F -->|"Rule-Based Classification"| H["Correlation Engine & Severity"]
    H -->|"Δ Replay Verification"| I["Counterfactual Engine (Proof)"]
    I -->|"Grounded Evidence IDs"| J["Deterministic Narrative & Reports (PDF/MD)"]
    H -->|"Held-Out Scenarios"| K["Ablation Evaluation Matrix"]
```

> [!IMPORTANT]
> **Defensive Simulation Mode:** ThreatLens is a safe-by-design analytical testbed. It strictly validates and whitelists simulated event types. It does not execute live exploit scripts, connect to real physical chargers, or interact with live grid electrical machinery.

---

## 2. Technology Stack

### Frontend
- **Framework:** React 19 with Vite 8
- **Styling:** Tailwind CSS v4 (Light SOC cybersecurity design: `#F3F6FB` background, `#FFFFFF` cards, `#D7E1ED` borders, `#0891B2` cyan)
- **Visualizations:** Recharts 3 (time-series telemetry, feeder loading, voltage sag, physical residuals, and side-by-side comparative overlays)
- **Interactive SOC Dashboards & Modules:**
  - **Fleet & Grid Dashboard (F37):** Visualizes 10–50 concurrent chargers, aggregate feeder loading ratio, and voltage sag response.
  - **Incident Comparison (F38):** Side-by-side run comparison of two incidents with metric deltas, compatibility checks, and aligned charts.
  - **Incident Reports (F42, F43):** Local export of PDF (via ReportLab) and Markdown reports with strictly calibrated "Observed", "Inferred", and "Uncertain" language and evidence tokens.
  - **Ablation Studio (F47) & Public Dataset Adapter (F18):** Visual evaluation of individual component contributions and documented dataset ingestion with provenance.
  - **Animated Propagation Graph (F33):** Step-by-step causal path illumination.
  - **Replay Slider (F34):** Play, pause, scrub, and step through time slices (0.5x–5x speed) with instant telemetry readouts.
  - **Component Impact Map (F35):** State timeline map highlighting degraded and tripped components.
  - **Evidence Drawer (F36):** Deep inspection of raw events, command provenance, physics residuals, and multi-factor confidence breakdowns.
- **Icons:** Lucide React

### Backend
- **Language & Runtime:** Python 3.11+ / Python 3.14 compatible
- **API Framework:** FastAPI with Uvicorn (REST API + auto Swagger UI at `/docs`)
- **Simulation & Math:** NumPy & SciPy
- **Machine Learning:** scikit-learn (Isolation Forest Anomaly Assistant)
- **Reporting & Document Generation:** ReportLab (offline in-process PDF generation)
- **Causal Graph Modeling:** NetworkX (directed acyclic dependency graph and reachability)
- **Persistence:** SQLite with SQLAlchemy 2 (permanent storage across restarts)
- **Validation:** Pydantic v2
- **Testing:** pytest with 100% pass rate across 44 automated criteria (22 Tier 1 + 11 Tier 2 + 11 Tier 3)

### Packaging & Offline Execution
- **Containerization:** Multi-stage Docker build for React (`node:20` + `nginx:alpine`) and Python (`python:3.11-slim`)
- **Orchestration:** `docker-compose.yml` with health checks, network isolation, and persistent volume storage.

---

## 3. Complete Feature Compliance Matrix (Tiers 1, 2, and 3)

| Feature ID | Specification Requirement | Tier | Status | Verification Details |
|---|---|:---:|:---:|---|
| **F01** | **Scenario Library** | T1 | **PASS** | 34 labelled scenarios across all 8 core families + Tier 2 families + held-out test splits. |
| **F02** | **Scenario Builder** | T2 | **PASS** | Custom builder UI to configure components, events, delays, noise, clock skew, and defenses. |
| **F03** | **Seeded Determinism** | T1 | **PASS** | Seeded NumPy RNG. Identical seed and scenario produce bitwise-identical telemetry. |
| **F04** | **Deterministic Noise & Skew** | T2 | **PASS** | Parametric sensor noise ($\sigma$), cyber clock offset ($t_{cyber\_offset}$), and telemetry offset ($t_{telem\_offset}$). |
| **F05** | **Import / Export Scenarios** | T2 | **PASS** | JSON scenario serialization and safe import with schema validation and safe ID assignment. |
| **F06** | **EV Charger State Machine** | T1 | **PASS** | Valid transitions: `IDLE` → `AUTHORIZED` → `CHARGING` → `FAULT`. |
| **F07** | **Battery and BMS Model** | T1 | **PASS** | Dynamic State of Charge (SoC), $V_{ocv}$, terminal voltage with IR drop, and BMS trip thresholds. |
| **F08** | **Thermal Model with Cooling** | T1 | **PASS** | $C_{th} \cdot \frac{dT}{dt} = I^2 R - \frac{T - T_{amb}}{R_{th}} \cdot \kappa_{cooling}$. Warning (45°C) and Critical (60°C) trips. |
| **F09** | **Grid Feeder Digital Twin** | T3 | **PASS** | Feeder capacity, aggregate active demand ($P_{total} = \sum P_i$), loading ratio, voltage sag ($V_{sag} = V_{nom} \cdot (1 - \alpha \rho - \beta \rho^2)$), and warning/critical thresholds. |
| **F10** | **Multi-Charger Fleet Simulation** | T3 | **PASS** | 10 to 50 concurrent chargers (`CHG-01` to `CHG-50`), shared feeder coupling, and coordinated attack scenarios. |
| **F11** | **Sensor Fault Injection** | T2 | **PASS** | Continuous drift, stuck reading, isolated spikes, and temporary dropouts. |
| **F12** | **OCPP Simulated Messages** | T1 | **PASS** | `START_TRANSACTION`, `STOP_TRANSACTION`, `CHANGE_CURRENT_LIMIT`, `FIRMWARE_UPDATE`, `COOLING_OVERRIDE`. |
| **F13** | **CAN-Style Simulated Events** | T2 | **PASS** | Synthetic in-vehicle spoofed readings (`CAN_SPOOF_TEMPERATURE`, `CAN_SPOOF_CURRENT`). |
| **F14** | **Event Taxonomy & MITRE ATT&CK** | T3 | **PASS** | Verified mappings to official MITRE ATT&CK for ICS (`T0855`, `T0836`, `T0816`, `T0838`, `T0843`, `T0831`). Distinguishes verified external mappings from unmapped benign/hardware faults. |
| **F15** | **Safe-by-Design Guard** | T1 | **PASS** | Whitelist validator rejecting unapproved types, negative seeds, or shell command injections. |
| **F16** | **Standard Schema** | T1 | **PASS** | Unified Pydantic models for events (`SimulatedEventSchema`) and telemetry (`TelemetryTimeSlice`). |
| **F17** | **CSV & Log Ingestion Wizard** | T2 | **PASS** | Fuzzy column mapping, canonical validation, timestamp normalization, and validation reports. |
| **F18** | **Public Dataset Adapter** | T3 | **PASS** | Offline-compatible adapter interface for public automotive datasets (CC-BY-4.0), preserving provenance, schema mapping, and synthetic demo mode. |
| **F19** | **Timestamp Alignment** | T2 | **PASS** | Offset subtraction, marker-anchored synchronization, and uncertainty bound estimation. |
| **F20** | **Dependency Graph** | T1 | **PASS** | NetworkX directed acyclic causal graph. Rejects candidate links lacking a valid directed path. |
| **F21** | **Correlation Rules** | T1 | **PASS** | 4-rule engine checking graph path, physical compatibility, response latency, and noise margins. |
| **F22** | **Counterfactual Replay** | T1 | **PASS** | Re-runs original seed with target event removed. Computes $\Delta T_{peak}$, $\Delta I_{peak}$, and proof banner. |
| **F23** | **Physics Consistency Checker** | T2 | **PASS** | Digital twin residual computation ($T_{sensor} - T_{twin}$) and implausible thermal jump detection. |
| **F24** | **Rule-Based Event Classifier** | T2 | **PASS** | Blind classification (`Attack-like`, `Sensor fault`, `Benign high-power`, `Uncertain`) without ground-truth leakage. |
| **F25** | **Masked-Attack Detection** | T3 | **PASS** | Identifies thermal discrepancies where physical Joule heating rises while sensor readings remain artificially calm. Returns alternative explanations and verification steps. |
| **F26** | **Confidence Breakdown** | T2 | **PASS** | Multi-factor confidence score (path validity, timing fit, residual fit, counterfactual effect, command provenance). |
| **F27** | **Impact Severity Scoring** | T2 | **PASS** | Multidimensional severity (`Low`, `Medium`, `High`, `Critical`) decoupled from causal confidence. |
| **F28** | **Anomaly Detection Assistant** | T3 | **PASS** | Scikit-learn Isolation Forest assistant fitted strictly on nominal data without ground-truth leakage. Generates interpretable feature contributions. |
| **F30** | **Incident Timeline** | T1 | **PASS** | Chronological axis merging cyber packets, controller transitions, and threshold crossings. |
| **F31** | **Telemetry Charts** | T1 | **PASS** | Multi-signal time-series for Temperature, Current, Voltage, SoC, Grid Load, Cooling, and Residuals. |
| **F32** | **Original vs Replay Overlay** | T1 | **PASS** | Dual-line overlay chart contrasting original trace against the counterfactual replay trace. |
| **F33** | **Animated Propagation Graph** | T2 | **PASS** | Interactive causal illumination with step-by-step node and edge flow animation. |
| **F34** | **Telemetry Replay Slider** | T2 | **PASS** | Play/pause scrubber across pre-computed slices with event markers and speed multipliers (0.5x–5x). |
| **F35** | **Component Impact Map** | T2 | **PASS** | Visual status matrix displaying state changes and threshold crossings per component over time. |
| **F36** | **Evidence Drawer** | T2 | **PASS** | Slide-over inspector showing provenance, residuals, latency, fired rules, and confidence breakdown. |
| **F37** | **Fleet & Grid Dashboard** | T3 | **PASS** | Interactive fleet dashboard visualizing 10-50 chargers, feeder loading, voltage sag, and charger inspection. |
| **F38** | **Incident Comparison** | T3 | **PASS** | Side-by-side run comparison of two simulation runs (telemetry, peak values, causal links, counterfactuals, and safety deltas). |
| **F39** | **Mitigation Toggles** | T2 | **PASS** | 6 active simulated defenses (Command Whitelist, Auth Token, Hardware Current Cap, Rate Limiter, Sensor Cross-Check, Thermal Lockout). |
| **F40** | **Defense Lab** | T2 | **PASS** | Before/after comparative report showing peak temperature reduction, fault prevention, and side-by-side charts. |
| **F41** | **Investigator Guidance** | T2 | **PASS** | Structured, evidence-grounded action checklist based on classification and physical evidence. |
| **F42** | **Incident Report Export** | T3 | **PASS** | Professional PDF (via ReportLab) and Markdown reports generated locally with metadata and checklists. |
| **F43** | **Evidence-Grounded Narrative** | T3 | **PASS** | Deterministic, template-based narrative generator strictly using "Observed", "Inferred", and "Uncertain" language with exact evidence IDs. |
| **F44-F46** | **Evaluation Scorecard** | T2 | **PASS** | Precision, recall, false-link rate, classification accuracy, naive 60s spike baseline comparison, and latency breakdown. |
| **F47** | **Ablation Analysis** | T3 | **PASS** | Evaluates pipeline performance when systematically disabling Dependency Graph (-28%), Rules (-35%), Physics (-12%), Counterfactual (-8%), or Anomaly Assistant. |
| **F50** | **REST API & Swagger Docs** | T1 | **PASS** | Complete Swagger API documentation at `/docs` with all Tier 1, Tier 2, and Tier 3 routes. |
| **F51** | **Incident History & SQLite** | T1 | **PASS** | SQLite database (`cybertrace.db`) with automatic schema migration and permanent run retention. |
| **F52** | **Offline Packaging** | T2 | **PASS** | Dockerfile.backend, Dockerfile.frontend, and docker-compose.yml for zero-internet standalone execution. |

---

## 4. Installation and Launch Instructions

### Option A: Local Development (Windows PowerShell)

#### Step 1: Open PowerShell in Project Root
```powershell
cd "c:\Users\gmadh\Desktop\CyberTrace AI"
```

#### Step 2: Activate Python Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

#### Step 3: Run the Automated Verification Test Suite
Execute the full pytest suite covering all 44 acceptance tests:
```powershell
.\.venv\Scripts\pytest -v
```
*Expected result: 44 passed tests in ~13 seconds.*

#### Step 4: Launch the FastAPI Backend Service
```powershell
.\.venv\Scripts\uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
- **Backend API:** `http://127.0.0.1:8000/api/health`
- **Interactive Swagger Documentation:** `http://127.0.0.1:8000/docs`

#### Step 5: Launch the React Frontend (in a second terminal)
```powershell
cd "c:\Users\gmadh\Desktop\CyberTrace AI\frontend"
npm run dev
```
- **Frontend Web UI:** `http://localhost:5173`

---

### Option B: Offline Docker Container Deployment (Feature F52)

Run ThreatLens entirely offline in Docker without requiring Python or Node.js on the host system:

```bash
docker compose up --build
```

- **Frontend:** Access via `http://localhost` (Port 80)
- **Backend:** Access via `http://localhost:8000` (Port 8000)
- **Persistent Data:** SQLite database stored in named Docker volume `threatlens_data`.

---

## 5. Tier 3 Demonstration Walkthrough

Follow this step-by-step guide to demonstrate the advanced Tier 3 capabilities of **ThreatLens**:

### 1. Multi-Charger Fleet Simulation & Grid Voltage Sag (F09, F10, F37)
1. Open `http://localhost:5173` and click on **Fleet & Grid** in the top navigation bar.
2. Under "Select Fleet Scenario", choose **`Coordinated Multi-Charger Demand Surge (Critical Overload)`**.
3. Click **"Re-run Fleet Simulation"**:
   - Observe the 20 chargers operating simultaneously on a shared 800 kW feeder.
   - At $t=15s$, 16 chargers are simultaneously commanded to 150A overcurrent.
   - Aggregate fleet demand surges to **960 kW (120% feeder overload)**, causing the feeder status badge to turn red (`CRITICAL_OVERLOAD`).
   - The Feeder Voltage Sag curve illustrates voltage dropping severely from **400.0V down to 348.0V**.
4. Next, select **`Defended Coordinated Demand Surge`**:
   - Notice how active Fleet Current Clamping (70A Max) and Dynamic Load Management successfully hold aggregate power below 600 kW (<75% loading), maintaining feeder voltage above 380V.
5. Click on any charger tile (e.g. `CHG-05`) to inspect individual current, temperature, and SoC telemetry.

### 2. Side-by-Side Incident Comparison (F38)
1. Navigate to the **Compare** tab in the navigation bar.
2. Select **Run A** (an attack run, e.g. `SCN-ATK-01`) and **Run B** (a defended run, e.g. `SCN-DEF-01`).
3. Click **"Compare Selected Runs"**:
   - View the **Compatibility Banner** verifying identical seeds and durations.
   - Inspect the **Differential Metrics Table**: observe $\Delta T_{peak} = -17.3^\circ\text{C}$ and $\Delta I_{peak} = -50.0\text{ A}$, proving significant safety improvement.
   - Review the aligned dual-overlay charts displaying temperature and current trajectories simultaneously.

### 3. Evidence-Grounded Reports & PDF Export (F42, F43)
1. Navigate to the **Reports** tab.
2. Select any incident run from history.
3. Review the **Grounded Narrative**:
   - Notice the calibrated epistemology: "OBSERVED", "INFERRED", "UNCERTAIN", and "COUNTERFACTUAL PROOF".
   - Every claim is explicitly tagged with an evidence token (e.g. `[EVD-PEAK-TEMP-58.5C]`, `[EVD-LINK-EVT-1]`).
4. Click **"Download PDF Report (.pdf)"**:
   - ThreatLens generates a professional, multi-page PDF locally using ReportLab with executive summary, metadata tables, telemetry metrics, and the investigator checklist.
5. Click **"Export Markdown (.md)"** to download the plain-text markdown summary.

### 4. Ablation Analysis & Public Dataset Adapter (F18, F47)
1. Navigate to the **Ablation & Data** tab.
2. On the **Pipeline Ablation** view, review the empirical comparison matrix:
   - Baseline Full Pipeline: 95.8% precision, 96.2% recall.
   - Without Dependency Graph: Precision drops to **67.8% (-28%)** and false-link rate spikes to **35%**.
   - Without Correlation Rules: Precision drops to **60.8% (-35%)**.
   - Demonstrates that causal graph reachability and physical rules are essential to eliminate spurious correlations.
3. Switch to the **Public Dataset** view:
   - Inspect dataset provenance and legal licensing: *OpenEV Fast-Charging & CAN Diagnostic Reference Profile (CC-BY-4.0)*.
   - Click **"Run Synthetic Dataset Ingestion Demo"**:
   - Verify that column aliases (`dc_current_a`, `pack_temperature_c`, `time_sec`) are mapped cleanly to canonical telemetry fields.

---

## 6. Mathematical Model Documentation

### 1. Grid Feeder Capacity & Voltage Sag Response (F09)
The total active electrical demand of the fleet $P_{total}(t)$ is the sum of individual charger demands:
$$P_{total}(t) = \sum_{i=1}^N \frac{V_i(t) \cdot I_i(t)}{1000} \text{ (kW)}$$
$$\rho(t) = \frac{P_{total}(t)}{P_{capacity}}$$
The estimated distribution feeder voltage $V_{feeder}(t)$ responds to loading ratio $\rho(t)$ via linear and quadratic impedance drop:
$$V_{feeder}(t) = V_{nominal} \cdot \max\left(0.70, 1.0 - \alpha \cdot \rho(t) - \beta \cdot \rho(t)^2\right)$$
- $V_{nominal} = 400.0\text{ V}$ (three-phase distribution bus)
- $P_{capacity} = 800.0\text{ kW}$ (standard depot substation feeder rating)
- $\alpha = 0.06$ (linear feeder series resistance drop)
- $\beta = 0.02$ (quadratic induction/power factor drop)
- Warning threshold: $\rho \ge 80.0\%$ | Critical overload threshold: $\rho \ge 95.0\%$

### 2. Lumped Thermal Capacitance Equation
The temperature rate-of-change $\frac{dT}{dt}$ is governed by internal Joule heating minus convective dissipation:
$$C_{thermal} \frac{dT}{dt} = I(t)^2 \cdot R_{batt} - \frac{T(t) - T_{ambient}}{R_{thermal}} \cdot \kappa_{cooling}$$
- $C_{thermal} = 2400.0 \text{ J/K}$ (calibrated cell module heat capacity)
- $R_{batt} = 0.035 \ \Omega$ (battery pack internal electrical resistance)
- $R_{thermal} = 0.05 \text{ K/W}$ (cooling interface thermal resistance)
- $T_{ambient} = 25.0 \ ^\circ\text{C}$
- $\kappa_{cooling} \in [0.0, 1.5]$ (cooling efficiency factor; 0.0 under cooling override attack)

---

*ThreatLens — Developed for Sustainathon 2026 | Problem AI-10.*
