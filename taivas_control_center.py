
from io import StringIO
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="TAIVAS Energy Control Center", layout="wide")

CITY_DATA = {
    "Taiwan": {
        "Taipei": {"lat": 25.0330, "lon": 121.5654, "population": 2500000, "country_model": "taiwan"},
        "Taichung": {"lat": 24.1477, "lon": 120.6736, "population": 2820000, "country_model": "taiwan"},
        "Kaohsiung": {"lat": 22.6273, "lon": 120.3014, "population": 2730000, "country_model": "taiwan"},
    },
    "Finland": {
        "Helsinki": {"lat": 60.1699, "lon": 24.9384, "population": 664000, "country_model": "finland"},
        "Tampere": {"lat": 61.4978, "lon": 23.7610, "population": 255000, "country_model": "finland"},
        "Rovaniemi": {"lat": 66.5039, "lon": 25.7294, "population": 65000, "country_model": "finland"},
    },
    "Switzerland": {
        "Zurich": {"lat": 47.3769, "lon": 8.5417, "population": 435000, "country_model": "switzerland"},
        "Geneva": {"lat": 46.2044, "lon": 6.1432, "population": 203000, "country_model": "switzerland"},
        "Bern": {"lat": 46.9480, "lon": 7.4474, "population": 134000, "country_model": "switzerland"},
    },
    "Norway": {
        "Oslo": {"lat": 59.9139, "lon": 10.7522, "population": 717000, "country_model": "norway"},
        "Bergen": {"lat": 60.3913, "lon": 5.3221, "population": 289000, "country_model": "norway"},
        "Trondheim": {"lat": 63.4305, "lon": 10.3951, "population": 214000, "country_model": "norway"},
    },
    "Germany": {
        "Berlin": {"lat": 52.5200, "lon": 13.4050, "population": 3570000, "country_model": "germany"},
        "Hamburg": {"lat": 53.5511, "lon": 9.9937, "population": 1910000, "country_model": "germany"},
        "Munich": {"lat": 48.1351, "lon": 11.5820, "population": 1510000, "country_model": "germany"},
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


def clamp(value, low, high):
    return max(low, min(high, value))


def safe_div(a, b):
    return a / b if b not in (0, 0.0) else 0.0


def normalize_mix(parts):
    total = sum(max(v, 0.0) for v in parts.values())
    if total <= 0:
        return {k: 0.0 for k in parts}
    return {k: max(v, 0.0) / total for k, v in parts.items()}


def base_demand_from_population(population):
    return 80 + population / 50000


def weather_adjustment(temp, humidity, precipitation):
    cooling = max(0.0, temp - 24) * 1.8
    humidity_load = max(0.0, humidity - 65) * 0.25
    rain_impact = precipitation * 0.08
    return 1.0 + (cooling + humidity_load + rain_impact) / 100.0


def compute_energy_supply(inputs, scenario_key):
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


def recommendation_lines(results, scenario_key):
    lines = []
    if results["shortfall"] > 0:
        lines.append("Increase storage and reserve capacity to reduce supply gaps under stressed conditions.")
    if results["grid_dependency"] > 15:
        lines.append("Grid dependency is elevated. Strengthen local diversified supply and backup planning.")
    if results["renewable_ratio"] < 60:
        lines.append("Renewable contribution is modest. Consider increasing solar, wind, hydro, or geothermal capacity.")
    if scenario_key in {"typhoon", "storm", "blizzard"}:
        lines.append("Severe-weather scenario selected. Prioritize resilience, backup dispatch, and critical-load continuity.")
    if not lines:
        lines.append("System balance is currently stable. Maintain monitoring and compare against stress scenarios.")
    return lines


def make_donut_chart(mix_pct):
    labels = list(mix_pct.keys())
    values = [mix_pct[k] for k in labels]

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    wedges, _ = ax.pie(
        values,
        startangle=90,
        wedgeprops=dict(width=0.36, edgecolor="white", linewidth=1.5),
        labels=None,
    )

    ax.text(
        0,
        0,
        "Renewable\nMix",
        ha="center",
        va="center",
        fontsize=18,
        weight="bold",
        color="white",
    )

    legend_labels = [f"{label} — {value:.1f}%" for label, value in zip(labels, values)]
    legend = ax.legend(
        wedges,
        legend_labels,
        loc="center left",
        bbox_to_anchor=(0.98, 0.5),
        frameon=False,
        fontsize=12,
    )
    for text in legend.get_texts():
        text.set_color("white")

    ax.set_title("Renewable Energy Mix", fontsize=18, pad=16, color="white")
    ax.axis("equal")
    plt.subplots_adjust(left=0.04, right=0.80, top=0.90, bottom=0.06)
    return fig


def comparison_dataframe(inputs):
    rows = []
    for key in SCENARIOS.keys():
        r = compute_energy_supply(inputs, key)
        rows.append({
            "scenario": key,
            "demand": r["demand"],
            "renewable_supply": r["renewable_supply"],
            "final_supply": r["final_supply"],
            "shortfall": r["shortfall"],
            "renewable_ratio": r["renewable_ratio"],
            "system_efficiency": r["system_efficiency"],
            "grid_dependency": r["grid_dependency"],
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

st.info(
    "This control center combines country logic, city profiles, weather simulation, "
    "scenario stress testing, and energy resilience dashboard outputs."
)

col1, col2 = st.columns([1.15, 1])
with col1:
    st.subheader(f"Country Logic: {country}")
    st.write(COUNTRY_NOTES.get(country, "Regional energy model loaded."))
    st.subheader(f"City Profile: {city}")
    st.write(f"Latitude: {city_profile['lat']}")
    st.write(f"Longitude: {city_profile['lon']}")
    st.write(f"Country Model: {city_profile['country_model']}")
with col2:
    st.subheader("Input Summary")
    r1 = st.columns(2)
    r1[0].metric("Country", country)
    r1[1].metric("City", city)

    r2 = st.columns(2)
    r2[0].metric("Population", f"{population:,}")
    r2[1].metric("Scenario", scenario_key)

    r3 = st.columns(2)
    r3[0].metric("Temperature", f"{temperature} °C")
    r3[1].metric("Wind Speed", f"{wind_speed} m/s")

    r4 = st.columns(2)
    r4[0].metric("Solar Radiation", f"{solar_radiation} W/m²")
    r4[1].metric("Precipitation", f"{precipitation} mm")

    r5 = st.columns(2)
    r5[0].metric("Humidity", f"{humidity}%")
    r5[1].metric("Coordinates", f"{city_profile['lat']:.2f}, {city_profile['lon']:.2f}")

st.divider()
top = st.columns(4)
top[0].metric("Demand", f"{results['demand']} MW")
top[1].metric("Renewable Supply", f"{results['renewable_supply']} MW")
top[2].metric("Final Supply", f"{results['final_supply']} MW")
top[3].metric("Shortfall", f"{results['shortfall']} MW")

bottom = st.columns(4)
bottom[0].metric("Battery Levels", f"{results['battery_levels']} MWh")
bottom[1].metric("Renewable Ratio", f"{results['renewable_ratio']}%")
bottom[2].metric("System Efficiency", f"{results['system_efficiency']}%")
bottom[3].metric("Grid Dependency", f"{results['grid_dependency']}%")

st.divider()
tab1, tab2, tab3 = st.tabs(["Energy Mix", "Scenario Comparison", "AI Recommendation"])

with tab1:
    st.pyplot(make_donut_chart(results["energy_mix_pct"]), clear_figure=True)

with tab2:
    compare_cols = st.columns(2)
    with compare_cols[0]:
        st.subheader("Baseline vs Selected Scenario")
        baseline_compare = pd.DataFrame([
            {"mode": "baseline_normal", **{k: baseline_results[k] for k in ["demand", "renewable_supply", "final_supply", "shortfall", "renewable_ratio", "system_efficiency", "grid_dependency"]}},
            {"mode": scenario_key, **{k: results[k] for k in ["demand", "renewable_supply", "final_supply", "shortfall", "renewable_ratio", "system_efficiency", "grid_dependency"]}},
        ])
        st.dataframe(baseline_compare, use_container_width=True, hide_index=True)
    with compare_cols[1]:
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
