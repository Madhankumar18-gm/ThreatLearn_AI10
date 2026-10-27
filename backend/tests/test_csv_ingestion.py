"""
Comprehensive automated tests for ThreatLens CSV & Telemetry Ingestion Wizard (F17, F19).
Verifies:
1. Header detection and fuzzy column mapping for all 6 columns:
   timestamp, component_id, signal, value, unit, quality.
2. ISO 8601 UTC timestamp parsing ('2026-10-26T09:00:00Z' etc.) without year-like decimal artifacts.
3. Accurate processing of all 40 rows from threatlens_sample_telemetry.csv.
4. Mathematical invariant: valid_rows_count + rejected_rows_count == total_submitted.
5. Row-specific rejection reasons on corrupted rows.
6. Clock skew offset alignment and readable time window calculation.
7. Persistence and retrieval of committed datasets.
8. Backward compatibility with pure relative seconds numeric timestamps.
"""

import os
import pytest
from backend.app.schemas.ingestion import (
    CSVColumnMapping,
    IngestionCommitRequest,
)
from backend.app.ingestion.csv_importer import CSVImporter


@pytest.fixture(scope="module")
def sample_csv_content():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "threatlens_sample_telemetry.csv")
    with open(sample_path, "r", encoding="utf-8") as f:
        return f.read()


def test_threatlens_sample_preview_mapping(sample_csv_content):
    """Verifies that all 6 columns are correctly mapped and 40 total rows are detected."""
    preview = CSVImporter.preview_csv("threatlens_sample_telemetry.csv", sample_csv_content)

    assert preview.total_rows == 40
    assert len(preview.sample_rows) == 10
    assert preview.detected_data_type == "telemetry"
    assert preview.time_format == "iso8601"
    assert preview.base_timestamp == "2026-10-26T09:00:00Z"
    assert preview.duration_seconds == 39.0

    mapping = preview.inferred_mapping
    assert mapping.timestamp_col == "timestamp"
    assert mapping.component_col == "component_id"
    assert mapping.signal_col == "signal"
    assert mapping.value_col == "value"
    assert mapping.unit_col == "unit"
    assert mapping.quality_col == "quality"


def test_threatlens_sample_commit_all_40_rows(sample_csv_content):
    """Verifies all 40 rows are processed, 40 valid, 0 rejected, with correct time range."""
    preview = CSVImporter.preview_csv("threatlens_sample_telemetry.csv", sample_csv_content)

    req = IngestionCommitRequest(
        filename="threatlens_sample_telemetry.csv",
        data_type="telemetry",
        mapping=preview.inferred_mapping,
        raw_content=sample_csv_content,
        clock_skew_offset=0.0
    )

    report, valid_rows = CSVImporter.validate_and_commit(req)

    assert report.total_submitted == 40
    assert report.valid_rows_count == 40
    assert report.rejected_rows_count == 0
    assert report.total_submitted == report.valid_rows_count + report.rejected_rows_count
    assert len(valid_rows) == 40

    # Time range check: 0.0s to 39.0s (not 2026.00s)
    time_range = report.aligned_time_range
    assert time_range["min_timestamp"] == 0.0
    assert time_range["max_timestamp"] == 39.0
    assert time_range["duration_seconds"] == 39.0
    assert "0.00s – 39.00s" in time_range["readable_window"]
    assert "2026-10-26T09:00:00Z" in time_range["readable_window"]
    assert "2026-10-26T09:00:39Z" in time_range["readable_window"]

    # Verify canonical row structure
    first_row = valid_rows[0]
    assert first_row["timestamp"] == 0.0
    assert first_row["elapsed_seconds"] == 0.0
    assert first_row["iso_timestamp"] == "2026-10-26T09:00:00Z"
    assert first_row["aligned_iso_timestamp"] == "2026-10-26T09:00:00Z"
    assert first_row["component"] == "evse_controller"
    assert first_row["component_id"] == "evse_controller"
    assert first_row["signal"] == "charging_current"
    assert first_row["value"] == 0.0
    assert first_row["unit"] == "A"
    assert first_row["quality"] == "GOOD"

    last_row = valid_rows[-1]
    assert last_row["timestamp"] == 39.0
    assert last_row["elapsed_seconds"] == 39.0
    assert last_row["iso_timestamp"] == "2026-10-26T09:00:39Z"
    assert last_row["component"] == "battery_pack"
    assert last_row["signal"] == "battery_temperature"
    assert last_row["value"] == 32.8
    assert last_row["unit"] == "C"
    assert last_row["quality"] == "GOOD"


