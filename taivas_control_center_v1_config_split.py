from io import StringIO
import json

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Dark-mode friendly chart defaults for Streamlit dashboards.
plt.rcParams.update({
    "text.color": "#E5E7EB",
    "axes.labelcolor": "#E5E7EB",
    "axes.edgecolor": "#94A3B8",
    "xtick.color": "#CBD5E1",
    "ytick.color": "#CBD5E1",
    "axes.titlecolor": "#F8FAFC",
    "figure.facecolor": "none",
    "axes.facecolor": "none",
})

from modules.charts import make_donut_chart
from modules.recommendations import recommendation_lines
from modules.energy_security import apply_energy_security_layer, ENERGY_SECURITY_SCENARIOS
from modules.survival_timeline import simulate_survival_timeline
from concept_lab_components import (
    render_thermal_principle_simulation,
    render_phase_change_buffer_concept,
    render_ground_thermal_sink_concept,
    render_distributed_thermal_control_concept,
    render_distributed_harvesting_buffering_concept,
)

from data_config import CITY_DATA, COUNTRY_NOTES, SCENARIOS
from facility_config import FACILITY_PROFILES
from i18n_config import I18N, PAGE_QUESTIONS
def tr(key: str) -> str:
    lang_pack = I18N.get(st.session_state.get("ui_lang", "English"), I18N["English"])
    return lang_pack.get(key, I18N["English"].get(key, key))

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def safe_div(a: float, b: float) -> float:
    return a / b if b not in (0, 0.0) else 0.0

def normalize_mix(parts):
    total = sum(max(v, 0.0) for v in parts.values())
    if total <= 0:
        return {k: 0.0 for k in parts}
    return {k: max(v, 0.0) / total for k, v in parts.items()}

def base_demand_from_population(population: int) -> float:
    return 80 + population / 50000

def weather_adjustment(temp: float, humidity: float, precipitation: float) -> float:
    cooling = max(0.0, temp - 24) * 1.8
    heating = max(0.0, 10 - temp) * 1.35
    humidity_load = max(0.0, humidity - 65) * 0.25
    rain_impact = precipitation * 0.08
    return 1.0 + (cooling + heating + humidity_load + rain_impact) / 100.0

def build_status_label(value: float, thresholds, reverse: bool = False) -> str:
    warn, critical = thresholds
    if reverse:
        if value <= critical:
            return tr("critical")
        if value <= warn:
            return tr("watch")
        return tr("stable")
    if value >= critical:
        return tr("critical")
    if value >= warn:
        return tr("watch")
    return tr("stable")

def mini_card(label: str, value: str):
    st.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)

def page_question(tab_label: str):
    lang = st.session_state.get("ui_lang", "English")
    st.markdown(f'<div class="question"><b>{tr("page_answers")}</b> {PAGE_QUESTIONS[lang][tab_label]}</div>', unsafe_allow_html=True)

def concept_badge():
    st.markdown(f'<div class="badge">{tr("concept_badge")}</div>', unsafe_allow_html=True)

def compute_energy_supply(inputs, scenario_key: str, failure_ratios: dict, reserve_recovery_lag_days: int):
    scenario = SCENARIOS.get(scenario_key, SCENARIOS["normal"])
    temperature = clamp(inputs["temperature"], -30, 55)
    wind_speed = clamp(inputs["wind_speed"], 0, 40)
    solar_radiation = clamp(inputs["solar_radiation"], 0, 1200)
    precipitation = clamp(inputs["precipitation"], 0, 500)
    humidity = clamp(inputs["humidity"], 0, 100)
    population = int(clamp(inputs["population"], 1000, 50000000))
    solar_capacity = clamp(inputs["solar_capacity"], 0, 5000)
    wind_capacity = clamp(inputs["wind_capacity"], 0, 5000)
    geothermal_capacity = clamp(inputs["geothermal_capacity"], 0, 5000)
    hydro_capacity = clamp(inputs["hydro_capacity"], 0, 5000)
    battery_capacity = clamp(inputs["battery_capacity"], 0, 10000)
    base_demand = base_demand_from_population(population)
    demand = base_demand * weather_adjustment(temperature, humidity, precipitation) * scenario["demand"]
    solar_cf = clamp((solar_radiation / 1000.0) * 0.58, 0.0, 0.95)
    wind_cf = clamp((wind_speed / 12.0) * 0.42, 0.0, 0.90)
    hydro_cf = clamp((0.45 + precipitation / 500.0 * 0.35), 0.15, 0.95)
    geo_cf = 0.85
    solar_availability = 1.0 - clamp(failure_ratios["solar"], 0.0, 1.0)
    wind_availability = 1.0 - clamp(failure_ratios["wind"], 0.0, 1.0)
    geo_availability = 1.0 - clamp(failure_ratios["geothermal"], 0.0, 1.0)
    hydro_availability = 1.0 - clamp(failure_ratios["hydro"], 0.0, 1.0)
    battery_availability = 1.0 - clamp(failure_ratios["battery"], 0.0, 1.0)
    solar_supply = solar_capacity * solar_cf * scenario["solar"] * solar_availability
    wind_supply = wind_capacity * wind_cf * scenario["wind"] * wind_availability
    hydro_supply = hydro_capacity * hydro_cf * scenario["hydro"] * hydro_availability
    geo_supply = geothermal_capacity * geo_cf * scenario["geo"] * geo_availability
    renewable_supply = solar_supply + wind_supply + hydro_supply + geo_supply
    battery_dispatch_limit = battery_capacity * 0.35 * scenario["battery"] * battery_availability
    lag_penalty = max(0.70, 1.0 - reserve_recovery_lag_days * 0.015)
    battery_dispatch = min(battery_dispatch_limit * lag_penalty, max(0.0, demand - renewable_supply))
    final_supply = renewable_supply + battery_dispatch
    shortfall = max(0.0, demand - final_supply)
    renewable_ratio = safe_div(renewable_supply, final_supply) * 100 if final_supply > 0 else 0.0
    system_efficiency = clamp(100 - shortfall * 0.55, 0, 100)
    grid_dependency = safe_div(shortfall, demand) * 100 if demand > 0 else 0.0
    battery_levels = max(0.0, battery_capacity - battery_dispatch)
    actual_mix_raw = {"Solar": solar_supply, "Wind": wind_supply, "Geothermal": geo_supply, "Hydro": hydro_supply}
    installed_mix_raw = {"Solar": solar_capacity, "Wind": wind_capacity, "Geothermal": geothermal_capacity, "Hydro": hydro_capacity}
    actual_mix_pct = {k: v * 100 for k, v in normalize_mix(actual_mix_raw).items()}
    installed_mix_pct = {k: v * 100 for k, v in normalize_mix(installed_mix_raw).items()}
    capacity_factors = {"Solar": round(solar_cf * 100, 1), "Wind": round(wind_cf * 100, 1), "Geothermal": round(geo_cf * 100, 1), "Hydro": round(hydro_cf * 100, 1)}
    dominant_source = max(actual_mix_raw, key=actual_mix_raw.get) if renewable_supply > 0 else "None"
    return {
        "demand": round(demand, 2),
        "renewable_supply": round(renewable_supply, 2),
        "final_supply": round(final_supply, 2),
        "battery_levels": round(battery_levels, 2),
        "shortfall": round(shortfall, 2),
        "renewable_ratio": round(renewable_ratio, 2),
        "system_efficiency": round(system_efficiency, 2),
        "grid_dependency": round(grid_dependency, 2),
        "actual_mix_pct": actual_mix_pct,
        "installed_mix_pct": installed_mix_pct,
        "actual_mix_mw": {k: round(v, 2) for k, v in actual_mix_raw.items()},
        "installed_mix_mw": {k: round(v, 2) for k, v in installed_mix_raw.items()},
        "capacity_factors": capacity_factors,
        "dominant_source": dominant_source,
    }

def apply_extended_security(results, fuel_price_shock, repair_crew_availability, spare_parts_delay_days, refill_uncertainty, single_point_failure_risk):
    penalty = fuel_price_shock * 0.10 + (1 - repair_crew_availability) * 0.16 + min(spare_parts_delay_days / 30.0, 1.0) * 0.12 + refill_uncertainty * 0.18 + single_point_failure_risk * 0.22
    results["extended_disruption_score"] = round(clamp(results["grid_dependency"] * 0.45 + penalty * 100, 0, 100), 2)
    results["spare_parts_risk"] = round(clamp(spare_parts_delay_days * 3.2, 0, 100), 2)
    results["maintenance_readiness"] = round(clamp(repair_crew_availability * 100 - spare_parts_delay_days * 1.8, 0, 100), 2)
    results["refill_stability"] = round(clamp((1 - refill_uncertainty) * 100, 0, 100), 2)
    results["single_point_pressure"] = round(single_point_failure_risk * 100, 2)
    results["reserve_days_remaining"] = max(0, round(results.get("reserve_days_remaining", 0) - penalty * 4.2, 1))
    results["recovery_time_estimate"] = max(1, round(results.get("recovery_time_estimate", 1) + penalty * 5 + spare_parts_delay_days * 0.3, 1))
    return results

def recommendation_reason_chain(results, energy_security_scenario, timeline_results, facility_type, facility_profile):
    if st.session_state.get("ui_lang", "English") == "繁體中文":
        rows = [{"Signal": f"缺口仍有 {results['shortfall']:.2f} MW" if results["shortfall"] > 0 else "目前情境下沒有模擬缺口",
                 "Impact": "需求高於目前可用供應。" if results["shortfall"] > 0 else "即時供需平衡暫時穩定。",
                 "Recommendation": "提高穩定供應、降低非關鍵負載，或加深儲能支援。" if results["shortfall"] > 0 else "保留備援餘裕並持續監看中斷訊號。",
                 "Expected effect": "降低未滿足負載並延長穩定運作時間。" if results["shortfall"] > 0 else "保住惡化時的緩衝空間。"}]
    else:
        rows = [{"Signal": f"Shortfall remains at {results['shortfall']:.2f} MW" if results["shortfall"] > 0 else "No modeled shortfall in the selected scenario",
                 "Impact": "Demand is above available modeled supply." if results["shortfall"] > 0 else "Immediate supply-demand balance is currently stable.",
                 "Recommendation": "Raise firm capacity, reduce non-critical load, or deepen storage support." if results["shortfall"] > 0 else "Protect reserve margin and watch disruption signals.",
                 "Expected effect": "Reduce unmet load and extend stable operation." if results["shortfall"] > 0 else "Preserve endurance against degradation."}]
    return rows

def scenario_delta_df(baseline, selected):
    return pd.DataFrame([
        {tr("metric"): tr("demand"), tr("baseline"): round(baseline["demand"], 2), tr("selected"): round(selected["demand"], 2), tr("delta"): round(selected["demand"] - baseline["demand"], 2)},
        {tr("metric"): tr("renewable"), tr("baseline"): round(baseline["renewable_supply"], 2), tr("selected"): round(selected["renewable_supply"], 2), tr("delta"): round(selected["renewable_supply"] - baseline["renewable_supply"], 2)},
        {tr("metric"): tr("final"), tr("baseline"): round(baseline["final_supply"], 2), tr("selected"): round(selected["final_supply"], 2), tr("delta"): round(selected["final_supply"] - baseline["final_supply"], 2)},
        {tr("metric"): tr("shortfall"), tr("baseline"): round(baseline["shortfall"], 2), tr("selected"): round(selected["shortfall"], 2), tr("delta"): round(selected["shortfall"] - baseline["shortfall"], 2)},
    ])

