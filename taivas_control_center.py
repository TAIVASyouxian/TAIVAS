from io import StringIO

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

SCENARIOS = {
    "normal": {"demand": 1.00, "solar": 1.00, "wind": 1.00, "hydro": 1.00, "geo": 1.00, "battery": 1.00},
    "heat_wave": {"demand": 1.22, "solar": 1.08, "wind": 0.90, "hydro": 0.93, "geo": 1.00, "battery": 0.96},
    "storm": {"demand": 1.10, "solar": 0.62, "wind": 1.20, "hydro": 1.05, "geo": 1.00, "battery": 0.90},
    "cold_wave": {"demand": 1.18, "solar": 0.72, "wind": 0.96, "hydro": 0.97, "geo": 1.00, "battery": 0.93},
    "blizzard": {"demand": 1.28, "solar": 0.40, "wind": 0.82, "hydro": 0.90, "geo": 1.00, "battery": 0.85},
    "typhoon": {"demand": 1.15, "solar": 0.35, "wind": 0.68, "hydro": 0.78, "geo": 1.00, "battery": 0.82},
}

SCENARIO_LIBRARY = {
    "Balanced Baseline": {
        "scenario_key": "normal",
        "energy_security_scenario": "normal",
        "temperature": 24,
        "wind_speed": 5.0,
        "solar_radiation": 650,
        "precipitation": 10,
        "humidity": 70,
        "import_dependency": 0.60,
        "strategic_reserve_days": 20,
        "critical_load_share": 0.35,
        "shipping_dependency": 0.65,
        "infrastructure_damage_ratio": 0.05,
        "primary_supply_failure_ratio": 0.15,
        "reserve_energy_per_day": 120.0,
    },
    "Winter Blizzard Stress": {
        "scenario_key": "blizzard",
        "energy_security_scenario": "high_risk",
        "temperature": -8,
        "wind_speed": 8.0,
        "solar_radiation": 180,
        "precipitation": 40,
        "humidity": 78,
        "import_dependency": 0.72,
        "strategic_reserve_days": 16,
        "critical_load_share": 0.42,
        "shipping_dependency": 0.82,
        "infrastructure_damage_ratio": 0.18,
        "primary_supply_failure_ratio": 0.35,
        "reserve_energy_per_day": 130.0,
    },
    "Import Disruption": {
        "scenario_key": "storm",
        "energy_security_scenario": "severe_disruption",
        "temperature": 19,
        "wind_speed": 7.0,
        "solar_radiation": 420,
        "precipitation": 20,
        "humidity": 76,
        "import_dependency": 0.88,
        "strategic_reserve_days": 10,
        "critical_load_share": 0.40,
        "shipping_dependency": 0.92,
        "infrastructure_damage_ratio": 0.12,
        "primary_supply_failure_ratio": 0.28,
        "reserve_energy_per_day": 110.0,
    },
    "Heat + Supply Shock": {
        "scenario_key": "heat_wave",
        "energy_security_scenario": "high_risk",
        "temperature": 35,
        "wind_speed": 3.0,
        "solar_radiation": 900,
        "precipitation": 2,
        "humidity": 78,
        "import_dependency": 0.80,
        "strategic_reserve_days": 12,
        "critical_load_share": 0.38,
        "shipping_dependency": 0.75,
        "infrastructure_damage_ratio": 0.08,
        "primary_supply_failure_ratio": 0.22,
        "reserve_energy_per_day": 125.0,
    },
}

CRITICAL_LOAD_SPLITS = {
    "Medical": 0.30,
    "Heating/Cooling": 0.30,
    "Communications": 0.18,
    "Water Systems": 0.22,
}

LAYER_SUMMARY = [
    ("Core Simulator", "Models demand, renewable supply, battery support, failure ratios, reserve planning, and survival timeline."),
    ("Decision Support", "Explains risk signals, compares scenarios, and structures recommendations as reason chains."),
    ("Concept Lab", "Explores thermal and resilience concepts as linked visuals for simulation, not hardware blueprints."),
]

