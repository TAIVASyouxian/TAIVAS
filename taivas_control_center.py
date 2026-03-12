import json
import urllib.parse
import urllib.request

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from modules.translations import translations
from modules.country_logic import country_logic
from modules.city_profiles import city_profiles

st.set_page_config(page_title="TAIVAS Energy Control Center", layout="wide")

# =========================
# Language
# =========================
preferred_order = ["English", "中文", "Deutsch", "Suomi", "Schweizerdeutsch", "Íslenska"]
available_languages = [lang for lang in preferred_order if lang in translations]
if not available_languages:
    available_languages = list(translations.keys())

language = st.sidebar.selectbox("Language / 語言", available_languages)
t = translations.get(language, translations.get("English", {}))

# =========================
# Font
# =========================
matplotlib.rcParams["axes.unicode_minus"] = False
if language == "中文":
    matplotlib.rcParams["font.sans-serif"] = [
        "Microsoft JhengHei",
        "PingFang TC",
        "Noto Sans CJK TC",
        "SimHei",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
else:
    matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans"]

# =========================
# UI text
# =========================
UI = {
    "English": {
        "info1": "This app is the main control center for TAIVAS.",
        "info2": "It combines country logic, city profiles, weather simulation, and energy dashboard controls.",
        "country_logic": "Country Logic",
        "city_profile": "City Profile",
        "current_inputs": "Current Inputs",
        "weather_mode": "Weather Mode",
        "live_weather": "Live Weather",
        "override_mode": "Scenario Override",
        "scenario": "Extreme Scenario",
        "normal": "Normal",
        "heat_wave": "Heat Wave",
        "storm": "Storm",
        "cold_wave": "Cold Wave",
        "blizzard": "Blizzard",
        "typhoon": "Typhoon",
        "weather_status": "Weather Status",
        "temperature": "Temperature",
        "wind_speed": "Wind Speed",
        "solar_radiation": "Solar Radiation",
        "precipitation": "Precipitation",
        "humidity": "Humidity",
        "system_performance": "System Performance",
        "energy_shortfall": "Energy Shortfall",
        "renewable_utilization": "Renewable Utilization",
        "system_efficiency": "System Efficiency",
        "grid_dependency": "Grid Dependency",
        "energy_demand_supply": "Energy Demand vs Supply",
        "battery_storage_level": "Battery Storage Level",
        "grid_stability": "Grid Stability",
        "energy_mix": "Energy Mix Breakdown",
        "ai_recommendation": "TAIVAS Recommendation",
        "demand": "Demand",
        "renewable": "Renewable",
        "final_supply": "Final Supply",
        "solar_label": "Solar",
        "wind_label": "Wind",
        "geothermal_label": "Geothermal",
        "hydro_label": "Hydropower",
        "hour": "Hour",
        "energy": "Energy",
        "stored_energy": "Stored Energy",
        "supply_minus_demand": "Supply - Demand",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "country_model": "Country Model",
        "balanced": "Current configuration is relatively balanced.",
        "detected": "System instability detected. Suggested improvements:",
        "sunny": "Sunny",
        "cloudy": "Cloudy",
    },
    "中文": {
        "info1": "這是 TAIVAS 的主要能源控制中心。",
        "info2": "它整合了國家邏輯、城市設定、天氣模擬與能源控制台功能。",
        "country_logic": "國家邏輯",
        "city_profile": "城市設定",
        "current_inputs": "目前輸入參數",
        "weather_mode": "天氣模式",
        "live_weather": "真實天氣",
        "override_mode": "情境覆寫",
        "scenario": "極端情境",
        "normal": "正常",
        "heat_wave": "熱浪",
        "storm": "暴風雨",
        "cold_wave": "寒流",
        "blizzard": "暴風雪",
        "typhoon": "颱風",
        "weather_status": "天氣狀態",
        "temperature": "溫度",
        "wind_speed": "風速",
        "solar_radiation": "太陽輻射",
        "precipitation": "降水",
        "humidity": "濕度",
        "system_performance": "系統表現",
        "energy_shortfall": "能源缺口",
        "renewable_utilization": "再生能源利用率",
        "system_efficiency": "系統效率",
        "grid_dependency": "電網依賴度",
        "energy_demand_supply": "能源需求與供給",
        "battery_storage_level": "電池儲能變化",
        "grid_stability": "電網穩定度",
        "energy_mix": "能源組成分析",
        "ai_recommendation": "TAIVAS 建議",
        "demand": "需求",
        "renewable": "再生能源",
        "final_supply": "最終供給",
        "solar_label": "太陽能",
        "wind_label": "風能",
        "geothermal_label": "地熱",
        "hydro_label": "水力",
        "hour": "小時",
        "energy": "能源",
        "stored_energy": "儲存能源",
        "supply_minus_demand": "供給 - 需求",
        "latitude": "緯度",
        "longitude": "經度",
        "country_model": "國家模型",
        "balanced": "目前配置相對平衡。",
        "detected": "偵測到系統不穩定，建議可考慮以下調整：",
        "sunny": "晴天",
        "cloudy": "陰天",
    },
    "Deutsch": {
        "info1": "Dies ist das Hauptkontrollzentrum von TAIVAS.",
        "info2": "Es kombiniert Länderlogik, Stadtprofile, Wettersimulation und Energie-Dashboard-Steuerung.",
        "country_logic": "Länderlogik",
        "city_profile": "Stadtprofil",
        "current_inputs": "Aktuelle Eingaben",
        "weather_mode": "Wettermodus",
        "live_weather": "Live-Wetter",
        "override_mode": "Szenario-Override",
        "scenario": "Extremszenario",
        "normal": "Normal",
        "heat_wave": "Hitzewelle",
        "storm": "Sturm",
        "cold_wave": "Kältewelle",
        "blizzard": "Schneesturm",
        "typhoon": "Taifun",
        "weather_status": "Wetterstatus",
        "temperature": "Temperatur",
        "wind_speed": "Windgeschwindigkeit",
        "solar_radiation": "Solarstrahlung",
        "precipitation": "Niederschlag",
        "humidity": "Luftfeuchtigkeit",
        "system_performance": "Systemleistung",
        "energy_shortfall": "Energieengpass",
        "renewable_utilization": "Nutzung erneuerbarer Energien",
        "system_efficiency": "Systemeffizienz",
        "grid_dependency": "Netzabhängigkeit",
        "energy_demand_supply": "Energienachfrage vs. Versorgung",
        "battery_storage_level": "Batteriespeicherstand",
        "grid_stability": "Netzstabilität",
        "energy_mix": "Energiemix",
        "ai_recommendation": "TAIVAS Empfehlung",
        "demand": "Nachfrage",
        "renewable": "Erneuerbar",
        "final_supply": "Endversorgung",
        "solar_label": "Solar",
        "wind_label": "Wind",
        "geothermal_label": "Geothermie",
        "hydro_label": "Wasserkraft",
        "hour": "Stunde",
        "energy": "Energie",
        "stored_energy": "Gespeicherte Energie",
        "supply_minus_demand": "Versorgung - Nachfrage",
        "latitude": "Breitengrad",
        "longitude": "Längengrad",
        "country_model": "Ländermodell",
        "balanced": "Die aktuelle Konfiguration ist relativ ausgewogen.",
        "detected": "Systeminstabilität erkannt. Empfohlene Verbesserungen:",
        "sunny": "Sonnig",
        "cloudy": "Bewölkt",
    },
    "Suomi": {
        "info1": "Tämä on TAIVASin pääohjauskeskus.",
        "info2": "Se yhdistää maalogiikan, kaupunkiprofiilit, sääsimulaation ja energiadashboard-ohjauksen.",
        "country_logic": "Maalogiikka",
        "city_profile": "Kaupunkiprofiili",
        "current_inputs": "Nykyiset syötteet",
        "weather_mode": "Säätila",
        "live_weather": "Live-sää",
        "override_mode": "Skenaarion ohitus",
        "scenario": "Ääriskenaario",
        "normal": "Normaali",
        "heat_wave": "Helleaalto",
        "storm": "Myrsky",
        "cold_wave": "Kylmä aalto",
        "blizzard": "Lumimyrsky",
        "typhoon": "Taifuuni",
        "weather_status": "Säätila",
        "temperature": "Lämpötila",
        "wind_speed": "Tuulen nopeus",
        "solar_radiation": "Auringonsäteily",
        "precipitation": "Sademäärä",
        "humidity": "Kosteus",
        "system_performance": "Järjestelmän suorituskyky",
        "energy_shortfall": "Energiavaje",
        "renewable_utilization": "Uusiutuvan energian käyttöaste",
        "system_efficiency": "Järjestelmän tehokkuus",
        "grid_dependency": "Verkkoriippuvuus",
        "energy_demand_supply": "Energian kysyntä vs tarjonta",
        "battery_storage_level": "Akun varaustaso",
        "grid_stability": "Verkon vakaus",
        "energy_mix": "Energiayhdistelmä",
        "ai_recommendation": "TAIVAS-suositus",
        "demand": "Kysyntä",
        "renewable": "Uusiutuva",
        "final_supply": "Lopullinen tarjonta",
        "solar_label": "Aurinko",
        "wind_label": "Tuuli",
        "geothermal_label": "Geoterminen",
        "hydro_label": "Vesivoima",
        "hour": "Tunti",
        "energy": "Energia",
        "stored_energy": "Varastoitu energia",
        "supply_minus_demand": "Tarjonta - kysyntä",
        "latitude": "Leveysaste",
        "longitude": "Pituusaste",
        "country_model": "Maamalli",
        "balanced": "Nykyinen kokoonpano on melko tasapainoinen.",
        "detected": "Järjestelmän epävakautta havaittu. Suositellut parannukset:",
        "sunny": "Aurinkoinen",
        "cloudy": "Pilvinen",
    },
    "Schweizerdeutsch": {
        "info1": "Das isch s Hauptkontrollzentrum vo TAIVAS.",
        "info2": "Es verbindet Länderlogik, Stadtprofile, Wättersimulation und Energie-Dashboard-Steuerig.",
        "country_logic": "Länderlogik",
        "city_profile": "Stadtprofil",
        "current_inputs": "Aktuelli Iigabe",
        "weather_mode": "Wättermodus",
        "live_weather": "Live-Wätter",
        "override_mode": "Szenario-Override",
        "scenario": "Extremszenario",
        "normal": "Normal",
        "heat_wave": "Hitzewälle",
        "storm": "Sturm",
        "cold_wave": "Chältiwälle",
        "blizzard": "Schneesturm",
        "typhoon": "Taifun",
        "weather_status": "Wätterstatus",
        "temperature": "Temperatur",
        "wind_speed": "Windgschwindigkeit",
        "solar_radiation": "Solarstrahlig",
        "precipitation": "Niederschlag",
        "humidity": "Luftfeuchtigkeit",
        "system_performance": "Systemleistig",
        "energy_shortfall": "Energie-Defizit",
        "renewable_utilization": "Nutzig vo erneuerbare Energie",
        "system_efficiency": "System-Effizienz",
        "grid_dependency": "Netz-Abhängigkeit",
        "energy_demand_supply": "Energiebedarf vs Versorgig",
        "battery_storage_level": "Batterie-Speicherstand",
        "grid_stability": "Netzstabilität",
        "energy_mix": "Energiemix",
        "ai_recommendation": "TAIVAS-Empfählig",
        "demand": "Bedarf",
        "renewable": "Erneuerbar",
        "final_supply": "Finali Versorgig",
        "solar_label": "Solar",
        "wind_label": "Wind",
        "geothermal_label": "Geothermie",
        "hydro_label": "Wasserkraft",
        "hour": "Stund",
        "energy": "Energie",
        "stored_energy": "Gspeichereti Energie",
        "supply_minus_demand": "Versorgig - Bedarf",
        "latitude": "Breitegrad",
        "longitude": "Längigrad",
        "country_model": "Ländermodell",
        "balanced": "D aktuelli Konfiguration isch relativ usgwoge.",
        "detected": "Systeminstabilität erkannt. Vorgschlagni Verbessrige:",
        "sunny": "Sunnig",
        "cloudy": "Bewölkt",
    },
    "Íslenska": {
        "info1": "Þetta er aðalstjórnstöð TAIVAS.",
        "info2": "Hún sameinar landslógík, borgarsnið, veðurhermun og orkustjórnborð.",
        "country_logic": "Landslógík",
        "city_profile": "Borgarsnið",
        "current_inputs": "Núverandi inntök",
        "weather_mode": "Veðurhamur",
        "live_weather": "Rauntímaveður",
        "override_mode": "Yfirskrifa sviðsmynd",
        "scenario": "Öfgasviðsmynd",
        "normal": "Venjulegt",
        "heat_wave": "Hitabylgja",
        "storm": "Stormur",
        "cold_wave": "Kuldabylgja",
        "blizzard": "Snjóbylur",
        "typhoon": "Fellibylur",
        "weather_status": "Veðurstaða",
        "temperature": "Hitastig",
        "wind_speed": "Vindhraði",
        "solar_radiation": "Sólgeislun",
        "precipitation": "Úrkoma",
        "humidity": "Raki",
        "system_performance": "Afköst kerfis",
        "energy_shortfall": "Orkuskortur",
        "renewable_utilization": "Nýting endurnýjanlegrar orku",
        "system_efficiency": "Kerfisnýtni",
        "grid_dependency": "Háð rafkerfi",
        "energy_demand_supply": "Orkuþörf vs framboð",
        "battery_storage_level": "Staða rafhlöðugeymslu",
        "grid_stability": "Stöðugleiki rafkerfis",
        "energy_mix": "Orkublanda",
        "ai_recommendation": "TAIVAS tillaga",
        "demand": "Eftirspurn",
        "renewable": "Endurnýjanlegt",
        "final_supply": "Lokaframboð",
        "solar_label": "Sól",
        "wind_label": "Vindur",
        "geothermal_label": "Jarðhiti",
        "hydro_label": "Vatnsafl",
        "hour": "Klst",
        "energy": "Orka",
        "stored_energy": "Geymd orka",
        "supply_minus_demand": "Framboð - eftirspurn",
        "latitude": "Breiddargráða",
        "longitude": "Lengdargráða",
        "country_model": "Landsmódel",
        "balanced": "Núverandi uppsetning er nokkuð vel í jafnvægi.",
        "detected": "Óstöðugleiki í kerfi greindur. Tillögur að úrbótum:",
        "sunny": "Sólríkt",
        "cloudy": "Skýjað",
    },
}
ui = UI.get(language, UI["English"])

# =========================
# Helpers
# =========================
def fetch_weather(lat: float, lon: float):
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urllib.parse.urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,wind_speed_10m,shortwave_radiation,precipitation,relative_humidity_2m",
                "forecast_days": 1,
                "timezone": "auto",
            }
        )
    )
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def safe_country_desc(key: str) -> str:
    return t.get("country_descriptions", {}).get(
        key,
        country_logic.get(key, {}).get("description", f"{key} energy model"),
    )

