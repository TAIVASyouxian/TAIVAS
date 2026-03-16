from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

# =========================
# TAIVAS V1 CORE CONSTANTS
# =========================
SCENARIOS = [
    "normal",
    "heat_wave",
    "storm",
    "cold_wave",
    "blizzard",
    "typhoon",
]

LANG = {
    "English": {
        "app_title": "TAIVAS Energy Control Center",
        "app_subtitle": "AI-driven energy resilience and recovery dashboard",
        "sidebar": "Control Panel",
        "language": "Language / 語言",
        "country": "Country",
        "city": "City",
        "scenario": "Scenario",
        "population": "Population",
        "weather": "Weather Inputs",
        "capacity": "Energy Capacity Inputs",
        "battery": "Battery Capacity (MWh)",
        "solar": "Solar Capacity (MW)",
        "wind": "Wind Capacity (MW)",
        "geo": "Geothermal Capacity (MW)",
        "hydro": "Hydropower Capacity (MW)",
        "temperature": "Temperature (°C)",
        "wind_speed": "Wind Speed (m/s)",
        "solar_rad": "Solar Radiation (W/m²)",
        "precip": "Precipitation (mm)",
        "humidity": "Humidity (%)",
        "run": "Simulation Summary",
        "baseline": "Baseline vs Selected Scenario",
        "energy_mix": "Energy Mix",
        "scenario_table": "Scenario Comparison Table",
        "recommendation": "AI Recommendation Panel",
        "governance": "Risk & Governance Reminder",
        "audit": "Audit Trail (Current Session)",
        "input_summary": "Input Summary",
        "city_profile": "City Profile",
        "weather_status": "Weather Status",
        "decision_support": "This product is decision-support software, not an unconditional guarantee.",
        "deviation": "I understand that changing assumptions may lead to different outcomes.",
        "accept_rec": "Accept AI recommendation",
        "reject_rec": "Override / reject AI recommendation",
        "stable": "System is relatively stable under the selected scenario.",
    },
    "繁體中文": {
        "app_title": "TAIVAS 能源控制中心",
        "app_subtitle": "AI 驅動的能源韌性與復原儀表板",
        "sidebar": "控制面板",
        "language": "Language / 語言",
        "country": "國家",
        "city": "城市",
        "scenario": "情境",
        "population": "人口",
        "weather": "氣候輸入",
        "capacity": "能源容量輸入",
        "battery": "電池容量 (MWh)",
        "solar": "太陽能容量 (MW)",
        "wind": "風力容量 (MW)",
        "geo": "地熱容量 (MW)",
        "hydro": "水力容量 (MW)",
        "temperature": "溫度 (°C)",
        "wind_speed": "風速 (m/s)",
        "solar_rad": "太陽輻射 (W/m²)",
        "precip": "降水量 (mm)",
        "humidity": "濕度 (%)",
        "run": "模擬摘要",
        "baseline": "基準情境 vs 選定情境",
        "energy_mix": "能源組成",
        "scenario_table": "情境比較表",
        "recommendation": "AI 建議面板",
        "governance": "風險與治理提醒",
        "audit": "稽核軌跡（本次工作階段）",
        "input_summary": "輸入摘要",
        "city_profile": "城市檔案",
        "weather_status": "天氣狀態",
        "decision_support": "本產品屬於決策輔助工具，並非無條件保證。",
        "deviation": "我理解調整假設條件後，結果可能不同。",
        "accept_rec": "接受 AI 建議",
        "reject_rec": "覆寫 / 不採納 AI 建議",
        "stable": "在目前情境下，系統整體相對穩定。",
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


@dataclass
class TaivasInputs:
    country_key: str
    city_key: str
    lat: float
    lon: float
    temperature: float
    wind_speed: float
    solar_radiation: float
    precipitation: float
    humidity: float
    population: int
    solar_capacity: float
    wind_capacity: float
    geothermal_capacity: float
    hydro_capacity: float
    battery_capacity: float


@dataclass
class TaivasOutputs:
    demand: float
    renewable_supply: float
    final_supply: float
    battery_levels: float
    shortfall: float
    renewable_ratio: float
    system_efficiency: float
    grid_dependency: float


def clamp(val: float, low: float, high: float) -> float:
    return max(low, min(high, val))


def apply_scenario(base: TaivasInputs, scenario: str) -> TaivasInputs:
    x = TaivasInputs(**asdict(base))
    if scenario == "heat_wave":
        x.temperature += 8
        x.humidity = clamp(x.humidity + 6, 0, 100)
        x.solar_radiation *= 1.05
    elif scenario == "storm":
        x.wind_speed *= 1.35
        x.precipitation *= 2.0
        x.solar_radiation *= 0.72
        x.humidity = clamp(x.humidity + 10, 0, 100)
    elif scenario == "cold_wave":
        x.temperature -= 10
        x.solar_radiation *= 0.82
        x.humidity = clamp(x.humidity + 2, 0, 100)
    elif scenario == "blizzard":
        x.temperature -= 15
        x.wind_speed *= 1.18
        x.precipitation *= 1.8
        x.solar_radiation *= 0.42
        x.humidity = clamp(x.humidity + 8, 0, 100)
    elif scenario == "typhoon":
        x.wind_speed *= 1.7
        x.precipitation *= 2.8
        x.solar_radiation *= 0.35
        x.humidity = clamp(x.humidity + 12, 0, 100)

    x.wind_speed = max(0.0, x.wind_speed)
    x.solar_radiation = max(0.0, x.solar_radiation)
    x.precipitation = max(0.0, x.precipitation)
    return x


def estimate_demand(inp: TaivasInputs, scenario: str) -> float:
    base = 0.00022 * inp.population
    temp_gap = abs(inp.temperature - 20.0)
    climate_load = temp_gap * 2.6
    humidity_load = max(inp.humidity - 65.0, 0.0) * 0.28

    scenario_multiplier = {
        "normal": 1.00,
        "heat_wave": 1.18,
        "storm": 1.10,
        "cold_wave": 1.16,
        "blizzard": 1.28,
        "typhoon": 1.24,
    }[scenario]
    return max((base + climate_load + humidity_load) * scenario_multiplier, 0.0)


def estimate_supply(inp: TaivasInputs) -> Dict[str, float]:
    solar_cf = clamp(inp.solar_radiation / 850.0, 0.0, 1.0) * (1 - clamp(inp.humidity / 300.0, 0.0, 0.35))
    wind_cf = clamp(inp.wind_speed / 12.0, 0.0, 1.0)
    hydro_cf = clamp(0.42 + inp.precipitation / 320.0, 0.2, 0.96)
    geo_cf = 0.9

    solar = inp.solar_capacity * solar_cf
    wind = inp.wind_capacity * wind_cf
    hydro = inp.hydro_capacity * hydro_cf
    geothermal = inp.geothermal_capacity * geo_cf
    renewable = solar + wind + hydro + geothermal

    return {
        "solar": round(solar, 2),
        "wind": round(wind, 2),
        "hydro": round(hydro, 2),
        "geothermal": round(geothermal, 2),
        "renewable": round(renewable, 2),
        "solar_cf": round(solar_cf, 4),
        "wind_cf": round(wind_cf, 4),
        "hydro_cf": round(hydro_cf, 4),
        "geo_cf": round(geo_cf, 4),
    }


def simulate_taivas(base: TaivasInputs, scenario: str) -> Tuple[TaivasOutputs, Dict[str, float], TaivasInputs]:
    adjusted = apply_scenario(base, scenario)
    demand = estimate_demand(adjusted, scenario)
    supply = estimate_supply(adjusted)
    renewable_supply = supply["renewable"]

    battery_dispatch_limit = adjusted.battery_capacity * 0.35
    battery_support = min(max(demand - renewable_supply, 0.0), battery_dispatch_limit)
    final_supply = renewable_supply + battery_support
    shortfall = max(demand - final_supply, 0.0)
    battery_levels = max(adjusted.battery_capacity - battery_support, 0.0)
    renewable_ratio = renewable_supply / demand if demand > 0 else 0.0
    system_efficiency = min(final_supply / demand, 1.0) if demand > 0 else 1.0
    grid_dependency = shortfall / demand if demand > 0 else 0.0

    out = TaivasOutputs(
        demand=round(demand, 2),
        renewable_supply=round(renewable_supply, 2),
        final_supply=round(final_supply, 2),
        battery_levels=round(battery_levels, 2),
        shortfall=round(shortfall, 2),
        renewable_ratio=round(renewable_ratio, 4),
        system_efficiency=round(system_efficiency, 4),
        grid_dependency=round(grid_dependency, 4),
    )
    return out, supply, adjusted


def build_explainable_recommendations(base_out: TaivasOutputs, scenario_out: TaivasOutputs, supply: Dict[str, float], scenario: str, labels: Dict[str, str]) -> List[Dict[str, str]]:
    recs: List[Dict[str, str]] = []

    if scenario_out.shortfall > 0:
        recs.append({
            "recommendation": "Increase battery reserve or add backup dispatch capacity.",
            "reason": f"Shortfall is {scenario_out.shortfall:.2f} MW under {scenario}.",
            "consequence": "This reduces unmet demand and lowers outage risk.",
        })
    if scenario_out.renewable_ratio < 0.75:
        recs.append({
            "recommendation": "Expand renewable capacity mix or rebalance local generation.",
            "reason": f"Renewable ratio is {scenario_out.renewable_ratio * 100:.1f}%.",
            "consequence": "Higher self-supply improves resilience and reduces grid stress.",
        })
    if scenario_out.grid_dependency > 0.15:
        recs.append({
            "recommendation": "Strengthen microgrid isolation and critical-load prioritization.",
            "reason": f"Grid dependency is {scenario_out.grid_dependency * 100:.1f}%.",
            "consequence": "Core services remain more stable during extreme events.",
        })
    if scenario in {"storm", "typhoon", "blizzard"}:
        recs.append({
            "recommendation": "Protect storage reserve and pre-position emergency operating mode.",
            "reason": "Extreme-weather scenario is active.",
            "consequence": "Improves response speed and protects essential loads.",
        })
    if supply["solar"] < supply["wind"] * 0.4 and scenario in {"normal", "heat_wave"}:
        recs.append({
            "recommendation": "Review solar assumptions or increase solar deployment.",
            "reason": "Solar contribution is materially lower than wind in a sun-favorable case.",
            "consequence": "This can improve daytime resilience and renewable ratio.",
        })
    if not recs:
        recs.append({
            "recommendation": labels["stable"],
            "reason": "No major resilience weakness is visible in this run.",
            "consequence": "Continue monitoring and compare with additional scenarios.",
        })

    if scenario_out.final_supply > base_out.final_supply:
        recs.append({
            "recommendation": "Keep scenario comparison enabled when presenting results.",
            "reason": "Selected scenario materially changes supply-demand balance from baseline.",
            "consequence": "This supports explainability and auditability.",
        })

    return recs


def get_labels(selected_language: str) -> Dict[str, str]:
    return LANG[selected_language]


def ensure_audit_log() -> None:
    if "taivas_audit_log" not in st.session_state:
        st.session_state.taivas_audit_log = []


def push_audit_entry(inputs: TaivasInputs, scenario: str, outputs: TaivasOutputs, accepted: str) -> None:
    st.session_state.taivas_audit_log.append(
        {
            "country": inputs.country_key,
            "city": inputs.city_key,
            "scenario": scenario,
            "demand": outputs.demand,
            "renewable_supply": outputs.renewable_supply,
            "final_supply": outputs.final_supply,
            "shortfall": outputs.shortfall,
            "renewable_ratio": round(outputs.renewable_ratio * 100, 2),
            "grid_dependency": round(outputs.grid_dependency * 100, 2),
            "accepted_ai_recommendation": accepted,
        }
    )


def render_sidebar(labels: Dict[str, str]) -> Tuple[str, TaivasInputs, str, Dict[str, float | str]]:
    st.sidebar.header(labels["sidebar"])
    language = st.sidebar.selectbox(labels["language"], list(LANG.keys()), index=0)
    labels = get_labels(language)

    country = st.sidebar.selectbox(labels["country"], list(COUNTRY_CITY_DATA.keys()), index=0)
    cities = list(COUNTRY_CITY_DATA[country].keys())
    city = st.sidebar.selectbox(labels["city"], cities, index=0)
    profile = COUNTRY_CITY_DATA[country][city]
    cap = COUNTRY_DEFAULT_CAPACITY[country]

    scenario = st.sidebar.selectbox(labels["scenario"], SCENARIOS, index=0)
    st.sidebar.subheader(labels["weather"])
    temperature = st.sidebar.slider(labels["temperature"], -30.0, 45.0, float(profile["temperature"]), 0.5)
    wind_speed = st.sidebar.slider(labels["wind_speed"], 0.0, 45.0, float(profile["wind_speed"]), 0.1)
    solar_radiation = st.sidebar.slider(labels["solar_rad"], 0.0, 1200.0, float(profile["solar_radiation"]), 5.0)
    precipitation = st.sidebar.slider(labels["precip"], 0.0, 500.0, float(profile["precipitation"]), 1.0)
    humidity = st.sidebar.slider(labels["humidity"], 0.0, 100.0, float(profile["humidity"]), 1.0)

    st.sidebar.subheader(labels["capacity"])
    population = st.sidebar.slider(labels["population"], 10000, 10000000, int(profile["population"]), 10000)
    solar_capacity = st.sidebar.slider(labels["solar"], 0.0, 1000.0, float(cap["solar"]), 5.0)
    wind_capacity = st.sidebar.slider(labels["wind"], 0.0, 1000.0, float(cap["wind"]), 5.0)
    geothermal_capacity = st.sidebar.slider(labels["geo"], 0.0, 500.0, float(cap["geo"]), 5.0)
    hydro_capacity = st.sidebar.slider(labels["hydro"], 0.0, 1000.0, float(cap["hydro"]), 5.0)
    battery_capacity = st.sidebar.slider(labels["battery"], 0.0, 1000.0, float(cap["battery"]), 5.0)

    inputs = TaivasInputs(
        country_key=country,
        city_key=city,
        lat=float(profile["lat"]),
        lon=float(profile["lon"]),
        temperature=temperature,
        wind_speed=wind_speed,
        solar_radiation=solar_radiation,
        precipitation=precipitation,
        humidity=humidity,
        population=population,
        solar_capacity=solar_capacity,
        wind_capacity=wind_capacity,
        geothermal_capacity=geothermal_capacity,
        hydro_capacity=hydro_capacity,
        battery_capacity=battery_capacity,
    )
    return language, inputs, scenario, profile


def metric_row(outputs: TaivasOutputs) -> None:
    a, b, c, d = st.columns(4)
    a.metric("Demand", f"{outputs.demand:.2f} MW")
    b.metric("Renewable Supply", f"{outputs.renewable_supply:.2f} MW")
    c.metric("Final Supply", f"{outputs.final_supply:.2f} MW")
    d.metric("Shortfall", f"{outputs.shortfall:.2f} MW")

    e, f, g, h = st.columns(4)
    e.metric("Battery Left", f"{outputs.battery_levels:.2f} MWh")
    f.metric("Renewable Ratio", f"{outputs.renewable_ratio * 100:.1f}%")
    g.metric("System Efficiency", f"{outputs.system_efficiency * 100:.1f}%")
    h.metric("Grid Dependency", f"{outputs.grid_dependency * 100:.1f}%")


def main() -> None:
    st.set_page_config(page_title="TAIVAS Energy Control Center", layout="wide")
    ensure_audit_log()

    default_labels = get_labels("English")
    language, inputs, scenario, profile = render_sidebar(default_labels)
    labels = get_labels(language)

    st.title(labels["app_title"])
    st.caption(labels["app_subtitle"])
    st.info(
        "This app is the main control center for TAIVAS. It combines country logic, city profiles, "
        "weather simulation, and energy resilience dashboard controls."
    )

    baseline_outputs, baseline_supply, baseline_adjusted = simulate_taivas(inputs, "normal")
    outputs, supply_map, adjusted = simulate_taivas(inputs, scenario)
    recommendations = build_explainable_recommendations(baseline_outputs, outputs, supply_map, scenario, labels)

    st.subheader(labels["run"])
    metric_row(outputs)

    left, right = st.columns([1.15, 0.85])
    with left:
        st.subheader(f"{labels['city_profile']}: {inputs.city_key}")
        st.write(f"Latitude: {inputs.lat}")
        st.write(f"Longitude: {inputs.lon}")
        st.write(f"Country Model: {profile['country_model']}")
        st.write(profile["climate_note"])
        st.success(f"{labels['weather_status']}: {profile['weather_tag']}")

        st.subheader(labels["input_summary"])
        st.json(asdict(inputs))

    with right:
        st.subheader(labels["baseline"])
        compare_df = pd.DataFrame(
            {
                "Metric": [
                    "Demand (MW)",
                    "Renewable Supply (MW)",
                    "Final Supply (MW)",
                    "Shortfall (MW)",
                    "Battery Left (MWh)",
                    "Renewable Ratio (%)",
                    "Grid Dependency (%)",
                ],
                "Normal": [
                    baseline_outputs.demand,
                    baseline_outputs.renewable_supply,
                    baseline_outputs.final_supply,
                    baseline_outputs.shortfall,
                    baseline_outputs.battery_levels,
                    round(baseline_outputs.renewable_ratio * 100, 2),
                    round(baseline_outputs.grid_dependency * 100, 2),
                ],
                scenario: [
                    outputs.demand,
                    outputs.renewable_supply,
                    outputs.final_supply,
                    outputs.shortfall,
                    outputs.battery_levels,
                    round(outputs.renewable_ratio * 100, 2),
                    round(outputs.grid_dependency * 100, 2),
                ],
            }
        )
        st.dataframe(compare_df, use_container_width=True, hide_index=True)

    st.divider()
    tab1, tab2, tab3, tab4 = st.tabs([
        labels["energy_mix"],
        labels["scenario_table"],
        labels["recommendation"],
        labels["audit"],
    ])

    with tab1:
        mix_df = pd.DataFrame(
            {
                "Source": ["Solar", "Wind", "Hydro", "Geothermal"],
                "Output (MW)": [supply_map["solar"], supply_map["wind"], supply_map["hydro"], supply_map["geothermal"]],
            }
        ).set_index("Source")
        st.bar_chart(mix_df)

        cf_df = pd.DataFrame(
            {
                "Source": ["Solar CF", "Wind CF", "Hydro CF", "Geo CF"],
                "Capacity Factor": [
                    supply_map["solar_cf"],
                    supply_map["wind_cf"],
                    supply_map["hydro_cf"],
                    supply_map["geo_cf"],
                ],
            }
        ).set_index("Source")
        st.line_chart(cf_df)

    with tab2:
        rows = []
        for sc in SCENARIOS:
            out, _, adj = simulate_taivas(inputs, sc)
            rows.append(
                {
                    "Scenario": sc,
                    "Temp": adj.temperature,
                    "Wind": round(adj.wind_speed, 2),
                    "Solar Rad": round(adj.solar_radiation, 2),
                    "Demand": out.demand,
                    "Renewable": out.renewable_supply,
                    "Final Supply": out.final_supply,
                    "Shortfall": out.shortfall,
                    "Renewable %": round(out.renewable_ratio * 100, 2),
                    "Grid %": round(out.grid_dependency * 100, 2),
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab3:
        st.subheader(labels["recommendation"])
        for idx, rec in enumerate(recommendations, start=1):
            st.markdown(
                f"**{idx}. Recommendation:** {rec['recommendation']}  \n"
                f"**Reason:** {rec['reason']}  \n"
                f"**Consequence:** {rec['consequence']}"
            )
            st.divider()

        st.subheader(labels["governance"])
        st.warning(labels["decision_support"])
        deviation_ack = st.checkbox(labels["deviation"], value=True)
        decision = st.radio("AI Decision", [labels["accept_rec"], labels["reject_rec"]], horizontal=True)

        if deviation_ack:
            push_audit_entry(inputs, scenario, outputs, decision)
            st.success("Session decision logged below.")

    with tab4:
        if st.session_state.taivas_audit_log:
            audit_df = pd.DataFrame(st.session_state.taivas_audit_log).tail(20)
            st.dataframe(audit_df, use_container_width=True, hide_index=True)
        else:
            st.write("No audit entries yet.")

    st.divider()
    st.code(
        """
Run locally:
python -m streamlit run taivas_control_center_complete.py

Core inputs:
country_key, city_key, lat, lon, temperature, wind_speed, solar_radiation,
precipitation, humidity, population, solar_capacity, wind_capacity,
geothermal_capacity, hydro_capacity, battery_capacity

Core outputs:
demand, renewable_supply, final_supply, battery_levels, shortfall,
renewable_ratio, system_efficiency, grid_dependency

Scenarios:
normal, heat_wave, storm, cold_wave, blizzard, typhoon
        """.strip(),
        language="python",
    )


if __name__ == "__main__":
    main()
