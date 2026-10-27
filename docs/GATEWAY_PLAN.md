# ThreatLens: OCPP Gateway Plan (No ML in This Stage)

## 1. Executive Summary & Objective

**ThreatLens** is a deterministic cybersecurity and cyber-physical impact analysis platform for electric vehicle (EV) charging infrastructure.

This document specifies the technical architecture, operational requirements, decision logic, and implementation roadmap for the **ThreatLens OCPP Gateway**. The gateway operates as an inline, real-time protocol verification and mitigation layer interposed between Central Systems (CSMS) and EVSE Charge Points.

The primary objective of this stage is to provide **deterministic, rule-based cyber protection** for simulated and localhost EVSE setups without introducing machine learning models, external cloud dependencies, or non-deterministic heuristics.

---

## 2. Architecture & Topography

The ThreatLens Gateway functions as a transparent, state-aware WebSocket proxy (man-in-the-middle) inspecting bidirectionally transmitted OCPP messages.

### High-Level System Architecture

```text
CSMS (backend) ↔ [ThreatLens Gateway] ↔ Charge Point (charger)
```

### Detailed Component Interaction

```text
┌─────────────────────────┐
│      CSMS Backend       │  (Central System Management Service)
│   (Port 9001 / ws://)   │
└────────────▲────────────┘
             │
             │ OCPP-J (JSON-RPC over WebSockets)
             │
┌────────────▼────────────────────────────────────────────────────────┐
│                      THREATLENS GATEWAY                             │
│                                                                     │
│  ┌───────────────────────┐          ┌────────────────────────────┐  │
│  │ CSMS Client Handler   │          │ ChargePoint Server Handler │  │
│  └──────────┬────────────┘          └────────────▲───────────────┘  │
│             │                                    │                  │
│             ▼                                    │                  │
│  ┌───────────────────────────────────────────────┴───────────────┐  │
│  │               Inspection & Decision Engine                    │  │
│  │                                                               │  │
│  │   • Schema & Protocol Validator (OCPP 1.6-J / 2.0.1)          │  │
│  │   • Decision Matrix: [ ALLOW | CLAMP | BLOCK ]                │  │
│  │   • State Machine Transition Tracker (IDLE/AUTH/CHARGE/FAULT) │  │
│  │   • Physical Threshold Guard (Current, Voltage, Temp)         │  │
│  │   • Rate Limiting & Command Authorization Filter              │  │
│  └──────────────────────────────┬────────────────────────────────┘  │
│                                 │                                   │
│                                 ▼                                   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │     ThreatLens Event Dispatcher & Counterfactual Logger       │  │
│  │     (Streams intervention records to ThreatLens Platform)     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────▲───────────────────────────────────┘
                                  │
                                  │ OCPP-J (JSON-RPC over WebSockets)
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                      Charge Point (charger)                         │
│                       (Port 9000 / ws://)                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Protocol & Operational Scope

### In-Scope Protocols & Standards
- **Protocol:** OCPP-J (Open Charge Point Protocol JSON over WebSockets).
- **Supported OCPP Versions:** OCPP 1.6-J (primary focus for EVSE market) and OCPP 2.0.1 message format compatibility.
- **Transport:** Standard WebSockets (`ws://`) over localhost loopback interface.

### Target OCPP Messages Inspected
1. **`SetChargingProfile` (CSMS → Charger):** Inspects charging current limits, power limits, duration, and schedule parameters to prevent overcurrent and thermal runaway attacks.
2. **`ChangeConfiguration` (CSMS → Charger):** Inspects modification of operational parameters (e.g., `MeterValueSampleInterval`, `MaxCurrent`, `HeartbeatInterval`).
3. **`RemoteStartTransaction` / `RemoteStopTransaction` (CSMS → Charger):** Verifies transaction legitimacy, token authorization, and connector ID validity.
4. **`ChangeAvailability` (CSMS → Charger):** Inspects operational state manipulation (Inoperative / Operative).
5. **`StatusNotification` (Charger → CSMS):** Monitors physical state transitions and error codes to track charger operating state.
6. **`MeterValues` (Charger → CSMS):** Validates reported energy, voltage, current, and SoC telemetry against digital twin expectations.

### Strict Out-of-Scope Constraints (No ML in This Stage)
- **No Machine Learning:** No neural networks, deep learning, clustering, or probabilistic anomaly detectors are permitted in this gateway stage. All decisions must be 100% deterministic and explainable.
- **Localhost-Only Prototype:** Operates strictly on `127.0.0.1` to eliminate external firewall, WAN routing, and remote network variance during testing.
- **No Production PKI Overhead:** Prototype uses unencrypted `ws://` on localhost loopback; production mTLS certificate management is deferred to subsequent enterprise deployment phases.
- **Simulated Hardware Coupling:** Couples with ThreatLens deterministic simulation engines rather than requiring live, physical high-voltage testbenches.

