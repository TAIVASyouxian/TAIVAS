from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="TAIVAS Energy Control Center",
    page_icon="⚡",
    layout="wide",
)

# -----------------------------
# Constants and localized text
# -----------------------------
SCENARIOS = ["normal", "heat_wave", "storm", "cold_wave", "blizzard", "typhoon"]

TEXT = {
    "English": {
        "title": "TAIVAS Energy Control Center",
        "subtitle": "AI-driven energy resilience and recovery dashboard",
        "overview_title": "System Overview",
        "overview_body": "TAIVAS combines country logic, city profiles, weather simulation, and energy resilience controls into one decision-support dashboard.",
        "language": "Language / 語言",
        "country": "Country",
        "city": "City",
        "scenario": "Scenario",
        "weather": "Weather Inputs",
        "capacity": "Energy Capacity Inputs",
        "population": "Population",
        "temperature": "Temperature (°C)",
        "wind_speed": "Wind Speed (m/s)",
        "solar_rad": "Solar Radiation (W/m²)",
        "precipitation": "Precipitation (mm)",
        "humidity": "Humidity (%)",
        "solar": "Solar Capacity (MW)",
        "wind": "Wind Capacity (MW)",
        "geo": "Geothermal Capacity (MW)",
        "hydro": "Hydropower Capacity (MW)",
        "battery": "Battery Capacity (MWh)",
        "city_profile": "City Profile",
        "country_logic": "Country Logic",
        "weather_status": "Weather Status",
        "simulation_summary": "Simulation Summary",
        "energy_mix": "Energy Mix",
        "comparison": "Scenario Comparison Table",
        "recommendation": "AI Recommendation Panel",
        "governance": "Risk & Governance Reminder",
        "audit": "Audit Trail (Current Session)",
        "show_debug": "Show developer debug panel",
        "download_csv": "Download audit CSV",
        "decision_support": "This product is decision-support software, not an unconditional guarantee.",
        "deviation": "Changing assumptions can change model outcomes.",
        "stable": "System is relatively stable under the selected scenario.",
        "lat": "Latitude",
        "lon": "Longitude",
        "country_model": "Country Model",
        "metrics": {
            "demand": "Demand",
            "renewable_supply": "Renewable Supply",
            "final_supply": "Final Supply",
            "shortfall": "Shortfall",
            "battery_levels": "Battery Levels",
            "renewable_ratio": "Renewable Ratio",
            "system_efficiency": "System Efficiency",
            "grid_dependency": "Grid Dependency",
        },
    },
    "繁體中文": {
        "title": "TAIVAS 能源控制中心",
        "subtitle": "AI 驅動的能源韌性與復原儀表板",
        "overview_title": "系統總覽",
        "overview_body": "TAIVAS 將國家邏輯、城市檔案、天氣模擬與能源韌性控制整合在同一個決策輔助儀表板中。",
        "language": "Language / 語言",
        "country": "國家",
        "city": "城市",
        "scenario": "情境",
        "weather": "氣候輸入",
        "capacity": "能源容量輸入",
        "population": "人口",
        "temperature": "溫度 (°C)",
        "wind_speed": "風速 (m/s)",
        "solar_rad": "太陽輻射 (W/m²)",
        "precipitation": "降水量 (mm)",
        "humidity": "濕度 (%)",
        "solar": "太陽能容量 (MW)",
        "wind": "風力容量 (MW)",
        "geo": "地熱容量 (MW)",
        "hydro": "水力容量 (MW)",
        "battery": "電池容量 (MWh)",
        "city_profile": "城市檔案",
        "country_logic": "國家邏輯",
        "weather_status": "天氣狀態",
        "simulation_summary": "模擬摘要",
        "energy_mix": "能源組成",
        "comparison": "情境比較表",
        "recommendation": "AI 建議面板",
        "governance": "風險與治理提醒",
        "audit": "稽核軌跡（本次工作階段）",
        "show_debug": "顯示開發除錯面板",
        "download_csv": "下載稽核 CSV",
        "decision_support": "本產品屬於決策輔助工具，並非無條件保證。",
        "deviation": "調整假設條件後，模型結果也可能改變。",
        "stable": "在目前情境下，系統整體相對穩定。",
        "lat": "緯度",
        "lon": "經度",
        "country_model": "國家模型",
        "metrics": {
            "demand": "需求",
            "renewable_supply": "再生能源供給",
            "final_supply": "最終供給",
            "shortfall": "缺口",
            "battery_levels": "電池水位",
            "renewable_ratio": "再生能源占比",
            "system_efficiency": "系統效率",
            "grid_dependency": "電網依賴度",
        },
    },
}

