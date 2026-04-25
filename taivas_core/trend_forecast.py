"""Trend, history sorting, and forecast helpers for TAIVAS.

This module was split out in V3 so the Streamlit main file can stay focused on UI/rendering.
"""

import pandas as pd

from data_config import SCENARIOS
from taivas_core.energy_model import compute_energy_supply

try:
    import streamlit as st
    from i18n_config import I18N
except Exception:  # Allows static checking outside Streamlit.
    st = None
    I18N = {"English": {}}


def tr(key: str) -> str:
    """Return the active UI label while keeping the forecast module import-safe."""
    if st is None:
        return key
    lang_pack = I18N.get(st.session_state.get("ui_lang", "English"), I18N.get("English", {}))
    return lang_pack.get(key, I18N.get("English", {}).get(key, key))


def compute_reference_average(inputs, uploaded_df, selected_country, selected_city):
    # Use uploaded historical rows first when available; otherwise fall back to model average across scenarios.
    source_order = ["Solar", "Wind", "Geothermal", "Hydro"]
    rows = []
    if uploaded_df is not None and not uploaded_df.empty:
        tmp = uploaded_df.copy()
        if "country_key" in tmp.columns and "city_key" in tmp.columns:
            tmp["_country"] = tmp["country_key"].astype(str).str.strip().str.title()
            tmp["_city"] = tmp["city_key"].astype(str).str.strip().str.title()
            matched = tmp[(tmp["_country"] == str(selected_country).title()) & (tmp["_city"] == str(selected_city).title())]
            if matched.empty:
                matched = tmp
        else:
            matched = tmp
        for _, r in matched.iterrows():
            local_inputs = dict(inputs)
            local_inputs["temperature"] = safe_float(r["temperature"], inputs["temperature"]) if "temperature" in matched.columns else inputs["temperature"]
            local_inputs["wind_speed"] = safe_float(r["wind_speed"], inputs["wind_speed"]) if "wind_speed" in matched.columns else inputs["wind_speed"]
            local_inputs["solar_radiation"] = safe_float(r["solar_radiation"], inputs["solar_radiation"]) if "solar_radiation" in matched.columns else inputs["solar_radiation"]
            local_inputs["precipitation"] = safe_float(r["precipitation"], inputs["precipitation"]) if "precipitation" in matched.columns else inputs["precipitation"]
            local_inputs["humidity"] = safe_float(r["humidity"], inputs["humidity"]) if "humidity" in matched.columns else inputs["humidity"]
            local_inputs["population"] = safe_int(r["population"], inputs["population"]) if "population" in matched.columns else inputs["population"]
            local_inputs["solar_capacity"] = safe_float(r["solar_capacity"], inputs["solar_capacity"]) if "solar_capacity" in matched.columns else inputs["solar_capacity"]
            local_inputs["wind_capacity"] = safe_float(r["wind_capacity"], inputs["wind_capacity"]) if "wind_capacity" in matched.columns else inputs["wind_capacity"]
            local_inputs["geothermal_capacity"] = safe_float(r["geothermal_capacity"], inputs["geothermal_capacity"]) if "geothermal_capacity" in matched.columns else inputs["geothermal_capacity"]
            local_inputs["hydro_capacity"] = safe_float(r["hydro_capacity"], inputs["hydro_capacity"]) if "hydro_capacity" in matched.columns else inputs["hydro_capacity"]
            local_inputs["battery_capacity"] = safe_float(r["battery_capacity"], inputs["battery_capacity"]) if "battery_capacity" in matched.columns else inputs["battery_capacity"]
            rr = compute_energy_supply(local_inputs, "normal", {k: 0.0 for k in ["solar", "wind", "geothermal", "hydro", "battery"]}, 0)
            rows.append(rr)
    if not rows:
        for sk in SCENARIOS.keys():
            rr = compute_energy_supply(inputs, sk, {k: 0.0 for k in ["solar", "wind", "geothermal", "hydro", "battery"]}, 0)
            rows.append(rr)
    avg_mix_pct = {s: round(sum(r["actual_mix_pct"].get(s, 0.0) for r in rows) / len(rows), 2) for s in source_order}
    avg_mix_mw = {s: round(sum(r["actual_mix_mw"].get(s, 0.0) for r in rows) / len(rows), 2) for s in source_order}
    avg_supply = round(sum(r["renewable_supply"] for r in rows) / len(rows), 2)
    return {"avg_mix_pct": avg_mix_pct, "avg_mix_mw": avg_mix_mw, "avg_supply": avg_supply, "used_uploaded_history": uploaded_df is not None and not uploaded_df.empty and len(rows) > 0}

