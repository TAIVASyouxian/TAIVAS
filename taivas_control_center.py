import math
from datetime import datetime
from typing import Dict, Any, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TAIVAS Energy Control Center",
    page_icon="⚡",
    layout="wide",
)

# -----------------------------
# Stable English-only version
# -----------------------------
APP_VERSION = "TAIVAS Stable SC v2.0"

CITY_DATA = {
    "Taiwan": {
        "Taipei": {
            "lat": 25.0330,
            "lon": 121.5654,
            "population": 2500000,
            "temperature": 26.0,
            "wind_speed": 4.2,
            "solar_radiation": 610.0,
            "precipitation": 8.0,
            "humidity": 74.0,
            "solar_capacity": 420.0,
            "wind_capacity": 180.0,
            "geothermal_capacity": 60.0,
            "hydro_capacity": 90.0,
            "battery_capacity": 240.0,
        },
        "Taichung": {
            "lat": 24.1477,
            "lon": 120.6736,
            "population": 2850000,
            "temperature": 27.0,
            "wind_speed": 4.8,
            "solar_radiation": 640.0,
            "precipitation": 6.0,
            "humidity": 70.0,
            "solar_capacity": 500.0,
            "wind_capacity": 210.0,
            "geothermal_capacity": 50.0,
            "hydro_capacity": 80.0,
            "battery_capacity": 220.0,
        },
        "Kaohsiung": {
            "lat": 22.6273,
            "lon": 120.3014,
            "population": 2730000,
            "temperature": 29.0,
            "wind_speed": 5.2,
            "solar_radiation": 700.0,
            "precipitation": 5.0,
            "humidity": 72.0,
            "solar_capacity": 620.0,
            "wind_capacity": 260.0,
            "geothermal_capacity": 55.0,
            "hydro_capacity": 70.0,
            "battery_capacity": 260.0,
        },
    },
    "Finland": {
        "Helsinki": {
            "lat": 60.1699,
            "lon": 24.9384,
            "population": 660000,
            "temperature": 11.0,
            "wind_speed": 5.8,
            "solar_radiation": 360.0,
            "precipitation": 4.0,
            "humidity": 78.0,
            "solar_capacity": 160.0,
            "wind_capacity": 340.0,
            "geothermal_capacity": 120.0,
            "hydro_capacity": 130.0,
            "battery_capacity": 210.0,
        },
        "Tampere": {
            "lat": 61.4978,
            "lon": 23.7610,
            "population": 255000,
            "temperature": 9.0,
            "wind_speed": 5.4,
            "solar_radiation": 330.0,
            "precipitation": 4.0,
            "humidity": 76.0,
            "solar_capacity": 140.0,
            "wind_capacity": 290.0,
            "geothermal_capacity": 150.0,
            "hydro_capacity": 160.0,
            "battery_capacity": 190.0,
        },
        "Rovaniemi": {
            "lat": 66.5039,
            "lon": 25.7294,
            "population": 65000,
            "temperature": 3.0,
            "wind_speed": 6.0,
            "solar_radiation": 250.0,
            "precipitation": 3.0,
            "humidity": 81.0,
            "solar_capacity": 100.0,
            "wind_capacity": 250.0,
            "geothermal_capacity": 170.0,
            "hydro_capacity": 180.0,
            "battery_capacity": 160.0,
        },
    },
    "Norway": {
        "Oslo": {
            "lat": 59.9139,
            "lon": 10.7522,
            "population": 710000,
            "temperature": 10.0,
            "wind_speed": 5.0,
            "solar_radiation": 350.0,
            "precipitation": 4.0,
            "humidity": 75.0,
            "solar_capacity": 150.0,
            "wind_capacity": 300.0,
            "geothermal_capacity": 70.0,
            "hydro_capacity": 420.0,
            "battery_capacity": 240.0,
        },
        "Bergen": {
            "lat": 60.3913,
            "lon": 5.3221,
            "population": 290000,
            "temperature": 9.0,
            "wind_speed": 6.2,
            "solar_radiation": 300.0,
            "precipitation": 10.0,
            "humidity": 82.0,
            "solar_capacity": 110.0,
            "wind_capacity": 330.0,
            "geothermal_capacity": 60.0,
            "hydro_capacity": 460.0,
            "battery_capacity": 200.0,
        },
        "Tromso": {
            "lat": 69.6492,
            "lon": 18.9553,
            "population": 78000,
            "temperature": 4.0,
            "wind_speed": 6.8,
            "solar_radiation": 220.0,
            "precipitation": 5.0,
            "humidity": 80.0,
            "solar_capacity": 90.0,
            "wind_capacity": 360.0,
            "geothermal_capacity": 55.0,
            "hydro_capacity": 380.0,
            "battery_capacity": 170.0,
        },
    },
}