COUNTRY_CITY_DATA: Dict[str, Dict[str, Dict[str, float | str]]] = {
    "[TW] Taiwan": {
        "[TW] Taipei, Taiwan": {
            "lat": 25.0330,
            "lon": 121.5654,
            "temperature": 26.0,
            "wind_speed": 4.2,
            "solar_radiation": 640.0,
            "precipitation": 12.0,
            "humidity": 73.0,
            "population": 2500000,
            "country_model": "taiwan",
            "climate_note": "Cooling-heavy island model with strong storage need.",
            "weather_tag": "☀️ Sunny",
        },
        "[TW] Taichung, Taiwan": {
            "lat": 24.1477,
            "lon": 120.6736,
            "temperature": 27.0,
            "wind_speed": 3.8,
            "solar_radiation": 680.0,
            "precipitation": 8.0,
            "humidity": 69.0,
            "population": 2850000,
            "country_model": "taiwan",
            "climate_note": "Balanced urban-industrial load with strong solar upside.",
            "weather_tag": "🌤️ Partly Sunny",
        },
        "[TW] Tainan, Taiwan": {
            "lat": 22.9999,
            "lon": 120.2270,
            "temperature": 28.0,
            "wind_speed": 4.0,
            "solar_radiation": 710.0,
            "precipitation": 6.0,
            "humidity": 68.0,
            "population": 1850000,
            "country_model": "taiwan",
            "climate_note": "Solar-favorable southern profile with heat sensitivity.",
            "weather_tag": "☀️ Sunny",
        },
        "[TW] Kaohsiung, Taiwan": {
            "lat": 22.6273,
            "lon": 120.3014,
            "temperature": 29.0,
            "wind_speed": 4.8,
            "solar_radiation": 730.0,
            "precipitation": 5.0,
            "humidity": 67.0,
            "population": 2730000,
            "country_model": "taiwan",
            "climate_note": "High solar output with industrial demand pressure.",
            "weather_tag": "☀️ Sunny",
        },
    },
    "[FI] Finland": {
        "[FI] Helsinki, Finland": {
            "lat": 60.1699,
            "lon": 24.9384,
            "temperature": 12.0,
            "wind_speed": 6.8,
            "solar_radiation": 420.0,
            "precipitation": 18.0,
            "humidity": 71.0,
            "population": 665000,
            "country_model": "finland",
            "climate_note": "Cold-resilient urban grid with strong winter heating swings.",
            "weather_tag": "🌥️ Cool",
        },
        "[FI] Rovaniemi, Finland": {
            "lat": 66.5039,
            "lon": 25.7294,
            "temperature": 5.0,
            "wind_speed": 6.0,
            "solar_radiation": 280.0,
            "precipitation": 15.0,
            "humidity": 78.0,
            "population": 65000,
            "country_model": "finland",
            "climate_note": "Extreme winter sensitivity with storage importance.",
            "weather_tag": "❄️ Arctic",
        },
        "[FI] Tampere, Finland": {
            "lat": 61.4978,
            "lon": 23.7610,
            "temperature": 11.0,
            "wind_speed": 5.9,
            "solar_radiation": 390.0,
            "precipitation": 17.0,
            "humidity": 72.0,
            "population": 255000,
            "country_model": "finland",
            "climate_note": "Manufacturing-linked city load with steady hydro support.",
            "weather_tag": "🌥️ Mild",
        },
    },
    "[NO] Norway": {
        "[NO] Oslo, Norway": {
            "lat": 59.9139,
            "lon": 10.7522,
            "temperature": 10.0,
            "wind_speed": 5.5,
            "solar_radiation": 400.0,
            "precipitation": 22.0,
            "humidity": 74.0,
            "population": 710000,
            "country_model": "norway",
            "climate_note": "Hydro-strong system with winter reliability focus.",
            "weather_tag": "🌦️ Mixed",
        },
        "[NO] Bergen, Norway": {
            "lat": 60.3913,
            "lon": 5.3221,
            "temperature": 9.0,
            "wind_speed": 6.8,
            "solar_radiation": 340.0,
            "precipitation": 40.0,
            "humidity": 83.0,
            "population": 290000,
            "country_model": "norway",
            "climate_note": "Rain-heavy coastal system with strong hydro response.",
            "weather_tag": "🌧️ Rainy",
        },
    },
    "[CH] Switzerland": {
        "[CH] Zurich, Switzerland": {
            "lat": 47.3769,
            "lon": 8.5417,
            "temperature": 14.0,
            "wind_speed": 4.5,
            "solar_radiation": 500.0,
            "precipitation": 16.0,
            "humidity": 66.0,
            "population": 434000,
            "country_model": "switzerland",
            "climate_note": "High-value resilient urban core with balanced grid integration.",
            "weather_tag": "🌤️ Mild",
        },
        "[CH] Geneva, Switzerland": {
            "lat": 46.2044,
            "lon": 6.1432,
            "temperature": 15.0,
            "wind_speed": 4.1,
            "solar_radiation": 520.0,
            "precipitation": 14.0,
            "humidity": 64.0,
            "population": 205000,
            "country_model": "switzerland",
            "climate_note": "Balanced city profile with stable hydro and storage opportunity.",
            "weather_tag": "🌤️ Clear",
        },
    },
}

