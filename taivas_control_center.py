from io import StringIO
import json

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

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

st.set_page_config(page_title="TAIVAS Energy Control Center", layout="wide")

if "ui_lang" not in st.session_state:
    st.session_state["ui_lang"] = "English"

CITY_DATA = {
    "Taiwan": {
        "Taipei": {"lat": 25.0330, "lon": 121.5654, "population": 2500000, "country_model": "Island Resilience Model"},
        "Taichung": {"lat": 24.1477, "lon": 120.6736, "population": 2820000, "country_model": "Island Resilience Model"},
        "Kaohsiung": {"lat": 22.6273, "lon": 120.3014, "population": 2730000, "country_model": "Island Resilience Model"},
    },
    "Finland": {
        "Helsinki": {"lat": 60.1699, "lon": 24.9384, "population": 664000, "country_model": "Winter Reliability Model"},
        "Tampere": {"lat": 61.4978, "lon": 23.7610, "population": 255000, "country_model": "Winter Reliability Model"},
        "Rovaniemi": {"lat": 66.5039, "lon": 25.7294, "population": 65000, "country_model": "Winter Reliability Model"},
    },
    "Switzerland": {
        "Zurich": {"lat": 47.3769, "lon": 8.5417, "population": 435000, "country_model": "Alpine Stability Model"},
        "Geneva": {"lat": 46.2044, "lon": 6.1432, "population": 203000, "country_model": "Alpine Stability Model"},
        "Bern": {"lat": 46.9480, "lon": 7.4474, "population": 134000, "country_model": "Alpine Stability Model"},
    },
    "Norway": {
        "Oslo": {"lat": 59.9139, "lon": 10.7522, "population": 717000, "country_model": "Nordic Hydro Resilience Model"},
        "Bergen": {"lat": 60.3913, "lon": 5.3221, "population": 289000, "country_model": "Nordic Hydro Resilience Model"},
        "Trondheim": {"lat": 63.4305, "lon": 10.3951, "population": 214000, "country_model": "Nordic Hydro Resilience Model"},
    },
    "Germany": {
        "Berlin": {"lat": 52.5200, "lon": 13.4050, "population": 3570000, "country_model": "Industrial Transition Model"},
        "Hamburg": {"lat": 53.5511, "lon": 9.9937, "population": 1910000, "country_model": "Industrial Transition Model"},
        "Munich": {"lat": 48.1351, "lon": 11.5820, "population": 1510000, "country_model": "Industrial Transition Model"},
    },
}

COUNTRY_NOTES = {
    "Taiwan": "Cooling-heavy island model with strong storage need.",
    "Finland": "Cold-climate resilience model with winter reliability focus.",
    "Switzerland": "High-stability alpine model with balanced reserve planning.",
    "Norway": "Hydro-friendly Nordic model with strong resilience potential.",
    "Germany": "Industrial transition model with grid balancing importance.",
}