SCENARIOS = {
    "normal": {
        "demand_mult": 1.00,
        "solar_mult": 1.00,
        "wind_mult": 1.00,
        "geothermal_mult": 1.00,
        "hydro_mult": 1.00,
        "battery_mult": 1.00,
        "temp_delta": 0.0,
        "wind_delta": 0.0,
        "rain_delta": 0.0,
        "desc": "Baseline operating condition.",
    },
    "heat_wave": {
        "demand_mult": 1.18,
        "solar_mult": 1.08,
        "wind_mult": 0.92,
        "geothermal_mult": 1.00,
        "hydro_mult": 0.95,
        "battery_mult": 0.93,
        "temp_delta": 7.0,
        "wind_delta": -0.8,
        "rain_delta": -2.0,
        "desc": "Higher cooling demand and mild renewable stress.",
    },
    "storm": {
        "demand_mult": 1.10,
        "solar_mult": 0.62,
        "wind_mult": 1.16,
        "geothermal_mult": 1.00,
        "hydro_mult": 1.04,
        "battery_mult": 0.88,
        "temp_delta": -2.0,
        "wind_delta": 1.6,
        "rain_delta": 5.0,
        "desc": "Cloud cover reduces solar while wind and hydro can improve.",
    },
    "cold_wave": {
        "demand_mult": 1.22,
        "solar_mult": 0.78,
        "wind_mult": 1.08,
        "geothermal_mult": 1.05,
        "hydro_mult": 0.96,
        "battery_mult": 0.90,
        "temp_delta": -8.0,
        "wind_delta": 0.7,
        "rain_delta": 0.0,
        "desc": "Heating demand rises sharply under colder temperatures.",
    },
    "blizzard": {
        "demand_mult": 1.30,
        "solar_mult": 0.35,
        "wind_mult": 0.85,
        "geothermal_mult": 1.04,
        "hydro_mult": 0.90,
        "battery_mult": 0.82,
        "temp_delta": -12.0,
        "wind_delta": 2.2,
        "rain_delta": 3.0,
        "desc": "Severe winter disruption with higher demand and lower reliability.",
    },
    "typhoon": {
        "demand_mult": 1.16,
        "solar_mult": 0.22,
        "wind_mult": 0.70,
        "geothermal_mult": 1.00,
        "hydro_mult": 1.10,
        "battery_mult": 0.78,
        "temp_delta": -1.0,
        "wind_delta": 3.0,
        "rain_delta": 12.0,
        "desc": "Extreme rain and grid stress; hydro may improve but outages rise.",
    },
}


def clamp(value: float, low: float, high: float) -> float:
    try:
        value = float(value)
    except Exception:
        return low
    if math.isnan(value) or math.isinf(value):
        return low
    return max(low, min(high, value))


def safe_div(a: float, b: float) -> float:
    if abs(b) < 1e-9:
        return 0.0
    return a / b


def init_state() -> None:
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []


def city_defaults(country: str, city: str) -> Dict[str, float]:
    return CITY_DATA[country][city].copy()


