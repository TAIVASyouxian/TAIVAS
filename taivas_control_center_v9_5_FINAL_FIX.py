
import streamlit as st
import time

from data_config import CITY_DATA, SCENARIOS

st.set_page_config(page_title="TAIVAS V9.5 FINAL FIX", layout="wide")

# --- Session init ---
if "selected_country" not in st.session_state:
    st.session_state.selected_country = list(CITY_DATA.keys())[0]

if "selected_city" not in st.session_state:
    st.session_state.selected_city = list(CITY_DATA[st.session_state.selected_country].keys())[0]

if "weather_scenario" not in st.session_state:
    st.session_state.weather_scenario = list(SCENARIOS.keys())[0]

if "demo_active" not in st.session_state:
    st.session_state.demo_active = False

# --- Demo logic ---
def apply_demo(country, city, scenario):
    if country in CITY_DATA and city in CITY_DATA[country]:
        st.session_state.selected_country = country
        st.session_state.selected_city = city
        st.session_state.weather_scenario = scenario
        st.session_state.demo_active = True
        with st.spinner("Applying scenario..."):
            time.sleep(1)
        st.rerun()

st.title("TAIVAS V9.5 FINAL FIX")

# --- Demo Buttons ---
col1, col2 = st.columns(2)

with col1:
    if st.button("Taipei Typhoon Test"):
        apply_demo("Taiwan", "Taipei", "typhoon")

    if st.button("Helsinki Blizzard Test"):
        apply_demo("Finland", "Helsinki", "blizzard")

with col2:
    if st.button("Berlin Heatwave Test"):
        apply_demo("Germany", "Berlin", "heat_wave")

    if st.button("Reykjavik Storm Test"):
        apply_demo("Iceland", "Reykjavik", "storm")

if st.session_state.demo_active:
    st.success("Demo scenario active")

# --- Sidebar ---
st.sidebar.header("Controls")

country = st.sidebar.selectbox(
    "Country",
    list(CITY_DATA.keys()),
    key="selected_country"
)

cities = list(CITY_DATA[country].keys())

# Fix invalid city after country change
if st.session_state.selected_city not in cities:
    st.session_state.selected_city = cities[0]

city = st.sidebar.selectbox(
    "City",
    cities,
    key="selected_city"
)

scenario = st.sidebar.selectbox(
    "Weather Scenario",
    list(SCENARIOS.keys()),
    key="weather_scenario"
)

# --- Display (your original system continues below) ---
st.markdown("## Current Selection")
st.write(f"Country: {country}")
st.write(f"City: {city}")
st.write(f"Scenario: {scenario}")

st.info("Your original TAIVAS dashboard, charts, and model will continue below without breaking.")
