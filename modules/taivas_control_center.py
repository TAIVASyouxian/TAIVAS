from io import StringIO

import pandas as pd
import streamlit as st

from modules.charts import make_donut_chart
from modules.recommendations import recommendation_lines
from modules.energy_security import apply_energy_security_layer, ENERGY_SECURITY_SCENARIOS
from modules.survival_timeline import simulate_survival_timeline

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

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.25rem; padding-bottom: 2rem;}
    .taivas-hero {
        padding: 1rem 1.1rem 1rem 1.1rem;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 16px;
        background: linear-gradient(135deg, rgba(21,60,110,0.58), rgba(11,18,32,0.28));
        margin-bottom: 1rem;
    }
    .taivas-hero h3 { margin: 0 0 0.35rem 0; font-size: 1.25rem; }
    .taivas-hero p { margin: 0; opacity: 0.92; line-height: 1.55; }
    .section-note {
        padding: 0.85rem 1rem;
        border-radius: 14px;
        background: rgba(59, 130, 246, 0.10);
        border: 1px solid rgba(96, 165, 250, 0.24);
        margin-bottom: 0.75rem;
    }
    .mini-card {
        padding: 0.85rem 0.95rem;
        border-radius: 14px;
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.12);
        margin-bottom: 0.65rem;
        min-height: 88px;
    }
    .mini-label { font-size: 0.82rem; opacity: 0.78; margin-bottom: 0.3rem; }
    .mini-value { font-size: 1.05rem; font-weight: 600; line-height: 1.3; }
    .subtle-divider { margin-top: 0.35rem; margin-bottom: 0.85rem; }
    .sidebar-note { font-size: 0.83rem; opacity: 0.8; margin-top: -0.35rem; margin-bottom: 0.45rem; }
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
    humidity_load = max(0.0, humidity - 65) * 0.25
    rain_impact = precipitation * 0.08
    return 1.0 + (cooling + humidity_load + rain_impact) / 100.0


def compute_energy_supply(inputs, scenario_key: str):
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

    solar_supply = solar_capacity * solar_cf * scenario["solar"]
    wind_supply = wind_capacity * wind_cf * scenario["wind"]
    hydro_supply = hydro_capacity * hydro_cf * scenario["hydro"]
    geo_supply = geothermal_capacity * geo_cf * scenario["geo"]

    renewable_supply = solar_supply + wind_supply + hydro_supply + geo_supply
    battery_dispatch = min(battery_capacity * 0.35 * scenario["battery"], max(0.0, demand - renewable_supply))
    final_supply = renewable_supply + battery_dispatch
    shortfall = max(0.0, demand - final_supply)

    renewable_ratio = safe_div(renewable_supply, final_supply) * 100 if final_supply > 0 else 0.0
    system_efficiency = clamp(100 - shortfall * 0.55, 0, 100)
    grid_dependency = safe_div(shortfall, demand) * 100 if demand > 0 else 0.0
    battery_levels = max(0.0, battery_capacity - battery_dispatch)

    actual_mix_raw = {
        "Solar": solar_supply,
        "Wind": wind_supply,
        "Geothermal": geo_supply,
        "Hydro": hydro_supply,
    }
    actual_mix_pct = {k: v * 100 for k, v in normalize_mix(actual_mix_raw).items()}

    installed_mix_raw = {
        "Solar": solar_capacity,
        "Wind": wind_capacity,
        "Geothermal": geothermal_capacity,
        "Hydro": hydro_capacity,
    }
    installed_mix_pct = {k: v * 100 for k, v in normalize_mix(installed_mix_raw).items()}

    capacity_factors = {
        "Solar": round(solar_cf * scenario["solar"] * 100, 1),
        "Wind": round(wind_cf * scenario["wind"] * 100, 1),
        "Geothermal": round(geo_cf * scenario["geo"] * 100, 1),
        "Hydro": round(hydro_cf * scenario["hydro"] * 100, 1),
    }

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
    }


def mini_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">{label}</div>
            <div class="mini-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def comparison_dataframe(inputs):
    rows = []
    for key in SCENARIOS.keys():
        r = compute_energy_supply(inputs, key)
        rows.append({
            "Scenario": key.replace("_", " ").title(),
            "Demand (MW)": r["demand"],
            "Renewable Supply (MW)": r["renewable_supply"],
            "Final Supply (MW)": r["final_supply"],
            "Shortfall (MW)": r["shortfall"],
            "Renewable Ratio (%)": r["renewable_ratio"],
            "System Efficiency (%)": r["system_efficiency"],
            "Grid Dependency (%)": r["grid_dependency"],
        })
    return pd.DataFrame(rows)


