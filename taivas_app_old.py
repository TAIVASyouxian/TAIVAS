import streamlit as st

from modules.translations import translations
from modules.country_logic import country_logic
from modules.city_profiles import city_profiles

st.set_page_config(page_title="TAIVAS", layout="wide")

language = st.sidebar.selectbox("Language / 語言", ["English", "中文"])
t = translations[language]

st.title(t["title"])

country_keys = list(country_logic.keys())
country_display_map = {t["countries"][k]: k for k in country_keys}
country_display = st.sidebar.selectbox(t["country"], list(country_display_map.keys()))
country_key = country_display_map[country_display]

available_cities = [
    city_key for city_key, city_data in city_profiles.items()
    if city_data["country"] == country_key
]

city_display_map = {t["cities"][k]: k for k in available_cities}
city_display = st.sidebar.selectbox(t["city"], list(city_display_map.keys()))
city_key = city_display_map[city_display]

st.subheader(f"{t['country']}: {country_display}")
st.write(country_logic[country_key]["description"])

st.subheader(f"{t['city']}: {city_display}")
city_data = city_profiles[city_key]

st.write(f"Latitude: {city_data['lat']}")
st.write(f"Longitude: {city_data['lon']}")
st.write(f"Country Model: {city_data['country']}")

population = st.sidebar.slider(t["population"], 10000, 5000000, 500000, step=50000)
solar = st.sidebar.slider(t["solar"], 0, 500, 120, step=10)
wind = st.sidebar.slider(t["wind"], 0, 500, 80, step=10)
geothermal = st.sidebar.slider(t["geothermal"], 0, 500, 60, step=10)
hydro = st.sidebar.slider(t["hydro"], 0, 500, 70, step=10)
battery = st.sidebar.slider(t["battery"], 0, 2000, 300, step=50)

st.subheader("Current Inputs")
st.write({
    t["population"]: population,
    t["solar"]: solar,
    t["wind"]: wind,
    t["geothermal"]: geothermal,
    t["hydro"]: hydro,
    t["battery"]: battery,
})