def build_inputs(country: str, city: str, scenario: str, base: Dict[str, float]) -> Dict[str, Any]:
    scenario_cfg = SCENARIOS.get(scenario, SCENARIOS["normal"])
    population = int(clamp(base.get("population", 100000), 1000, 50000000))

    inputs = {
        "country_key": country,
        "city_key": city,
        "lat": clamp(base.get("lat", 0.0), -90.0, 90.0),
        "lon": clamp(base.get("lon", 0.0), -180.0, 180.0),
        "temperature": clamp(base.get("temperature", 20.0) + scenario_cfg["temp_delta"], -50.0, 60.0),
        "wind_speed": clamp(base.get("wind_speed", 4.0) + scenario_cfg["wind_delta"], 0.0, 50.0),
        "solar_radiation": clamp(base.get("solar_radiation", 400.0), 0.0, 1500.0),
        "precipitation": clamp(base.get("precipitation", 3.0) + scenario_cfg["rain_delta"], 0.0, 500.0),
        "humidity": clamp(base.get("humidity", 60.0), 0.0, 100.0),
        "population": population,
        "solar_capacity": clamp(base.get("solar_capacity", 100.0), 0.0, 10000.0),
        "wind_capacity": clamp(base.get("wind_capacity", 100.0), 0.0, 10000.0),
        "geothermal_capacity": clamp(base.get("geothermal_capacity", 100.0), 0.0, 10000.0),
        "hydro_capacity": clamp(base.get("hydro_capacity", 100.0), 0.0, 10000.0),
        "battery_capacity": clamp(base.get("battery_capacity", 100.0), 0.0, 10000.0),
    }
    return inputs


def simulate(inputs: Dict[str, Any], scenario: str) -> Dict[str, Any]:
    cfg = SCENARIOS.get(scenario, SCENARIOS["normal"])

    population = inputs["population"]
    temp = inputs["temperature"]
    wind_speed = inputs["wind_speed"]
    solar_rad = inputs["solar_radiation"]
    precipitation = inputs["precipitation"]
    humidity = inputs["humidity"]

    demand_base = 120 + population * 0.00042
    temp_stress = max(0.0, temp - 24) * 3.3 + max(0.0, 12 - temp) * 2.8
    humidity_stress = max(0.0, humidity - 70) * 0.25
    demand = (demand_base + temp_stress + humidity_stress) * cfg["demand_mult"]

    solar_factor = clamp((solar_rad / 700.0) * cfg["solar_mult"], 0.0, 1.35)
    wind_factor = clamp((wind_speed / 7.0) * cfg["wind_mult"], 0.0, 1.30)
    geothermal_factor = clamp(0.92 * cfg["geothermal_mult"], 0.0, 1.20)
    hydro_weather_bonus = 1.0 + min(precipitation, 100.0) / 500.0
    hydro_factor = clamp(hydro_weather_bonus * cfg["hydro_mult"], 0.0, 1.35)

    solar_supply = inputs["solar_capacity"] * solar_factor
    wind_supply = inputs["wind_capacity"] * wind_factor
    geothermal_supply = inputs["geothermal_capacity"] * geothermal_factor
    hydro_supply = inputs["hydro_capacity"] * hydro_factor

    renewable_supply = solar_supply + wind_supply + geothermal_supply + hydro_supply

    battery_effective = inputs["battery_capacity"] * cfg["battery_mult"]
    excess = max(0.0, renewable_supply - demand)
    deficit = max(0.0, demand - renewable_supply)
    battery_discharge = min(deficit, battery_effective * 0.55)
    shortfall = max(0.0, deficit - battery_discharge)

    final_supply = renewable_supply + battery_discharge
    renewable_ratio = clamp(safe_div(renewable_supply, demand) * 100.0, 0.0, 1000.0)
    grid_dependency = clamp(safe_div(shortfall, demand) * 100.0, 0.0, 100.0)

    reliability_penalty = 0.0
    if scenario in ["storm", "blizzard", "typhoon"]:
        reliability_penalty = {"storm": 6.0, "blizzard": 10.0, "typhoon": 14.0}[scenario]
    system_efficiency = clamp(
        100.0
        - grid_dependency * 0.75
        - reliability_penalty
        - max(0.0, abs(temp - 22.0)) * 0.15,
        0.0,
        100.0,
    )

    battery_levels = clamp(battery_effective - battery_discharge + min(excess, battery_effective * 0.25), 0.0, battery_effective)

    mix_total = max(renewable_supply, 1e-9)
    energy_mix_pct = {
        "Solar": safe_div(solar_supply, mix_total) * 100.0,
        "Wind": safe_div(wind_supply, mix_total) * 100.0,
        "Geothermal": safe_div(geothermal_supply, mix_total) * 100.0,
        "Hydro": safe_div(hydro_supply, mix_total) * 100.0,
    }

    recommendation = []
    if shortfall > 0:
        recommendation.append("Increase firm capacity or storage to reduce unmet demand.")
    if energy_mix_pct["Solar"] > 50 and scenario in ["storm", "typhoon"]:
        recommendation.append("Reduce over-reliance on solar for bad-weather resilience.")
    if battery_levels < battery_effective * 0.25:
        recommendation.append("Battery reserve is low; add storage or peak shaving logic.")
    if renewable_ratio < 70:
        recommendation.append("Renewable contribution is below target; rebalance the energy mix.")
    if not recommendation:
        recommendation.append("Current setup is reasonably balanced under this scenario.")

    return {
        "demand": round(demand, 2),
        "renewable_supply": round(renewable_supply, 2),
        "final_supply": round(final_supply, 2),
        "battery_levels": round(battery_levels, 2),
        "shortfall": round(shortfall, 2),
        "renewable_ratio": round(renewable_ratio, 2),
        "system_efficiency": round(system_efficiency, 2),
        "grid_dependency": round(grid_dependency, 2),
        "solar_supply": round(solar_supply, 2),
        "wind_supply": round(wind_supply, 2),
        "geothermal_supply": round(geothermal_supply, 2),
        "hydro_supply": round(hydro_supply, 2),
        "energy_mix_pct": energy_mix_pct,
        "scenario_desc": cfg["desc"],
        "recommendation": recommendation,
    }


