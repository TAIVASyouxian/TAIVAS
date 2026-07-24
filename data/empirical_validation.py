"""Empirical-validation data helpers for TAIVAS.

This module keeps observed comparison data separate from model inputs. It does
not import Streamlit or call the TAIVAS simulation core.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


TAIVAS_WEATHER_INPUT_COLUMNS = (
    "timestamp",
    "country_key",
    "city_key",
    "lat",
    "lon",
    "population",
    "temperature",
    "wind_speed",
    "solar_radiation",
    "precipitation",
    "humidity",
)

CAPACITY_COLUMNS = (
    "solar_capacity",
    "wind_capacity",
    "geothermal_capacity",
    "hydro_capacity",
    "battery_capacity",
)

OBSERVED_COMPARISON_COLUMNS = (
    "observed_demand_mw",
    "observed_peak_15min_demand_mw",
    "observed_thermal_mw",
    "observed_nuclear_mw",
    "observed_wind_mw",
    "observed_solar_mw",
    "observed_hydro_mw",
    "observed_bioenergy_mw",
    "observed_local_generation_mw",
    "observed_renewable_generation_mw",
    "observed_external_support_mw",
    "observed_battery_net_mw",
    "observed_import_dependency_pct",
    "observed_balance_residual_mw",
)


def read_empirical_validation_csv(source: str | Path) -> tuple[pd.DataFrame, list[str]]:
    """Read a staging CSV without raising UI-level exceptions."""
    try:
        dataframe = pd.read_csv(source)
    except FileNotFoundError:
        return pd.DataFrame(), [f"Empirical validation dataset was not found: {source}"]
    except pd.errors.EmptyDataError:
        return pd.DataFrame(), ["Empirical validation dataset is empty."]
    except pd.errors.ParserError as exc:
        return pd.DataFrame(), [f"Empirical validation dataset could not be parsed: {exc}"]
    except Exception as exc:
        return pd.DataFrame(), [f"Empirical validation dataset could not be loaded: {exc}"]
    return dataframe, []


def _clean_text(value: Any, default: str = "") -> str:
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    return text or default


def _number(value: Any) -> float | None:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return None if pd.isna(parsed) else float(parsed)


def validate_empirical_dataframe(dataframe: pd.DataFrame) -> list[dict[str, str]]:
    """Return non-destructive findings for an empirical-validation dataset."""
    findings: list[dict[str, str]] = []
    if dataframe is None or dataframe.empty:
        return [{
            "severity": "Error",
            "area": "Dataset",
            "message": "No empirical validation rows are available.",
        }]

    missing_columns = [
        column for column in TAIVAS_WEATHER_INPUT_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        findings.append({
            "severity": "Error",
            "area": "TAIVAS weather inputs",
            "message": f"Missing required column(s): {', '.join(missing_columns)}.",
        })

    missing_observed = [
        column for column in (
            "observed_demand_mw",
            "observed_renewable_generation_mw",
            "observed_external_support_mw",
        )
        if column not in dataframe.columns
    ]
    if missing_observed:
        findings.append({
            "severity": "Warning",
            "area": "Observed comparison",
            "message": f"Missing observed comparison column(s): {', '.join(missing_observed)}.",
        })

    if "timestamp" in dataframe.columns:
        timestamps = pd.to_datetime(dataframe["timestamp"], errors="coerce")
        invalid_count = int(timestamps.isna().sum())
        if invalid_count:
            findings.append({
                "severity": "Error",
                "area": "Timestamp",
                "message": f"{invalid_count} timestamp value(s) could not be parsed.",
            })

    key_columns = [
        column for column in ("country_key", "city_key", "timestamp")
        if column in dataframe.columns
    ]
    if len(key_columns) == 3:
        duplicate_count = int(dataframe.duplicated(key_columns).sum())
        if duplicate_count:
            findings.append({
                "severity": "Error",
                "area": "Record identity",
                "message": (
                    f"{duplicate_count} duplicate country/city/timestamp key(s) detected. "
                    "No row was silently overwritten."
                ),
            })

    for column in TAIVAS_WEATHER_INPUT_COLUMNS[3:]:
        if column not in dataframe.columns:
            continue
        invalid_count = int(pd.to_numeric(dataframe[column], errors="coerce").isna().sum())
        if invalid_count:
            findings.append({
                "severity": "Error",
                "area": "TAIVAS weather inputs",
                "message": f"{column} contains {invalid_count} missing or non-numeric value(s).",
            })

    capacity_columns_present = [c for c in CAPACITY_COLUMNS if c in dataframe.columns]
    blank_capacities = {
        column: int(pd.to_numeric(dataframe[column], errors="coerce").isna().sum())
        for column in capacity_columns_present
    }
    if blank_capacities and any(count > 0 for count in blank_capacities.values()):
        findings.append({
            "severity": "Notice",
            "area": "Capacity provenance",
            "message": (
                "Blank capacity fields remain TAIVAS assumption / user input values; "
                "they are not treated as observed French installed capacity."
            ),
        })

    if "data_quality_flag" in dataframe.columns:
        quality_values = sorted({
            _clean_text(value, "missing") for value in dataframe["data_quality_flag"]
        })
        findings.append({
            "severity": "Notice",
            "area": "Data quality",
            "message": f"Dataset quality flag(s): {', '.join(quality_values)}.",
        })
    return findings


def model_inputs_from_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return only the approved weather/geography fields for the TAIVAS core."""
    timestamp = pd.to_datetime(record.get("timestamp"), errors="coerce")
    return {
        "timestamp": (
            timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if not pd.isna(timestamp)
            else _clean_text(record.get("timestamp"))
        ),
        "country_key": _clean_text(record.get("country_key"), "Unknown"),
        "city_key": _clean_text(record.get("city_key"), "Unknown"),
        "lat": _number(record.get("lat")),
        "lon": _number(record.get("lon")),
        "population": _number(record.get("population")),
        "temperature": _number(record.get("temperature")),
        "wind_speed": _number(record.get("wind_speed")),
        "solar_radiation": _number(record.get("solar_radiation")),
        "precipitation": _number(record.get("precipitation")),
        "humidity": _number(record.get("humidity")),
    }


