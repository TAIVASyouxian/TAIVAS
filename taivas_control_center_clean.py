import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

# Optional plotting backend
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False


# -----------------------------
# App config
# -----------------------------
st.set_page_config(
    page_title="TAIVAS Energy Control Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Defensive helpers
# -----------------------------
def safe_float(value, default=0.0, min_value=None, max_value=None) -> float:
    try:
        v = float(value)
    except Exception:
        v = float(default)
    if min_value is not None:
        v = max(v, min_value)
    if max_value is not None:
        v = min(v, max_value)
    if math.isnan(v) or math.isinf(v):
        return float(default)
    return v


def safe_int(value, default=0, min_value=None, max_value=None) -> int:
    try:
        v = int(round(float(value)))
    except Exception:
        v = int(default)
    if min_value is not None:
        v = max(v, min_value)
    if max_value is not None:
        v = min(v, max_value)
    return v


def pct(numerator: float, denominator: float) -> float:
    denominator = safe_float(denominator, 1.0)
    if denominator == 0:
        return 0.0
    return (safe_float(numerator) / denominator) * 100.0


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    denominator = safe_float(denominator, 0.0)
    if denominator == 0:
        return default
    return safe_float(numerator) / denominator


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    clean = {k: max(0.0, safe_float(v, 0.0)) for k, v in weights.items()}
    total = sum(clean.values())
    if total <= 0:
        count = max(len(clean), 1)
        return {k: 1.0 / count for k in clean}
    return {k: v / total for k, v in clean.items()}


def add_audit_log(entry: Dict):
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []
    st.session_state.audit_log.insert(0, entry)
    st.session_state.audit_log = st.session_state.audit_log[:25]


# -----------------------------
# Domain data
# -----------------------------
LANG = {
    "English": {
        "title": "TAIVAS Energy Control Center",
        "subtitle": "AI-driven energy resilience and recovery dashboard",
        "main_desc": "This app is the main control center for TAIVAS. It combines country logic, city profiles, weather simulation, scenario analysis, and energy resilience dashboard controls.",
        "weather_status": "Weather Status",
        "scenario": "Scenario",
        "run": "Run simulation",
        "baseline": "Baseline",
        "summary": "Simulation Summary",
        "recommendation": "AI Recommendation",
        "risk": "Risk / Governance Notice",
        "audit": "Session Audit Trail",
        "inputs_ok": "Inputs validated successfully.",
        "fix_inputs": "Some inputs were auto-corrected to keep the model stable.",
    },
    "中文": {
        "title": "TAIVAS 能源控制中心",
        "subtitle": "AI 驅動的能源韌性與復原儀表板",
        "main_desc": "此應用程式是 TAIVAS 的主控制中心，整合國家邏輯、城市檔案、天氣模擬、情境分析與能源韌性儀表板控制。",
        "weather_status": "天氣狀態",
        "scenario": "情境",
        "run": "執行模擬",
        "baseline": "基準情境",
        "summary": "模擬摘要",
        "recommendation": "AI 建議",
        "risk": "風險 / 治理提醒",
        "audit": "本次工作階段稽核紀錄",
        "inputs_ok": "輸入已通過驗證。",
        "fix_inputs": "系統已自動修正部分輸入，避免模型不穩定。",
    },
}


CITY_DATA: Dict[str, Dict[str, Dict]] = {
    "[TW] Taiwan": {
        "[TW] Taipei, Taiwan": {
            "lat": 25.0330,
            "lon": 121.5654,
            "temperature": 28,
            "wind_speed": 4.5,
            "solar_radiation": 5.2,
            "precipitation": 6.0,
            "humidity": 74,
            "country_model": "taiwan",
            "logic": "Cooling-heavy island model with strong storage need.",
        },
        "[TW] Kaohsiung, Taiwan": {
            "lat": 22.6273,
            "lon": 120.3014,
            "temperature": 30,
            "wind_speed": 5.0,
            "solar_radiation": 5.6,
            "precipitation": 4.0,
            "humidity": 71,
            "country_model": "taiwan",
            "logic": "Industrial-port city with good solar potential.",
        },
        "[TW] Taichung, Taiwan": {
            "lat": 24.1477,
            "lon": 120.6736,
            "temperature": 29,
            "wind_speed": 4.2,
            "solar_radiation": 5.4,
            "precipitation": 3.5,
            "humidity": 68,
            "country_model": "taiwan",
            "logic": "Balanced metro profile with moderate wind and solar mix.",
        },
    },
    "[FI] Finland": {
        "[FI] Helsinki, Finland": {
            "lat": 60.1699,
            "lon": 24.9384,
            "temperature": 9,
            "wind_speed": 6.2,
            "solar_radiation": 2.8,
            "precipitation": 2.3,
            "humidity": 77,
            "country_model": "finland",
            "logic": "Heating-heavy northern model with high resilience priority.",
        },
        "[FI] Rovaniemi, Finland": {
            "lat": 66.5039,
            "lon": 25.7294,
            "temperature": 1,
            "wind_speed": 5.5,
            "solar_radiation": 2.0,
            "precipitation": 2.7,
            "humidity": 80,
            "country_model": "finland",
            "logic": "Cold-climate resilience model with extreme winter sensitivity.",
        },
    },
    "[NO] Norway": {
        "[NO] Oslo, Norway": {
            "lat": 59.9139,
            "lon": 10.7522,
            "temperature": 8,
            "wind_speed": 5.8,
            "solar_radiation": 2.9,
            "precipitation": 3.1,
            "humidity": 76,
            "country_model": "norway",
            "logic": "Hydro-advantaged resilience model with strong winter demand.",
        }
    },
    "[CH] Switzerland": {
        "[CH] Zurich, Switzerland": {
            "lat": 47.3769,
            "lon": 8.5417,
            "temperature": 11,
            "wind_speed": 4.6,
            "solar_radiation": 3.4,
            "precipitation": 3.2,
            "humidity": 72,
            "country_model": "switzerland",
            "logic": "High-value urban resilience model with balanced diversification need.",
        }
    },
}


SCENARIOS = {
    "normal": {
        "label": "Normal",
        "demand_mult": 1.00,
        "solar_mult": 1.00,
        "wind_mult": 1.00,
        "hydro_mult": 1.00,
        "geo_mult": 1.00,
        "battery_stress": 1.00,
        "desc": "Standard operations.",
    },
    "heat_wave": {
        "label": "Heat Wave",
        "demand_mult": 1.25,
        "solar_mult": 1.08,
        "wind_mult": 0.92,
        "hydro_mult": 0.95,
        "geo_mult": 1.00,
        "battery_stress": 1.10,
        "desc": "High cooling load, slightly stronger solar, stressed storage.",
    },
    "storm": {
        "label": "Storm",
        "demand_mult": 1.12,
        "solar_mult": 0.55,
        "wind_mult": 1.18,
        "hydro_mult": 1.05,
        "geo_mult": 1.00,
        "battery_stress": 1.08,
        "desc": "Cloud cover reduces solar, wind may spike, grid stress rises.",
    },
    "cold_wave": {
        "label": "Cold Wave",
        "demand_mult": 1.35,
        "solar_mult": 0.78,
        "wind_mult": 1.05,
        "hydro_mult": 0.97,
        "geo_mult": 1.05,
        "battery_stress": 1.18,
        "desc": "Heating demand surges, solar weakens, storage under pressure.",
    },
    "blizzard": {
        "label": "Blizzard",
        "demand_mult": 1.42,
        "solar_mult": 0.40,
        "wind_mult": 1.12,
        "hydro_mult": 0.92,
        "geo_mult": 1.03,
        "battery_stress": 1.25,
        "desc": "Extreme winter disruption with severe renewable instability.",
    },
    "typhoon": {
        "label": "Typhoon",
        "demand_mult": 1.18,
        "solar_mult": 0.25,
        "wind_mult": 0.85,
        "hydro_mult": 1.10,
        "geo_mult": 1.00,
        "battery_stress": 1.22,
        "desc": "Severe storm event with strong outage and storage pressure risk.",
    },
}


WEATHER_STATUS = [
    "☀️ Sunny",
    "⛅ Partly Cloudy",
    "🌧️ Rainy",
    "⛈️ Stormy",
    "❄️ Snowy",
    "🌫️ Foggy",
]


@dataclass
class SimulationInputs:
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
    scenario_key: str


# -----------------------------
# Validation
# -----------------------------
def validate_inputs(data: SimulationInputs) -> Tuple[SimulationInputs, List[str]]:
    fixes = []

    lat = safe_float(data.lat, 0.0, -90, 90)
    if lat != data.lat:
        fixes.append("Latitude adjusted to valid range.")
    lon = safe_float(data.lon, 0.0, -180, 180)
    if lon != data.lon:
        fixes.append("Longitude adjusted to valid range.")

    population = safe_int(data.population, 100000, 1, 100_000_000)
    if population != data.population:
        fixes.append("Population adjusted.")

    vals = {}
    for name in [
        "temperature",
        "wind_speed",
        "solar_radiation",
        "precipitation",
        "humidity",
        "solar_capacity",
        "wind_capacity",
        "geothermal_capacity",
        "hydro_capacity",
        "battery_capacity",
    ]:
        raw = getattr(data, name)
        max_value = 100 if name == "humidity" else None
        clean = safe_float(raw, 0.0, 0.0 if name != "temperature" else -50.0, max_value)
        vals[name] = clean
        if clean != raw:
            fixes.append(f"{name} adjusted.")

    temperature = safe_float(data.temperature, 20.0, -50, 60)
    if temperature != data.temperature:
        fixes.append("temperature adjusted.")

    scenario_key = data.scenario_key if data.scenario_key in SCENARIOS else "normal"
    if scenario_key != data.scenario_key:
        fixes.append("Scenario reset to normal.")

    clean = SimulationInputs(
        country_key=data.country_key,
        city_key=data.city_key,
        lat=lat,
        lon=lon,
        temperature=temperature,
        wind_speed=vals["wind_speed"],
        solar_radiation=vals["solar_radiation"],
        precipitation=vals["precipitation"],
        humidity=vals["humidity"],
        population=population,
        solar_capacity=vals["solar_capacity"],
        wind_capacity=vals["wind_capacity"],
        geothermal_capacity=vals["geothermal_capacity"],
        hydro_capacity=vals["hydro_capacity"],
        battery_capacity=vals["battery_capacity"],
        scenario_key=scenario_key,
    )
    return clean, fixes


# -----------------------------
# Model core
# -----------------------------
def build_country_weights(country_model: str) -> Dict[str, float]:
    presets = {
        "taiwan": {"solar": 0.33, "wind": 0.27, "geothermal": 0.12, "hydro": 0.08, "battery": 0.20},
        "finland": {"solar": 0.14, "wind": 0.24, "geothermal": 0.12, "hydro": 0.20, "battery": 0.30},
        "norway": {"solar": 0.08, "wind": 0.22, "geothermal": 0.10, "hydro": 0.40, "battery": 0.20},
        "switzerland": {"solar": 0.20, "wind": 0.16, "geothermal": 0.12, "hydro": 0.22, "battery": 0.30},
    }
    return normalize_weights(presets.get(country_model, presets["taiwan"]))


def compute_base_demand(inp: SimulationInputs) -> float:
    # MW-scale simplified model
    pop_factor = inp.population / 100_000
    thermal_pressure = max(0, inp.temperature - 24) * 0.8 + max(0, 12 - inp.temperature) * 1.2
    humidity_pressure = max(0, inp.humidity - 65) * 0.08
    weather_pressure = inp.precipitation * 0.15
    return max(10.0, 28 * pop_factor + thermal_pressure + humidity_pressure + weather_pressure)


def compute_supply(inp: SimulationInputs, country_model: str, scenario_key: str) -> Dict[str, float]:
    sc = SCENARIOS[scenario_key]
    weights = build_country_weights(country_model)

    solar_cf = min(0.35, max(0.03, 0.08 + inp.solar_radiation * 0.035)) * sc["solar_mult"]
    wind_cf = min(0.55, max(0.06, 0.12 + inp.wind_speed * 0.035)) * sc["wind_mult"]
    geo_cf = 0.86 * sc["geo_mult"]
    hydro_cf = min(0.72, max(0.12, 0.28 + inp.precipitation * 0.05)) * sc["hydro_mult"]

    solar = inp.solar_capacity * solar_cf * (0.8 + weights["solar"])
    wind = inp.wind_capacity * wind_cf * (0.8 + weights["wind"])
    geothermal = inp.geothermal_capacity * geo_cf * (0.8 + weights["geothermal"])
    hydro = inp.hydro_capacity * hydro_cf * (0.8 + weights["hydro"])

    renewable_supply = max(0.0, solar + wind + geothermal + hydro)
    return {
        "solar": solar,
        "wind": wind,
        "geothermal": geothermal,
        "hydro": hydro,
        "renewable_supply": renewable_supply,
        "weights": weights,
    }


def simulate(inp: SimulationInputs, city_meta: Dict) -> Dict:
    country_model = city_meta.get("country_model", "taiwan")
    sc = SCENARIOS[inp.scenario_key]

    demand = compute_base_demand(inp) * sc["demand_mult"]
    supply = compute_supply(inp, country_model, inp.scenario_key)
    renewable_supply = supply["renewable_supply"]

    battery_discharge_cap = inp.battery_capacity * 0.42 / sc["battery_stress"]
    battery_charge_cap = inp.battery_capacity * 0.28

    direct_gap = demand - renewable_supply
    if direct_gap > 0:
        battery_used = min(battery_discharge_cap, direct_gap)
        grid_needed = max(0.0, direct_gap - battery_used)
        curtailed_energy = 0.0
    else:
        battery_used = 0.0
        grid_needed = 0.0
        curtailed_energy = min(abs(direct_gap), battery_charge_cap)

    final_supply = renewable_supply + battery_used + grid_needed
    shortfall = max(0.0, demand - final_supply)

    renewable_ratio = min(100.0, pct(renewable_supply, final_supply if final_supply > 0 else demand))
    system_efficiency = max(0.0, min(100.0, 100.0 - pct(curtailed_energy + shortfall, max(final_supply, 1.0))))
    grid_dependency = pct(grid_needed, final_supply if final_supply > 0 else demand)

    battery_remaining = max(0.0, inp.battery_capacity - battery_used)
    resilience_score = max(
        0.0,
        min(
            100.0,
            45
            + renewable_ratio * 0.25
            + system_efficiency * 0.20
            + max(0, 20 - grid_dependency) * 0.9
            - shortfall * 0.8,
        ),
    )

    return {
        "country_model": country_model,
        "demand": round(demand, 2),
        "renewable_supply": round(renewable_supply, 2),
        "final_supply": round(final_supply, 2),
        "shortfall": round(shortfall, 2),
        "renewable_ratio": round(renewable_ratio, 2),
        "system_efficiency": round(system_efficiency, 2),
        "grid_dependency": round(grid_dependency, 2),
        "battery_levels": round(battery_remaining, 2),
        "battery_used": round(battery_used, 2),
        "curtailed_energy": round(curtailed_energy, 2),
        "resilience_score": round(resilience_score, 2),
        "mix": {
            "solar": round(supply["solar"], 2),
            "wind": round(supply["wind"], 2),
            "geothermal": round(supply["geothermal"], 2),
            "hydro": round(supply["hydro"], 2),
            "battery_support": round(battery_used, 2),
            "grid_support": round(grid_needed, 2),
        },
        "scenario_desc": sc["desc"],
    }


def compare_all_scenarios(inp: SimulationInputs, city_meta: Dict) -> pd.DataFrame:
    rows = []
    for key, meta in SCENARIOS.items():
        temp_inp = SimulationInputs(**{**inp.__dict__, "scenario_key": key})
        out = simulate(temp_inp, city_meta)
        rows.append(
            {
                "Scenario": meta["label"],
                "Demand (MW)": out["demand"],
                "Renewable Supply (MW)": out["renewable_supply"],
                "Final Supply (MW)": out["final_supply"],
                "Shortfall (MW)": out["shortfall"],
                "Renewable Ratio (%)": out["renewable_ratio"],
                "Grid Dependency (%)": out["grid_dependency"],
                "Battery Remaining (MWh)": out["battery_levels"],
                "Resilience Score": out["resilience_score"],
            }
        )
    return pd.DataFrame(rows)


def make_recommendation(out: Dict, inp: SimulationInputs) -> List[str]:
    recs = []
    if out["shortfall"] > 0:
        recs.append("Increase dispatchable backup or add more battery reserve; current supply does not fully meet demand.")
    if out["grid_dependency"] > 30:
        recs.append("Grid dependency is high. Consider increasing local renewable capacity or storage to reduce external reliance.")
    if out["renewable_ratio"] < 60:
        recs.append("Renewable ratio is below target. Solar/wind mix or geothermal/hydro balancing should be improved.")
    if inp.scenario_key in {"typhoon", "storm", "blizzard"}:
        recs.append("For severe-weather scenarios, prioritize critical-load logic, staged recovery, and reserve capacity buffers.")
    if out["battery_levels"] < inp.battery_capacity * 0.25:
        recs.append("Battery reserve is low after dispatch. Add storage or reduce peak demand stress through load shifting.")
    if not recs:
        recs.append("System is stable under current assumptions. Next step: compare against a harsher scenario and export the audit trail.")
    return recs


# -----------------------------
# UI
# -----------------------------
def render_mix_chart(mix: Dict[str, float]):
    df = pd.DataFrame({"Source": list(mix.keys()), "MW": list(mix.values())})
    st.bar_chart(df.set_index("Source"))

    if MATPLOTLIB_OK:
        positive = df[df["MW"] > 0]
        if not positive.empty:
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.pie(positive["MW"], labels=positive["Source"], autopct="%1.1f%%")
            ax.set_title("Energy Mix")
            st.pyplot(fig, clear_figure=True)


def render_metric_cards(out: Dict):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Demand (MW)", out["demand"])
    c2.metric("Renewable Supply (MW)", out["renewable_supply"])
    c3.metric("Final Supply (MW)", out["final_supply"])
    c4.metric("Shortfall (MW)", out["shortfall"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Renewable Ratio (%)", out["renewable_ratio"])
    c6.metric("System Efficiency (%)", out["system_efficiency"])
    c7.metric("Grid Dependency (%)", out["grid_dependency"])
    c8.metric("Battery Remaining (MWh)", out["battery_levels"])


# -----------------------------
# Main app
# -----------------------------
def main():
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []

    with st.sidebar:
        language = st.selectbox("Language / 語言", list(LANG.keys()), index=0)
        txt = LANG[language]

        countries = list(CITY_DATA.keys())
        country = st.selectbox("Country", countries, index=0)
        cities = list(CITY_DATA[country].keys())
        city = st.selectbox("City", cities, index=0)
        city_meta = CITY_DATA[country][city]

        population = st.slider("Population", 1_000, 10_000_000, 500_000, step=1_000)
        solar_capacity = st.slider("Solar Capacity (MW)", 0, 2_000, 120, step=10)
        wind_capacity = st.slider("Wind Capacity (MW)", 0, 2_000, 80, step=10)
        geothermal_capacity = st.slider("Geothermal Capacity (MW)", 0, 2_000, 60, step=10)
        hydro_capacity = st.slider("Hydropower Capacity (MW)", 0, 2_000, 70, step=10)
        battery_capacity = st.slider("Battery Capacity (MWh)", 0, 5_000, 300, step=25)

        st.markdown("---")
        weather_status = st.selectbox(txt["weather_status"], WEATHER_STATUS, index=0)
        temperature = st.slider("Temperature (°C)", -20, 50, safe_int(city_meta["temperature"], 25), step=1)
        wind_speed = st.slider("Wind Speed (m/s)", 0.0, 25.0, float(city_meta["wind_speed"]), step=0.1)
        solar_radiation = st.slider("Solar Radiation (kWh/m²/day)", 0.0, 10.0, float(city_meta["solar_radiation"]), step=0.1)
        precipitation = st.slider("Precipitation (mm/hr eq.)", 0.0, 20.0, float(city_meta["precipitation"]), step=0.1)
        humidity = st.slider("Humidity (%)", 0, 100, safe_int(city_meta["humidity"], 70), step=1)

        scenario_key = st.selectbox(txt["scenario"], list(SCENARIOS.keys()), format_func=lambda k: SCENARIOS[k]["label"])
        run = st.button(txt["run"], type="primary", use_container_width=True)

    txt = LANG[language]
    st.title(txt["title"])
    st.caption(txt["subtitle"])
    st.info(txt["main_desc"])

    st.subheader(f"Country Logic: {country}")
    st.write(CITY_DATA[country][city].get("logic", "No country logic available."))

    st.subheader(f"City Profile: {city}")
    left, right = st.columns([2, 3])
    with left:
        st.write(f"Latitude: {city_meta['lat']}")
        st.write(f"Longitude: {city_meta['lon']}")
        st.write(f"Country Model: {city_meta.get('country_model', 'unknown')}")
    with right:
        st.success(f"{txt['weather_status']}: {weather_status}")

    inp = SimulationInputs(
        country_key=country,
        city_key=city,
        lat=city_meta["lat"],
        lon=city_meta["lon"],
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
        scenario_key=scenario_key,
    )

    clean_inp, fixes = validate_inputs(inp)
    if fixes:
        st.warning(txt["fix_inputs"])
    else:
        st.success(txt["inputs_ok"])

    # always compute to keep app responsive even without button press
    try:
        baseline_inp = SimulationInputs(**{**clean_inp.__dict__, "scenario_key": "normal"})
        baseline_out = simulate(baseline_inp, city_meta)
        scenario_out = simulate(clean_inp, city_meta)
        all_df = compare_all_scenarios(clean_inp, city_meta)
        recommendations = make_recommendation(scenario_out, clean_inp)
    except Exception as e:
        st.error(f"Simulation failed safely: {e}")
        st.stop()

    if run:
        add_audit_log(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "country": clean_inp.country_key,
                "city": clean_inp.city_key,
                "scenario": clean_inp.scenario_key,
                "demand": scenario_out["demand"],
                "final_supply": scenario_out["final_supply"],
                "shortfall": scenario_out["shortfall"],
                "recommendation_count": len(recommendations),
            }
        )
        st.toast("Simulation completed and saved to audit trail.")

    st.markdown("---")
    st.subheader(txt["summary"])
    render_metric_cards(scenario_out)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Baseline vs Current Scenario")
        cmp_df = pd.DataFrame(
            {
                "Metric": [
                    "Demand (MW)",
                    "Renewable Supply (MW)",
                    "Final Supply (MW)",
                    "Shortfall (MW)",
                    "Renewable Ratio (%)",
                    "Grid Dependency (%)",
                    "Resilience Score",
                ],
                txt["baseline"]: [
                    baseline_out["demand"],
                    baseline_out["renewable_supply"],
                    baseline_out["final_supply"],
                    baseline_out["shortfall"],
                    baseline_out["renewable_ratio"],
                    baseline_out["grid_dependency"],
                    baseline_out["resilience_score"],
                ],
                SCENARIOS[clean_inp.scenario_key]["label"]: [
                    scenario_out["demand"],
                    scenario_out["renewable_supply"],
                    scenario_out["final_supply"],
                    scenario_out["shortfall"],
                    scenario_out["renewable_ratio"],
                    scenario_out["grid_dependency"],
                    scenario_out["resilience_score"],
                ],
            }
        )
        st.dataframe(cmp_df, use_container_width=True, hide_index=True)

    with c2:
        st.markdown("### Energy Mix")
        render_mix_chart(scenario_out["mix"])

    st.markdown("### All Scenario Comparison")
    st.dataframe(all_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader(txt["recommendation"])
    st.write(scenario_out["scenario_desc"])
    for i, rec in enumerate(recommendations, start=1):
        st.write(f"{i}. {rec}")

    st.markdown("---")
    st.subheader(txt["risk"])
    st.warning(
        "TAIVAS is a decision-support simulator, not an unconditional guarantee. "
        "All outputs depend on assumptions, simplified formulas, and user inputs. "
        "For operational use, log inputs/outputs, compare baseline vs AI-recommended settings, "
        "and keep a human review step before any real-world action."
    )

    st.markdown("---")
    st.subheader(txt["audit"])
    if st.session_state.audit_log:
        st.dataframe(pd.DataFrame(st.session_state.audit_log), use_container_width=True, hide_index=True)
        csv = pd.DataFrame(st.session_state.audit_log).to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Download audit trail CSV",
            data=csv,
            file_name="taivas_audit_trail.csv",
            mime="text/csv",
        )
    else:
        st.caption("No audit entries yet. Click 'Run simulation' to store a checkpoint.")


if __name__ == "__main__":
    main()