FACILITY_PROFILES = {
    "Long-term Care": {
        "critical_load_share": 0.48,
        "temp_band_c": "20–26",
        "notes": "Temperature stability, life-support continuity, and water systems are highly sensitive.",
        "priority_order": ["Medical", "Heating/Cooling", "Water Systems", "Communications"],
        "critical_split": {"Medical": 0.34, "Heating/Cooling": 0.28, "Water Systems": 0.22, "Communications": 0.16},
        "failure_tolerance_hours": 6,
    },
    "Hospital": {
        "critical_load_share": 0.58,
        "temp_band_c": "19–24",
        "notes": "ICU, surgery, pharmacy refrigeration, and core communications require stronger protection.",
        "priority_order": ["Medical", "Water Systems", "Heating/Cooling", "Communications"],
        "critical_split": {"Medical": 0.42, "Heating/Cooling": 0.22, "Water Systems": 0.18, "Communications": 0.18},
        "failure_tolerance_hours": 4,
    },
    "Data Center": {
        "critical_load_share": 0.52,
        "temp_band_c": "18–27",
        "notes": "Thermal stability and core digital continuity dominate the resilience profile.",
        "priority_order": ["Heating/Cooling", "Communications", "Water Systems", "Medical"],
        "critical_split": {"Medical": 0.05, "Heating/Cooling": 0.46, "Water Systems": 0.14, "Communications": 0.35},
        "failure_tolerance_hours": 3,
    },
    "School / Campus": {
        "critical_load_share": 0.28,
        "temp_band_c": "18–29",
        "notes": "Lower life-support sensitivity, but sheltering, water, and communications still matter.",
        "priority_order": ["Heating/Cooling", "Water Systems", "Communications", "Medical"],
        "critical_split": {"Medical": 0.08, "Heating/Cooling": 0.38, "Water Systems": 0.28, "Communications": 0.26},
        "failure_tolerance_hours": 12,
    },
    "Residential Block": {
        "critical_load_share": 0.22,
        "temp_band_c": "16–30",
        "notes": "Basic habitability, water, and communications matter more than clinical continuity.",
        "priority_order": ["Heating/Cooling", "Water Systems", "Communications", "Medical"],
        "critical_split": {"Medical": 0.07, "Heating/Cooling": 0.44, "Water Systems": 0.29, "Communications": 0.20},
        "failure_tolerance_hours": 16,
    },
}

SCENARIOS = {
    "normal": {"demand": 1.00, "solar": 1.00, "wind": 1.00, "hydro": 1.00, "geo": 1.00, "battery": 1.00},
    "heat_wave": {"demand": 1.22, "solar": 1.08, "wind": 0.90, "hydro": 0.93, "geo": 1.00, "battery": 0.96},
    "storm": {"demand": 1.10, "solar": 0.62, "wind": 1.20, "hydro": 1.05, "geo": 1.00, "battery": 0.90},
    "cold_wave": {"demand": 1.18, "solar": 0.72, "wind": 0.96, "hydro": 0.97, "geo": 1.00, "battery": 0.93},
    "blizzard": {"demand": 1.28, "solar": 0.40, "wind": 0.82, "hydro": 0.90, "geo": 1.00, "battery": 0.85},
    "typhoon": {"demand": 1.15, "solar": 0.35, "wind": 0.68, "hydro": 0.78, "geo": 1.00, "battery": 0.82},
}

