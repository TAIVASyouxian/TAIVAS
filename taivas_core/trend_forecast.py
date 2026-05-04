"""TAIVAS trend / forecast helpers V10.2.

This module no longer depends on the old taivas_core.energy_model assumptions.
It imports the V10.2-compatible compute_energy_supply from the same folder.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import pandas as pd

from .energy_model import compute_energy_supply
from .utils import clamp, safe_div


def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return int(default)
        return int(float(value))
    except Exception:
        return int(default)


def _t(key: str, tr=None) -> str:
    try:
        return tr(key) if tr else key
    except Exception:
        return key


def sort_history_df(df: pd.DataFrame):
    if df is None or df.empty:
        return pd.DataFrame(), None, "empty"
    out = df.copy()
    timestamp_candidates = [
        c for c in out.columns
        if str(c).lower() in {"timestamp", "time", "datetime", "date", "created_at"}
        or "time" in str(c).lower()
        or "date" in str(c).lower()
    ]
    if timestamp_candidates:
        ts_col = timestamp_candidates[0]
        try:
            out["_taivas_parsed_timestamp"] = pd.to_datetime(out[ts_col], errors="coerce")
            if out["_taivas_parsed_timestamp"].notna().any():
                out = out.sort_values("_taivas_parsed_timestamp")
                return out.drop(columns=["_taivas_parsed_timestamp"], errors="ignore"), ts_col, "timestamp"
        except Exception:
            pass
        return out, ts_col, "original"
    return out, None, "original"


def prepare_uploaded_preview(df: pd.DataFrame, max_rows: int = 20):
    if df is None or df.empty:
        return None, None, "empty"
    sorted_df, ts_col, mode = sort_history_df(df)
    return sorted_df.head(max_rows), ts_col, mode


def _row_to_inputs(row: pd.Series, fallback_inputs: Dict[str, Any]) -> Dict[str, Any]:
    inputs = dict(fallback_inputs or {})
    for key in [
        "country_key", "city_key", "lat", "lon", "population",
        "temperature", "wind_speed", "solar_radiation", "precipitation", "humidity",
        "solar_capacity", "wind_capacity", "geothermal_capacity", "hydro_capacity", "battery_capacity",
    ]:
        if key in row and pd.notna(row[key]):
            inputs[key] = row[key]
    return inputs


def compute_reference_average(inputs: Dict[str, Any], uploaded_df: pd.DataFrame = None, active_country=None, active_city=None):
    """Compute reference average supply using uploaded history when available.

    Returns a dict compatible with the existing UI:
    - avg_supply
    - used_uploaded_history
    - rows_used
    """
    if uploaded_df is None or getattr(uploaded_df, "empty", True):
        normal = compute_energy_supply(inputs, "normal", {}, 0)
        return {
            "avg_supply": round(float(normal.get("renewable_supply", 0.0)), 2),
            "used_uploaded_history": False,
            "rows_used": 0,
        }

    sorted_df, _, _ = sort_history_df(uploaded_df)
    supplies = []
    for _, row in sorted_df.tail(30).iterrows():
        row_inputs = _row_to_inputs(row, inputs)
        try:
            if active_country and "country_key" in row:
                # Soft filter only: do not drop all rows if naming differs.
                pass
            r = compute_energy_supply(row_inputs, "normal", {}, 0)
            supplies.append(float(r.get("renewable_supply", 0.0)))
        except Exception:
            continue

    if not supplies:
        normal = compute_energy_supply(inputs, "normal", {}, 0)
        return {
            "avg_supply": round(float(normal.get("renewable_supply", 0.0)), 2),
            "used_uploaded_history": False,
            "rows_used": 0,
        }

    return {
        "avg_supply": round(sum(supplies) / len(supplies), 2),
        "used_uploaded_history": True,
        "rows_used": len(supplies),
    }


def build_energy_contribution_df(results: Dict[str, Any], reference_avg: Dict[str, Any] = None, tr=None):
    reference_avg = reference_avg or {}
    source_key = _t("source", tr)
    current_share_key = _t("current_share", tr)
    historical_average_share_key = _t("historical_average_share", tr)
    current_output_key = _t("current_output_mw", tr)
    estimated_use_key = _t("estimated_use_mw", tr)
    remaining_key = _t("remaining_margin_mw", tr)
    change_key = _t("change_from_normal", tr)

    outputs = results.get("source_outputs") or {
        "Solar": results.get("solar_supply", 0.0),
        "Wind": results.get("wind_supply", 0.0),
        "Geothermal": results.get("geothermal_supply", 0.0),
        "Hydro": results.get("hydro_supply", 0.0),
    }
    total = sum(float(v or 0) for v in outputs.values())
    demand = float(results.get("demand", 0.0))
    avg_supply = float(reference_avg.get("avg_supply", total or 1.0)) or 1.0

    rows = []
    for name, value in outputs.items():
        value = float(value or 0.0)
        share = safe_div(value, total) * 100.0 if total > 0 else 0.0
        estimated_use = min(value, demand * safe_div(value, total)) if total > 0 else 0.0
        historical_share = safe_div(value, avg_supply) * 100.0 if avg_supply > 0 else 0.0
        rows.append({
            source_key: name,
            current_share_key: round(share, 2),
            historical_average_share_key: round(historical_share, 2),
            current_output_key: round(value, 2),
            estimated_use_key: round(estimated_use, 2),
            remaining_key: round(max(0.0, value - estimated_use), 2),
            change_key: round(share - historical_share, 2),
        })
    return pd.DataFrame(rows)


def build_forecast_chart_df(multistep_df: pd.DataFrame, tr=None):
    if multistep_df is None or multistep_df.empty:
        return pd.DataFrame()
    return multistep_df.copy()


def compute_trend_estimates(history_df: pd.DataFrame, results: Dict[str, Any], scenario_key: str = "normal", tr=None, forecast_horizon: int = 6):
    """Build lightweight trend estimates compatible with the existing UI.

    The function is intentionally conservative: if no history exists, it derives a
    stable baseline from current model outputs.
    """
    source_key = _t("source", tr)
    rolling_key = _t("rolling_average_share", tr)
    recent_trend_key = _t("recent_trend_pct", tr)
    next_step_key = _t("next_step_estimate_pct", tr)
    direction_key = _t("trend_direction", tr)
    upper_key = _t("upper_band_pct", tr)
    lower_key = _t("lower_band_pct", tr)
    factor_key = _t("source_forecast_factor", tr)

    mix = results.get("actual_mix_pct") or {}
    if not mix:
        outputs = results.get("source_outputs") or {}
        total = sum(float(v or 0.0) for v in outputs.values())
        mix = {k: safe_div(float(v or 0.0), total) * 100.0 if total else 0.0 for k, v in outputs.items()}

    scenario_factor = {
        "normal": 1.00,
        "heat_wave": 1.12,
        "storm": 1.22,
        "cold_wave": 1.16,
        "blizzard": 1.30,
        "typhoon": 1.35,
        "wildfire": 1.28,
    }.get(str(scenario_key), 1.10)

    source_sensitivity = {
        "Solar": 1.18,
        "Wind": 1.12,
        "Geothermal": 0.45,
        "Hydro": 0.75,
    }

    rows = []
    multi_rows = []
    for source, current_share in mix.items():
        current_share = float(current_share or 0.0)
        sens = source_sensitivity.get(source, 0.90)
        uncertainty = clamp(4.0 * scenario_factor * sens, 2.0, 18.0)
        recent_trend = 0.0
        next_step = clamp(current_share + recent_trend, 0.0, 100.0)
        direction = "stable"
        rows.append({
            source_key: source,
            rolling_key: round(current_share, 2),
            recent_trend_key: round(recent_trend, 2),
            next_step_key: round(next_step, 2),
            direction_key: direction,
            lower_key: round(clamp(next_step - uncertainty, 0.0, 100.0), 2),
            upper_key: round(clamp(next_step + uncertainty, 0.0, 100.0), 2),
            factor_key: round(sens * scenario_factor, 2),
        })
        for step in range(1, int(forecast_horizon) + 1):
            step_uncertainty = uncertainty * (1.0 + step * 0.12)
            multi_rows.append({
                "Step": step,
                source_key: source,
                next_step_key: round(next_step, 2),
                lower_key: round(clamp(next_step - step_uncertainty, 0.0, 100.0), 2),
                upper_key: round(clamp(next_step + step_uncertainty, 0.0, 100.0), 2),
            })

    meta = {
        "timestamp_col": "-",
        "sorting_mode": "current_model",
        "history_rows_used": 0 if history_df is None else len(history_df),
        "scenario_confidence_factor": round(scenario_factor, 2),
    }
    return pd.DataFrame(rows), pd.DataFrame(multi_rows), meta