def add_audit_row(inputs: Dict[str, Any], outputs: Dict[str, Any], scenario: str) -> None:
    st.session_state.audit_log.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "country": inputs["country_key"],
            "city": inputs["city_key"],
            "scenario": scenario,
            "population": inputs["population"],
            "demand": outputs["demand"],
            "renewable_supply": outputs["renewable_supply"],
            "final_supply": outputs["final_supply"],
            "shortfall": outputs["shortfall"],
            "renewable_ratio": outputs["renewable_ratio"],
            "grid_dependency": outputs["grid_dependency"],
            "system_efficiency": outputs["system_efficiency"],
        }
    )
    st.session_state.audit_log = st.session_state.audit_log[-50:]


def render_pie_chart(outputs: Dict[str, Any]) -> None:
    labels = ["Solar", "Wind", "Geothermal", "Hydro"]
    values = [
        max(outputs["solar_supply"], 0.0),
        max(outputs["wind_supply"], 0.0),
        max(outputs["geothermal_supply"], 0.0),
        max(outputs["hydro_supply"], 0.0),
    ]

    total = sum(values)
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    if total <= 0:
        ax.text(0.5, 0.5, "No renewable output", ha="center", va="center", fontsize=14)
        ax.axis("off")
    else:
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"width": 0.45, "edgecolor": "white"},
            textprops={"fontsize": 10},
        )
        ax.set_title("Renewable Energy Mix")
        ax.axis("equal")
    st.pyplot(fig, clear_figure=True)


