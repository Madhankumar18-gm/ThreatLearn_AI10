"""
Incident Report Export Generator (Feature F42).
Generates professional incident reports in Markdown (.md) and PDF (.pdf) formats
using local in-process formatting (ReportLab). Completely offline, safe, and deterministic.
"""

import io
import html
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from backend.app.analysis.narrative import GroundedNarrative


class ReportGenerator:
    """Generates downloadable Markdown and PDF incident reports."""

    @classmethod
    def generate_markdown(
        cls,
        run_data: Dict[str, Any],
        narrative: GroundedNarrative,
        correlation_links: Optional[List[Dict[str, Any]]] = None,
        cf_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """Constructs a comprehensive, well-structured Markdown incident report."""
        run_id = run_data.get("run_id", "RUN-UNKNOWN")
        scn_id = run_data.get("scenario_id", "SCN-UNKNOWN")
        scn_name = run_data.get("scenario_name", "EV Charging Simulation")
        created_at = run_data.get("created_at", datetime.now(timezone.utc).isoformat())

        md = []
        md.append(f"# THREATLENS INCIDENT REPORT — {run_id}")
        md.append(f"> **Category:** Cyber-Physical Incident Analysis & Causal Attribution")
        md.append(f"> **Tagline:** *See the Threat. Trace the Impact. Prove the Difference.*")
        md.append(f"> **Generated:** {created_at} | **Mode:** Simulation Testbed\n")
        md.append("---\n")

        md.append("## 1. Executive Summary")
        md.append(narrative.executive_summary + "\n")

        md.append("## 2. Incident & Scenario Metadata")
        md.append(f"| Property | Value |")
        md.append(f"|---|---|")
        md.append(f"| **Incident ID** | `{run_id}` |")
        md.append(f"| **Scenario ID** | `{scn_id}` |")
        md.append(f"| **Scenario Name** | {scn_name} |")
        md.append(f"| **Random Seed** | `{run_data.get('seed', 'N/A')}` |")
        md.append(f"| **Classification** | `{run_data.get('classification', 'N/A')}` |")
        md.append(f"| **Impact Severity** | `{run_data.get('severity', 'N/A')}` |")
        md.append(f"| **Model Version** | ThreatLens Twin v2.1 (Lumped Thermal + BMS) |\n")

        md.append("## 3. Physical Telemetry Summary")
        md.append(f"| Measured Parameter | Peak Value | Safety Limit | Status |")
        md.append(f"|---|---|---|---|")
        peak_t = run_data.get("peak_temperature", 25.0)
        peak_i = run_data.get("peak_current", 0.0)
        peak_g = run_data.get("peak_grid_load", 0.0)
        tripped = run_data.get("safety_trip_occurred", False)

        t_status = "CRITICAL (>=60°C)" if peak_t >= 60.0 else ("WARNING (>=45°C)" if peak_t >= 45.0 else "NORMAL")
        i_status = "EXCESSIVE" if peak_i > 120.0 else "NOMINAL"

        md.append(f"| **Battery Pack Temperature** | **{peak_t:.1f} °C** | 45.0 °C / 60.0 °C | {t_status} |")
        md.append(f"| **Charging Current** | **{peak_i:.1f} A** | 150.0 A (HW Limit) | {i_status} |")
        md.append(f"| **Grid Electrical Demand** | **{peak_g:.1f} kW** | 80.0 kW (Depot) | {'HIGH' if peak_g > 50 else 'NORMAL'} |")
        md.append(f"| **BMS Hardware Contactor** | **{'TRIPPED' if tripped else 'CLOSED'}** | Closed | {'FAULT' if tripped else 'HEALTHY'} |\n")

        md.append("## 4. Analytical Observations & Evidence")
        md.append(narrative.observations_section + "\n")
        md.append(narrative.inferred_causal_relationships + "\n")

        if correlation_links:
            md.append("### Inferred Causal Dependency Links")
            md.append("| Event ID | Event Type | Source | Target Signal | Delay (s) | Confidence | Status |")
            md.append("|---|---|---|---|---|---|---|")
            for l in correlation_links:
                md.append(
                    f"| `{l.get('event_id', 'E1')}` | {l.get('event_type', 'CMD')} | `{l.get('source_component', 'evse')}` | "
                    f"`{l.get('target_signal', 'temp')}` | {l.get('delay_seconds', 0.0):.1f}s | "
                    f"{l.get('confidence_score', 0.9):.0%} | {l.get('classification', 'Inferred')} |"
                )
            md.append("")

        md.append("## 5. Counterfactual Replay Verification")
        md.append(narrative.counterfactual_proof_statement + "\n")
        if cf_result and cf_result.get("replay_executed"):
            md.append(f"- **Excised Event:** `{cf_result.get('omitted_event_id', 'N/A')}`")
            md.append(f"- **Original Peak Temp:** {cf_result.get('original_peak_temp', 0.0):.1f} °C")
            md.append(f"- **Replay Peak Temp:** {cf_result.get('counterfactual_peak_temp', 0.0):.1f} °C")
            md.append(f"- **Thermal Delta (ΔT):** {cf_result.get('delta_peak_temp', 0.0):.1f} °C")
            md.append(f"- **Attribution Verdict:** **{cf_result.get('attribution_verdict', 'N/A')}**\n")

        md.append("## 6. Uncertainties & Alternative Explanations")
        md.append(narrative.uncertainties_and_alternatives + "\n")

        md.append("## 7. Recommended Investigative Checklist")
        for idx, act in enumerate(narrative.recommended_investigative_actions, 1):
            md.append(f"{idx}. [ ] {act}")
        md.append("")

        md.append("## 8. Evidence Registry")
        md.append("Referenced evidence tokens logged during analysis:")
        for eid in sorted(narrative.referenced_evidence_ids):
            md.append(f"- `{eid}`")
        md.append("")

        md.append("## 9. Safety & Limitations Disclaimer")
        md.append(f"> {narrative.disclaimer}\n")

        return "\n".join(md)

    @classmethod
    def generate_pdf(
        cls,
        run_data: Dict[str, Any],
        narrative: GroundedNarrative,
        correlation_links: Optional[List[Dict[str, Any]]] = None,
        cf_result: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Constructs a clean, styled PDF document in memory using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0891B2"),
            fontName="Helvetica-Bold",
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            "DocH2",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#172033"),
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=6
        )
        disclaimer_style = ParagraphStyle(
            "DocDisclaimer",
            parent=styles["Italic"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748B"),
            spaceBefore=10
        )

        elements = []

        # Header Title
        run_id = html.escape(str(run_data.get("run_id", "RUN-UNKNOWN")))
        elements.append(Paragraph(f"ThreatLens Incident Report &mdash; {run_id}", title_style))
        elements.append(Paragraph("Category: Cyber-Physical Incident Analysis &middot; Tagline: See the Threat. Trace the Impact. Prove the Difference.", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0891B2"), spaceAfter=10))

        # Executive Summary
        elements.append(Paragraph("1. Executive Summary", heading_style))
        elements.append(Paragraph(html.escape(narrative.executive_summary), body_style))
        elements.append(Spacer(1, 8))

        # Metadata Table
        elements.append(Paragraph("2. Incident & System Metadata", heading_style))
        scn_id = html.escape(str(run_data.get("scenario_id", "SCN-UNKNOWN")))
        scn_name = html.escape(str(run_data.get("scenario_name", "EV Charging Simulation")))
        classification = html.escape(str(run_data.get("classification", "N/A")))
        severity = html.escape(str(run_data.get("severity", "N/A")))

        meta_data = [
            ["Incident ID", run_id, "Scenario ID", scn_id],
            ["Scenario Name", scn_name, "Random Seed", str(run_data.get("seed", 42))],
            ["Classification", classification, "Severity", severity],
            ["Digital Twin", "Lumped Thermal + BMS v2.1", "Mode", "SIMULATION TESTBED"]
        ]
        t_meta = Table(meta_data, colWidths=[110, 155, 110, 155])
        t_meta.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1E293B")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE5EF")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 10))

        # Telemetry Metrics Table
        elements.append(Paragraph("3. Observed Telemetry & Safety Thresholds", heading_style))
        peak_t = float(run_data.get("peak_temperature", 25.0))
        peak_i = float(run_data.get("peak_current", 0.0))
        peak_g = float(run_data.get("peak_grid_load", 0.0))
        tripped = run_data.get("safety_trip_occurred", False)

        telem_data = [
            ["Parameter", "Measured Peak", "Safety Limit", "Assessment"],
            ["Battery Pack Temperature", f"{peak_t:.1f} °C", "45.0°C (Warn) / 60.0°C (Trip)", "CRITICAL" if peak_t >= 60.0 else ("WARNING" if peak_t >= 45.0 else "NOMINAL")],
            ["Charging Current", f"{peak_i:.1f} A", "150.0 A (Hardware Limit)", "HIGH" if peak_i > 120.0 else "NORMAL"],
            ["Grid Active Demand", f"{peak_g:.1f} kW", "80.0 kW (Depot Limit)", "HIGH" if peak_g > 50.0 else "NORMAL"],
            ["BMS Hardware Breaker", "TRIPPED" if tripped else "CLOSED", "Closed", "FAULT" if tripped else "HEALTHY"]
        ]
        t_telem = Table(telem_data, colWidths=[150, 110, 160, 110])
        t_telem.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0891B2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE5EF")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0891B2")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_telem)
        elements.append(Spacer(1, 10))

        # Observations & Causal Proof
        elements.append(Paragraph("4. Causal Inference & Counterfactual Proof", heading_style))
        elements.append(Paragraph(html.escape(narrative.observations_section), body_style))
        elements.append(Paragraph(html.escape(narrative.inferred_causal_relationships), body_style))
        elements.append(Paragraph(html.escape(narrative.counterfactual_proof_statement), body_style))
        elements.append(Spacer(1, 8))

        # Uncertainties & Alternatives
        elements.append(Paragraph("5. Uncertainties & Alternative Non-Attack Hypotheses", heading_style))
        elements.append(Paragraph(html.escape(narrative.uncertainties_and_alternatives), body_style))
        elements.append(Spacer(1, 8))

        # Investigative Checklist
        elements.append(Paragraph("6. Investigator Recommended Verification Checklist", heading_style))
        for act in narrative.recommended_investigative_actions:
            elements.append(Paragraph(f"&bull; [ ] {html.escape(act)}", body_style))
        elements.append(Spacer(1, 8))

        # Disclaimer
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=6))
        elements.append(Paragraph(html.escape(narrative.disclaimer), disclaimer_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