PAGE_QUESTIONS = {
    "Energy Mix": "What is the system actually running on, and how different is actual supply from installed capacity?",
    "Scenario Comparison": "How much better or worse is the selected scenario versus baseline and other scenarios?",
    "Stress Test": "Which subsystems fail first, and how badly does component degradation reduce resilience?",
    "AI Recommendation": "Why is the model concerned, and what action should be prioritized first?",
    "Energy Security": "How much do import exposure, shipping dependence, and reserve lag increase risk?",
    "Survival Timeline": "If supply is disrupted, how long can the system operate before shortfall and critical failure?",
    "Concept Lab": "If advanced thermal concepts are introduced, which resilience metrics improve and by how much?",
}

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.1rem; padding-bottom: 2rem;}
    .hero {
        padding: 1rem 1.1rem;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(21,60,110,0.60), rgba(11,18,32,0.24));
        margin-bottom: 1rem;
    }
    .hero h3 { margin: 0 0 0.35rem 0; font-size: 1.24rem; }
    .hero p { margin: 0; opacity: 0.94; line-height: 1.58; }
    .note {
        padding: 0.82rem 0.95rem;
        border-radius: 14px;
        background: rgba(59,130,246,0.10);
        border: 1px solid rgba(96,165,250,0.24);
        margin-bottom: 0.75rem;
    }
    .question {
        padding: 0.8rem 0.95rem;
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
    .card-label { font-size: 0.82rem; opacity: 0.78; margin-bottom: 0.3rem; }
    .card-value { font-size: 1.02rem; font-weight: 600; line-height: 1.32; }
    .layer-box {
        padding: 0.82rem 0.92rem;
        border-radius: 14px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.10);
        min-height: 108px;
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
    """,
    unsafe_allow_html=True,
)

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
            return "Critical"
        if value <= warn:
            return "Watch"
        return "Stable"
    if value >= critical:
        return "Critical"
    if value >= warn:
        return "Watch"
    return "Stable"

def mini_card(label: str, value: str):
    st.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)

def page_question(key: str):
    st.markdown(f'<div class="question"><b>This page answers:</b> {PAGE_QUESTIONS[key]}</div>', unsafe_allow_html=True)

def concept_badge():
    st.markdown('<div class="badge">Conceptual Simulation • Not hardware-validated</div>', unsafe_allow_html=True)

def scenario_delta_df(baseline: dict, selected: dict) -> pd.DataFrame:
    metrics = [
        ("Demand (MW)", baseline["demand"], selected["demand"]),
        ("Renewable Supply (MW)", baseline["renewable_supply"], selected["renewable_supply"]),
        ("Final Supply (MW)", baseline["final_supply"], selected["final_supply"]),
        ("Shortfall (MW)", baseline["shortfall"], selected["shortfall"]),
        ("Renewable Ratio (%)", baseline["renewable_ratio"], selected["renewable_ratio"]),
        ("System Efficiency (%)", baseline["system_efficiency"], selected["system_efficiency"]),
        ("Grid Dependency (%)", baseline["grid_dependency"], selected["grid_dependency"]),
    ]
    rows = []
    for name, base, new in metrics:
        rows.append({"Metric": name, "Baseline": round(base, 2), "Selected": round(new, 2), "Delta": round(new - base, 2)})
    return pd.DataFrame(rows)

def reason_chain(results: dict, energy_security_scenario: str, timeline_results: dict) -> list[dict]:
    chain = []
    if results["shortfall"] > 0:
        chain.append({"Signal": f"Shortfall remains at {results['shortfall']:.2f} MW",
                      "Impact": "Demand is still above available modeled supply.",
                      "Action": "Raise firm capacity, storage dispatch, or lower protected demand.",
                      "Expected effect": "Reduce unmet load and delay degradation."})
    else:
        chain.append({"Signal": "No modeled shortfall in the selected scenario",
                      "Impact": "Immediate supply-demand balance is stable under current assumptions.",
                      "Action": "Preserve reserve margin and monitor exposure.",
                      "Expected effect": "Keep headroom for deterioration."})
    if results["renewable_ratio"] < 70:
        chain.append({"Signal": f"Renewable ratio is {results['renewable_ratio']:.1f}%",
                      "Impact": "System depends more on backup support or external stability.",
                      "Action": "Diversify renewable mix or improve thermal/storage smoothing.",
                      "Expected effect": "Raise renewable coverage and lower reserve stress."})
    if results.get("reserve_days_remaining", 0) < 7:
        chain.append({"Signal": f"Reserve days remaining are {results.get('reserve_days_remaining', 0)}",
                      "Impact": "Reserve exhaustion could happen before logistics recover.",
                      "Action": "Increase reserve depth or reduce recovery lag dependence.",
                      "Expected effect": "Extend endurance during prolonged disruption."})
    if timeline_results["hours_until_critical_failure"] != "No Failure":
        chain.append({"Signal": f"Critical failure projected at hour {timeline_results['hours_until_critical_failure']}",
                      "Impact": "Core services may collapse if stress persists.",
                      "Action": "Reduce non-critical load and strengthen core protection.",
                      "Expected effect": "Push failure later and preserve critical operations."})
    if energy_security_scenario != "normal":
        chain.append({"Signal": f"Security scenario is '{energy_security_scenario.replace('_', ' ')}'",
                      "Impact": "Import, shipping, and infrastructure assumptions are degrading resilience.",
                      "Action": "Reduce import exposure and review logistics bottlenecks.",
                      "Expected effect": "Lower disruption score and improve reserve survivability."})
    return chain

def critical_load_breakdown(total_demand: float, critical_share: float) -> pd.DataFrame:
    critical_total = total_demand * critical_share
    return pd.DataFrame({"Category": list(CRITICAL_LOAD_SPLITS.keys()),
                         "Critical Demand (MW)": [round(critical_total * w, 2) for w in CRITICAL_LOAD_SPLITS.values()]})

def comparison_dataframe(inputs, failure_ratios: dict, reserve_recovery_lag_days: int):
    rows = []
    for key in SCENARIOS.keys():
        r = compute_energy_supply(inputs, key, failure_ratios, reserve_recovery_lag_days)
        rows.append({"Scenario": key.replace("_", " ").title(),
                     "Demand (MW)": r["demand"],
                     "Renewable Supply (MW)": r["renewable_supply"],
                     "Final Supply (MW)": r["final_supply"],
                     "Shortfall (MW)": r["shortfall"],
                     "Renewable Ratio (%)": r["renewable_ratio"],
                     "System Efficiency (%)": r["system_efficiency"],
                     "Grid Dependency (%)": r["grid_dependency"]})
    return pd.DataFrame(rows)

def export_text_summary(results: dict, timeline_results: dict, selected_country: str, selected_city: str, weather_scenario: str, security_scenario: str) -> str:
    lines = [
        "TAIVAS Scenario Summary",
        f"Location: {selected_country} / {selected_city}",
        f"Weather scenario: {weather_scenario}",
        f"Energy security scenario: {security_scenario}",
        f"Demand: {results['demand']} MW",
        f"Renewable supply: {results['renewable_supply']} MW",
        f"Final supply: {results['final_supply']} MW",
        f"Shortfall: {results['shortfall']} MW",
        f"Renewable ratio: {results['renewable_ratio']}%",
        f"System efficiency: {results['system_efficiency']}%",
        f"Grid dependency: {results['grid_dependency']}%",
        f"Reserve days remaining: {results.get('reserve_days_remaining', 0)}",
        f"Hours until shortfall: {timeline_results['hours_until_shortfall']}",
        f"Hours until critical failure: {timeline_results['hours_until_critical_failure']}",
    ]
    return "\n".join(lines)

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

def thermal_concept_adjustment(enabled, demand, reserve_days_remaining, hours_until_shortfall, hours_until_critical_failure,
                              fresh_air_temp_c, exhaust_air_temp_c, recovery_efficiency,
                              buffer_state_pct, sink_utilization_pct, damage_ratio_pct, diversification_score):
    if not enabled:
        return {
            "adjusted_demand": demand,
            "adjusted_reserve_days": reserve_days_remaining,
            "adjusted_hours_until_shortfall": hours_until_shortfall,
            "adjusted_hours_until_critical_failure": hours_until_critical_failure,
            "thermal_demand_reduction_pct": 0.0,
            "delivered_supply_temp_c": fresh_air_temp_c,
            "buffer_state_pct": buffer_state_pct,
            "sink_utilization_pct": sink_utilization_pct,
            "damage_ratio_pct": damage_ratio_pct,
            "diversification_score": diversification_score,
        }

    thermal_gradient = max(exhaust_air_temp_c - fresh_air_temp_c, 0.0)
    thermal_demand_reduction_pct = clamp((thermal_gradient / 40.0) * recovery_efficiency * 0.28, 0.0, 0.22)
    adjusted_demand = round(demand * (1.0 - thermal_demand_reduction_pct), 2)
    reserve_bonus_days = round(thermal_demand_reduction_pct * 9.0, 2)
    shortfall_bonus_hours = int(round(thermal_demand_reduction_pct * 36.0))
    critical_bonus_hours = int(round(thermal_demand_reduction_pct * 42.0))

    return {
        "adjusted_demand": adjusted_demand,
        "adjusted_reserve_days": round(reserve_days_remaining + reserve_bonus_days, 2),
        "adjusted_hours_until_shortfall": hours_until_shortfall + shortfall_bonus_hours,
        "adjusted_hours_until_critical_failure": hours_until_critical_failure + critical_bonus_hours,
        "thermal_demand_reduction_pct": round(thermal_demand_reduction_pct * 100, 2),
        "delivered_supply_temp_c": round(fresh_air_temp_c + (exhaust_air_temp_c - fresh_air_temp_c) * recovery_efficiency, 2),
        "buffer_state_pct": round(clamp(buffer_state_pct + thermal_demand_reduction_pct * 45, 0, 100), 1),
        "sink_utilization_pct": round(clamp(sink_utilization_pct + recovery_efficiency * 12, 0, 100), 1),
        "damage_ratio_pct": round(clamp(damage_ratio_pct * (1 - thermal_demand_reduction_pct * 0.35), 0, 100), 1),
        "diversification_score": round(clamp(diversification_score + thermal_demand_reduction_pct * 20, 0, 100), 1),
    }

def render_capacity_factor_chart(capacity_factors: dict):
    labels = list(capacity_factors.keys())
    values = [capacity_factors[k] for k in labels]
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    ax.barh(labels, values)
    ax.set_xlabel("Capacity Factor (%)")
    ax.set_xlim(0, 100)
    ax.set_title("Capacity Factors")
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)

def render_delta_chart(delta_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9.0, 4.2))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    ax.barh(delta_df["Metric"], delta_df["Delta"])
    ax.axvline(0, linewidth=1.0)
    ax.set_title("Selected Scenario Delta vs Baseline")
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)

def render_critical_load_chart(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    ax.bar(df["Category"], df["Critical Demand (MW)"])
    ax.set_ylabel("Critical Demand (MW)")
    ax.set_title("Critical Load Protection Profile")
    ax.grid(axis="y", alpha=0.22)
    plt.xticks(rotation=15)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)

st.title("TAIVAS Energy Control Center")
st.caption("TAIVAS is a resilience decision-support simulator for energy, thermal, and critical facility scenarios under extreme conditions.")

with st.sidebar:
    st.header("Controls")
    country = st.selectbox("Country", list(CITY_DATA.keys()))
    city = st.selectbox("City", list(CITY_DATA[country].keys()))
    city_profile = CITY_DATA[country][city]

    preset_name = st.selectbox("Scenario Library Preset", ["Custom"] + list(SCENARIO_LIBRARY.keys()), index=0)
    preset = SCENARIO_LIBRARY.get(preset_name, {})

    population = st.slider("Population", 10000, 5000000, int(city_profile["population"]), step=10000)
    st.caption(f"Selected population: {population:,}")

    st.divider()
    st.subheader("Capacity Inputs")
    solar_capacity = st.slider("Solar Capacity", 0, 500, 120, 5)
    wind_capacity = st.slider("Wind Capacity", 0, 500, 80, 5)
    geothermal_capacity = st.slider("Geothermal Capacity", 0, 500, 60, 5)
    hydro_capacity = st.slider("Hydro Capacity", 0, 500, 70, 5)
    battery_capacity = st.slider("Battery Capacity", 0, 1000, 180, 10)

    st.divider()
    st.subheader("Weather Inputs")
    temperature = st.slider("Temperature (°C)", -20, 50, int(preset.get("temperature", 26)), 1)
    wind_speed = st.slider("Wind Speed (m/s)", 0.0, 30.0, float(preset.get("wind_speed", 4.2)), 0.1)
    solar_radiation = st.slider("Solar Radiation (W/m²)", 0, 1200, int(preset.get("solar_radiation", 640)), 10)
    precipitation = st.slider("Precipitation (mm)", 0, 300, int(preset.get("precipitation", 12)), 1)
    humidity = st.slider("Humidity (%)", 0, 100, int(preset.get("humidity", 73)), 1)

    st.divider()
    scenario_key = st.selectbox("Weather Scenario", list(SCENARIOS.keys()), index=list(SCENARIOS.keys()).index(preset.get("scenario_key", "normal")))

    st.divider()
    st.subheader("Stress Inputs")
    solar_failure_ratio = st.number_input("Solar Failure Ratio", 0.0, 1.0, 0.00, 0.05, format="%.2f")
    wind_failure_ratio = st.number_input("Wind Failure Ratio", 0.0, 1.0, 0.00, 0.05, format="%.2f")
    geothermal_failure_ratio = st.number_input("Geothermal Failure Ratio", 0.0, 1.0, 0.00, 0.05, format="%.2f")
    hydro_failure_ratio = st.number_input("Hydro Failure Ratio", 0.0, 1.0, 0.00, 0.05, format="%.2f")
    battery_failure_ratio = st.number_input("Battery Failure Ratio", 0.0, 1.0, 0.00, 0.05, format="%.2f")

    st.divider()
    st.subheader("Energy Security Inputs")
    energy_security_options = list(ENERGY_SECURITY_SCENARIOS.keys())
    default_security = preset.get("energy_security_scenario", energy_security_options[0])
    energy_security_scenario = st.selectbox("Energy Security Scenario", energy_security_options, index=energy_security_options.index(default_security) if default_security in energy_security_options else 0)
    import_dependency = st.number_input("Import Dependency", 0.0, 1.0, float(preset.get("import_dependency", 0.70)), 0.01, format="%.2f")
    strategic_reserve_days = st.number_input("Strategic Reserve Days", 0, 365, int(preset.get("strategic_reserve_days", 20)), 1)
    critical_load_share = st.number_input("Critical Load Share", 0.0, 1.0, float(preset.get("critical_load_share", 0.35)), 0.01, format="%.2f")
    shipping_dependency = st.number_input("Shipping Dependency", 0.0, 1.0, float(preset.get("shipping_dependency", 0.85)), 0.01, format="%.2f")
    infrastructure_damage_ratio = st.number_input("Infrastructure Damage Ratio", 0.0, 1.0, float(preset.get("infrastructure_damage_ratio", 0.10)), 0.01, format="%.2f")
    reserve_recovery_lag_days = st.number_input("Reserve Recovery Lag (days)", 0, 30, 3, 1)

    st.divider()
    st.subheader("Survival Timeline Inputs")
    simulation_hours = st.selectbox("Simulation Hours", [24, 72, 168], index=0)
    primary_supply_failure_ratio = st.number_input("Primary Supply Failure Ratio", 0.0, 1.0, float(preset.get("primary_supply_failure_ratio", 0.30)), 0.01, format="%.2f")
    reserve_energy_per_day = st.number_input("Reserve Energy per Day", 20.0, 300.0, float(preset.get("reserve_energy_per_day", 120.0)), 5.0, format="%.1f")
    survival_mode = st.selectbox("Survival Mode", ["full_load", "critical_load_only"], index=0)

    st.divider()
    st.subheader("Thermal Concept Inputs")
    thermal_concept_enabled = st.toggle("Enable Thermal Concept Mode", value=True)
    fresh_air_temp_c = st.slider("Outside Air (°C)", -30.0, 20.0, -8.0, 0.5)
    exhaust_air_temp_c = st.slider("Indoor Exhaust Air (°C)", 10.0, 35.0, 23.0, 0.5)
    recovery_efficiency = st.slider("Thermal Recovery Efficiency", 0.0, 1.0, 0.72, 0.01)
    thermal_animation_speed = st.slider("Thermal Animation Speed", 0.4, 2.5, 1.0, 0.1)

failure_ratios = {"solar": solar_failure_ratio, "wind": wind_failure_ratio, "geothermal": geothermal_failure_ratio, "hydro": hydro_failure_ratio, "battery": battery_failure_ratio}

inputs = {
    "country_key": country, "city_key": city, "lat": city_profile["lat"], "lon": city_profile["lon"],
    "temperature": temperature, "wind_speed": wind_speed, "solar_radiation": solar_radiation,
    "precipitation": precipitation, "humidity": humidity, "population": population,
    "solar_capacity": solar_capacity, "wind_capacity": wind_capacity, "geothermal_capacity": geothermal_capacity,
    "hydro_capacity": hydro_capacity, "battery_capacity": battery_capacity,
}

results = compute_energy_supply(inputs, scenario_key, failure_ratios, reserve_recovery_lag_days)
results, energy_security_profile = apply_energy_security_layer(
    base_results=results,
    scenario_key=energy_security_scenario,
    import_dependency=import_dependency,
    strategic_reserve_days=strategic_reserve_days,
    critical_load_share=critical_load_share,
    shipping_dependency=shipping_dependency,
    infrastructure_damage_ratio=infrastructure_damage_ratio,
    reserve_recovery_lag_days=reserve_recovery_lag_days,
)

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

base_damage_pct = round((sum(failure_ratios.values()) / len(failure_ratios)) * 100, 1)
base_div_score = round(len([v for v in results["actual_mix_mw"].values() if v > 0]) / 4 * 100, 1)
thermal_results = thermal_concept_adjustment(
    enabled=thermal_concept_enabled,
    demand=results["demand"],
    reserve_days_remaining=results.get("reserve_days_remaining", 0),
    hours_until_shortfall=timeline_results["hours_until_shortfall"] if timeline_results["hours_until_shortfall"] != "No Failure" else 999,
    hours_until_critical_failure=timeline_results["hours_until_critical_failure"] if timeline_results["hours_until_critical_failure"] != "No Failure" else 999,
    fresh_air_temp_c=fresh_air_temp_c,
    exhaust_air_temp_c=exhaust_air_temp_c,
    recovery_efficiency=recovery_efficiency,
    buffer_state_pct=70.0,
    sink_utilization_pct=clamp(results["renewable_ratio"], 10, 95),
    damage_ratio_pct=base_damage_pct,
    diversification_score=base_div_score,
)

scenario_df = comparison_dataframe(inputs, failure_ratios, reserve_recovery_lag_days)
timeline_df = pd.DataFrame(timeline_results["rows"])
delta_df = scenario_delta_df(baseline_results, results)
critical_load_df = critical_load_breakdown(results["demand"], critical_load_share)
reason_df = pd.DataFrame(reason_chain(results, energy_security_scenario, timeline_results))

mix_table = pd.DataFrame(
    {
        "Source": list(results["actual_mix_mw"].keys()),
        "Installed Capacity (MW)": [results["installed_mix_mw"][k] for k in results["actual_mix_mw"]],
        "Actual Supply (MW)": [results["actual_mix_mw"][k] for k in results["actual_mix_mw"]],
        "Installed Mix (%)": [round(results["installed_mix_pct"][k], 2) for k in results["actual_mix_mw"]],
        "Actual Mix (%)": [round(results["actual_mix_pct"][k], 2) for k in results["actual_mix_mw"]],
        "Capacity Factor (%)": [results["capacity_factors"][k] for k in results["actual_mix_mw"]],
    }
)

status_shortfall = build_status_label(results["shortfall"], (5, 15))
status_efficiency = build_status_label(results["system_efficiency"], (85, 70), reverse=True)
status_grid = build_status_label(results["grid_dependency"], (10, 25))
status_reserve = build_status_label(results.get("reserve_days_remaining", 0), (14, 7), reverse=True)

scenario_summary_text = export_text_summary(results, timeline_results, country, city, scenario_key, energy_security_scenario)
buf1 = StringIO(); scenario_df.to_csv(buf1, index=False)
buf2 = StringIO(); reason_df.to_csv(buf2, index=False)
buf3 = StringIO(); delta_df.to_csv(buf3, index=False)

st.markdown(
    """
    <div class="hero">
        <h3>Operational Overview</h3>
        <p>TAIVAS combines a core resilience simulator, an explainable decision-support layer, and a concept lab for advanced thermal ideas. It is designed to test how energy, thermal management, and critical facility protection behave under extreme climate and disruption scenarios.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

layer_cols = st.columns(3)
for col, (name, desc) in zip(layer_cols, LAYER_SUMMARY):
    with col:
        st.markdown(f'<div class="layer-box"><div class="card-label">{name}</div><div class="card-value" style="font-size:0.98rem;">{desc}</div></div>', unsafe_allow_html=True)

overview_col, summary_col = st.columns([1.05, 1.1])

with overview_col:
    st.subheader(f"Country Logic: {country}")
    st.write(COUNTRY_NOTES.get(country, "Regional energy model loaded."))
    st.subheader(f"City Profile: {city}")
    geo_a, geo_b, geo_c = st.columns(3)
    with geo_a:
        mini_card("Latitude", f"{city_profile['lat']}")
    with geo_b:
        mini_card("Longitude", f"{city_profile['lon']}")
    with geo_c:
        mini_card("Country Model", city_profile["country_model"])

with summary_col:
    st.subheader("Input Summary")
    sum_a, sum_b = st.columns(2)
    with sum_a:
        mini_card("Country", country)
        mini_card("City", city)
        mini_card("Population", f"{population:,}")
        mini_card("Weather Scenario", scenario_key.replace("_", " ").title())
    with sum_b:
        mini_card("Energy Security", energy_security_scenario.replace("_", " ").title())
        mini_card("Import Dependency", f"{import_dependency * 100:.0f}%")
        mini_card("Reserve Days", f"{strategic_reserve_days} days")
        mini_card("Timeline Horizon", f"{simulation_hours} hours")

st.subheader("System Performance")
perf_top = st.columns(4)
perf_top[0].metric("Demand", f"{results['demand']} MW", delta=f"{round(results['demand'] - baseline_results['demand'], 2)} vs baseline")
perf_top[1].metric("Renewable Supply", f"{results['renewable_supply']} MW", delta=f"{round(results['renewable_supply'] - baseline_results['renewable_supply'], 2)}")
perf_top[2].metric("Final Supply", f"{results['final_supply']} MW", delta=f"{round(results['final_supply'] - baseline_results['final_supply'], 2)}")
perf_top[3].metric("Shortfall", f"{results['shortfall']} MW", delta=f"{round(results['shortfall'] - baseline_results['shortfall'], 2)}")

st.subheader("Resilience Indicators")
perf_bottom = st.columns(4)
perf_bottom[0].metric("Battery Levels", f"{results['battery_levels']} MWh")
perf_bottom[1].metric("Renewable Ratio", f"{results['renewable_ratio']}%")
perf_bottom[2].metric("System Efficiency", f"{results['system_efficiency']}%")
perf_bottom[3].metric("Grid Dependency", f"{results['grid_dependency']}%")

status_cols = st.columns(4)
status_cols[0].metric("Shortfall Status", status_shortfall)
status_cols[1].metric("Efficiency Status", status_efficiency)
status_cols[2].metric("Grid Stress Status", status_grid)
status_cols[3].metric("Reserve Status", status_reserve)

export_cols = st.columns(3)
with export_cols[0]:
    st.download_button("Scenario CSV", buf1.getvalue(), file_name="taivas_scenario_comparison.csv", mime="text/csv")
with export_cols[1]:
    st.download_button("Reason Chain CSV", buf2.getvalue(), file_name="taivas_reason_chain.csv", mime="text/csv")
with export_cols[2]:
    st.download_button("Summary TXT", scenario_summary_text, file_name="taivas_summary.txt", mime="text/plain")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["Energy Mix", "Scenario Comparison", "Stress Test", "AI Recommendation", "Energy Security", "Survival Timeline", "Concept Lab"]
)