def comparison_dataframe(inputs, failure_ratios, reserve_recovery_lag_days):
    rows = []
    for key in SCENARIOS.keys():
        r = compute_energy_supply(inputs, key, failure_ratios, reserve_recovery_lag_days)
        rows.append({tr("scenario"): key.replace("_", " ").title(), tr("demand"): r["demand"], tr("renewable"): r["renewable_supply"], tr("final"): r["final_supply"], tr("shortfall"): r["shortfall"], tr("grid"): r["grid_dependency"]})
    return pd.DataFrame(rows)

def critical_load_breakdown(total_demand, critical_share, split):
    critical_total = total_demand * critical_share
    return pd.DataFrame({"Category": list(split.keys()), f"{tr('demand')} (MW)": [round(critical_total * w, 2) for w in split.values()]})

def render_capacity_factor_chart(capacity_factors):
    labels = list(capacity_factors.keys())
    values = [capacity_factors[k] for k in labels]
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    ax.barh(labels, values)
    ax.set_xlabel("Capacity Factor (%)" if st.session_state.get("ui_lang", "English") == "English" else "容量因子 (%)")
    ax.set_xlim(0, 100)
    ax.set_title(tr("capacity_factors"))
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)

def render_delta_chart(delta_df):
    fig, ax = plt.subplots(figsize=(8.8, 4.0))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    metric_col = tr("metric") if tr("metric") in delta_df.columns else "Metric"
    delta_col = tr("delta") if tr("delta") in delta_df.columns else "Delta"
    ax.barh(delta_df[metric_col], delta_df[delta_col])
    ax.axvline(0, linewidth=1.0)
    ax.set_title(tr("baseline_vs_selected"))
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)

def render_critical_load_chart(df):
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    col = f"{tr('demand')} (MW)"
    ax.bar(df["Category"], df[col])
    ax.set_ylabel(col)
    ax.set_title(tr("critical_breakdown"))
    ax.grid(axis="y", alpha=0.22)
    plt.xticks(rotation=15)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)


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

def estimate_refill_hours(results, timeline_results):
    battery_capacity_initial = max(float(inputs["battery_capacity"]) * (1 - battery_failure_ratio), 0.0)
    battery_remaining = max(float(results["battery_levels"]), 0.0)
    to_refill = max(battery_capacity_initial - battery_remaining, 0.0)
    surplus_rate = max(float(results["final_supply"]) - float(results["demand"]), 0.0)
    if surplus_rate <= 0.01:
        return tr("no_surplus")
    return f"{round(to_refill / surplus_rate, 1)} {tr('hours_short')}"

