"""Validation helpers for TAIVAS data quality checks."""

import pandas as pd


def detect_timestamp_column(df):
    if df is None or df.empty:
        return None
    candidates = [
        "timestamp", "datetime", "date", "time", "recorded_at",
        "created_at", "observation_time", "observed_at",
    ]
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    for column in df.columns:
        name = str(column).strip().lower()
        if "time" in name or "date" in name:
            return column
    return None


def validate_uploaded_dataframe(df, expected_columns=None):
    """Return validation warning dictionaries for uploaded data."""
    findings = []
    if df is None:
        return findings
    if df.empty:
        return [{"Severity": "High", "Area": "Uploaded CSV", "Finding": "Uploaded dataset is empty."}]

    expected_columns = expected_columns or []
    missing = [column for column in expected_columns if column not in df.columns]
    if missing:
        findings.append({
            "Severity": "Moderate",
            "Area": "Uploaded CSV",
            "Finding": f"Missing optional expected column(s): {', '.join(missing)}.",
        })

    duplicate_count = int(df.duplicated().sum())
    if duplicate_count > 0:
        findings.append({
            "Severity": "Moderate",
            "Area": "Uploaded CSV",
            "Finding": f"{duplicate_count} duplicate uploaded row(s) detected.",
        })

    ts_col = detect_timestamp_column(df)
    if ts_col is not None and pd.to_datetime(df[ts_col], errors="coerce").notna().sum() == 0:
        findings.append({
            "Severity": "Moderate",
            "Area": "Uploaded CSV",
            "Finding": "Timestamp column was detected but could not be parsed.",
        })

    numeric_candidates = [
        "population", "temperature", "wind_speed", "solar_radiation",
        "precipitation", "humidity", "solar_capacity", "wind_capacity",
        "geothermal_capacity", "hydro_capacity", "battery_capacity",
    ]
    for column in numeric_candidates:
        if column in df.columns:
            parsed = pd.to_numeric(df[column], errors="coerce")
            if parsed.notna().sum() == 0:
                findings.append({
                    "Severity": "Moderate",
                    "Area": "Uploaded CSV",
                    "Finding": f"Column '{column}' has no parseable numeric values.",
                })
    return findings