def comparison_dataframe(country: str, city: str, base: Dict[str, float]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for sc in SCENARIOS.keys():
        inputs = build_inputs(country, city, sc, base)
        out = simulate(inputs, sc)
        rows.append(
            {
                "Scenario": sc,
                "Demand": out["demand"],
                "Renewable Supply": out["renewable_supply"],
                "Final Supply": out["final_supply"],
                "Shortfall": out["shortfall"],
                "Renewable Ratio %": out["renewable_ratio"],
                "Grid Dependency %": out["grid_dependency"],
                "System Efficiency %": out["system_efficiency"],
            }
        )
    return pd.DataFrame(rows)


def render_sidebar() -> Dict[str, Any]:
    st.sidebar.header("Simulation Controls")

    country = st.sidebar.selectbox("Country", list(CITY_DATA.keys()), index=0)
    city = st.sidebar.selectbox("City", list(CITY_DATA[country].keys()), index=0)
    scenario = st.sidebar.selectbox("Scenario", list(SCENARIOS.keys()), index=0)

    defaults = city_defaults(country, city)

    population = st.sidebar.slider("Population", 1_000, 10_000_000, int(defaults["population"]), step=1_000)

    st.sidebar.subheader("Weather Inputs")
    temperature = st.sidebar.slider("Temperature (°C)", -20.0, 45.0, float(defaults["temperature"]), step=0.5)
    wind_speed = st.sidebar.slider("Wind Speed (m/s)", 0.0, 25.0, float(defaults["wind_speed"]), step=0.1)
    solar_radiation = st.sidebar.slider("Solar Radiation (W/m²)", 0.0, 1200.0, float(defaults["solar_radiation"]), step=5.0)
    precipitation = st.sidebar.slider("Precipitation (mm)", 0.0, 200.0, float(defaults["precipitation"]), step=1.0)
    humidity = st.sidebar.slider("Humidity (%)", 0.0, 100.0, float(defaults["humidity"]), step=1.0)

    st.sidebar.subheader("Installed Capacity")
    solar_capacity = st.sidebar.slider("Solar Capacity", 0.0, 3000.0, float(defaults["solar_capacity"]), step=10.0)
    wind_capacity = st.sidebar.slider("Wind Capacity", 0.0, 3000.0, float(defaults["wind_capacity"]), step=10.0)
    geothermal_capacity = st.sidebar.slider("Geothermal Capacity", 0.0, 3000.0, float(defaults["geothermal_capacity"]), step=10.0)
    hydro_capacity = st.sidebar.slider("Hydro Capacity", 0.0, 3000.0, float(defaults["hydro_capacity"]), step=10.0)
    battery_capacity = st.sidebar.slider("Battery Capacity", 0.0, 3000.0, float(defaults["battery_capacity"]), step=10.0)

    if st.sidebar.button("Reset to city defaults"):
        st.rerun()

    return {
        "country": country,
        "city": city,
        "scenario": scenario,
        "base": {
            **defaults,
            "population": population,
            "temperature": temperature,
            "wind_speed": wind_speed,
            "solar_radiation": solar_radiation,
            "precipitation": precipitation,
            "humidity": humidity,
            "solar_capacity": solar_capacity,
            "wind_capacity": wind_capacity,
            "geothermal_capacity": geothermal_capacity,
            "hydro_capacity": hydro_capacity,
            "battery_capacity": battery_capacity,
        },
    }


def main() -> None:
    init_state()
    ui = render_sidebar()

    inputs = build_inputs(ui["country"], ui["city"], ui["scenario"], ui["base"])
    outputs = simulate(inputs, ui["scenario"])
    add_audit_row(inputs, outputs, ui["scenario"])

    st.title("TAIVAS Energy Control Center")
    st.caption(f"{APP_VERSION} · Streamlit Cloud deployment-safe version")

    info_col1, info_col2 = st.columns([1.4, 1])
    with info_col1:
        st.markdown(
            f"**Location:** {inputs['city_key']}, {inputs['country_key']}  \\\n**Scenario:** {ui['scenario']}  \\\n**Scenario note:** {outputs['scenario_desc']}"
        )
    with info_col2:
        st.info(
            "This tool is decision support, not an unconditional guarantee. "
            "Use exported results together with domain judgment and local data."
        )

    a, b, c, d = st.columns(4)
    a.metric("Demand", outputs["demand"])
    b.metric("Renewable Supply", outputs["renewable_supply"])
    c.metric("Final Supply", outputs["final_supply"])
    d.metric("Shortfall", outputs["shortfall"])

    e, f, g, h = st.columns(4)
    e.metric("Battery Levels", outputs["battery_levels"])
    f.metric("Renewable Ratio", f"{outputs['renewable_ratio']}%")
    g.metric("System Efficiency", f"{outputs['system_efficiency']}%")
    h.metric("Grid Dependency", f"{outputs['grid_dependency']}%")

    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("Renewable Energy Mix")
        render_pie_chart(outputs)
    with right:
        st.subheader("Input Summary")
        summary_df = pd.DataFrame(
            [
                ["Country", inputs["country_key"]],
                ["City", inputs["city_key"]],
                ["Population", f"{inputs['population']:,}"],
                ["Temperature", f"{inputs['temperature']} °C"],
                ["Wind Speed", f"{inputs['wind_speed']} m/s"],
                ["Solar Radiation", f"{inputs['solar_radiation']} W/m²"],
                ["Precipitation", f"{inputs['precipitation']} mm"],
                ["Humidity", f"{inputs['humidity']} %"],
                ["Battery Capacity", inputs["battery_capacity"]],
            ],
            columns=["Field", "Value"],
        )
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        mix_table = pd.DataFrame(
            {
                "Energy Source": ["Solar", "Wind", "Geothermal", "Hydro"],
                "Supply": [outputs["solar_supply"], outputs["wind_supply"], outputs["geothermal_supply"], outputs["hydro_supply"]],
                "Share %": [
                    round(outputs["energy_mix_pct"]["Solar"], 2),
                    round(outputs["energy_mix_pct"]["Wind"], 2),
                    round(outputs["energy_mix_pct"]["Geothermal"], 2),
                    round(outputs["energy_mix_pct"]["Hydro"], 2),
                ],
            }
        )
        st.dataframe(mix_table, use_container_width=True, hide_index=True)

    st.subheader("Baseline vs Selected Scenario")
    base_inputs = build_inputs(ui["country"], ui["city"], "normal", ui["base"])
    baseline_outputs = simulate(base_inputs, "normal")
    compare_df = pd.DataFrame(
        [
            ["Demand", baseline_outputs["demand"], outputs["demand"]],
            ["Renewable Supply", baseline_outputs["renewable_supply"], outputs["renewable_supply"]],
            ["Final Supply", baseline_outputs["final_supply"], outputs["final_supply"]],
            ["Shortfall", baseline_outputs["shortfall"], outputs["shortfall"]],
            ["Renewable Ratio %", baseline_outputs["renewable_ratio"], outputs["renewable_ratio"]],
            ["Grid Dependency %", baseline_outputs["grid_dependency"], outputs["grid_dependency"]],
            ["System Efficiency %", baseline_outputs["system_efficiency"], outputs["system_efficiency"]],
        ],
        columns=["Metric", "Baseline", "Selected Scenario"],
    )
    st.dataframe(compare_df, use_container_width=True, hide_index=True)

    st.subheader("All Scenario Comparison")
    scenario_df = comparison_dataframe(ui["country"], ui["city"], ui["base"])
    st.dataframe(scenario_df, use_container_width=True, hide_index=True)

    st.subheader("AI Recommendation")
    for rec in outputs["recommendation"]:
        st.write(f"- {rec}")

    st.subheader("Audit Trail")
    audit_df = pd.DataFrame(st.session_state.audit_log)
    st.dataframe(audit_df.tail(10), use_container_width=True, hide_index=True)
    csv_bytes = audit_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download audit trail CSV",
        data=csv_bytes,
        file_name="taivas_audit_trail.csv",
        mime="text/csv",
    )

    with st.expander("Developer Debug Panel"):
        st.write("Raw inputs")
        st.json(inputs)
        st.write("Raw outputs")
        st.json(outputs)
        st.write("Scenario config")
        st.json(SCENARIOS[ui["scenario"]])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        st.error("The app encountered a runtime issue, but it stayed in a safe failure mode.")
        st.exception(exc)