---

## 4. Decision Model: ALLOW / CLAMP / BLOCK

Every OCPP message passing through the ThreatLens Gateway is subjected to the three-tier deterministic decision matrix:

```
                            OCPP Message Arrives
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │    Schema & Syntax Valid?   │────── NO ─────► [ BLOCK ] (CallError: FormationViolation)
                      └──────────────┬──────────────┘
                                     │ YES
                                     ▼
                      ┌─────────────────────────────┐
                      │    Authorized & Allowed?    │────── NO ─────► [ BLOCK ] (CallError: SecurityError)
                      └──────────────┬──────────────┘
                                     │ YES
                                     ▼
                      ┌─────────────────────────────┐
                      │ Exceeds Physical Safe Cap?  │────── YES ────► [ CLAMP ] (Modify payload to safe limit)
                      └──────────────┬──────────────┘
                                     │ NO
                                     ▼
                                [ ALLOW ] (Forward unchanged)
```

### 1. ALLOW (Pass-Through)
- **Condition:** The message passes all protocol syntax checks, adheres to the current state machine transition rules, is within legitimate authorization boundaries, and does not exceed physical safety thresholds.
- **Action:** Forwarded directly to the recipient endpoint with sub-millisecond latency.
- **Audit:** Recorded in gateway transaction logs with status `ALLOW`.

### 2. CLAMP (Dynamic Mitigation & Capping)
- **Condition:** The message is syntactically valid and authorized, but specifies a current or power setpoint that exceeds safe physical bounds, feeder capacities, or thermal budgets.
  - *Example:* A compromised or misconfigured CSMS issues a `SetChargingProfile` requesting 180A, while the hardware breaker ceiling is 150A and the active safety cap is 100A.
- **Action:** The gateway intercepts the payload, clamps the requested limit to the maximum configured safe limit (e.g., 100.0A), recalculates message length, and forwards the modified message to the Charge Point.
- **Audit:** Dispatches a `CAPPED` intervention to the ThreatLens dashboard, logging the requested vs. modified setpoints.

### 3. BLOCK (Active Rejection & Drop)
- **Condition:** The message exhibits malicious or unauthorized behavior:
  - Unauthorized command injection (e.g., unauthenticated `RemoteStartTransaction`).
  - High-frequency setpoint oscillations violating rate-limiting intervals (< 5.0s between changes).
  - Malformed OCPP JSON payloads or unrecognized message action types.
  - Commands issued while the charger is in a `FAULT` or `THERMAL_LOCKOUT` state.
- **Action:** The message is completely dropped. The gateway synthesizes and returns an OCPP `CallError` (e.g., `SecurityError`, `FormationViolation`, or `InternalError`) back to the sender without forwarding to the downstream device.
- **Audit:** Dispatches a `BLOCKED` intervention to the ThreatLens event log with full rule provenance and trigger reason.

---

## 5. Safety Rules & Fail-Mode Architecture

### Fail-Safe vs. Fail-Open Architecture
In industrial cyber-physical systems, security mechanisms must never induce catastrophic hardware damage upon software failure.

- **Mandatory Policy:** **Fail-Safe (Deterministic Safe De-energization)**
- **Behavior:**
  - If the ThreatLens Gateway experiences an unhandled exception, process crash, or socket disconnect:
    1. The downstream socket to the Charge Point is cleanly terminated.
    2. The Charge Point state machine detects websocket disconnect and automatically executes its standard OCPP offline fallback: throttling current to 0A (or safe pilot signal 6A) and transitioning to `SUSPENDED_EVSE`.
    3. The gateway will **never fail-open** (i.e. it will never bypass safety guards to allow unmonitored raw current flow).

### Deterministic Safety Rules
1. **Rule R-01 (Hardware Current Ceiling):**
   - Absolute limit: `charging_current <= 150.0 A`.
   - Action: Any setpoint $> 150.0\text{ A}$ is clamped to $150.0\text{ A}$ (or active cap).
2. **Rule R-02 (Rate Limiting & Command Flutter Protection):**
   - Minimum interval: $5.0\text{ seconds}$ between consecutive `SetChargingProfile` commands.
   - Action: Rapid fluctuations intended to induce transformer stress or contactor wear are `BLOCK`ed.
3. **Rule R-03 (State Machine Sequence Validation):**
   - Transition enforcement: `IDLE` → `AUTHORIZED` → `CHARGING` → `FAULT`.
   - Direct jumps from `IDLE` to `CHARGING` without prior authorization are `BLOCK`ed.
4. **Rule R-04 (Thermal Lockout Protection):**
   - If battery or charger temperature exceeds $45.0^\circ\text{C}$ (Caution) or $50.0^\circ\text{C}$ (Critical), the gateway enforces an immediate software lockout, blocking any new charging authorization.