st.title("TAIVAS Energy Control Center")
st.caption("AI-driven energy resilience, recovery, energy-security, and survival-timeline dashboard")
st.info("This revised main file preserves your original module-based structure while separating installed capacity mix from actual supply mix for clearer interpretation.")

with st.sidebar:
    st.header("Controls")
    country = st.selectbox("Country", list(CITY_DATA.keys()))
    city = st.selectbox("City", list(CITY_DATA[country].keys()))

    city_profile = CITY_DATA[country][city]

    population = st.slider("Population", 10000, 5000000, int(city_profile["population"]), step=10000)
    st.markdown(f'<div class="sidebar-note">Selected population: {population:,}</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("Capacity Inputs (MW / MWh)")
    solar_capacity = st.slider("Solar Capacity", 0, 500, 120, 5)
    wind_capacity = st.slider("Wind Capacity", 0, 500, 80, 5)
    geothermal_capacity = st.slider("Geothermal Capacity", 0, 500, 60, 5)
    hydro_capacity = st.slider("Hydro Capacity", 0, 500, 70, 5)
    battery_capacity = st.slider("Battery Capacity", 0, 1000, 180, 10)

    st.divider()
    st.subheader("Weather Inputs")
    temperature = st.slider("Temperature (°C)", -20, 50, 26, 1)
    wind_speed = st.slider("Wind Speed (m/s)", 0.0, 30.0, 4.2, 0.1)
    solar_radiation = st.slider("Solar Radiation (W/m²)", 0, 1200, 640, 10)
    precipitation = st.slider("Precipitation (mm)", 0, 300, 12, 1)
    humidity = st.slider("Humidity (%)", 0, 100, 73, 1)

    st.divider()
    scenario_key = st.selectbox("Weather Scenario", list(SCENARIOS.keys()), index=0)

    st.divider()
    st.subheader("Energy Security Inputs")
    energy_security_scenario = st.selectbox("Energy Security Scenario", list(ENERGY_SECURITY_SCENARIOS.keys()), index=0)
    import_dependency = st.number_input("Import Dependency", min_value=0.0, max_value=1.0, value=0.70, step=0.01, format="%.2f")
    strategic_reserve_days = st.number_input("Strategic Reserve Days", min_value=0, max_value=365, value=20, step=1)
    critical_load_share = st.number_input("Critical Load Share", min_value=0.0, max_value=1.0, value=0.35, step=0.01, format="%.2f")
    shipping_dependency = st.number_input("Shipping Dependency", min_value=0.0, max_value=1.0, value=0.85, step=0.01, format="%.2f")
    infrastructure_damage_ratio = st.number_input("Infrastructure Damage Ratio", min_value=0.0, max_value=1.0, value=0.10, step=0.01, format="%.2f")

    st.divider()
    st.subheader("Survival Timeline Inputs")
    simulation_hours = st.selectbox("Simulation Hours", [24, 72, 168], index=0)
    primary_supply_failure_ratio = st.number_input("Primary Supply Failure Ratio", min_value=0.0, max_value=1.0, value=0.30, step=0.01, format="%.2f")
    reserve_energy_per_day = st.number_input("Reserve Energy per Day", min_value=20.0, max_value=300.0, value=120.0, step=5.0, format="%.1f")
    survival_mode = st.selectbox("Survival Mode", ["full_load", "critical_load_only"], index=0)

inputs = {
    "country_key": country,
    "city_key": city,
    "lat": city_profile["lat"],
    "lon": city_profile["lon"],
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
}

results = compute_energy_supply(inputs, scenario_key)
results, energy_security_profile = apply_energy_security_layer(
    base_results=results,
    scenario_key=energy_security_scenario,
    import_dependency=import_dependency,
    strategic_reserve_days=strategic_reserve_days,
    critical_load_share=critical_load_share,
    shipping_dependency=shipping_dependency,
    infrastructure_damage_ratio=infrastructure_damage_ratio,
)

timeline_results = simulate_survival_timeline(
    demand=results["demand"],
    renewable_supply=results["renewable_supply"],
    battery_capacity=inputs["battery_capacity"],
    strategic_reserve_days=strategic_reserve_days,
    critical_load_share=critical_load_share,
    weather_scenario=scenario_key,
    simulation_hours=simulation_hours,
    primary_supply_failure_ratio=primary_supply_failure_ratio,
    reserve_energy_per_day=reserve_energy_per_day,
    survival_mode=survival_mode,
)

baseline_results = compute_energy_supply(inputs, "normal")
baseline_results, _ = apply_energy_security_layer(
    base_results=baseline_results,
    scenario_key="normal",
    import_dependency=import_dependency,
    strategic_reserve_days=strategic_reserve_days,
    critical_load_share=critical_load_share,
    shipping_dependency=shipping_dependency,
    infrastructure_damage_ratio=0.0,
)

scenario_df = comparison_dataframe(inputs)
timeline_df = pd.DataFrame(timeline_results["rows"])

st.markdown(
    """
    <div class="taivas-hero">
        <h3>Operational Overview</h3>
        <p>This control center combines country logic, city profiles, weather simulation, scenario stress testing, energy security indicators, and a survival timeline layer for estimating how long the system can hold under supply disruption.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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

st.markdown('<div class="subtle-divider"></div>', unsafe_allow_html=True)
st.subheader("System Performance")
perf_top = st.columns(4)
perf_top[0].metric("Demand", f"{results['demand']} MW")
perf_top[1].metric("Renewable Supply", f"{results['renewable_supply']} MW")
perf_top[2].metric("Final Supply", f"{results['final_supply']} MW")
perf_top[3].metric("Shortfall", f"{results['shortfall']} MW")

st.subheader("Resilience Indicators")
perf_bottom = st.columns(4)
perf_bottom[0].metric("Battery Levels", f"{results['battery_levels']} MWh")
perf_bottom[1].metric("Renewable Ratio", f"{results['renewable_ratio']}%")
perf_bottom[2].metric("System Efficiency", f"{results['system_efficiency']}%")
perf_bottom[3].metric("Grid Dependency", f"{results['grid_dependency']}%")

st.divider()
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Energy Mix", "Scenario Comparison", "AI Recommendation", "Energy Security", "Survival Timeline"]
)

with tab1:
    st.markdown('<div class="section-note">This chart shows the modeled renewable contribution structure under the selected city, weather, and scenario settings.</div>', unsafe_allow_html=True)
    mix_left, mix_right = st.columns(2)
    with mix_left:
        st.markdown("**Installed Capacity Mix**")
        st.caption("This chart follows the capacity sliders on the left sidebar.")
        st.pyplot(make_donut_chart(results["installed_mix_pct"], 100), clear_figure=True)
        st.dataframe(
            pd.DataFrame([
                {"Source": k, "Installed Capacity (MW)": v, "Share (%)": round(results["installed_mix_pct"][k], 2)}
                for k, v in results["installed_mix_mw"].items()
            ]),
            use_container_width=True,
            hide_index=True,
        )
    with mix_right:
        st.markdown("**Actual Renewable Supply Mix**")
        st.caption("This chart changes with weather inputs, scenario modifiers, and current capacity settings.")
        st.pyplot(make_donut_chart(results["actual_mix_pct"], results["renewable_ratio"]), clear_figure=True)
        st.dataframe(
            pd.DataFrame([
                {
                    "Source": k,
                    "Modeled Output (MW)": v,
                    "Share (%)": round(results["actual_mix_pct"][k], 2),
                    "Effective Factor (%)": results["capacity_factors"][k],
                }
                for k, v in results["actual_mix_mw"].items()
            ]),
            use_container_width=True,
            hide_index=True,
        )

with tab2:
    compare_left, compare_right = st.columns(2)
    with compare_left:
        st.subheader("Baseline vs Selected Scenario")
        baseline_compare = pd.DataFrame([
            {
                "Mode": "Baseline Normal",
                "Demand (MW)": baseline_results["demand"],
                "Renewable Supply (MW)": baseline_results["renewable_supply"],
                "Final Supply (MW)": baseline_results["final_supply"],
                "Shortfall (MW)": baseline_results["shortfall"],
                "Renewable Ratio (%)": baseline_results["renewable_ratio"],
                "System Efficiency (%)": baseline_results["system_efficiency"],
                "Grid Dependency (%)": baseline_results["grid_dependency"],
            },
            {
                "Mode": f"{scenario_key.replace('_', ' ').title()} + {energy_security_scenario.replace('_', ' ').title()}",
                "Demand (MW)": results["demand"],
                "Renewable Supply (MW)": results["renewable_supply"],
                "Final Supply (MW)": results["final_supply"],
                "Shortfall (MW)": results["shortfall"],
                "Renewable Ratio (%)": results["renewable_ratio"],
                "System Efficiency (%)": results["system_efficiency"],
                "Grid Dependency (%)": results["grid_dependency"],
            },
        ])
        st.dataframe(baseline_compare, use_container_width=True, hide_index=True)
    with compare_right:
        st.subheader("All Weather Scenarios")
        st.dataframe(scenario_df, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("AI Recommendation Panel")
    recommendation_output = recommendation_lines(results, energy_security_scenario)
    for idx, line in enumerate(recommendation_output, 1):
        st.write(f"{idx}. {line}")

    rec_left, rec_right = st.columns(2)
    with rec_left:
        st.markdown("**Why the recommendation appears**")
        why_lines = []
        if results["shortfall"] > 0:
            why_lines.append(f"Shortfall is present at {results['shortfall']} MW.")
        if results["grid_dependency"] >= 10:
            why_lines.append(f"Grid dependency is elevated at {results['grid_dependency']}%.")
        if results.get("import_disruption_score", 0) >= 40:
            why_lines.append(f"Import disruption pressure is high at {results['import_disruption_score']}%.")
        if timeline_results["hours_until_shortfall"] not in ("None within horizon", None) and str(timeline_results["hours_until_shortfall"]).isdigit():
            why_lines.append(f"Timeline model shows shortfall beginning by hour {timeline_results['hours_until_shortfall']}.")
        if not why_lines:
            why_lines.append("Current settings are relatively stable under the selected scenario horizon.")
        for item in why_lines:
            st.write(f"- {item}")

    with rec_right:
        st.markdown("**Expected effect focus**")
        effect_rows = [
            {"Metric": "Renewable Ratio", "Current": f"{results['renewable_ratio']}%"},
            {"Metric": "System Efficiency", "Current": f"{results['system_efficiency']}%"},
            {"Metric": "Reserve Days Remaining", "Current": f"{results['reserve_days_remaining']} days"},
            {"Metric": "Hours Until Critical Failure", "Current": f"{timeline_results['hours_until_critical_failure']}"},
        ]
        st.dataframe(pd.DataFrame(effect_rows), use_container_width=True, hide_index=True)

    st.subheader("Risk and Governance Notice")
    st.warning("This product is a decision-support tool and not an unconditional guarantee. Model outputs may change when assumptions or parameters change.")

with tab4:
    st.subheader("Energy Security")
    st.markdown('<div class="section-note">This section adds import exposure, reserve endurance, critical-load protection, and recovery indicators on top of the core resilience model.</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    s1.metric("Import Disruption Score", f"{results['import_disruption_score']}%")
    s2.metric("Reserve Days Remaining", f"{results['reserve_days_remaining']} days")
    s3.metric("Fuel Cost Stress", f"{results['fuel_cost_stress']}%")
    s4, s5 = st.columns(2)
    s4.metric("Critical Load Coverage", f"{results['critical_load_coverage']}%")
    s5.metric("Recovery Time Estimate", f"{results['recovery_time_estimate']} days")

with tab5:
    st.subheader("Survival Timeline")
    st.markdown('<div class="section-note">This section estimates how long the system can continue operating under hourly demand/supply changes, battery depletion, reserve depletion, and primary-supply failure conditions.</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Hours Until Shortfall", timeline_results["hours_until_shortfall"])
    m2.metric("Hours Until Critical Failure", timeline_results["hours_until_critical_failure"])
    m3.metric("Survival Mode Duration", timeline_results["survival_mode_duration"])
    m4, m5 = st.columns(2)
    m4.metric("Battery Depletion Hour", timeline_results["battery_depletion_hour"])
    m5.metric("Reserve Depletion Hour", timeline_results["reserve_depletion_hour"])
    st.subheader("Hourly Timeline Table")
    st.dataframe(timeline_df, use_container_width=True, hide_index=True)

csv_buffer = StringIO()
scenario_df.to_csv(csv_buffer, index=False)
st.download_button(
    "Download scenario comparison CSV",
    csv_buffer.getvalue(),
    file_name="taivas_scenario_comparison.csv",
    mime="text/csv",
)