COUNTRY_DEFAULT_CAPACITY = {
    "[TW] Taiwan": {"solar": 120.0, "wind": 80.0, "geo": 60.0, "hydro": 70.0, "battery": 180.0},
    "[FI] Finland": {"solar": 70.0, "wind": 120.0, "geo": 50.0, "hydro": 110.0, "battery": 220.0},
    "[NO] Norway": {"solar": 50.0, "wind": 110.0, "geo": 40.0, "hydro": 180.0, "battery": 200.0},
    "[CH] Switzerland": {"solar": 85.0, "wind": 60.0, "geo": 35.0, "hydro": 160.0, "battery": 170.0},
}

SCENARIO_MULTIPLIERS = {
    "normal": {"demand": 1.00, "solar": 1.00, "wind": 1.00, "hydro": 1.00, "battery": 1.00, "grid_risk": 1.00},
    "heat_wave": {"demand": 1.18, "solar": 1.10, "wind": 0.92, "hydro": 0.96, "battery": 0.95, "grid_risk": 1.08},
    "storm": {"demand": 1.06, "solar": 0.62, "wind": 1.15, "hydro": 1.05, "battery": 0.92, "grid_risk": 1.15},
    "cold_wave": {"demand": 1.16, "solar": 0.78, "wind": 1.06, "hydro": 1.03, "battery": 0.90, "grid_risk": 1.10},
    "blizzard": {"demand": 1.25, "solar": 0.42, "wind": 0.84, "hydro": 0.94, "battery": 0.82, "grid_risk": 1.22},
    "typhoon": {"demand": 1.12, "solar": 0.28, "wind": 0.70, "hydro": 1.12, "battery": 0.76, "grid_risk": 1.30},
}

COUNTRY_LOAD_FACTORS = {
    "taiwan": 1.10,
    "finland": 1.02,
    "norway": 0.98,
    "switzerland": 1.00,
}


