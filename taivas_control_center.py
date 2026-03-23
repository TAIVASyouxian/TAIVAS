from io import StringIO

import pandas as pd
import streamlit as st

from modules.charts import make_donut_chart
from modules.recommendations import recommendation_lines

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
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        background: linear-gradient(135deg, rgba(21,60,110,0.55), rgba(11,18,32,0.25));
        margin-bottom: 1rem;
    }
    .taivas-hero h3 {
        margin: 0 0 0.35rem 0;
        font-size: 1.25rem;
    }
    .taivas-hero p {
        margin: 0;
        opacity: 0.9;
        line-height: 1.55;
    }
    .section-note {
        padding: 0.85rem 1rem;
        border-radius: 14px;
        background: rgba(59, 130, 246, 0.10);
        border: 1px solid rgba(96, 165, 250, 0.20);
        margin-bottom: 0.75rem;
    }
    .mini-card {
        padding: 0.85rem 0.95rem;
        border-radius: 14px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        margin-bottom: 0.65rem;
        min-height: 88px;
    }
    .mini-label {
        font-size: 0.82rem;
        opacity: 0.78;
        margin-bottom: 0.3rem;
    }
    .mini-value {
        font-size: 1.05rem;
        font-weight: 600;
        line-height: 1.3;
    }
    .subtle-divider {
        margin-top: 0.35rem;
        margin-bottom: 0.85rem;
    }
    .sidebar-note {
        font-size: 0.83rem;
        opacity: 0.8;
        margin-top: -0.35rem;
        margin-bottom: 0.45rem;
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

    energy_mix_raw = {
        "Solar": solar_supply,
        "Wind": wind_supply,
        "Geothermal": geo_supply,
        "Hydro": hydro_supply,
    }
    energy_mix_pct = {k: v * 100 for k, v in normalize_mix(energy_mix_raw).items()}

    return {
        "demand": round(demand, 2),
        "renewable_supply": round(renewable_supply, 2),
        "final_supply": round(final_supply, 2),
        "battery_levels": round(battery_levels, 2),
        "shortfall": round(shortfall, 2),
        "renewable_ratio": round(renewable_ratio, 2),
        "system_efficiency": round(system_efficiency, 2),
        "grid_dependency": round(grid_dependency, 2),
        "energy_mix_pct": energy_mix_pct,
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
st.caption("AI-driven energy resilience and recovery dashboard")

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
    scenario_key = st.selectbox("Scenario", list(SCENARIOS.keys()), index=0)

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
baseline_results = compute_energy_supply(inputs, "normal")
scenario_df = comparison_dataframe(inputs)

st.markdown(
    """
    <div class="taivas-hero">
        <h3>Operational Overview</h3>
        <p>This control center combines country logic, city profiles, weather simulation, scenario stress testing, and energy resilience dashboard outputs.</p>
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
        mini_card("Scenario", scenario_key.replace("_", " ").title())
    with sum_b:
        mini_card("Temperature", f"{temperature} °C")
        mini_card("Wind Speed", f"{wind_speed} m/s")
        mini_card("Solar Radiation", f"{solar_radiation} W/m²")
        mini_card("Humidity", f"{humidity} %")

st.markdown('<div class="subtle-divider"></div>', unsafe_allow_html=True)
st.subheader("System Performance")
perf_top = st.columns(4)
perf_top[0].metric("Demand", f"{results['demand']} MW", help="Current modeled energy demand.")
perf_top[1].metric("Renewable Supply", f"{results['renewable_supply']} MW", help="Modeled renewable generation under the selected settings.")
perf_top[2].metric("Final Supply", f"{results['final_supply']} MW", help="Renewables plus battery dispatch.")
perf_top[3].metric("Shortfall", f"{results['shortfall']} MW", help="Unmet supply after renewable and battery dispatch.")

st.subheader("Resilience Indicators")
perf_bottom = st.columns(4)
perf_bottom[0].metric("Battery Levels", f"{results['battery_levels']} MWh", help="Remaining battery reserve after dispatch.")
perf_bottom[1].metric("Renewable Ratio", f"{results['renewable_ratio']}%", help="Share of final supply coming from renewables.")
perf_bottom[2].metric("System Efficiency", f"{results['system_efficiency']}%", help="Proxy indicator of overall resilience performance.")
perf_bottom[3].metric("Grid Dependency", f"{results['grid_dependency']}%", help="Residual dependency on external grid support.")

st.divider()
tab1, tab2, tab3 = st.tabs(["Energy Mix", "Scenario Comparison", "AI Recommendation"])

with tab1:
    st.markdown(
        '<div class="section-note">This chart shows the modeled renewable contribution structure under the selected city, weather, and scenario settings.</div>',
        unsafe_allow_html=True,
    )
    st.pyplot(make_donut_chart(results["energy_mix_pct"], results["renewable_ratio"]), clear_figure=True)

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
                "Mode": scenario_key.replace("_", " ").title(),
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
        st.subheader("All Scenarios")
        st.dataframe(scenario_df, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("AI Recommendation Panel")
    for idx, line in enumerate(recommendation_lines(results, scenario_key), 1):
        st.write(f"{idx}. {line}")
    st.subheader("Risk and Governance Notice")
    st.warning(
        "This product is a decision-support tool and not an unconditional guarantee. "
        "Model outputs may change when assumptions or parameters change."
    )

csv_buffer = StringIO()
scenario_df.to_csv(csv_buffer, index=False)
st.download_button(
    "Download scenario comparison CSV",
    csv_buffer.getvalue(),
    file_name="taivas_scenario_comparison.csv",
    mime="text/csv",
)