I18N = {
    "English": {
        "title": "TAIVAS Energy Control Center",
        "caption": "TAIVAS is a resilience decision-support simulator for energy, thermal, and critical facility scenarios under extreme conditions.",
        "controls": "Controls",
        "country": "Country",
        "city": "City",
        "facility_type": "Facility Type",
        "population": "Population",
        "capacity_inputs": "Capacity Inputs",
        "weather_inputs": "Weather Inputs",
        "weather_scenario": "Weather Scenario",
        "stress_inputs": "Stress Inputs",
        "security_inputs": "Energy Security Inputs",
        "timeline_inputs": "Survival Timeline Inputs",
        "thermal_inputs": "Thermal Concept Inputs",
        "hero_title": "Operational Overview",
        "hero_body": "TAIVAS combines a core resilience simulator, an explainable decision-support layer, and a concept lab for advanced thermal ideas. It is designed to test how energy, thermal management, and critical facility protection behave under extreme climate and disruption scenarios.",
        "core": "Core Simulator",
        "decision": "Decision Support",
        "concept": "Concept Lab",
        "core_desc": "Models demand, renewable supply, battery support, failure ratios, reserve planning, facility logic, and survival timeline.",
        "decision_desc": "Explains risk signals, compares scenarios, structures recommendation chains, and produces export-ready summaries.",
        "concept_desc": "Explores thermal and resilience concepts as linked visuals for simulation insight, not hardware blueprints.",
        "country_logic": "Country Logic",
        "facility_logic": "Facility Logic",
        "input_summary": "Input Summary",
        "system_perf": "System Performance",
        "resilience": "Resilience Indicators",
        "demand": "Demand",
        "renewable": "Renewable Supply",
        "final": "Final Supply",
        "shortfall": "Shortfall",
        "battery": "Battery Levels",
        "rr": "Renewable Ratio",
        "eff": "System Efficiency",
        "grid": "Grid Dependency",
        "status_shortfall": "Shortfall Status",
        "status_eff": "Efficiency Status",
        "status_grid": "Grid Stress Status",
        "status_reserve": "Reserve Status",
        "stable": "Stable",
        "watch": "Watch",
        "critical": "Critical",
        "download_scenario": "Scenario CSV",
        "download_reason": "Reason Chain CSV",
        "download_summary": "Executive Summary TXT",
        "download_audit": "Audit Trail JSON",
        "tabs": ["Energy Mix", "Scenario Comparison", "Stress Test", "AI Recommendation", "Energy Security", "Survival Timeline", "Concept Lab"],
        "page_answers": "This page answers:",
        "mix_note": "This tab separates installed capacity from actual modeled supply. Weather, failure ratios, and scenario assumptions change the real contribution of each energy source.",
        "installed_mix": "Installed Capacity Mix",
        "actual_mix": "Actual Renewable Supply Mix",
        "energy_table": "Energy Source Table",
        "capacity_factors": "Capacity Factors",
        "dominant": "Dominant modeled renewable source",
        "baseline_vs_selected": "Baseline vs Selected Scenario",
        "all_scenarios": "All Weather Scenarios",
        "critical_breakdown": "Critical Load Breakdown",
        "quick_reco": "Quick Recommendation Layer",
        "reason_chain": "Reason Chain",
        "priority_signals": "Priority Signals",
        "timeline_chart": "Timeline Chart",
        "timeline_table": "Hourly Timeline Table",
        "concept_note": "These modules are illustrative simulation layers for resilience exploration. They are not hardware blueprints and do not replace physical engineering validation.",
        "concept_badge": "Conceptual Simulation • Not hardware-validated",
        "thermal_tabs": ["Thermal Principle", "Phase-Change Buffer", "Ground Sink", "Distributed Control", "Harvesting & Buffering"],
        "mode": "Mode",
        "current": "Current",
        "thermal_concept": "Thermal Concept",
        "reserve_days": "Reserve Days",
        "shortfall_hour": "Shortfall Hour",
        "critical_failure_hour": "Critical Failure Hour",
        "thermal_compare": "Current vs Thermal Concept",
    },
    "繁體中文": {
        "title": "TAIVAS 能源控制中心",
        "caption": "TAIVAS 是一套用於極端情境下能源、熱管理與關鍵設施韌性的決策支援模擬器。",
        "controls": "控制面板",
        "country": "國家",
        "city": "城市",
        "facility_type": "設施類型",
        "population": "人口",
        "capacity_inputs": "容量輸入",
        "weather_inputs": "天氣輸入",
        "weather_scenario": "天氣情境",
        "stress_inputs": "壓力測試輸入",
        "security_inputs": "能源安全輸入",
        "timeline_inputs": "生存時間軸輸入",
        "thermal_inputs": "熱管理概念輸入",
        "hero_title": "系統總覽",
        "hero_body": "TAIVAS 結合核心韌性模擬器、可解釋決策支援層，以及進階熱管理概念模組，用來測試在極端氣候與中斷情境下，能源、熱管理與關鍵設施保護會如何變化。",
        "core": "核心模擬層",
        "decision": "決策支援層",
        "concept": "概念模擬層",
        "core_desc": "模擬需求、再生能源供應、電池支援、失效比例、備援規劃、設施邏輯與生存時間軸。",
        "decision_desc": "解釋風險訊號、比較情境、整理建議鏈，並輸出可摘要的結果。",
        "concept_desc": "以可視化方式探索熱管理與韌性概念，不等同硬體藍圖。",
        "country_logic": "國家邏輯",
        "facility_logic": "設施邏輯",
        "input_summary": "輸入摘要",
        "system_perf": "系統表現",
        "resilience": "韌性指標",
        "demand": "需求",
        "renewable": "再生供應",
        "final": "最終供應",
        "shortfall": "缺口",
        "battery": "電池存量",
        "rr": "再生比例",
        "eff": "系統效率",
        "grid": "外部依賴",
        "status_shortfall": "缺口狀態",
        "status_eff": "效率狀態",
        "status_grid": "電網壓力狀態",
        "status_reserve": "備援狀態",
        "stable": "穩定",
        "watch": "注意",
        "critical": "危急",
        "download_scenario": "下載情境 CSV",
        "download_reason": "下載理由鏈 CSV",
        "download_summary": "下載摘要 TXT",
        "download_audit": "下載稽核 JSON",
        "tabs": ["能源組成", "情境比較", "壓力測試", "AI 建議", "能源安全", "生存時間軸", "概念模組"],
        "page_answers": "本頁回答：",
        "mix_note": "本頁將裝機容量與實際模擬供應拆開呈現。天氣、失效比例與情境假設，都會改變各能源的真實貢獻。",
        "installed_mix": "裝機容量組成",
        "actual_mix": "實際再生供應組成",
        "energy_table": "能源來源表",
        "capacity_factors": "容量因子",
        "dominant": "主要再生來源",
        "baseline_vs_selected": "基準與選定情境比較",
        "all_scenarios": "所有天氣情境",
        "critical_breakdown": "關鍵負載拆解",
        "quick_reco": "快速建議層",
        "reason_chain": "理由鏈",
        "priority_signals": "優先訊號",
        "timeline_chart": "時間軸圖表",
        "timeline_table": "逐時時間軸表",
        "concept_note": "這些模組是用來探索韌性的概念模擬層，不是硬體藍圖，也不取代實體工程驗證。",
        "concept_badge": "概念模擬 • 非硬體驗證版",
        "thermal_tabs": ["熱交換原理", "相變緩衝", "地下熱匯", "分散控制", "採收與緩衝"],
        "mode": "模式",
        "current": "目前",
        "thermal_concept": "熱概念",
        "reserve_days": "備援天數",
        "shortfall_hour": "缺口時點",
        "critical_failure_hour": "關鍵失效時點",
        "thermal_compare": "目前模式與熱概念比較",
    },
}