@dataclass
class SimulationResult:
    demand: float
    renewable_supply: float
    final_supply: float
    battery_levels: float
    shortfall: float
    renewable_ratio: float
    system_efficiency: float
    grid_dependency: float
    solar_supply: float
    wind_supply: float
    geothermal_supply: float
    hydro_supply: float


# -----------------------------
# Utility functions
# -----------------------------
def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(float(value), max_value))


def safe_ratio(numerator: float, denominator: float) -> float:
    if abs(denominator) < 1e-9:
        return 0.0
    return numerator / denominator


def get_country_logic_text(country: str) -> str:
    mapping = {
        "[TW] Taiwan": "Cooling-heavy island model with strong storage need.",
        "[FI] Finland": "Cold-climate resilience model with winter demand sensitivity.",
        "[NO] Norway": "Hydro-dominant resilience model with strong backup stability.",
        "[CH] Switzerland": "Balanced alpine model with reliability and storage discipline.",
    }
    return mapping.get(country, "Balanced resilience model.")


def compute_weather_factors(temperature: float, wind_speed: float, solar_radiation: float, precipitation: float, humidity: float) -> Dict[str, float]:
    solar_factor = clamp(solar_radiation / 700.0, 0.20, 1.25)
    wind_factor = clamp(wind_speed / 6.0, 0.30, 1.35)
    hydro_factor = clamp(0.75 + precipitation / 60.0, 0.55, 1.25)
    thermal_stress = 1.0 + max(0.0, temperature - 24.0) * 0.015 + max(0.0, humidity - 65.0) * 0.003
    cold_stress = 1.0 + max(0.0, 10.0 - temperature) * 0.02
    demand_weather_factor = max(thermal_stress, cold_stress)
    return {
        "solar": solar_factor,
        "wind": wind_factor,
        "hydro": hydro_factor,
        "demand": clamp(demand_weather_factor, 0.90, 1.35),
    }


def simulate(inputs: Dict[str, float | str], scenario: str) -> SimulationResult:
    scenario = scenario if scenario in SCENARIO_MULTIPLIERS else "normal"
    sm = SCENARIO_MULTIPLIERS[scenario]

    country_model = str(inputs["country_model"])
    population = clamp(float(inputs["population"]), 1000, 100_000_000)
    temperature = clamp(float(inputs["temperature"]), -40, 55)
    wind_speed = clamp(float(inputs["wind_speed"]), 0, 50)
    solar_radiation = clamp(float(inputs["solar_radiation"]), 0, 1300)
    precipitation = clamp(float(inputs["precipitation"]), 0, 500)
    humidity = clamp(float(inputs["humidity"]), 0, 100)

    solar_capacity = clamp(float(inputs["solar_capacity"]), 0, 2000)
    wind_capacity = clamp(float(inputs["wind_capacity"]), 0, 2000)
    geothermal_capacity = clamp(float(inputs["geothermal_capacity"]), 0, 2000)
    hydro_capacity = clamp(float(inputs["hydro_capacity"]), 0, 2000)
    battery_capacity = clamp(float(inputs["battery_capacity"]), 0, 5000)

    weather = compute_weather_factors(temperature, wind_speed, solar_radiation, precipitation, humidity)
    country_load = COUNTRY_LOAD_FACTORS.get(country_model, 1.0)

    base_demand = (population / 10000.0) * 1.85 * country_load
    demand = base_demand * weather["demand"] * sm["demand"]

    solar_supply = solar_capacity * 0.34 * weather["solar"] * sm["solar"]
    wind_supply = wind_capacity * 0.40 * weather["wind"] * sm["wind"]
    geothermal_supply = geothermal_capacity * 0.90
    hydro_supply = hydro_capacity * 0.58 * weather["hydro"] * sm["hydro"]

    renewable_supply = solar_supply + wind_supply + geothermal_supply + hydro_supply

    battery_support = min(battery_capacity * 0.28 * sm["battery"], max(demand - renewable_supply, 0.0))
    final_supply = renewable_supply + battery_support
    shortfall = max(demand - final_supply, 0.0)
    battery_levels = max(battery_capacity - battery_support, 0.0)

    renewable_ratio = clamp(safe_ratio(renewable_supply, final_supply if final_supply > 0 else renewable_supply) * 100.0, 0.0, 100.0)
    system_efficiency = clamp((100.0 - shortfall * 0.65) * (1.0 / sm["grid_risk"]), 0.0, 100.0)
    grid_dependency = clamp(safe_ratio(shortfall, demand) * 100.0 * sm["grid_risk"], 0.0, 100.0)

    return SimulationResult(
        demand=round(demand, 2),
        renewable_supply=round(renewable_supply, 2),
        final_supply=round(final_supply, 2),
        battery_levels=round(battery_levels, 2),
        shortfall=round(shortfall, 2),
        renewable_ratio=round(renewable_ratio, 2),
        system_efficiency=round(system_efficiency, 2),
        grid_dependency=round(grid_dependency, 2),
        solar_supply=round(solar_supply, 2),
        wind_supply=round(wind_supply, 2),
        geothermal_supply=round(geothermal_supply, 2),
        hydro_supply=round(hydro_supply, 2),
    )


