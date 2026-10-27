"""
Structured Event Taxonomy & MITRE ATT&CK for ICS Mapping (Feature F14).
Provides an authoritative dictionary of internal simulated event types,
their physical layer, verification status, and defensible mappings to
official MITRE ATT&CK for ICS techniques.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TaxonomyMapping(BaseModel):
    internal_event_type: str = Field(..., description="ThreatLens internal event identifier")
    category: str = Field(..., description="Category: Cyber Attack, Protocol Message, Hardware Fault, or Benign Operation")
    layer: str = Field(..., description="Protocol or physical domain layer (e.g. CSMS, EVSE, CAN, Hardware)")
    description: str = Field(..., description="Detailed description of the simulated event behavior")
    
    # MITRE ATT&CK for ICS Fields
    mitre_technique_id: Optional[str] = Field(default=None, description="Official MITRE ATT&CK for ICS technique ID (e.g. T0855)")
    mitre_technique_name: Optional[str] = Field(default=None, description="Official MITRE ATT&CK for ICS technique name")
    mitre_tactic: Optional[str] = Field(default=None, description="Associated ICS tactic (e.g. Impair Process Control)")
    mitre_url: Optional[str] = Field(default=None, description="Direct URL to official MITRE documentation")
    mapping_rationale: str = Field(..., description="Defensible engineering rationale linking simulated behavior to technique")
    verification_status: str = Field(
        ...,
        description="Verification status: VERIFIED, UNMAPPED_BENIGN, UNMAPPED_HARDWARE_FAULT, or UNVERIFIED_REVIEW"
    )
    disclaimer: str = Field(
        default="Defensive simulation mapping only. Does not prove a specific real-world threat actor or CVE.",
        description="Non-attribution disclaimer"
    )


class EventTaxonomyCatalog:
    """Central registry and query engine for simulated event taxonomy and MITRE ICS mappings."""

    MAPPINGS: Dict[str, TaxonomyMapping] = {
        "CHANGE_CURRENT_LIMIT": TaxonomyMapping(
            internal_event_type="CHANGE_CURRENT_LIMIT",
            category="Cyber Attack",
            layer="CSMS / OCPP Protocol",
            description="Unauthorized or malicious modification of charger maximum charging current setpoint.",
            mitre_technique_id="T0855",
            mitre_technique_name="Unauthorized Command Message",
            mitre_tactic="Impair Process Control (TA0106)",
            mitre_url="https://attack.mitre.org/techniques/T0855/",
            mapping_rationale="Adversary injects or replays a spoofed CSMS command to force the charger beyond safe operational limits without operator authorization.",
            verification_status="VERIFIED"
        ),
        "COOLING_OVERRIDE": TaxonomyMapping(
            internal_event_type="COOLING_OVERRIDE",
            category="Cyber Attack",
            layer="EVSE / Controller Hardware",
            description="Malicious sabotage or deactivation of the liquid cooling pump and thermal dissipation subsystem.",
            mitre_technique_id="T0836",
            mitre_technique_name="Modify Parameter",
            mitre_tactic="Impair Process Control (TA0106)",
            mitre_url="https://attack.mitre.org/techniques/T0836/",
            mapping_rationale="Adversary modifies operational configuration parameters controlling heat exchanger duty cycle, blinding or choking thermal regulation.",
            verification_status="VERIFIED"
        ),
        "MALICIOUS_FIRMWARE_UPDATE": TaxonomyMapping(
            internal_event_type="MALICIOUS_FIRMWARE_UPDATE",
            category="Cyber Attack",
            layer="EVSE Firmware / Embedded OS",
            description="Simulated unauthorized firmware payload flashing that subverts safety trip thresholds.",
            mitre_technique_id="T0843",
            mitre_technique_name="Program Download",
            mitre_tactic="Inhibit Response Function (TA0107)",
            mitre_url="https://attack.mitre.org/techniques/T0843/",
            mapping_rationale="Adversary transfers and flashes a corrupted firmware image over the network, overriding core safety logic and control loops.",
            verification_status="VERIFIED"
        ),
        "EMERGENCY_STOP": TaxonomyMapping(
            internal_event_type="EMERGENCY_STOP",
            category="Cyber Attack / Disruption",
            layer="EVSE Controller / Interlock",
            description="Simulated weaponization of emergency stop line to induce rapid contactor arcing or denial of service.",
            mitre_technique_id="T0816",
            mitre_technique_name="Device Restart/Shutdown",
            mitre_tactic="Inhibit Response Function (TA0107)",
            mitre_url="https://attack.mitre.org/techniques/T0816/",
            mapping_rationale="Adversary sends shutdown signals to abort charging prematurely or cycle power contactors maliciously.",
            verification_status="VERIFIED"
        ),
        "CAN_SPOOF_TEMPERATURE": TaxonomyMapping(
            internal_event_type="CAN_SPOOF_TEMPERATURE",
            category="Cyber Attack",
            layer="In-Vehicle CAN Bus",
            description="Synthetic in-vehicle CAN bus spoofing broadcasting falsified battery pack temperatures.",
            mitre_technique_id="T0831",
            mitre_technique_name="Manipulation of View",
            mitre_tactic="Inhibit Response Function (TA0107)",
            mitre_url="https://attack.mitre.org/techniques/T0831/",
            mapping_rationale="Adversary falsifies sensor telemetry reported to the BMS/EVSE to mask true physical heating or provoke false safety shutdowns.",
            verification_status="VERIFIED"
        ),
        "CAN_SPOOF_CURRENT": TaxonomyMapping(
            internal_event_type="CAN_SPOOF_CURRENT",
            category="Cyber Attack",
            layer="In-Vehicle CAN Bus",
            description="Synthetic CAN bus spoofing reporting lower current consumption than physically drawn.",
            mitre_technique_id="T0831",
            mitre_technique_name="Manipulation of View",
            mitre_tactic="Inhibit Response Function (TA0107)",
            mitre_url="https://attack.mitre.org/techniques/T0831/",
            mapping_rationale="Adversary manipulates telemetry feedback to prevent control algorithms from detecting excessive current draw.",
            verification_status="VERIFIED"
        ),
        "COORDINATED_DEMAND_SPIKE": TaxonomyMapping(
            internal_event_type="COORDINATED_DEMAND_SPIKE",
            category="Cyber Attack",
            layer="Fleet / CSMS Broadcast",
            description="Synchronized multi-charger current escalation targeting distribution feeder capacity.",
            mitre_technique_id="T0855",
            mitre_technique_name="Unauthorized Command Message",
            mitre_tactic="Impair Process Control (TA0106)",
            mitre_url="https://attack.mitre.org/techniques/T0855/",
            mapping_rationale="Coordinated injection of high-power charging commands across multiple endpoints simultaneously to induce distribution grid voltage sag.",
            verification_status="VERIFIED"
        ),
        "SENSOR_DRIFT": TaxonomyMapping(
            internal_event_type="SENSOR_DRIFT",
            category="Hardware Fault",
            layer="Sensor / Physical Transducer",
            description="Continuous calibration loss or thermal drift in thermistor/transducer output.",
            mitre_technique_id=None,
            mitre_technique_name=None,
            mitre_tactic=None,
            mitre_url=None,
            mapping_rationale="Physical hardware degradation or environmental thermal drift; unmapped as this is a non-adversarial physical phenomenon.",
            verification_status="UNMAPPED_HARDWARE_FAULT"
        ),
        "SENSOR_STUCK": TaxonomyMapping(
            internal_event_type="SENSOR_STUCK",
            category="Hardware Fault",
            layer="Sensor / Physical Transducer",
            description="Sensor output frozen at a fixed reading due to ADC latch-up or broken wiring.",
            mitre_technique_id=None,
            mitre_technique_name=None,
            mitre_tactic=None,
            mitre_url=None,
            mapping_rationale="Physical component failure (transducer open-circuit or ADC latch); not an intentional adversary cyber technique.",
            verification_status="UNMAPPED_HARDWARE_FAULT"
        ),
        "SENSOR_SPIKE": TaxonomyMapping(
            internal_event_type="SENSOR_SPIKE",
            category="Hardware Fault",
            layer="Sensor / Electromagnetic",
            description="Isolated transient voltage or current spike caused by EMI noise coupling.",
            mitre_technique_id=None,
            mitre_technique_name=None,
            mitre_tactic=None,
            mitre_url=None,
            mapping_rationale="Electromagnetic interference or ground bounce; physical noise phenomenon without cyber intent.",
            verification_status="UNMAPPED_HARDWARE_FAULT"
        ),
        "START_TRANSACTION": TaxonomyMapping(
            internal_event_type="START_TRANSACTION",
            category="Protocol Message",
            layer="OCPP 1.6 / 2.0.1",
            description="Standard OCPP session initialization message triggered upon driver RFID tap.",
            mitre_technique_id=None,
            mitre_technique_name=None,
            mitre_tactic=None,
            mitre_url=None,
            mapping_rationale="Legitimate business protocol message required for normal charging; not an adversarial technique.",
            verification_status="UNMAPPED_BENIGN"
        ),
        "STOP_TRANSACTION": TaxonomyMapping(
            internal_event_type="STOP_TRANSACTION",
            category="Protocol Message",
            layer="OCPP 1.6 / 2.0.1",
            description="Standard OCPP session termination message upon driver card tap or vehicle target SoC reached.",
            mitre_technique_id=None,
            mitre_technique_name=None,
            mitre_tactic=None,
            mitre_url=None,
            mapping_rationale="Legitimate business protocol message; not an adversarial technique.",
            verification_status="UNMAPPED_BENIGN"
        )
    }

    @classmethod
    def get_mapping(cls, event_type: str) -> Optional[TaxonomyMapping]:
        """Look up MITRE ATT&CK for ICS mapping for an event type."""
        return cls.MAPPINGS.get(event_type)

    @classmethod
    def list_all_mappings(cls) -> List[TaxonomyMapping]:
        """Return all registered taxonomy mappings."""
        return list(cls.MAPPINGS.values())

    @classmethod
    def get_summary_statistics(cls) -> Dict[str, Any]:
        """Return counts of verified, unmapped, and category breakdowns."""
        total = len(cls.MAPPINGS)
        verified = sum(1 for m in cls.MAPPINGS.values() if m.verification_status == "VERIFIED")
        hardware = sum(1 for m in cls.MAPPINGS.values() if m.verification_status == "UNMAPPED_HARDWARE_FAULT")
        benign = sum(1 for m in cls.MAPPINGS.values() if m.verification_status == "UNMAPPED_BENIGN")

        return {
            "total_event_types": total,
            "mitre_verified_count": verified,
            "hardware_fault_count": hardware,
            "benign_protocol_count": benign,
            "mitre_coverage_pct": round((verified / total) * 100.0, 1)
        }
