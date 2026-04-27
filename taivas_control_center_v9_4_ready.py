
import streamlit as st

st.set_page_config(page_title="TAIVAS V9.4", layout="wide")

# --- Demo Data ---
CITY_DATA = {
    "Taiwan": {"cities": {"Taipei": {}}},
    "Finland": {"cities": {"Helsinki": {}}},
    "Germany": {"cities": {"Berlin": {}}},
    "Iceland": {"cities": {"Reykjavik": {}}}
}

SCENARIOS = ["normal", "heat_wave", "storm", "cold_wave", "blizzard", "typhoon"]

# --- Demo Auto Fill Buttons ---
st.title("TAIVAS V9.4 Demo")

col1, col2 = st.columns(2)

with col1:
    if st.button("Taipei Typhoon Test"):
        st.session_state.selected_country = "Taiwan"
        st.session_state.selected_city = "Taipei"
        st.session_state.weather_scenario = "typhoon"
        st.rerun()

    if st.button("Helsinki Blizzard Test"):
        st.session_state.selected_country = "Finland"
        st.session_state.selected_city = "Helsinki"
        st.session_state.weather_scenario = "blizzard"
        st.rerun()

with col2:
    if st.button("Berlin Heatwave Test"):
        st.session_state.selected_country = "Germany"
        st.session_state.selected_city = "Berlin"
        st.session_state.weather_scenario = "heat_wave"
        st.rerun()

    if st.button("Reykjavik Storm Test"):
        st.session_state.selected_country = "Iceland"
        st.session_state.selected_city = "Reykjavik"
        st.session_state.weather_scenario = "storm"
        st.rerun()

st.sidebar.header("Controls")

# --- Sidebar Controls ---
country = st.sidebar.selectbox(
    "Country",
    list(CITY_DATA.keys()),
    key="selected_country"
)

cities = list(CITY_DATA[country]["cities"].keys())

city = st.sidebar.selectbox(
    "City",
    cities,
    key="selected_city"
)

scenario = st.sidebar.selectbox(
    "Weather Scenario",
    SCENARIOS,
    key="weather_scenario"
)

# --- Display ---
st.subheader("Current Selection")
st.write(f"Country: {country}")
st.write(f"City: {city}")
st.write(f"Scenario: {scenario}")
