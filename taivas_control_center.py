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
        "Turku": {"lat": 60.4518, "lon": 22.2666, "population": 196000, "country_model": "Winter Reliability Model"},
    },
    "Sweden": {
        "Stockholm": {"lat": 59.3293, "lon": 18.0686, "population": 975000, "country_model": "Nordic Urban Resilience Model"},
        "Gothenburg": {"lat": 57.7089, "lon": 11.9746, "population": 587000, "country_model": "Nordic Urban Resilience Model"},
        "Malmo": {"lat": 55.6050, "lon": 13.0038, "population": 362000, "country_model": "Nordic Urban Resilience Model"},
    },
    "Norway": {
        "Oslo": {"lat": 59.9139, "lon": 10.7522, "population": 717000, "country_model": "Nordic Hydro Resilience Model"},
        "Bergen": {"lat": 60.3913, "lon": 5.3221, "population": 289000, "country_model": "Nordic Hydro Resilience Model"},
        "Trondheim": {"lat": 63.4305, "lon": 10.3951, "population": 214000, "country_model": "Nordic Hydro Resilience Model"},
    },
    "Denmark": {
        "Copenhagen": {"lat": 55.6761, "lon": 12.5683, "population": 654000, "country_model": "Coastal Flexibility Model"},
        "Aarhus": {"lat": 56.1629, "lon": 10.2039, "population": 285000, "country_model": "Coastal Flexibility Model"},
        "Odense": {"lat": 55.4038, "lon": 10.4024, "population": 180000, "country_model": "Coastal Flexibility Model"},
    },
    "Iceland": {
        "Reykjavik": {"lat": 64.1466, "lon": -21.9426, "population": 139000, "country_model": "Geothermal Continuity Model"},
        "Akureyri": {"lat": 65.6885, "lon": -18.1262, "population": 19000, "country_model": "Geothermal Continuity Model"},
        "Keflavik": {"lat": 64.0049, "lon": -22.5624, "population": 16000, "country_model": "Geothermal Continuity Model"},
    },
    "Germany": {
        "Berlin": {"lat": 52.5200, "lon": 13.4050, "population": 3570000, "country_model": "Industrial Transition Model"},
        "Hamburg": {"lat": 53.5511, "lon": 9.9937, "population": 1910000, "country_model": "Industrial Transition Model"},
        "Munich": {"lat": 48.1351, "lon": 11.5820, "population": 1510000, "country_model": "Industrial Transition Model"},
        "Frankfurt": {"lat": 50.1109, "lon": 8.6821, "population": 776000, "country_model": "Industrial Transition Model"},
    },
    "Switzerland": {
        "Zurich": {"lat": 47.3769, "lon": 8.5417, "population": 435000, "country_model": "Alpine Stability Model"},
        "Geneva": {"lat": 46.2044, "lon": 6.1432, "population": 203000, "country_model": "Alpine Stability Model"},
        "Bern": {"lat": 46.9480, "lon": 7.4474, "population": 134000, "country_model": "Alpine Stability Model"},
        "Basel": {"lat": 47.5596, "lon": 7.5886, "population": 177000, "country_model": "Alpine Stability Model"},
    },
    "Netherlands": {
        "Amsterdam": {"lat": 52.3676, "lon": 4.9041, "population": 922000, "country_model": "Delta Resilience Model"},
        "Rotterdam": {"lat": 51.9244, "lon": 4.4777, "population": 671000, "country_model": "Delta Resilience Model"},
        "The Hague": {"lat": 52.0705, "lon": 4.3007, "population": 565000, "country_model": "Delta Resilience Model"},
    },
    "Belgium": {
        "Brussels": {"lat": 50.8503, "lon": 4.3517, "population": 185000, "country_model": "Western Europe Stability Model"},
        "Antwerp": {"lat": 51.2194, "lon": 4.4025, "population": 530000, "country_model": "Western Europe Stability Model"},
        "Ghent": {"lat": 51.0543, "lon": 3.7174, "population": 265000, "country_model": "Western Europe Stability Model"},
    },
    "Austria": {
        "Vienna": {"lat": 48.2082, "lon": 16.3738, "population": 2000000, "country_model": "Central Europe Reliability Model"},
        "Graz": {"lat": 47.0707, "lon": 15.4395, "population": 291000, "country_model": "Central Europe Reliability Model"},
        "Linz": {"lat": 48.3069, "lon": 14.2858, "population": 206000, "country_model": "Central Europe Reliability Model"},
    },
    "France": {
        "Paris": {"lat": 48.8566, "lon": 2.3522, "population": 2100000, "country_model": "Western Europe Flex Model"},
        "Lyon": {"lat": 45.7640, "lon": 4.8357, "population": 522000, "country_model": "Western Europe Flex Model"},
        "Marseille": {"lat": 43.2965, "lon": 5.3698, "population": 877000, "country_model": "Western Europe Flex Model"},
    },
    "United Kingdom": {
        "London": {"lat": 51.5072, "lon": -0.1276, "population": 8980000, "country_model": "Island Urban Continuity Model"},
        "Manchester": {"lat": 53.4808, "lon": -2.2426, "population": 568000, "country_model": "Island Urban Continuity Model"},
        "Edinburgh": {"lat": 55.9533, "lon": -3.1883, "population": 506000, "country_model": "Island Urban Continuity Model"},
    },
    "Ireland": {
        "Dublin": {"lat": 53.3498, "lon": -6.2603, "population": 592000, "country_model": "Atlantic Resilience Model"},
        "Cork": {"lat": 51.8985, "lon": -8.4756, "population": 224000, "country_model": "Atlantic Resilience Model"},
        "Galway": {"lat": 53.2707, "lon": -9.0568, "population": 85000, "country_model": "Atlantic Resilience Model"},
    },
    "Spain": {
        "Madrid": {"lat": 40.4168, "lon": -3.7038, "population": 3300000, "country_model": "Southern Heat Stress Model"},
        "Barcelona": {"lat": 41.3851, "lon": 2.1734, "population": 1660000, "country_model": "Southern Heat Stress Model"},
        "Valencia": {"lat": 39.4699, "lon": -0.3763, "population": 792000, "country_model": "Southern Heat Stress Model"},
    },
    "Italy": {
        "Rome": {"lat": 41.9028, "lon": 12.4964, "population": 2740000, "country_model": "Mediterranean Continuity Model"},
        "Milan": {"lat": 45.4642, "lon": 9.1900, "population": 1370000, "country_model": "Mediterranean Continuity Model"},
        "Turin": {"lat": 45.0703, "lon": 7.6869, "population": 848000, "country_model": "Mediterranean Continuity Model"},
    },
    "Portugal": {
        "Lisbon": {"lat": 38.7223, "lon": -9.1393, "population": 545000, "country_model": "Atlantic Heat Buffer Model"},
        "Porto": {"lat": 41.1579, "lon": -8.6291, "population": 231000, "country_model": "Atlantic Heat Buffer Model"},
        "Braga": {"lat": 41.5454, "lon": -8.4265, "population": 193000, "country_model": "Atlantic Heat Buffer Model"},
    },
    "Poland": {
        "Warsaw": {"lat": 52.2297, "lon": 21.0122, "population": 1860000, "country_model": "Eastern Europe Recovery Model"},
        "Krakow": {"lat": 50.0647, "lon": 19.9450, "population": 804000, "country_model": "Eastern Europe Recovery Model"},
        "Wroclaw": {"lat": 51.1079, "lon": 17.0385, "population": 674000, "country_model": "Eastern Europe Recovery Model"},
    },
    "Czech Republic": {
        "Prague": {"lat": 50.0755, "lon": 14.4378, "population": 1380000, "country_model": "Central Europe Reliability Model"},
        "Brno": {"lat": 49.1951, "lon": 16.6068, "population": 398000, "country_model": "Central Europe Reliability Model"},
        "Ostrava": {"lat": 49.8209, "lon": 18.2625, "population": 285000, "country_model": "Central Europe Reliability Model"},
    },
    "USA": {
        "Seattle": {"lat": 47.6062, "lon": -122.3321, "population": 749000, "country_model": "Northwest Resilience Model"},
        "Boston": {"lat": 42.3601, "lon": -71.0589, "population": 654000, "country_model": "Northwest Resilience Model"},
        "New York": {"lat": 40.7128, "lon": -74.0060, "population": 8337000, "country_model": "Northwest Resilience Model"},
    },
}