def get_bias(key: str, field: str, default: float) -> float:
    return float(country_logic.get(key, {}).get(field, default))

# =========================
# Style
# =========================
st.markdown(
    """
    <style>
    .taivas-box {
        background: #0d1b3d;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Header
# =========================
title_text = t.get("title", "TAIVAS Energy Control Center")
subtitle_text = t.get("subtitle", "AI-driven energy resilience and recovery dashboard")

st.title(title_text)
st.caption(subtitle_text)
st.markdown(
    "<div class='taivas-box'><div>{}</div><div style='margin-top:8px'>{}</div></div>".format(
        ui["info1"], ui["info2"]
    ),
    unsafe_allow_html=True,
)

# =========================
# Country / City
# =========================
country_keys = list(country_logic.keys())
country_labels = t.get("countries", {})
city_labels = t.get("cities", {})

country_display_map = {country_labels.get(k, k): k for k in country_keys}
country_display = st.sidebar.selectbox(
    t.get("country", "Country"),
    list(country_display_map.keys())
)
country_key = country_display_map[country_display]

available_cities = [
    city_key for city_key, city_data in city_profiles.items()
    if city_data.get("country") == country_key
]
city_display_map = {city_labels.get(k, k): k for k in available_cities}
city_display = st.sidebar.selectbox(
    t.get("city", "City"),
    list(city_display_map.keys())
)
city_key = city_display_map[city_display]
city_data = city_profiles[city_key]

# =========================
# Inputs
# =========================
population = st.sidebar.slider(t.get("population", "Population"), 10000, 5000000, 500000, step=50000)
solar_capacity = st.sidebar.slider(t.get("solar", "Solar Capacity (MW)"), 0, 500, 120, step=10)
wind_capacity = st.sidebar.slider(t.get("wind", "Wind Capacity (MW)"), 0, 500, 80, step=10)
geothermal_capacity = st.sidebar.slider(t.get("geothermal", "Geothermal Capacity (MW)"), 0, 500, 60, step=10)
hydro_capacity = st.sidebar.slider(t.get("hydro", "Hydropower Capacity (MW)"), 0, 500, 70, step=10)
battery_capacity = st.sidebar.slider(t.get("battery", "Battery Storage (MWh)"), 0, 2000, 300, step=50)

weather_mode = st.sidebar.selectbox(
    ui["weather_mode"],
    [ui["live_weather"], ui["override_mode"]]
)
scenario = st.sidebar.selectbox(
    ui["scenario"],
    [ui["normal"], ui["heat_wave"], ui["storm"], ui["cold_wave"], ui["blizzard"], ui["typhoon"]]
)

# =========================
# Country / City info
# =========================
st.subheader(f"{ui['country_logic']}: {country_display}")
st.write(safe_country_desc(country_key))

st.subheader(f"{ui['city_profile']}: {city_display}")
st.write(f"{ui['latitude']}: {city_data.get('lat', '-')}")
st.write(f"{ui['longitude']}: {city_data.get('lon', '-')}")
st.write(f"{ui['country_model']}: {city_data.get('country', '-')}")

# =========================
# Weather
# =========================
try:
    weather_data = fetch_weather(city_data["lat"], city_data["lon"])
    h = weather_data["hourly"]
    temperature = np.array(h["temperature_2m"][:24], dtype=float)
    wind_speed = np.array(h["wind_speed_10m"][:24], dtype=float)
    solar_radiation = np.array(h["shortwave_radiation"][:24], dtype=float)
    precipitation = np.array(h["precipitation"][:24], dtype=float)
    humidity = np.array(h["relative_humidity_2m"][:24], dtype=float)
except Exception:
    temperature = np.array([24] * 24, dtype=float)
    wind_speed = np.array([5] * 24, dtype=float)
    solar_radiation = np.array(
        [0, 0, 0, 0, 0, 40, 120, 220, 380, 520, 650, 740, 780, 720, 600, 420, 240, 90, 20, 0, 0, 0, 0, 0],
        dtype=float,
    )
    precipitation = np.array([0] * 24, dtype=float)
    humidity = np.array([70] * 24, dtype=float)

if weather_mode == ui["override_mode"]:
    if scenario == ui["heat_wave"]:
        temperature = temperature + 8
        solar_radiation = solar_radiation * 1.05
    elif scenario == ui["storm"]:
        solar_radiation = solar_radiation * 0.35
        wind_speed = wind_speed * 1.25
        precipitation = precipitation + 10
    elif scenario == ui["cold_wave"]:
        temperature = temperature - 10
        solar_radiation = solar_radiation * 0.75
    elif scenario == ui["blizzard"]:
        temperature = temperature - 12
        solar_radiation = solar_radiation * 0.20
        wind_speed = wind_speed * 1.15
        precipitation = precipitation + 5
    elif scenario == ui["typhoon"]:
        solar_radiation = solar_radiation * 0.15
        wind_speed = wind_speed * 1.50
        precipitation = precipitation + 25

hours = np.arange(24)

avg_temp = float(np.mean(temperature))
avg_wind = float(np.mean(wind_speed))
avg_rad = float(np.mean(solar_radiation))
total_precip = float(np.sum(precipitation))
avg_humidity = float(np.mean(humidity))

if weather_mode == ui["override_mode"]:
    weather_label = scenario
else:
    if total_precip > 20:
        weather_label = ui["storm"]
    elif avg_rad < 180:
        weather_label = ui["cloudy"]
    else:
        weather_label = ui["sunny"]

if weather_label == ui["sunny"]:
    weather_icon = "☀️"
elif weather_label == ui["cloudy"]:
    weather_icon = "☁️"
elif weather_label in [ui["storm"], ui["typhoon"]]:
    weather_icon = "⛈️"
elif weather_label == ui["blizzard"]:
    weather_icon = "🌨️"
elif weather_label == ui["cold_wave"]:
    weather_icon = "🥶"
else:
    weather_icon = "🌦️"

st.info(f"{ui.get('weather_status', 'Weather Status')}: {weather_icon} {weather_label}")

w1, w2, w3, w4, w5 = st.columns(5)
w1.metric(ui["temperature"], f"{avg_temp:.1f} °C")
w2.metric(ui["wind_speed"], f"{avg_wind:.1f} m/s")
w3.metric(ui["solar_radiation"], f"{avg_rad:.0f} W/m²")
w4.metric(ui["precipitation"], f"{total_precip:.1f} mm")
w5.metric(ui["humidity"], f"{avg_humidity:.0f}%")

# =========================
# Simulation
# =========================
solar_bias = get_bias(country_key, "solar_bias", 1.0)
wind_bias = get_bias(country_key, "wind_bias", 1.0)
geo_bias = get_bias(country_key, "geo_bias", 0.3)
hydro_bias = get_bias(country_key, "hydro_bias", 0.5)

desc = safe_country_desc(country_key).lower()
heat_sens = 0.25
cool_sens = 0.25

if any(x in desc for x in ["cooling", "高濕", "島嶼", "kühl", "chüel", "jääh", "kæli"]):
    cool_sens = 0.85
    heat_sens = 0.20
elif any(x in desc for x in ["cold", "nordic", "寒冷", "北歐", "heating", "冬季", "heiz", "lämm", "hitun"]):
    heat_sens = 1.00
    cool_sens = 0.08
elif any(x in desc for x in ["geothermal", "地熱", "geothermie", "jarðhiti"]):
    heat_sens = 0.95
    cool_sens = 0.02
elif any(x in desc for x in ["alpine", "阿爾卑斯", "alp", "alpa"]):
    heat_sens = 0.75
    cool_sens = 0.15

base_curve = np.array([
    0.78, 0.74, 0.72, 0.70, 0.70, 0.75,
    0.90, 1.05, 1.20, 1.32, 1.42, 1.48,
    1.55, 1.50, 1.40, 1.30, 1.18, 1.08,
    0.98, 0.90, 0.86, 0.82, 0.80, 0.79
])

base_demand = population / 4500.0
heating_load = np.maximum(0, (18 - temperature)) * heat_sens * 0.9
cooling_load = np.maximum(0, (temperature - 24)) * cool_sens * 0.9
demand = base_demand * base_curve + heating_load + cooling_load

solar_cf = np.clip(solar_radiation / 800.0, 0, 1) * solar_bias
solar_cf = np.clip(solar_cf, 0, 1.25)
solar = solar_capacity * solar_cf

cut_in = 3.0
rated = 12.0
wind_cf = np.clip((wind_speed - cut_in) / (rated - cut_in), 0, 1) ** 1.4
wind_cf = np.clip(wind_cf * wind_bias, 0, 1.25)
wind = wind_capacity * wind_cf

geothermal_cf = np.array([0.92] * 24) * geo_bias
geothermal = geothermal_capacity * geothermal_cf

hydro_pattern = np.array([
    0.75, 0.75, 0.75, 0.75, 0.76, 0.78,
    0.82, 0.86, 0.90, 0.92, 0.94, 0.96,
    0.96, 0.95, 0.93, 0.90, 0.88, 0.86,
    0.84, 0.82, 0.80, 0.78, 0.76, 0.75
])
hydro_weather_boost = min(1.15, 1 + total_precip / 200)
hydro = hydro_capacity * hydro_pattern * hydro_bias * hydro_weather_boost

renewable_supply = solar + wind + geothermal + hydro

battery_level = 0.0
battery_levels = []
final_supply = []
grid_support_used = []
grid_support_capacity = 140

for i in range(24):
    supply = renewable_supply[i]
    diff = supply - demand[i]

    if diff > 0:
        battery_level = min(battery_capacity, battery_level + diff)
        grid_used = 0.0
    else:
        use_battery = min(battery_level, abs(diff))
        battery_level -= use_battery
        supply += use_battery

        remaining_gap = max(0.0, demand[i] - supply)
        use_grid = min(grid_support_capacity, remaining_gap)
        supply += use_grid
        grid_used = use_grid

    battery_levels.append(battery_level)
    final_supply.append(supply)
    grid_support_used.append(grid_used)

battery_levels = np.array(battery_levels)
final_supply = np.array(final_supply)
grid_support_used = np.array(grid_support_used)

shortfall = np.maximum(demand - final_supply, 0).sum()
renewable_ratio = min((renewable_supply.sum() / demand.sum()) * 100, 100)
system_efficiency = max(0, 100 - (shortfall / demand.sum() * 100))
grid_dependency = (grid_support_used.sum() / demand.sum()) * 100

# =========================
# Current Inputs
# =========================
st.subheader(ui["current_inputs"])
st.write(f"{t.get('population', 'Population')}: {population}")
st.write(f"{t.get('solar', 'Solar Capacity (MW)')}: {solar_capacity}")
st.write(f"{t.get('wind', 'Wind Capacity (MW)')}: {wind_capacity}")
st.write(f"{t.get('geothermal', 'Geothermal Capacity (MW)')}: {geothermal_capacity}")
st.write(f"{t.get('hydro', 'Hydropower Capacity (MW)')}: {hydro_capacity}")
st.write(f"{t.get('battery', 'Battery Storage (MWh)')}: {battery_capacity}")

# =========================
# KPI
# =========================
st.subheader(ui["system_performance"])
k1, k2, k3, k4 = st.columns(4)
k1.metric(ui["energy_shortfall"], f"{shortfall:.1f} MWh")
k2.metric(ui["renewable_utilization"], f"{renewable_ratio:.1f}%")
k3.metric(ui["system_efficiency"], f"{system_efficiency:.1f}%")
k4.metric(ui["grid_dependency"], f"{grid_dependency:.1f}%")

# =========================
# Charts
# =========================
plt.style.use("dark_background")

c1, c2 = st.columns(2)

with c1:
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    fig1.patch.set_facecolor("#0B1220")
    ax1.set_facecolor("#0B1220")
    ax1.plot(hours, demand, label=ui["demand"], linewidth=2.5, color="#60A5FA")
    ax1.plot(hours, renewable_supply, label=ui["renewable"], linewidth=2.5, color="#F59E0B")
    ax1.plot(hours, final_supply, label=ui["final_supply"], linewidth=2.5, color="#22C55E")
    ax1.set_title(ui["energy_demand_supply"])
    ax1.set_xlabel(ui["hour"])
    ax1.set_ylabel(ui["energy"])
    ax1.grid(alpha=0.15)
    ax1.legend()
    st.pyplot(fig1)

with c2:
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    fig2.patch.set_facecolor("#0B1220")
    ax2.set_facecolor("#0B1220")
    ax2.fill_between(hours, battery_levels, color="#22C55E", alpha=0.35)
    ax2.plot(hours, battery_levels, color="#22C55E", linewidth=2.5)
    ax2.set_title(ui["battery_storage_level"])
    ax2.set_xlabel(ui["hour"])
    ax2.set_ylabel(ui["stored_energy"])
    ax2.grid(alpha=0.15)
    st.pyplot(fig2)

fig3, ax3 = plt.subplots(figsize=(12, 4))
fig3.patch.set_facecolor("#0B1220")
ax3.set_facecolor("#0B1220")
stability = final_supply - demand
colors = ["#22C55E" if x >= 0 else "#EF4444" for x in stability]
ax3.bar(hours, stability, color=colors)
ax3.axhline(0, color="white", linewidth=1, alpha=0.7)
ax3.set_title(ui["grid_stability"])
ax3.set_xlabel(ui["hour"])
ax3.set_ylabel(ui["supply_minus_demand"])
ax3.grid(axis="y", alpha=0.15)
st.pyplot(fig3)

st.subheader(ui["energy_mix"])
fig4, ax4 = plt.subplots(figsize=(7, 4))
fig4.patch.set_facecolor("#0B1220")
ax4.set_facecolor("#0B1220")
mix_values = [solar.sum(), wind.sum(), geothermal.sum(), hydro.sum()]
mix_labels = [
    ui["solar_label"],
    ui["wind_label"],
    ui["geothermal_label"],
    ui["hydro_label"],
]
mix_colors = ["#FACC15", "#38BDF8", "#F97316", "#3B82F6"]
ax4.pie(mix_values, labels=mix_labels, autopct="%1.1f%%", colors=mix_colors)
st.pyplot(fig4)

# =========================
# Recommendation
# =========================
st.subheader(ui["ai_recommendation"])

if shortfall < 50:
    st.success(ui["balanced"])
else:
    deficit = shortfall
    solar_add = deficit / max(24 * max(solar_bias, 0.2), 1)
    wind_add = deficit / max(28 * max(wind_bias, 0.2), 1)
    geothermal_add = deficit / max(30 * max(geo_bias, 0.15), 1)
    hydro_add = deficit / max(35 * max(hydro_bias, 0.15), 1)

    st.warning(ui["detected"])
    a1, a2 = st.columns(2)
    with a1:
        st.write(f"☀️ {ui['solar_label']}: **+{solar_add:.0f} MW**")
        st.write(f"🌬️ {ui['wind_label']}: **+{wind_add:.0f} MW**")
    with a2:
        st.write(f"🌋 {ui['geothermal_label']}: **+{geothermal_add:.0f} MW**")
        st.write(f"💧 {ui['hydro_label']}: **+{hydro_add:.0f} MW**")