def render_energy_contribution_panel(df):
    st.subheader(tr("current_energy_contribution"))
    st.markdown(f'<div class="note">{tr("current_energy_contribution_note")}</div>', unsafe_allow_html=True)
    for _, row in df.iterrows():
        source = row[tr("source")]
        share = row[tr("current_share")]
        avg_share = row[tr("historical_average_share")]
        current_mw = row[tr("current_output_mw")]
        used_mw = row[tr("estimated_use_mw")]
        remaining = row[tr("remaining_margin_mw")]
        delta = row[tr("change_from_normal")]
        delta_text = f"{delta:+.1f}%"
        width = max(6, min(100, int(round(share))))
        st.markdown(
            f"""
            <div style="border:1px solid rgba(255,255,255,0.10); border-radius:16px; padding:12px 14px; margin-bottom:10px; background:rgba(255,255,255,0.04);">
              <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:8px;">
                <div style="font-size:1rem; font-weight:700;">{source}</div>
                <div style="font-size:0.92rem; opacity:0.88;">{delta_text}</div>
              </div>
              <div style="width:100%; height:12px; background:rgba(255,255,255,0.10); border-radius:999px; overflow:hidden; margin-bottom:10px;">
                <div style="width:{width}%; height:100%; background:linear-gradient(90deg, rgba(96,165,250,0.95), rgba(34,211,238,0.95)); border-radius:999px;"></div>
              </div>
              <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; font-size:0.88rem; line-height:1.45;">
                <div><b>{tr("current_share")}</b><br>{share:.2f}%</div>
                <div><b>{tr("historical_average_share")}</b><br>{avg_share:.2f}%</div>
                <div><b>{tr("current_output_mw")}</b><br>{current_mw:.2f} MW</div>
                <div><b>{tr("estimated_use_mw")}</b><br>{used_mw:.2f} MW</div>
                <div><b>{tr("remaining_margin_mw")}</b><br>{remaining:.2f} MW</div>
                <div><b>{tr("change_from_normal")}</b><br>{delta_text}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_reserve_outlook_panel(reference_avg, results, timeline_results):
    st.subheader(tr("reserve_outlook"))
    st.markdown(f'<div class="note">{tr("reserve_outlook_note")}</div>', unsafe_allow_html=True)
    if reference_avg.get("used_uploaded_history"):
        st.caption(tr("uploaded_history_used"))
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(tr("historical_average_supply"), f'{reference_avg["avg_supply"]} MW')
    c2.metric(tr("current_renewable_supply"), f'{results["renewable_supply"]} MW')
    c3.metric(tr("estimated_renewable_use"), f'{round(min(results["renewable_supply"], results["demand"]), 2)} MW')
    c4.metric(tr("remaining_battery_reserve"), f'{results["battery_levels"]} MWh')
    c5.metric(tr("estimated_refill_time"), estimate_refill_hours(results, timeline_results))

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

def render_trend_estimate_panel(trend_df, multistep_df, trend_meta):
    st.subheader(tr("trend_panel"))
    st.markdown(f'<div class="note">{tr("trend_panel_note")}</div>', unsafe_allow_html=True)
    meta_cols = st.columns(4)
    meta_cols[0].metric(tr("timestamp_col"), str(trend_meta.get("timestamp_col", "-")))
    meta_cols[1].metric(tr("sorting_mode"), str(trend_meta.get("sorting_mode", "-")))
    meta_cols[2].metric(tr("history_rows_used"), str(trend_meta.get("history_rows_used", 0)))
    meta_cols[3].metric(tr("scenario_confidence_factor"), str(trend_meta.get("scenario_confidence_factor", 1.0)))

    for _, row in trend_df.iterrows():
        source = row[tr("source")]
        rolling_avg = row[tr("rolling_average_share")]
        trend = row[tr("recent_trend_pct")]
        next_step = row[tr("next_step_estimate_pct")]
        direction = row[tr("trend_direction")]
        upper = row[tr("upper_band_pct")]
        lower = row[tr("lower_band_pct")]
        width = max(6, min(100, int(round(next_step))))
        lower_w = max(2, min(100, int(round(lower))))
        upper_w = max(lower_w, min(100, int(round(upper))))
        trend_text = f"{trend:+.2f}%"
        st.markdown(
            f"""
            <div style="border:1px solid rgba(255,255,255,0.10); border-radius:16px; padding:12px 14px; margin-bottom:10px; background:rgba(255,255,255,0.04);">
              <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:8px;">
                <div style="font-size:1rem; font-weight:700;">{source}</div>
                <div style="font-size:0.92rem; opacity:0.88;">{direction}</div>
              </div>
              <div style="position:relative; width:100%; height:14px; background:rgba(255,255,255,0.10); border-radius:999px; overflow:hidden; margin-bottom:10px;">
                <div style="position:absolute; left:0; top:0; width:{upper_w}%; height:100%; background:rgba(251,191,36,0.20); border-radius:999px;"></div>
                <div style="position:absolute; left:0; top:0; width:{lower_w}%; height:100%; background:rgba(251,191,36,0.32); border-radius:999px;"></div>
                <div style="position:absolute; left:0; top:0; width:{width}%; height:100%; background:linear-gradient(90deg, rgba(251,191,36,0.95), rgba(245,158,11,0.95)); border-radius:999px;"></div>
              </div>
              <div style="display:grid; grid-template-columns: repeat(5, 1fr); gap:10px; font-size:0.88rem; line-height:1.45;">
                <div><b>{tr("rolling_average_share")}</b><br>{rolling_avg:.2f}%</div>
                <div><b>{tr("recent_trend_pct")}</b><br>{trend_text}</div>
                <div><b>{tr("next_step_estimate_pct")}</b><br>{next_step:.2f}%</div>
                <div><b>{tr("lower_band_pct")}</b><br>{lower:.2f}%</div>
                <div><b>{tr("upper_band_pct")}</b><br>{upper:.2f}%</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    render_forecast_chart(multistep_df)
    st.subheader(tr("source_logic"))
    st.markdown(f'<div class="note">{tr("source_logic_note")}</div>', unsafe_allow_html=True)
    if not trend_df.empty and tr("source_forecast_factor") in trend_df.columns:
        st.dataframe(trend_df[[tr("source"), tr("source_forecast_factor"), tr("trend_direction"), tr("next_step_estimate_pct"), tr("lower_band_pct"), tr("upper_band_pct")]], use_container_width=True, hide_index=True)
    st.subheader(tr("multi_step_forecast"))
    st.markdown(f'<div class="note">{tr("multi_step_forecast_note")}</div>', unsafe_allow_html=True)
    st.dataframe(multistep_df, use_container_width=True, hide_index=True)


st.markdown("""
<style>
.block-container {padding-top: 1.05rem; padding-bottom: 2rem;}
.hero {
    padding: 1rem 1.1rem;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(21,60,110,0.60), rgba(11,18,32,0.24));
    margin-bottom: 1rem;
}
.hero h3 { margin: 0 0 0.35rem 0; font-size: 1.22rem; }
.hero p { margin: 0; opacity: 0.94; line-height: 1.56; }
.note {
    padding: 0.82rem 0.95rem;
    border-radius: 14px;
    background: rgba(59,130,246,0.10);
    border: 1px solid rgba(96,165,250,0.24);
    margin-bottom: 0.75rem;
    line-height: 1.55;
}
.question {
    padding: 0.78rem 0.95rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 0.75rem;
    line-height: 1.55;
}
.product-strip {display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:0.75rem; margin:0.8rem 0 1rem 0;}
.product-card {padding:0.9rem 1rem; border-radius:18px; border:1px solid rgba(255,255,255,0.10); background:linear-gradient(145deg, rgba(15,23,42,0.78), rgba(30,41,59,0.42));}
.product-label {font-size:0.78rem; opacity:0.72; margin-bottom:0.35rem;}
.product-value {font-size:1.25rem; font-weight:800;}
.product-sub {font-size:0.78rem; opacity:0.74; margin-top:0.2rem;}
.notice-box {padding:0.85rem 1rem; border-radius:16px; background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.28); line-height:1.55; margin:0.8rem 0;}
.demo-pill {display:inline-block; padding:0.25rem 0.55rem; border-radius:999px; margin-left:0.35rem; background:rgba(34,197,94,0.12); border:1px solid rgba(34,197,94,0.32); font-size:0.78rem;}
@media (max-width: 900px) {.product-strip {grid-template-columns: repeat(2, minmax(0,1fr));}}
.card {
    padding: 0.82rem 0.95rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 0.65rem;
    min-height: 88px;
}
.card-label { font-size: 0.82rem; opacity: 0.78; margin-bottom: 0.28rem; }
.card-value { font-size: 1.00rem; font-weight: 600; line-height: 1.30; }
.layer-box {
    padding: 0.82rem 0.92rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    min-height: 112px;
}
.badge {
    display: inline-block;
    padding: 0.28rem 0.55rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    background: rgba(245,158,11,0.12);
    border: 1px solid rgba(245,158,11,0.35);
    color: #fde68a;
    margin-bottom: 0.55rem;
}
</style>
""", unsafe_allow_html=True)



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


def normalize_name(value: str) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def safe_str(value, default=""):
    try:
        if value is None:
            return default
        value = str(value).strip()
        return value if value else default
    except Exception:
        return default


def safe_read_csv(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        return pd.read_csv(uploaded_file)
    except Exception as e:
        st.sidebar.warning(f"CSV read failed: {e}")
        return None



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

def render_forecast_chart(multistep_df: pd.DataFrame):
    st.subheader(tr("forecast_chart"))
    st.markdown(f'<div class="note">{tr("forecast_chart_note")}</div>', unsafe_allow_html=True)
    chart_df = build_forecast_chart_df(multistep_df)
    if not chart_df.empty:
        st.line_chart(chart_df)

def build_uploaded_profiles(df: pd.DataFrame):
    if df is None or df.empty:
        return {}
    sorted_df, ts_col, _ = sort_history_df(df)
    rows = {}
    required = [
        "country_key", "city_key", "lat", "lon", "population",
        "temperature", "wind_speed", "solar_radiation", "precipitation", "humidity",
        "solar_capacity", "wind_capacity", "geothermal_capacity", "hydro_capacity", "battery_capacity",
    ]
    for idx, raw in sorted_df.iterrows():
        row = {k: raw[k] if k in sorted_df.columns else None for k in required}
        country_raw = str(row.get("country_key") or "Uploaded").strip() or "Uploaded"
        city_raw = str(row.get("city_key") or f"Row {idx + 1}").strip() or f"Row {idx + 1}"
        country = country_raw.replace("_", " ").title()
        city = city_raw.replace("_", " ").title()
        rows[f"{country} / {city}"] = {
            "country": country,
            "city": city,
            "lat": safe_float(row.get("lat"), 0.0),
            "lon": safe_float(row.get("lon"), 0.0),
            "population": safe_int(row.get("population"), 100000),
            "temperature": safe_int(row.get("temperature"), 20),
            "wind_speed": safe_float(row.get("wind_speed"), 4.0),
            "solar_radiation": safe_int(row.get("solar_radiation"), 500),
            "precipitation": safe_int(row.get("precipitation"), 10),
            "humidity": safe_int(row.get("humidity"), 60),
            "solar_capacity": safe_int(row.get("solar_capacity"), 120),
            "wind_capacity": safe_int(row.get("wind_capacity"), 80),
            "geothermal_capacity": safe_int(row.get("geothermal_capacity"), 60),
            "hydro_capacity": safe_int(row.get("hydro_capacity"), 70),
            "battery_capacity": safe_int(row.get("battery_capacity"), 180),
            "timestamp_value": safe_str(raw.get(ts_col), "") if ts_col is not None else "",
        }
    return rows



# =============================
# TAIVAS Geopolitical Energy Shock Module V1
# Integrated directly into the main file to avoid extra module dependency.
# =============================

GEOPOLITICAL_EVENT_WEIGHTS = {
    "None": 0.0,
    "Minor diplomatic tension": 0.30,
    "Proxy conflict escalation": 0.60,
    "Oil tanker attack": 0.90,
    "Energy infrastructure strike": 1.10,
    "Hormuz disruption": 1.50,
    "Regional war": 2.00,
}

GEOPOLITICAL_EVENT_NOTES = {
    "None": "No additional geopolitical shock is applied.",
    "Minor diplomatic tension": "Political pressure and market anxiety, but no major physical disruption.",
    "Proxy conflict escalation": "Indirect conflict raises logistics and price risk without full direct war.",
    "Oil tanker attack": "Maritime risk increases insurance, shipping delay, and fuel market volatility.",
    "Energy infrastructure strike": "Physical energy infrastructure damage raises supply and repair uncertainty.",
    "Hormuz disruption": "High-impact chokepoint disruption affecting oil and gas shipping routes.",
    "Regional war": "Large-scale regional conflict with severe energy market and logistics stress.",
}

def calculate_geopolitical_shock(event_type, severity, duration_days, import_dependency, fossil_share, shipping_dependency):
    event_type = event_type if event_type in GEOPOLITICAL_EVENT_WEIGHTS else "Proxy conflict escalation"
    severity = int(clamp(severity, 0, 5))
    duration_days = int(clamp(duration_days, 0, 90))
    import_dependency = clamp(float(import_dependency), 0.0, 1.0)
    fossil_share = clamp(float(fossil_share), 0.0, 1.0)
    shipping_dependency = clamp(float(shipping_dependency), 0.0, 1.0)
    duration_factor = min(duration_days / 30.0, 1.5)
    if event_type == "None" or severity == 0 or duration_days == 0:
        oil_supply_disruption = 0.0
    else:
        oil_supply_disruption = severity * GEOPOLITICAL_EVENT_WEIGHTS[event_type] * duration_factor * 4.0
    oil_supply_disruption = clamp(oil_supply_disruption, 0.0, 60.0)
    price_spike_index = oil_supply_disruption * 1.25
    logistics_stress = oil_supply_disruption * shipping_dependency * 1.15
    grid_stress_index = clamp(
        oil_supply_disruption * import_dependency * 0.42
        + oil_supply_disruption * fossil_share * 0.38
        + logistics_stress * 0.20,
        0.0, 100.0
    )
    if grid_stress_index < 10:
        risk_level = "Low"
    elif grid_stress_index < 25:
        risk_level = "Moderate"
    elif grid_stress_index < 45:
        risk_level = "High"
    else:
        risk_level = "Critical"
    return {
        "event_type": event_type,
        "severity": severity,
        "duration_days": duration_days,
        "oil_supply_disruption_percent": round(oil_supply_disruption, 2),
        "price_spike_index": round(price_spike_index, 2),
        "logistics_stress": round(logistics_stress, 2),
        "grid_stress_index": round(grid_stress_index, 2),
        "risk_level": risk_level,
        "supply_penalty_pct": round(clamp(grid_stress_index * 0.18, 0.0, 18.0), 2),
        "demand_penalty_pct": round(clamp(price_spike_index * 0.035, 0.0, 8.0), 2),
        "event_note": GEOPOLITICAL_EVENT_NOTES.get(event_type, "Geopolitical shock scenario."),
        "model_note": "Simplified geopolitical energy shock simulation for decision support; not a political or market forecast.",
    }

def apply_geopolitical_shock_to_results(results, shock):
    updated = dict(results)
    supply_penalty = clamp(float(shock.get("supply_penalty_pct", 0.0)) / 100.0, 0.0, 0.30)
    demand_penalty = clamp(float(shock.get("demand_penalty_pct", 0.0)) / 100.0, 0.0, 0.15)
    original_demand = float(updated.get("demand", 0.0))
    original_renewable = float(updated.get("renewable_supply", 0.0))
    original_final = float(updated.get("final_supply", 0.0))
    original_battery = float(updated.get("battery_levels", 0.0))
    adjusted_demand = original_demand * (1.0 + demand_penalty)
    adjusted_final = original_final * (1.0 - supply_penalty)
    adjusted_shortfall = max(0.0, adjusted_demand - adjusted_final)
    updated["demand"] = round(adjusted_demand, 2)
    updated["final_supply"] = round(adjusted_final, 2)
    updated["shortfall"] = round(adjusted_shortfall, 2)
    updated["grid_dependency"] = round(safe_div(adjusted_shortfall, adjusted_demand) * 100 if adjusted_demand > 0 else 0.0, 2)
    updated["system_efficiency"] = round(clamp(100 - adjusted_shortfall * 0.55 - float(shock.get("grid_stress_index", 0.0)) * 0.08, 0.0, 100.0), 2)
    updated["battery_levels"] = round(max(0.0, original_battery - adjusted_shortfall * 0.08), 2)
    updated["renewable_ratio"] = round(safe_div(original_renewable, adjusted_final) * 100 if adjusted_final > 0 else 0.0, 2)
    updated["geopolitical_event_type"] = shock.get("event_type")
    updated["geopolitical_risk_level"] = shock.get("risk_level")
    updated["geopolitical_grid_stress_index"] = shock.get("grid_stress_index", 0.0)
    updated["geopolitical_price_spike_index"] = shock.get("price_spike_index", 0.0)
    updated["geopolitical_oil_supply_disruption_percent"] = shock.get("oil_supply_disruption_percent", 0.0)
    return updated

def build_geopolitical_reason_chain(shock, results):
    if st.session_state.get("ui_lang", "English") == "繁體中文":
        return pd.DataFrame([
            {"Signal": "地緣政治事件", "Value": shock.get("event_type", "None"), "Interpretation": shock.get("event_note", "")},
            {"Signal": "油氣供應中斷估計", "Value": f"{shock.get('oil_supply_disruption_percent', 0)}%", "Interpretation": "用事件嚴重度、持續時間與地點權重估算的簡化中斷壓力。"},
            {"Signal": "價格衝擊指數", "Value": shock.get("price_spike_index", 0), "Interpretation": "代表市場價格與燃料成本壓力，不等於實際油價預測。"},
            {"Signal": "電網壓力指數", "Value": shock.get("grid_stress_index", 0), "Interpretation": f"目前風險等級：{shock.get('risk_level', 'Low')}。"},
            {"Signal": "系統結果", "Value": f"Shortfall {results.get('shortfall', 0)} MW", "Interpretation": "衝擊已折算進需求、可用供應、效率與外部依賴。"},
        ])
    return pd.DataFrame([
        {"Signal": "Geopolitical Event", "Value": shock.get("event_type", "None"), "Interpretation": shock.get("event_note", "")},
        {"Signal": "Oil/Gas Supply Disruption Estimate", "Value": f"{shock.get('oil_supply_disruption_percent', 0)}%", "Interpretation": "Simplified disruption pressure from severity, duration, and location weight."},
        {"Signal": "Price Spike Index", "Value": shock.get("price_spike_index", 0), "Interpretation": "Market and fuel-cost stress signal; not an oil price forecast."},
        {"Signal": "Grid Stress Index", "Value": shock.get("grid_stress_index", 0), "Interpretation": f"Current geopolitical risk level: {shock.get('risk_level', 'Low')}."},
        {"Signal": "System Result", "Value": f"Shortfall {results.get('shortfall', 0)} MW", "Interpretation": "Shock is reflected in demand, usable supply, efficiency, and grid dependency."},
    ])


def _risk_color_class(value):
    try:
        v = float(value)
    except Exception:
        v = 0.0
    if v >= 70:
        return "critical"
    if v >= 40:
        return "watch"
    return "stable"

def _scenario_stress_profile(results, geopolitical_shock=None):
    shock = geopolitical_shock or {}
    return {
        "solar": round(float(results.get("actual_mix_pct", {}).get("Solar", 0.0)), 1),
        "wind": round(float(results.get("actual_mix_pct", {}).get("Wind", 0.0)), 1),
        "hydro": round(float(results.get("actual_mix_pct", {}).get("Hydro", 0.0)), 1),
        "geothermal": round(float(results.get("actual_mix_pct", {}).get("Geothermal", 0.0)), 1),
        "grid_stress": round(float(results.get("grid_dependency", 0.0)), 1),
        "shortfall": round(float(results.get("shortfall", 0.0)), 2),
        "battery": round(float(results.get("battery_levels", 0.0)), 2),
        "geopolitical_stress": round(float(shock.get("grid_stress_index", results.get("geopolitical_grid_stress_index", 0.0))), 1),
        "oil_disruption": round(float(shock.get("oil_supply_disruption_percent", 0.0)), 1),
        "price_spike": round(float(shock.get("price_spike_index", 0.0)), 1),
    }

def render_visual_simulator_header():
    st.markdown("""
        <style>
        .visual-wrap {border:1px solid rgba(255,255,255,0.10); border-radius:22px; padding:18px; background:linear-gradient(145deg, rgba(15,23,42,0.88), rgba(30,41,59,0.72)); margin:10px 0 18px 0;}
        .visual-title {font-size:1.15rem; font-weight:800; margin-bottom:4px;}
        .visual-note {opacity:0.78; font-size:0.92rem; line-height:1.55; margin-bottom:12px;}
        .flow-grid {display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; margin-top:12px;}
        .flow-card {border:1px solid rgba(255,255,255,0.10); background:rgba(255,255,255,0.045); border-radius:16px; padding:12px; min-height:86px;}
        .flow-label {font-size:0.78rem; opacity:0.72; margin-bottom:6px;}
        .flow-value {font-size:1.25rem; font-weight:800;}
        .stable {box-shadow: inset 0 0 0 1px rgba(34,197,94,0.28);}
        .watch {box-shadow: inset 0 0 0 1px rgba(245,158,11,0.38);}
        .critical {box-shadow: inset 0 0 0 1px rgba(239,68,68,0.42);}
        .scenario-map {height:360px; position:relative; overflow:hidden; border-radius:22px; background:radial-gradient(circle at 50% 45%, rgba(59,130,246,0.22), transparent 30%), linear-gradient(180deg, rgba(2,6,23,0.85), rgba(15,23,42,0.95)); border:1px solid rgba(255,255,255,0.10); margin-top:12px;}
        .city-node {position:absolute; left:49%; top:48%; width:18px; height:18px; border-radius:99px; background:white; box-shadow:0 0 22px rgba(255,255,255,0.9);}
        .pulse {position:absolute; border:1px solid rgba(125,211,252,0.35); border-radius:999px; animation:pulse-ring 3s infinite ease-out;}
        .pulse.p2 {animation-delay:.65s;} .pulse.p3 {animation-delay:1.25s;}
        .storm-core {position:absolute; width:116px; height:116px; left:22%; top:24%; border-radius:999px; background:conic-gradient(from 45deg, rgba(148,163,184,0.10), rgba(56,189,248,0.75), rgba(15,23,42,0.15), rgba(96,165,250,0.65)); animation:spin 7s linear infinite; opacity:.9;}
        .heat-dome {position:absolute; width:240px; height:180px; left:28%; top:28%; border-radius:999px; background:radial-gradient(circle, rgba(251,146,60,0.38), rgba(239,68,68,0.16), transparent 70%); animation:heat-breathe 3.2s infinite ease-in-out;}
        .snow-band {position:absolute; inset:0; background-image:radial-gradient(circle, rgba(255,255,255,.55) 1px, transparent 1.5px); background-size:28px 28px; animation:drift 10s linear infinite; opacity:.45;}
        .route-line {position:absolute; left:14%; top:54%; width:72%; height:3px; background:linear-gradient(90deg, rgba(56,189,248,.15), rgba(248,113,113,.95), rgba(56,189,248,.15)); transform:rotate(-8deg); box-shadow:0 0 18px rgba(248,113,113,.65);}
        .route-shock {position:absolute; left:48%; top:43%; width:70px; height:70px; border-radius:999px; background:radial-gradient(circle, rgba(248,113,113,.65), transparent 62%); animation:pulse-red 2.2s infinite ease-in-out;}
        .battery-shell {position:absolute; left:27%; top:37%; width:46%; height:70px; border:2px solid rgba(255,255,255,.72); border-radius:18px; padding:8px;}
        .battery-tip {position:absolute; right:24%; top:45%; width:18px; height:38px; border:2px solid rgba(255,255,255,.72); border-left:none; border-radius:0 8px 8px 0;}
        .battery-fill {height:100%; border-radius:12px; background:linear-gradient(90deg, rgba(34,197,94,.88), rgba(250,204,21,.88), rgba(239,68,68,.88)); transition:width .5s ease;}
        @keyframes pulse-ring {0%{width:40px;height:40px;left:calc(50% - 20px);top:calc(50% - 20px);opacity:.75;}100%{width:300px;height:300px;left:calc(50% - 150px);top:calc(50% - 150px);opacity:0;}}
        @keyframes pulse-red {0%,100%{transform:scale(.78);opacity:.7;}50%{transform:scale(1.28);opacity:.25;}}
        @keyframes spin {to{transform:rotate(360deg);}}
        @keyframes heat-breathe {0%,100%{transform:scale(.92);opacity:.58;}50%{transform:scale(1.14);opacity:.9;}}
        @keyframes drift {to{background-position:60px 120px;}}
        </style>
        """, unsafe_allow_html=True)

def render_visual_metric_cards(profile):
    st.markdown(f"""
        <div class="flow-grid">
          <div class="flow-card {_risk_color_class(100-profile['solar'])}"><div class="flow-label">Solar Contribution</div><div class="flow-value">{profile['solar']}%</div></div>
          <div class="flow-card {_risk_color_class(100-profile['wind'])}"><div class="flow-label">Wind Contribution</div><div class="flow-value">{profile['wind']}%</div></div>
          <div class="flow-card {_risk_color_class(profile['grid_stress'])}"><div class="flow-label">Grid Dependency</div><div class="flow-value">{profile['grid_stress']}%</div></div>
          <div class="flow-card {_risk_color_class(profile['geopolitical_stress'])}"><div class="flow-label">Geo Shock Stress</div><div class="flow-value">{profile['geopolitical_stress']}</div></div>
        </div>
        """, unsafe_allow_html=True)

def render_scenario_visual_map(visual_scenario, profile):
    try:
        battery_pct = int(clamp(profile.get("battery", 0.0) / max(float(inputs.get("battery_capacity", 1.0)), 1.0) * 100.0, 0.0, 100.0))
    except Exception:
        battery_pct = 50
    if visual_scenario == "Typhoon Impact":
        inner = '<div class="storm-core"></div><div class="pulse"></div><div class="pulse p2"></div><div class="pulse p3"></div><div class="city-node"></div>'
        caption = "Typhoon bands reduce solar output, destabilize wind contribution, and push the system toward battery support."
    elif visual_scenario == "Heat Wave Spread":
        inner = '<div class="heat-dome"></div><div class="pulse"></div><div class="pulse p2"></div><div class="city-node"></div>'
        caption = "Heat load expands around the city; demand rises while cooling-sensitive facilities consume reserve margin faster."
    elif visual_scenario == "Blizzard / Cold Wave":
        inner = '<div class="snow-band"></div><div class="pulse"></div><div class="pulse p2"></div><div class="city-node"></div>'
        caption = "Cold stress suppresses solar availability, raises heating load, and shortens survival time when reserve is weak."
    elif visual_scenario == "Battery Depletion":
        inner = f'<div class="battery-shell"><div class="battery-fill" style="width:{battery_pct}%;"></div></div><div class="battery-tip"></div><div class="pulse"></div>'
        caption = "Battery reserve becomes the visible buffer between disrupted supply and critical facility failure."
    else:
        inner = '<div class="route-line"></div><div class="route-shock"></div><div class="pulse"></div><div class="pulse p2"></div><div class="city-node"></div>'
        caption = "External shock travels through fuel markets, import routes, logistics, and grid dependency before appearing as shortfall."
    st.markdown(f"""
        <div class="visual-wrap">
          <div class="visual-title">{visual_scenario}</div>
          <div class="visual-note">{caption}</div>
          <div class="scenario-map">{inner}</div>
        </div>
        """, unsafe_allow_html=True)

def render_energy_flow_diagram(profile):
    st.markdown("#### Energy Flow Interpretation")
    for name, value in [("Solar", profile["solar"]), ("Wind", profile["wind"]), ("Hydro", profile["hydro"]), ("Geothermal", profile["geothermal"])]:
        width = max(4, min(100, int(value)))
        st.markdown(f"""
            <div style="display:grid; grid-template-columns:110px 1fr 72px; gap:10px; align-items:center; margin:8px 0;">
              <div style="font-weight:700; opacity:.9;">{name}</div>
              <div style="height:12px; background:rgba(255,255,255,.10); border-radius:999px; overflow:hidden;">
                <div style="width:{width}%; height:100%; background:linear-gradient(90deg, rgba(96,165,250,.95), rgba(34,211,238,.95)); border-radius:999px;"></div>
              </div>
              <div style="text-align:right; opacity:.85;">{value}%</div>
            </div>
            """, unsafe_allow_html=True)

def render_visual_scenario_layer(results, baseline_results, geopolitical_shock=None):
    render_visual_simulator_header()
    st.markdown(f'<div class="note">{tr("visual_simulator_note")}</div>', unsafe_allow_html=True)
    left, right = st.columns([1.05, 1.4])
    with left:
        visual_scenario = st.selectbox(tr("visual_scenario"), ["Typhoon Impact", "Heat Wave Spread", "Blizzard / Cold Wave", "Battery Depletion", "Geopolitical Shock"])
        profile = _scenario_stress_profile(results, geopolitical_shock)
        render_visual_metric_cards(profile)
        st.markdown("#### Stress Chain")
        if visual_scenario == "Geopolitical Shock":
            chain_df = pd.DataFrame([
                {"Stage": "External event", "Signal": str((geopolitical_shock or {}).get("event_type", "None"))},
                {"Stage": "Oil / gas disruption", "Signal": f"{profile['oil_disruption']}%"},
                {"Stage": "Price spike", "Signal": profile["price_spike"]},
                {"Stage": "Grid stress", "Signal": profile["geopolitical_stress"]},
                {"Stage": "Shortfall", "Signal": f"{profile['shortfall']} MW"},
            ])
        elif visual_scenario == "Battery Depletion":
            chain_df = pd.DataFrame([
                {"Stage": "Demand", "Signal": f"{results.get('demand', 0)} MW"},
                {"Stage": "Renewable supply", "Signal": f"{results.get('renewable_supply', 0)} MW"},
                {"Stage": "Battery remaining", "Signal": f"{profile['battery']} MWh"},
                {"Stage": "Shortfall", "Signal": f"{profile['shortfall']} MW"},
            ])
        else:
            chain_df = pd.DataFrame([
                {"Stage": "Climate event", "Signal": visual_scenario},
                {"Stage": "Renewable change", "Signal": f"Solar {profile['solar']}% / Wind {profile['wind']}%"},
                {"Stage": "Grid dependency", "Signal": f"{profile['grid_stress']}%"},
                {"Stage": "Battery buffer", "Signal": f"{profile['battery']} MWh"},
                {"Stage": "Shortfall", "Signal": f"{profile['shortfall']} MW"},
            ])
        st.dataframe(chain_df, use_container_width=True, hide_index=True)
    with right:
        render_scenario_visual_map(visual_scenario, profile)
        render_energy_flow_diagram(profile)

def extend_i18n():
    extras = {
        "English": {
            "sim_hours": "Simulation Hours",
            "survival_mode": "Survival Mode",
            "enable_thermal": "Enable Thermal Concept",
            "animation_speed": "Animation Speed",
            "uploaded_data": "Uploaded Open Data CSV",
            "use_uploaded": "Use uploaded row as input preset",
            "uploaded_row": "Uploaded Row",
            "csv_mode": "CSV Preset Mode",
            "uploaded_preview": "Uploaded History Preview",
            "selected_timestamp": "Selected Timestamp",
            "parsed_timestamp": "Parsed Timestamp",
            "forecast_chart": "Forecast Chart",
            "forecast_chart_note": "This chart visualizes each source across the forecast horizon, including lower and upper confidence bands.",
            "source_logic": "Source Forecast Logic",
            "source_logic_note": "Different sources do not accelerate at the same rate. Solar and wind react more strongly to weather shifts, geothermal is more damped, and hydro sits in the middle unless the scenario widens uncertainty.",
            "source_forecast_factor": "Source Forecast Factor",
            "geopolitical_inputs": "Geopolitical Risk Inputs",
            "enable_geopolitical_shock": "Enable Geopolitical Shock",
            "geopolitical_event_type": "Geopolitical Event Type",
            "geopolitical_severity": "Conflict Severity",
            "geopolitical_duration_days": "Shock Duration Days",
            "fossil_share": "Fossil Fuel Share",
            "geopolitical_panel": "Geopolitical Energy Shock",
            "oil_supply_disruption": "Oil Supply Disruption",
            "price_spike_index": "Price Spike Index",
            "geopolitical_grid_stress": "Geopolitical Grid Stress",
            "geopolitical_risk_level": "Geopolitical Risk Level",
            "geopolitical_reason_chain": "Geopolitical Reason Chain",
            "geopolitical_model_note": "This module converts geopolitical tension into energy-system stress. It is for decision support, not prediction.",
            "visual_simulator": "Visual Scenario Simulator",
            "visual_scenario": "Visual Scenario",
            "visual_simulator_note": "This visual layer turns the current model outputs into an intuitive disruption map. It is designed for quick explanation during demos, not as a GIS or real-time weather product."
        },
        "繁體中文": {
            "sim_hours": "模擬時數",
            "survival_mode": "生存模式",
            "enable_thermal": "啟用熱管理概念",
            "animation_speed": "動畫速度",
            "uploaded_data": "上傳 Open Data CSV",
            "use_uploaded": "使用上傳列作為輸入預設",
            "uploaded_row": "上傳資料列",
            "csv_mode": "CSV 預設模式",
            "uploaded_preview": "上傳歷史預覽",
            "selected_timestamp": "選定時間",
            "parsed_timestamp": "解析後時間",
            "forecast_chart": "預測圖表",
            "forecast_chart_note": "這張圖會把各能源在 forecast horizon 中的預測值，以及上下信賴帶一起畫出來。",
            "source_logic": "來源預測邏輯",
            "source_logic_note": "不同能源的加速/阻尼不一樣。太陽能與風能對天氣變化更敏感，地熱較平穩，水力通常介於中間，極端情境下不確定性會再放大。",
            "source_forecast_factor": "來源預測因子",
            "geopolitical_inputs": "地緣政治風險輸入",
            "enable_geopolitical_shock": "啟用地緣政治衝擊",
            "geopolitical_event_type": "地緣政治事件類型",
            "geopolitical_severity": "衝突嚴重度",
            "geopolitical_duration_days": "衝擊持續天數",
            "fossil_share": "化石燃料占比",
            "geopolitical_panel": "地緣政治能源衝擊",
            "oil_supply_disruption": "油氣供應中斷",
            "price_spike_index": "價格衝擊指數",
            "geopolitical_grid_stress": "地緣政治電網壓力",
            "geopolitical_risk_level": "地緣政治風險等級",
            "geopolitical_reason_chain": "地緣政治理由鏈",
            "geopolitical_model_note": "此模組將地緣政治緊張轉換為能源系統壓力，僅供決策支援，不是預測。",
            "visual_simulator": "情境視覺模擬器",
            "visual_scenario": "視覺情境",
            "visual_simulator_note": "此視覺層會把目前模型輸出轉成直覺化的中斷圖，適合 Demo 快速說明；它不是 GIS，也不是即時氣象產品。"
        },
    }
    for lang, mapping in extras.items():
        I18N.setdefault(lang, {}).update({k: v for k, v in mapping.items() if k not in I18N.get(lang, {})})


extend_i18n()

with st.sidebar:
    ui_lang = st.selectbox("Language / 語言", list(I18N.keys()), index=list(I18N.keys()).index(st.session_state.get("ui_lang", "English")))
    st.session_state["ui_lang"] = ui_lang
    st.header(tr("controls"))

    demo_mode = st.selectbox(
        "Demo Mode",
        ["Manual", "Taiwan Typhoon", "Finland Blizzard", "Germany Energy Security", "Middle East Shock"],
        index=0,
        help="Use a prepared scenario for fast demos. Manual keeps all sidebar values unchanged.",
    )
    if demo_mode != "Manual":
        st.caption(f"Demo preset active: {demo_mode}")

    uploaded_baseline_file = st.file_uploader(tr("uploaded_data"), type=["csv"], key="uploaded_baseline_csv")
    uploaded_df = safe_read_csv(uploaded_baseline_file)
    uploaded_profiles = build_uploaded_profiles(uploaded_df)
    use_uploaded = False
    uploaded_profile = None
    uploaded_preview_df, uploaded_ts_col, uploaded_sorting_mode = prepare_uploaded_preview(uploaded_df)
    if uploaded_profiles:
        use_uploaded = st.toggle(tr("use_uploaded"), value=True)
        uploaded_row_key = st.selectbox(tr("uploaded_row"), list(uploaded_profiles.keys()))
        uploaded_profile = uploaded_profiles.get(uploaded_row_key)
        st.caption(f"{tr('csv_mode')}: {uploaded_row_key}")
        if uploaded_profile is not None:
            st.caption(f"{tr('selected_timestamp')}: {uploaded_profile.get('timestamp_value', '-') or '-'}")
        with st.expander(tr("uploaded_preview"), expanded=False):
            if uploaded_ts_col is not None:
                st.caption(f"{tr('timestamp_col')}: {uploaded_ts_col} • {tr('sorting_mode')}: {tr('timestamp_sorted') if uploaded_sorting_mode == 'timestamp' else tr('original_order')}")
            if uploaded_preview_df is not None:
                st.dataframe(uploaded_preview_df, use_container_width=True, hide_index=True)

    merged_city_data = {country_name: dict(cities) for country_name, cities in CITY_DATA.items()}
    for profile in uploaded_profiles.values():
        csv_country = safe_str(profile.get("country"), "Uploaded")
        csv_city = safe_str(profile.get("city"), "Row")
        merged_city_data.setdefault(csv_country, {})
        merged_city_data[csv_country].setdefault(csv_city, {
            "lat": safe_float(profile.get("lat"), 0.0),
            "lon": safe_float(profile.get("lon"), 0.0),
            "population": safe_int(profile.get("population"), 100000),
            "country_model": "CSV Open Data Model",
        })

    default_country = uploaded_profile["country"] if (use_uploaded and uploaded_profile) else list(merged_city_data.keys())[0]
    country_options = list(merged_city_data.keys())
    country_index = country_options.index(default_country) if default_country in country_options else 0
    country = st.selectbox(tr("country"), country_options, index=country_index, disabled=(use_uploaded and uploaded_profile is not None))

    city_options = list(merged_city_data[country].keys())
    default_city = uploaded_profile["city"] if (use_uploaded and uploaded_profile and uploaded_profile["country"] == country) else city_options[0]
    city_index = city_options.index(default_city) if default_city in city_options else 0
    city = st.selectbox(tr("city"), city_options, index=city_index, disabled=(use_uploaded and uploaded_profile is not None))
    city_profile = merged_city_data[country][city]

    active_country = uploaded_profile["country"] if (use_uploaded and uploaded_profile) else country
    active_city = uploaded_profile["city"] if (use_uploaded and uploaded_profile) else city
    active_lat = uploaded_profile["lat"] if (use_uploaded and uploaded_profile) else city_profile["lat"]
    active_lon = uploaded_profile["lon"] if (use_uploaded and uploaded_profile) else city_profile["lon"]
    active_population = uploaded_profile["population"] if (use_uploaded and uploaded_profile) else int(city_profile["population"])

    facility_type = st.selectbox(tr("facility_type"), list(FACILITY_PROFILES.keys()))
    facility_profile = FACILITY_PROFILES[facility_type]
    population = st.slider(tr("population"), 10000, 5000000, int(clamp(active_population, 10000, 5000000)), step=10000)
    st.caption(f"{tr('population')}: {population:,}")

    st.divider()
    st.subheader(tr("capacity_inputs"))
    solar_capacity = st.slider(tr("solar_capacity"), 0, 500, int(clamp((uploaded_profile["solar_capacity"] if (use_uploaded and uploaded_profile) else 120), 0, 500)), 5)
    wind_capacity = st.slider(tr("wind_capacity"), 0, 500, int(clamp((uploaded_profile["wind_capacity"] if (use_uploaded and uploaded_profile) else 80), 0, 500)), 5)
    geothermal_capacity = st.slider(tr("geothermal_capacity"), 0, 500, int(clamp((uploaded_profile["geothermal_capacity"] if (use_uploaded and uploaded_profile) else 60), 0, 500)), 5)
    hydro_capacity = st.slider(tr("hydro_capacity"), 0, 500, int(clamp((uploaded_profile["hydro_capacity"] if (use_uploaded and uploaded_profile) else 70), 0, 500)), 5)
    battery_capacity = st.slider(tr("battery_capacity"), 0, 1000, int(clamp((uploaded_profile["battery_capacity"] if (use_uploaded and uploaded_profile) else 180), 0, 1000)), 10)

    st.divider()
    st.subheader(tr("weather_inputs"))
    temperature = st.slider(tr("temperature") + " (°C)", -20, 50, int(clamp((uploaded_profile["temperature"] if (use_uploaded and uploaded_profile) else 26), -20, 50)), 1)
    wind_speed = st.slider(tr("wind_speed") + " (m/s)", 0.0, 30.0, float(clamp((uploaded_profile["wind_speed"] if (use_uploaded and uploaded_profile) else 4.2), 0.0, 30.0)), 0.1)
    solar_radiation = st.slider(tr("solar_radiation") + " (W/m²)", 0, 1200, int(clamp((uploaded_profile["solar_radiation"] if (use_uploaded and uploaded_profile) else 640), 0, 1200)), 10)
    precipitation = st.slider(tr("precipitation") + " (mm)", 0, 300, int(clamp((uploaded_profile["precipitation"] if (use_uploaded and uploaded_profile) else 12), 0, 300)), 1)
    humidity = st.slider(tr("humidity") + " (%)", 0, 100, int(clamp((uploaded_profile["humidity"] if (use_uploaded and uploaded_profile) else 73), 0, 100)), 1)
    scenario_key = st.selectbox(tr("weather_scenario"), list(SCENARIOS.keys()))

    st.divider()
    st.subheader(tr("stress_inputs"))
    solar_failure_ratio = st.number_input(tr("solar_failure_ratio"), 0.0, 1.0, 0.00, 0.05, format="%.2f")
    wind_failure_ratio = st.number_input(tr("wind_failure_ratio"), 0.0, 1.0, 0.00, 0.05, format="%.2f")
    geothermal_failure_ratio = st.number_input(tr("geothermal_failure_ratio"), 0.0, 1.0, 0.00, 0.05, format="%.2f")
    hydro_failure_ratio = st.number_input(tr("hydro_failure_ratio"), 0.0, 1.0, 0.00, 0.05, format="%.2f")
    battery_failure_ratio = st.number_input(tr("battery_failure_ratio"), 0.0, 1.0, 0.00, 0.05, format="%.2f")

    st.divider()
    st.subheader(tr("security_inputs"))
    energy_security_scenario = st.selectbox(tr("energy_security_scenario"), list(ENERGY_SECURITY_SCENARIOS.keys()))
    import_dependency = st.number_input(tr("import_dependency"), 0.0, 1.0, 0.70, 0.01, format="%.2f")
    strategic_reserve_days = st.number_input(tr("strategic_reserve_days"), 0, 365, 20, 1)
    shipping_dependency = st.number_input(tr("shipping_dependency"), 0.0, 1.0, 0.85, 0.01, format="%.2f")
    infrastructure_damage_ratio = st.number_input(tr("infrastructure_damage_ratio"), 0.0, 1.0, 0.10, 0.01, format="%.2f")
    reserve_recovery_lag_days = st.number_input(tr("reserve_recovery_lag_days"), 0, 30, 3, 1)

    st.divider()
    st.subheader(tr("geopolitical_inputs"))
    enable_geopolitical_shock = st.toggle(tr("enable_geopolitical_shock"), value=False)
    geopolitical_event_type = st.selectbox(tr("geopolitical_event_type"), list(GEOPOLITICAL_EVENT_WEIGHTS.keys()), index=0)
    geopolitical_severity = st.slider(tr("geopolitical_severity"), 0, 5, 2, 1)
    geopolitical_duration_days = st.slider(tr("geopolitical_duration_days"), 0, 90, 7, 1)
    fossil_share = st.slider(tr("fossil_share"), 0.0, 1.0, 0.40, 0.05)

    st.divider()
    st.subheader(tr("time_window_control"))
    rolling_window_rows = st.slider(tr("time_window_rows"), 2, 8, 3, 1)
    forecast_steps = st.slider(tr("forecast_steps"), 1, 6, 2, 1)
    confidence_level = st.slider(tr("confidence_level"), 0.5, 2.0, 1.0, 0.1)

    st.divider()
    st.subheader(tr("timeline_inputs"))
    simulation_hours = st.selectbox(tr("sim_hours"), [24, 72, 168], index=0)
    primary_supply_failure_ratio = st.number_input(tr("primary_supply_failure_ratio"), 0.0, 1.0, 0.30, 0.01, format="%.2f")
    reserve_energy_per_day = st.number_input(tr("reserve_energy_per_day"), 20.0, 300.0, 120.0, 5.0, format="%.1f")
    survival_mode = st.selectbox(tr("survival_mode"), ["full_load", "critical_load_only"], index=0)

    st.divider()
    st.subheader(tr("thermal_inputs"))
    thermal_concept_enabled = st.toggle(tr("enable_thermal"), value=True)
    fresh_air_temp_c = st.slider(tr("outside_air") + " (°C)", -30.0, 20.0, -8.0, 0.5)
    exhaust_air_temp_c = st.slider(tr("indoor_exhaust_air") + " (°C)", 10.0, 35.0, 23.0, 0.5)
    recovery_efficiency = st.slider(tr("thermal_recovery_efficiency"), 0.0, 1.0, 0.72, 0.01)
    thermal_animation_speed = st.slider(tr("animation_speed"), 0.4, 2.5, 1.0, 0.1)

# V4 Demo Mode presets: override runtime values after widgets are created,
# so manual controls remain available while demos can be activated instantly.
if demo_mode != "Manual":
    demo_presets = {
        "Taiwan Typhoon": {
            "country": "Taiwan", "city": "Taipei", "population": 2500000,
            "scenario_key": "typhoon", "temperature": 29, "wind_speed": 18.0,
            "solar_radiation": 180, "precipitation": 160, "humidity": 92,
            "solar_failure_ratio": 0.25, "wind_failure_ratio": 0.18, "hydro_failure_ratio": 0.12, "battery_failure_ratio": 0.08,
            "enable_geopolitical_shock": False,
        },
        "Finland Blizzard": {
            "country": "Finland", "city": "Helsinki", "population": 664000,
            "scenario_key": "blizzard", "temperature": -12, "wind_speed": 14.0,
            "solar_radiation": 90, "precipitation": 80, "humidity": 84,
            "solar_failure_ratio": 0.35, "wind_failure_ratio": 0.16, "hydro_failure_ratio": 0.08, "battery_failure_ratio": 0.10,
            "enable_geopolitical_shock": False,
        },
        "Germany Energy Security": {
            "country": "Germany", "city": "Berlin", "population": 3570000,
            "scenario_key": "cold_wave", "temperature": 1, "wind_speed": 5.5,
            "solar_radiation": 220, "precipitation": 28, "humidity": 78,
            "import_dependency": 0.62, "shipping_dependency": 0.55, "infrastructure_damage_ratio": 0.12,
            "reserve_recovery_lag_days": 7, "enable_geopolitical_shock": False,
        },
        "Middle East Shock": {
            "country": active_country, "city": active_city, "population": population,
            "scenario_key": scenario_key, "import_dependency": max(import_dependency, 0.78),
            "shipping_dependency": max(shipping_dependency, 0.90), "infrastructure_damage_ratio": max(infrastructure_damage_ratio, 0.18),
            "reserve_recovery_lag_days": max(reserve_recovery_lag_days, 10),
            "enable_geopolitical_shock": True, "geopolitical_event_type": "Hormuz disruption",
            "geopolitical_severity": 4, "geopolitical_duration_days": 21, "fossil_share": max(fossil_share, 0.55),
        },
    }
    preset = demo_presets.get(demo_mode, {})
    active_country = preset.get("country", active_country)
    active_city = preset.get("city", active_city)
    population = int(preset.get("population", population))
    scenario_key = preset.get("scenario_key", scenario_key)
    temperature = preset.get("temperature", temperature)
    wind_speed = preset.get("wind_speed", wind_speed)
    solar_radiation = preset.get("solar_radiation", solar_radiation)
    precipitation = preset.get("precipitation", precipitation)
    humidity = preset.get("humidity", humidity)
    solar_failure_ratio = preset.get("solar_failure_ratio", solar_failure_ratio)
    wind_failure_ratio = preset.get("wind_failure_ratio", wind_failure_ratio)
    hydro_failure_ratio = preset.get("hydro_failure_ratio", hydro_failure_ratio)
    battery_failure_ratio = preset.get("battery_failure_ratio", battery_failure_ratio)
    import_dependency = preset.get("import_dependency", import_dependency)
    shipping_dependency = preset.get("shipping_dependency", shipping_dependency)
    infrastructure_damage_ratio = preset.get("infrastructure_damage_ratio", infrastructure_damage_ratio)
    reserve_recovery_lag_days = preset.get("reserve_recovery_lag_days", reserve_recovery_lag_days)
    enable_geopolitical_shock = preset.get("enable_geopolitical_shock", enable_geopolitical_shock)
    geopolitical_event_type = preset.get("geopolitical_event_type", geopolitical_event_type)
    geopolitical_severity = preset.get("geopolitical_severity", geopolitical_severity)
    geopolitical_duration_days = preset.get("geopolitical_duration_days", geopolitical_duration_days)
    fossil_share = preset.get("fossil_share", fossil_share)

failure_ratios = {
    "solar": solar_failure_ratio,
    "wind": wind_failure_ratio,
    "geothermal": geothermal_failure_ratio,
    "hydro": hydro_failure_ratio,
    "battery": battery_failure_ratio,
}
inputs = {
    "country_key": active_country, "city_key": active_city, "lat": active_lat, "lon": active_lon,
    "temperature": temperature, "wind_speed": wind_speed, "solar_radiation": solar_radiation,
    "precipitation": precipitation, "humidity": humidity, "population": population,
    "solar_capacity": solar_capacity, "wind_capacity": wind_capacity,
    "geothermal_capacity": geothermal_capacity, "hydro_capacity": hydro_capacity,
    "battery_capacity": battery_capacity,
}
critical_load_share = facility_profile["critical_load_share"]

results = compute_energy_supply(inputs, scenario_key, failure_ratios, reserve_recovery_lag_days)
results, _ = apply_energy_security_layer(
    base_results=results,
    scenario_key=energy_security_scenario,
    import_dependency=import_dependency,
    strategic_reserve_days=strategic_reserve_days,
    critical_load_share=critical_load_share,
    shipping_dependency=shipping_dependency,
    infrastructure_damage_ratio=infrastructure_damage_ratio,
    reserve_recovery_lag_days=reserve_recovery_lag_days,
)
results = apply_extended_security(results, 0.2, 0.8, 7, 0.25, 0.2)

geopolitical_shock = calculate_geopolitical_shock(
    event_type=geopolitical_event_type if enable_geopolitical_shock else "None",
    severity=geopolitical_severity if enable_geopolitical_shock else 0,
    duration_days=geopolitical_duration_days if enable_geopolitical_shock else 0,
    import_dependency=import_dependency,
    fossil_share=fossil_share,
    shipping_dependency=shipping_dependency,
)
results = apply_geopolitical_shock_to_results(results, geopolitical_shock)

timeline_results = simulate_survival_timeline(
    demand=results["demand"],
    renewable_supply=results["renewable_supply"],
    battery_capacity=inputs["battery_capacity"] * (1 - battery_failure_ratio),
    strategic_reserve_days=strategic_reserve_days,
    critical_load_share=critical_load_share,
    weather_scenario=scenario_key,
    simulation_hours=simulation_hours,
    primary_supply_failure_ratio=primary_supply_failure_ratio,
    reserve_energy_per_day=reserve_energy_per_day,
    survival_mode=survival_mode,
)

baseline_results = compute_energy_supply(inputs, "normal", failure_ratios={k: 0.0 for k in failure_ratios}, reserve_recovery_lag_days=0)
baseline_results, _ = apply_energy_security_layer(
    base_results=baseline_results,
    scenario_key="normal",
    import_dependency=import_dependency,
    strategic_reserve_days=strategic_reserve_days,
    critical_load_share=critical_load_share,
    shipping_dependency=shipping_dependency,
    infrastructure_damage_ratio=0.0,
    reserve_recovery_lag_days=0.0,
)

reference_avg = compute_reference_average(inputs, uploaded_df, active_country, active_city)
energy_contribution_df = build_energy_contribution_df(results, baseline_results, reference_avg)
trend_estimate_df, multistep_forecast_df, trend_meta = compute_trend_estimates(inputs, uploaded_df, active_country, active_city, baseline_results, scenario_key=scenario_key, rolling_window_rows=rolling_window_rows, forecast_steps=forecast_steps, confidence_level=confidence_level)

st.title(tr("title"))
st.caption(tr("caption"))
st.caption("V4 Product Polish • Demo Mode / Export Center / Decision Support Guardrails")
st.markdown(f'<div class="hero"><h3>{tr("hero_title")}</h3><p>{tr("hero_body")}</p></div>', unsafe_allow_html=True)

layer_cols = st.columns(3)
for col, label, desc in zip(layer_cols, [tr("core"), tr("decision"), tr("concept")], [tr("core_desc"), tr("decision_desc"), tr("concept_desc")]):
    with col:
        st.markdown(f'<div class="layer-box"><div class="card-label">{label}</div><div class="card-value" style="font-size:0.98rem;">{desc}</div></div>', unsafe_allow_html=True)

top_left, top_right = st.columns([1.02, 1.08])
with top_left:
    st.subheader(tr("country_logic") + f": {active_country}")
    st.write(COUNTRY_NOTES.get(active_country, "Regional energy model loaded."))
    st.subheader(tr("facility_logic"))
    st.write(facility_profile["notes"])
    info_cols = st.columns(3)
    with info_cols[0]:
        mini_card(tr("facility_type"), facility_type)
    with info_cols[1]:
        mini_card("Critical Load Share", f"{facility_profile['critical_load_share'] * 100:.0f}%")
    with info_cols[2]:
        mini_card("Temp Band", f"{facility_profile['temp_band_c']} °C")

with top_right:
    st.subheader(tr("input_summary"))
    c1, c2 = st.columns(2)
    with c1:
        mini_card(tr("country"), active_country)
        mini_card(tr("city"), active_city)
        mini_card(tr("population"), f"{population:,}")
        mini_card(tr("weather_scenario"), scenario_key.replace("_", " ").title())
    with c2:
        mini_card("Energy Security", energy_security_scenario.replace("_", " ").title())
        if enable_geopolitical_shock:
            mini_card(tr("geopolitical_risk_level"), geopolitical_shock["risk_level"])
        mini_card("Facility Tolerance", f"{facility_profile['failure_tolerance_hours']} h")
        mini_card("Import Dependency", f"{import_dependency * 100:.0f}%")
        mini_card("Timeline Horizon", f"{simulation_hours} h")
        if use_uploaded and uploaded_profile is not None:
            mini_card(tr("selected_timestamp"), uploaded_profile.get("timestamp_value", "-") or "-")

st.subheader(tr("system_perf"))
perf_top = st.columns(4)
perf_top[0].metric(tr("demand"), f"{results['demand']} MW", delta=f"{round(results['demand'] - baseline_results['demand'], 2)} vs baseline")
perf_top[1].metric(tr("renewable"), f"{results['renewable_supply']} MW", delta=f"{round(results['renewable_supply'] - baseline_results['renewable_supply'], 2)}")
perf_top[2].metric(tr("final"), f"{results['final_supply']} MW", delta=f"{round(results['final_supply'] - baseline_results['final_supply'], 2)}")
perf_top[3].metric(tr("shortfall"), f"{results['shortfall']} MW", delta=f"{round(results['shortfall'] - baseline_results['shortfall'], 2)}")

st.subheader(tr("resilience"))
perf_bottom = st.columns(4)
perf_bottom[0].metric(tr("battery"), f"{results['battery_levels']} MWh")
perf_bottom[1].metric(tr("rr"), f"{results['renewable_ratio']}%")
perf_bottom[2].metric(tr("eff"), f"{results['system_efficiency']}%")
perf_bottom[3].metric(tr("grid"), f"{results['grid_dependency']}%")

status_cols = st.columns(4)
status_cols[0].metric(tr("status_shortfall"), build_status_label(results["shortfall"], (5, 15)))
status_cols[1].metric(tr("status_eff"), build_status_label(results["system_efficiency"], (85, 70), reverse=True))
status_cols[2].metric(tr("status_grid"), build_status_label(results["grid_dependency"], (10, 25)))
status_cols[3].metric(tr("status_reserve"), build_status_label(results.get("reserve_days_remaining", 0), (14, 7), reverse=True))

def build_executive_summary_text():
    lines = [
        "TAIVAS Executive Summary",
        "========================",
        f"Demo Mode: {demo_mode}",
        f"Location: {active_city}, {active_country}",
        f"Facility: {facility_type}",
        f"Weather Scenario: {scenario_key}",
        f"Energy Security Scenario: {energy_security_scenario}",
        "",
        "Core Metrics",
        f"- Demand: {results['demand']} MW",
        f"- Renewable Supply: {results['renewable_supply']} MW",
        f"- Final Supply: {results['final_supply']} MW",
        f"- Shortfall: {results['shortfall']} MW",
        f"- Battery Remaining: {results['battery_levels']} MWh",
        f"- System Efficiency: {results['system_efficiency']}%",
        f"- Grid Dependency: {results['grid_dependency']}%",
        "",
        "Risk Notes",
        f"- Geopolitical Risk Level: {geopolitical_shock.get('risk_level', 'N/A')}",
        f"- Oil/Gas Supply Disruption: {geopolitical_shock.get('oil_supply_disruption_percent', 0)}%",
        f"- Estimated Hours Until Shortfall: {timeline_results.get('hours_until_shortfall')}",
        f"- Estimated Hours Until Critical Failure: {timeline_results.get('hours_until_critical_failure')}",
        "",
        "Model Limitation",
        "TAIVAS is a decision-support simulator. It does not guarantee real-world outcomes and does not replace engineering, grid-operator, legal, security, or emergency-management validation.",
    ]
    return "\n".join(lines)


def render_product_notice():
    st.markdown(
        """
        <div class="notice-box">
        <b>Decision-support notice:</b> TAIVAS converts scenario assumptions into operational risk signals.
        It is not a disaster prediction engine, not a guarantee of physical system behavior, and not a substitute for professional engineering validation.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_executive_overview_workspace():
    if demo_mode != "Manual":
        st.markdown(f"<span class='demo-pill'>Demo Mode: {demo_mode}</span>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="product-strip">
          <div class="product-card"><div class="product-label">Location</div><div class="product-value">{active_city}</div><div class="product-sub">{active_country}</div></div>
          <div class="product-card"><div class="product-label">Scenario</div><div class="product-value">{scenario_key.replace('_',' ').title()}</div><div class="product-sub">{energy_security_scenario.replace('_',' ').title()}</div></div>
          <div class="product-card"><div class="product-label">Shortfall</div><div class="product-value">{results['shortfall']} MW</div><div class="product-sub">Grid dependency {results['grid_dependency']}%</div></div>
          <div class="product-card"><div class="product-label">Recommendation Focus</div><div class="product-value">{build_status_label(results['shortfall'], (5, 15)).title()}</div><div class="product-sub">Protect critical load first</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_product_notice()
    st.subheader("Executive Recommendation")
    for idx, line in enumerate(recommendation_lines(results, energy_security_scenario)[:3], 1):
        st.write(f"{idx}. {line}")


summary_txt = build_executive_summary_text()
buf_scen = StringIO(); comparison_dataframe(inputs, failure_ratios, reserve_recovery_lag_days).to_csv(buf_scen, index=False)
buf_reason = StringIO(); pd.DataFrame(recommendation_reason_chain(results, energy_security_scenario, timeline_results, facility_type, facility_profile)).to_csv(buf_reason, index=False)
audit_json = json.dumps({
    "version": "V4 Product Polish",
    "demo_mode": demo_mode,
    "country": active_country,
    "city": active_city,
    "facility_type": facility_type,
    "scenario_key": scenario_key,
    "results": results,
    "timeline": timeline_results,
    "geopolitical_shock": geopolitical_shock,
    "model_limitation": "Decision-support simulation only; not a prediction or guarantee.",
}, indent=2, ensure_ascii=False)

with st.expander("Export Center", expanded=False):
    st.caption("Download scenario data, reason chain, executive summary, or audit trail when needed.")
    download_cols = st.columns(4)
    with download_cols[0]:
        st.download_button(tr("download_scenario"), buf_scen.getvalue(), file_name="taivas_scenarios.csv", mime="text/csv")
    with download_cols[1]:
        st.download_button(tr("download_reason"), buf_reason.getvalue(), file_name="taivas_reason_chain.csv", mime="text/csv")
    with download_cols[2]:
        st.download_button(tr("download_summary"), summary_txt, file_name="taivas_executive_summary.txt", mime="text/plain")
    with download_cols[3]:
        st.download_button(tr("download_audit"), audit_json, file_name="taivas_audit_trail.json", mime="application/json")

def render_energy_mix_workspace():
    page_question(tr("tabs")[0])
    st.markdown(f'<div class="note">{tr("mix_note")}</div>', unsafe_allow_html=True)
    mix_cols = st.columns(2)
    with mix_cols[0]:
        st.subheader(tr("installed_mix"))
        st.pyplot(make_donut_chart(results["installed_mix_pct"], 100.0, title=tr("installed_mix")), clear_figure=True)
    with mix_cols[1]:
        st.subheader(tr("actual_mix"))
        st.pyplot(make_donut_chart(results["actual_mix_pct"], results["renewable_ratio"], title=tr("actual_mix")), clear_figure=True)
    mix_table = pd.DataFrame({
        tr("source"): list(results["actual_mix_mw"].keys()),
        tr("installed_capacity_mw"): [results["installed_mix_mw"][k] for k in results["actual_mix_mw"]],
        tr("actual_supply_mw"): [results["actual_mix_mw"][k] for k in results["actual_mix_mw"]],
        tr("installed_mix_pct"): [round(results["installed_mix_pct"][k], 2) for k in results["actual_mix_mw"]],
        tr("actual_mix_pct"): [round(results["actual_mix_pct"][k], 2) for k in results["actual_mix_mw"]],
        tr("capacity_factor_pct"): [results["capacity_factors"][k] for k in results["actual_mix_mw"]],
    })
    render_energy_contribution_panel(energy_contribution_df)
    render_reserve_outlook_panel(reference_avg, results, timeline_results)
    render_trend_estimate_panel(trend_estimate_df, multistep_forecast_df, trend_meta)
    st.subheader(tr("energy_table"))
    st.dataframe(mix_table, use_container_width=True, hide_index=True)
    st.caption(f"{tr('dominant')}: {results['dominant_source']}")


def render_scenario_comparison_workspace():
    page_question(tr("tabs")[1])
    delta_df = scenario_delta_df(baseline_results, results)
    scenario_df = comparison_dataframe(inputs, failure_ratios, reserve_recovery_lag_days)
    critical_load_df = critical_load_breakdown(results["demand"], facility_profile["critical_load_share"], facility_profile["critical_split"])
    left, right = st.columns([1.02, 1.0])
    with left:
        st.subheader(tr("baseline_vs_selected"))
        st.dataframe(delta_df, use_container_width=True, hide_index=True)
        render_delta_chart(delta_df)
    with right:
        st.subheader(tr("all_scenarios"))
        st.dataframe(scenario_df, use_container_width=True, hide_index=True)
        scenario_index_col = tr("scenario") if tr("scenario") in scenario_df.columns else "Scenario"
        shortfall_col = tr("shortfall") if tr("shortfall") in scenario_df.columns else "Shortfall"
        grid_col = tr("grid") if tr("grid") in scenario_df.columns else "Grid Dependency"
        st.bar_chart(scenario_df.set_index(scenario_index_col)[[shortfall_col, grid_col]])
    st.subheader(tr("critical_breakdown"))
    render_critical_load_chart(critical_load_df)
    st.dataframe(critical_load_df, use_container_width=True, hide_index=True)


def render_stress_test_workspace():
    page_question(tr("tabs")[2])
    st.markdown('<div class="note">Multi-failure stress testing and subsystem degradation view.</div>', unsafe_allow_html=True)
    stress_df = pd.DataFrame({tr("subsystem"): list(failure_ratios.keys()), tr("failure_ratio"): list(failure_ratios.values()), tr("availability_pct"): [round((1 - v) * 100, 1) for v in failure_ratios.values()]})
    st.dataframe(stress_df, use_container_width=True, hide_index=True)
    st.bar_chart(stress_df.set_index(tr("subsystem"))[[tr("availability_pct")]])


def render_ai_recommendation_workspace():
    page_question(tr("tabs")[3])
    st.subheader(tr("quick_reco"))
    for idx, line in enumerate(recommendation_lines(results, energy_security_scenario), 1):
        st.write(f"{idx}. {line}")
    reason_df = pd.DataFrame(recommendation_reason_chain(results, energy_security_scenario, timeline_results, facility_type, facility_profile))
    st.subheader(tr("reason_chain"))
    st.dataframe(reason_df, use_container_width=True, hide_index=True)


def render_energy_security_workspace():
    page_question(tr("tabs")[4])
    row1 = st.columns(4)
    row1[0].metric("Import Disruption", f"{results['import_disruption_score']}%")
    row1[1].metric(tr("reserve_days"), f"{results['reserve_days_remaining']} days")
    row1[2].metric("Fuel Cost Stress", f"{results['fuel_cost_stress']}%")
    row1[3].metric("Extended Disruption", f"{results['extended_disruption_score']}%")

    st.subheader(tr("geopolitical_panel"))
    st.markdown(f'<div class="note">{tr("geopolitical_model_note")}</div>', unsafe_allow_html=True)
    geo_cols = st.columns(4)
    geo_cols[0].metric(tr("oil_supply_disruption"), f"{geopolitical_shock['oil_supply_disruption_percent']}%")
    geo_cols[1].metric(tr("price_spike_index"), geopolitical_shock["price_spike_index"])
    geo_cols[2].metric(tr("geopolitical_grid_stress"), geopolitical_shock["grid_stress_index"])
    geo_cols[3].metric(tr("geopolitical_risk_level"), geopolitical_shock["risk_level"])
    st.caption(geopolitical_shock.get("event_note", ""))
    st.subheader(tr("geopolitical_reason_chain"))
    st.dataframe(build_geopolitical_reason_chain(geopolitical_shock, results), use_container_width=True, hide_index=True)


def render_survival_timeline_workspace():
    page_question(tr("tabs")[5])
    t1, t2, t3 = st.columns(3)
    t1.metric(tr("shortfall_hour"), timeline_results["hours_until_shortfall"])
    t2.metric(tr("critical_failure_hour"), timeline_results["hours_until_critical_failure"])
    t3.metric("Survival Mode", timeline_results["survival_mode_duration"])
    timeline_df = pd.DataFrame(timeline_results["rows"])
    if not timeline_df.empty:
        chart_cols = [c for c in ["raw_demand", "target_demand", "renewable_supply", "battery_used", "reserve_used", "final_supply", "shortfall", "battery_level", "reserve_energy"] if c in timeline_df.columns]
        if chart_cols:
            st.subheader(tr("timeline_chart"))
            st.line_chart(timeline_df[chart_cols])
    st.subheader(tr("timeline_table"))
    st.dataframe(timeline_df, use_container_width=True, hide_index=True)


def render_visual_simulator_workspace():
    page_question(tr("tabs")[6])
    st.subheader(tr("visual_simulator"))
    render_visual_scenario_layer(results, baseline_results, geopolitical_shock)


def render_concept_lab_workspace():
    page_question(tr("tabs")[7])
    st.markdown(f'<div class="note">{tr("concept_note")}</div>', unsafe_allow_html=True)
    concept_tabs = st.tabs(tr("thermal_tabs"))
    base_damage_pct = round((sum(failure_ratios.values()) / len(failure_ratios)) * 100, 1)
    base_div_score = round(len([v for v in results["actual_mix_mw"].values() if v > 0]) / 4 * 100, 1)
    timeline_shortfall_num = timeline_results["hours_until_shortfall"] if timeline_results["hours_until_shortfall"] != "No Failure" else 999
    timeline_critical_num = timeline_results["hours_until_critical_failure"] if timeline_results["hours_until_critical_failure"] != "No Failure" else 999
    thermal_results = {
        "adjusted_demand": results["demand"] * 0.95 if thermal_concept_enabled else results["demand"],
        "adjusted_reserve_days": results.get("reserve_days_remaining", 0) + 1,
        "adjusted_hours_until_shortfall": timeline_shortfall_num + 4,
        "adjusted_hours_until_critical_failure": timeline_critical_num + 5,
        "thermal_demand_reduction_pct": 5.0,
        "buffer_state_pct": 75.0,
        "sink_utilization_pct": 60.0,
        "damage_ratio_pct": max(base_damage_pct - 2, 0),
        "diversification_score": min(base_div_score + 5, 100),
    }
    with concept_tabs[0]:
        concept_badge()
        render_thermal_principle_simulation(fresh_air_temp_c=fresh_air_temp_c, exhaust_air_temp_c=exhaust_air_temp_c, recovery_efficiency=recovery_efficiency, airflow_speed=thermal_animation_speed, height=820)
    with concept_tabs[1]:
        concept_badge()
        render_phase_change_buffer_concept(heat_load_mw=max(results["demand"] * 0.18, 1.0), buffer_state_pct=thermal_results["buffer_state_pct"], demand_reduction_pct=max(thermal_results["thermal_demand_reduction_pct"], 1.0), reserve_bonus_hours=4.0, height=720)
    with concept_tabs[2]:
        concept_badge()
        render_ground_thermal_sink_concept(cooling_offset_pct=4.0, sink_utilization_pct=thermal_results["sink_utilization_pct"], saturation_risk_pct=20.0, height=720)
    with concept_tabs[3]:
        concept_badge()
        availability = round((1 - max(failure_ratios.values())) * 100, 0)
        rerouting_efficiency = round(max(40.0, 100 - (sum(failure_ratios.values()) / len(failure_ratios)) * 100), 0)
        render_distributed_thermal_control_concept(node_availability_pct=availability, rerouting_efficiency_pct=rerouting_efficiency, damage_ratio_pct=thermal_results["damage_ratio_pct"], protected_core_pct=round(max(45.0, 100 - results["grid_dependency"]), 0), height=720)
    with concept_tabs[4]:
        concept_badge()
        core_hours = timeline_results["hours_until_critical_failure"] if timeline_results["hours_until_critical_failure"] != "No Failure" else 168
        render_distributed_harvesting_buffering_concept(diversification_score=thermal_results["diversification_score"], reserve_gain_hours=4.0, shortfall_reduction_pct=8.0, core_preservation_hours=float(core_hours), height=720)


# -----------------------------------------------------------------------------
# V4 Product Polish Workspace Layer
# Users choose a workspace first, then see only the tabs relevant to that task.
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("Workspace Mode")
workspace_mode = st.radio(
    "Choose how you want to use TAIVAS",
    ["Executive Dashboard", "Analyst Workspace", "Concept Lab"],
    horizontal=True,
    help="Executive is for quick demos and decision review. Analyst is for deeper testing. Concept Lab is for thermal/resilience concept exploration.",
)

workspace_note = {
    "Executive Dashboard": "A clean demo view for investors, institutions, and non-technical reviewers. It focuses on what is happening, why it matters, and what the system recommends.",
    "Analyst Workspace": "A professional analysis view for scenario comparison, subsystem stress testing, survival timeline, and operational risk interpretation.",
    "Concept Lab": "An experimental visualization area for thermal buffering, ground sink, distributed control, and harvesting concepts.",
}
st.markdown(f'<div class="note">{workspace_note[workspace_mode]}</div>', unsafe_allow_html=True)

if workspace_mode == "Executive Dashboard":
    executive_tabs = st.tabs(["Operational Overview", "Visual Simulator", "AI Recommendation", "Energy Mix", "Energy Security"])
    with executive_tabs[0]:
        render_executive_overview_workspace()
    with executive_tabs[1]:
        render_visual_simulator_workspace()
    with executive_tabs[2]:
        render_ai_recommendation_workspace()
    with executive_tabs[3]:
        render_energy_mix_workspace()
    with executive_tabs[4]:
        render_energy_security_workspace()

elif workspace_mode == "Analyst Workspace":
    analyst_tabs = st.tabs(["Scenario Comparison", "Stress Test", "Survival Timeline", "Energy Security"])
    with analyst_tabs[0]:
        render_scenario_comparison_workspace()
    with analyst_tabs[1]:
        render_stress_test_workspace()
    with analyst_tabs[2]:
        render_survival_timeline_workspace()
    with analyst_tabs[3]:
        render_energy_security_workspace()

else:
    concept_workspace_tabs = st.tabs(["Concept Lab"])
    with concept_workspace_tabs[0]:
        render_concept_lab_workspace()