def build_comparison_table(inputs: Dict[str, float | str]) -> pd.DataFrame:
    rows: List[Dict[str, float | str]] = []
    for scenario in SCENARIOS:
        r = simulate(inputs, scenario)
        rows.append(
            {
                "scenario": scenario,
                "demand": r.demand,
                "renewable_supply": r.renewable_supply,
                "final_supply": r.final_supply,
                "battery_levels": r.battery_levels,
                "shortfall": r.shortfall,
                "renewable_ratio": r.renewable_ratio,
                "system_efficiency": r.system_efficiency,
                "grid_dependency": r.grid_dependency,
            }
        )
    return pd.DataFrame(rows)


def recommendation_text(result: SimulationResult, scenario: str, language: str) -> List[str]:
    zh = language == "繁體中文"
    recs: List[str] = []
    if result.shortfall > 15:
        recs.append("優先增加儲能與備援容量，降低高風險情境下的供應缺口。" if zh else "Increase storage and reserve capacity first to reduce scenario shortfall.")
    if result.grid_dependency > 20:
        recs.append("目前對外部電網依賴偏高，建議提升在地多元供給。" if zh else "Grid dependency is elevated; diversify local generation sources.")
    if result.renewable_ratio < 65:
        recs.append("再生能源占比偏低，可優先補強太陽能或風能配置。" if zh else "Renewable ratio is low; strengthen solar or wind allocation.")
    if scenario in {"typhoon", "storm", "blizzard"}:
        recs.append("極端事件情境下，建議建立關鍵設施優先供電邏輯。" if zh else "For extreme-event scenarios, prioritize critical-facility supply logic.")
    if not recs:
        recs.append(TEXT[language]["stable"])
    return recs


def init_audit_state() -> None:
    if "audit_rows" not in st.session_state:
        st.session_state.audit_rows = []


def add_audit_row(inputs: Dict[str, float | str], scenario: str, result: SimulationResult) -> None:
    row = {
        "country": inputs["country_key"],
        "city": inputs["city_key"],
        "scenario": scenario,
        "population": inputs["population"],
        "temperature": inputs["temperature"],
        "wind_speed": inputs["wind_speed"],
        "solar_radiation": inputs["solar_radiation"],
        "precipitation": inputs["precipitation"],
        "humidity": inputs["humidity"],
        "solar_capacity": inputs["solar_capacity"],
        "wind_capacity": inputs["wind_capacity"],
        "geothermal_capacity": inputs["geothermal_capacity"],
        "hydro_capacity": inputs["hydro_capacity"],
        "battery_capacity": inputs["battery_capacity"],
        "demand": result.demand,
        "renewable_supply": result.renewable_supply,
        "final_supply": result.final_supply,
        "battery_levels": result.battery_levels,
        "shortfall": result.shortfall,
        "renewable_ratio": result.renewable_ratio,
        "system_efficiency": result.system_efficiency,
        "grid_dependency": result.grid_dependency,
    }
    st.session_state.audit_rows.append(row)
    st.session_state.audit_rows = st.session_state.audit_rows[-20:]