PAGE_QUESTIONS = {
    "English": {
        "Energy Mix": "What is the system actually running on, and how different is actual supply from installed capacity?",
        "Scenario Comparison": "How much better or worse is the selected scenario versus baseline and other scenarios?",
        "Stress Test": "Which subsystems fail first, and how badly does component degradation reduce resilience?",
        "AI Recommendation": "Why is the model concerned, which signal matters most, and what action should be prioritized first?",
        "Energy Security": "How much do import exposure, logistics, refill uncertainty, repair delay, and single-point risk increase disruption?",
        "Survival Timeline": "If supply is disrupted, how long can the system operate before shortfall and critical failure?",
        "Concept Lab": "If advanced thermal concepts are introduced, which resilience metrics improve and by how much?",
    },
    "繁體中文": {
        "能源組成": "系統實際靠什麼在運作？實際供應和裝機容量差多少？",
        "情境比較": "選定情境和基準情境相比，到底更好還是更差？",
        "壓力測試": "哪些子系統會先出問題？失效比例會把韌性拉低多少？",
        "AI 建議": "模型在擔心什麼？最重要的訊號是什麼？應該先做哪個動作？",
        "能源安全": "進口暴露、物流、補給不確定性、修復延遲與單點風險會把中斷拉高多少？",
        "生存時間軸": "如果供應中斷，系統在出現缺口與關鍵失效前還能撐多久？",
        "概念模組": "如果引入進階熱管理概念，哪些韌性指標會改善？改善多少？",
    },
}

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
        {"Metric": tr("demand"), "Baseline": round(baseline["demand"], 2), "Selected": round(selected["demand"], 2), "Delta": round(selected["demand"] - baseline["demand"], 2)},
        {"Metric": tr("renewable"), "Baseline": round(baseline["renewable_supply"], 2), "Selected": round(selected["renewable_supply"], 2), "Delta": round(selected["renewable_supply"] - baseline["renewable_supply"], 2)},
        {"Metric": tr("final"), "Baseline": round(baseline["final_supply"], 2), "Selected": round(selected["final_supply"], 2), "Delta": round(selected["final_supply"] - baseline["final_supply"], 2)},
        {"Metric": tr("shortfall"), "Baseline": round(baseline["shortfall"], 2), "Selected": round(selected["shortfall"], 2), "Delta": round(selected["shortfall"] - baseline["shortfall"], 2)},
    ])