def build_energy_contribution_df(results, baseline_results, reference_avg):
    rows = []
    source_order = ["Solar", "Wind", "Geothermal", "Hydro"]
    demand = max(float(results["demand"]), 0.0)
    renewable_supply = max(float(results["renewable_supply"]), 0.0)
    for source in source_order:
        current_share = float(results["actual_mix_pct"].get(source, 0.0))
        avg_share = float(reference_avg["avg_mix_pct"].get(source, 0.0))
        current_mw = float(results["actual_mix_mw"].get(source, 0.0))
        installed_mw = float(results["installed_mix_mw"].get(source, 0.0))
        normal_share = float(baseline_results["actual_mix_pct"].get(source, 0.0))
        estimated_use = min(current_mw, demand * (current_share / 100.0))
        remaining_margin = max(installed_mw - current_mw, 0.0)
        change_from_normal = current_share - normal_share
        rows.append({
            tr("source"): source,
            tr("current_share"): round(current_share, 2),
            tr("historical_average_share"): round(avg_share, 2),
            tr("current_output_mw"): round(current_mw, 2),
            tr("estimated_use_mw"): round(estimated_use, 2),
            tr("remaining_margin_mw"): round(remaining_margin, 2),
            tr("change_from_normal"): round(change_from_normal, 2),
            "_sort_share": current_share,
        })
    df = pd.DataFrame(rows).sort_values("_sort_share", ascending=False).reset_index(drop=True)
    return df.drop(columns=["_sort_share"])