# -----------------------------
# Sidebar controls
# -----------------------------
init_audit_state()

language = st.sidebar.selectbox(TEXT["English"]["language"], ["English", "繁體中文"])
T = TEXT[language]

country = st.sidebar.selectbox(T["country"], list(COUNTRY_CITY_DATA.keys()))
city = st.sidebar.selectbox(T["city"], list(COUNTRY_CITY_DATA[country].keys()))
profile = COUNTRY_CITY_DATA[country][city]
default_capacity = COUNTRY_DEFAULT_CAPACITY[country]

scenario = st.sidebar.selectbox(T["scenario"], SCENARIOS, index=0)

st.sidebar.markdown(f"### {T['weather']}")
population = st.sidebar.slider(T["population"], 10_000, 10_000_000, int(profile["population"]), step=10_000)
temperature = st.sidebar.slider(T["temperature"], -20, 50, int(round(float(profile["temperature"]))))
wind_speed = st.sidebar.slider(T["wind_speed"], 0.0, 20.0, float(profile["wind_speed"]), step=0.1)
solar_radiation = st.sidebar.slider(T["solar_rad"], 0, 1200, int(round(float(profile["solar_radiation"]))))
precipitation = st.sidebar.slider(T["precipitation"], 0, 300, int(round(float(profile["precipitation"]))))
humidity = st.sidebar.slider(T["humidity"], 0, 100, int(round(float(profile["humidity"]))))

st.sidebar.markdown(f"### {T['capacity']}")
solar_capacity = st.sidebar.slider(T["solar"], 0, 500, int(default_capacity["solar"]))
wind_capacity = st.sidebar.slider(T["wind"], 0, 500, int(default_capacity["wind"]))
geothermal_capacity = st.sidebar.slider(T["geo"], 0, 500, int(default_capacity["geo"]))
hydro_capacity = st.sidebar.slider(T["hydro"], 0, 500, int(default_capacity["hydro"]))
battery_capacity = st.sidebar.slider(T["battery"], 0, 1000, int(default_capacity["battery"]))

inputs: Dict[str, float | str] = {
    "country_key": country,
    "city_key": city,
    "lat": float(profile["lat"]),
    "lon": float(profile["lon"]),
    "temperature": temperature,
    "wind_speed": wind_speed,
    "solar_radiation": solar_radiation,
    "precipitation": precipitation,
    "humidity": humidity,
    "population": population,
    "solar_capacity": solar_capacity,
    "wind_capacity": wind_capacity,
    "geothermal_capacity": geothermal_capacity,
    "hydro_capacity": hydro_capacity,
    "battery_capacity": battery_capacity,
    "country_model": profile["country_model"],
}

# -----------------------------
# Simulation
# -----------------------------
result = simulate(inputs, scenario)
comparison_df = build_comparison_table(inputs)
add_audit_row(inputs, scenario, result)

# -----------------------------
# Main UI
# -----------------------------
st.title(T["title"])
st.caption(T["subtitle"])

st.info(f"**{T['overview_title']}**\n\n{T['overview_body']}")

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader(f"{T['country_logic']}: {country}")
    st.write(get_country_logic_text(country))
with col2:
    st.subheader(f"{T['city_profile']}: {city}")
    p1, p2 = st.columns(2)
    with p1:
        st.write(f"**{T['lat']}:** {profile['lat']}")
        st.write(f"**{T['lon']}:** {profile['lon']}")
    with p2:
        st.write(f"**{T['country_model']}:** {profile['country_model']}")
        st.write(profile["climate_note"])

st.success(f"**{T['weather_status']}:** {profile['weather_tag']}")

