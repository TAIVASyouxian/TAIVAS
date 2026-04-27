
from io import StringIO
import json
import time
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from modules.charts import make_donut_chart
from modules.recommendations import recommendation_lines
from modules.energy_security import apply_energy_security_layer, ENERGY_SECURITY_SCENARIOS
from modules.survival_timeline import simulate_survival_timeline

from data_config import CITY_DATA, COUNTRY_NOTES, SCENARIOS
from facility_config import FACILITY_PROFILES
from i18n_config import I18N, PAGE_QUESTIONS

from taivas_core.energy_model import compute_energy_supply

st.set_page_config(page_title="TAIVAS V9.5 FULL", layout="wide")

# --- Session init ---
if "selected_country" not in st.session_state:
    st.session_state.selected_country = "Taiwan"
if "selected_city" not in st.session_state:
    st.session_state.selected_city = "Taipei"
if "weather_scenario" not in st.session_state:
    st.session_state.weather_scenario = "normal"
if "demo_active" not in st.session_state:
    st.session_state.demo_active = False

# --- Demo logic ---
def apply_demo(country, city, scenario):
    st.session_state.selected_country = country
    st.session_state.selected_city = city
    st.session_state.weather_scenario = scenario
    st.session_state.demo_active = True
    with st.spinner("Applying scenario..."):
        time.sleep(1)
    st.rerun()

st.title("TAIVAS V9.5 FULL")

st.markdown("## 🚀 Guided Demo")

col1, col2 = st.columns(2)

with col1:
    if st.button("Taipei Typhoon"):
        apply_demo("Taiwan","Taipei","typhoon")
    if st.button("Helsinki Blizzard"):
        apply_demo("Finland","Helsinki","blizzard")

with col2:
    if st.button("Berlin Heatwave"):
        apply_demo("Germany","Berlin","heat_wave")
    if st.button("Reykjavik Storm"):
        apply_demo("Iceland","Reykjavik","storm")

if st.session_state.demo_active:
    st.success("Demo scenario active")

# --- Sidebar ---
country = st.sidebar.selectbox("Country", list(CITY_DATA.keys()), key="selected_country")
cities = list(CITY_DATA[country]["cities"].keys())
city = st.sidebar.selectbox("City", cities, key="selected_city")
scenario = st.sidebar.selectbox("Scenario", list(SCENARIOS.keys()), key="weather_scenario")

# --- Core call ---
result = compute_energy_supply(country, city, scenario)

st.markdown("## System Output")
st.write(result)
