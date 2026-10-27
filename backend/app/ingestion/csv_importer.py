"""
CSV and Log Ingestion Service (Feature F17, F19).
Provides CSV upload preview, header detection, fuzzy column mapping,
data type classification, row validation, ISO 8601 & numeric timestamp alignment,
and sanitization into ThreatLens canonical format.
"""

import csv
import io
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple, Optional
from backend.app.schemas.ingestion import (
    CSVColumnMapping,
    CSVPreviewResponse,
    IngestionCommitRequest,
    IngestionValidationReport,
    RowRejection,
)


class CSVImporter:

    HEADER_SYNONYMS = {
        "timestamp_col": ["timestamp", "time", "ts", "seconds", "sec", "datetime", "epoch", "utc_timestamp", "date_time", "iso_timestamp"],
        "component_col": ["component_id", "component", "device", "subsystem", "module", "node", "asset_id", "target"],
        "event_type_col": ["event_type", "event", "action", "command", "type", "message_type"],
        "signal_col": ["signal", "signal_name", "metric", "measurement", "sensor", "variable", "channel"],
        "value_col": ["value", "reading", "val", "data", "measurement_value"],
        "unit_col": ["unit", "units", "dim", "engineering_unit"],
        "quality_col": ["quality", "quality_flag", "data_quality", "confidence", "flag", "validity", "status_quality"],
        "auth_status_col": ["auth_status", "auth", "authorized", "status"],
        "source_col": ["source", "origin", "sender", "protocol"]
    }

    # In-memory store for committed datasets
    _COMMITTED_DATASETS: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def preview_csv(cls, filename: str, content_str: str) -> CSVPreviewResponse:
        """
        Parses CSV string, detects headers, infers canonical column mappings,
        determines timestamp format, and returns preview with sample rows.
        """
        f = io.StringIO(content_str.strip())
        reader = csv.reader(f)
        try:
            headers = [h.strip() for h in next(reader)]
        except StopIteration:
            raise ValueError("Uploaded file is empty.")

        sample_rows: List[Dict[str, Any]] = []
        all_timestamps: List[Any] = []
        total_rows = 0

        inferred_mapping = cls._infer_mapping(headers)
        ts_col = inferred_mapping.timestamp_col

        for row in reader:
            if not any(row):  # Skip empty lines
                continue
            total_rows += 1
            row_dict = {headers[i]: (row[i].strip() if i < len(row) else "") for i in range(len(headers))}
            if len(sample_rows) < 10:
                sample_rows.append(row_dict)
            if ts_col in row_dict and row_dict[ts_col]:
                all_timestamps.append(row_dict[ts_col])

        detected_type = cls._classify_data_type(headers)

        # Detect timestamp format and base/duration
        time_format = "relative_seconds"
        base_ts_str: Optional[str] = None
        duration_sec: Optional[float] = None

        if all_timestamps:
            has_iso = any(isinstance(t, str) and ("-" in t or "T" in t or ":" in t) for t in all_timestamps[:20])
            if has_iso:
                time_format = "iso8601"
                dts = []
                for t in all_timestamps:
                    dt = cls._parse_iso_datetime(str(t))
                    if dt:
                        dts.append(dt)
                if dts:
                    min_dt = min(dts)
                    max_dt = max(dts)
                    base_ts_str = min_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    duration_sec = round((max_dt - min_dt).total_seconds(), 3)
            else:
                try:
                    num_ts = [float(str(t).strip()) for t in all_timestamps if str(t).strip()]
                    if num_ts:
                        min_t = min(num_ts)
                        max_t = max(num_ts)
                        duration_sec = round(max_t - min_t, 3)
                        if min_t > 1e9:
                            time_format = "epoch"
                            base_ts_str = datetime.fromtimestamp(min_t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    pass

        return CSVPreviewResponse(
            filename=filename,
            total_rows=total_rows,
            headers=headers,
            sample_rows=sample_rows,
            inferred_mapping=inferred_mapping,
            detected_data_type=detected_type,
            time_format=time_format,
            base_timestamp=base_ts_str,
            duration_seconds=duration_sec
        )

    @classmethod
    def _parse_iso_datetime(cls, s: str) -> Optional[datetime]:
        """Parses ISO 8601 UTC timestamp string safely."""
        clean = s.strip()
        if not clean:
            return None
        # Handle trailing Z
        if clean.endswith("Z"):
            clean = clean[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

        try:
            import dateutil.parser
            dt = dateutil.parser.parse(s.strip())
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    @classmethod
    def _infer_mapping(cls, headers: List[str]) -> CSVColumnMapping:
        """Fuzzy matches headers against synonym dictionary."""
        mapping: Dict[str, str] = {}
        lower_headers = {h.lower(): h for h in headers}

        for target_field, synonyms in cls.HEADER_SYNONYMS.items():
            matched = None
            for syn in synonyms:
                for h_lower, orig in lower_headers.items():
                    if syn == h_lower or syn in h_lower.split("_") or h_lower in syn.split("_") or h_lower.startswith(syn):
                        matched = orig
                        break
                if matched:
                    break
            if matched:
                mapping[target_field] = matched

        # Fallback for timestamp if not matched
        if "timestamp_col" not in mapping and headers:
            mapping["timestamp_col"] = headers[0]

        return CSVColumnMapping(
            timestamp_col=mapping.get("timestamp_col", headers[0] if headers else "timestamp"),
            component_col=mapping.get("component_col"),
            event_type_col=mapping.get("event_type_col"),
            signal_col=mapping.get("signal_col"),
            value_col=mapping.get("value_col"),
            unit_col=mapping.get("unit_col"),
            quality_col=mapping.get("quality_col"),
            auth_status_col=mapping.get("auth_status_col"),
            source_col=mapping.get("source_col")
        )

    @classmethod
    def _classify_data_type(cls, headers: List[str]) -> str:
        h_str = " ".join(headers).lower()
        has_event_clues = any(k in h_str for k in ["event", "command", "source", "action", "auth"])
        has_telem_clues = any(k in h_str for k in ["temp", "current", "volt", "soc", "reading", "value", "signal", "quality", "unit"])

        if has_event_clues and not has_telem_clues:
            return "events"
        elif has_telem_clues and not has_event_clues:
            return "telemetry"
        return "telemetry" if "signal" in h_str else "mixed"

    @classmethod
    def validate_and_commit(cls, req: IngestionCommitRequest) -> Tuple[IngestionValidationReport, List[Dict[str, Any]]]:
        """
        Validates mapped records, parses ISO 8601 and numeric timestamps, applies clock offset,
        sanitizes fields into ThreatLens canonical format, and records row-specific rejections.
        """
        # Step 1: Collect all raw rows to process
        rows_to_process: List[Dict[str, Any]] = []

        if req.raw_content and req.raw_content.strip():
            f = io.StringIO(req.raw_content.strip())
            reader = csv.reader(f)
            try:
                headers = [h.strip() for h in next(reader)]
            except StopIteration:
                raise ValueError("Uploaded raw_content is empty.")

            for row in reader:
                if not any(row):  # Skip empty lines
                    continue
                row_dict = {headers[i]: (row[i].strip() if i < len(row) else "") for i in range(len(headers))}
                rows_to_process.append(row_dict)
        elif req.rows is not None:
            rows_to_process = req.rows
        else:
            raise ValueError("No rows or raw_content provided for validation.")

        total_submitted = len(rows_to_process)
        ts_col = req.mapping.timestamp_col
        offset = float(req.clock_skew_offset or 0.0)

        # Step 2: Pre-scan timestamps to determine if they are ISO 8601 datetimes
        parsed_dts: Dict[int, datetime] = {}
        parsed_nums: Dict[int, float] = {}
        row_raw_ts: Dict[int, Any] = {}

        for idx, row in enumerate(rows_to_process, start=1):
            if ts_col in row and row[ts_col] is not None and str(row[ts_col]).strip() != "":
                raw_val = str(row[ts_col]).strip()
                row_raw_ts[idx] = raw_val
                if "-" in raw_val or "T" in raw_val or ":" in raw_val:
                    dt = cls._parse_iso_datetime(raw_val)
                    if dt:
                        parsed_dts[idx] = dt
                else:
                    try:
                        parsed_nums[idx] = float(raw_val)
                    except ValueError:
                        pass

        # If majority are datetimes, determine base datetime
        has_datetimes = len(parsed_dts) > 0
        base_dt: Optional[datetime] = min(parsed_dts.values()) if has_datetimes else None

        valid_rows: List[Dict[str, Any]] = []
        rejections: List[RowRejection] = []
        errors: List[str] = []
        warnings: List[str] = []

        # Step 3: Process and validate each row
        for idx, row in enumerate(rows_to_process, start=1):
            # Check 1: Timestamp exists
            if ts_col not in row or row[ts_col] is None or str(row[ts_col]).strip() == "":
                rej = RowRejection(
                    row_index=idx,
                    reason=f"Row {idx}: Missing timestamp value in column '{ts_col}'.",
                    column=ts_col,
                    raw_value=str(row.get(ts_col, ""))
                )
                rejections.append(rej)
                errors.append(rej.reason)
                continue

            raw_ts = str(row[ts_col]).strip()

            # Check 2: Parse timestamp
            orig_ts_val: Any = raw_ts
            aligned_elapsed: float = 0.0
            elapsed_sec: float = 0.0
            raw_iso: Optional[str] = None
            aligned_iso: Optional[str] = None

            if idx in parsed_dts:
                dt = parsed_dts[idx]
                raw_iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                elapsed_sec = max(0.0, round((dt - base_dt).total_seconds(), 3)) if base_dt else 0.0
                aligned_elapsed = max(0.0, round(elapsed_sec + offset, 3))
                aligned_dt = dt + timedelta(seconds=offset)
                aligned_iso = aligned_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            elif idx in parsed_nums:
                f_val = parsed_nums[idx]
                if f_val > 1e9:  # Epoch seconds
                    epoch_dt = datetime.fromtimestamp(f_val, tz=timezone.utc)
                    raw_iso = epoch_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    aligned_dt = epoch_dt + timedelta(seconds=offset)
                    aligned_iso = aligned_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    elapsed_sec = f_val
                    aligned_elapsed = max(0.0, round(f_val + offset, 3))
                else:  # Relative seconds
                    elapsed_sec = f_val
                    aligned_elapsed = max(0.0, round(f_val + offset, 3))
            else:
                # Timestamp parsing failed
                rej = RowRejection(
                    row_index=idx,
                    reason=f"Row {idx}: Invalid timestamp '{raw_ts}' (cannot parse as ISO 8601 datetime or numeric seconds).",
                    column=ts_col,
                    raw_value=raw_ts
                )
                rejections.append(rej)
                errors.append(rej.reason)
                continue

            # Check 3: Component & Signal (if mapped)
            comp_val = ""
            if req.mapping.component_col and req.mapping.component_col in row:
                comp_val = str(row[req.mapping.component_col]).strip()

            signal_val = ""
            if req.mapping.signal_col and req.mapping.signal_col in row:
                signal_val = str(row[req.mapping.signal_col]).strip()

            # Check 4: Value (if mapped)
            val_col = req.mapping.value_col
            parsed_value: Any = None
            if val_col and val_col in row:
                raw_measurement = str(row[val_col]).strip()
                if raw_measurement == "" and signal_val:
                    rej = RowRejection(
                        row_index=idx,
                        reason=f"Row {idx}: Missing measurement value for signal '{signal_val}' in column '{val_col}'.",
                        column=val_col,
                        raw_value=raw_measurement
                    )
                    rejections.append(rej)
                    errors.append(rej.reason)
                    continue

                try:
                    parsed_value = float(raw_measurement)
                except ValueError:
                    parsed_value = raw_measurement

            # Check 5: Unit & Quality
            unit_val = ""
            if req.mapping.unit_col and req.mapping.unit_col in row:
                unit_val = str(row[req.mapping.unit_col]).strip()

            quality_val = "GOOD"
            if req.mapping.quality_col and req.mapping.quality_col in row:
                quality_val = str(row[req.mapping.quality_col]).strip()

            # Construct canonical row
            canonical_row: Dict[str, Any] = {
                "original_timestamp": orig_ts_val,
                "timestamp": aligned_elapsed,
                "elapsed_seconds": elapsed_sec,
                "iso_timestamp": raw_iso,
                "aligned_iso_timestamp": aligned_iso,
                "component": comp_val,
                "component_id": comp_val,
                "signal": signal_val,
                "value": parsed_value,
                "unit": unit_val,
                "quality": quality_val,
                "raw_data": row
            }

            # Optional event attributes
            if req.mapping.event_type_col and req.mapping.event_type_col in row:
                canonical_row["event_type"] = str(row[req.mapping.event_type_col]).strip()
            if req.mapping.auth_status_col and req.mapping.auth_status_col in row:
                canonical_row["auth_status"] = str(row[req.mapping.auth_status_col]).strip()
            if req.mapping.source_col and req.mapping.source_col in row:
                canonical_row["source"] = str(row[req.mapping.source_col]).strip()

            valid_rows.append(canonical_row)

        # Step 4: Calculate aligned time range
        if valid_rows:
            min_ts = min(r["timestamp"] for r in valid_rows)
            max_ts = max(r["timestamp"] for r in valid_rows)
            duration_sec = round(max_ts - min_ts, 3)

            iso_start = next((r["aligned_iso_timestamp"] for r in valid_rows if r.get("aligned_iso_timestamp")), None)
            iso_end = next((r["aligned_iso_timestamp"] for r in reversed(valid_rows) if r.get("aligned_iso_timestamp")), None)

            if iso_start and iso_end:
                readable_window = f"{min_ts:.2f}s – {max_ts:.2f}s ({iso_start} – {iso_end})"
            else:
                readable_window = f"{min_ts:.2f}s – {max_ts:.2f}s"
        else:
            min_ts = 0.0
            max_ts = 0.0
            duration_sec = 0.0
            readable_window = "0.00s – 0.00s"
            iso_start = None
            iso_end = None

        dataset_id = f"DS-{uuid.uuid4().hex[:8].upper()}"

        report = IngestionValidationReport(
            dataset_id=dataset_id,
            total_submitted=total_submitted,
            valid_rows_count=len(valid_rows),
            rejected_rows_count=len(rejections),
            warnings=warnings,
            errors=errors,
            rejections=rejections,
            aligned_time_range={
                "min_timestamp": min_ts,
                "max_timestamp": max_ts,
                "duration_seconds": duration_sec,
                "readable_window": readable_window,
                "iso_start": iso_start,
                "iso_end": iso_end
            }
        )

        # Step 5: Store in committed datasets registry (F17 persistence)
        cls._COMMITTED_DATASETS[dataset_id] = {
            "dataset_id": dataset_id,
            "filename": req.filename,
            "data_type": req.data_type,
            "report": report.model_dump(),
            "valid_rows": valid_rows,
            "row_count": len(valid_rows),
            "committed_at": datetime.now(timezone.utc).isoformat()
        }

        return report, valid_rows

    @classmethod
    def get_dataset(cls, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves committed dataset by ID."""
        return cls._COMMITTED_DATASETS.get(dataset_id)

    @classmethod
    def list_datasets(cls) -> List[Dict[str, Any]]:
        """Lists metadata of all committed datasets."""
        return [
            {
                "dataset_id": d["dataset_id"],
                "filename": d["filename"],
                "data_type": d["data_type"],
                "row_count": d["row_count"],
                "committed_at": d["committed_at"]
            }
            for d in cls._COMMITTED_DATASETS.values()
        ]