def test_threatlens_sample_commit_with_clock_skew(sample_csv_content):
    """Verifies clock skew offset shifts aligned elapsed time and ISO timestamps correctly."""
    preview = CSVImporter.preview_csv("threatlens_sample_telemetry.csv", sample_csv_content)

    req = IngestionCommitRequest(
        filename="threatlens_sample_telemetry.csv",
        data_type="telemetry",
        mapping=preview.inferred_mapping,
        raw_content=sample_csv_content,
        clock_skew_offset=2.5  # +2.5 seconds clock skew
    )

    report, valid_rows = CSVImporter.validate_and_commit(req)

    assert report.total_submitted == 40
    assert report.valid_rows_count == 40
    assert report.rejected_rows_count == 0

    time_range = report.aligned_time_range
    assert time_range["min_timestamp"] == 2.5
    assert time_range["max_timestamp"] == 41.5
    assert time_range["duration_seconds"] == 39.0

    # First row aligned: 0.0 + 2.5 = 2.5s, ISO: 09:00:02.500Z -> 09:00:02Z
    assert valid_rows[0]["timestamp"] == 2.5
    assert valid_rows[0]["elapsed_seconds"] == 0.0
    assert valid_rows[0]["aligned_iso_timestamp"] == "2026-10-26T09:00:02Z"

    # Persistence verification
    saved_ds = CSVImporter.get_dataset(report.dataset_id)
    assert saved_ds is not None
    assert saved_ds["row_count"] == 40
    assert saved_ds["filename"] == "threatlens_sample_telemetry.csv"


def test_rejection_reasons_and_invariant():
    """Verifies corrupt rows produce row-specific rejections and valid + rejected == total."""
    dirty_csv = (
        "timestamp,component_id,signal,value,unit,quality\n"
        "2026-10-26T09:00:00Z,evse,charging_current,10.0,A,GOOD\n"
        ",evse,charging_current,15.0,A,GOOD\n"  # Missing timestamp
        "not-a-timestamp,evse,charging_current,20.0,A,GOOD\n"  # Invalid timestamp
        "2026-10-26T09:00:03Z,evse,charging_current,,A,GOOD\n"  # Missing measurement value
        "2026-10-26T09:00:04Z,battery_pack,battery_temperature,28.5,C,GOOD\n"
    )

    preview = CSVImporter.preview_csv("dirty.csv", dirty_csv)
    assert preview.total_rows == 5

    req = IngestionCommitRequest(
        filename="dirty.csv",
        data_type="telemetry",
        mapping=preview.inferred_mapping,
        raw_content=dirty_csv,
        clock_skew_offset=0.0
    )

    report, valid_rows = CSVImporter.validate_and_commit(req)

    assert report.total_submitted == 5
    assert report.valid_rows_count == 2
    assert report.rejected_rows_count == 3
    assert report.valid_rows_count + report.rejected_rows_count == report.total_submitted
    assert len(report.rejections) == 3

    # Check row-specific rejection reasons
    rejection_rows = [r.row_index for r in report.rejections]
    assert rejection_rows == [2, 3, 4]
    assert "Missing timestamp" in report.rejections[0].reason
    assert "Invalid timestamp" in report.rejections[1].reason
    assert "Missing measurement value" in report.rejections[2].reason


def test_backward_compatibility_relative_numeric_timestamps():
    """Verifies relative numeric timestamps (e.g. Tier 1/2 test cases) work without issue."""
    numeric_csv = (
        "timestamp,component,signal,value\n"
        "0.0,evse,charging_current,0.0\n"
        "5.0,evse,charging_current,50.0\n"
        "10.0,evse,charging_current,80.0\n"
    )

    preview = CSVImporter.preview_csv("numeric.csv", numeric_csv)
    assert preview.total_rows == 3

    req = IngestionCommitRequest(
        filename="numeric.csv",
        data_type="telemetry",
        mapping=preview.inferred_mapping,
        rows=preview.sample_rows,
        clock_skew_offset=1.5
    )

    report, valid_rows = CSVImporter.validate_and_commit(req)

    assert report.total_submitted == 3
    assert report.valid_rows_count == 3
    assert report.rejected_rows_count == 0
    assert valid_rows[0]["timestamp"] == 1.5
    assert valid_rows[1]["timestamp"] == 6.5
    assert valid_rows[2]["timestamp"] == 11.5
    assert report.aligned_time_range["min_timestamp"] == 1.5
    assert report.aligned_time_range["max_timestamp"] == 11.5