COUNTRY_NOTES = {
    "Taiwan": "Cooling-heavy island model with strong storage need.",
    "Finland": "Cold-climate resilience model with winter reliability focus.",
    "Sweden": "Nordic urban resilience model with district-scale cold and heat balancing.",
    "Norway": "Hydro-friendly Nordic model with strong resilience potential.",
    "Denmark": "Coastal flexibility model with wind and import balancing sensitivity.",
    "Iceland": "Geothermal continuity model with strong baseload resilience and storm exposure.",
    "Germany": "Industrial transition model with grid balancing importance.",
    "Switzerland": "High-stability alpine model with balanced reserve planning.",
    "Netherlands": "Delta resilience model with logistics and flood-aware infrastructure planning.",
    "Belgium": "Western Europe stability model with dense urban continuity needs.",
    "Austria": "Central Europe reliability model with alpine and urban mixed loads.",
    "France": "Western Europe flex model with large urban loads and diverse generation mix.",
    "United Kingdom": "Island urban continuity model with import and coastal exposure considerations.",
    "Ireland": "Atlantic resilience model with maritime weather variability.",
    "Spain": "Southern heat stress model with cooling-heavy seasonal pressure.",
    "Italy": "Mediterranean continuity model with urban heat and critical facility load complexity.",
    "Portugal": "Atlantic heat buffer model with coastal weather variation.",
    "Poland": "Eastern Europe recovery model with winter load and grid transition pressure.",
    "Czech Republic": "Central Europe reliability model with industrial and urban load balancing.",
    "USA": "Northwest resilience model for cross-market comparison and export testing.",
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
        "solar_capacity": "Solar Capacity",
        "wind_capacity": "Wind Capacity",
        "geothermal_capacity": "Geothermal Capacity",
        "hydro_capacity": "Hydro Capacity",
        "battery_capacity": "Battery Capacity",
        "temperature": "Temperature",
        "wind_speed": "Wind Speed",
        "solar_radiation": "Solar Radiation",
        "precipitation": "Precipitation",
        "humidity": "Humidity",
        "solar_failure_ratio": "Solar Failure Ratio",
        "wind_failure_ratio": "Wind Failure Ratio",
        "geothermal_failure_ratio": "Geothermal Failure Ratio",
        "hydro_failure_ratio": "Hydro Failure Ratio",
        "battery_failure_ratio": "Battery Failure Ratio",
        "energy_security_scenario": "Energy Security Scenario",
        "import_dependency": "Import Dependency",
        "strategic_reserve_days": "Strategic Reserve Days",
        "shipping_dependency": "Shipping Dependency",
        "infrastructure_damage_ratio": "Infrastructure Damage Ratio",
        "reserve_recovery_lag_days": "Reserve Recovery Lag (days)",
        "primary_supply_failure_ratio": "Primary Supply Failure Ratio",
        "reserve_energy_per_day": "Reserve Energy per Day",
        "outside_air": "Outside Air",
        "indoor_exhaust_air": "Indoor Exhaust Air",
        "thermal_recovery_efficiency": "Thermal Recovery Efficiency",
        "source": "Source",
        "installed_capacity_mw": "Installed Capacity (MW)",
        "actual_supply_mw": "Actual Supply (MW)",
        "installed_mix_pct": "Installed Mix (%)",
        "actual_mix_pct": "Actual Mix (%)",
        "capacity_factor_pct": "Capacity Factor (%)",
        "subsystem": "Subsystem",
        "failure_ratio": "Failure Ratio",
        "availability_pct": "Availability (%)",
        "scenario": "Scenario",
        "metric": "Metric",
        "baseline": "Baseline",
        "selected": "Selected",
        "delta": "Delta"
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
        "solar_capacity": "太陽能容量",
        "wind_capacity": "風能容量",
        "geothermal_capacity": "地熱容量",
        "hydro_capacity": "水力容量",
        "battery_capacity": "電池容量",
        "temperature": "溫度",
        "wind_speed": "風速",
        "solar_radiation": "太陽輻射",
        "precipitation": "降雨量",
        "humidity": "濕度",
        "solar_failure_ratio": "太陽能失效比例",
        "wind_failure_ratio": "風能失效比例",
        "geothermal_failure_ratio": "地熱失效比例",
        "hydro_failure_ratio": "水力失效比例",
        "battery_failure_ratio": "電池失效比例",
        "energy_security_scenario": "能源安全情境",
        "import_dependency": "進口依賴",
        "strategic_reserve_days": "戰略備援天數",
        "shipping_dependency": "航運依賴",
        "infrastructure_damage_ratio": "基礎設施損害比例",
        "reserve_recovery_lag_days": "備援恢復延遲（天）",
        "primary_supply_failure_ratio": "主要供應失效比例",
        "reserve_energy_per_day": "每日備援能源",
        "outside_air": "外部空氣",
        "indoor_exhaust_air": "室內排氣",
        "thermal_recovery_efficiency": "熱回收效率",
        "source": "來源",
        "installed_capacity_mw": "裝機容量 (MW)",
        "actual_supply_mw": "實際供應 (MW)",
        "installed_mix_pct": "裝機占比 (%)",
        "actual_mix_pct": "實際占比 (%)",
        "capacity_factor_pct": "容量因子 (%)",
        "subsystem": "子系統",
        "failure_ratio": "失效比例",
        "availability_pct": "可用率 (%)",
        "scenario": "情境",
        "metric": "指標",
        "baseline": "基準",
        "selected": "選定值",
        "delta": "差值"
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


def safe_read_csv(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        return pd.read_csv(uploaded_file)
    except Exception as e:
        st.sidebar.warning(f"CSV read failed: {e}")
        return None


def build_uploaded_profiles(df: pd.DataFrame):
    if df is None or df.empty:
        return {}
    rows = {}
    required = [
        "country_key", "city_key", "lat", "lon", "population",
        "temperature", "wind_speed", "solar_radiation", "precipitation", "humidity",
        "solar_capacity", "wind_capacity", "geothermal_capacity", "hydro_capacity", "battery_capacity",
    ]
    for idx, raw in df.iterrows():
        row = {k: raw[k] if k in df.columns else None for k in required}
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
        }
    return rows


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
        },
    }
    for lang, mapping in extras.items():
        I18N.setdefault(lang, {}).update({k: v for k, v in mapping.items() if k not in I18N.get(lang, {})})