def compute_trend_estimates(inputs, uploaded_df, selected_country, selected_city, baseline_results, scenario_key="normal", rolling_window_rows=3, forecast_steps=2, confidence_level=1.0):
    source_order = ["Solar", "Wind", "Geothermal", "Hydro"]
    scenario_factor_map = {
        "normal": 1.00,
        "heat_wave": 1.10,
        "storm": 1.22,
        "cold_wave": 1.15,
        "blizzard": 1.35,
        "typhoon": 1.42,
    }
    scenario_conf_factor = float(scenario_factor_map.get(str(scenario_key), 1.10))
    records = []
    history_count = 0
    timestamp_col = None
    sorting_mode = "original"
    if uploaded_df is not None and not uploaded_df.empty:
        sorted_df, timestamp_col, sorting_mode = sort_history_df(uploaded_df)
        tmp = sorted_df.copy()
        if "country_key" in tmp.columns and "city_key" in tmp.columns:
            tmp["_country"] = tmp["country_key"].astype(str).str.strip().str.title()
            tmp["_city"] = tmp["city_key"].astype(str).str.strip().str.title()
            matched = tmp[(tmp["_country"] == str(selected_country).title()) & (tmp["_city"] == str(selected_city).title())]
            if matched.empty:
                matched = tmp
        else:
            matched = tmp
        history_count = len(matched)
        for _, r in matched.iterrows():
            local_inputs = dict(inputs)
            for key, default in [
                ("temperature", inputs["temperature"]),
                ("wind_speed", inputs["wind_speed"]),
                ("solar_radiation", inputs["solar_radiation"]),
                ("precipitation", inputs["precipitation"]),
                ("humidity", inputs["humidity"]),
                ("population", inputs["population"]),
                ("solar_capacity", inputs["solar_capacity"]),
                ("wind_capacity", inputs["wind_capacity"]),
                ("geothermal_capacity", inputs["geothermal_capacity"]),
                ("hydro_capacity", inputs["hydro_capacity"]),
                ("battery_capacity", inputs["battery_capacity"]),
            ]:
                if key in matched.columns:
                    local_inputs[key] = safe_float(r[key], default) if key != "population" else safe_int(r[key], default)
            rr = compute_energy_supply(local_inputs, "normal", {k: 0.0 for k in ["solar", "wind", "geothermal", "hydro", "battery"]}, 0)
            records.append(rr)
    if not records:
        fallback_keys = list(SCENARIOS.keys())
        records = [compute_energy_supply(inputs, sk, {k: 0.0 for k in ["solar", "wind", "geothermal", "hydro", "battery"]}, 0) for sk in fallback_keys]
        history_count = len(records)

    window = max(2, min(int(rolling_window_rows), max(2, len(records))))
    recent_records = records[-window:]
    prev_records = records[-(window * 2):-window] if len(records) >= window * 2 else records[:-window]

    rolling_avg = {s: round(sum(r["actual_mix_pct"].get(s, 0.0) for r in recent_records) / max(len(recent_records), 1), 2) for s in source_order}
    if prev_records:
        prev_avg = {s: round(sum(r["actual_mix_pct"].get(s, 0.0) for r in prev_records) / max(len(prev_records), 1), 2) for s in source_order}
    else:
        prev_avg = {s: float(baseline_results["actual_mix_pct"].get(s, 0.0)) for s in source_order}

    recent_trend = {s: round(rolling_avg[s] - float(prev_avg.get(s, 0.0)), 2) for s in source_order}

    if len(recent_records) > 1:
        volatility = {
            s: max(r["actual_mix_pct"].get(s, 0.0) for r in recent_records) - min(r["actual_mix_pct"].get(s, 0.0) for r in recent_records)
            for s in source_order
        }
    else:
        volatility = {s: abs(recent_trend[s]) for s in source_order}

    next_step = {}
    source_factor_map = {
        "Solar": {"normal": 1.00, "heat_wave": 1.12, "storm": 0.90, "cold_wave": 0.92, "blizzard": 0.78, "typhoon": 0.72},
        "Wind": {"normal": 1.00, "heat_wave": 0.92, "storm": 1.20, "cold_wave": 0.98, "blizzard": 0.90, "typhoon": 0.82},
        "Geothermal": {"normal": 1.00, "heat_wave": 1.01, "storm": 1.00, "cold_wave": 1.00, "blizzard": 1.00, "typhoon": 1.00},
        "Hydro": {"normal": 1.00, "heat_wave": 0.95, "storm": 1.08, "cold_wave": 0.98, "blizzard": 0.94, "typhoon": 0.86},
    }
    next_step = {}
    for s in source_order:
        source_factor = float(source_factor_map.get(s, {}).get(str(scenario_key), 1.0))
        projected = max(0.0, rolling_avg[s] + recent_trend[s] * max(1, int(forecast_steps)) * 0.5 * source_factor)
        next_step[s] = round(projected, 2)
    total_next = sum(next_step.values())
    if total_next > 0:
        next_step = {s: round(v / total_next * 100.0, 2) for s, v in next_step.items()}

    trend_rows = []
    multistep_rows = []
    for s in source_order:
        delta = recent_trend[s]
        if delta > 0.25:
            direction = tr("rising")
        elif delta < -0.25:
            direction = tr("falling")
        else:
            direction = tr("flat")

        base_band = volatility[s] * float(confidence_level) * 0.5 * scenario_conf_factor
        upper = min(100.0, next_step[s] + base_band)
        lower = max(0.0, next_step[s] - base_band)

        trend_rows.append({
            tr("source"): s,
            tr("rolling_average_share"): rolling_avg[s],
            tr("recent_trend_pct"): round(delta, 2),
            tr("next_step_estimate_pct"): round(next_step[s], 2),
            tr("trend_direction"): direction,
            tr("upper_band_pct"): round(upper, 2),
            tr("lower_band_pct"): round(lower, 2),
            tr("source_forecast_factor"): round(float(source_factor_map.get(s, {}).get(str(scenario_key), 1.0)), 2),
            "_sort": next_step[s],
        })

        for step in range(1, int(forecast_steps) + 1):
            source_factor = float(source_factor_map.get(s, {}).get(str(scenario_key), 1.0))
            projected = max(0.0, rolling_avg[s] + delta * step * 0.5 * source_factor)
            step_band = base_band * (1 + 0.18 * (step - 1))
            multistep_rows.append({
                tr("source"): s,
                tr("forecast_step"): step,
                tr("next_step_estimate_pct"): round(projected, 2),
                tr("lower_band_pct"): round(max(0.0, projected - step_band), 2),
                tr("upper_band_pct"): round(min(100.0, projected + step_band), 2),
                tr("trend_direction"): direction,
                tr("source_forecast_factor"): round(float(source_factor_map.get(s, {}).get(str(scenario_key), 1.0)), 2),
            })

    trend_df = pd.DataFrame(trend_rows).sort_values("_sort", ascending=False).drop(columns=["_sort"]).reset_index(drop=True)
    multistep_df = pd.DataFrame(multistep_rows)
    if not multistep_df.empty:
        multistep_df = multistep_df.sort_values([tr("forecast_step"), tr("next_step_estimate_pct")], ascending=[True, False]).reset_index(drop=True)

    meta = {
        "timestamp_col": timestamp_col if timestamp_col is not None else "-",
        "sorting_mode": tr("timestamp_sorted") if sorting_mode == "timestamp" else tr("original_order"),
        "history_rows_used": history_count,
        "scenario_confidence_factor": round(scenario_conf_factor, 2),
    }
    return trend_df, multistep_df, meta

