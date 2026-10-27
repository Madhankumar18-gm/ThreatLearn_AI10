"""
Database Repository providing persistent CRUD operations for simulation runs,
correlation links, and counterfactual replays.
"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.database.models import (
    ScenarioModel, SimulationRunModel, CorrelationLinkModel, CounterfactualReplayModel, FleetRunModel
)
from backend.app.schemas.scenario import ScenarioSchema
from backend.app.schemas.simulation import SimulationRunResponse, RunSummary
from backend.app.schemas.analysis import CorrelationLink, CounterfactualResponse, CounterfactualOverlayPoint


class Repository:

    @staticmethod
    def save_scenario(db: Session, scenario: ScenarioSchema) -> ScenarioModel:
        db_scenario = db.query(ScenarioModel).filter(ScenarioModel.scenario_id == scenario.scenario_id).first()
        if not db_scenario:
            db_scenario = ScenarioModel(
                scenario_id=scenario.scenario_id,
                name=scenario.name,
                family=scenario.family,
                description=scenario.description,
                duration_seconds=scenario.duration_seconds,
                default_seed=scenario.default_seed,
                components_json=json.dumps(scenario.components_involved),
                events_json=json.dumps([e.model_dump() for e in scenario.scheduled_events]),
                expected_physical_effects=scenario.expected_physical_effects,
                ground_truth_links_json=json.dumps([l.model_dump() for l in scenario.ground_truth_links]),
                expected_outcome=scenario.expected_outcome,
                safety_limitations=scenario.safety_limitations
            )
            db.add(db_scenario)
        else:
            db_scenario.name = scenario.name
            db_scenario.family = scenario.family
            db_scenario.description = scenario.description
            db_scenario.duration_seconds = scenario.duration_seconds
            db_scenario.default_seed = scenario.default_seed
            db_scenario.components_json = json.dumps(scenario.components_involved)
            db_scenario.events_json = json.dumps([e.model_dump() for e in scenario.scheduled_events])
            db_scenario.expected_physical_effects = scenario.expected_physical_effects
            db_scenario.ground_truth_links_json = json.dumps([l.model_dump() for l in scenario.ground_truth_links])
            db_scenario.expected_outcome = scenario.expected_outcome
            db_scenario.safety_limitations = scenario.safety_limitations
        db.commit()
        db.refresh(db_scenario)
        return db_scenario

    @staticmethod
    def get_all_scenarios(db: Session) -> List[ScenarioModel]:
        return db.query(ScenarioModel).all()

    @staticmethod
    def get_scenario(db: Session, scenario_id: str) -> Optional[ScenarioModel]:
        return db.query(ScenarioModel).filter(ScenarioModel.scenario_id == scenario_id).first()

    @staticmethod
    def save_run(db: Session, run_data: SimulationRunResponse) -> SimulationRunModel:
        db_run = SimulationRunModel(
            run_id=run_data.run_id,
            scenario_id=run_data.scenario_id,
            scenario_name=run_data.scenario_name,
            scenario_family=run_data.scenario_family,
            seed=run_data.seed,
            duration_seconds=run_data.duration_seconds,
            is_counterfactual=run_data.is_counterfactual,
            omitted_event_id=run_data.omitted_event_id,
            peak_current=run_data.peak_current,
            peak_temperature=run_data.peak_temperature,
            final_soc=run_data.final_soc,
            fault_triggered=run_data.fault_triggered,
            status=run_data.status,
            created_at=run_data.created_at,
            events_json=json.dumps([e.model_dump() for e in run_data.events]),
            telemetry_json=json.dumps([t.model_dump() for t in run_data.telemetry]),
            threshold_crossings_json=json.dumps([c.model_dump() for c in run_data.threshold_crossings])
        )
        db.add(db_run)
        db.commit()
        db.refresh(db_run)
        return db_run

    @staticmethod
    def get_runs(db: Session, limit: int = 50) -> List[RunSummary]:
        runs = db.query(SimulationRunModel).order_by(SimulationRunModel.created_at.desc()).limit(limit).all()
        return [
            RunSummary(
                run_id=r.run_id,
                scenario_id=r.scenario_id,
                scenario_name=r.scenario_name,
                scenario_family=r.scenario_family,
                seed=r.seed,
                duration_seconds=r.duration_seconds,
                created_at=r.created_at,
                status=r.status,
                is_counterfactual=r.is_counterfactual,
                omitted_event_id=r.omitted_event_id,
                peak_current=r.peak_current,
                peak_temperature=r.peak_temperature,
                fault_triggered=r.fault_triggered
            )
            for r in runs
        ]

    @staticmethod
    def get_run(db: Session, run_id: str) -> Optional[SimulationRunResponse]:
        r = db.query(SimulationRunModel).filter(SimulationRunModel.run_id == run_id).first()
        if not r:
            return None
        return SimulationRunResponse(
            run_id=r.run_id,
            scenario_id=r.scenario_id,
            scenario_name=r.scenario_name,
            scenario_family=r.scenario_family,
            seed=r.seed,
            duration_seconds=r.duration_seconds,
            created_at=r.created_at,
            status=r.status,
            is_counterfactual=r.is_counterfactual,
            omitted_event_id=r.omitted_event_id,
            events=json.loads(r.events_json),
            telemetry=json.loads(r.telemetry_json),
            peak_current=r.peak_current,
            peak_temperature=r.peak_temperature,
            final_soc=r.final_soc,
            fault_triggered=r.fault_triggered,
            threshold_crossings=json.loads(r.threshold_crossings_json or "[]")
        )

    @staticmethod
    def save_correlation_links(db: Session, run_id: str, links: List[CorrelationLink]) -> None:
        # Clear existing links for this run if any
        db.query(CorrelationLinkModel).filter(CorrelationLinkModel.run_id == run_id).delete()
        for link in links:
            db_link = CorrelationLinkModel(
                link_id=link.link_id,
                run_id=run_id,
                event_id=link.event_id,
                event_type=link.event_type,
                source=link.source,
                target_signal=link.target_signal,
                target_component=link.target_component,
                dependency_path_json=json.dumps(link.dependency_path),
                time_delay=link.time_delay,
                observed_change=link.observed_change,
                change_unit=link.change_unit,
                confidence_score=link.confidence_score,
                evidence_label=link.evidence_label.value if hasattr(link.evidence_label, "value") else str(link.evidence_label),
                rules_matched_json=json.dumps(link.rules_matched),
                explanation=link.explanation,
                uncertainty_notes=link.uncertainty_notes
            )
            db.add(db_link)
        db.commit()

    @staticmethod
    def get_correlation_links(db: Session, run_id: str) -> List[CorrelationLink]:
        links = db.query(CorrelationLinkModel).filter(CorrelationLinkModel.run_id == run_id).all()
        return [
            CorrelationLink(
                link_id=l.link_id,
                event_id=l.event_id,
                event_type=l.event_type,
                source=l.source,
                target_signal=l.target_signal,
                target_component=l.target_component,
                dependency_path=json.loads(l.dependency_path_json),
                time_delay=l.time_delay,
                observed_change=l.observed_change,
                change_unit=l.change_unit,
                confidence_score=l.confidence_score,
                evidence_label=l.evidence_label,
                rules_matched=json.loads(l.rules_matched_json),
                explanation=l.explanation,
                uncertainty_notes=l.uncertainty_notes
            )
            for l in links
        ]

    @staticmethod
    def save_counterfactual_replay(db: Session, cf: CounterfactualResponse) -> CounterfactualReplayModel:
        db_cf = CounterfactualReplayModel(
            counterfactual_id=f"CF-{cf.original_run_id}-{cf.target_event_id}",
            original_run_id=cf.original_run_id,
            counterfactual_run_id=cf.counterfactual_run_id,
            target_event_id=cf.target_event_id,
            seed_used=cf.seed_used,
            peak_current_diff=cf.peak_current_diff,
            peak_temp_diff=cf.peak_temp_diff,
            final_soc_diff=cf.final_soc_diff,
            effect_attribution=cf.effect_attribution,
            is_causally_proven=cf.is_causally_proven,
            summary=cf.summary,
            limitations=cf.limitations,
            overlay_json=json.dumps([p.model_dump() for p in cf.overlay_data])
        )
        db.add(db_cf)
        db.commit()
        db.refresh(db_cf)
        return db_cf

    @staticmethod
    def get_counterfactual_for_run(db: Session, original_run_id: str, target_event_id: Optional[str] = None) -> Optional[CounterfactualResponse]:
        query = db.query(CounterfactualReplayModel).filter(CounterfactualReplayModel.original_run_id == original_run_id)
        if target_event_id:
            query = query.filter(CounterfactualReplayModel.target_event_id == target_event_id)
        cf = query.order_by(CounterfactualReplayModel.created_at.desc()).first()
        if not cf:
            return None
        return CounterfactualResponse(
            original_run_id=cf.original_run_id,
            counterfactual_run_id=cf.counterfactual_run_id,
            target_event_id=cf.target_event_id,
            seed_used=cf.seed_used,
            peak_current_diff=cf.peak_current_diff,
            peak_temp_diff=cf.peak_temp_diff,
            final_soc_diff=cf.final_soc_diff,
            effect_attribution=cf.effect_attribution,
            is_causally_proven=cf.is_causally_proven,
            summary=cf.summary,
            limitations=cf.limitations,
            overlay_data=[CounterfactualOverlayPoint(**p) for p in json.loads(cf.overlay_json)]
        )

    @staticmethod
    def save_fleet_run(db: Session, fleet_run: Any) -> FleetRunModel:
        db_fleet = FleetRunModel(
            run_id=fleet_run.run_id,
            fleet_scenario_id=fleet_run.fleet_scenario_id,
            charger_count=fleet_run.charger_count,
            feeder_capacity_kw=fleet_run.feeder_capacity_kw,
            peak_fleet_power_kw=fleet_run.peak_fleet_power_kw,
            peak_feeder_loading_pct=fleet_run.peak_feeder_loading_pct,
            min_feeder_voltage_v=fleet_run.min_feeder_voltage_v,
            overload_duration_seconds=fleet_run.overload_duration_seconds,
            affected_chargers_json=json.dumps(fleet_run.affected_chargers),
            summary_json=json.dumps(fleet_run.summary)
        )
        db.add(db_fleet)
        db.commit()
        db.refresh(db_fleet)
        return db_fleet

    @staticmethod
    def get_fleet_runs(db: Session, limit: int = 20) -> List[FleetRunModel]:
        return db.query(FleetRunModel).order_by(FleetRunModel.created_at.desc()).limit(limit).all()