extend_i18n()

with st.sidebar:
    ui_lang = st.selectbox("Language / 語言", list(I18N.keys()), index=list(I18N.keys()).index(st.session_state.get("ui_lang", "English")))
    st.session_state["ui_lang"] = ui_lang
    st.header(tr("controls"))

    uploaded_baseline_file = st.file_uploader(tr("uploaded_data"), type=["csv"], key="uploaded_baseline_csv")
    uploaded_df = safe_read_csv(uploaded_baseline_file)
    uploaded_profiles = build_uploaded_profiles(uploaded_df)
    use_uploaded = False
    uploaded_profile = None
    if uploaded_profiles:
        use_uploaded = st.toggle(tr("use_uploaded"), value=True)
        uploaded_row_key = st.selectbox(tr("uploaded_row"), list(uploaded_profiles.keys()))
        uploaded_profile = uploaded_profiles.get(uploaded_row_key)
        st.caption(f"{tr('csv_mode')}: {uploaded_row_key}")

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
audit_json = json.dumps({"country": active_country, "city": active_city, "facility_type": facility_type}, indent=2, ensure_ascii=False)

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
        tr("source"): list(results["actual_mix_mw"].keys()),
        tr("installed_capacity_mw"): [results["installed_mix_mw"][k] for k in results["actual_mix_mw"]],
        tr("actual_supply_mw"): [results["actual_mix_mw"][k] for k in results["actual_mix_mw"]],
        tr("installed_mix_pct"): [round(results["installed_mix_pct"][k], 2) for k in results["actual_mix_mw"]],
        tr("actual_mix_pct"): [round(results["actual_mix_pct"][k], 2) for k in results["actual_mix_mw"]],
        tr("capacity_factor_pct"): [results["capacity_factors"][k] for k in results["actual_mix_mw"]],
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
        scenario_index_col = tr("scenario") if tr("scenario") in scenario_df.columns else "Scenario"
        shortfall_col = tr("shortfall") if tr("shortfall") in scenario_df.columns else "Shortfall"
        grid_col = tr("grid") if tr("grid") in scenario_df.columns else "Grid Dependency"
        st.bar_chart(scenario_df.set_index(scenario_index_col)[[shortfall_col, grid_col]])
    st.subheader(tr("critical_breakdown"))
    render_critical_load_chart(critical_load_df)
    st.dataframe(critical_load_df, use_container_width=True, hide_index=True)

with stress_tab:
    page_question(tr("tabs")[2])
    st.markdown('<div class="note">Multi-failure stress testing and subsystem degradation view.</div>', unsafe_allow_html=True)
    stress_df = pd.DataFrame({tr("subsystem"): list(failure_ratios.keys()), tr("failure_ratio"): list(failure_ratios.values()), tr("availability_pct"): [round((1 - v) * 100, 1) for v in failure_ratios.values()]})
    st.dataframe(stress_df, use_container_width=True, hide_index=True)
    st.bar_chart(stress_df.set_index(tr("subsystem"))[[tr("availability_pct")]])

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