def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default

def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default

def detect_timestamp_column(df: pd.DataFrame):
    if df is None or df.empty:
        return None
    candidates = [
        "timestamp", "datetime", "date", "time", "recorded_at",
        "created_at", "observation_time", "observed_at"
    ]
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    for c in df.columns:
        name = str(c).strip().lower()
        if "time" in name or "date" in name:
            return c
    return None

def sort_history_df(df: pd.DataFrame):
    if df is None or df.empty:
        return df, None, "original"
    ts_col = detect_timestamp_column(df)
    if ts_col is None:
        return df.copy(), None, "original"
    tmp = df.copy()
    parsed = pd.to_datetime(tmp[ts_col], errors="coerce")
    valid = parsed.notna().sum()
    if valid == 0:
        return df.copy(), ts_col, "original"
    tmp["_parsed_ts"] = parsed
    tmp = tmp.sort_values("_parsed_ts", kind="stable").drop(columns=["_parsed_ts"]).reset_index(drop=True)
    return tmp, ts_col, "timestamp"

def prepare_uploaded_preview(df: pd.DataFrame, max_rows: int = 8):
    if df is None or df.empty:
        return None, None, None
    sorted_df, ts_col, sorting_mode = sort_history_df(df)
    preview_df = sorted_df.copy()
    parsed_col = None
    if ts_col is not None:
        parsed_col = "__parsed_timestamp_display__"
        preview_df[parsed_col] = pd.to_datetime(preview_df[ts_col], errors="coerce")
    preferred_cols = []
    if ts_col is not None:
        preferred_cols.append(ts_col)
    if parsed_col is not None:
        preferred_cols.append(parsed_col)
    for c in ["country_key", "city_key", "temperature", "wind_speed", "solar_radiation", "precipitation", "humidity", "solar_capacity", "wind_capacity", "geothermal_capacity", "hydro_capacity", "battery_capacity"]:
        if c in preview_df.columns and c not in preferred_cols:
            preferred_cols.append(c)
    if not preferred_cols:
        preferred_cols = list(preview_df.columns)
    preview_df = preview_df[preferred_cols].head(max_rows).copy()
    return preview_df, ts_col, sorting_mode

def build_forecast_chart_df(multistep_df: pd.DataFrame):
    if multistep_df is None or multistep_df.empty:
        return pd.DataFrame()

    src_col = tr("source")
    step_col = tr("forecast_step")
    est_col = tr("next_step_estimate_pct")
    low_col = tr("lower_band_pct")
    up_col = tr("upper_band_pct")

    required_cols = [src_col, step_col, est_col, low_col, up_col]
    if any(col not in multistep_df.columns for col in required_cols):
        return pd.DataFrame()

    df = multistep_df.copy()

    # Create explicit label columns first, then pivot by column name.
    df["series_est"] = df[src_col].astype(str) + " • est"
    df["series_low"] = df[src_col].astype(str) + " • low"
    df["series_high"] = df[src_col].astype(str) + " • high"

    est_wide = df.pivot(index=step_col, columns="series_est", values=est_col)
    low_wide = df.pivot(index=step_col, columns="series_low", values=low_col)
    high_wide = df.pivot(index=step_col, columns="series_high", values=up_col)

    out = pd.concat([est_wide, low_wide, high_wide], axis=1).sort_index()
    out.index.name = step_col
    return out