---

## 6. Implementation Phases & Milestones

### Phase 1: Localhost Proxy & Protocol Framing
- Build async WebSocket server on `127.0.0.1:9000` (facing Charger) and client on `127.0.0.1:9001` (facing CSMS).
- Parse OCPP 1.6-J framing: `[MessageTypeId, "UniqueId", "Action", {Payload}]`.
- Implement transparent pass-through (`ALLOW` mode) with bidirectional heartbeats.

### Phase 2: Inspection Engine & Decision Matrix
- Implement strict Pydantic payload validators for `SetChargingProfile`, `ChangeConfiguration`, and `RemoteStartTransaction`.
- Implement the `ALLOW / CLAMP / BLOCK` decision module.
- Implement rate limiting with monotonic sliding window timers.
- Implement automated OCPP `CallError` response synthesizer.

### Phase 3: ThreatLens Platform Integration
- Stream gateway decision telemetry directly to ThreatLens SQLite repository and live WebSocket monitor.
- Align gateway event identifiers with the ThreatLens Event Taxonomy (`EventTaxonomyCatalog`).
- Expose gateway configuration toggles in the ThreatLens Defense Lab interface.

### Phase 4: Deterministic Validation & Counterfactual Coupling
- Coupling with ThreatLens digital twin simulation scenarios (e.g. Scenarios 1–28).
- Execute counterfactual replay: compare identical attack scenarios with Gateway active vs. Gateway omitted.
- Provide automated verification test suite asserting 100% deterministic behavior under identical seeds.

---

## 7. Acceptance Criteria (Verification Suite)

| ID | Requirement | Verification Method | Pass Criteria |
|---|---|---|---|
| **AC-01** | **Benign Pass-Through** | Stream standard OCPP 1.6-J charging session (`RemoteStart` → `MeterValues` → `RemoteStop`). | 100% messages allowed with $<2\text{ ms}$ gateway latency; zero message corruption. |
| **AC-02** | **Overcurrent Clamping** | Send `SetChargingProfile` with current setpoint $= 200.0\text{ A}$ (configured cap $= 100.0\text{ A}$). | Forwarded payload current strictly modified to $100.0\text{ A}$; `CAPPED` event recorded. |
| **AC-03** | **Unauthorized Injection Blocking** | Inject `RemoteStartTransaction` without prior RFID/token validation. | Message blocked; `CallError: SecurityError` returned; charger remains `IDLE`. |
| **AC-04** | **Rate Limiting Enforcement** | Send three `SetChargingProfile` updates within $2.0\text{ seconds}$. | First message allowed; subsequent messages within 5s window rejected with `RateExceeded`. |
| **AC-05** | **Zero Machine Learning** | Codebase audit of gateway inspection engine. | Zero imports of ML/statistical learning libraries; 100% rule-based branching logic. |
| **AC-06** | **Deterministic Reproducibility**| Run identical attack profile 10 times under identical seed. | 100% identical decision sequence and exact bitwise timestamp alignment. |

---

## 8. ThreatLens Dashboard & Demonstration Workflow

### ThreatLens Defense Lab Integration
The gateway integrates directly with the ThreatLens frontend:
- **Defense Configuration Panel:** Enables/disables gateway mitigation rules (`auth_validation`, `current_cap`, `rate_limiting`, `thermal_lockout`).
- **Intervention Stream:** Real-time table displaying timestamped gateway actions (`ALLOW`, `CLAMP`, `BLOCK`).
- **Counterfactual Delta:** Shows physical temperature and current differences with gateway active vs. inactive.

### Standalone Localhost Demo Script (`scripts/demo_gateway.py`)
A self-contained demonstration script illustrates the gateway in action:
1. Spawns mock CSMS on `127.0.0.1:9001`.
2. Spawns mock EVSE Charge Point on `127.0.0.1:9000`.
3. Starts ThreatLens Gateway.
4. Executes test suite simulating benign charging, an overcurrent manipulation attack, and an unauthorized command burst.
5. Displays clear terminal output confirming `ALLOW`, `CLAMP`, and `BLOCK` outcomes.

---

## 9. Document History & Revision Control

| Version | Date | Author | Description of Changes |
|---|---|---|---|
| **1.0** | 2026-10-24 | Platform Engineering | Initial OCPP Gateway technical specification. |
| **2.0** | 2026-10-27 | ThreatLens Architecture | Official specification update for **ThreatLens**. Updated title and architecture diagram (`CSMS (backend) ↔ [ThreatLens Gateway] ↔ Charge Point (charger)`). Preserved all technical requirements, ALLOW/CLAMP/BLOCK model, localhost-only scope, and no-ML constraints. |