def comparison_dataframe(inputs, failure_ratios, reserve_recovery_lag_days):
    rows = []
    for key in SCENARIOS.keys():
        r = compute_energy_supply(inputs, key, failure_ratios, reserve_recovery_lag_days)
        rows.append({"Scenario": key.replace("_", " ").title(), tr("demand"): r["demand"], tr("renewable"): r["renewable_supply"], tr("final"): r["final_supply"], tr("shortfall"): r["shortfall"], tr("grid"): r["grid_dependency"]})
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
    ax.barh(delta_df["Metric"], delta_df["Delta"])
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

with st.sidebar:
    ui_lang = st.selectbox("Language / 語言", list(I18N.keys()), index=list(I18N.keys()).index(st.session_state.get("ui_lang", "English")))
    st.session_state["ui_lang"] = ui_lang
    st.header(tr("controls"))
    country = st.selectbox(tr("country"), list(CITY_DATA.keys()))
    city = st.selectbox(tr("city"), list(CITY_DATA[country].keys()))
    city_profile = CITY_DATA[country][city]
    facility_type = st.selectbox(tr("facility_type"), list(FACILITY_PROFILES.keys()))
    facility_profile = FACILITY_PROFILES[facility_type]
    population = st.slider(tr("population"), 10000, 5000000, int(city_profile["population"]), step=10000)
    st.caption(f"{tr('population')}: {population:,}")

    st.divider()
    st.subheader(tr("capacity_inputs"))
    solar_capacity = st.slider("Solar Capacity", 0, 500, 120, 5)
    wind_capacity = st.slider("Wind Capacity", 0, 500, 80, 5)
    geothermal_capacity = st.slider("Geothermal Capacity", 0, 500, 60, 5)
    hydro_capacity = st.slider("Hydro Capacity", 0, 500, 70, 5)
    battery_capacity = st.slider("Battery Capacity", 0, 1000, 180, 10)

    st.divider()
    st.subheader(tr("weather_inputs"))
    temperature = st.slider("Temperature (°C)", -20, 50, 26, 1)
    wind_speed = st.slider("Wind Speed (m/s)", 0.0, 30.0, 4.2, 0.1)
    solar_radiation = st.slider("Solar Radiation (W/m²)", 0, 1200, 640, 10)
    precipitation = st.slider("Precipitation (mm)", 0, 300, 12, 1)
    humidity = st.slider("Humidity (%)", 0, 100, 73, 1)
    scenario_key = st.selectbox(tr("weather_scenario"), list(SCENARIOS.keys()))

    st.divider()
    st.subheader(tr("stress_inputs"))
    solar_failure_ratio = st.number_input("Solar Failure Ratio", 0.0, 1.0, 0.00, 0.05, format="%.2f")
    wind_failure_ratio = st.number_input("Wind Failure Ratio", 0.0, 1.0, 0.00, 0.05, format="%.2f")
    geothermal_failure_ratio = st.number_input("Geothermal Failure Ratio", 0.0, 1.0, 0.00, 0.05, format="%.2f")
    hydro_failure_ratio = st.number_input("Hydro Failure Ratio", 0.0, 1.0, 0.00, 0.05, format="%.2f")
    battery_failure_ratio = st.number_input("Battery Failure Ratio", 0.0, 1.0, 0.00, 0.05, format="%.2f")

    st.divider()
    st.subheader(tr("security_inputs"))
    energy_security_scenario = st.selectbox("Energy Security Scenario", list(ENERGY_SECURITY_SCENARIOS.keys()))
    import_dependency = st.number_input("Import Dependency", 0.0, 1.0, 0.70, 0.01, format="%.2f")
    strategic_reserve_days = st.number_input("Strategic Reserve Days", 0, 365, 20, 1)
    shipping_dependency = st.number_input("Shipping Dependency", 0.0, 1.0, 0.85, 0.01, format="%.2f")
    infrastructure_damage_ratio = st.number_input("Infrastructure Damage Ratio", 0.0, 1.0, 0.10, 0.01, format="%.2f")
    reserve_recovery_lag_days = st.number_input("Reserve Recovery Lag (days)", 0, 30, 3, 1)

    st.divider()
    st.subheader(tr("timeline_inputs"))
    simulation_hours = st.selectbox(tr("sim_hours"), [24, 72, 168], index=0)
    primary_supply_failure_ratio = st.number_input("Primary Supply Failure Ratio", 0.0, 1.0, 0.30, 0.01, format="%.2f")
    reserve_energy_per_day = st.number_input("Reserve Energy per Day", 20.0, 300.0, 120.0, 5.0, format="%.1f")
    survival_mode = st.selectbox(tr("survival_mode"), ["full_load", "critical_load_only"], index=0)

    st.divider()
    st.subheader(tr("thermal_inputs"))
    thermal_concept_enabled = st.toggle("Enable Thermal Concept Mode", value=True)
    fresh_air_temp_c = st.slider("Outside Air (°C)", -30.0, 20.0, -8.0, 0.5)
    exhaust_air_temp_c = st.slider("Indoor Exhaust Air (°C)", 10.0, 35.0, 23.0, 0.5)
    recovery_efficiency = st.slider("Thermal Recovery Efficiency", 0.0, 1.0, 0.72, 0.01)
    thermal_animation_speed = st.slider(tr("animation_speed"), 0.4, 2.5, 1.0, 0.1)

