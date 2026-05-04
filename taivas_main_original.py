# TAIVAS CONTROL CENTER V9.5 CLEAN (FULL STABLE VERSION)

import streamlit as st
from taivas_core.energy_model import compute_energy_supply

st.set_page_config(page_title="TAIVAS", layout="wide")

st.title("TAIVAS Control Center")
st.caption("V9.5 CLEAN STABLE")

# =====================
# INPUT
# =====================
temperature = st.slider("Temperature (°C)", -20, 50, 25)
wind_speed = st.slider("Wind Speed (m/s)", 0.0, 30.0, 5.0)
solar_radiation = st.slider("Solar Radiation", 0, 1000, 500)
precipitation = st.slider("Precipitation", 0, 300, 0)
humidity = st.slider("Humidity", 0, 100, 60)
population = st.number_input("Population", value=100000)

solar_capacity = st.slider("Solar Capacity", 0, 1000, 200)
wind_capacity = st.slider("Wind Capacity", 0, 1000, 200)
geothermal_capacity = st.slider("Geothermal Capacity", 0, 1000, 100)
hydro_capacity = st.slider("Hydro Capacity", 0, 1000, 100)
battery_capacity = st.slider("Battery Capacity", 0, 2000, 500)

scenario_key = st.selectbox("Scenario", [
    "normal","heat_wave","storm","cold_wave","blizzard","typhoon","wildfire"
])

# =====================
# BUILD INPUT STRUCT
# =====================
inputs = {
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

failure_ratios = {
    "solar": 0.0,
    "wind": 0.0,
    "geothermal": 0.0,
    "hydro": 0.0,
    "battery": 0.0
}

# =====================
# COMPUTE
# =====================
results = compute_energy_supply(inputs, scenario_key, failure_ratios, 0)

# =====================
# OUTPUT
# =====================
col1, col2, col3 = st.columns(3)

col1.metric("Demand", results["demand"])
col2.metric("Supply", results["final_supply"])
col3.metric("Shortfall", results["shortfall"])

st.divider()

st.write("### System Status")

if results["shortfall"] > 0:
    st.error("⚠ Energy Shortage Detected")
else:
    st.success("✔ System Stable")

st.write("### Mix (%)")
st.write(results["actual_mix_pct"])

st.write("### Core Metrics")
st.write({
    "Renewable Supply": results["renewable_supply"],
    "Battery": results["battery_levels"],
    "Efficiency": results["system_efficiency"],
    "Grid Dependency": results["grid_dependency"]
})

st.info("Model: PVWatts + Wind Curve + Weather-adjusted Demand + Wildfire impact")