with tab1:
    page_question("Energy Mix")
    st.markdown('<div class="note">This tab separates configured capacity from actual modeled renewable output under the selected weather, scenario, and failure assumptions.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Installed Capacity Mix")
        st.pyplot(make_donut_chart(results["installed_mix_pct"], 100.0, title="Installed Capacity Mix"), clear_figure=True)
    with c2:
        st.subheader("Actual Renewable Supply Mix")
        st.pyplot(make_donut_chart(results["actual_mix_pct"], results["renewable_ratio"], title="Actual Renewable Supply Mix"), clear_figure=True)
    st.subheader("Energy Source Table")
    st.dataframe(mix_table, use_container_width=True, hide_index=True)
    st.subheader("Capacity Factors")
    render_capacity_factor_chart(results["capacity_factors"])
    st.caption(f"Dominant modeled renewable source: {results['dominant_source']}")

with tab2:
    page_question("Scenario Comparison")
    left, right = st.columns([1.02, 1.0])
    with left:
        st.subheader("Baseline vs Selected Scenario")
        st.dataframe(delta_df, use_container_width=True, hide_index=True)
        render_delta_chart(delta_df)
    with right:
        st.subheader("All Weather Scenarios")
        st.dataframe(scenario_df, use_container_width=True, hide_index=True)
        st.bar_chart(scenario_df.set_index("Scenario")[["Shortfall (MW)", "Grid Dependency (%)"]])
    st.subheader("Critical Load Breakdown")
    render_critical_load_chart(critical_load_df)
    st.dataframe(critical_load_df, use_container_width=True, hide_index=True)

with tab3:
    page_question("Stress Test")
    st.markdown('<div class="note">This tab focuses on multi-failure stress testing and shows where the resilience model is being degraded by component-level availability loss.</div>', unsafe_allow_html=True)
    stress_df = pd.DataFrame({"Subsystem": list(failure_ratios.keys()),
                              "Failure Ratio": list(failure_ratios.values()),
                              "Availability (%)": [round((1 - v) * 100, 1) for v in failure_ratios.values()]})
    st.dataframe(stress_df, use_container_width=True, hide_index=True)
    st.bar_chart(stress_df.set_index("Subsystem")[["Availability (%)"]])

with tab4:
    page_question("AI Recommendation")
    st.subheader("Quick Recommendation Layer")
    for idx, line in enumerate(recommendation_lines(results, energy_security_scenario), 1):
        st.write(f"{idx}. {line}")
    st.subheader("Reason Chain")
    st.dataframe(reason_df, use_container_width=True, hide_index=True)
    why_df = pd.DataFrame(
        [{"Signal": "Shortfall", "Value": results["shortfall"]},
         {"Signal": "Reserve Days Remaining", "Value": results.get("reserve_days_remaining", 0)},
         {"Signal": "Hours Until Critical Failure", "Value": timeline_results["hours_until_critical_failure"]},
         {"Signal": "Grid Dependency (%)", "Value": results["grid_dependency"]}]
    )
    st.subheader("Priority Signals")
    st.dataframe(why_df, use_container_width=True, hide_index=True)

with tab5:
    page_question("Energy Security")
    s1, s2, s3 = st.columns(3)
    s1.metric("Import Disruption Score", f"{results['import_disruption_score']}%")
    s2.metric("Reserve Days Remaining", f"{results['reserve_days_remaining']} days")
    s3.metric("Fuel Cost Stress", f"{results['fuel_cost_stress']}%")
    s4, s5, s6 = st.columns(3)
    s4.metric("Critical Load Coverage", f"{results['critical_load_coverage']}%")
    s5.metric("Recovery Time Estimate", f"{results['recovery_time_estimate']} days")
    s6.metric("Reserve Recovery Lag", f"{reserve_recovery_lag_days} days")

with tab6:
    page_question("Survival Timeline")
    m1, m2, m3 = st.columns(3)
    m1.metric("Hours Until Shortfall", timeline_results["hours_until_shortfall"])
    m2.metric("Hours Until Critical Failure", timeline_results["hours_until_critical_failure"])
    m3.metric("Survival Mode Duration", timeline_results["survival_mode_duration"])
    m4, m5 = st.columns(2)
    m4.metric("Battery Depletion Hour", timeline_results["battery_depletion_hour"])
    m5.metric("Reserve Depletion Hour", timeline_results["reserve_depletion_hour"])
    if not timeline_df.empty:
        chart_cols = [c for c in ["raw_demand", "target_demand", "renewable_supply", "battery_used", "reserve_used", "final_supply", "shortfall", "battery_level", "reserve_energy"] if c in timeline_df.columns]
        if chart_cols:
            st.subheader("Timeline Chart")
            st.line_chart(timeline_df[chart_cols])
    st.subheader("Hourly Timeline Table")
    st.dataframe(timeline_df, use_container_width=True, hide_index=True)

with tab7:
    page_question("Concept Lab")
    st.markdown('<div class="note">These concept modules are illustrative simulation layers for resilience exploration. They are not hardware blueprints.</div>', unsafe_allow_html=True)
    concept_tabs = st.tabs(["Thermal Principle", "Phase-Change Buffer", "Ground Sink", "Distributed Control", "Harvesting & Buffering"])

    with concept_tabs[0]:
        concept_badge()
        render_thermal_principle_simulation(
            fresh_air_temp_c=fresh_air_temp_c,
            exhaust_air_temp_c=exhaust_air_temp_c,
            recovery_efficiency=recovery_efficiency,
            airflow_speed=thermal_animation_speed,
            height=820,
        )
        thermal_compare_df = pd.DataFrame(
            [
                {"Mode": "Current", "Demand (MW)": results["demand"], "Reserve Days": results.get("reserve_days_remaining", 0), "Shortfall Hour": timeline_results["hours_until_shortfall"], "Critical Failure Hour": timeline_results["hours_until_critical_failure"]},
                {"Mode": "Thermal Concept", "Demand (MW)": thermal_results["adjusted_demand"], "Reserve Days": thermal_results["adjusted_reserve_days"], "Shortfall Hour": thermal_results["adjusted_hours_until_shortfall"], "Critical Failure Hour": thermal_results["adjusted_hours_until_critical_failure"]},
            ]
        )
        st.dataframe(thermal_compare_df, use_container_width=True, hide_index=True)

    with concept_tabs[1]:
        concept_badge()
        reserve_bonus_hours = max((thermal_results["adjusted_reserve_days"] - results.get("reserve_days_remaining", 0)) * 24, 0.0)
        render_phase_change_buffer_concept(
            heat_load_mw=max(results["demand"] * 0.18, 1.0),
            buffer_state_pct=thermal_results["buffer_state_pct"],
            demand_reduction_pct=max(thermal_results["thermal_demand_reduction_pct"], 1.0),
            reserve_bonus_hours=reserve_bonus_hours,
            height=720,
        )

    with concept_tabs[2]:
        concept_badge()
        render_ground_thermal_sink_concept(
            cooling_offset_pct=round(max(thermal_results["thermal_demand_reduction_pct"] * 0.8, 2.0), 1),
            sink_utilization_pct=thermal_results["sink_utilization_pct"],
            saturation_risk_pct=round(max(5.0, 100 - thermal_results["sink_utilization_pct"]), 0),
            height=720,
        )

    with concept_tabs[3]:
        concept_badge()
        availability = round((1 - max(failure_ratios.values())) * 100, 0)
        rerouting_efficiency = round(max(40.0, 100 - (sum(failure_ratios.values()) / len(failure_ratios)) * 100), 0)
        render_distributed_thermal_control_concept(
            node_availability_pct=availability,
            rerouting_efficiency_pct=rerouting_efficiency,
            damage_ratio_pct=thermal_results["damage_ratio_pct"],
            protected_core_pct=round(max(45.0, 100 - results["grid_dependency"]), 0),
            height=720,
        )

    with concept_tabs[4]:
        concept_badge()
        reserve_gain_hours = round(max((thermal_results["adjusted_reserve_days"] - results.get("reserve_days_remaining", 0)) * 24, 0.0), 1)
        shortfall_reduction_pct = round(max((baseline_results["shortfall"] - results["shortfall"]) / max(baseline_results["shortfall"], 1) * 100, 0.0), 1)
        core_hours = timeline_results["hours_until_critical_failure"] if timeline_results["hours_until_critical_failure"] != "No Failure" else 168
        render_distributed_harvesting_buffering_concept(
            diversification_score=thermal_results["diversification_score"],
            reserve_gain_hours=reserve_gain_hours,
            shortfall_reduction_pct=shortfall_reduction_pct,
            core_preservation_hours=float(core_hours),
            height=720,
        )