def observed_values_from_record(record: dict[str, Any]) -> dict[str, float | None]:
    """Return observed fields for comparison only, never as model inputs."""
    return {
        column: _number(record.get(column))
        for column in OBSERVED_COMPARISON_COLUMNS
        if column in record
    }


def capacity_provenance_from_record(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Classify capacity values without ever calling them observed data."""
    provenance: dict[str, dict[str, Any]] = {}
    for column in CAPACITY_COLUMNS:
        value = _number(record.get(column))
        if value is None:
            provenance[column] = {
                "csv_value": None,
                "label": "TAIVAS assumption / user input",
                "observed": False,
            }
        else:
            provenance[column] = {
                "csv_value": value,
                "label": "Uploaded capacity input (not observed)",
                "observed": False,
            }
    return provenance


def has_complete_model_inputs(model_inputs: dict[str, Any]) -> bool:
    """Reject records that cannot supply one complete timestamped weather input."""
    required_text = ("timestamp", "country_key", "city_key")
    required_numeric = TAIVAS_WEATHER_INPUT_COLUMNS[3:]
    return all(model_inputs.get(column) for column in required_text) and all(
        model_inputs.get(column) is not None for column in required_numeric
    )


def build_empirical_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    """Build one selectable record per row without city-level overwriting."""
    if dataframe is None or dataframe.empty:
        return []

    records: list[dict[str, Any]] = []
    seen_labels: dict[str, int] = {}
    for row_number, (_, row) in enumerate(dataframe.iterrows(), start=1):
        raw = row.to_dict()
        model_inputs = model_inputs_from_record(raw)
        if not has_complete_model_inputs(model_inputs):
            continue
        country = model_inputs["country_key"]
        city = model_inputs["city_key"]
        timestamp = model_inputs["timestamp"] or f"Row {row_number}"
        base_label = f"{country} / {city} / {timestamp}"
        seen_labels[base_label] = seen_labels.get(base_label, 0) + 1
        selector_label = (
            base_label
            if seen_labels[base_label] == 1
            else f"{base_label} / duplicate row {seen_labels[base_label]}"
        )
        records.append({
            "record_id": f"{country}|{city}|{timestamp}|{row_number}",
            "selector_label": selector_label,
            "row_number": row_number,
            "model_inputs": model_inputs,
            "observed": observed_values_from_record(raw),
            "capacity_provenance": capacity_provenance_from_record(raw),
            "metadata": {
                "capacity_data_status": _clean_text(raw.get("capacity_data_status")),
                "capacity_source": _clean_text(raw.get("capacity_source")),
                "model_spatial_scope": _clean_text(raw.get("model_spatial_scope")),
                "electricity_data_scope": _clean_text(raw.get("electricity_data_scope")),
                "weather_data_scope": _clean_text(raw.get("weather_data_scope")),
                "weather_match_status": _clean_text(raw.get("weather_match_status")),
                "data_quality_flag": _clean_text(raw.get("data_quality_flag")),
                "source_rte": _clean_text(raw.get("source_rte")),
                "source_era5": _clean_text(raw.get("source_era5")),
                "notes": _clean_text(raw.get("notes")),
            },
        })
    return records


def select_empirical_record(
    records: list[dict[str, Any]],
    selector_label: str,
) -> dict[str, Any] | None:
    """Return the exact timestamped record selected in the UI."""
    return next(
        (
            record
            for record in records
            if record.get("selector_label") == selector_label
        ),
        None,
    )


def format_observed_mw_for_display(value: Any) -> str:
    """Format an observed MW value without percentage conversion or scaling."""
    numeric_value = _number(value)
    return "Not available" if numeric_value is None else f"{numeric_value} MW"


def _descriptive_share(numerator: Any, denominator: Any) -> float | None:
    numerator_value = _number(numerator)
    denominator_value = _number(denominator)
    if numerator_value is None or denominator_value in (None, 0.0):
        return None
    return round(numerator_value / denominator_value * 100.0, 2)


def build_empirical_validation_snapshot(
    empirical_record: dict[str, Any] | None,
    simulation_results: dict[str, Any],
) -> dict[str, Any] | None:
    """Build a read-only descriptive comparison without mutating model results."""
    if not empirical_record:
        return None

    model_inputs = dict(empirical_record.get("model_inputs", {}))
    observed = dict(empirical_record.get("observed", {}))
    metadata = dict(empirical_record.get("metadata", {}))
    capacity_provenance = dict(
        empirical_record.get("capacity_provenance", {})
    )
    demand = _number(simulation_results.get("demand"))
    renewable_supply = _number(simulation_results.get("renewable_supply"))
    battery_contribution = _number(
        simulation_results.get(
            "battery_discharge",
            simulation_results.get("battery_contribution"),
        )
    )
    battery_remaining = _number(
        simulation_results.get(
            "battery_levels",
            simulation_results.get("battery_remaining"),
        )
    )
    external_support_proxy = _number(
        simulation_results.get(
            "external_support_need_proxy",
            simulation_results.get("grid_dependency"),
        )
    )
    system_performance = _number(
        simulation_results.get(
            "system_performance_score",
            simulation_results.get("system_efficiency"),
        )
    )
    all_capacities_missing = bool(capacity_provenance) and all(
        item.get("csv_value") is None
        for item in capacity_provenance.values()
    )

    return {
        "selected_observation": {
            key: model_inputs.get(key)
            for key in (
                "timestamp",
                "temperature",
                "wind_speed",
                "solar_radiation",
                "precipitation",
                "humidity",
            )
        },
        "taivas": {
            "simulated_demand_mw": demand,
            "renewable_supply_mw": renewable_supply,
            "external_support_need_proxy_pct": external_support_proxy,
            "battery_contribution_mw": battery_contribution,
            "battery_remaining_mwh": battery_remaining,
            "system_performance_pct": system_performance,
            "risk_tier": simulation_results.get("risk_tier"),
            "descriptive_renewable_share_pct": _descriptive_share(
                renewable_supply, demand
            ),
        },
        "rte": {
            key: observed.get(key)
            for key in (
                "observed_demand_mw",
                "observed_renewable_generation_mw",
                "observed_local_generation_mw",
                "observed_external_support_mw",
                "observed_battery_net_mw",
                "observed_import_dependency_pct",
            )
        }
        | {
            "descriptive_renewable_share_pct": _descriptive_share(
                observed.get("observed_renewable_generation_mw"),
                observed.get("observed_demand_mw"),
            ),
            "descriptive_external_support_share_pct": _descriptive_share(
                observed.get("observed_external_support_mw"),
                observed.get("observed_demand_mw"),
            ),
        },
        "capacity": {
            "all_missing": all_capacities_missing,
            "installed_capacity_label": (
                "TAIVAS assumption / user input"
                if all_capacities_missing
                else "Uploaded capacity input (not observed)"
            ),
            "capacity_source": (
                "Not available in current RTE / ERA5 extracts"
                if all_capacities_missing
                else metadata.get("capacity_source")
                or "Uploaded capacity input (not observed)"
            ),
        },
        "metadata": {
            key: metadata.get(key)
            for key in (
                "electricity_data_scope",
                "weather_data_scope",
                "weather_match_status",
                "data_quality_flag",
                "capacity_data_status",
            )
        },
    }


def summarize_empirical_dataframe(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Return timestamp range and completeness information for display."""
    if dataframe is None or dataframe.empty:
        return {
            "row_count": 0,
            "unique_record_count": 0,
            "time_start": None,
            "time_end": None,
            "missing_weather_values": 0,
            "missing_observed_values": 0,
        }

    timestamps = (
        pd.to_datetime(dataframe["timestamp"], errors="coerce")
        if "timestamp" in dataframe.columns
        else pd.Series(dtype="datetime64[ns]")
    )
    key_columns = [
        column for column in ("country_key", "city_key", "timestamp")
        if column in dataframe.columns
    ]
    missing_weather_values = sum(
        int(dataframe[column].isna().sum())
        for column in TAIVAS_WEATHER_INPUT_COLUMNS
        if column in dataframe.columns
    )
    observed_present = [
        column for column in OBSERVED_COMPARISON_COLUMNS if column in dataframe.columns
    ]
    missing_observed_values = sum(
        int(dataframe[column].isna().sum()) for column in observed_present
    )
    return {
        "row_count": int(len(dataframe)),
        "unique_record_count": (
            int(dataframe[key_columns].drop_duplicates().shape[0])
            if len(key_columns) == 3
            else 0
        ),
        "time_start": (
            timestamps.min().strftime("%Y-%m-%d %H:%M:%S")
            if not timestamps.empty and timestamps.notna().any()
            else None
        ),
        "time_end": (
            timestamps.max().strftime("%Y-%m-%d %H:%M:%S")
            if not timestamps.empty and timestamps.notna().any()
            else None
        ),
        "missing_weather_values": missing_weather_values,
        "missing_observed_values": missing_observed_values,
    }