failure_ratios = {
    "solar": solar_failure_ratio,
    "wind": wind_failure_ratio,
    "geothermal": geothermal_failure_ratio,
    "hydro": hydro_failure_ratio,
    "battery": battery_failure_ratio,
}
inputs = {
    "country_key": country, "city_key": city, "lat": city_profile["lat"], "lon": city_profile["lon"],
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

st.title(tr("title"))
st.caption(tr("caption"))
st.markdown(f'<div class="hero"><h3>{tr("hero_title")}</h3><p>{tr("hero_body")}</p></div>', unsafe_allow_html=True)

layer_cols = st.columns(3)
for col, label, desc in zip(layer_cols, [tr("core"), tr("decision"), tr("concept")], [tr("core_desc"), tr("decision_desc"), tr("concept_desc")]):
    with col:
        st.markdown(f'<div class="layer-box"><div class="card-label">{label}</div><div class="card-value" style="font-size:0.98rem;">{desc}</div></div>', unsafe_allow_html=True)

top_left, top_right = st.columns([1.02, 1.08])
with top_left:
    st.subheader(tr("country_logic") + f": {country}")
    st.write(COUNTRY_NOTES.get(country, "Regional energy model loaded."))
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
        mini_card(tr("country"), country)
        mini_card(tr("city"), city)
        mini_card(tr("population"), f"{population:,}")
        mini_card(tr("weather_scenario"), scenario_key.replace("_", " ").title())
    with c2:
        mini_card("Energy Security", energy_security_scenario.replace("_", " ").title())
        mini_card("Facility Tolerance", f"{facility_profile['failure_tolerance_hours']} h")
        mini_card("Import Dependency", f"{import_dependency * 100:.0f}%")
        mini_card("Timeline Horizon", f"{simulation_hours} h")

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

summary_txt = json.dumps({"summary": "use export"}, ensure_ascii=False)
buf_scen = StringIO(); comparison_dataframe(inputs, failure_ratios, reserve_recovery_lag_days).to_csv(buf_scen, index=False)
buf_reason = StringIO(); pd.DataFrame(recommendation_reason_chain(results, energy_security_scenario, timeline_results, facility_type, facility_profile)).to_csv(buf_reason, index=False)
audit_json = json.dumps({"country": country, "city": city, "facility_type": facility_type}, indent=2, ensure_ascii=False)

download_cols = st.columns(4)
with download_cols[0]:
    st.download_button(tr("download_scenario"), buf_scen.getvalue(), file_name="taivas_scenarios.csv", mime="text/csv")
with download_cols[1]:
    st.download_button(tr("download_reason"), buf_reason.getvalue(), file_name="taivas_reason_chain.csv", mime="text/csv")
with download_cols[2]:
    st.download_button(tr("download_summary"), summary_txt, file_name="taivas_executive_summary.txt", mime="text/plain")
with download_cols[3]:
    st.download_button(tr("download_audit"), audit_json, file_name="taivas_audit_trail.json", mime="application/json")

tabs = st.tabs(tr("tabs"))
mix_tab, compare_tab, stress_tab, ai_tab, sec_tab, timeline_tab, concept_tab = tabs

with mix_tab:
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
        "Source": list(results["actual_mix_mw"].keys()),
        "Installed Capacity (MW)": [results["installed_mix_mw"][k] for k in results["actual_mix_mw"]],
        "Actual Supply (MW)": [results["actual_mix_mw"][k] for k in results["actual_mix_mw"]],
        "Installed Mix (%)": [round(results["installed_mix_pct"][k], 2) for k in results["actual_mix_mw"]],
        "Actual Mix (%)": [round(results["actual_mix_pct"][k], 2) for k in results["actual_mix_mw"]],
        "Capacity Factor (%)": [results["capacity_factors"][k] for k in results["actual_mix_mw"]],
    })
    st.subheader(tr("energy_table"))
    st.dataframe(mix_table, use_container_width=True, hide_index=True)
    st.subheader(tr("capacity_factors"))
    render_capacity_factor_chart(results["capacity_factors"])
    st.caption(f"{tr('dominant')}: {results['dominant_source']}")

