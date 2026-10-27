"""
Scenario Import & Export Service (Feature F05).
Provides strict JSON serialization, version checking, schema validation,
and safe scenario ID assignment to prevent collisions or unsafe executions.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from pydantic import ValidationError

from backend.app.schemas.scenario import ScenarioSchema, ScenarioExportSchema
from backend.app.core.guard import SafeByDesignGuard


class ScenarioImportExport:
    CURRENT_SCHEMA_VERSION = "2.0.0"
    SUPPORTED_VERSIONS = {"1.0.0", "2.0.0"}

    @classmethod
    def export_scenario(cls, scenario: ScenarioSchema) -> Dict[str, Any]:
        """
        Serializes a ScenarioSchema instance to a versioned export envelope.
        """
        export_envelope = ScenarioExportSchema(
            schema_version=cls.CURRENT_SCHEMA_VERSION,
            exported_at=datetime.now(timezone.utc).isoformat(),
            scenario=scenario
        )
        return export_envelope.model_dump()

    @classmethod
    def import_scenario(cls, raw_data: Dict[str, Any]) -> Tuple[ScenarioSchema, str]:
        """
        Validates and imports an external scenario payload.
        Ensures version compatibility, safe parameters, and whitelisted events.
        Assigns a new safe identifier prefix SCN-IMP-XXXX to avoid collisions.
        """
        # 1. Version check
        schema_version = raw_data.get("schema_version")
        if not schema_version or schema_version not in cls.SUPPORTED_VERSIONS:
            raise ValueError(
                f"Unsupported schema version: '{schema_version}'. Supported versions: {list(cls.SUPPORTED_VERSIONS)}"
            )

        scenario_dict = raw_data.get("scenario")
        if not scenario_dict or not isinstance(scenario_dict, dict):
            raise ValueError("Payload missing valid 'scenario' object definition.")

        # 2. Pydantic validation
        try:
            # Temporary ID to validate parsing
            temp_dict = dict(scenario_dict)
            if "scenario_id" not in temp_dict:
                temp_dict["scenario_id"] = "SCN-TEMP"
            
            parsed = ScenarioSchema(**temp_dict)
        except ValidationError as e:
            raise ValueError(f"Scenario validation error: {str(e)}")

        # 3. Safe-by-design guard verification
        SafeByDesignGuard.validate_simulation_parameters(parsed.default_seed, parsed.duration_seconds)

        for ev in parsed.scheduled_events:
            SafeByDesignGuard.validate_event(ev.model_dump())
            if ev.timestamp > parsed.duration_seconds:
                raise ValueError(
                    f"Event {ev.event_id} at {ev.timestamp}s exceeds duration {parsed.duration_seconds}s."
                )

        # 4. Assign safe new ID
        new_id = f"SCN-IMP-{uuid.uuid4().hex[:6].upper()}"
        imported_scenario = parsed.model_copy(update={
            "scenario_id": new_id,
            "name": f"{parsed.name} (Imported)",
            "is_custom": True,
            "is_held_out": False
        })

        return imported_scenario, f"Successfully imported scenario as {new_id}"