# Summary cards
st.subheader(T["simulation_summary"])
m = T["metrics"]
row1 = st.columns(4)
row1[0].metric(m["demand"], f"{result.demand:.2f}")
row1[1].metric(m["renewable_supply"], f"{result.renewable_supply:.2f}")
row1[2].metric(m["final_supply"], f"{result.final_supply:.2f}")
row1[3].metric(m["shortfall"], f"{result.shortfall:.2f}")

row2 = st.columns(4)
row2[0].metric(m["battery_levels"], f"{result.battery_levels:.2f}")
row2[1].metric(m["renewable_ratio"], f"{result.renewable_ratio:.2f}%")
row2[2].metric(m["system_efficiency"], f"{result.system_efficiency:.2f}%")
row2[3].metric(m["grid_dependency"], f"{result.grid_dependency:.2f}%")

# Two-column dashboard section
left, right = st.columns([1.1, 1.2])
with left:
    st.subheader(T["energy_mix"])
    energy_values = [
        max(result.solar_supply, 0.0),
        max(result.wind_supply, 0.0),
        max(result.geothermal_supply, 0.0),
        max(result.hydro_supply, 0.0),
    ]
    energy_labels = ["Solar", "Wind", "Geothermal", "Hydro"]
    total_mix = sum(energy_values)

    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    if total_mix > 0:
        percentages = [(v / total_mix) * 100.0 for v in energy_values]

        def pct_fmt(pct: float) -> str:
            return f"{pct:.1f}%" if pct >= 4 else ""

        wedges, _, autotexts = ax.pie(
            energy_values,
            labels=None,
            autopct=pct_fmt,
            startangle=90,
            pctdistance=0.72,
            wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.2},
            textprops={"fontsize": 10},
        )

        for autotext in autotexts:
            autotext.set_fontsize(11)
            autotext.set_weight("bold")

        ax.text(0, 0, "Renewable\nMix", ha="center", va="center", fontsize=13, fontweight="bold")
        ax.axis("equal")

        legend_labels = [
            f"{label} — {pct:.1f}%"
            for label, pct in zip(energy_labels, percentages)
        ]
        ax.legend(
            wedges,
            legend_labels,
            title="Share",
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
            frameon=False,
        )
    else:
        ax.text(0.5, 0.5, "No energy supply", ha="center", va="center")
        ax.axis("off")
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    mix_df = pd.DataFrame(
        {
            "Source": energy_labels,
            "Supply": [round(v, 2) for v in energy_values],
            "Share %": [round((v / total_mix) * 100, 2) if total_mix > 0 else 0.0 for v in energy_values],
        }
    )
    st.dataframe(mix_df, use_container_width=True, hide_index=True)

with right:
    st.subheader(T["comparison"])
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

st.subheader(T["recommendation"])
for idx, rec in enumerate(recommendation_text(result, scenario, language), start=1):
    st.write(f"{idx}. {rec}")

st.subheader(T["governance"])
st.warning(f"{T['decision_support']} {T['deviation']}")

st.subheader(T["audit"])
audit_df = pd.DataFrame(st.session_state.audit_rows)
if not audit_df.empty:
    st.dataframe(audit_df.iloc[::-1], use_container_width=True, hide_index=True)
    st.download_button(
        label=T["download_csv"],
        data=audit_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="taivas_audit_trail.csv",
        mime="text/csv",
    )
else:
    st.write("No audit rows yet.")

with st.expander(T["show_debug"], expanded=False):
    st.json(inputs)
    st.json(
        {
            "scenario": scenario,
            "result": {
                "demand": result.demand,
                "renewable_supply": result.renewable_supply,
                "final_supply": result.final_supply,
                "battery_levels": result.battery_levels,
                "shortfall": result.shortfall,
                "renewable_ratio": result.renewable_ratio,
                "system_efficiency": result.system_efficiency,
                "grid_dependency": result.grid_dependency,
            },
        }
    )