with compare_tab:
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
        st.bar_chart(scenario_df.set_index("Scenario")[[tr("shortfall"), tr("grid")]])
    st.subheader(tr("critical_breakdown"))
    render_critical_load_chart(critical_load_df)
    st.dataframe(critical_load_df, use_container_width=True, hide_index=True)

with stress_tab:
    page_question(tr("tabs")[2])
    st.markdown('<div class="note">Multi-failure stress testing and subsystem degradation view.</div>', unsafe_allow_html=True)
    stress_df = pd.DataFrame({"Subsystem": list(failure_ratios.keys()), "Failure Ratio": list(failure_ratios.values()), "Availability (%)": [round((1 - v) * 100, 1) for v in failure_ratios.values()]})
    st.dataframe(stress_df, use_container_width=True, hide_index=True)
    st.bar_chart(stress_df.set_index("Subsystem")[["Availability (%)"]])

with ai_tab:
    page_question(tr("tabs")[3])
    st.subheader(tr("quick_reco"))
    for idx, line in enumerate(recommendation_lines(results, energy_security_scenario), 1):
        st.write(f"{idx}. {line}")
    reason_df = pd.DataFrame(recommendation_reason_chain(results, energy_security_scenario, timeline_results, facility_type, facility_profile))
    st.subheader(tr("reason_chain"))
    st.dataframe(reason_df, use_container_width=True, hide_index=True)

with sec_tab:
    page_question(tr("tabs")[4])
    row1 = st.columns(4)
    row1[0].metric("Import Disruption", f"{results['import_disruption_score']}%")
    row1[1].metric(tr("reserve_days"), f"{results['reserve_days_remaining']} days")
    row1[2].metric("Fuel Cost Stress", f"{results['fuel_cost_stress']}%")
    row1[3].metric("Extended Disruption", f"{results['extended_disruption_score']}%")

with timeline_tab:
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

with concept_tab:
    page_question(tr("tabs")[6])
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
