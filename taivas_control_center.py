from io import StringIO
import json

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Dark-mode friendly chart defaults for Streamlit dashboards.
plt.rcParams.update({
    "text.color": "#E5E7EB",
    "axes.labelcolor": "#E5E7EB",
    "axes.edgecolor": "#94A3B8",
    "xtick.color": "#CBD5E1",
    "ytick.color": "#CBD5E1",
    "axes.titlecolor": "#F8FAFC",
    "figure.facecolor": "none",
    "axes.facecolor": "none",
})

from modules.charts import make_donut_chart
from modules.recommendations import recommendation_lines
from modules.energy_security import apply_energy_security_layer, ENERGY_SECURITY_SCENARIOS
from modules.survival_timeline import simulate_survival_timeline
from concept_lab_components import (
    render_thermal_principle_simulation,
    render_phase_change_buffer_concept,
    render_ground_thermal_sink_concept,
    render_distributed_thermal_control_concept,
    render_distributed_harvesting_buffering_concept,
)

st.set_page_config(page_title="TAIVAS Energy Control Center", layout="wide")

if "ui_lang" not in st.session_state:
    st.session_state["ui_lang"] = "English"

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
        "Turku": {"lat": 60.4518, "lon": 22.2666, "population": 196000, "country_model": "Winter Reliability Model"},
    },
    "Sweden": {
        "Stockholm": {"lat": 59.3293, "lon": 18.0686, "population": 975000, "country_model": "Nordic Urban Resilience Model"},
        "Gothenburg": {"lat": 57.7089, "lon": 11.9746, "population": 587000, "country_model": "Nordic Urban Resilience Model"},
        "Malmo": {"lat": 55.6050, "lon": 13.0038, "population": 362000, "country_model": "Nordic Urban Resilience Model"},
    },
    "Norway": {
        "Oslo": {"lat": 59.9139, "lon": 10.7522, "population": 717000, "country_model": "Nordic Hydro Resilience Model"},
        "Bergen": {"lat": 60.3913, "lon": 5.3221, "population": 289000, "country_model": "Nordic Hydro Resilience Model"},
        "Trondheim": {"lat": 63.4305, "lon": 10.3951, "population": 214000, "country_model": "Nordic Hydro Resilience Model"},
    },
    "Denmark": {
        "Copenhagen": {"lat": 55.6761, "lon": 12.5683, "population": 654000, "country_model": "Coastal Flexibility Model"},
        "Aarhus": {"lat": 56.1629, "lon": 10.2039, "population": 285000, "country_model": "Coastal Flexibility Model"},
        "Odense": {"lat": 55.4038, "lon": 10.4024, "population": 180000, "country_model": "Coastal Flexibility Model"},
    },
    "Iceland": {
        "Reykjavik": {"lat": 64.1466, "lon": -21.9426, "population": 139000, "country_model": "Geothermal Continuity Model"},
        "Akureyri": {"lat": 65.6885, "lon": -18.1262, "population": 19000, "country_model": "Geothermal Continuity Model"},
        "Keflavik": {"lat": 64.0049, "lon": -22.5624, "population": 16000, "country_model": "Geothermal Continuity Model"},
    },
    "Germany": {
        "Berlin": {"lat": 52.5200, "lon": 13.4050, "population": 3570000, "country_model": "Industrial Transition Model"},
        "Hamburg": {"lat": 53.5511, "lon": 9.9937, "population": 1910000, "country_model": "Industrial Transition Model"},
        "Munich": {"lat": 48.1351, "lon": 11.5820, "population": 1510000, "country_model": "Industrial Transition Model"},
        "Frankfurt": {"lat": 50.1109, "lon": 8.6821, "population": 776000, "country_model": "Industrial Transition Model"},
    },
    "Switzerland": {
        "Zurich": {"lat": 47.3769, "lon": 8.5417, "population": 435000, "country_model": "Alpine Stability Model"},
        "Geneva": {"lat": 46.2044, "lon": 6.1432, "population": 203000, "country_model": "Alpine Stability Model"},
        "Bern": {"lat": 46.9480, "lon": 7.4474, "population": 134000, "country_model": "Alpine Stability Model"},
        "Basel": {"lat": 47.5596, "lon": 7.5886, "population": 177000, "country_model": "Alpine Stability Model"},
    },
    "Netherlands": {
        "Amsterdam": {"lat": 52.3676, "lon": 4.9041, "population": 922000, "country_model": "Delta Resilience Model"},
        "Rotterdam": {"lat": 51.9244, "lon": 4.4777, "population": 671000, "country_model": "Delta Resilience Model"},
        "The Hague": {"lat": 52.0705, "lon": 4.3007, "population": 565000, "country_model": "Delta Resilience Model"},
    },
    "Belgium": {
        "Brussels": {"lat": 50.8503, "lon": 4.3517, "population": 185000, "country_model": "Western Europe Stability Model"},
        "Antwerp": {"lat": 51.2194, "lon": 4.4025, "population": 530000, "country_model": "Western Europe Stability Model"},
        "Ghent": {"lat": 51.0543, "lon": 3.7174, "population": 265000, "country_model": "Western Europe Stability Model"},
    },
    "Austria": {
        "Vienna": {"lat": 48.2082, "lon": 16.3738, "population": 2000000, "country_model": "Central Europe Reliability Model"},
        "Graz": {"lat": 47.0707, "lon": 15.4395, "population": 291000, "country_model": "Central Europe Reliability Model"},
        "Linz": {"lat": 48.3069, "lon": 14.2858, "population": 206000, "country_model": "Central Europe Reliability Model"},
    },
    "France": {
        "Paris": {"lat": 48.8566, "lon": 2.3522, "population": 2100000, "country_model": "Western Europe Flex Model"},
        "Lyon": {"lat": 45.7640, "lon": 4.8357, "population": 522000, "country_model": "Western Europe Flex Model"},
        "Marseille": {"lat": 43.2965, "lon": 5.3698, "population": 877000, "country_model": "Western Europe Flex Model"},
    },
