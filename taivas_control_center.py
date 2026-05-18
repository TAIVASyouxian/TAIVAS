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

# UI-ONLY CHANGE START
# TAIVAS UI Design System / UI Rules
# This section is an internal design reference for future TAIVAS UI work.
# It is documentation only: it must not drive calculations, scenario logic, or data flow.
TAIVAS_UI_DESIGN_SYSTEM = """
TAIVAS FULL INTERFACE DESIGN DIRECTION

Core Principle:
- TAIVAS is a climate-energy resilience decision-support simulator.
- Every section should help users understand:
  1. What is happening?
  2. What is changing compared with baseline?
  3. What risk may increase?
  4. What should be reviewed first?
  5. What is only a scenario-based estimate?
- The interface must be clear, calm, professional, decision-support focused,
  understandable for non-engineers, and useful for officials, operators,
  researchers, and facility managers.
- Information clarity comes before visual effects.

Avoid:
- Overly technical wording, panic language, fake precision, flashy/gamer-style UI.
- Hardware-blueprint claims or pretending the model guarantees outcomes.
- Video game HUD, cyberpunk arcade, toy dashboard, overdecorated sci-fi cockpit.
- Academic PDF density or plain Excel-dashboard flatness.

Global Section Structure:
1. Plain-language title.
2. One-sentence explanation.
3. Key metric or visual.
4. Operational meaning.
5. Model boundary / limitation when needed.

Primary UI Layers:
1. Situation Awareness Layer
   Purpose: scenario impact, risk state, system pressure, approaching disruption.
   Examples: typhoon/storm visual, extreme-weather influence map, risk state panel.

2. Energy System Layer
   Purpose: demand, supply, storage, energy gap, grid dependency, renewable contribution.
   Examples: energy balance cards, stress chain, storage buffer depletion.

3. Infrastructure Resilience Layer
   Purpose: subsystem mechanisms that reduce risk or stabilize the system.
   Examples: cold-weather thermal buffer, passive heat recovery concept,
   cold-climate stabilization layer.

4. Decision Support Layer
   Purpose: recommendations, warnings, risk tier, model boundaries, user interpretation.
   Examples: recommendation card, public risk summary, operational priority,
   model boundary notice.

Preferred Plain-English Terms:
- Energy Gap, Backup Grid Need, Renewable Share, Battery Reserve, System Stability.
- Cold-Weather Buffer, Heat Stress, Storm Impact, Scenario Comparison.
- Operational Summary, Public Risk Summary.

Terms To Avoid Or Explain:
- multipliers, coupled dynamics, thermodynamic exchange layer, resilience coefficient,
  nonlinear impact index, autonomous prediction, guaranteed forecast,
  validated engineering performance.

Section Direction:
- Header: TAIVAS / Climate & Energy Resilience Platform /
  Decision-Support Simulation Environment. Premium, calm, not oversized.
- Quick Start: choose location, select scenario, review results.
- Public Risk Communication Summary: Public Message, Decision Brief, Technical Basis,
  and the disclaimer "This is scenario-based decision-support information,
  not a confirmed prediction."
- Operational Summary: system stability, battery reserve, renewable supply,
  backup support need.
- Main System Status: Demand, Final Supply, Energy Gap, System Stability.
- Scenario Comparison: core identity of TAIVAS; baseline vs extreme scenario with
  demand, supply, energy gap, battery reserve, backup grid need, and risk tier changes.
- Risk Tier / Resilience Status: Low, Moderate, High, Critical in a calm analytical tone.
- Explainability Panel: what caused stress, which metric changed most,
  what should be checked first.
- Battery / Storage: Battery Reserve, Reserve Days, Energy Gap Hours, Storage Trend.
- Renewable Mix: Renewable Share, Dominant Source, Renewable Supply,
  with reminder that scenario conditions may reduce actual output when needed.
- Thermal / Concept Lab: concept visualizations, not engineering blueprints.
  Use clear names such as Cold-Weather Thermal Buffer Concept,
  Heat-Stress Cooling Support Concept, Passive Resilience Support Concept.
- Advanced Analytics: available for technical users, but not overwhelming.
- Export / Report: scenario, location, core outputs, risk tier, plain-language summary,
  and model boundary disclaimer.

Color Semantics:
- Blue / cyan: cooling, fresh air, water, stable flow, external environment.
- Green: normal, safe, renewable supply, healthy buffer.
- Yellow / amber: caution, stress rising, limited buffer.
- Orange: high stress, warning, transition to risk.
- Red: critical risk, energy gap, failure pressure, severe disruption.
- Purple: uncertainty, scenario simulation, forecast band.
- Gray / slate: neutral structure, inactive state, baseline.
- Gold: high-value emphasis, protected core, recovery efficiency, controlled priority.

Metric Display Rules:
- Critical values use short label, large numeric value, unit, and one-line interpretation.
- Avoid long paragraphs inside operational panels.
- Prefer short bullets, chips, status labels, and compact cards.

Panel Naming Rules:
- Prefer system-oriented names:
  Storage Buffer Depletion, Cold-Weather Thermal Buffer Concept,
  Scenario Impact Field, Energy Stress Chain, Resilience State, Grid Dependency,
  Renewable Supply Stability, Operational Recommendation.
- Avoid weak names:
  Chart, Graph, Result, Data View, Demo, Toy, Fancy UI.

Animation Rules:
- Allowed: slow pulse for active risk zones, gentle directional flow,
  subtle moving cloud/rain bands, soft glow change based on state,
  lightweight CSS-only animation.
- Not allowed: flashing emergency lights, excessive particles, rapid movement,
  distracting loops, heavy JavaScript animation, external animation libraries.

Model Boundary Rule:
- Whenever a section could be mistaken as a real-world engineering guarantee,
  add a boundary note.
- Use wording like:
  "Scenario-based estimate only."
  "Decision-support output, not a confirmed prediction."
  "Concept visualization only, not validated hardware design."
- Required for public communication, thermal concepts, risk tier,
  forecast-like summaries, and operational recommendations.

Streamlit Cloud Constraints:
- Standard Streamlit + safe HTML/CSS via st.markdown(..., unsafe_allow_html=True).
- Avoid external JS/CDN dependencies, large images, videos, and heavy frontend frameworks.
- Keep CSS lightweight and deployment-safe.

Architecture Rules:
- Keep calculation/simulation logic separate from presentation.
- UI changes must not modify formulas, scenario engine, data structures, CSV parsing,
  forecast flow, export workflow, chart data sources, deployment structure,
  or session_state unless explicitly requested.
- Before editing, classify the target as:
  a) calculation logic, b) data processing, c) UI presentation, or d) mixed-risk logic.
- Clearly mark UI-only changes and prefer modular render functions.
"""

# Major render functions should be annotated with one of:
# Situation Awareness Layer, Energy System Layer, Infrastructure Resilience Layer,
# or Decision Support Layer.
# UI-ONLY CHANGE END

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
    "United Kingdom": {
        "London": {"lat": 51.5072, "lon": -0.1276, "population": 8980000, "country_model": "Island Urban Continuity Model"},
        "Manchester": {"lat": 53.4808, "lon": -2.2426, "population": 568000, "country_model": "Island Urban Continuity Model"},
        "Edinburgh": {"lat": 55.9533, "lon": -3.1883, "population": 506000, "country_model": "Island Urban Continuity Model"},
    },
    "Ireland": {
        "Dublin": {"lat": 53.3498, "lon": -6.2603, "population": 592000, "country_model": "Atlantic Resilience Model"},
        "Cork": {"lat": 51.8985, "lon": -8.4756, "population": 224000, "country_model": "Atlantic Resilience Model"},
        "Galway": {"lat": 53.2707, "lon": -9.0568, "population": 85000, "country_model": "Atlantic Resilience Model"},
    },
    "Spain": {
        "Madrid": {"lat": 40.4168, "lon": -3.7038, "population": 3300000, "country_model": "Southern Heat Stress Model"},
        "Barcelona": {"lat": 41.3851, "lon": 2.1734, "population": 1660000, "country_model": "Southern Heat Stress Model"},
        "Valencia": {"lat": 39.4699, "lon": -0.3763, "population": 792000, "country_model": "Southern Heat Stress Model"},
    },
    "Italy": {
        "Rome": {"lat": 41.9028, "lon": 12.4964, "population": 2740000, "country_model": "Mediterranean Continuity Model"},
        "Milan": {"lat": 45.4642, "lon": 9.1900, "population": 1370000, "country_model": "Mediterranean Continuity Model"},
        "Turin": {"lat": 45.0703, "lon": 7.6869, "population": 848000, "country_model": "Mediterranean Continuity Model"},
    },
    "Portugal": {
        "Lisbon": {"lat": 38.7223, "lon": -9.1393, "population": 545000, "country_model": "Atlantic Heat Buffer Model"},
        "Porto": {"lat": 41.1579, "lon": -8.6291, "population": 231000, "country_model": "Atlantic Heat Buffer Model"},
        "Braga": {"lat": 41.5454, "lon": -8.4265, "population": 193000, "country_model": "Atlantic Heat Buffer Model"},
    },
    "Poland": {
        "Warsaw": {"lat": 52.2297, "lon": 21.0122, "population": 1860000, "country_model": "Eastern Europe Recovery Model"},
        "Krakow": {"lat": 50.0647, "lon": 19.9450, "population": 804000, "country_model": "Eastern Europe Recovery Model"},
        "Wroclaw": {"lat": 51.1079, "lon": 17.0385, "population": 674000, "country_model": "Eastern Europe Recovery Model"},
    },
    "Czech Republic": {
        "Prague": {"lat": 50.0755, "lon": 14.4378, "population": 1380000, "country_model": "Central Europe Reliability Model"},
        "Brno": {"lat": 49.1951, "lon": 16.6068, "population": 398000, "country_model": "Central Europe Reliability Model"},
        "Ostrava": {"lat": 49.8209, "lon": 18.2625, "population": 285000, "country_model": "Central Europe Reliability Model"},
    },
    "USA": {
        "Seattle": {"lat": 47.6062, "lon": -122.3321, "population": 749000, "country_model": "Northwest Resilience Model"},
        "Boston": {"lat": 42.3601, "lon": -71.0589, "population": 654000, "country_model": "Northwest Resilience Model"},
        "New York": {"lat": 40.7128, "lon": -74.0060, "population": 8337000, "country_model": "Northwest Resilience Model"},
    },
}


COUNTRY_NOTES = {
    "Taiwan": "Cooling-heavy island model with strong storage need.",
    "Finland": "Cold-climate resilience model with winter reliability focus.",
    "Sweden": "Nordic urban resilience model with district-scale cold and heat balancing.",
    "Norway": "Hydro-friendly Nordic model with strong resilience potential.",
    "Denmark": "Coastal flexibility model with wind and import balancing sensitivity.",
    "Iceland": "Geothermal continuity model with strong baseload resilience and storm exposure.",
    "Germany": "Industrial transition model with grid balancing importance.",
    "Switzerland": "High-stability alpine model with balanced reserve planning.",
    "Netherlands": "Delta resilience model with logistics and flood-aware infrastructure planning.",
    "Belgium": "Western Europe stability model with dense urban continuity needs.",
    "Austria": "Central Europe reliability model with alpine and urban mixed loads.",
    "France": "Western Europe flex model with large urban loads and diverse generation mix.",
    "United Kingdom": "Island urban continuity model with import and coastal exposure considerations.",
    "Ireland": "Atlantic resilience model with maritime weather variability.",
    "Spain": "Southern heat stress model with cooling-heavy seasonal pressure.",
    "Italy": "Mediterranean continuity model with urban heat and critical facility load complexity.",
    "Portugal": "Atlantic heat buffer model with coastal weather variation.",
    "Poland": "Eastern Europe recovery model with winter load and grid transition pressure.",
    "Czech Republic": "Central Europe reliability model with industrial and urban load balancing.",
    "USA": "Northwest resilience model for cross-market comparison and export testing.",
}


FACILITY_PROFILES = {
    "Long-term Care": {
        "critical_load_share": 0.48,
        "temp_band_c": "20–26",
        "notes": "Temperature stability, life-support continuity, and water systems are highly sensitive.",
        "priority_order": ["Medical", "Heating/Cooling", "Water Systems", "Communications"],
        "critical_split": {"Medical": 0.34, "Heating/Cooling": 0.28, "Water Systems": 0.22, "Communications": 0.16},
        "failure_tolerance_hours": 6,
    },
    "Hospital": {
        "critical_load_share": 0.58,
        "temp_band_c": "19–24",
        "notes": "ICU, surgery, pharmacy refrigeration, and core communications require stronger protection.",
        "priority_order": ["Medical", "Water Systems", "Heating/Cooling", "Communications"],
        "critical_split": {"Medical": 0.42, "Heating/Cooling": 0.22, "Water Systems": 0.18, "Communications": 0.18},
        "failure_tolerance_hours": 4,
    },
    "Data Center": {
        "critical_load_share": 0.52,
        "temp_band_c": "18–27",
        "notes": "Thermal stability and core digital continuity dominate the resilience profile.",
        "priority_order": ["Heating/Cooling", "Communications", "Water Systems", "Medical"],
        "critical_split": {"Medical": 0.05, "Heating/Cooling": 0.46, "Water Systems": 0.14, "Communications": 0.35},
        "failure_tolerance_hours": 3,
    },
    "School / Campus": {
        "critical_load_share": 0.28,
        "temp_band_c": "18–29",
        "notes": "Lower life-support sensitivity, but sheltering, water, and communications still matter.",
        "priority_order": ["Heating/Cooling", "Water Systems", "Communications", "Medical"],
        "critical_split": {"Medical": 0.08, "Heating/Cooling": 0.38, "Water Systems": 0.28, "Communications": 0.26},
        "failure_tolerance_hours": 12,
    },
    "Residential Block": {
        "critical_load_share": 0.22,
        "temp_band_c": "16–30",
        "notes": "Basic habitability, water, and communications matter more than clinical continuity.",
        "priority_order": ["Heating/Cooling", "Water Systems", "Communications", "Medical"],
        "critical_split": {"Medical": 0.07, "Heating/Cooling": 0.44, "Water Systems": 0.29, "Communications": 0.20},
        "failure_tolerance_hours": 16,
    },
}

SCENARIOS = {
    "normal": {"demand": 1.00, "solar": 1.00, "wind": 1.00, "hydro": 1.00, "geo": 1.00, "battery": 1.00},
    "heat_wave": {"demand": 1.22, "solar": 1.08, "wind": 0.90, "hydro": 0.93, "geo": 1.00, "battery": 0.96},
    "storm": {"demand": 1.10, "solar": 0.62, "wind": 1.20, "hydro": 1.05, "geo": 1.00, "battery": 0.90},
    "cold_wave": {"demand": 1.18, "solar": 0.72, "wind": 0.96, "hydro": 0.97, "geo": 1.00, "battery": 0.93},
    "blizzard": {"demand": 1.28, "solar": 0.40, "wind": 0.82, "hydro": 0.90, "geo": 1.00, "battery": 0.85},
    "typhoon": {"demand": 1.15, "solar": 0.35, "wind": 0.68, "hydro": 0.78, "geo": 1.00, "battery": 0.82},
}

I18N = {
    "English": {
        "title": "TAIVAS Energy Control Center",
        "caption": "TAIVAS is a resilience decision-support simulator for energy, thermal, and critical facility scenarios under extreme conditions.",
        "controls": "Controls",
        "country": "Country",
        "city": "City",
        "facility_type": "Facility Type",
        "population": "Population",
        "capacity_inputs": "Capacity Inputs",
        "weather_inputs": "Weather Inputs",
        "weather_scenario": "Weather Scenario",
        "stress_inputs": "Stress Inputs",
        "security_inputs": "Energy Security Inputs",
        "timeline_inputs": "Survival Timeline Inputs",
        "thermal_inputs": "Thermal Concept Inputs",
        "hero_title": "Operational Overview",
        "hero_body": "TAIVAS combines a core resilience simulator, an explainable decision-support layer, and a concept lab for advanced thermal ideas. It is designed to test how energy, thermal management, and critical facility protection behave under extreme climate and disruption scenarios.",
        "core": "Core Simulator",
        "decision": "Decision Support",
        "concept": "Concept Lab",
        "core_desc": "Models demand, renewable supply, battery support, failure ratios, reserve planning, facility logic, and survival timeline.",
        "decision_desc": "Explains risk signals, compares scenarios, structures recommendation chains, and produces export-ready summaries.",
        "concept_desc": "Explores thermal and resilience concepts as linked visuals for simulation insight, not hardware blueprints.",
        "country_logic": "Country Logic",
        "facility_logic": "Facility Logic",
        "input_summary": "Input Summary",
        "system_perf": "System Performance",
        "resilience": "Resilience Indicators",
        "demand": "Demand",
        "renewable": "Renewable Supply",
        "final": "Final Supply",
        "shortfall": "Shortfall",
        "battery": "Battery Levels",
        "rr": "Renewable Ratio",
        "eff": "System Efficiency",
        "grid": "Grid Dependency",
        "status_shortfall": "Shortfall Status",
        "status_eff": "Efficiency Status",
        "status_grid": "Grid Stress Status",
        "status_reserve": "Reserve Status",
        "stable": "Stable",
        "watch": "Watch",
        "critical": "Critical",
        "download_scenario": "Scenario CSV",
        "download_reason": "Reason Chain CSV",
        "download_summary": "Executive Summary TXT",
        "download_audit": "Audit Trail JSON",
        "tabs": ["Energy Mix", "Scenario Comparison", "Stress Test", "AI Recommendation", "Energy Security", "Survival Timeline", "Visual Simulator", "Concept Lab"],
        "page_answers": "This page answers:",
        "mix_note": "This tab separates installed capacity from actual modeled supply. Weather, failure ratios, and scenario assumptions change the real contribution of each energy source.",
        "installed_mix": "Installed Capacity Mix",
        "actual_mix": "Actual Renewable Supply Mix",
        "energy_table": "Energy Source Table",
        "capacity_factors": "Capacity Factors",
        "dominant": "Dominant modeled renewable source",
        "baseline_vs_selected": "Baseline vs Selected Scenario",
        "all_scenarios": "All Weather Scenarios",
        "critical_breakdown": "Critical Load Breakdown",
        "quick_reco": "Quick Recommendation Layer",
        "reason_chain": "Reason Chain",
        "priority_signals": "Priority Signals",
        "timeline_chart": "Timeline Chart",
        "timeline_table": "Hourly Timeline Table",
        "concept_note": "These modules are illustrative simulation layers for resilience exploration. They are not hardware blueprints and do not replace physical engineering validation.",
        "concept_badge": "Conceptual Simulation • Not hardware-validated",
        "thermal_tabs": ["Thermal Principle", "Phase-Change Buffer", "Ground Sink", "Distributed Control", "Harvesting & Buffering"],
        "mode": "Mode",
        "current": "Current",
        "thermal_concept": "Thermal Concept",
        "reserve_days": "Reserve Days",
        "shortfall_hour": "Shortfall Hour",
        "critical_failure_hour": "Critical Failure Hour",
        "thermal_compare": "Current vs Thermal Concept",
        "solar_capacity": "Solar Capacity",
        "wind_capacity": "Wind Capacity",
        "geothermal_capacity": "Geothermal Capacity",
        "hydro_capacity": "Hydro Capacity",
        "battery_capacity": "Battery Capacity",
        "temperature": "Temperature",
        "wind_speed": "Wind Speed",
        "solar_radiation": "Solar Radiation",
        "precipitation": "Precipitation",
        "humidity": "Humidity",
        "solar_failure_ratio": "Solar Failure Ratio",
        "wind_failure_ratio": "Wind Failure Ratio",
        "geothermal_failure_ratio": "Geothermal Failure Ratio",
        "hydro_failure_ratio": "Hydro Failure Ratio",
        "battery_failure_ratio": "Battery Failure Ratio",
        "energy_security_scenario": "Energy Security Scenario",
        "import_dependency": "Import Dependency",
        "strategic_reserve_days": "Strategic Reserve Days",
        "shipping_dependency": "Shipping Dependency",
        "infrastructure_damage_ratio": "Infrastructure Damage Ratio",
        "reserve_recovery_lag_days": "Reserve Recovery Lag (days)",
        "primary_supply_failure_ratio": "Primary Supply Failure Ratio",
        "reserve_energy_per_day": "Reserve Energy per Day",
        "outside_air": "Outside Air",
        "indoor_exhaust_air": "Indoor Exhaust Air",
        "thermal_recovery_efficiency": "Thermal Recovery Efficiency",
        "source": "Source",
        "installed_capacity_mw": "Installed Capacity (MW)",
        "actual_supply_mw": "Actual Supply (MW)",
        "installed_mix_pct": "Installed Mix (%)",
        "actual_mix_pct": "Actual Mix (%)",
        "capacity_factor_pct": "Capacity Factor (%)",
        "subsystem": "Subsystem",
        "failure_ratio": "Failure Ratio",
        "availability_pct": "Availability (%)",
        "scenario": "Scenario",
        "metric": "Metric",
        "baseline": "Baseline",
        "selected": "Selected",
        "delta": "Delta",
        "current_energy_contribution": "Current Energy Contribution",
        "current_energy_contribution_note": "This panel shows the live contribution of each renewable source under the selected scenario, plus a practical reference average, current contribution, estimated use, remaining margin, and reserve outlook.",
        "historical_average_share": "Average Share (%)",
        "current_share": "Current Share (%)",
        "current_output_mw": "Current Output (MW)",
        "estimated_use_mw": "Estimated Use (MW)",
        "remaining_margin_mw": "Remaining Margin (MW)",
        "change_from_normal": "Change from Normal (%)",
        "reserve_outlook": "Reserve Outlook",
        "reserve_outlook_note": "This panel estimates current reserve position, modeled average renewable output, and how long reserve refill may take under the current balance.",
        "historical_average_supply": "Average Renewable Supply",
        "current_renewable_supply": "Current Renewable Supply",
        "estimated_renewable_use": "Estimated Renewable Use",
        "remaining_battery_reserve": "Remaining Battery Reserve",
        "estimated_refill_time": "Estimated Refill Time",
        "no_surplus": "No surplus now",
        "hours_short": "h",
        "source_detail_panel": "Source Detail Panel",
        "uploaded_history_used": "Uploaded historical rows are being used as the average reference when available.",
        "trend_panel": "Trend & Next-Step Estimate",
        "trend_panel_note": "This section uses uploaded historical rows when available to estimate a rolling average, a recent trend, and a simple next-step contribution estimate for each renewable source.",
        "rolling_average_share": "Rolling Avg Share (%)",
        "recent_trend_pct": "Recent Trend (%)",
        "next_step_estimate_pct": "Next-Step Estimate (%)",
        "trend_direction": "Trend Direction",
        "rising": "Rising",
        "falling": "Falling",
        "flat": "Flat",
        "time_window_control": "Time Window Control",
        "forecast_horizon": "Forecast Horizon",
        "confidence_band": "Confidence Band",
        "time_window_rows": "Rolling Window (rows)",
        "forecast_steps": "Forecast Horizon (steps)",
        "confidence_level": "Confidence Band Strength",
        "upper_band_pct": "Upper Band (%)",
        "lower_band_pct": "Lower Band (%)",
        "history_sorting": "History Sorting",
        "history_sorting_note": "Uploaded history rows are sorted by timestamp when a recognizable time column is available; otherwise the original row order is used.",
        "multi_step_forecast": "Multi-Step Forecast Table",
        "multi_step_forecast_note": "This table projects each source across the selected forecast horizon using the recent trend, rolling average, and confidence widening for the current scenario.",
        "forecast_step": "Forecast Step",
        "timestamp_col": "Timestamp Column",
        "history_rows_used": "History Rows Used",
        "scenario_confidence_factor": "Scenario Confidence Factor",
        "sorting_mode": "Sorting Mode",
        "timestamp_sorted": "Timestamp Sorted",
        "original_order": "Original Row Order"
    },
    "繁體中文": {
        "title": "TAIVAS 能源控制中心",
        "caption": "TAIVAS 是一套用於極端情境下能源、熱管理與關鍵設施韌性的決策支援模擬器。",
        "controls": "控制面板",
        "country": "國家",
        "city": "城市",
        "facility_type": "設施類型",
        "population": "人口",
        "capacity_inputs": "容量輸入",
        "weather_inputs": "天氣輸入",
        "weather_scenario": "天氣情境",
        "stress_inputs": "壓力測試輸入",
        "security_inputs": "能源安全輸入",
        "timeline_inputs": "生存時間軸輸入",
        "thermal_inputs": "熱管理概念輸入",
        "hero_title": "系統總覽",
        "hero_body": "TAIVAS 結合核心韌性模擬器、可解釋決策支援層，以及進階熱管理概念模組，用來測試在極端氣候與中斷情境下，能源、熱管理與關鍵設施保護會如何變化。",
        "core": "核心模擬層",
        "decision": "決策支援層",
        "concept": "概念模擬層",
        "core_desc": "模擬需求、再生能源供應、電池支援、失效比例、備援規劃、設施邏輯與生存時間軸。",
        "decision_desc": "解釋風險訊號、比較情境、整理建議鏈，並輸出可摘要的結果。",
        "concept_desc": "以可視化方式探索熱管理與韌性概念，不等同硬體藍圖。",
        "country_logic": "國家邏輯",
        "facility_logic": "設施邏輯",
        "input_summary": "輸入摘要",
        "system_perf": "系統表現",
        "resilience": "韌性指標",
        "demand": "需求",
        "renewable": "再生供應",
        "final": "最終供應",
        "shortfall": "缺口",
        "battery": "電池存量",
        "rr": "再生比例",
        "eff": "系統效率",
        "grid": "外部依賴",
        "status_shortfall": "缺口狀態",
        "status_eff": "效率狀態",
        "status_grid": "電網壓力狀態",
        "status_reserve": "備援狀態",
        "stable": "穩定",
        "watch": "注意",
        "critical": "危急",
        "download_scenario": "下載情境 CSV",
        "download_reason": "下載理由鏈 CSV",
        "download_summary": "下載摘要 TXT",
        "download_audit": "下載稽核 JSON",
        "tabs": ["能源組成", "情境比較", "壓力測試", "AI 建議", "能源安全", "生存時間軸", "視覺模擬", "概念模組"],
        "page_answers": "本頁回答：",
        "mix_note": "本頁將裝機容量與實際模擬供應拆開呈現。天氣、失效比例與情境假設，都會改變各能源的真實貢獻。",
        "installed_mix": "裝機容量組成",
        "actual_mix": "實際再生供應組成",
        "energy_table": "能源來源表",
        "capacity_factors": "容量因子",
        "dominant": "主要再生來源",
        "baseline_vs_selected": "基準與選定情境比較",
        "all_scenarios": "所有天氣情境",
        "critical_breakdown": "關鍵負載拆解",
        "quick_reco": "快速建議層",
        "reason_chain": "理由鏈",
        "priority_signals": "優先訊號",
        "timeline_chart": "時間軸圖表",
        "timeline_table": "逐時時間軸表",
        "concept_note": "這些模組是用來探索韌性的概念模擬層，不是硬體藍圖，也不取代實體工程驗證。",
        "concept_badge": "概念模擬 • 非硬體驗證版",
        "thermal_tabs": ["熱交換原理", "相變緩衝", "地下熱匯", "分散控制", "採收與緩衝"],
        "mode": "模式",
        "current": "目前",
        "thermal_concept": "熱概念",
        "reserve_days": "備援天數",
        "shortfall_hour": "缺口時點",
        "critical_failure_hour": "關鍵失效時點",
        "thermal_compare": "目前模式與熱概念比較",
        "solar_capacity": "太陽能容量",
        "wind_capacity": "風能容量",
        "geothermal_capacity": "地熱容量",
        "hydro_capacity": "水力容量",
        "battery_capacity": "電池容量",
        "temperature": "溫度",
        "wind_speed": "風速",
        "solar_radiation": "太陽輻射",
        "precipitation": "降雨量",
        "humidity": "濕度",
        "solar_failure_ratio": "太陽能失效比例",
        "wind_failure_ratio": "風能失效比例",
        "geothermal_failure_ratio": "地熱失效比例",
        "hydro_failure_ratio": "水力失效比例",
        "battery_failure_ratio": "電池失效比例",
        "energy_security_scenario": "能源安全情境",
        "import_dependency": "進口依賴",
        "strategic_reserve_days": "戰略備援天數",
        "shipping_dependency": "航運依賴",
        "infrastructure_damage_ratio": "基礎設施損害比例",
        "reserve_recovery_lag_days": "備援恢復延遲（天）",
        "primary_supply_failure_ratio": "主要供應失效比例",
        "reserve_energy_per_day": "每日備援能源",
        "outside_air": "外部空氣",
        "indoor_exhaust_air": "室內排氣",
        "thermal_recovery_efficiency": "熱回收效率",
        "source": "來源",
        "installed_capacity_mw": "裝機容量 (MW)",
        "actual_supply_mw": "實際供應 (MW)",
        "installed_mix_pct": "裝機占比 (%)",
        "actual_mix_pct": "實際占比 (%)",
        "capacity_factor_pct": "容量因子 (%)",
        "subsystem": "子系統",
        "failure_ratio": "失效比例",
        "availability_pct": "可用率 (%)",
        "scenario": "情境",
        "metric": "指標",
        "baseline": "基準",
        "selected": "選定值",
        "delta": "差值",
        "current_energy_contribution": "目前能源貢獻",
        "current_energy_contribution_note": "這個區塊會顯示目前情境下各再生能源的即時貢獻，並附上可參考的平均值、目前輸出、估計使用量、剩餘餘裕與備援判讀。",
        "historical_average_share": "平均占比 (%)",
        "current_share": "目前占比 (%)",
        "current_output_mw": "目前輸出 (MW)",
        "estimated_use_mw": "估計使用量 (MW)",
        "remaining_margin_mw": "剩餘餘裕 (MW)",
        "change_from_normal": "相較正常差異 (%)",
        "reserve_outlook": "備援判讀",
        "reserve_outlook_note": "這裡會估算目前備援位置、模型平均再生供應，以及在當前平衡下大約要多久才能回補備援。",
        "historical_average_supply": "平均再生供應",
        "current_renewable_supply": "目前再生供應",
        "estimated_renewable_use": "估計再生使用量",
        "remaining_battery_reserve": "剩餘電池備援",
        "estimated_refill_time": "預估回補時間",
        "no_surplus": "目前沒有多餘供應",
        "hours_short": "小時",
        "source_detail_panel": "能源細節面板",
        "uploaded_history_used": "若有可用的上傳歷史資料列，平均值會優先採用該資料。",
        "trend_panel": "趨勢與下一步估計",
        "trend_panel_note": "這裡會優先利用上傳的歷史資料列，估算 rolling average、近期趨勢，以及各能源的下一步占比推估。",
        "rolling_average_share": "滾動平均占比 (%)",
        "recent_trend_pct": "近期趨勢 (%)",
        "next_step_estimate_pct": "下一步估計 (%)",
        "trend_direction": "趨勢方向",
        "rising": "上升中",
        "falling": "下降中",
        "flat": "持平",
        "time_window_control": "時間視窗控制",
        "forecast_horizon": "預測範圍",
        "confidence_band": "信賴帶",
        "time_window_rows": "滾動視窗（列）",
        "forecast_steps": "預測步數",
        "confidence_level": "信賴帶強度",
        "upper_band_pct": "上緣 (%)",
        "lower_band_pct": "下緣 (%)",
        "history_sorting": "歷史排序",
        "history_sorting_note": "若上傳資料中有可辨識的時間欄位，系統會先依 timestamp 排序；否則沿用原始列順序。",
        "multi_step_forecast": "多步預測表",
        "multi_step_forecast_note": "這張表會依照你選的 forecast horizon，結合近期趨勢、rolling average 與情境擴大的信賴帶，推估各能源接下來的變化。",
        "forecast_step": "預測步數",
        "timestamp_col": "時間欄位",
        "history_rows_used": "使用歷史列數",
        "scenario_confidence_factor": "情境信賴因子",
        "sorting_mode": "排序模式",
        "timestamp_sorted": "依時間排序",
        "original_order": "原始列順序"
    },
}

PAGE_QUESTIONS = {
    "English": {
        "Energy Mix": "What is the system actually running on, and how different is actual supply from installed capacity?",
        "Scenario Comparison": "How much better or worse is the selected scenario versus baseline and other scenarios?",
        "Stress Test": "Which subsystems fail first, and how badly does component degradation reduce resilience?",
        "AI Recommendation": "Why is the model concerned, which signal matters most, and what action should be prioritized first?",
        "Energy Security": "How much do import exposure, logistics, refill uncertainty, repair delay, and single-point risk increase disruption?",
        "Survival Timeline": "If supply is disrupted, how long can the system operate before shortfall and critical failure?",
        "Visual Simulator": "What does this disruption look like, and which part of the energy system is being stressed first?",
        "Concept Lab": "If advanced thermal concepts are introduced, which resilience metrics improve and by how much?",
    },
    "繁體中文": {
        "能源組成": "系統實際靠什麼在運作？實際供應和裝機容量差多少？",
        "情境比較": "選定情境和基準情境相比，到底更好還是更差？",
        "壓力測試": "哪些子系統會先出問題？失效比例會把韌性拉低多少？",
        "AI 建議": "模型在擔心什麼？最重要的訊號是什麼？應該先做哪個動作？",
        "能源安全": "進口暴露、物流、補給不確定性、修復延遲與單點風險會把中斷拉高多少？",
        "生存時間軸": "如果供應中斷，系統在出現缺口與關鍵失效前還能撐多久？",
        "視覺模擬": "這個中斷看起來會怎麼發生？能源系統哪一段會最先被壓迫？",
        "概念模組": "如果引入進階熱管理概念，哪些韌性指標會改善？改善多少？",
    },
}

def tr(key: str) -> str:
    lang_pack = I18N.get(st.session_state.get("ui_lang", "English"), I18N["English"])
    return lang_pack.get(key, I18N["English"].get(key, key))

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
    heating = max(0.0, 10 - temp) * 1.35
    humidity_load = max(0.0, humidity - 65) * 0.25
    rain_impact = precipitation * 0.08
    return 1.0 + (cooling + heating + humidity_load + rain_impact) / 100.0

# CORE FORMULA UPDATE START
# These constants and helper functions support the requested calculation model.
# They are intentionally small and local so the Streamlit UI and data flow stay unchanged.
DEMAND_PER_CAPITA_MW = 0.000035
SOLAR_EFFICIENCY = 0.58
WIND_EFFICIENCY = 0.42
GEOTHERMAL_AVAILABILITY_FACTOR = 0.85
BATTERY_ROUND_TRIP_LOSS_RATE = 0.04

FACILITY_DEMAND_FACTORS = {
    "Long-term Care": 1.12,
    "Hospital": 1.22,
    "Data Center": 1.18,
    "School / Campus": 0.92,
    "Residential Block": 0.88,
}


def scenario_temperature_stress_factor(scenario_key: str, temperature: float) -> float:
    """Demand weather factor: combines selected scenario pressure with hot/cold temperature stress."""
    scenario = SCENARIOS.get(scenario_key, SCENARIOS["normal"])
    heat_stress = max(0.0, temperature - 24.0) * 0.012
    cold_stress = max(0.0, 10.0 - temperature) * 0.010
    return clamp(float(scenario.get("demand", 1.0)) * (1.0 + heat_stress + cold_stress), 0.65, 2.25)


def facility_demand_factor(facility_name: str) -> float:
    """Facility factor: critical facilities receive higher modeled demand pressure."""
    return FACILITY_DEMAND_FACTORS.get(str(facility_name), 1.0)


def calculate_risk_tier(shortfall: float, demand: float) -> str:
    """Risk tier formula based on unmet demand ratio."""
    if shortfall <= 0:
        return "Low"
    shortfall_ratio = safe_div(shortfall, demand)
    if shortfall_ratio < 0.05:
        return "Elevated"
    if shortfall_ratio < 0.15:
        return "High"
    return "Critical"
# CORE FORMULA UPDATE END

def build_status_label(value: float, thresholds, reverse: bool = False) -> str:
    warn, critical = thresholds
    if reverse:
        if value <= critical:
            return tr("critical")
        if value <= warn:
            return tr("watch")
        return tr("stable")
    if value >= critical:
        return tr("critical")
    if value >= warn:
        return tr("watch")
    return tr("stable")

def mini_card(label: str, value: str):
    st.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)

def page_question(tab_label: str):
    lang = st.session_state.get("ui_lang", "English")
    st.markdown(f'<div class="question"><b>{tr("page_answers")}</b> {PAGE_QUESTIONS[lang][tab_label]}</div>', unsafe_allow_html=True)

def concept_badge():
    st.markdown(f'<div class="badge">{tr("concept_badge")}</div>', unsafe_allow_html=True)

def compute_energy_supply(inputs, scenario_key: str, failure_ratios: dict, reserve_recovery_lag_days: int):
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
    facility_name = inputs.get("facility_type", globals().get("facility_type", "Residential Block"))

    # Demand formula:
    # base_demand = population * demand_per_capita_mw
    # weather_factor depends on selected scenario and temperature stress.
    # facility_factor depends on the selected facility type.
    # demand = base_demand * weather_factor * facility_factor
    base_demand = population * DEMAND_PER_CAPITA_MW
    weather_factor = scenario_temperature_stress_factor(scenario_key, temperature)
    facility_factor = facility_demand_factor(facility_name)
    demand = base_demand * weather_factor * facility_factor

    # Renewable resource factors convert weather inputs into normalized source availability.
    solar_resource_factor = clamp(solar_radiation / 1000.0, 0.0, 1.20)
    wind_resource_factor = clamp(wind_speed / 12.0, 0.0, 1.50)
    hydro_availability_factor = clamp(0.45 + precipitation / 500.0 * 0.35, 0.15, 0.95)
    geothermal_availability_factor = GEOTHERMAL_AVAILABILITY_FACTOR
    solar_availability = 1.0 - clamp(failure_ratios["solar"], 0.0, 1.0)
    wind_availability = 1.0 - clamp(failure_ratios["wind"], 0.0, 1.0)
    geo_availability = 1.0 - clamp(failure_ratios["geothermal"], 0.0, 1.0)
    hydro_availability = 1.0 - clamp(failure_ratios["hydro"], 0.0, 1.0)
    battery_availability = 1.0 - clamp(failure_ratios["battery"], 0.0, 1.0)

    # Renewable supply formulas:
    # solar_supply = solar_capacity * solar_resource_factor * solar_efficiency * scenario_solar_factor
    # wind_supply = wind_capacity * wind_resource_factor * wind_efficiency * scenario_wind_factor
    # hydro_supply = hydro_capacity * hydro_availability_factor * scenario_hydro_factor
    # geothermal_supply = geothermal_capacity * geothermal_availability_factor
    # Existing failure ratios are preserved as availability multipliers.
    solar_supply = solar_capacity * solar_resource_factor * SOLAR_EFFICIENCY * scenario["solar"] * solar_availability
    wind_supply = wind_capacity * wind_resource_factor * WIND_EFFICIENCY * scenario["wind"] * wind_availability
    hydro_supply = hydro_capacity * hydro_availability_factor * scenario["hydro"] * hydro_availability
    geo_supply = geothermal_capacity * geothermal_availability_factor * geo_availability
    renewable_supply = solar_supply + wind_supply + hydro_supply + geo_supply

    # Battery formula:
    # battery_next = min(battery_capacity, battery_current + charge - discharge - battery_losses)
    battery_current = clamp(inputs.get("battery_current", battery_capacity), 0, battery_capacity)
    charge = max(0.0, renewable_supply - demand) * 0.30
    battery_dispatch_limit = battery_capacity * 0.35 * scenario["battery"] * battery_availability
    lag_penalty = max(0.70, 1.0 - reserve_recovery_lag_days * 0.015)
    discharge = min(battery_current, battery_dispatch_limit * lag_penalty, max(0.0, demand - renewable_supply))
    battery_losses = (charge + discharge) * BATTERY_ROUND_TRIP_LOSS_RATE
    battery_next = min(battery_capacity, max(0.0, battery_current + charge - discharge - battery_losses))

    # Final supply formula:
    # final_supply = renewable_supply + battery_discharge + grid_support
    grid_support = clamp(inputs.get("grid_support", 0.0), 0.0, demand)
    battery_dispatch = discharge
    final_supply = renewable_supply + battery_dispatch + grid_support

    # Shortfall formula:
    # shortfall = max(demand - final_supply, 0)
    shortfall = max(0.0, demand - final_supply)

    # Risk tier formula:
    # Low when no shortfall, then Elevated/High/Critical by shortfall share of demand.
    risk_tier = calculate_risk_tier(shortfall, demand)
    renewable_ratio = safe_div(renewable_supply, final_supply) * 100 if final_supply > 0 else 0.0
    system_efficiency = clamp(100 - shortfall * 0.55, 0, 100)
    grid_dependency = safe_div(shortfall, demand) * 100 if demand > 0 else 0.0
    battery_levels = battery_next
    actual_mix_raw = {"Solar": solar_supply, "Wind": wind_supply, "Geothermal": geo_supply, "Hydro": hydro_supply}
    installed_mix_raw = {"Solar": solar_capacity, "Wind": wind_capacity, "Geothermal": geothermal_capacity, "Hydro": hydro_capacity}
    actual_mix_pct = {k: v * 100 for k, v in normalize_mix(actual_mix_raw).items()}
    installed_mix_pct = {k: v * 100 for k, v in normalize_mix(installed_mix_raw).items()}
    capacity_factors = {
        "Solar": round(clamp(solar_resource_factor * SOLAR_EFFICIENCY, 0.0, 1.0) * 100, 1),
        "Wind": round(clamp(wind_resource_factor * WIND_EFFICIENCY, 0.0, 1.0) * 100, 1),
        "Geothermal": round(geothermal_availability_factor * 100, 1),
        "Hydro": round(hydro_availability_factor * 100, 1),
    }
    dominant_source = max(actual_mix_raw, key=actual_mix_raw.get) if renewable_supply > 0 else "None"
    return {
        "demand": round(demand, 2),
        "renewable_supply": round(renewable_supply, 2),
        "final_supply": round(final_supply, 2),
        "battery_levels": round(battery_levels, 2),
        "shortfall": round(shortfall, 2),
        "renewable_ratio": round(renewable_ratio, 2),
        "system_efficiency": round(system_efficiency, 2),
        "grid_dependency": round(grid_dependency, 2),
        "risk_tier": risk_tier,
        "grid_support": round(grid_support, 2),
        "battery_discharge": round(battery_dispatch, 2),
        "actual_mix_pct": actual_mix_pct,
        "installed_mix_pct": installed_mix_pct,
        "actual_mix_mw": {k: round(v, 2) for k, v in actual_mix_raw.items()},
        "installed_mix_mw": {k: round(v, 2) for k, v in installed_mix_raw.items()},
        "capacity_factors": capacity_factors,
        "dominant_source": dominant_source,
    }

def apply_extended_security(results, fuel_price_shock, repair_crew_availability, spare_parts_delay_days, refill_uncertainty, single_point_failure_risk):
    penalty = fuel_price_shock * 0.10 + (1 - repair_crew_availability) * 0.16 + min(spare_parts_delay_days / 30.0, 1.0) * 0.12 + refill_uncertainty * 0.18 + single_point_failure_risk * 0.22
    results["extended_disruption_score"] = round(clamp(results["grid_dependency"] * 0.45 + penalty * 100, 0, 100), 2)
    results["spare_parts_risk"] = round(clamp(spare_parts_delay_days * 3.2, 0, 100), 2)
    results["maintenance_readiness"] = round(clamp(repair_crew_availability * 100 - spare_parts_delay_days * 1.8, 0, 100), 2)
    results["refill_stability"] = round(clamp((1 - refill_uncertainty) * 100, 0, 100), 2)
    results["single_point_pressure"] = round(single_point_failure_risk * 100, 2)
    results["reserve_days_remaining"] = max(0, round(results.get("reserve_days_remaining", 0) - penalty * 4.2, 1))
    results["recovery_time_estimate"] = max(1, round(results.get("recovery_time_estimate", 1) + penalty * 5 + spare_parts_delay_days * 0.3, 1))
    return results

def recommendation_reason_chain(results, energy_security_scenario, timeline_results, facility_type, facility_profile):
    if st.session_state.get("ui_lang", "English") == "繁體中文":
        rows = [{"Signal": f"缺口仍有 {results['shortfall']:.2f} MW" if results["shortfall"] > 0 else "目前情境下沒有模擬缺口",
                 "Impact": "需求高於目前可用供應。" if results["shortfall"] > 0 else "即時供需平衡暫時穩定。",
                 "Recommendation": "提高穩定供應、降低非關鍵負載，或加深儲能支援。" if results["shortfall"] > 0 else "保留備援餘裕並持續監看中斷訊號。",
                 "Expected effect": "降低未滿足負載並延長穩定運作時間。" if results["shortfall"] > 0 else "保住惡化時的緩衝空間。"}]
    else:
        rows = [{"Signal": f"Shortfall remains at {results['shortfall']:.2f} MW" if results["shortfall"] > 0 else "No modeled shortfall in the selected scenario",
                 "Impact": "Demand is above available modeled supply." if results["shortfall"] > 0 else "Immediate supply-demand balance is currently stable.",
                 "Recommendation": "Raise firm capacity, reduce non-critical load, or deepen storage support." if results["shortfall"] > 0 else "Protect reserve margin and watch disruption signals.",
                 "Expected effect": "Reduce unmet load and extend stable operation." if results["shortfall"] > 0 else "Preserve endurance against degradation."}]
    return rows

def scenario_delta_df(baseline, selected):
    return pd.DataFrame([
        {tr("metric"): tr("demand"), tr("baseline"): round(baseline["demand"], 2), tr("selected"): round(selected["demand"], 2), tr("delta"): round(selected["demand"] - baseline["demand"], 2)},
        {tr("metric"): tr("renewable"), tr("baseline"): round(baseline["renewable_supply"], 2), tr("selected"): round(selected["renewable_supply"], 2), tr("delta"): round(selected["renewable_supply"] - baseline["renewable_supply"], 2)},
        {tr("metric"): tr("final"), tr("baseline"): round(baseline["final_supply"], 2), tr("selected"): round(selected["final_supply"], 2), tr("delta"): round(selected["final_supply"] - baseline["final_supply"], 2)},
        {tr("metric"): tr("shortfall"), tr("baseline"): round(baseline["shortfall"], 2), tr("selected"): round(selected["shortfall"], 2), tr("delta"): round(selected["shortfall"] - baseline["shortfall"], 2)},
    ])

def comparison_dataframe(inputs, failure_ratios, reserve_recovery_lag_days):
    rows = []
    for key in SCENARIOS.keys():
        r = compute_energy_supply(inputs, key, failure_ratios, reserve_recovery_lag_days)
        rows.append({tr("scenario"): key.replace("_", " ").title(), tr("demand"): r["demand"], tr("renewable"): r["renewable_supply"], tr("final"): r["final_supply"], tr("shortfall"): r["shortfall"], tr("grid"): r["grid_dependency"]})
    return pd.DataFrame(rows)

def critical_load_breakdown(total_demand, critical_share, split):
    critical_total = total_demand * critical_share
    return pd.DataFrame({"Category": list(split.keys()), f"{tr('demand')} (MW)": [round(critical_total * w, 2) for w in split.values()]})

# UI IMPROVEMENT START
# Chart readability polish only: larger canvas, fixed colors, clearer labels.
def render_capacity_factor_chart(capacity_factors):
    labels = list(capacity_factors.keys())
    values = [capacity_factors[k] for k in labels]
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    ax.barh(labels, values, color=["#38BDF8", "#22C55E", "#F59E0B", "#A78BFA"])
    ax.set_xlabel("Capacity Factor (%)" if st.session_state.get("ui_lang", "English") == "English" else "容量因子 (%)")
    ax.set_xlim(0, 100)
    ax.set_title(tr("capacity_factors"))
    ax.grid(axis="x", alpha=0.25)
    ax.tick_params(axis="both", labelsize=11)
    ax.title.set_size(14)
    ax.xaxis.label.set_size(12)
    for i, value in enumerate(values):
        ax.text(min(value + 2, 98), i, f"{value:.1f}%", va="center", fontsize=11, color="#E5E7EB")
    plt.tight_layout(pad=1.4)
    st.pyplot(fig, clear_figure=True)

def render_delta_chart(delta_df):
    fig, ax = plt.subplots(figsize=(9.4, 4.5))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    metric_col = tr("metric") if tr("metric") in delta_df.columns else "Metric"
    delta_col = tr("delta") if tr("delta") in delta_df.columns else "Delta"
    colors = ["#22C55E" if v >= 0 else "#F97316" for v in delta_df[delta_col]]
    ax.barh(delta_df[metric_col], delta_df[delta_col], color=colors)
    ax.axvline(0, linewidth=1.0)
    ax.set_title(tr("baseline_vs_selected"))
    ax.grid(axis="x", alpha=0.25)
    ax.tick_params(axis="both", labelsize=11)
    ax.title.set_size(14)
    for i, value in enumerate(delta_df[delta_col]):
        offset = 0.8 if value >= 0 else -0.8
        ha = "left" if value >= 0 else "right"
        ax.text(value + offset, i, f"{value:+.2f}", va="center", ha=ha, fontsize=11, color="#E5E7EB")
    plt.tight_layout(pad=1.4)
    st.pyplot(fig, clear_figure=True)

def render_critical_load_chart(df):
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    col = f"{tr('demand')} (MW)"
    ax.bar(df["Category"], df[col], color=["#60A5FA", "#FBBF24", "#34D399", "#C084FC"])
    ax.set_ylabel(col)
    ax.set_title(tr("critical_breakdown"))
    ax.grid(axis="y", alpha=0.22)
    ax.tick_params(axis="both", labelsize=11)
    ax.title.set_size(14)
    ax.yaxis.label.set_size(12)
    plt.xticks(rotation=18, ha="right")
    plt.tight_layout(pad=1.5)
    st.pyplot(fig, clear_figure=True)
# UI IMPROVEMENT END


def compute_reference_average(inputs, uploaded_df, selected_country, selected_city):
    # Use uploaded historical rows first when available; otherwise fall back to model average across scenarios.
    source_order = ["Solar", "Wind", "Geothermal", "Hydro"]
    rows = []
    if uploaded_df is not None and not uploaded_df.empty:
        tmp = uploaded_df.copy()
        if "country_key" in tmp.columns and "city_key" in tmp.columns:
            tmp["_country"] = tmp["country_key"].astype(str).str.strip().str.title()
            tmp["_city"] = tmp["city_key"].astype(str).str.strip().str.title()
            matched = tmp[(tmp["_country"] == str(selected_country).title()) & (tmp["_city"] == str(selected_city).title())]
            if matched.empty:
                matched = tmp
        else:
            matched = tmp
        for _, r in matched.iterrows():
            local_inputs = dict(inputs)
            local_inputs["temperature"] = safe_float(r["temperature"], inputs["temperature"]) if "temperature" in matched.columns else inputs["temperature"]
            local_inputs["wind_speed"] = safe_float(r["wind_speed"], inputs["wind_speed"]) if "wind_speed" in matched.columns else inputs["wind_speed"]
            local_inputs["solar_radiation"] = safe_float(r["solar_radiation"], inputs["solar_radiation"]) if "solar_radiation" in matched.columns else inputs["solar_radiation"]
            local_inputs["precipitation"] = safe_float(r["precipitation"], inputs["precipitation"]) if "precipitation" in matched.columns else inputs["precipitation"]
            local_inputs["humidity"] = safe_float(r["humidity"], inputs["humidity"]) if "humidity" in matched.columns else inputs["humidity"]
            local_inputs["population"] = safe_int(r["population"], inputs["population"]) if "population" in matched.columns else inputs["population"]
            local_inputs["solar_capacity"] = safe_float(r["solar_capacity"], inputs["solar_capacity"]) if "solar_capacity" in matched.columns else inputs["solar_capacity"]
            local_inputs["wind_capacity"] = safe_float(r["wind_capacity"], inputs["wind_capacity"]) if "wind_capacity" in matched.columns else inputs["wind_capacity"]
            local_inputs["geothermal_capacity"] = safe_float(r["geothermal_capacity"], inputs["geothermal_capacity"]) if "geothermal_capacity" in matched.columns else inputs["geothermal_capacity"]
            local_inputs["hydro_capacity"] = safe_float(r["hydro_capacity"], inputs["hydro_capacity"]) if "hydro_capacity" in matched.columns else inputs["hydro_capacity"]
            local_inputs["battery_capacity"] = safe_float(r["battery_capacity"], inputs["battery_capacity"]) if "battery_capacity" in matched.columns else inputs["battery_capacity"]
            rr = compute_energy_supply(local_inputs, "normal", {k: 0.0 for k in ["solar", "wind", "geothermal", "hydro", "battery"]}, 0)
            rows.append(rr)
    if not rows:
        for sk in SCENARIOS.keys():
            rr = compute_energy_supply(inputs, sk, {k: 0.0 for k in ["solar", "wind", "geothermal", "hydro", "battery"]}, 0)
            rows.append(rr)
    avg_mix_pct = {s: round(sum(r["actual_mix_pct"].get(s, 0.0) for r in rows) / len(rows), 2) for s in source_order}
    avg_mix_mw = {s: round(sum(r["actual_mix_mw"].get(s, 0.0) for r in rows) / len(rows), 2) for s in source_order}
    avg_supply = round(sum(r["renewable_supply"] for r in rows) / len(rows), 2)
    return {"avg_mix_pct": avg_mix_pct, "avg_mix_mw": avg_mix_mw, "avg_supply": avg_supply, "used_uploaded_history": uploaded_df is not None and not uploaded_df.empty and len(rows) > 0}

def build_energy_contribution_df(results, baseline_results, reference_avg):
    rows = []
    source_order = ["Solar", "Wind", "Geothermal", "Hydro"]
    demand = max(float(results["demand"]), 0.0)
    renewable_supply = max(float(results["renewable_supply"]), 0.0)
    for source in source_order:
        current_share = float(results["actual_mix_pct"].get(source, 0.0))
        avg_share = float(reference_avg["avg_mix_pct"].get(source, 0.0))
        current_mw = float(results["actual_mix_mw"].get(source, 0.0))
        installed_mw = float(results["installed_mix_mw"].get(source, 0.0))
        normal_share = float(baseline_results["actual_mix_pct"].get(source, 0.0))
        estimated_use = min(current_mw, demand * (current_share / 100.0))
        remaining_margin = max(installed_mw - current_mw, 0.0)
        change_from_normal = current_share - normal_share
        rows.append({
            tr("source"): source,
            tr("current_share"): round(current_share, 2),
            tr("historical_average_share"): round(avg_share, 2),
            tr("current_output_mw"): round(current_mw, 2),
            tr("estimated_use_mw"): round(estimated_use, 2),
            tr("remaining_margin_mw"): round(remaining_margin, 2),
            tr("change_from_normal"): round(change_from_normal, 2),
            "_sort_share": current_share,
        })
    df = pd.DataFrame(rows).sort_values("_sort_share", ascending=False).reset_index(drop=True)
    return df.drop(columns=["_sort_share"])

def estimate_refill_hours(results, timeline_results):
    battery_capacity_initial = max(float(inputs["battery_capacity"]) * (1 - battery_failure_ratio), 0.0)
    battery_remaining = max(float(results["battery_levels"]), 0.0)
    to_refill = max(battery_capacity_initial - battery_remaining, 0.0)
    surplus_rate = max(float(results["final_supply"]) - float(results["demand"]), 0.0)
    if surplus_rate <= 0.01:
        return tr("no_surplus")
    return f"{round(to_refill / surplus_rate, 1)} {tr('hours_short')}"

def render_energy_contribution_panel(df):
    st.subheader(tr("current_energy_contribution"))
    st.markdown(f'<div class="note">{tr("current_energy_contribution_note")}</div>', unsafe_allow_html=True)
    for _, row in df.iterrows():
        source = row[tr("source")]
        share = row[tr("current_share")]
        avg_share = row[tr("historical_average_share")]
        current_mw = row[tr("current_output_mw")]
        used_mw = row[tr("estimated_use_mw")]
        remaining = row[tr("remaining_margin_mw")]
        delta = row[tr("change_from_normal")]
        delta_text = f"{delta:+.1f}%"
        width = max(6, min(100, int(round(share))))
        st.markdown(
            f"""
            <div style="border:1px solid rgba(148,163,184,0.22); border-radius:12px; padding:14px 15px; margin-bottom:12px; background:rgba(15,23,42,0.46);">
              <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:8px;">
                <div style="font-size:1.08rem; font-weight:800;">{source}</div>
                <div style="font-size:0.96rem; opacity:0.9;">{delta_text}</div>
              </div>
              <div style="width:100%; height:12px; background:rgba(255,255,255,0.10); border-radius:999px; overflow:hidden; margin-bottom:10px;">
                <div style="width:{width}%; height:100%; background:linear-gradient(90deg, rgba(96,165,250,0.95), rgba(34,211,238,0.95)); border-radius:999px;"></div>
              </div>
              <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap:10px; font-size:0.94rem; line-height:1.48;">
                <div><b>{tr("current_share")}</b><br>{share:.2f}%</div>
                <div><b>{tr("historical_average_share")}</b><br>{avg_share:.2f}%</div>
                <div><b>{tr("current_output_mw")}</b><br>{current_mw:.2f} MW</div>
                <div><b>{tr("estimated_use_mw")}</b><br>{used_mw:.2f} MW</div>
                <div><b>{tr("remaining_margin_mw")}</b><br>{remaining:.2f} MW</div>
                <div><b>{tr("change_from_normal")}</b><br>{delta_text}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_reserve_outlook_panel(reference_avg, results, timeline_results):
    st.subheader(tr("reserve_outlook"))
    st.markdown(f'<div class="note">{tr("reserve_outlook_note")}</div>', unsafe_allow_html=True)
    if reference_avg.get("used_uploaded_history"):
        st.caption(tr("uploaded_history_used"))
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(tr("historical_average_supply"), f'{reference_avg["avg_supply"]} MW')
    c2.metric(tr("current_renewable_supply"), f'{results["renewable_supply"]} MW')
    c3.metric(tr("estimated_renewable_use"), f'{round(min(results["renewable_supply"], results["demand"]), 2)} MW')
    c4.metric(tr("remaining_battery_reserve"), f'{results["battery_levels"]} MWh')
    c5.metric(tr("estimated_refill_time"), estimate_refill_hours(results, timeline_results))

def compute_trend_estimates(inputs, uploaded_df, selected_country, selected_city, baseline_results, scenario_key="normal", rolling_window_rows=3, forecast_steps=2, confidence_level=1.0):
    source_order = ["Solar", "Wind", "Geothermal", "Hydro"]
    scenario_factor_map = {
        "normal": 1.00,
        "heat_wave": 1.10,
        "storm": 1.22,
        "cold_wave": 1.15,
        "blizzard": 1.35,
        "typhoon": 1.42,
    }
    scenario_conf_factor = float(scenario_factor_map.get(str(scenario_key), 1.10))
    records = []
    history_count = 0
    timestamp_col = None
    sorting_mode = "original"
    if uploaded_df is not None and not uploaded_df.empty:
        sorted_df, timestamp_col, sorting_mode = sort_history_df(uploaded_df)
        tmp = sorted_df.copy()
        if "country_key" in tmp.columns and "city_key" in tmp.columns:
            tmp["_country"] = tmp["country_key"].astype(str).str.strip().str.title()
            tmp["_city"] = tmp["city_key"].astype(str).str.strip().str.title()
            matched = tmp[(tmp["_country"] == str(selected_country).title()) & (tmp["_city"] == str(selected_city).title())]
            if matched.empty:
                matched = tmp
        else:
            matched = tmp
        history_count = len(matched)
        for _, r in matched.iterrows():
            local_inputs = dict(inputs)
            for key, default in [
                ("temperature", inputs["temperature"]),
                ("wind_speed", inputs["wind_speed"]),
                ("solar_radiation", inputs["solar_radiation"]),
                ("precipitation", inputs["precipitation"]),
                ("humidity", inputs["humidity"]),
                ("population", inputs["population"]),
                ("solar_capacity", inputs["solar_capacity"]),
                ("wind_capacity", inputs["wind_capacity"]),
                ("geothermal_capacity", inputs["geothermal_capacity"]),
                ("hydro_capacity", inputs["hydro_capacity"]),
                ("battery_capacity", inputs["battery_capacity"]),
            ]:
                if key in matched.columns:
                    local_inputs[key] = safe_float(r[key], default) if key != "population" else safe_int(r[key], default)
            rr = compute_energy_supply(local_inputs, "normal", {k: 0.0 for k in ["solar", "wind", "geothermal", "hydro", "battery"]}, 0)
            records.append(rr)
    if not records:
        fallback_keys = list(SCENARIOS.keys())
        records = [compute_energy_supply(inputs, sk, {k: 0.0 for k in ["solar", "wind", "geothermal", "hydro", "battery"]}, 0) for sk in fallback_keys]
        history_count = len(records)

    window = max(2, min(int(rolling_window_rows), max(2, len(records))))
    recent_records = records[-window:]
    prev_records = records[-(window * 2):-window] if len(records) >= window * 2 else records[:-window]

    rolling_avg = {s: round(sum(r["actual_mix_pct"].get(s, 0.0) for r in recent_records) / max(len(recent_records), 1), 2) for s in source_order}
    if prev_records:
        prev_avg = {s: round(sum(r["actual_mix_pct"].get(s, 0.0) for r in prev_records) / max(len(prev_records), 1), 2) for s in source_order}
    else:
        prev_avg = {s: float(baseline_results["actual_mix_pct"].get(s, 0.0)) for s in source_order}

    recent_trend = {s: round(rolling_avg[s] - float(prev_avg.get(s, 0.0)), 2) for s in source_order}

    if len(recent_records) > 1:
        volatility = {
            s: max(r["actual_mix_pct"].get(s, 0.0) for r in recent_records) - min(r["actual_mix_pct"].get(s, 0.0) for r in recent_records)
            for s in source_order
        }
    else:
        volatility = {s: abs(recent_trend[s]) for s in source_order}

    next_step = {}
    source_factor_map = {
        "Solar": {"normal": 1.00, "heat_wave": 1.12, "storm": 0.90, "cold_wave": 0.92, "blizzard": 0.78, "typhoon": 0.72},
        "Wind": {"normal": 1.00, "heat_wave": 0.92, "storm": 1.20, "cold_wave": 0.98, "blizzard": 0.90, "typhoon": 0.82},
        "Geothermal": {"normal": 1.00, "heat_wave": 1.01, "storm": 1.00, "cold_wave": 1.00, "blizzard": 1.00, "typhoon": 1.00},
        "Hydro": {"normal": 1.00, "heat_wave": 0.95, "storm": 1.08, "cold_wave": 0.98, "blizzard": 0.94, "typhoon": 0.86},
    }
    next_step = {}
    for s in source_order:
        source_factor = float(source_factor_map.get(s, {}).get(str(scenario_key), 1.0))
        projected = max(0.0, rolling_avg[s] + recent_trend[s] * max(1, int(forecast_steps)) * 0.5 * source_factor)
        next_step[s] = round(projected, 2)
    total_next = sum(next_step.values())
    if total_next > 0:
        next_step = {s: round(v / total_next * 100.0, 2) for s, v in next_step.items()}

    trend_rows = []
    multistep_rows = []
    for s in source_order:
        delta = recent_trend[s]
        if delta > 0.25:
            direction = tr("rising")
        elif delta < -0.25:
            direction = tr("falling")
        else:
            direction = tr("flat")

        base_band = volatility[s] * float(confidence_level) * 0.5 * scenario_conf_factor
        upper = min(100.0, next_step[s] + base_band)
        lower = max(0.0, next_step[s] - base_band)

        trend_rows.append({
            tr("source"): s,
            tr("rolling_average_share"): rolling_avg[s],
            tr("recent_trend_pct"): round(delta, 2),
            tr("next_step_estimate_pct"): round(next_step[s], 2),
            tr("trend_direction"): direction,
            tr("upper_band_pct"): round(upper, 2),
            tr("lower_band_pct"): round(lower, 2),
            tr("source_forecast_factor"): round(float(source_factor_map.get(s, {}).get(str(scenario_key), 1.0)), 2),
            "_sort": next_step[s],
        })

        for step in range(1, int(forecast_steps) + 1):
            source_factor = float(source_factor_map.get(s, {}).get(str(scenario_key), 1.0))
            projected = max(0.0, rolling_avg[s] + delta * step * 0.5 * source_factor)
            step_band = base_band * (1 + 0.18 * (step - 1))
            multistep_rows.append({
                tr("source"): s,
                tr("forecast_step"): step,
                tr("next_step_estimate_pct"): round(projected, 2),
                tr("lower_band_pct"): round(max(0.0, projected - step_band), 2),
                tr("upper_band_pct"): round(min(100.0, projected + step_band), 2),
                tr("trend_direction"): direction,
                tr("source_forecast_factor"): round(float(source_factor_map.get(s, {}).get(str(scenario_key), 1.0)), 2),
            })

    trend_df = pd.DataFrame(trend_rows).sort_values("_sort", ascending=False).drop(columns=["_sort"]).reset_index(drop=True)
    multistep_df = pd.DataFrame(multistep_rows)
    if not multistep_df.empty:
        multistep_df = multistep_df.sort_values([tr("forecast_step"), tr("next_step_estimate_pct")], ascending=[True, False]).reset_index(drop=True)

    meta = {
        "timestamp_col": timestamp_col if timestamp_col is not None else "-",
        "sorting_mode": tr("timestamp_sorted") if sorting_mode == "timestamp" else tr("original_order"),
        "history_rows_used": history_count,
        "scenario_confidence_factor": round(scenario_conf_factor, 2),
    }
    return trend_df, multistep_df, meta

def render_trend_estimate_panel(trend_df, multistep_df, trend_meta):
    st.subheader(tr("trend_panel"))
    st.markdown(f'<div class="note">{tr("trend_panel_note")}</div>', unsafe_allow_html=True)
    meta_cols = st.columns(4)
    meta_cols[0].metric(tr("timestamp_col"), str(trend_meta.get("timestamp_col", "-")))
    meta_cols[1].metric(tr("sorting_mode"), str(trend_meta.get("sorting_mode", "-")))
    meta_cols[2].metric(tr("history_rows_used"), str(trend_meta.get("history_rows_used", 0)))
    meta_cols[3].metric(tr("scenario_confidence_factor"), str(trend_meta.get("scenario_confidence_factor", 1.0)))

    for _, row in trend_df.iterrows():
        source = row[tr("source")]
        rolling_avg = row[tr("rolling_average_share")]
        trend = row[tr("recent_trend_pct")]
        next_step = row[tr("next_step_estimate_pct")]
        direction = row[tr("trend_direction")]
        upper = row[tr("upper_band_pct")]
        lower = row[tr("lower_band_pct")]
        width = max(6, min(100, int(round(next_step))))
        lower_w = max(2, min(100, int(round(lower))))
        upper_w = max(lower_w, min(100, int(round(upper))))
        trend_text = f"{trend:+.2f}%"
        st.markdown(
            f"""
            <div style="border:1px solid rgba(148,163,184,0.22); border-radius:12px; padding:14px 15px; margin-bottom:12px; background:rgba(15,23,42,0.46);">
              <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:8px;">
                <div style="font-size:1.08rem; font-weight:800;">{source}</div>
                <div style="font-size:0.96rem; opacity:0.9;">{direction}</div>
              </div>
              <div style="position:relative; width:100%; height:14px; background:rgba(255,255,255,0.10); border-radius:999px; overflow:hidden; margin-bottom:10px;">
                <div style="position:absolute; left:0; top:0; width:{upper_w}%; height:100%; background:rgba(251,191,36,0.20); border-radius:999px;"></div>
                <div style="position:absolute; left:0; top:0; width:{lower_w}%; height:100%; background:rgba(251,191,36,0.32); border-radius:999px;"></div>
                <div style="position:absolute; left:0; top:0; width:{width}%; height:100%; background:linear-gradient(90deg, rgba(251,191,36,0.95), rgba(245,158,11,0.95)); border-radius:999px;"></div>
              </div>
              <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:10px; font-size:0.94rem; line-height:1.48;">
                <div><b>{tr("rolling_average_share")}</b><br>{rolling_avg:.2f}%</div>
                <div><b>{tr("recent_trend_pct")}</b><br>{trend_text}</div>
                <div><b>{tr("next_step_estimate_pct")}</b><br>{next_step:.2f}%</div>
                <div><b>{tr("lower_band_pct")}</b><br>{lower:.2f}%</div>
                <div><b>{tr("upper_band_pct")}</b><br>{upper:.2f}%</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    render_forecast_chart(multistep_df)
    st.subheader(tr("source_logic"))
    st.markdown(f'<div class="note">{tr("source_logic_note")}</div>', unsafe_allow_html=True)
    if not trend_df.empty and tr("source_forecast_factor") in trend_df.columns:
        st.dataframe(trend_df[[tr("source"), tr("source_forecast_factor"), tr("trend_direction"), tr("next_step_estimate_pct"), tr("lower_band_pct"), tr("upper_band_pct")]], use_container_width=True, hide_index=True)
    st.subheader(tr("multi_step_forecast"))
    st.markdown(f'<div class="note">{tr("multi_step_forecast_note")}</div>', unsafe_allow_html=True)
    st.dataframe(multistep_df, use_container_width=True, hide_index=True)


# UI IMPROVEMENT START
# Global visual hierarchy, responsive layout, sidebar spacing, metric cards, tabs, and buttons.
st.markdown("""
<style>
/* UI polish block: spacing, typography, mobile layout, metrics, buttons, and scenario hierarchy. */
:root {
    --taivas-panel: rgba(15, 23, 42, 0.72);
    --taivas-panel-soft: rgba(30, 41, 59, 0.46);
    --taivas-border: rgba(148, 163, 184, 0.22);
    --taivas-text: #E5E7EB;
    --taivas-muted: #A7B3C7;
    --taivas-blue: #38BDF8;
    --taivas-green: #22C55E;
    --taivas-amber: #F59E0B;
    --taivas-violet: #A78BFA;
}
html, body, [class*="css"] {font-size: 16px;}
.block-container {padding-top: 0.85rem; padding-bottom: 2.2rem; max-width: 1440px;}
h1 {font-size: clamp(1.9rem, 2.4vw, 2.75rem) !important; line-height: 1.1 !important; margin-bottom: 0.25rem !important;}
h2, h3 {letter-spacing: 0;}
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stCaptionContainer"],
label, .stSelectbox label, .stSlider label, .stNumberInput label, .stFileUploader label {
    font-size: 0.98rem !important;
}
section[data-testid="stSidebar"] {
    min-width: 325px;
}
section[data-testid="stSidebar"] > div {
    padding-top: 1.15rem;
    padding-left: 1rem;
    padding-right: 1rem;
}
section[data-testid="stSidebar"] [data-testid="stExpander"] {
    border: 1px solid var(--taivas-border);
    border-radius: 12px;
    background: rgba(15,23,42,0.40);
    margin-bottom: 0.65rem;
}
section[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    font-size: 0.98rem;
    font-weight: 800;
}
section[data-testid="stSidebar"] .stSlider,
section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stNumberInput,
section[data-testid="stSidebar"] .stFileUploader {
    margin-bottom: 0.7rem;
}
.hero {
    padding: 0.95rem 1.1rem;
    border: 1px solid var(--taivas-border);
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(14,116,144,0.38), rgba(15,23,42,0.52));
    margin-bottom: 0.85rem;
}
.hero h3 { margin: 0 0 0.35rem 0; font-size: 1.26rem; }
.hero p { margin: 0; opacity: 0.94; line-height: 1.5; font-size: 0.98rem; }
.note {
    padding: 0.78rem 0.95rem;
    border-radius: 12px;
    background: rgba(59,130,246,0.10);
    border: 1px solid rgba(96,165,250,0.24);
    margin-bottom: 0.7rem;
    line-height: 1.48;
    font-size: 0.98rem;
}
.quick-start {
    padding: 0.72rem 0.9rem;
    border-radius: 10px;
    background: rgba(59,130,246,0.09);
    border: 1px solid rgba(96,165,250,0.22);
    margin: 0.65rem 0 0.9rem 0;
    line-height: 1.42;
    font-size: 0.96rem;
}
.quick-start b {display:block; margin-bottom:0.18rem;}
.section-break {
    height: 1px;
    background: rgba(148,163,184,0.18);
    margin: 1.1rem 0 0.75rem 0;
}
.question {
    padding: 0.9rem 1.05rem;
    border-radius: 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 0.85rem;
    line-height: 1.6;
    font-size: 0.98rem;
}
.product-strip {display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:0.85rem; margin:0.9rem 0 1.15rem 0;}
.product-card {padding:1rem 1.05rem; border-radius:12px; border:1px solid var(--taivas-border); background:linear-gradient(145deg, rgba(15,23,42,0.82), rgba(30,41,59,0.46)); min-height:118px;}
.product-label {font-size:0.86rem; color:var(--taivas-muted); margin-bottom:0.4rem;}
.product-value {font-size:1.38rem; font-weight:800; line-height:1.15; overflow-wrap:anywhere;}
.product-sub {font-size:0.86rem; color:var(--taivas-muted); margin-top:0.3rem; line-height:1.35;}
.notice-box {padding:0.95rem 1.05rem; border-radius:12px; background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.28); line-height:1.6; margin:0.9rem 0; font-size:0.98rem;}
.demo-pill {display:inline-block; padding:0.3rem 0.65rem; border-radius:999px; margin-left:0.35rem; background:rgba(34,197,94,0.12); border:1px solid rgba(34,197,94,0.32); font-size:0.86rem; font-weight:700;}
.card {
    padding: 0.78rem 0.9rem;
    border-radius: 12px;
    background: var(--taivas-panel-soft);
    border: 1px solid var(--taivas-border);
    margin-bottom: 0.6rem;
    min-height: 76px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.card-label { font-size: 0.88rem; color: var(--taivas-muted); margin-bottom: 0.32rem; }
.card-value { font-size: 1.08rem; font-weight: 750; line-height: 1.34; overflow-wrap:anywhere; }
.layer-box {
    padding: 1rem 1.05rem;
    border-radius: 12px;
    background: linear-gradient(180deg, rgba(15,23,42,0.72), rgba(30,41,59,0.42));
    border: 1px solid var(--taivas-border);
    min-height: 126px;
    border-left: 4px solid var(--taivas-blue);
}
.badge {
    display: inline-block;
    padding: 0.28rem 0.55rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    background: rgba(245,158,11,0.12);
    border: 1px solid rgba(245,158,11,0.35);
    color: #fde68a;
    margin-bottom: 0.55rem;
}
div[data-testid="stMetric"] {
    min-height: 78px;
    padding: 0.78rem 0.9rem;
    border: 1px solid var(--taivas-border);
    border-radius: 12px;
    background: rgba(15,23,42,0.48);
}
div[data-testid="stMetricLabel"] p {font-size:0.9rem !important; color:var(--taivas-muted) !important; line-height:1.3 !important;}
div[data-testid="stMetricValue"] {font-size:1.22rem !important; line-height:1.15 !important;}
div[data-testid="stMetricDelta"] {font-size:0.86rem !important;}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div:first-child {
    background: rgba(56,189,248,0.26) !important;
}
section[data-testid="stSidebar"] .stSlider [role="slider"] {
    background-color: var(--taivas-blue) !important;
    border-color: var(--taivas-blue) !important;
    box-shadow: 0 0 0 2px rgba(56,189,248,0.18) !important;
}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[style*="background-color"] {
    background-color: var(--taivas-blue) !important;
}
.stButton > button,
.stDownloadButton > button,
button[kind="primary"],
button[kind="secondary"] {
    border-radius: 10px !important;
    border: 1px solid rgba(56,189,248,0.38) !important;
    background: rgba(14,116,144,0.24) !important;
    color: var(--taivas-text) !important;
    font-weight: 800 !important;
    min-height: 2.7rem;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: rgba(56,189,248,0.72) !important;
    background: rgba(14,116,144,0.36) !important;
}
div[data-testid="stHorizontalBlock"] {gap: 0.9rem;}
div[data-testid="stDataFrame"] {font-size: 0.95rem;}
.stTabs [data-baseweb="tab-list"] {gap:0.35rem; flex-wrap:wrap;}
.stTabs [data-baseweb="tab"] {
    min-height: 2.6rem;
    padding: 0.55rem 0.85rem;
    border-radius: 10px 10px 0 0;
    font-size: 0.95rem;
}
@media (max-width: 900px) {
    .block-container {padding-left: 0.9rem; padding-right: 0.9rem;}
    .product-strip {grid-template-columns: repeat(2, minmax(0,1fr));}
    div[data-testid="column"] {width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important;}
    .card, .layer-box, .product-card, div[data-testid="stMetric"] {min-height: auto;}
    h1 {font-size: 2rem !important;}
}
@media (max-width: 560px) {
    html, body, [class*="css"] {font-size: 15px;}
    .product-strip {grid-template-columns: 1fr;}
    .hero, .note, .question, .card, .layer-box, .product-card {padding: 0.9rem;}
    .stTabs [data-baseweb="tab"] {font-size: 0.88rem; padding: 0.5rem 0.65rem;}
}
</style>
""", unsafe_allow_html=True)
# UI IMPROVEMENT END

# UI REFINEMENT START
# Deployment-safe visual polish for product-style header, tabs, sidebar, and chart containers.
st.markdown("""
<style>
.taivas-brand {
    margin: 0.25rem 0 0.55rem 0;
}
.taivas-brand-title {
    font-size: clamp(2.2rem, 3vw, 3.35rem);
    line-height: 0.98;
    font-weight: 900;
    letter-spacing: 0;
}
.taivas-brand-subtitle {
    margin-top: 0.28rem;
    font-size: clamp(1.05rem, 1.45vw, 1.42rem);
    color: #CBD5E1;
    font-weight: 700;
}
.taivas-brand-kicker {
    margin-top: 0.42rem;
    color: #8EA0B8;
    font-size: 0.94rem;
}
.status-grid {
    display: grid;
    grid-template-columns: minmax(280px, 0.9fr) minmax(420px, 1.35fr);
    gap: 0.95rem;
    align-items: stretch;
}
.status-metrics {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
}
.chart-panel {
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 12px;
    background: rgba(15,23,42,0.36);
    padding: 0.75rem 0.85rem 0.35rem 0.85rem;
}
section[data-testid="stSidebar"] label {
    color: #F8FAFC !important;
    font-weight: 750 !important;
}
section[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: rgba(17,24,39,0.52);
}
section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
    color: #67E8F9;
}
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid rgba(148,163,184,0.18);
    padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0 !important;
    background: transparent !important;
    color: #CBD5E1;
    font-weight: 750;
}
.stTabs [aria-selected="true"] {
    color: #67E8F9 !important;
    border-bottom: 2px solid #38BDF8 !important;
}
@media (max-width: 980px) {
    .status-grid {grid-template-columns: 1fr;}
}
@media (max-width: 560px) {
    .status-metrics {grid-template-columns: 1fr;}
}
</style>
""", unsafe_allow_html=True)
# UI REFINEMENT END

# UI-ONLY CHANGE START
# Calm sci-fi command-center shell. Presentation only; no simulation values or data flow are changed.
st.markdown("""
<style>
body {
    background:
        radial-gradient(circle at 24% 8%, rgba(56,189,248,0.08), transparent 24%),
        radial-gradient(circle at 80% 0%, rgba(14,165,233,0.06), transparent 22%),
        #0B101B;
}
.block-container {
    position: relative;
}
.block-container::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(148,163,184,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(148,163,184,0.035) 1px, transparent 1px);
    background-size: 48px 48px;
    mask-image: linear-gradient(180deg, rgba(0,0,0,0.70), transparent 72%);
}
.taivas-brand {
    position: relative;
    padding: 1.05rem 1.15rem 1rem 1.15rem;
    border: 1px solid rgba(56,189,248,0.22);
    border-radius: 14px;
    background:
        linear-gradient(135deg, rgba(15,23,42,0.78), rgba(8,47,73,0.28)),
        radial-gradient(circle at 88% 30%, rgba(56,189,248,0.10), transparent 22%);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 18px 48px rgba(0,0,0,0.22);
}
.taivas-brand::after {
    content: "RESILIENCE COMMAND INTERFACE";
    position: absolute;
    top: 0.9rem;
    right: 1rem;
    color: rgba(125,211,252,0.72);
    font-size: 0.72rem;
    font-weight: 850;
    letter-spacing: 0.10em;
}
.command-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.9rem;
}
.command-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.42rem;
    padding: 0.36rem 0.58rem;
    border-radius: 999px;
    border: 1px solid rgba(148,163,184,0.22);
    background: rgba(15,23,42,0.48);
    color: #CBD5E1;
    font-size: 0.78rem;
    font-weight: 760;
}
.command-chip::before {
    content: "";
    width: 7px;
    height: 7px;
    border-radius: 999px;
    background: #22C55E;
    box-shadow: 0 0 10px rgba(34,197,94,0.45);
}
.quick-start,
.communication-summary,
.emergency-summary,
.risk-strip,
.scenario-card,
.chart-panel,
.visual-wrap,
div[data-testid="stMetric"],
.product-card,
.card,
.layer-box {
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.035), 0 10px 28px rgba(0,0,0,0.14);
}
.visual-wrap {
    background:
        linear-gradient(145deg, rgba(15,23,42,0.88), rgba(17,24,39,0.72)),
        radial-gradient(circle at 85% 15%, rgba(56,189,248,0.12), transparent 24%);
    border-color: rgba(56,189,248,0.20);
}
.visual-title::before {
    content: "MONITOR // ";
    color: rgba(125,211,252,0.70);
    font-size: 0.82rem;
    letter-spacing: 0.08em;
}
.scenario-map {
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.035), inset 0 -30px 90px rgba(8,13,28,0.42);
}
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(56,189,248,0.10);
}
@media (max-width: 760px) {
    .taivas-brand::after {
        position: static;
        display: block;
        margin-top: 0.7rem;
    }
}
</style>
""", unsafe_allow_html=True)
# UI-ONLY CHANGE END

# UI-ONLY CHANGE START
# Scenario comparison and risk storytelling styling only. No calculation logic or data source changes.
st.markdown("""
<style>
.risk-strip {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.8rem;
    padding: 0.9rem 1rem;
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(15,23,42,0.82), rgba(8,47,73,0.34));
    margin: 0.7rem 0 0.95rem 0;
}
.risk-title {font-size: 1rem; font-weight: 850; color: #F8FAFC;}
.risk-note {font-size: 0.9rem; color: #A7B3C7; margin-top: 0.2rem;}
.risk-badge {
    white-space: nowrap;
    border-radius: 999px;
    padding: 0.38rem 0.7rem;
    font-weight: 850;
    border: 1px solid rgba(148,163,184,0.26);
}
.risk-low {background: rgba(34,197,94,0.13); color: #86EFAC; border-color: rgba(34,197,94,0.34);}
.risk-moderate {background: rgba(56,189,248,0.13); color: #7DD3FC; border-color: rgba(56,189,248,0.34);}
.risk-high {background: rgba(245,158,11,0.14); color: #FCD34D; border-color: rgba(245,158,11,0.36);}
.risk-critical {background: rgba(248,113,113,0.14); color: #FCA5A5; border-color: rgba(248,113,113,0.34);}
.comparison-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.85rem;
    margin: 0.85rem 0 1rem 0;
}
.scenario-card {
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 12px;
    background: rgba(15,23,42,0.46);
    padding: 0.95rem;
}
.scenario-card h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
}
.comparison-row {
    display: grid;
    grid-template-columns: minmax(112px, 1fr) minmax(82px, auto) minmax(92px, auto);
    gap: 0.55rem;
    align-items: center;
    padding: 0.48rem 0;
    border-top: 1px solid rgba(148,163,184,0.12);
}
.comparison-row:first-of-type {border-top: 0;}
.comparison-label {color: #A7B3C7; font-size: 0.88rem;}
.comparison-value {font-weight: 850; text-align: right;}
.comparison-delta {font-size: 0.84rem; text-align: right; border-radius: 999px; padding: 0.2rem 0.44rem;}
.delta-up {background: rgba(245,158,11,0.13); color: #FCD34D;}
.delta-down {background: rgba(56,189,248,0.12); color: #7DD3FC;}
.delta-flat {background: rgba(148,163,184,0.12); color: #CBD5E1;}
.explain-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
    margin: 0.65rem 0 1rem 0;
}
.explain-card {
    border: 1px solid rgba(148,163,184,0.18);
    border-radius: 12px;
    background: rgba(15,23,42,0.34);
    padding: 0.85rem 0.95rem;
    color: #D7DEE9;
    line-height: 1.5;
}
.emergency-summary {
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(15,23,42,0.72), rgba(8,47,73,0.28));
    padding: 0.95rem 1rem;
    margin: 0.75rem 0 1rem 0;
}
.emergency-summary h3 {
    margin: 0 0 0.65rem 0;
    font-size: 1.05rem;
}
.emergency-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.72rem;
}
.emergency-item {
    border-left: 3px solid rgba(56,189,248,0.72);
    padding: 0.2rem 0 0.2rem 0.68rem;
}
.emergency-label {
    color: #A7B3C7;
    font-size: 0.78rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    margin-bottom: 0.2rem;
}
.emergency-text {
    color: #F8FAFC;
    font-size: 0.94rem;
    line-height: 1.42;
}
.communication-summary {
    border: 1px solid rgba(56,189,248,0.24);
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(8,47,73,0.42), rgba(15,23,42,0.64));
    padding: 0.95rem 1rem;
    margin: 0.75rem 0 1rem 0;
}
.communication-summary h3 {
    margin: 0 0 0.72rem 0;
    font-size: 1.05rem;
}
.communication-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
}
.communication-card {
    border: 1px solid rgba(148,163,184,0.18);
    border-radius: 12px;
    background: rgba(15,23,42,0.42);
    padding: 0.85rem 0.95rem;
}
.communication-label {
    color: #A7B3C7;
    font-size: 0.8rem;
    font-weight: 850;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    margin-bottom: 0.35rem;
}
.communication-text {
    color: #F8FAFC;
    line-height: 1.5;
    font-size: 0.95rem;
}
.communication-disclaimer {
    margin-top: 0.72rem;
    color: #A7B3C7;
    font-size: 0.84rem;
    line-height: 1.45;
    border-top: 1px solid rgba(148,163,184,0.14);
    padding-top: 0.62rem;
}
@media (max-width: 820px) {
    .comparison-grid, .explain-grid, .emergency-grid, .communication-grid {grid-template-columns: 1fr;}
    .risk-strip {align-items: flex-start; flex-direction: column;}
}
</style>
""", unsafe_allow_html=True)
# UI-ONLY CHANGE END



def safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def normalize_name(value: str) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def safe_str(value, default=""):
    try:
        if value is None:
            return default
        value = str(value).strip()
        return value if value else default
    except Exception:
        return default


def safe_read_csv(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        return pd.read_csv(uploaded_file)
    except Exception as e:
        st.sidebar.warning(f"CSV read failed: {e}")
        return None



def detect_timestamp_column(df: pd.DataFrame):
    if df is None or df.empty:
        return None
    candidates = [
        "timestamp", "datetime", "date", "time", "recorded_at",
        "created_at", "observation_time", "observed_at"
    ]
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    for c in df.columns:
        name = str(c).strip().lower()
        if "time" in name or "date" in name:
            return c
    return None

def sort_history_df(df: pd.DataFrame):
    if df is None or df.empty:
        return df, None, "original"
    ts_col = detect_timestamp_column(df)
    if ts_col is None:
        return df.copy(), None, "original"
    tmp = df.copy()
    parsed = pd.to_datetime(tmp[ts_col], errors="coerce")
    valid = parsed.notna().sum()
    if valid == 0:
        return df.copy(), ts_col, "original"
    tmp["_parsed_ts"] = parsed
    tmp = tmp.sort_values("_parsed_ts", kind="stable").drop(columns=["_parsed_ts"]).reset_index(drop=True)
    return tmp, ts_col, "timestamp"

def prepare_uploaded_preview(df: pd.DataFrame, max_rows: int = 8):
    if df is None or df.empty:
        return None, None, None
    sorted_df, ts_col, sorting_mode = sort_history_df(df)
    preview_df = sorted_df.copy()
    parsed_col = None
    if ts_col is not None:
        parsed_col = "__parsed_timestamp_display__"
        preview_df[parsed_col] = pd.to_datetime(preview_df[ts_col], errors="coerce")
    preferred_cols = []
    if ts_col is not None:
        preferred_cols.append(ts_col)
    if parsed_col is not None:
        preferred_cols.append(parsed_col)
    for c in ["country_key", "city_key", "temperature", "wind_speed", "solar_radiation", "precipitation", "humidity", "solar_capacity", "wind_capacity", "geothermal_capacity", "hydro_capacity", "battery_capacity"]:
        if c in preview_df.columns and c not in preferred_cols:
            preferred_cols.append(c)
    if not preferred_cols:
        preferred_cols = list(preview_df.columns)
    preview_df = preview_df[preferred_cols].head(max_rows).copy()
    return preview_df, ts_col, sorting_mode

def build_forecast_chart_df(multistep_df: pd.DataFrame):
    if multistep_df is None or multistep_df.empty:
        return pd.DataFrame()

    src_col = tr("source")
    step_col = tr("forecast_step")
    est_col = tr("next_step_estimate_pct")
    low_col = tr("lower_band_pct")
    up_col = tr("upper_band_pct")

    required_cols = [src_col, step_col, est_col, low_col, up_col]
    if any(col not in multistep_df.columns for col in required_cols):
        return pd.DataFrame()

    df = multistep_df.copy()

    # Create explicit label columns first, then pivot by column name.
    df["series_est"] = df[src_col].astype(str) + " • est"
    df["series_low"] = df[src_col].astype(str) + " • low"
    df["series_high"] = df[src_col].astype(str) + " • high"

    est_wide = df.pivot(index=step_col, columns="series_est", values=est_col)
    low_wide = df.pivot(index=step_col, columns="series_low", values=low_col)
    high_wide = df.pivot(index=step_col, columns="series_high", values=up_col)

    out = pd.concat([est_wide, low_wide, high_wide], axis=1).sort_index()
    out.index.name = step_col
    return out

def render_forecast_chart(multistep_df: pd.DataFrame):
    st.subheader(tr("forecast_chart"))
    st.markdown(f'<div class="note">{tr("forecast_chart_note")}</div>', unsafe_allow_html=True)
    chart_df = build_forecast_chart_df(multistep_df)
    if not chart_df.empty:
        st.line_chart(chart_df)

def build_uploaded_profiles(df: pd.DataFrame):
    if df is None or df.empty:
        return {}
    sorted_df, ts_col, _ = sort_history_df(df)
    rows = {}
    required = [
        "country_key", "city_key", "lat", "lon", "population",
        "temperature", "wind_speed", "solar_radiation", "precipitation", "humidity",
        "solar_capacity", "wind_capacity", "geothermal_capacity", "hydro_capacity", "battery_capacity",
    ]
    for idx, raw in sorted_df.iterrows():
        row = {k: raw[k] if k in sorted_df.columns else None for k in required}
        country_raw = str(row.get("country_key") or "Uploaded").strip() or "Uploaded"
        city_raw = str(row.get("city_key") or f"Row {idx + 1}").strip() or f"Row {idx + 1}"
        country = country_raw.replace("_", " ").title()
        city = city_raw.replace("_", " ").title()
        rows[f"{country} / {city}"] = {
            "country": country,
            "city": city,
            "lat": safe_float(row.get("lat"), 0.0),
            "lon": safe_float(row.get("lon"), 0.0),
            "population": safe_int(row.get("population"), 100000),
            "temperature": safe_int(row.get("temperature"), 20),
            "wind_speed": safe_float(row.get("wind_speed"), 4.0),
            "solar_radiation": safe_int(row.get("solar_radiation"), 500),
            "precipitation": safe_int(row.get("precipitation"), 10),
            "humidity": safe_int(row.get("humidity"), 60),
            "solar_capacity": safe_int(row.get("solar_capacity"), 120),
            "wind_capacity": safe_int(row.get("wind_capacity"), 80),
            "geothermal_capacity": safe_int(row.get("geothermal_capacity"), 60),
            "hydro_capacity": safe_int(row.get("hydro_capacity"), 70),
            "battery_capacity": safe_int(row.get("battery_capacity"), 180),
            "timestamp_value": safe_str(raw.get(ts_col), "") if ts_col is not None else "",
        }
    return rows



# =============================
# TAIVAS Geopolitical Energy Shock Module V1
# Integrated directly into the main file to avoid extra module dependency.
# =============================

GEOPOLITICAL_EVENT_WEIGHTS = {
    "None": 0.0,
    "Minor diplomatic tension": 0.30,
    "Proxy conflict escalation": 0.60,
    "Oil tanker attack": 0.90,
    "Energy infrastructure strike": 1.10,
    "Hormuz disruption": 1.50,
    "Regional war": 2.00,
}

GEOPOLITICAL_EVENT_NOTES = {
    "None": "No additional geopolitical shock is applied.",
    "Minor diplomatic tension": "Political pressure and market anxiety, but no major physical disruption.",
    "Proxy conflict escalation": "Indirect conflict raises logistics and price risk without full direct war.",
    "Oil tanker attack": "Maritime risk increases insurance, shipping delay, and fuel market volatility.",
    "Energy infrastructure strike": "Physical energy infrastructure damage raises supply and repair uncertainty.",
    "Hormuz disruption": "High-impact chokepoint disruption affecting oil and gas shipping routes.",
    "Regional war": "Large-scale regional conflict with severe energy market and logistics stress.",
}

def calculate_geopolitical_shock(event_type, severity, duration_days, import_dependency, fossil_share, shipping_dependency):
    event_type = event_type if event_type in GEOPOLITICAL_EVENT_WEIGHTS else "Proxy conflict escalation"
    severity = int(clamp(severity, 0, 5))
    duration_days = int(clamp(duration_days, 0, 90))
    import_dependency = clamp(float(import_dependency), 0.0, 1.0)
    fossil_share = clamp(float(fossil_share), 0.0, 1.0)
    shipping_dependency = clamp(float(shipping_dependency), 0.0, 1.0)
    duration_factor = min(duration_days / 30.0, 1.5)
    if event_type == "None" or severity == 0 or duration_days == 0:
        oil_supply_disruption = 0.0
    else:
        oil_supply_disruption = severity * GEOPOLITICAL_EVENT_WEIGHTS[event_type] * duration_factor * 4.0
    oil_supply_disruption = clamp(oil_supply_disruption, 0.0, 60.0)
    price_spike_index = oil_supply_disruption * 1.25
    logistics_stress = oil_supply_disruption * shipping_dependency * 1.15
    grid_stress_index = clamp(
        oil_supply_disruption * import_dependency * 0.42
        + oil_supply_disruption * fossil_share * 0.38
        + logistics_stress * 0.20,
        0.0, 100.0
    )
    if grid_stress_index < 10:
        risk_level = "Low"
    elif grid_stress_index < 25:
        risk_level = "Moderate"
    elif grid_stress_index < 45:
        risk_level = "High"
    else:
        risk_level = "Critical"
    return {
        "event_type": event_type,
        "severity": severity,
        "duration_days": duration_days,
        "oil_supply_disruption_percent": round(oil_supply_disruption, 2),
        "price_spike_index": round(price_spike_index, 2),
        "logistics_stress": round(logistics_stress, 2),
        "grid_stress_index": round(grid_stress_index, 2),
        "risk_level": risk_level,
        "supply_penalty_pct": round(clamp(grid_stress_index * 0.18, 0.0, 18.0), 2),
        "demand_penalty_pct": round(clamp(price_spike_index * 0.035, 0.0, 8.0), 2),
        "event_note": GEOPOLITICAL_EVENT_NOTES.get(event_type, "Geopolitical shock scenario."),
        "model_note": "Simplified geopolitical energy shock simulation for decision support; not a political or market forecast.",
    }

def apply_geopolitical_shock_to_results(results, shock):
    updated = dict(results)
    supply_penalty = clamp(float(shock.get("supply_penalty_pct", 0.0)) / 100.0, 0.0, 0.30)
    demand_penalty = clamp(float(shock.get("demand_penalty_pct", 0.0)) / 100.0, 0.0, 0.15)
    original_demand = float(updated.get("demand", 0.0))
    original_renewable = float(updated.get("renewable_supply", 0.0))
    original_final = float(updated.get("final_supply", 0.0))
    original_battery = float(updated.get("battery_levels", 0.0))
    adjusted_demand = original_demand * (1.0 + demand_penalty)
    adjusted_final = original_final * (1.0 - supply_penalty)
    adjusted_shortfall = max(0.0, adjusted_demand - adjusted_final)
    updated["demand"] = round(adjusted_demand, 2)
    updated["final_supply"] = round(adjusted_final, 2)
    updated["shortfall"] = round(adjusted_shortfall, 2)
    updated["grid_dependency"] = round(safe_div(adjusted_shortfall, adjusted_demand) * 100 if adjusted_demand > 0 else 0.0, 2)
    updated["system_efficiency"] = round(clamp(100 - adjusted_shortfall * 0.55 - float(shock.get("grid_stress_index", 0.0)) * 0.08, 0.0, 100.0), 2)
    updated["battery_levels"] = round(max(0.0, original_battery - adjusted_shortfall * 0.08), 2)
    updated["renewable_ratio"] = round(safe_div(original_renewable, adjusted_final) * 100 if adjusted_final > 0 else 0.0, 2)
    updated["geopolitical_event_type"] = shock.get("event_type")
    updated["geopolitical_risk_level"] = shock.get("risk_level")
    updated["geopolitical_grid_stress_index"] = shock.get("grid_stress_index", 0.0)
    updated["geopolitical_price_spike_index"] = shock.get("price_spike_index", 0.0)
    updated["geopolitical_oil_supply_disruption_percent"] = shock.get("oil_supply_disruption_percent", 0.0)
    return updated

def build_geopolitical_reason_chain(shock, results):
    if st.session_state.get("ui_lang", "English") == "繁體中文":
        return pd.DataFrame([
            {"Signal": "地緣政治事件", "Value": shock.get("event_type", "None"), "Interpretation": shock.get("event_note", "")},
            {"Signal": "油氣供應中斷估計", "Value": f"{shock.get('oil_supply_disruption_percent', 0)}%", "Interpretation": "用事件嚴重度、持續時間與地點權重估算的簡化中斷壓力。"},
            {"Signal": "價格衝擊指數", "Value": shock.get("price_spike_index", 0), "Interpretation": "代表市場價格與燃料成本壓力，不等於實際油價預測。"},
            {"Signal": "電網壓力指數", "Value": shock.get("grid_stress_index", 0), "Interpretation": f"目前風險等級：{shock.get('risk_level', 'Low')}。"},
            {"Signal": "系統結果", "Value": f"Shortfall {results.get('shortfall', 0)} MW", "Interpretation": "衝擊已折算進需求、可用供應、效率與外部依賴。"},
        ])
    return pd.DataFrame([
        {"Signal": "Geopolitical Event", "Value": shock.get("event_type", "None"), "Interpretation": shock.get("event_note", "")},
        {"Signal": "Oil/Gas Supply Disruption Estimate", "Value": f"{shock.get('oil_supply_disruption_percent', 0)}%", "Interpretation": "Simplified disruption pressure from severity, duration, and location weight."},
        {"Signal": "Price Spike Index", "Value": shock.get("price_spike_index", 0), "Interpretation": "Market and fuel-cost stress signal; not an oil price forecast."},
        {"Signal": "Grid Stress Index", "Value": shock.get("grid_stress_index", 0), "Interpretation": f"Current geopolitical risk level: {shock.get('risk_level', 'Low')}."},
        {"Signal": "System Result", "Value": f"Shortfall {results.get('shortfall', 0)} MW", "Interpretation": "Shock is reflected in demand, usable supply, efficiency, and grid dependency."},
    ])


def _risk_color_class(value):
    try:
        v = float(value)
    except Exception:
        v = 0.0
    if v >= 70:
        return "critical"
    if v >= 40:
        return "watch"
    return "stable"

def _scenario_stress_profile(results, geopolitical_shock=None):
    shock = geopolitical_shock or {}
    return {
        "solar": round(float(results.get("actual_mix_pct", {}).get("Solar", 0.0)), 1),
        "wind": round(float(results.get("actual_mix_pct", {}).get("Wind", 0.0)), 1),
        "hydro": round(float(results.get("actual_mix_pct", {}).get("Hydro", 0.0)), 1),
        "geothermal": round(float(results.get("actual_mix_pct", {}).get("Geothermal", 0.0)), 1),
        "grid_stress": round(float(results.get("grid_dependency", 0.0)), 1),
        "shortfall": round(float(results.get("shortfall", 0.0)), 2),
        "battery": round(float(results.get("battery_levels", 0.0)), 2),
        "geopolitical_stress": round(float(shock.get("grid_stress_index", results.get("geopolitical_grid_stress_index", 0.0))), 1),
        "oil_disruption": round(float(shock.get("oil_supply_disruption_percent", 0.0)), 1),
        "price_spike": round(float(shock.get("price_spike_index", 0.0)), 1),
    }

# UI IMPROVEMENT START
# Visual simulator layout polish only: card consistency and mobile-friendly grids.
def render_visual_simulator_header():
    st.markdown("""
        <style>
        .visual-wrap {border:1px solid rgba(148,163,184,0.22); border-radius:12px; padding:18px; background:linear-gradient(145deg, rgba(15,23,42,0.88), rgba(30,41,59,0.72)); margin:10px 0 18px 0;}
        .visual-title {font-size:1.26rem; font-weight:800; margin-bottom:6px;}
        .visual-note {opacity:0.84; font-size:0.98rem; line-height:1.6; margin-bottom:12px;}
        .flow-grid {display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:12px; margin-top:12px;}
        .flow-card {border:1px solid rgba(148,163,184,0.22); background:rgba(15,23,42,0.46); border-radius:12px; padding:13px; min-height:96px;}
        .flow-label {font-size:0.86rem; opacity:0.78; margin-bottom:7px; line-height:1.3;}
        .flow-value {font-size:1.38rem; font-weight:800; line-height:1.15;}
        .stable {box-shadow: inset 0 0 0 1px rgba(34,197,94,0.28);}
        .watch {box-shadow: inset 0 0 0 1px rgba(245,158,11,0.38);}
        .critical {box-shadow: inset 0 0 0 1px rgba(239,68,68,0.42);}
        .scenario-map {height:360px; position:relative; overflow:hidden; border-radius:12px; background:radial-gradient(circle at 50% 45%, rgba(59,130,246,0.22), transparent 30%), linear-gradient(180deg, rgba(2,6,23,0.85), rgba(15,23,42,0.95)); border:1px solid rgba(148,163,184,0.22); margin-top:12px;}
        .city-node {position:absolute; left:49%; top:48%; width:18px; height:18px; border-radius:99px; background:white; box-shadow:0 0 22px rgba(255,255,255,0.9);}
        .pulse {position:absolute; border:1px solid rgba(125,211,252,0.35); border-radius:999px; animation:pulse-ring 3s infinite ease-out;}
        .pulse.p2 {animation-delay:.65s;} .pulse.p3 {animation-delay:1.25s;}
        .storm-core {position:absolute; width:116px; height:116px; left:22%; top:24%; border-radius:999px; background:conic-gradient(from 45deg, rgba(148,163,184,0.10), rgba(56,189,248,0.75), rgba(15,23,42,0.15), rgba(96,165,250,0.65)); animation:spin 7s linear infinite; opacity:.9;}
        /* UI-ONLY CHANGE START: satellite-style typhoon visualization. */
        .satellite-layer {position:absolute; inset:0; background:radial-gradient(circle at 72% 49%, rgba(217,70,239,0.34), transparent 22%), radial-gradient(circle at 63% 52%, rgba(245,158,11,0.24), transparent 33%), radial-gradient(circle at 35% 60%, rgba(45,212,191,0.18), transparent 38%), linear-gradient(135deg, #17345b 0%, #10607a 36%, #174e72 62%, #10213f 100%);}
        .satellite-layer::before {content:""; position:absolute; inset:-20%; background-image:repeating-linear-gradient(104deg, transparent 0 28px, rgba(255,255,255,0.09) 29px, transparent 31px), radial-gradient(circle at 58% 40%, rgba(255,255,255,0.10), transparent 44%); opacity:.30; animation:wind-field-drift 11s linear infinite;}
        .satellite-layer::after {content:""; position:absolute; inset:0; background:radial-gradient(ellipse at 30% 58%, rgba(34,197,94,0.10), transparent 32%), linear-gradient(90deg, rgba(15,23,42,0.22), transparent 28%, transparent 74%, rgba(15,23,42,0.18)); pointer-events:none;}
        .satellite-grid {position:absolute; inset:0; background-image:linear-gradient(rgba(226,232,240,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(226,232,240,0.10) 1px, transparent 1px); background-size:64px 64px; opacity:.15;}
        .weather-land {position:absolute; left:-8%; top:-10%; width:40%; height:126%; background:linear-gradient(140deg, rgba(42,96,46,0.96), rgba(70,132,70,0.84) 48%, rgba(37,87,62,0.92)); clip-path:polygon(0 0, 72% 0, 60% 9%, 74% 18%, 61% 28%, 70% 37%, 54% 49%, 64% 60%, 47% 72%, 57% 86%, 40% 100%, 0 100%); filter:drop-shadow(0 0 16px rgba(0,0,0,0.38));}
        .weather-land::after {content:""; position:absolute; right:-10px; inset-block:0; width:26px; background:linear-gradient(180deg, transparent, rgba(187,247,208,0.26), transparent 28%, rgba(187,247,208,0.18), transparent 58%, rgba(187,247,208,0.22), transparent); filter:blur(4px);}
        .taiwan-island {position:absolute; left:18.5%; top:39%; width:48px; height:112px; background:linear-gradient(155deg, rgba(121,191,102,0.95), rgba(47,112,83,0.86)); clip-path:polygon(54% 0, 76% 8%, 88% 24%, 84% 43%, 72% 61%, 63% 79%, 46% 100%, 25% 92%, 16% 74%, 14% 52%, 21% 32%, 32% 14%); transform:rotate(18deg); box-shadow:0 0 0 1px rgba(226,232,240,0.30), 0 10px 24px rgba(0,0,0,0.28);}
        .map-label {position:absolute; left:16%; top:33%; color:rgba(226,232,240,0.62); font-size:.74rem; letter-spacing:.06em;}
        .wind-stream {position:absolute; height:2px; border-radius:999px; background:linear-gradient(90deg, transparent, rgba(240,249,255,0.88), transparent); opacity:.62; transform-origin:left center; animation:stream-flow 3.8s ease-in-out infinite;}
        .wind-stream.s1 {left:34%; top:19%; width:33%; transform:rotate(15deg);}
        .wind-stream.s2 {left:38%; top:31%; width:42%; transform:rotate(28deg); animation-delay:.4s;}
        .wind-stream.s3 {left:36%; top:48%; width:48%; transform:rotate(-7deg); animation-delay:.8s;}
        .wind-stream.s4 {left:30%; top:65%; width:42%; transform:rotate(-25deg); animation-delay:1.2s;}
        .wind-stream.s5 {left:55%; top:77%; width:34%; transform:rotate(-42deg); animation-delay:1.6s;}
        .typhoon-system {position:absolute; left:50%; top:23%; width:270px; height:270px; border-radius:999px; animation:typhoon-drift 8s ease-in-out infinite;}
        .typhoon-system::before {content:""; position:absolute; inset:18px; border-radius:999px; background:radial-gradient(circle, rgba(248,250,252,0.84) 0 8%, rgba(226,232,240,0.50) 9% 18%, transparent 19%), conic-gradient(from 18deg, rgba(248,250,252,0.20), transparent 38deg, rgba(255,255,255,0.44) 72deg, transparent 120deg, rgba(226,232,240,0.34) 174deg, transparent 230deg, rgba(248,250,252,0.38) 292deg, transparent 342deg); filter:blur(8px); opacity:.78; animation:typhoon-spin 28s linear infinite;}
        .typhoon-system::after {content:""; position:absolute; inset:46px; border-radius:999px; border:1px solid rgba(255,255,255,0.20); box-shadow:0 0 32px rgba(125,211,252,0.20);}
        .cloud-band {position:absolute; left:-18px; top:118px; width:265px; height:52px; border-radius:999px 42% 999px 42%; background:linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.74) 18%, rgba(226,232,240,0.46) 45%, rgba(125,211,252,0.14) 68%, transparent 100%); transform-origin:88% 50%; transform:rotate(-22deg); filter:blur(2px); opacity:.88; animation:cloud-arm-one 9s ease-in-out infinite;}
        .cloud-band::before {content:""; position:absolute; left:44px; top:-18px; width:132px; height:38px; border-radius:999px; background:radial-gradient(ellipse, rgba(255,255,255,0.76), rgba(226,232,240,0.25) 62%, transparent 76%);}
        .cloud-band::after {content:""; position:absolute; right:22px; bottom:-15px; width:104px; height:30px; border-radius:999px; background:radial-gradient(ellipse, rgba(248,250,252,0.50), rgba(125,211,252,0.14) 60%, transparent 78%);}
        .cloud-band.b2 {left:86px; top:34px; width:250px; height:48px; opacity:.80; transform-origin:2% 190%; transform:rotate(34deg); animation:cloud-arm-two 11s ease-in-out infinite; background:linear-gradient(270deg, transparent 0%, rgba(255,255,255,0.70) 24%, rgba(226,232,240,0.38) 54%, rgba(186,230,253,0.16) 72%, transparent 100%);}
        .cloud-band.b3 {left:74px; top:196px; width:230px; height:44px; opacity:.76; transform-origin:14% -190%; transform:rotate(-44deg); animation:cloud-arm-three 10s ease-in-out infinite; background:linear-gradient(95deg, transparent 0%, rgba(255,255,255,0.64) 23%, rgba(226,232,240,0.34) 50%, rgba(125,211,252,0.13) 74%, transparent 100%);}
        .typhoon-eye {position:absolute; left:calc(50% - 15px); top:calc(50% - 15px); width:30px; height:30px; border-radius:999px; background:radial-gradient(circle, rgba(9,16,31,0.98) 0 36%, rgba(255,255,255,0.92) 37% 57%, rgba(56,189,248,0.36) 58% 100%); box-shadow:0 0 18px rgba(125,211,252,0.55); z-index:3;}
        .rain-band {position:absolute; width:58%; height:2px; left:31%; top:36%; background:linear-gradient(90deg, transparent, rgba(240,249,255,0.82), transparent); transform:rotate(21deg); opacity:.62; animation:rain-sweep 3.2s ease-in-out infinite;}
        .rain-band.r2 {top:52%; left:29%; width:64%; animation-delay:.6s; opacity:.52;}
        .rain-band.r3 {top:68%; left:36%; width:50%; animation-delay:1.15s; opacity:.42;}
        .satellite-city-node {position:absolute; left:20.7%; top:50%; width:11px; height:11px; border-radius:99px; background:#ffffff; box-shadow:0 0 14px rgba(255,255,255,0.9), 0 0 30px rgba(56,189,248,0.55); z-index:4;}
        .impact-ring {position:absolute; left:calc(20.7% - 42px); top:calc(50% - 42px); width:94px; height:94px; border-radius:999px; border:1px solid rgba(125,211,252,0.34); animation:impact-pulse 2.8s ease-out infinite;}
        .impact-ring.r2 {animation-delay:.9s;}
        .storm-info-box {position:absolute; right:18%; top:21%; padding:8px 10px; border-left:1px solid rgba(255,255,255,0.68); background:rgba(15,23,42,0.32); color:#f8fafc; font-size:.8rem; line-height:1.35; min-width:112px;}
        .storm-info-box b {font-size:1.02rem;}
        .storm-info-box::before {content:""; position:absolute; left:-2px; top:100%; width:1px; height:112px; background:rgba(255,255,255,0.42);}
        .weather-scale {position:absolute; right:14px; bottom:14px; width:132px; height:10px; border-radius:999px; background:linear-gradient(90deg, #22c55e, #facc15, #fb7185, #a855f7, #38bdf8); box-shadow:0 0 0 1px rgba(255,255,255,0.18);}
        .weather-scale::before {content:"wind / rain intensity"; position:absolute; right:0; bottom:14px; color:#cbd5e1; font-size:.7rem;}
        .satellite-badge {position:absolute; left:14px; bottom:14px; padding:7px 10px; border-radius:999px; background:rgba(15,23,42,0.76); border:1px solid rgba(148,163,184,0.28); color:#cbd5e1; font-size:.76rem; letter-spacing:.01em;}
        .satellite-metric {position:absolute; right:14px; bottom:14px; display:grid; gap:6px; min-width:156px;}
        .satellite-metric span {display:flex; justify-content:space-between; gap:12px; padding:6px 9px; border-radius:10px; background:rgba(15,23,42,0.72); border:1px solid rgba(148,163,184,0.20); font-size:.78rem; color:#dbeafe;}
        /* UI-ONLY CHANGE END */
        /* UI-ONLY CHANGE START: richer non-typhoon visual scenarios. */
        .heat-map {position:absolute; inset:0; background:radial-gradient(circle at 47% 52%, rgba(248,113,113,0.45), transparent 18%), radial-gradient(circle at 34% 38%, rgba(251,146,60,0.22), transparent 22%), linear-gradient(135deg, #1a2440, #311c35 46%, #422016 100%);}
        .urban-grid {position:absolute; inset:0; background-image:linear-gradient(rgba(251,191,36,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(251,191,36,0.10) 1px, transparent 1px); background-size:44px 44px; opacity:.34;}
        .heat-core {position:absolute; left:38%; top:34%; width:190px; height:150px; border-radius:999px; background:radial-gradient(circle, rgba(254,240,138,0.72), rgba(251,146,60,0.44) 38%, rgba(239,68,68,0.20) 66%, transparent 78%); filter:blur(7px); animation:heat-breathe 3.2s infinite ease-in-out;}
        .heat-ring {position:absolute; left:calc(50% - 100px); top:calc(50% - 100px); width:200px; height:200px; border:1px solid rgba(251,191,36,0.26); border-radius:999px; animation:impact-pulse 3.4s ease-out infinite;}
        .heat-ring.r2 {animation-delay:1.2s;}
        .heat-arrow {position:absolute; width:130px; height:2px; background:linear-gradient(90deg, transparent, rgba(251,191,36,0.86)); opacity:.70; transform-origin:right center; animation:stream-flow 3s ease-in-out infinite;}
        .heat-arrow.a1 {left:14%; top:28%; transform:rotate(18deg);} .heat-arrow.a2 {left:16%; top:62%; transform:rotate(-18deg); animation-delay:.7s;} .heat-arrow.a3 {right:16%; top:32%; transform:rotate(160deg); animation-delay:1.1s;}
        .heat-panel {position:absolute; right:18px; top:18px; padding:10px 12px; border-radius:12px; background:rgba(15,23,42,0.64); border:1px solid rgba(251,191,36,0.28); color:#fde68a; font-size:.78rem; line-height:1.45;}
        .cold-map {position:absolute; inset:0; background:radial-gradient(circle at 50% 52%, rgba(96,165,250,0.20), transparent 22%), linear-gradient(135deg, #061526, #0d2442 48%, #17213c 100%);}
        .cold-map::before {content:""; position:absolute; inset:0; background-image:radial-gradient(circle, rgba(219,234,254,.65) 1px, transparent 1.7px); background-size:30px 30px; opacity:.44; animation:drift 10s linear infinite;}
        .cold-front {position:absolute; left:-8%; top:36%; width:116%; height:96px; background:linear-gradient(105deg, transparent, rgba(191,219,254,0.10), rgba(147,197,253,0.42), rgba(226,232,240,0.28), transparent); transform:rotate(-12deg); filter:blur(1px); animation:cold-front-slide 7s ease-in-out infinite;}
        .ice-band {position:absolute; left:14%; top:22%; width:72%; height:2px; background:linear-gradient(90deg, transparent, rgba(191,219,254,0.74), transparent); transform:rotate(-18deg); opacity:.60;}
        .ice-band.b2 {top:57%; transform:rotate(12deg); opacity:.46;} .ice-band.b3 {top:74%; transform:rotate(-7deg); opacity:.35;}
        .cold-core {position:absolute; left:calc(50% - 70px); top:calc(50% - 70px); width:140px; height:140px; border-radius:999px; background:radial-gradient(circle, rgba(219,234,254,0.42), rgba(59,130,246,0.18), transparent 72%); box-shadow:0 0 0 1px rgba(147,197,253,0.20);}
        .battery-dashboard {position:absolute; inset:0; background:radial-gradient(circle at 50% 50%, rgba(59,130,246,0.16), transparent 28%), linear-gradient(145deg, #071126, #111827);}
        .battery-flow {position:absolute; left:14%; right:14%; top:31%; height:2px; background:linear-gradient(90deg, transparent, rgba(34,197,94,0.76), rgba(250,204,21,0.70), rgba(239,68,68,0.58), transparent); opacity:.55; animation:stream-flow 2.6s ease-in-out infinite;}
        .battery-frame {position:absolute; left:26%; top:39%; width:48%; height:82px; border:2px solid rgba(226,232,240,.72); border-radius:22px; padding:9px; background:rgba(15,23,42,0.42); box-shadow:0 18px 40px rgba(0,0,0,.24);}
        .battery-frame::after {content:""; position:absolute; right:-25px; top:25px; width:20px; height:34px; border:2px solid rgba(226,232,240,.72); border-left:0; border-radius:0 8px 8px 0;}
        .battery-charge {height:100%; border-radius:14px; background:linear-gradient(90deg, #22c55e, #a3e635, #facc15, #fb923c, #ef4444); box-shadow:inset 0 0 18px rgba(255,255,255,0.18);}
        .battery-readout {position:absolute; left:26%; top:65%; display:flex; gap:8px; flex-wrap:wrap;}
        .battery-readout span {padding:6px 9px; border-radius:999px; background:rgba(15,23,42,0.70); border:1px solid rgba(148,163,184,0.24); color:#dbeafe; font-size:.76rem;}
        .geo-map {position:absolute; inset:0; background:radial-gradient(circle at 51% 50%, rgba(248,113,113,0.18), transparent 16%), linear-gradient(145deg, #091223, #111b32);}
        .geo-node {position:absolute; width:12px; height:12px; border-radius:999px; background:#f8fafc; box-shadow:0 0 18px rgba(248,250,252,0.78);}
        .geo-node.n1 {left:16%; top:52%;} .geo-node.n2 {left:50%; top:50%;} .geo-node.n3 {right:15%; top:42%;}
        .trade-route {position:absolute; left:16%; top:52%; width:70%; height:2px; background:linear-gradient(90deg, rgba(56,189,248,.20), rgba(248,113,113,.92), rgba(56,189,248,.18)); transform:rotate(-8deg); box-shadow:0 0 18px rgba(248,113,113,.42);}
        .route-pulse {position:absolute; left:48%; top:42%; width:82px; height:82px; border-radius:999px; background:radial-gradient(circle, rgba(248,113,113,.42), transparent 64%); animation:pulse-red 2.2s infinite ease-in-out;}
        .geo-panel {position:absolute; right:18px; bottom:18px; width:190px; padding:10px 12px; border-radius:12px; background:rgba(15,23,42,0.72); border:1px solid rgba(248,113,113,0.22); color:#e5e7eb; font-size:.76rem; line-height:1.5;}
        /* UI-ONLY CHANGE END */
        .heat-dome {position:absolute; width:240px; height:180px; left:28%; top:28%; border-radius:999px; background:radial-gradient(circle, rgba(251,146,60,0.38), rgba(239,68,68,0.16), transparent 70%); animation:heat-breathe 3.2s infinite ease-in-out;}
        .snow-band {position:absolute; inset:0; background-image:radial-gradient(circle, rgba(255,255,255,.55) 1px, transparent 1.5px); background-size:28px 28px; animation:drift 10s linear infinite; opacity:.45;}
        .route-line {position:absolute; left:14%; top:54%; width:72%; height:3px; background:linear-gradient(90deg, rgba(56,189,248,.15), rgba(248,113,113,.95), rgba(56,189,248,.15)); transform:rotate(-8deg); box-shadow:0 0 18px rgba(248,113,113,.65);}
        .route-shock {position:absolute; left:48%; top:43%; width:70px; height:70px; border-radius:999px; background:radial-gradient(circle, rgba(248,113,113,.65), transparent 62%); animation:pulse-red 2.2s infinite ease-in-out;}
        .battery-shell {position:absolute; left:27%; top:37%; width:46%; height:70px; border:2px solid rgba(255,255,255,.72); border-radius:18px; padding:8px;}
        .battery-tip {position:absolute; right:24%; top:45%; width:18px; height:38px; border:2px solid rgba(255,255,255,.72); border-left:none; border-radius:0 8px 8px 0;}
        .battery-fill {height:100%; border-radius:12px; background:linear-gradient(90deg, rgba(34,197,94,.88), rgba(250,204,21,.88), rgba(239,68,68,.88)); transition:width .5s ease;}
        @keyframes pulse-ring {0%{width:40px;height:40px;left:calc(50% - 20px);top:calc(50% - 20px);opacity:.75;}100%{width:300px;height:300px;left:calc(50% - 150px);top:calc(50% - 150px);opacity:0;}}
        @keyframes pulse-red {0%,100%{transform:scale(.78);opacity:.7;}50%{transform:scale(1.28);opacity:.25;}}
        @keyframes spin {to{transform:rotate(360deg);}}
        @keyframes typhoon-spin {to{transform:rotate(360deg);}}
        @keyframes typhoon-drift {0%,100%{transform:translate(0,0) scale(1);}50%{transform:translate(12px,6px) scale(1.03);}}
        @keyframes cloud-arm-one {0%,100%{transform:rotate(-22deg) translateX(0); opacity:.70;}50%{transform:rotate(-12deg) translateX(10px); opacity:.92;}}
        @keyframes cloud-arm-two {0%,100%{transform:rotate(34deg) translateX(0); opacity:.62;}50%{transform:rotate(46deg) translateX(-8px); opacity:.86;}}
        @keyframes cloud-arm-three {0%,100%{transform:rotate(-44deg) translateX(0); opacity:.58;}50%{transform:rotate(-34deg) translateX(8px); opacity:.82;}}
        @keyframes rain-sweep {0%,100%{transform:translateX(-8px) rotate(18deg); opacity:.28;}50%{transform:translateX(14px) rotate(18deg); opacity:.74;}}
        @keyframes cold-front-slide {0%,100%{transform:translateX(-18px) rotate(-12deg); opacity:.44;}50%{transform:translateX(18px) rotate(-12deg); opacity:.78;}}
        @keyframes wind-field-drift {to{transform:translate(72px, 18px);}}
        @keyframes stream-flow {0%,100%{opacity:.24; filter:blur(.4px);}50%{opacity:.82; filter:blur(0);}}
        @keyframes satellite-scan {to{transform:translate(74px,74px);}}
        @keyframes impact-pulse {0%{transform:scale(.55); opacity:.78;}100%{transform:scale(1.55); opacity:0;}}
        @keyframes heat-breathe {0%,100%{transform:scale(.92);opacity:.58;}50%{transform:scale(1.14);opacity:.9;}}
        @keyframes drift {to{background-position:60px 120px;}}
        @media (max-width: 900px) {
            .flow-grid {grid-template-columns: repeat(2, minmax(0, 1fr));}
            .scenario-map {height:300px;}
        }
        @media (max-width: 560px) {
            .flow-grid {grid-template-columns: 1fr;}
            .visual-wrap {padding:14px;}
            .scenario-map {height:260px;}
            .typhoon-system {left:45%; top:28%; width:190px; height:190px;}
            .weather-land {width:42%;}
            .taiwan-island {width:44px; height:88px;}
            .storm-info-box {right:10%; top:16%; transform:scale(.86); transform-origin:top right;}
            .satellite-metric {left:14px; right:auto; bottom:48px; min-width:0;}
        }
        </style>
        """, unsafe_allow_html=True)

def render_visual_metric_cards(profile):
    st.markdown(f"""
        <div class="flow-grid">
          <div class="flow-card {_risk_color_class(100-profile['solar'])}"><div class="flow-label">Solar Contribution</div><div class="flow-value">{profile['solar']}%</div></div>
          <div class="flow-card {_risk_color_class(100-profile['wind'])}"><div class="flow-label">Wind Contribution</div><div class="flow-value">{profile['wind']}%</div></div>
          <div class="flow-card {_risk_color_class(profile['grid_stress'])}"><div class="flow-label">Grid Dependency</div><div class="flow-value">{profile['grid_stress']}%</div></div>
          <div class="flow-card {_risk_color_class(profile['geopolitical_stress'])}"><div class="flow-label">Geo Shock Stress</div><div class="flow-value">{profile['geopolitical_stress']}</div></div>
        </div>
        """, unsafe_allow_html=True)
# UI IMPROVEMENT END

def render_scenario_visual_map(visual_scenario, profile):
    # Situation Awareness Layer: scenario impact field and disruption visualization.
    visual_title = "Storage Buffer Depletion" if visual_scenario == "Battery Depletion" else visual_scenario
    try:
        battery_pct = int(clamp(profile.get("battery", 0.0) / max(float(inputs.get("battery_capacity", 1.0)), 1.0) * 100.0, 0.0, 100.0))
    except Exception:
        battery_pct = 50
    if visual_scenario == "Typhoon Impact":
        # UI-ONLY CHANGE START
        inner = f"""
            <div class="satellite-layer">
              <div class="satellite-grid"></div>
              <div class="weather-land"></div>
              <div class="taiwan-island"></div>
              <div class="map-label">TAIWAN</div>
              <div class="wind-stream s1"></div>
              <div class="wind-stream s2"></div>
              <div class="wind-stream s3"></div>
              <div class="wind-stream s4"></div>
              <div class="wind-stream s5"></div>
              <div class="typhoon-system">
                <div class="cloud-band"></div>
                <div class="cloud-band b2"></div>
                <div class="cloud-band b3"></div>
                <div class="typhoon-eye"></div>
              </div>
              <div class="storm-info-box">mode<br><b>{scenario_key.replace("_", " ").title()}</b><br>scenario field</div>
              <div class="rain-band"></div>
              <div class="rain-band r2"></div>
              <div class="rain-band r3"></div>
              <div class="impact-ring"></div>
              <div class="impact-ring r2"></div>
              <div class="satellite-city-node"></div>
              <div class="satellite-badge">Scenario visualization - Not live weather data</div>
              <div class="weather-scale"></div>
              <div class="satellite-metric">
                <span><b>Solar</b><b>{profile.get("solar", 0)}%</b></span>
                <span><b>Wind</b><b>{profile.get("wind", 0)}%</b></span>
                <span><b>Battery</b><b>{profile.get("battery", 0)} MWh</b></span>
              </div>
            </div>
        """
        caption = "Satellite-style scenario view: cloud bands represent typhoon pressure on solar output, wind stability, and battery support. This is a simulation visual, not live weather data."
        # UI-ONLY CHANGE END
    elif visual_scenario == "Heat Wave Spread":
        # UI-ONLY CHANGE START
        inner = f"""
            <div class="heat-map">
              <div class="urban-grid"></div>
              <div class="heat-core"></div>
              <div class="heat-ring"></div>
              <div class="heat-ring r2"></div>
              <div class="heat-arrow a1"></div>
              <div class="heat-arrow a2"></div>
              <div class="heat-arrow a3"></div>
              <div class="satellite-city-node" style="left:50%; top:52%;"></div>
              <div class="heat-panel">Heat load<br><b>{results.get("demand", 0)} MW</b><br>Cooling pressure</div>
              <div class="satellite-badge">Scenario heat-risk field - Not live weather data</div>
            </div>
        """
        # UI-ONLY CHANGE END
        caption = "Heat load expands around the city; demand rises while cooling-sensitive facilities consume reserve margin faster."
    elif visual_scenario == "Blizzard / Cold Wave":
        # UI-ONLY CHANGE START
        inner = """
            <div class="cold-map">
              <div class="cold-front"></div>
              <div class="ice-band"></div>
              <div class="ice-band b2"></div>
              <div class="ice-band b3"></div>
              <div class="cold-core"></div>
              <div class="impact-ring" style="left:calc(50% - 47px); top:calc(50% - 47px);"></div>
              <div class="impact-ring r2" style="left:calc(50% - 47px); top:calc(50% - 47px);"></div>
              <div class="satellite-city-node" style="left:50%; top:50%;"></div>
              <div class="satellite-badge">Cold-front simulation field</div>
            </div>
        """
        # UI-ONLY CHANGE END
        caption = "Cold stress suppresses solar availability, raises heating load, and shortens survival time when reserve is weak."
    elif visual_scenario == "Battery Depletion":
        # UI-ONLY CHANGE START
        inner = f"""
            <div class="battery-dashboard">
              <div class="battery-flow"></div>
              <div class="battery-frame"><div class="battery-charge" style="width:{battery_pct}%;"></div></div>
              <div class="battery-readout">
                <span>Reserve {battery_pct}%</span>
                <span>{profile.get("battery", 0)} MWh</span>
                <span>Gap {profile.get("shortfall", 0)} MW</span>
              </div>
              <div class="satellite-badge">Storage buffer view</div>
            </div>
        """
        # UI-ONLY CHANGE END
        caption = "Storage reserve is the visible emergency buffer between disrupted supply and critical facility failure."
    else:
        # UI-ONLY CHANGE START
        inner = f"""
            <div class="geo-map">
              <div class="trade-route"></div>
              <div class="route-pulse"></div>
              <div class="geo-node n1"></div>
              <div class="geo-node n2"></div>
              <div class="geo-node n3"></div>
              <div class="impact-ring" style="left:calc(50% - 47px); top:calc(50% - 47px);"></div>
              <div class="geo-panel">Route pressure<br><b>{profile.get("geopolitical_stress", 0)}</b><br>Grid stress signal</div>
              <div class="satellite-badge">Supply-route risk simulation</div>
            </div>
        """
        # UI-ONLY CHANGE END
        caption = "External shock travels through fuel markets, import routes, logistics, and grid dependency before appearing as shortfall."
    st.markdown(f"""
        <div class="visual-wrap">
          <div class="visual-title">{visual_title}</div>
          <div class="visual-note">{caption}</div>
          <div class="scenario-map">{inner}</div>
        </div>
        """, unsafe_allow_html=True)

def render_energy_flow_diagram(profile):
    st.markdown("#### Energy Flow Interpretation")
    for name, value in [("Solar", profile["solar"]), ("Wind", profile["wind"]), ("Hydro", profile["hydro"]), ("Geothermal", profile["geothermal"])]:
        width = max(4, min(100, int(value)))
        st.markdown(f"""
            <div style="display:grid; grid-template-columns:minmax(86px, 120px) minmax(120px, 1fr) 72px; gap:10px; align-items:center; margin:10px 0; font-size:0.96rem;">
              <div style="font-weight:700; opacity:.9;">{name}</div>
              <div style="height:12px; background:rgba(255,255,255,.10); border-radius:999px; overflow:hidden;">
                <div style="width:{width}%; height:100%; background:linear-gradient(90deg, rgba(96,165,250,.95), rgba(34,211,238,.95)); border-radius:999px;"></div>
              </div>
              <div style="text-align:right; opacity:.85;">{value}%</div>
            </div>
            """, unsafe_allow_html=True)

def render_visual_scenario_layer(results, baseline_results, geopolitical_shock=None):
    # Situation Awareness Layer: combines scenario visual, stress chain, and system pressure cues.
    render_visual_simulator_header()
    st.markdown(f'<div class="note">{tr("visual_simulator_note")}</div>', unsafe_allow_html=True)
    left, right = st.columns([1.05, 1.4])
    with left:
        # UI-ONLY CHANGE START
        visual_labels = {"Battery Depletion": "Storage Buffer Depletion"}
        visual_scenario = st.selectbox(
            tr("visual_scenario"),
            ["Typhoon Impact", "Heat Wave Spread", "Blizzard / Cold Wave", "Battery Depletion", "Geopolitical Shock"],
            format_func=lambda option: visual_labels.get(option, option),
        )
        # UI-ONLY CHANGE END
        profile = _scenario_stress_profile(results, geopolitical_shock)
        render_visual_metric_cards(profile)
        st.markdown("#### Stress Chain")
        if visual_scenario == "Geopolitical Shock":
            chain_df = pd.DataFrame([
                {"Stage": "External event", "Signal": str((geopolitical_shock or {}).get("event_type", "None"))},
                {"Stage": "Oil / gas disruption", "Signal": f"{profile['oil_disruption']}%"},
                {"Stage": "Price spike", "Signal": profile["price_spike"]},
                {"Stage": "Grid stress", "Signal": profile["geopolitical_stress"]},
                {"Stage": "Shortfall", "Signal": f"{profile['shortfall']} MW"},
            ])
        elif visual_scenario == "Battery Depletion":
            chain_df = pd.DataFrame([
                {"Stage": "Demand", "Signal": f"{results.get('demand', 0)} MW"},
                {"Stage": "Renewable supply", "Signal": f"{results.get('renewable_supply', 0)} MW"},
                {"Stage": "Storage buffer remaining", "Signal": f"{profile['battery']} MWh"},
                {"Stage": "Energy gap", "Signal": f"{profile['shortfall']} MW"},
            ])
        else:
            chain_df = pd.DataFrame([
                {"Stage": "Climate event", "Signal": visual_scenario},
                {"Stage": "Renewable change", "Signal": f"Solar {profile['solar']}% / Wind {profile['wind']}%"},
                {"Stage": "Grid dependency", "Signal": f"{profile['grid_stress']}%"},
                {"Stage": "Battery buffer", "Signal": f"{profile['battery']} MWh"},
                {"Stage": "Shortfall", "Signal": f"{profile['shortfall']} MW"},
            ])
        st.dataframe(chain_df, use_container_width=True, hide_index=True)
    with right:
        render_scenario_visual_map(visual_scenario, profile)
        render_energy_flow_diagram(profile)

def extend_i18n():
    extras = {
        "English": {
            "sim_hours": "Simulation Hours",
            "survival_mode": "Survival Mode",
            "enable_thermal": "Enable Thermal Concept",
            "animation_speed": "Animation Speed",
            "uploaded_data": "Uploaded Open Data CSV",
            "use_uploaded": "Use uploaded row as input preset",
            "uploaded_row": "Uploaded Row",
            "csv_mode": "CSV Preset Mode",
            "uploaded_preview": "Uploaded History Preview",
            "selected_timestamp": "Selected Timestamp",
            "parsed_timestamp": "Parsed Timestamp",
            "forecast_chart": "Forecast Chart",
            "forecast_chart_note": "This chart visualizes each source across the forecast horizon, including lower and upper confidence bands.",
            "source_logic": "Source Forecast Logic",
            "source_logic_note": "Different sources do not accelerate at the same rate. Solar and wind react more strongly to weather shifts, geothermal is more damped, and hydro sits in the middle unless the scenario widens uncertainty.",
            "source_forecast_factor": "Source Forecast Factor",
            "geopolitical_inputs": "Geopolitical Risk Inputs",
            "enable_geopolitical_shock": "Enable Geopolitical Shock",
            "geopolitical_event_type": "Geopolitical Event Type",
            "geopolitical_severity": "Conflict Severity",
            "geopolitical_duration_days": "Shock Duration Days",
            "fossil_share": "Fossil Fuel Share",
            "geopolitical_panel": "Geopolitical Energy Shock",
            "oil_supply_disruption": "Oil Supply Disruption",
            "price_spike_index": "Price Spike Index",
            "geopolitical_grid_stress": "Geopolitical Grid Stress",
            "geopolitical_risk_level": "Geopolitical Risk Level",
            "geopolitical_reason_chain": "Geopolitical Reason Chain",
            "geopolitical_model_note": "This module converts geopolitical tension into energy-system stress. It is for decision support, not prediction.",
            "visual_simulator": "Visual Scenario Simulator",
            "visual_scenario": "Visual Scenario",
            "visual_simulator_note": "This visual layer turns the current model outputs into an intuitive disruption map. It is designed for quick explanation during demos, not as a GIS or real-time weather product."
        },
        "繁體中文": {
            "sim_hours": "模擬時數",
            "survival_mode": "生存模式",
            "enable_thermal": "啟用熱管理概念",
            "animation_speed": "動畫速度",
            "uploaded_data": "上傳 Open Data CSV",
            "use_uploaded": "使用上傳列作為輸入預設",
            "uploaded_row": "上傳資料列",
            "csv_mode": "CSV 預設模式",
            "uploaded_preview": "上傳歷史預覽",
            "selected_timestamp": "選定時間",
            "parsed_timestamp": "解析後時間",
            "forecast_chart": "預測圖表",
            "forecast_chart_note": "這張圖會把各能源在 forecast horizon 中的預測值，以及上下信賴帶一起畫出來。",
            "source_logic": "來源預測邏輯",
            "source_logic_note": "不同能源的加速/阻尼不一樣。太陽能與風能對天氣變化更敏感，地熱較平穩，水力通常介於中間，極端情境下不確定性會再放大。",
            "source_forecast_factor": "來源預測因子",
            "geopolitical_inputs": "地緣政治風險輸入",
            "enable_geopolitical_shock": "啟用地緣政治衝擊",
            "geopolitical_event_type": "地緣政治事件類型",
            "geopolitical_severity": "衝突嚴重度",
            "geopolitical_duration_days": "衝擊持續天數",
            "fossil_share": "化石燃料占比",
            "geopolitical_panel": "地緣政治能源衝擊",
            "oil_supply_disruption": "油氣供應中斷",
            "price_spike_index": "價格衝擊指數",
            "geopolitical_grid_stress": "地緣政治電網壓力",
            "geopolitical_risk_level": "地緣政治風險等級",
            "geopolitical_reason_chain": "地緣政治理由鏈",
            "geopolitical_model_note": "此模組將地緣政治緊張轉換為能源系統壓力，僅供決策支援，不是預測。",
            "visual_simulator": "情境視覺模擬器",
            "visual_scenario": "視覺情境",
            "visual_simulator_note": "此視覺層會把目前模型輸出轉成直覺化的中斷圖，適合 Demo 快速說明；它不是 GIS，也不是即時氣象產品。"
        },
    }
    for lang, mapping in extras.items():
        I18N.setdefault(lang, {}).update({k: v for k, v in mapping.items() if k not in I18N.get(lang, {})})


extend_i18n()

# USER-FRIENDLY UI START
# Plain-English display labels and helper copy only. Calculation keys and formulas stay unchanged.
I18N["English"].update({
    "shortfall": "Energy Gap",
    "grid": "Backup Grid Need",
    "rr": "Renewable Share",
    "eff": "System Stability",
    "quick_start": "Quick Start",
    "quick_start_body": "Choose a city, select a climate scenario, then run the simulation.",
    "basic_setup": "Basic Setup",
    "scenario_setup": "Scenario",
    "energy_capacity": "Energy Capacity",
    "advanced_settings": "Advanced Settings",
    "export_report": "Export / Report",
    "basic_setup_help": "Start here. Pick the location, facility type, and population.",
    "scenario_help": "Choose the climate or disruption situation you want to test.",
    "capacity_help": "Set the available local energy resources. Higher capacity usually improves resilience.",
    "advanced_help": "Optional expert controls for weather details, component failures, security risk, timeline, and thermal concepts.",
    "export_help": "After the simulation loads, use the Export Center in the dashboard to download CSV, TXT, or JSON reports.",
    "metric_help": "Energy Gap shows unmet demand. Renewable Share shows how much supply comes from renewables. System Stability is the simplified health score. Backup Grid Need shows how much outside grid support may be needed.",
    "product_positioning": "TAIVAS is an energy resilience decision-support simulator for evaluating infrastructure stability under extreme climate scenarios.",
    "main_system_status": "Main System Status",
    "battery_storage_status": "Battery / Storage Status",
    "renewable_mix": "Renewable Mix",
    "advanced_analytics": "Advanced Analytics",
    "scenario_analysis": "Scenario Analysis",
    "overview": "Overview",
    "view_detailed_analysis": "View Detailed Technical Analysis",
    "low_shortfall_risk": "Low shortfall risk",
    "supply_stress_detected": "Supply stress detected",
    "high_grid_instability_risk": "High grid instability risk",
    "battery_reserve_declining": "Battery reserve declining",
    "battery_reserve_available": "Battery reserve available",
    "renewable_acceptable": "Renewable contribution acceptable",
    "renewable_watch": "Renewable contribution needs attention",
})
# USER-FRIENDLY UI END

with st.sidebar:
    ui_lang = st.selectbox("Language / 語言", list(I18N.keys()), index=list(I18N.keys()).index(st.session_state.get("ui_lang", "English")))
    st.session_state["ui_lang"] = ui_lang
    st.header(tr("controls"))
    # USER-FRIENDLY UI START
    basic_panel = st.expander(tr("basic_setup"), expanded=True)
    basic_panel.caption(tr("basic_setup_help"))

    demo_mode = basic_panel.selectbox(
        "Demo Mode",
        ["Manual", "Taiwan Typhoon", "Finland Blizzard", "Germany Energy Security", "Middle East Shock"],
        index=0,
        help="Use a prepared scenario for fast demos. Manual keeps all sidebar values unchanged.",
    )
    if demo_mode != "Manual":
        basic_panel.caption(f"Demo preset active: {demo_mode}")

    use_csv_upload = basic_panel.checkbox("Use uploaded CSV", value=False, help="Optional. Leave this off for a simple guided setup.")
    uploaded_baseline_file = basic_panel.file_uploader(tr("uploaded_data"), type=["csv"], key="uploaded_baseline_csv") if use_csv_upload else None
    uploaded_df = safe_read_csv(uploaded_baseline_file)
    uploaded_profiles = build_uploaded_profiles(uploaded_df)
    use_uploaded = False
    uploaded_profile = None
    uploaded_preview_df, uploaded_ts_col, uploaded_sorting_mode = prepare_uploaded_preview(uploaded_df)
    if uploaded_profiles:
        use_uploaded = basic_panel.toggle(tr("use_uploaded"), value=True)
        uploaded_row_key = basic_panel.selectbox(tr("uploaded_row"), list(uploaded_profiles.keys()))
        uploaded_profile = uploaded_profiles.get(uploaded_row_key)
        basic_panel.caption(f"{tr('csv_mode')}: {uploaded_row_key}")
        if uploaded_profile is not None:
            basic_panel.caption(f"{tr('selected_timestamp')}: {uploaded_profile.get('timestamp_value', '-') or '-'}")
        show_uploaded_preview = basic_panel.checkbox(tr("uploaded_preview"), value=False)
        if show_uploaded_preview:
            if uploaded_ts_col is not None:
                basic_panel.caption(f"{tr('timestamp_col')}: {uploaded_ts_col} • {tr('sorting_mode')}: {tr('timestamp_sorted') if uploaded_sorting_mode == 'timestamp' else tr('original_order')}")
            if uploaded_preview_df is not None:
                basic_panel.dataframe(uploaded_preview_df, use_container_width=True, hide_index=True)

    merged_city_data = {country_name: dict(cities) for country_name, cities in CITY_DATA.items()}
    for profile in uploaded_profiles.values():
        csv_country = safe_str(profile.get("country"), "Uploaded")
        csv_city = safe_str(profile.get("city"), "Row")
        merged_city_data.setdefault(csv_country, {})
        merged_city_data[csv_country].setdefault(csv_city, {
            "lat": safe_float(profile.get("lat"), 0.0),
            "lon": safe_float(profile.get("lon"), 0.0),
            "population": safe_int(profile.get("population"), 100000),
            "country_model": "CSV Open Data Model",
        })

    default_country = uploaded_profile["country"] if (use_uploaded and uploaded_profile) else list(merged_city_data.keys())[0]
    country_options = list(merged_city_data.keys())
    country_index = country_options.index(default_country) if default_country in country_options else 0
    country = basic_panel.selectbox(tr("country"), country_options, index=country_index, disabled=(use_uploaded and uploaded_profile is not None), help="Choose the country or uploaded location profile.")

    city_options = list(merged_city_data[country].keys())
    default_city = uploaded_profile["city"] if (use_uploaded and uploaded_profile and uploaded_profile["country"] == country) else city_options[0]
    city_index = city_options.index(default_city) if default_city in city_options else 0
    city = basic_panel.selectbox(tr("city"), city_options, index=city_index, disabled=(use_uploaded and uploaded_profile is not None), help="Choose the city to simulate.")
    city_profile = merged_city_data[country][city]

    active_country = uploaded_profile["country"] if (use_uploaded and uploaded_profile) else country
    active_city = uploaded_profile["city"] if (use_uploaded and uploaded_profile) else city
    active_lat = uploaded_profile["lat"] if (use_uploaded and uploaded_profile) else city_profile["lat"]
    active_lon = uploaded_profile["lon"] if (use_uploaded and uploaded_profile) else city_profile["lon"]
    active_population = uploaded_profile["population"] if (use_uploaded and uploaded_profile) else int(city_profile["population"])

    facility_type = basic_panel.selectbox(tr("facility_type"), list(FACILITY_PROFILES.keys()), help="Choose the kind of building or site being protected.")
    facility_profile = FACILITY_PROFILES[facility_type]
    population = basic_panel.slider(tr("population"), 10000, 5000000, int(clamp(active_population, 10000, 5000000)), step=10000, help="Approximate number of people affected by this energy system.")
    basic_panel.caption(f"{tr('population')}: {population:,}")

    scenario_panel = st.expander(tr("scenario_setup"), expanded=True)
    scenario_panel.caption(tr("scenario_help"))
    scenario_key = scenario_panel.selectbox(tr("weather_scenario"), list(SCENARIOS.keys()), help="Pick the main situation to simulate, such as normal, heat wave, storm, blizzard, or typhoon.")

    capacity_panel = st.expander(tr("energy_capacity"), expanded=True)
    capacity_panel.caption(tr("capacity_help"))
    solar_capacity = capacity_panel.slider(tr("solar_capacity"), 0, 500, int(clamp((uploaded_profile["solar_capacity"] if (use_uploaded and uploaded_profile) else 120), 0, 500)), 5, help="Local solar power capacity in MW.")
    wind_capacity = capacity_panel.slider(tr("wind_capacity"), 0, 500, int(clamp((uploaded_profile["wind_capacity"] if (use_uploaded and uploaded_profile) else 80), 0, 500)), 5, help="Local wind power capacity in MW.")
    battery_capacity = capacity_panel.slider(tr("battery_capacity"), 0, 1000, int(clamp((uploaded_profile["battery_capacity"] if (use_uploaded and uploaded_profile) else 180), 0, 1000)), 10, help="Battery reserve capacity in MWh.")

    advanced_panel = st.expander(tr("advanced_settings"), expanded=False)
    advanced_panel.caption(tr("advanced_help"))
    advanced_panel.markdown("**Additional energy sources**")
    geothermal_capacity = advanced_panel.slider(tr("geothermal_capacity"), 0, 500, int(clamp((uploaded_profile["geothermal_capacity"] if (use_uploaded and uploaded_profile) else 60), 0, 500)), 5, help="Stable geothermal capacity in MW.")
    hydro_capacity = advanced_panel.slider(tr("hydro_capacity"), 0, 500, int(clamp((uploaded_profile["hydro_capacity"] if (use_uploaded and uploaded_profile) else 70), 0, 500)), 5, help="Hydro power capacity in MW.")
    advanced_panel.markdown("**Weather details**")
    temperature = advanced_panel.slider(tr("temperature") + " (°C)", -20, 50, int(clamp((uploaded_profile["temperature"] if (use_uploaded and uploaded_profile) else 26), -20, 50)), 1, help="Used to estimate heating or cooling pressure.")
    wind_speed = advanced_panel.slider(tr("wind_speed") + " (m/s)", 0.0, 30.0, float(clamp((uploaded_profile["wind_speed"] if (use_uploaded and uploaded_profile) else 4.2), 0.0, 30.0)), 0.1, help="Affects wind power output.")
    solar_radiation = advanced_panel.slider(tr("solar_radiation") + " (W/m²)", 0, 1200, int(clamp((uploaded_profile["solar_radiation"] if (use_uploaded and uploaded_profile) else 640), 0, 1200)), 10, help="Affects solar power output.")
    precipitation = advanced_panel.slider(tr("precipitation") + " (mm)", 0, 300, int(clamp((uploaded_profile["precipitation"] if (use_uploaded and uploaded_profile) else 12), 0, 300)), 1, help="Affects demand and hydro behavior.")
    humidity = advanced_panel.slider(tr("humidity") + " (%)", 0, 100, int(clamp((uploaded_profile["humidity"] if (use_uploaded and uploaded_profile) else 73), 0, 100)), 1, help="Higher humidity can increase cooling pressure.")

    advanced_panel.markdown("**Component failures**")
    solar_failure_ratio = advanced_panel.number_input(tr("solar_failure_ratio"), 0.0, 1.0, 0.00, 0.05, format="%.2f", help="0 means no failure. 1 means fully unavailable.")
    wind_failure_ratio = advanced_panel.number_input(tr("wind_failure_ratio"), 0.0, 1.0, 0.00, 0.05, format="%.2f")
    geothermal_failure_ratio = advanced_panel.number_input(tr("geothermal_failure_ratio"), 0.0, 1.0, 0.00, 0.05, format="%.2f")
    hydro_failure_ratio = advanced_panel.number_input(tr("hydro_failure_ratio"), 0.0, 1.0, 0.00, 0.05, format="%.2f")
    battery_failure_ratio = advanced_panel.number_input(tr("battery_failure_ratio"), 0.0, 1.0, 0.00, 0.05, format="%.2f")

    advanced_panel.markdown("**Energy security**")
    energy_security_scenario = advanced_panel.selectbox(tr("energy_security_scenario"), list(ENERGY_SECURITY_SCENARIOS.keys()))
    import_dependency = advanced_panel.number_input(tr("import_dependency"), 0.0, 1.0, 0.70, 0.01, format="%.2f", help="How much the system relies on external energy supply.")
    strategic_reserve_days = advanced_panel.number_input(tr("strategic_reserve_days"), 0, 365, 20, 1)
    shipping_dependency = advanced_panel.number_input(tr("shipping_dependency"), 0.0, 1.0, 0.85, 0.01, format="%.2f")
    infrastructure_damage_ratio = advanced_panel.number_input(tr("infrastructure_damage_ratio"), 0.0, 1.0, 0.10, 0.01, format="%.2f")
    reserve_recovery_lag_days = advanced_panel.number_input(tr("reserve_recovery_lag_days"), 0, 30, 3, 1)

    advanced_panel.markdown("**Geopolitical shock**")
    enable_geopolitical_shock = advanced_panel.toggle(tr("enable_geopolitical_shock"), value=False)
    geopolitical_event_type = advanced_panel.selectbox(tr("geopolitical_event_type"), list(GEOPOLITICAL_EVENT_WEIGHTS.keys()), index=0)
    geopolitical_severity = advanced_panel.slider(tr("geopolitical_severity"), 0, 5, 2, 1)
    geopolitical_duration_days = advanced_panel.slider(tr("geopolitical_duration_days"), 0, 90, 7, 1)
    fossil_share = advanced_panel.slider(tr("fossil_share"), 0.0, 1.0, 0.40, 0.05)

    advanced_panel.markdown("**Timeline and forecast**")
    rolling_window_rows = advanced_panel.slider(tr("time_window_rows"), 2, 8, 3, 1)
    forecast_steps = advanced_panel.slider(tr("forecast_steps"), 1, 6, 2, 1)
    confidence_level = advanced_panel.slider(tr("confidence_level"), 0.5, 2.0, 1.0, 0.1)
    simulation_hours = advanced_panel.selectbox(tr("sim_hours"), [24, 72, 168], index=0)
    primary_supply_failure_ratio = advanced_panel.number_input(tr("primary_supply_failure_ratio"), 0.0, 1.0, 0.30, 0.01, format="%.2f")
    reserve_energy_per_day = advanced_panel.number_input(tr("reserve_energy_per_day"), 20.0, 300.0, 120.0, 5.0, format="%.1f")
    survival_mode = advanced_panel.selectbox(tr("survival_mode"), ["full_load", "critical_load_only"], index=0)

    advanced_panel.markdown("**Thermal concept lab**")
    thermal_concept_enabled = advanced_panel.toggle(tr("enable_thermal"), value=True)
    fresh_air_temp_c = advanced_panel.slider(tr("outside_air") + " (°C)", -30.0, 20.0, -8.0, 0.5)
    exhaust_air_temp_c = advanced_panel.slider(tr("indoor_exhaust_air") + " (°C)", 10.0, 35.0, 23.0, 0.5)
    recovery_efficiency = advanced_panel.slider(tr("thermal_recovery_efficiency"), 0.0, 1.0, 0.72, 0.01)
    thermal_animation_speed = advanced_panel.slider(tr("animation_speed"), 0.4, 2.5, 1.0, 0.1)

    report_panel = st.expander(tr("export_report"), expanded=False)
    report_panel.caption(tr("export_help"))
    # USER-FRIENDLY UI END

# V4 Demo Mode presets: override runtime values after widgets are created,
# so manual controls remain available while demos can be activated instantly.
if demo_mode != "Manual":
    demo_presets = {
        "Taiwan Typhoon": {
            "country": "Taiwan", "city": "Taipei", "population": 2500000,
            "scenario_key": "typhoon", "temperature": 29, "wind_speed": 18.0,
            "solar_radiation": 180, "precipitation": 160, "humidity": 92,
            "solar_failure_ratio": 0.25, "wind_failure_ratio": 0.18, "hydro_failure_ratio": 0.12, "battery_failure_ratio": 0.08,
            "enable_geopolitical_shock": False,
        },
        "Finland Blizzard": {
            "country": "Finland", "city": "Helsinki", "population": 664000,
            "scenario_key": "blizzard", "temperature": -12, "wind_speed": 14.0,
            "solar_radiation": 90, "precipitation": 80, "humidity": 84,
            "solar_failure_ratio": 0.35, "wind_failure_ratio": 0.16, "hydro_failure_ratio": 0.08, "battery_failure_ratio": 0.10,
            "enable_geopolitical_shock": False,
        },
        "Germany Energy Security": {
            "country": "Germany", "city": "Berlin", "population": 3570000,
            "scenario_key": "cold_wave", "temperature": 1, "wind_speed": 5.5,
            "solar_radiation": 220, "precipitation": 28, "humidity": 78,
            "import_dependency": 0.62, "shipping_dependency": 0.55, "infrastructure_damage_ratio": 0.12,
            "reserve_recovery_lag_days": 7, "enable_geopolitical_shock": False,
        },
        "Middle East Shock": {
            "country": active_country, "city": active_city, "population": population,
            "scenario_key": scenario_key, "import_dependency": max(import_dependency, 0.78),
            "shipping_dependency": max(shipping_dependency, 0.90), "infrastructure_damage_ratio": max(infrastructure_damage_ratio, 0.18),
            "reserve_recovery_lag_days": max(reserve_recovery_lag_days, 10),
            "enable_geopolitical_shock": True, "geopolitical_event_type": "Hormuz disruption",
            "geopolitical_severity": 4, "geopolitical_duration_days": 21, "fossil_share": max(fossil_share, 0.55),
        },
    }
    preset = demo_presets.get(demo_mode, {})
    active_country = preset.get("country", active_country)
    active_city = preset.get("city", active_city)
    population = int(preset.get("population", population))
    scenario_key = preset.get("scenario_key", scenario_key)
    temperature = preset.get("temperature", temperature)
    wind_speed = preset.get("wind_speed", wind_speed)
    solar_radiation = preset.get("solar_radiation", solar_radiation)
    precipitation = preset.get("precipitation", precipitation)
    humidity = preset.get("humidity", humidity)
    solar_failure_ratio = preset.get("solar_failure_ratio", solar_failure_ratio)
    wind_failure_ratio = preset.get("wind_failure_ratio", wind_failure_ratio)
    hydro_failure_ratio = preset.get("hydro_failure_ratio", hydro_failure_ratio)
    battery_failure_ratio = preset.get("battery_failure_ratio", battery_failure_ratio)
    import_dependency = preset.get("import_dependency", import_dependency)
    shipping_dependency = preset.get("shipping_dependency", shipping_dependency)
    infrastructure_damage_ratio = preset.get("infrastructure_damage_ratio", infrastructure_damage_ratio)
    reserve_recovery_lag_days = preset.get("reserve_recovery_lag_days", reserve_recovery_lag_days)
    enable_geopolitical_shock = preset.get("enable_geopolitical_shock", enable_geopolitical_shock)
    geopolitical_event_type = preset.get("geopolitical_event_type", geopolitical_event_type)
    geopolitical_severity = preset.get("geopolitical_severity", geopolitical_severity)
    geopolitical_duration_days = preset.get("geopolitical_duration_days", geopolitical_duration_days)
    fossil_share = preset.get("fossil_share", fossil_share)

failure_ratios = {
    "solar": solar_failure_ratio,
    "wind": wind_failure_ratio,
    "geothermal": geothermal_failure_ratio,
    "hydro": hydro_failure_ratio,
    "battery": battery_failure_ratio,
}
inputs = {
    "country_key": active_country, "city_key": active_city, "lat": active_lat, "lon": active_lon,
    "temperature": temperature, "wind_speed": wind_speed, "solar_radiation": solar_radiation,
    "precipitation": precipitation, "humidity": humidity, "population": population,
    "facility_type": facility_type,
    "solar_capacity": solar_capacity, "wind_capacity": wind_capacity,
    "geothermal_capacity": geothermal_capacity, "hydro_capacity": hydro_capacity,
    "battery_capacity": battery_capacity,
}
critical_load_share = facility_profile["critical_load_share"]

results = compute_energy_supply(inputs, scenario_key, failure_ratios, reserve_recovery_lag_days)
results, _ = apply_energy_security_layer(
    base_results=results,
    scenario_key=energy_security_scenario,
    import_dependency=import_dependency,
    strategic_reserve_days=strategic_reserve_days,
    critical_load_share=critical_load_share,
    shipping_dependency=shipping_dependency,
    infrastructure_damage_ratio=infrastructure_damage_ratio,
    reserve_recovery_lag_days=reserve_recovery_lag_days,
)
results = apply_extended_security(results, 0.2, 0.8, 7, 0.25, 0.2)

geopolitical_shock = calculate_geopolitical_shock(
    event_type=geopolitical_event_type if enable_geopolitical_shock else "None",
    severity=geopolitical_severity if enable_geopolitical_shock else 0,
    duration_days=geopolitical_duration_days if enable_geopolitical_shock else 0,
    import_dependency=import_dependency,
    fossil_share=fossil_share,
    shipping_dependency=shipping_dependency,
)
results = apply_geopolitical_shock_to_results(results, geopolitical_shock)

timeline_results = simulate_survival_timeline(
    demand=results["demand"],
    renewable_supply=results["renewable_supply"],
    battery_capacity=inputs["battery_capacity"] * (1 - battery_failure_ratio),
    strategic_reserve_days=strategic_reserve_days,
    critical_load_share=critical_load_share,
    weather_scenario=scenario_key,
    simulation_hours=simulation_hours,
    primary_supply_failure_ratio=primary_supply_failure_ratio,
    reserve_energy_per_day=reserve_energy_per_day,
    survival_mode=survival_mode,
)

baseline_results = compute_energy_supply(inputs, "normal", failure_ratios={k: 0.0 for k in failure_ratios}, reserve_recovery_lag_days=0)
baseline_results, _ = apply_energy_security_layer(
    base_results=baseline_results,
    scenario_key="normal",
    import_dependency=import_dependency,
    strategic_reserve_days=strategic_reserve_days,
    critical_load_share=critical_load_share,
    shipping_dependency=shipping_dependency,
    infrastructure_damage_ratio=0.0,
    reserve_recovery_lag_days=0.0,
)

reference_avg = compute_reference_average(inputs, uploaded_df, active_country, active_city)
energy_contribution_df = build_energy_contribution_df(results, baseline_results, reference_avg)
trend_estimate_df, multistep_forecast_df, trend_meta = compute_trend_estimates(inputs, uploaded_df, active_country, active_city, baseline_results, scenario_key=scenario_key, rolling_window_rows=rolling_window_rows, forecast_steps=forecast_steps, confidence_level=confidence_level)

# UI-ONLY CHANGE START
# Plain-language emergency summary only. Uses existing calculated outputs without changing formulas or data flow.
def main_emergency_concern():
    battery_ratio = safe_div(results["battery_levels"], inputs["battery_capacity"]) if inputs["battery_capacity"] > 0 else 1.0
    if results["shortfall"] > 0:
        return "Energy Gap"
    if battery_ratio < 0.30:
        return "Battery Reserve"
    if results["grid_dependency"] >= 10:
        return "Backup Grid Need"
    if results["renewable_supply"] < baseline_results["renewable_supply"]:
        return "Renewable Supply"
    return "System Stability"


def plain_language_severity():
    tier = results.get("risk_tier", "")
    if tier == "Critical":
        return "critical"
    if tier == "High":
        return "high risk"
    if tier == "Elevated":
        return "stressed"
    if results["shortfall"] > 0 or results["grid_dependency"] >= 10:
        return "stressed"
    return "stable"


def render_plain_language_emergency_summary():
    # Decision Support Layer: plain-language operational interpretation.
    concern = main_emergency_concern()
    severity = plain_language_severity()
    scenario_label = scenario_key.replace("_", " ").title()
    st.markdown(
        f"""
        <div class="emergency-summary">
          <h3>Plain-Language Emergency Summary</h3>
          <div class="emergency-grid">
            <div class="emergency-item">
              <div class="emergency-label">Current situation</div>
              <div class="emergency-text">{active_city}, {active_country} under the {scenario_label} scenario.</div>
            </div>
            <div class="emergency-item">
              <div class="emergency-label">Main risk</div>
              <div class="emergency-text">{concern} is the main item to watch in this simulation.</div>
            </div>
            <div class="emergency-item">
              <div class="emergency-label">Expected impact</div>
              <div class="emergency-text">The system appears {severity} based on current simulation outputs.</div>
            </div>
            <div class="emergency-item">
              <div class="emergency-label">First check</div>
              <div class="emergency-text">Review battery reserve, energy gap, and backup grid need first.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def public_risk_message():
    severity = plain_language_severity()
    concern = main_emergency_concern()
    if severity in ("critical", "high risk"):
        return "Energy demand may increase under this scenario. Please reduce non-essential electricity use and follow official updates."
    if severity == "stressed":
        return "Energy conditions require monitoring. Please conserve electricity where possible and follow official updates."
    return "Energy conditions appear stable in this simulation. Continue normal use and follow official updates."


def decision_brief_message():
    concern = main_emergency_concern()
    gap = results["shortfall"]
    grid_need = results["grid_dependency"]
    return (
        f"The simulation indicates {concern.lower()} as the first communication priority. "
        f"Current modeled energy gap is {gap:.2f} MW and backup grid need is {grid_need:.2f}%. "
        "Review battery reserve, energy gap, and backup grid support before issuing operational guidance."
    )


def render_public_risk_communication_summary():
    # Decision Support Layer: public and official communication summary.
    technical_basis = pd.DataFrame([
        {"Metric": "Energy Gap", "Value": f"{results['shortfall']} MW"},
        {"Metric": "Battery Stability", "Value": f"{results['battery_levels']} MWh"},
        {"Metric": "Backup Grid Need", "Value": f"{results['grid_dependency']}%"},
        {"Metric": "Renewable Share", "Value": f"{results['renewable_ratio']}%"},
        {"Metric": "System Stability", "Value": f"{results['system_efficiency']}%"},
        {"Metric": "Risk Tier", "Value": results.get("risk_tier", plain_language_severity().title())},
    ])
    st.markdown(
        f"""
        <div class="communication-summary">
          <h3>Public Risk Communication Summary</h3>
          <div class="communication-grid">
            <div class="communication-card">
              <div class="communication-label">Public Message</div>
              <div class="communication-text">{public_risk_message()}</div>
            </div>
            <div class="communication-card">
              <div class="communication-label">Decision Brief</div>
              <div class="communication-text">{decision_brief_message()}</div>
            </div>
          </div>
          <div class="communication-disclaimer">This summary is scenario-based decision-support information and not a confirmed prediction.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Technical Basis", expanded=False):
        st.dataframe(technical_basis, use_container_width=True, hide_index=True)
# UI-ONLY CHANGE END

# PRODUCT UI RESTRUCTURE START
# Product positioning only. Detailed results are rendered later inside tabs to reduce page length.
# UI REFINEMENT START
st.markdown(
    """
    <div class="taivas-brand">
      <div class="taivas-brand-title">TAIVAS</div>
      <div class="taivas-brand-subtitle">Climate &amp; Energy Resilience Platform</div>
      <div class="taivas-brand-kicker">Decision-Support Simulation Environment</div>
      <div class="command-meta">
        <span class="command-chip">Scenario-based</span>
        <span class="command-chip">Decision support</span>
        <span class="command-chip">Simulation integrity preserved</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
# UI REFINEMENT END
st.markdown(f'<div class="quick-start"><b>{tr("quick_start")}</b>{tr("quick_start_body")}</div>', unsafe_allow_html=True)
# UI-ONLY CHANGE START
render_plain_language_emergency_summary()
render_public_risk_communication_summary()
# UI-ONLY CHANGE END
# PRODUCT UI RESTRUCTURE END

def build_executive_summary_text():
    lines = [
        "TAIVAS Executive Summary",
        "========================",
        f"Demo Mode: {demo_mode}",
        f"Location: {active_city}, {active_country}",
        f"Facility: {facility_type}",
        f"Weather Scenario: {scenario_key}",
        f"Energy Security Scenario: {energy_security_scenario}",
        "",
        "Core Metrics",
        f"- Demand: {results['demand']} MW",
        f"- Renewable Supply: {results['renewable_supply']} MW",
        f"- Final Supply: {results['final_supply']} MW",
        f"- Shortfall: {results['shortfall']} MW",
        f"- Battery Remaining: {results['battery_levels']} MWh",
        f"- System Efficiency: {results['system_efficiency']}%",
        f"- Grid Dependency: {results['grid_dependency']}%",
        "",
        "Risk Notes",
        f"- Geopolitical Risk Level: {geopolitical_shock.get('risk_level', 'N/A')}",
        f"- Oil/Gas Supply Disruption: {geopolitical_shock.get('oil_supply_disruption_percent', 0)}%",
        f"- Estimated Hours Until Shortfall: {timeline_results.get('hours_until_shortfall')}",
        f"- Estimated Hours Until Critical Failure: {timeline_results.get('hours_until_critical_failure')}",
        "",
        "Model Limitation",
        "TAIVAS is a decision-support simulator. It does not guarantee real-world outcomes and does not replace engineering, grid-operator, legal, security, or emergency-management validation.",
    ]
    return "\n".join(lines)


def render_product_notice():
    st.markdown(
        """
        <div class="notice-box">
        <b>Decision-support notice:</b> TAIVAS converts scenario assumptions into operational risk signals.
        It is not a disaster prediction engine, not a guarantee of physical system behavior, and not a substitute for professional engineering validation.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_executive_overview_workspace():
    if demo_mode != "Manual":
        st.markdown(f"<span class='demo-pill'>Demo Mode: {demo_mode}</span>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="product-strip">
          <div class="product-card"><div class="product-label">Location</div><div class="product-value">{active_city}</div><div class="product-sub">{active_country}</div></div>
          <div class="product-card"><div class="product-label">Scenario</div><div class="product-value">{scenario_key.replace('_',' ').title()}</div><div class="product-sub">{energy_security_scenario.replace('_',' ').title()}</div></div>
          <div class="product-card"><div class="product-label">Shortfall</div><div class="product-value">{results['shortfall']} MW</div><div class="product-sub">Grid dependency {results['grid_dependency']}%</div></div>
          <div class="product-card"><div class="product-label">Recommendation Focus</div><div class="product-value">{build_status_label(results['shortfall'], (5, 15)).title()}</div><div class="product-sub">Protect critical load first</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_product_notice()
    st.subheader("Executive Recommendation")
    for idx, line in enumerate(recommendation_lines(results, energy_security_scenario)[:3], 1):
        st.write(f"{idx}. {line}")


summary_txt = build_executive_summary_text()
buf_scen = StringIO(); comparison_dataframe(inputs, failure_ratios, reserve_recovery_lag_days).to_csv(buf_scen, index=False)
buf_reason = StringIO(); pd.DataFrame(recommendation_reason_chain(results, energy_security_scenario, timeline_results, facility_type, facility_profile)).to_csv(buf_reason, index=False)
audit_json = json.dumps({
    "version": "V4 Product Polish",
    "demo_mode": demo_mode,
    "country": active_country,
    "city": active_city,
    "facility_type": facility_type,
    "scenario_key": scenario_key,
    "results": results,
    "timeline": timeline_results,
    "geopolitical_shock": geopolitical_shock,
    "model_limitation": "Decision-support simulation only; not a prediction or guarantee.",
}, indent=2, ensure_ascii=False)

def render_export_center():
    with st.expander("Export Center", expanded=False):
        st.caption("Download scenario data, reason chain, executive summary, or audit trail when needed.")
        download_cols = st.columns(4)
        with download_cols[0]:
            st.download_button(tr("download_scenario"), buf_scen.getvalue(), file_name="taivas_scenarios.csv", mime="text/csv")
        with download_cols[1]:
            st.download_button(tr("download_reason"), buf_reason.getvalue(), file_name="taivas_reason_chain.csv", mime="text/csv")
        with download_cols[2]:
            st.download_button(tr("download_summary"), summary_txt, file_name="taivas_executive_summary.txt", mime="text/plain")
        with download_cols[3]:
            st.download_button(tr("download_audit"), audit_json, file_name="taivas_audit_trail.json", mime="application/json")

# UI IMPROVEMENT START
# Donut chart UI renderer only: fixed source colors and external legend prevent label overlap.
def render_stable_donut_chart(mix_pct, center_value, title):
    # UI-only chart renderer: fixed source colors and external legend prevent label overlap.
    source_colors = {
        "Solar": "#FBBF24",
        "Wind": "#38BDF8",
        "Geothermal": "#A78BFA",
        "Hydro": "#22C55E",
    }
    labels = list(mix_pct.keys())
    values = [max(float(mix_pct.get(label, 0.0)), 0.0) for label in labels]
    colors = [source_colors.get(label, "#94A3B8") for label in labels]
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    if sum(values) <= 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=13, color="#E5E7EB")
        ax.axis("off")
    else:
        wedges, _ = ax.pie(
            values,
            labels=None,
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops={"width": 0.34, "edgecolor": "#0F172A", "linewidth": 1.2},
        )
        legend_labels = [f"{label}: {value:.1f}%" for label, value in zip(labels, values)]
        ax.legend(
            wedges,
            legend_labels,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=11,
            labelcolor="#E5E7EB",
            borderaxespad=0.0,
        )
        ax.text(0, 0.05, f"{center_value:.1f}%", ha="center", va="center", fontsize=18, fontweight="bold", color="#F8FAFC")
        ax.text(0, -0.15, "ratio", ha="center", va="center", fontsize=10, color="#A7B3C7")
        ax.set_title(title, fontsize=14, pad=16, color="#F8FAFC")
        ax.set_aspect("equal")
    plt.tight_layout(pad=1.6)
    st.pyplot(fig, clear_figure=True)
# UI IMPROVEMENT END

def render_energy_mix_workspace():
    # Energy System Layer: renewable supply composition and contribution context.
    page_question(tr("tabs")[0])
    st.markdown(f'<div class="note">{tr("mix_note")}</div>', unsafe_allow_html=True)
    mix_cols = st.columns(2)
    with mix_cols[0]:
        st.subheader(tr("installed_mix"))
        render_stable_donut_chart(results["installed_mix_pct"], 100.0, tr("installed_mix"))
    with mix_cols[1]:
        st.subheader(tr("actual_mix"))
        render_stable_donut_chart(results["actual_mix_pct"], results["renewable_ratio"], tr("actual_mix"))
    mix_table = pd.DataFrame({
        tr("source"): list(results["actual_mix_mw"].keys()),
        tr("installed_capacity_mw"): [results["installed_mix_mw"][k] for k in results["actual_mix_mw"]],
        tr("actual_supply_mw"): [results["actual_mix_mw"][k] for k in results["actual_mix_mw"]],
        tr("installed_mix_pct"): [round(results["installed_mix_pct"][k], 2) for k in results["actual_mix_mw"]],
        tr("actual_mix_pct"): [round(results["actual_mix_pct"][k], 2) for k in results["actual_mix_mw"]],
        tr("capacity_factor_pct"): [results["capacity_factors"][k] for k in results["actual_mix_mw"]],
    })
    render_energy_contribution_panel(energy_contribution_df)
    render_reserve_outlook_panel(reference_avg, results, timeline_results)
    render_trend_estimate_panel(trend_estimate_df, multistep_forecast_df, trend_meta)
    st.subheader(tr("energy_table"))
    st.dataframe(mix_table, use_container_width=True, hide_index=True)
    st.caption(f"{tr('dominant')}: {results['dominant_source']}")


# UI-ONLY CHANGE START
# Scenario comparison presentation helpers only. They read existing result dictionaries without modifying calculations.
def display_delta(current_value, baseline_value, unit="", invert=False):
    delta = current_value - baseline_value
    pct = safe_div(delta, abs(baseline_value)) * 100 if baseline_value not in (0, 0.0) else 0.0
    if abs(delta) < 0.005:
        return '<span class="comparison-delta delta-flat">0.0%</span>'
    arrow = "↑" if delta > 0 else "↓"
    class_name = "delta-down" if invert and delta < 0 else "delta-up" if delta > 0 else "delta-down"
    if invert and delta > 0:
        class_name = "delta-up"
    return f'<span class="comparison-delta {class_name}">{arrow} {pct:+.1f}%</span>'


def format_metric_value(value, unit=""):
    suffix = f" {unit}" if unit else ""
    return f"{value:.2f}{suffix}"


def scenario_comparison_metrics():
    return [
        ("Demand", baseline_results["demand"], results["demand"], "MW", True),
        ("Renewable Supply", baseline_results["renewable_supply"], results["renewable_supply"], "MW", False),
        ("Final Supply", baseline_results["final_supply"], results["final_supply"], "MW", False),
        ("Energy Gap", baseline_results["shortfall"], results["shortfall"], "MW", True),
        ("Battery Stability", baseline_results["battery_levels"], results["battery_levels"], "MWh", False),
        ("Renewable Share", baseline_results["renewable_ratio"], results["renewable_ratio"], "%", False),
        ("Backup Grid Need", baseline_results["grid_dependency"], results["grid_dependency"], "%", True),
        ("System Stability", baseline_results["system_efficiency"], results["system_efficiency"], "%", False),
    ]


def operational_risk_tier_for_display():
    ratio = safe_div(results["shortfall"], results["demand"]) if results["demand"] > 0 else 0.0
    if results["shortfall"] <= 0:
        return "Low", "risk-low", "No modeled energy gap under the selected scenario."
    if ratio < 0.05:
        return "Moderate", "risk-moderate", "Small energy gap detected; monitor reserve margin."
    if ratio < 0.15:
        return "High", "risk-high", "Supply stress is material; prioritize critical load protection."
    return "Critical", "risk-critical", "Large energy gap detected; immediate resilience action is recommended."


def render_risk_tier_panel():
    tier, class_name, note = operational_risk_tier_for_display()
    st.markdown(
        f"""
        <div class="risk-strip">
          <div>
            <div class="risk-title">Operational Risk Tier</div>
            <div class="risk-note">{note}</div>
          </div>
          <div class="risk-badge {class_name}">{tier}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_baseline_extreme_cards():
    metrics = scenario_comparison_metrics()
    baseline_rows = []
    selected_rows = []
    for label, base_value, selected_value, unit, invert in metrics:
        baseline_rows.append(
            f'<div class="comparison-row">'
            f'<div class="comparison-label">{label}</div>'
            f'<div class="comparison-value">{format_metric_value(base_value, unit)}</div>'
            f'<div class="comparison-delta delta-flat">baseline</div>'
            f'</div>'
        )
        selected_rows.append(
            f'<div class="comparison-row">'
            f'<div class="comparison-label">{label}</div>'
            f'<div class="comparison-value">{format_metric_value(selected_value, unit)}</div>'
            f'<div>{display_delta(selected_value, base_value, unit, invert)}</div>'
            f'</div>'
        )
    selected_title = scenario_key.replace("_", " ").title()
    comparison_html = (
        '<div class="comparison-grid">'
        '<div class="scenario-card"><h4>Baseline Scenario</h4>'
        + "".join(baseline_rows)
        + '</div>'
        + f'<div class="scenario-card"><h4>Selected Scenario: {selected_title}</h4>'
        + "".join(selected_rows)
        + '</div></div>'
    )
    st.markdown(comparison_html, unsafe_allow_html=True)


def render_resilience_storytelling():
    renewable_delta_pct = safe_div(results["renewable_supply"] - baseline_results["renewable_supply"], abs(baseline_results["renewable_supply"])) * 100 if baseline_results["renewable_supply"] else 0.0
    grid_delta_pct = results["grid_dependency"] - baseline_results["grid_dependency"]
    gap_delta = results["shortfall"] - baseline_results["shortfall"]
    st.markdown(
        f"""
        <div class="note">
        Under the selected <b>{scenario_key.replace("_", " ").title()}</b> scenario,
        renewable output changes by <b>{renewable_delta_pct:+.1f}%</b>,
        backup grid need changes by <b>{grid_delta_pct:+.1f} percentage points</b>,
        and the modeled energy gap changes by <b>{gap_delta:+.2f} MW</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_system_explanation_panel():
    explanations = []
    if results["demand"] > baseline_results["demand"]:
        explanations.append("Demand is higher than baseline, indicating stronger load pressure from the selected scenario and facility profile.")
    else:
        explanations.append("Demand remains at or below baseline, so load pressure is not the main source of stress.")
    if results["renewable_supply"] < baseline_results["renewable_supply"]:
        explanations.append("Renewable supply is lower than baseline, reducing the amount of local energy available before storage or backup support.")
    else:
        explanations.append("Renewable supply is holding at or above baseline, supporting system resilience.")
    if results["battery_levels"] < baseline_results["battery_levels"]:
        explanations.append("Battery reserve is lower than baseline, which can shorten operating time during sustained disruption.")
    else:
        explanations.append("Battery reserve remains available, preserving a useful buffer against short-term supply stress.")
    if results["grid_dependency"] > baseline_results["grid_dependency"]:
        explanations.append("Backup grid need has increased, meaning the selected scenario places more pressure on external support.")
    else:
        explanations.append("Backup grid need has not increased, suggesting the modeled local supply stack remains sufficient.")
    st.subheader("System Explanation")
    st.markdown(
        '<div class="explain-grid">' + "".join(f'<div class="explain-card">{line}</div>' for line in explanations) + "</div>",
        unsafe_allow_html=True,
    )
# UI-ONLY CHANGE END


def render_scenario_comparison_workspace():
    # Situation Awareness Layer: baseline-vs-selected scenario resilience comparison.
    page_question(tr("tabs")[1])
    delta_df = scenario_delta_df(baseline_results, results)
    scenario_df = comparison_dataframe(inputs, failure_ratios, reserve_recovery_lag_days)
    critical_load_df = critical_load_breakdown(results["demand"], facility_profile["critical_load_share"], facility_profile["critical_split"])
    # UI-ONLY CHANGE START
    st.subheader("Baseline vs Selected Scenario")
    render_risk_tier_panel()
    render_resilience_storytelling()
    render_baseline_extreme_cards()
    render_system_explanation_panel()
    with st.expander("Detailed Technical Comparison", expanded=False):
        left, right = st.columns([1.02, 1.0])
        with left:
            st.subheader(tr("baseline_vs_selected"))
            st.dataframe(delta_df, use_container_width=True, hide_index=True)
            render_delta_chart(delta_df)
        with right:
            st.subheader(tr("all_scenarios"))
            st.dataframe(scenario_df, use_container_width=True, hide_index=True)
            scenario_index_col = tr("scenario") if tr("scenario") in scenario_df.columns else "Scenario"
            shortfall_col = tr("shortfall") if tr("shortfall") in scenario_df.columns else "Shortfall"
            grid_col = tr("grid") if tr("grid") in scenario_df.columns else "Grid Dependency"
            st.bar_chart(scenario_df.set_index(scenario_index_col)[[shortfall_col, grid_col]])
        st.subheader(tr("critical_breakdown"))
        render_critical_load_chart(critical_load_df)
        st.dataframe(critical_load_df, use_container_width=True, hide_index=True)
    # UI-ONLY CHANGE END


def render_stress_test_workspace():
    page_question(tr("tabs")[2])
    st.markdown('<div class="note">Multi-failure stress testing and subsystem degradation view.</div>', unsafe_allow_html=True)
    stress_df = pd.DataFrame({tr("subsystem"): list(failure_ratios.keys()), tr("failure_ratio"): list(failure_ratios.values()), tr("availability_pct"): [round((1 - v) * 100, 1) for v in failure_ratios.values()]})
    st.dataframe(stress_df, use_container_width=True, hide_index=True)
    st.bar_chart(stress_df.set_index(tr("subsystem"))[[tr("availability_pct")]])


def render_ai_recommendation_workspace():
    page_question(tr("tabs")[3])
    st.subheader(tr("quick_reco"))
    for idx, line in enumerate(recommendation_lines(results, energy_security_scenario), 1):
        st.write(f"{idx}. {line}")
    reason_df = pd.DataFrame(recommendation_reason_chain(results, energy_security_scenario, timeline_results, facility_type, facility_profile))
    st.subheader(tr("reason_chain"))
    st.dataframe(reason_df, use_container_width=True, hide_index=True)


def render_energy_security_workspace():
    page_question(tr("tabs")[4])
    row1 = st.columns(4)
    row1[0].metric("Import Disruption", f"{results['import_disruption_score']}%")
    row1[1].metric(tr("reserve_days"), f"{results['reserve_days_remaining']} days")
    row1[2].metric("Fuel Cost Stress", f"{results['fuel_cost_stress']}%")
    row1[3].metric("Extended Disruption", f"{results['extended_disruption_score']}%")

    st.subheader(tr("geopolitical_panel"))
    st.markdown(f'<div class="note">{tr("geopolitical_model_note")}</div>', unsafe_allow_html=True)
    geo_cols = st.columns(4)
    geo_cols[0].metric(tr("oil_supply_disruption"), f"{geopolitical_shock['oil_supply_disruption_percent']}%")
    geo_cols[1].metric(tr("price_spike_index"), geopolitical_shock["price_spike_index"])
    geo_cols[2].metric(tr("geopolitical_grid_stress"), geopolitical_shock["grid_stress_index"])
    geo_cols[3].metric(tr("geopolitical_risk_level"), geopolitical_shock["risk_level"])
    st.caption(geopolitical_shock.get("event_note", ""))
    st.subheader(tr("geopolitical_reason_chain"))
    st.dataframe(build_geopolitical_reason_chain(geopolitical_shock, results), use_container_width=True, hide_index=True)


def render_survival_timeline_workspace():
    page_question(tr("tabs")[5])
    t1, t2, t3 = st.columns(3)
    t1.metric(tr("shortfall_hour"), timeline_results["hours_until_shortfall"])
    t2.metric(tr("critical_failure_hour"), timeline_results["hours_until_critical_failure"])
    t3.metric("Survival Mode", timeline_results["survival_mode_duration"])
    timeline_df = pd.DataFrame(timeline_results["rows"])
    if not timeline_df.empty:
        chart_cols = [c for c in ["raw_demand", "target_demand", "renewable_supply", "battery_used", "reserve_used", "final_supply", "shortfall", "battery_level", "reserve_energy"] if c in timeline_df.columns]
        if chart_cols:
            st.subheader(tr("timeline_chart"))
            st.line_chart(timeline_df[chart_cols])
    st.subheader(tr("timeline_table"))
    st.dataframe(timeline_df, use_container_width=True, hide_index=True)


def render_visual_simulator_workspace():
    # Situation Awareness Layer: visual crisis-monitoring scenario display.
    page_question(tr("tabs")[6])
    st.subheader(tr("visual_simulator"))
    render_visual_scenario_layer(results, baseline_results, geopolitical_shock)


# UI-ONLY CHANGE START
# Presentation-only override for the Concept Lab thermal panel.
# It preserves the same inputs and conceptual outputs while changing the interface
# from equipment-centric to system-flow-centric.
def render_thermal_principle_simulation(
    fresh_air_temp_c=-8.0,
    exhaust_air_temp_c=23.0,
    recovery_efficiency=0.72,
    airflow_speed=1.0,
    height=820,
):
    # Infrastructure Resilience Layer: thermal stabilization subsystem presentation.
    from textwrap import dedent

    efficiency_pct = round(clamp(float(recovery_efficiency), 0.0, 1.0) * 100)
    delta_c = float(exhaust_air_temp_c) - float(fresh_air_temp_c)
    delivered_supply_c = float(fresh_air_temp_c) + delta_c * float(recovery_efficiency)
    exhaust_after_c = float(exhaust_air_temp_c) - delta_c * float(recovery_efficiency)
    heating_relief_pct = round(clamp(float(recovery_efficiency) * 0.82, 0.0, 1.0) * 100)
    flow_speed = round(float(airflow_speed), 2)
    flow_duration = max(4.2, 7.0 / max(flow_speed, 0.4))

    thermal_panel_html = dedent(f"""
        <style>
        .thermal-layer-shell {{
            border: 1px solid rgba(56,189,248,0.22);
            border-radius: 14px;
            background:
                linear-gradient(145deg, rgba(15,23,42,0.86), rgba(8,47,73,0.22)),
                radial-gradient(circle at 74% 18%, rgba(56,189,248,0.10), transparent 26%);
            padding: 1.05rem;
            min-height: {max(int(height) - 120, 560)}px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 18px 48px rgba(0,0,0,0.20);
        }}
        .thermal-layer-header {{
            display:flex;
            align-items:flex-start;
            justify-content:space-between;
            gap:1rem;
            margin-bottom:1rem;
        }}
        .thermal-kicker {{
            color:rgba(125,211,252,0.78);
            font-size:.76rem;
            font-weight:850;
            letter-spacing:.10em;
            text-transform:uppercase;
            margin-bottom:.35rem;
        }}
        .thermal-title {{
            color:#F8FAFC;
            font-size:clamp(1.35rem, 1.8vw, 2rem);
            line-height:1.12;
            font-weight:900;
            margin:0;
        }}
        .thermal-subtitle {{
            color:#A7B3C7;
            margin-top:.45rem;
            max-width:720px;
            line-height:1.48;
            font-size:.95rem;
        }}
        .thermal-status-pill {{
            white-space:nowrap;
            padding:.42rem .68rem;
            border-radius:999px;
            border:1px solid rgba(34,197,94,0.34);
            background:rgba(34,197,94,0.12);
            color:#86EFAC;
            font-size:.78rem;
            font-weight:850;
        }}
        .thermal-grid {{
            display:grid;
            grid-template-columns:minmax(0, 1.85fr) minmax(280px, .85fr);
            gap:1rem;
            align-items:stretch;
        }}
        .thermal-flow-panel, .thermal-side-panel {{
            border:1px solid rgba(148,163,184,0.22);
            border-radius:14px;
            background:rgba(8,13,28,0.56);
            padding:1rem;
        }}
        .thermal-flow-map {{
            position:relative;
            min-height:390px;
            overflow:hidden;
            border-radius:12px;
            background:
                radial-gradient(circle at 16% 48%, rgba(56,189,248,0.18), transparent 26%),
                radial-gradient(circle at 72% 48%, rgba(251,191,36,0.16), transparent 28%),
                linear-gradient(90deg, rgba(8,47,73,0.34), rgba(15,23,42,0.72), rgba(69,26,3,0.22));
            border:1px solid rgba(56,189,248,0.14);
        }}
        .thermal-flow-map::before {{
            content:"";
            position:absolute;
            inset:0;
            background-image:
                linear-gradient(rgba(148,163,184,0.055) 1px, transparent 1px),
                linear-gradient(90deg, rgba(148,163,184,0.055) 1px, transparent 1px);
            background-size:42px 42px;
            opacity:.7;
        }}
        .thermal-zone {{
            position:absolute;
            top:46px;
            bottom:46px;
            width:28%;
            border-radius:18px;
            border:1px solid rgba(148,163,184,0.16);
            display:flex;
            flex-direction:column;
            justify-content:flex-end;
            padding:1rem;
            color:#E5E7EB;
        }}
        .thermal-zone.cold {{left:4%; background:linear-gradient(180deg, rgba(14,165,233,0.18), rgba(8,47,73,0.20));}}
        .thermal-zone.protected {{right:4%; background:linear-gradient(180deg, rgba(251,191,36,0.16), rgba(69,26,3,0.22));}}
        .thermal-zone-label {{font-size:.82rem; color:#A7B3C7; font-weight:800; text-transform:uppercase; letter-spacing:.05em;}}
        .thermal-zone-value {{font-size:1.55rem; font-weight:900; margin-top:.25rem;}}
        .thermal-exchange-core {{
            position:absolute;
            left:calc(50% - 82px);
            top:calc(50% - 82px);
            width:164px;
            height:164px;
            border-radius:50%;
            border:1px solid rgba(125,211,252,0.32);
            background:
                radial-gradient(circle, rgba(253,224,71,0.34), rgba(56,189,248,0.13) 48%, rgba(15,23,42,0.40) 72%);
            box-shadow:0 0 44px rgba(56,189,248,0.12), inset 0 0 28px rgba(251,191,36,0.12);
        }}
        .thermal-exchange-core::before {{
            content:"";
            position:absolute;
            inset:22px;
            border-radius:50%;
            border:1px dashed rgba(226,232,240,0.24);
            animation:typhoon-spin 16s linear infinite;
        }}
        .thermal-exchange-core::after {{
            content:"{efficiency_pct}%";
            position:absolute;
            inset:0;
            display:grid;
            place-items:center;
            color:#FDE68A;
            font-size:1.45rem;
            font-weight:950;
        }}
        .thermal-flow-line {{
            position:absolute;
            left:8%;
            right:8%;
            height:18px;
            border-radius:999px;
            overflow:hidden;
            background:rgba(15,23,42,0.62);
            border:1px solid rgba(148,163,184,0.16);
        }}
        .thermal-flow-line.intake {{top:38%;}}
        .thermal-flow-line.supply {{top:57%;}}
        .thermal-flow-line.exhaust {{top:47%; opacity:.70;}}
        .thermal-flow-line.intake::before,
        .thermal-flow-line.supply::before,
        .thermal-flow-line.exhaust::before {{
            content:"";
            position:absolute;
            inset:0;
            width:42%;
            border-radius:999px;
            animation:thermal-flow {flow_duration}s linear infinite;
        }}
        .thermal-flow-line.intake::before {{background:linear-gradient(90deg, transparent, rgba(56,189,248,0.92), transparent);}}
        .thermal-flow-line.supply::before {{background:linear-gradient(90deg, transparent, rgba(251,191,36,0.88), transparent); animation-delay:1.1s;}}
        .thermal-flow-line.exhaust::before {{background:linear-gradient(90deg, transparent, rgba(248,113,113,0.76), transparent); animation-delay:2.0s;}}
        .thermal-transfer-arrow {{
            position:absolute;
            left:calc(50% - 125px);
            top:calc(50% - 1px);
            width:250px;
            height:2px;
            background:linear-gradient(90deg, rgba(56,189,248,0.18), rgba(253,224,71,0.72), rgba(248,113,113,0.18));
            transform:rotate(-28deg);
            opacity:.78;
        }}
        .thermal-transfer-arrow.a2 {{transform:rotate(28deg); opacity:.52;}}
        .thermal-map-caption {{
            position:absolute;
            left:1rem;
            top:1rem;
            padding:.45rem .6rem;
            border-radius:999px;
            background:rgba(15,23,42,0.66);
            border:1px solid rgba(125,211,252,0.18);
            color:#CBD5E1;
            font-size:.76rem;
            font-weight:800;
        }}
        .thermal-indicators {{
            display:grid;
            grid-template-columns:repeat(4, minmax(0, 1fr));
            gap:.7rem;
            margin-top:.8rem;
        }}
        .thermal-indicator {{
            border:1px solid rgba(148,163,184,0.18);
            border-radius:12px;
            padding:.75rem;
            background:rgba(15,23,42,0.50);
            min-height:86px;
        }}
        .thermal-indicator-label {{color:#A7B3C7; font-size:.78rem; font-weight:800; line-height:1.3;}}
        .thermal-indicator-value {{color:#F8FAFC; font-size:1.16rem; font-weight:900; margin-top:.25rem;}}
        .thermal-indicator-note {{color:#8EA0B8; font-size:.74rem; margin-top:.22rem; line-height:1.3;}}
        .thermal-side-panel h4 {{
            margin:.1rem 0 .65rem 0;
            color:#F8FAFC;
            font-size:1.04rem;
        }}
        .thermal-status-list {{
            display:grid;
            gap:.62rem;
            margin-bottom:.9rem;
        }}
        .thermal-status-row {{
            display:flex;
            justify-content:space-between;
            gap:.75rem;
            padding:.62rem .7rem;
            border-radius:10px;
            background:rgba(15,23,42,0.48);
            border:1px solid rgba(148,163,184,0.16);
            color:#D7DEE9;
            font-size:.84rem;
        }}
        .thermal-status-row b {{color:#F8FAFC;}}
        .thermal-brief {{
            border-left:3px solid rgba(56,189,248,0.70);
            padding-left:.72rem;
            color:#CBD5E1;
            line-height:1.5;
            font-size:.9rem;
            margin:.75rem 0 .9rem 0;
        }}
        .thermal-boundary {{
            padding:.72rem .78rem;
            border-radius:12px;
            background:rgba(245,158,11,0.10);
            border:1px solid rgba(245,158,11,0.24);
            color:#FDE68A;
            font-size:.82rem;
            line-height:1.45;
        }}
        @keyframes thermal-flow {{
            0% {{transform:translateX(-120%);}}
            100% {{transform:translateX(250%);}}
        }}
        @media (max-width: 980px) {{
            .thermal-grid {{grid-template-columns:1fr;}}
            .thermal-indicators {{grid-template-columns:repeat(2, minmax(0, 1fr));}}
        }}
        @media (max-width: 560px) {{
            .thermal-layer-header {{display:block;}}
            .thermal-status-pill {{display:inline-block; margin-top:.75rem;}}
            .thermal-flow-map {{min-height:330px;}}
            .thermal-zone {{display:none;}}
            .thermal-indicators {{grid-template-columns:1fr;}}
        }}
        </style>

        <div class="thermal-layer-shell">
          <div class="thermal-layer-header">
            <div>
              <div class="thermal-kicker">CONCEPT LAB // THERMAL RESILIENCE</div>
              <h2 class="thermal-title">Cold-Weather Thermal Buffer Concept</h2>
              <div class="thermal-subtitle">
                This concept shows how recovered indoor heat may reduce heating pressure during cold-weather disruption.
                It illustrates a passive thermal buffer for stabilizing protected indoor environments.
              </div>
            </div>
            <div class="thermal-status-pill">Thermal Buffer Active</div>
          </div>

          <div class="thermal-grid">
            <div class="thermal-flow-panel">
              <div class="thermal-flow-map">
                <div class="thermal-map-caption">System-flow view - conceptual simulation</div>
                <div class="thermal-zone cold">
                  <div class="thermal-zone-label">External Cold Air</div>
                  <div class="thermal-zone-value">{fresh_air_temp_c:.1f} C</div>
                </div>
                <div class="thermal-zone protected">
                  <div class="thermal-zone-label">Protected Supply Zone</div>
                  <div class="thermal-zone-value">{delivered_supply_c:.1f} C</div>
                </div>
                <div class="thermal-flow-line intake"></div>
                <div class="thermal-flow-line exhaust"></div>
                <div class="thermal-flow-line supply"></div>
                <div class="thermal-transfer-arrow"></div>
                <div class="thermal-transfer-arrow a2"></div>
                <div class="thermal-exchange-core"></div>
              </div>

              <div class="thermal-indicators">
                <div class="thermal-indicator">
                  <div class="thermal-indicator-label">Outside air</div>
                  <div class="thermal-indicator-value">{fresh_air_temp_c:.1f} C</div>
                  <div class="thermal-indicator-note">Cold-climate intake condition</div>
                </div>
                <div class="thermal-indicator">
                  <div class="thermal-indicator-label">Delivered supply</div>
                  <div class="thermal-indicator-value">{delivered_supply_c:.1f} C</div>
                  <div class="thermal-indicator-note">Stabilized air after exchange</div>
                </div>
                <div class="thermal-indicator">
                  <div class="thermal-indicator-label">Recovery efficiency</div>
                  <div class="thermal-indicator-value">{efficiency_pct}%</div>
                  <div class="thermal-indicator-note">Thermal buffer transfer level</div>
                </div>
                <div class="thermal-indicator">
                  <div class="thermal-indicator-label">Heating demand relief</div>
                  <div class="thermal-indicator-value">{heating_relief_pct}%</div>
                  <div class="thermal-indicator-note">Conceptual resilience contribution</div>
                </div>
              </div>
            </div>

            <div class="thermal-side-panel">
              <h4>Operational Meaning</h4>
              <div class="thermal-brief">
                This layer is shown as a resilience subsystem, not a hardware blueprint.
                It buffers cold intake air and helps reduce immediate heating load on protected facilities.
              </div>
              <div class="thermal-status-list">
                <div class="thermal-status-row"><span>Thermal status</span><b>Stabilizing</b></div>
                <div class="thermal-status-row"><span>Recovery efficiency</span><b>{efficiency_pct}%</b></div>
                <div class="thermal-status-row"><span>Grid load relief</span><b>{heating_relief_pct}%</b></div>
                <div class="thermal-status-row"><span>Airflow speed</span><b>{flow_speed:.2f}x</b></div>
                <div class="thermal-status-row"><span>Exhaust after exchange</span><b>{exhaust_after_c:.1f} C</b></div>
              </div>
              <div class="thermal-boundary">
                <b>Model boundary</b><br>
                Scenario-based concept visualization only. It does not represent validated hardware design,
                physical engineering performance, or guaranteed energy outcome.
              </div>
            </div>
          </div>
        </div>
        """).strip()
    thermal_panel_html = "\n".join(line.strip() for line in thermal_panel_html.splitlines() if line.strip())
    st.markdown(thermal_panel_html, unsafe_allow_html=True)
# UI-ONLY CHANGE END


# UI-ONLY CHANGE START
# Presentation-only override for Ground Thermal Sink wording and boundary clarity.
# Keeps the same visual metaphor and input bindings, but frames values as concept indicators.
def render_ground_thermal_sink_concept(
    cooling_offset_pct=4.0,
    sink_utilization_pct=60.0,
    saturation_risk_pct=20.0,
    height=720,
):
    from textwrap import dedent

    cooling_offset_pct = clamp(float(cooling_offset_pct), 0.0, 100.0)
    sink_utilization_pct = clamp(float(sink_utilization_pct), 0.0, 100.0)
    saturation_risk_pct = clamp(float(saturation_risk_pct), 0.0, 100.0)
    flow_duration = max(4.0, 9.0 - sink_utilization_pct / 14.0)

    ground_panel_html = dedent(f"""
    <style>
    .ground-buffer-shell {{
        border:1px solid rgba(56,189,248,0.22);
        border-radius:14px;
        background:linear-gradient(145deg, rgba(15,23,42,0.86), rgba(8,47,73,0.18));
        padding:1.05rem;
        min-height:{max(int(height) - 120, 520)}px;
        box-shadow:inset 0 1px 0 rgba(255,255,255,0.04), 0 18px 48px rgba(0,0,0,0.18);
    }}
    .ground-buffer-header {{
        display:flex;
        align-items:flex-start;
        justify-content:space-between;
        gap:1rem;
        margin-bottom:1rem;
    }}
    .ground-kicker {{
        color:rgba(125,211,252,0.78);
        font-size:.76rem;
        font-weight:850;
        letter-spacing:.10em;
        text-transform:uppercase;
        margin-bottom:.35rem;
    }}
    .ground-title {{
        color:#F8FAFC;
        font-size:clamp(1.35rem, 1.9vw, 2rem);
        line-height:1.12;
        font-weight:900;
        margin:0;
    }}
    .ground-subtitle {{
        color:#A7B3C7;
        margin-top:.45rem;
        max-width:760px;
        line-height:1.48;
        font-size:.95rem;
    }}
    .ground-layout {{
        display:grid;
        grid-template-columns:minmax(0, 1.8fr) minmax(280px, .85fr);
        gap:1rem;
        align-items:stretch;
    }}
    .ground-visual, .ground-side {{
        border:1px solid rgba(148,163,184,0.22);
        border-radius:14px;
        background:rgba(8,13,28,0.56);
        padding:1rem;
    }}
    .ground-map {{
        position:relative;
        min-height:390px;
        overflow:hidden;
        border-radius:12px;
        border:1px solid rgba(56,189,248,0.16);
        background:
            linear-gradient(180deg, rgba(15,23,42,0.84) 0 48%, rgba(30,41,59,0.68) 49% 62%, rgba(23,37,25,0.72) 63% 100%),
            radial-gradient(circle at 50% 76%, rgba(34,197,94,0.14), transparent 30%);
    }}
    .ground-map::before {{
        content:"";
        position:absolute;
        inset:0;
        background-image:
            linear-gradient(rgba(148,163,184,0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(148,163,184,0.05) 1px, transparent 1px);
        background-size:46px 46px;
    }}
    .facility-zone {{
        position:absolute;
        left:8%;
        right:8%;
        top:9%;
        height:30%;
        border:1px solid rgba(96,165,250,0.58);
        border-radius:16px;
        background:rgba(14,165,233,0.08);
        padding:1rem;
    }}
    .ground-zone {{
        position:absolute;
        left:8%;
        right:8%;
        bottom:11%;
        height:33%;
        border:1px solid rgba(148,163,184,0.28);
        border-radius:16px;
        background:linear-gradient(180deg, rgba(15,23,42,0.58), rgba(22,101,52,0.16));
        padding:1rem;
    }}
    .zone-title {{font-size:1.22rem; font-weight:900; color:#F8FAFC; margin-bottom:.35rem;}}
    .zone-note {{font-size:.9rem; font-weight:760; color:#A7B3C7;}}
    .zone-note.warm {{color:#FCA5A5;}}
    .zone-note.cool {{color:#93C5FD;}}
    .down-flow {{
        position:absolute;
        top:30%;
        width:20px;
        height:42%;
        border-radius:999px;
        background:rgba(14,116,144,0.34);
        overflow:hidden;
        border:1px solid rgba(56,189,248,0.16);
    }}
    .down-flow.f1 {{left:42%;}}
    .down-flow.f2 {{right:36%;}}
    .down-flow::before {{
        content:"";
        position:absolute;
        left:2px;
        right:2px;
        top:-42%;
        height:42%;
        border-radius:999px;
        background:linear-gradient(180deg, transparent, rgba(56,189,248,0.92), transparent);
        animation:ground-flow {flow_duration}s linear infinite;
    }}
    .down-flow.f2::before {{animation-delay:1.4s;}}
    .ground-buffer-core {{
        position:absolute;
        left:38%;
        bottom:20%;
        width:24%;
        height:58px;
        border-radius:50%;
        background:radial-gradient(ellipse, rgba(34,197,94,0.26), rgba(56,189,248,0.10) 48%, transparent 72%);
        filter:blur(.5px);
    }}
    .ground-chip {{
        position:absolute;
        border:1px solid rgba(56,189,248,0.28);
        background:rgba(15,23,42,0.72);
        border-radius:10px;
        padding:.38rem .58rem;
        color:#D7DEE9;
        font-size:.78rem;
        font-weight:800;
    }}
    .ground-chip.offset {{left:10%; top:43%; color:#BBF7D0;}}
    .ground-chip.risk {{right:10%; top:43%; color:#FCA5A5;}}
    .ground-utilization {{
        position:absolute;
        left:10%;
        right:10%;
        bottom:5%;
        height:22px;
        border-radius:999px;
        border:1px solid rgba(56,189,248,0.28);
        background:rgba(15,23,42,0.68);
        overflow:hidden;
    }}
    .ground-utilization span {{
        display:block;
        width:{sink_utilization_pct:.0f}%;
        height:100%;
        background:linear-gradient(90deg, rgba(56,189,248,0.92), rgba(34,197,94,0.76));
    }}
    .ground-utilization b {{
        position:absolute;
        inset:0;
        display:grid;
        place-items:center;
        color:#F8FAFC;
        font-size:.78rem;
    }}
    .ground-side h4 {{margin:.1rem 0 .65rem 0; color:#F8FAFC; font-size:1.04rem;}}
    .ground-brief {{
        border-left:3px solid rgba(56,189,248,0.70);
        padding-left:.72rem;
        color:#CBD5E1;
        line-height:1.5;
        font-size:.9rem;
        margin:.75rem 0 .9rem 0;
    }}
    .ground-status-list {{display:grid; gap:.62rem; margin-bottom:.9rem;}}
    .ground-status-row {{
        display:flex;
        justify-content:space-between;
        gap:.75rem;
        padding:.62rem .7rem;
        border-radius:10px;
        background:rgba(15,23,42,0.48);
        border:1px solid rgba(148,163,184,0.16);
        color:#D7DEE9;
        font-size:.84rem;
    }}
    .ground-status-row b {{color:#F8FAFC;}}
    .ground-boundary {{
        padding:.72rem .78rem;
        border-radius:12px;
        background:rgba(245,158,11,0.10);
        border:1px solid rgba(245,158,11,0.24);
        color:#FDE68A;
        font-size:.82rem;
        line-height:1.45;
    }}
    @keyframes ground-flow {{
        0% {{transform:translateY(-40%); opacity:.25;}}
        50% {{opacity:.95;}}
        100% {{transform:translateY(260%); opacity:.25;}}
    }}
    @media (max-width: 980px) {{
        .ground-layout {{grid-template-columns:1fr;}}
    }}
    </style>
    <div class="ground-buffer-shell">
      <div class="ground-buffer-header">
        <div>
          <div class="ground-kicker">CONCEPT LAB // INFRASTRUCTURE RESILIENCE</div>
          <h2 class="ground-title">Ground-Coupled Thermal Buffer Concept</h2>
          <div class="ground-subtitle">
            Conceptual ground-coupled cooling and subsurface thermal buffering visualization.
            The values are scenario-based indicators, not validated engineering performance.
          </div>
        </div>
      </div>
      <div class="ground-layout">
        <div class="ground-visual">
          <div class="ground-map">
            <div class="facility-zone">
              <div class="zone-title">Facility Thermal Zone</div>
              <div class="zone-note warm">Conceptual heat pressure routed downward for buffering</div>
            </div>
            <div class="ground-zone">
              <div class="zone-title">Ground-Coupled Buffer Zone</div>
              <div class="zone-note cool">Subsurface heat absorption concept</div>
            </div>
            <div class="down-flow f1"></div>
            <div class="down-flow f2"></div>
            <div class="ground-buffer-core"></div>
            <div class="ground-chip offset">Cooling offset: {cooling_offset_pct:.1f}%</div>
            <div class="ground-chip risk">Saturation risk: {saturation_risk_pct:.0f}%</div>
            <div class="ground-utilization"><span></span><b>Sink utilization {sink_utilization_pct:.0f}%</b></div>
          </div>
        </div>
        <div class="ground-side">
          <h4>How to interpret this panel</h4>
          <div class="ground-brief">
            Upper zone: facility thermal load area.<br>
            Lower zone: conceptual ground-coupled buffer.<br>
            Blue vertical flow: guided transfer into a subsurface exchange zone.
          </div>
          <div class="ground-brief">
            This visual emphasizes downward guided flow and buffer utilization. It should be read as a concept indicator, not a hardware blueprint.
          </div>
          <h4>Illustrative Concept Indicators</h4>
          <div class="ground-status-list">
            <div class="ground-status-row"><span>Cooling offset</span><b>{cooling_offset_pct:.1f}%</b></div>
            <div class="ground-status-row"><span>Sink utilization</span><b>{sink_utilization_pct:.0f}%</b></div>
            <div class="ground-status-row"><span>Saturation risk</span><b>{saturation_risk_pct:.0f}%</b></div>
          </div>
          <div class="ground-boundary">
            Values shown are scenario-based concept indicators, not validated engineering performance.
          </div>
        </div>
      </div>
    </div>
    """).strip()
    ground_panel_html = "\n".join(line.strip() for line in ground_panel_html.splitlines() if line.strip())
    st.markdown(ground_panel_html, unsafe_allow_html=True)
# UI-ONLY CHANGE END


# UI-ONLY CHANGE START
# Presentation-only Concept Lab wording overrides.
# These preserve input bindings and visual metaphors while making concept boundaries clearer.
CONCEPT_BOUNDARY_NOTE = (
    "Scenario-based concept visualization only. It does not represent validated hardware design, "
    "real-time control capability, physical engineering performance, or guaranteed energy outcome."
)


def concept_level_label(value, high_label="High", medium_label="Moderate", low_label="Limited"):
    value = clamp(float(value), 0.0, 100.0)
    if value >= 80:
        return high_label
    if value >= 45:
        return medium_label
    return low_label


def concept_disruption_label(value):
    value = clamp(float(value), 0.0, 100.0)
    if value <= 10:
        return "Low disruption state"
    if value <= 35:
        return "Moderate disruption state"
    return "Elevated disruption state"


def _render_concept_html(html: str):
    from textwrap import dedent

    html = dedent(html).strip()
    html = "\n".join(line.strip() for line in html.splitlines() if line.strip())
    st.markdown(html, unsafe_allow_html=True)


def render_phase_change_buffer_concept(
    heat_load_mw=18.0,
    buffer_state_pct=75.0,
    demand_reduction_pct=5.0,
    reserve_bonus_hours=4.0,
    height=720,
):
    # Infrastructure Resilience Layer: phase-change thermal storage concept.
    buffer_state_pct = clamp(float(buffer_state_pct), 0.0, 100.0)
    demand_reduction_pct = clamp(float(demand_reduction_pct), 0.0, 100.0)
    reserve_bonus_hours = max(float(reserve_bonus_hours), 0.0)
    heat_load_mw = max(float(heat_load_mw), 0.0)
    buffer_state_label = concept_level_label(buffer_state_pct, "High storage state", "Moderate storage state", "Limited storage state")
    flow_duration = max(4.0, 8.0 - buffer_state_pct / 20.0)

    _render_concept_html(f"""
    <style>
    .pcm-shell {{border:1px solid rgba(56,189,248,0.22); border-radius:14px; background:linear-gradient(145deg, rgba(15,23,42,0.86), rgba(8,47,73,0.18)); padding:1.05rem; min-height:{max(int(height)-120, 520)}px;}}
    .pcm-title {{font-size:clamp(1.35rem,1.9vw,2rem); font-weight:900; color:#F8FAFC; margin:0;}}
    .pcm-sub {{color:#A7B3C7; margin:.45rem 0 1rem 0; line-height:1.48;}}
    .pcm-grid {{display:grid; grid-template-columns:minmax(0,1.8fr) minmax(280px,.85fr); gap:1rem;}}
    .pcm-visual,.pcm-side {{border:1px solid rgba(148,163,184,0.22); border-radius:14px; background:rgba(8,13,28,0.56); padding:1rem;}}
    .pcm-map {{position:relative; min-height:365px; border:1px solid rgba(56,189,248,0.16); border-radius:12px; overflow:hidden; background:radial-gradient(circle at 50% 48%, rgba(251,191,36,0.12), transparent 28%), linear-gradient(135deg, rgba(15,23,42,.94), rgba(8,47,73,.25));}}
    .pcm-map::before {{content:""; position:absolute; inset:0; background-image:linear-gradient(rgba(148,163,184,.055) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,.055) 1px, transparent 1px); background-size:44px 44px;}}
    .pcm-node {{position:absolute; border:2px solid rgba(96,165,250,.70); border-radius:16px; background:rgba(15,23,42,.72); padding:1rem; color:#F8FAFC;}}
    .pcm-node.server {{left:9%; top:25%; width:170px;}} .pcm-node.buffer {{left:38%; top:30%; width:190px; height:128px; display:grid; place-content:center; text-align:center;}} .pcm-node.state {{right:9%; top:25%; width:150px; text-align:center;}}
    .pcm-node h4 {{margin:0 0 .35rem 0; font-size:1.25rem;}} .pcm-node b {{font-size:1.35rem; color:#FDE68A;}}
    .pcm-flow {{position:absolute; left:10%; right:10%; height:18px; border-radius:999px; overflow:hidden; background:rgba(15,23,42,.70); border:1px solid rgba(148,163,184,.18);}}
    .pcm-flow.cold {{top:38%;}} .pcm-flow.warm {{top:62%;}}
    .pcm-flow::before {{content:""; position:absolute; inset:0; width:34%; border-radius:999px; animation:pcm-flow {flow_duration}s linear infinite;}}
    .pcm-flow.cold::before {{background:linear-gradient(90deg, transparent, rgba(56,189,248,.92), transparent);}}
    .pcm-flow.warm::before {{background:linear-gradient(90deg, transparent, rgba(248,113,113,.78), transparent); animation-delay:1.2s;}}
    .pcm-indicators {{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.7rem; margin-top:.8rem;}}
    .pcm-chip {{border:1px solid rgba(56,189,248,.22); border-radius:10px; background:rgba(15,23,42,.60); padding:.65rem; color:#D7DEE9; font-size:.84rem;}}
    .pcm-chip b {{display:block; color:#F8FAFC; font-size:1rem; margin-top:.18rem;}}
    .pcm-side h4 {{margin:.1rem 0 .65rem 0; color:#F8FAFC; font-size:1.04rem;}}
    .pcm-brief {{border-left:3px solid rgba(56,189,248,.70); padding-left:.72rem; color:#CBD5E1; line-height:1.5; font-size:.9rem; margin:.75rem 0 .9rem 0;}}
    .pcm-row {{display:flex; justify-content:space-between; gap:.7rem; padding:.6rem .7rem; border-radius:10px; background:rgba(15,23,42,.48); border:1px solid rgba(148,163,184,.16); color:#D7DEE9; font-size:.84rem; margin-bottom:.55rem;}}
    .pcm-row b {{color:#F8FAFC;}} .pcm-boundary {{padding:.72rem .78rem; border-radius:12px; background:rgba(245,158,11,.10); border:1px solid rgba(245,158,11,.24); color:#FDE68A; font-size:.82rem; line-height:1.45; margin-top:.8rem;}}
    @keyframes pcm-flow {{0%{{transform:translateX(-120%);}}100%{{transform:translateX(260%);}}}}
    @media(max-width:980px){{.pcm-grid{{grid-template-columns:1fr;}} .pcm-indicators{{grid-template-columns:1fr;}}}}
    </style>
    <div class="pcm-shell">
      <h2 class="pcm-title">Phase-Change Thermal Storage Concept</h2>
      <div class="pcm-sub">Conceptual latent-heat storage and charge/discharge visualization. This shows scenario-based thermal storage behavior, not validated hardware performance.</div>
      <div class="pcm-grid">
        <div class="pcm-visual">
          <div class="pcm-map">
            <div class="pcm-flow cold"></div><div class="pcm-flow warm"></div>
            <div class="pcm-node server"><h4>Server Core</h4><span>Heat load</span><br><b>{heat_load_mw:.1f} MW</b></div>
            <div class="pcm-node buffer"><h4>PCM Buffer</h4><span>Latent heat storage concept</span></div>
            <div class="pcm-node state"><h4>Buffer State</h4><b>{buffer_state_label}</b></div>
          </div>
          <div class="pcm-indicators">
            <div class="pcm-chip">Estimated demand relief<b>{demand_reduction_pct:.1f}%</b></div>
            <div class="pcm-chip">Estimated reserve support<b>{reserve_bonus_hours:.1f} h</b></div>
            <div class="pcm-chip">Peak-load buffering active<b>Concept indicator</b></div>
          </div>
        </div>
        <div class="pcm-side">
          <h4>How to interpret this panel</h4>
          <div class="pcm-brief">Blue loop: conceptual cold-side storage circulation.<br>Red loop: conceptual heat recovery / discharge circulation.<br>Center tank: phase-change thermal storage concept.</div>
          <div class="pcm-brief">The visual illustrates latent heat buffering for scenario thinking. It should not be read as validated engineering hardware.</div>
          <h4>Illustrative Concept Indicators</h4>
          <div class="pcm-row"><span>Buffer State</span><b>{buffer_state_label}</b></div>
          <div class="pcm-row"><span>Estimated demand relief</span><b>{demand_reduction_pct:.1f}%</b></div>
          <div class="pcm-row"><span>Estimated scenario support duration</span><b>{reserve_bonus_hours:.1f} h</b></div>
          <div class="pcm-boundary">{CONCEPT_BOUNDARY_NOTE}</div>
        </div>
      </div>
    </div>
    """)


def render_distributed_thermal_control_concept(
    node_availability_pct=100.0,
    rerouting_efficiency_pct=100.0,
    damage_ratio_pct=0.0,
    protected_core_pct=100.0,
    height=720,
):
    # Infrastructure Resilience Layer: distributed thermal routing concept.
    node_availability_pct = clamp(float(node_availability_pct), 0.0, 100.0)
    rerouting_efficiency_pct = clamp(float(rerouting_efficiency_pct), 0.0, 100.0)
    damage_ratio_pct = clamp(float(damage_ratio_pct), 0.0, 100.0)
    protected_core_pct = clamp(float(protected_core_pct), 0.0, 100.0)
    pathway_state = concept_level_label(node_availability_pct, "High pathway availability", "Moderate pathway availability", "Limited pathway availability")
    rerouting_state = concept_level_label(rerouting_efficiency_pct, "Strong rerouting state", "Moderate rerouting state", "Limited rerouting state")
    support_state = concept_level_label(protected_core_pct, "Nominal support state", "Partial support state", "Limited support state")
    disruption_state = concept_disruption_label(damage_ratio_pct)

    _render_concept_html(f"""
    <style>
    .routing-shell {{border:1px solid rgba(56,189,248,.22); border-radius:14px; background:linear-gradient(145deg, rgba(15,23,42,.86), rgba(8,47,73,.18)); padding:1.05rem; min-height:{max(int(height)-120,520)}px;}}
    .routing-title {{font-size:clamp(1.35rem,1.9vw,2rem); font-weight:900; color:#F8FAFC; margin:0;}} .routing-sub {{color:#A7B3C7; margin:.45rem 0 1rem 0; line-height:1.48;}}
    .routing-grid {{display:grid; grid-template-columns:minmax(0,1.8fr) minmax(280px,.85fr); gap:1rem;}} .routing-visual,.routing-side {{border:1px solid rgba(148,163,184,.22); border-radius:14px; background:rgba(8,13,28,.56); padding:1rem;}}
    .routing-map {{position:relative; min-height:365px; border:1px solid rgba(56,189,248,.16); border-radius:12px; background:linear-gradient(135deg, rgba(15,23,42,.94), rgba(8,47,73,.22)); overflow:hidden;}}
    .route-link {{position:absolute; height:8px; border-radius:999px; background:#64748B; opacity:.78;}} .route-link.blue {{background:#0EA5E9;}} .route-link.red {{background:#E11D48; opacity:.82;}}
    .rl1 {{left:13%; top:30%; width:23%;}} .rl2 {{left:32%; top:47%; width:26%; transform:rotate(-34deg);}} .rl3 {{left:49%; top:47%; width:26%;}} .rl4 {{left:15%; top:67%; width:22%;}} .rl5 {{left:33%; top:67%; width:42%;}}
    .route-node {{position:absolute; width:42px; height:42px; border-radius:999px; background:#1E293B; border:3px solid #94A3B8;}} .route-core {{position:absolute; left:45%; top:43%; width:60px; height:60px; border-radius:999px; background:#5EEAD4; border:3px solid #E0F2FE; display:grid; place-items:center; font-weight:900; color:#06251F;}}
    .n1{{left:11%; top:24%;}} .n2{{left:27%; top:24%;}} .n3{{left:43%; top:24%;}} .n4{{left:59%; top:24%;}} .n5{{left:75%; top:24%;}} .n6{{left:11%; top:56%;}} .n7{{left:27%; top:56%;}} .n8{{left:59%; top:56%;}} .n9{{left:75%; top:56%;}}
    .routing-indicators {{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.7rem; margin-top:.8rem;}} .routing-chip {{border:1px solid rgba(56,189,248,.22); border-radius:10px; background:rgba(15,23,42,.60); padding:.65rem; color:#D7DEE9; font-size:.82rem;}} .routing-chip b{{display:block; color:#F8FAFC; margin-top:.18rem;}}
    .routing-side h4{{margin:.1rem 0 .65rem 0; color:#F8FAFC; font-size:1.04rem;}} .routing-brief{{border-left:3px solid rgba(56,189,248,.70); padding-left:.72rem; color:#CBD5E1; line-height:1.5; font-size:.9rem; margin:.75rem 0 .9rem 0;}} .routing-boundary{{padding:.72rem .78rem; border-radius:12px; background:rgba(245,158,11,.10); border:1px solid rgba(245,158,11,.24); color:#FDE68A; font-size:.82rem; line-height:1.45; margin-top:.8rem;}}
    @media(max-width:980px){{.routing-grid{{grid-template-columns:1fr;}} .routing-indicators{{grid-template-columns:1fr 1fr;}}}}
    </style>
    <div class="routing-shell">
      <h2 class="routing-title">Distributed Thermal Routing Concept</h2>
      <div class="routing-sub">Conceptual modular routing and disruption-tolerance visualization. This panel shows routing indicators, not real-time engineering control.</div>
      <div class="routing-grid">
        <div class="routing-visual"><div class="routing-map">
          <div class="route-link blue rl1"></div><div class="route-link red rl2"></div><div class="route-link blue rl3"></div><div class="route-link red rl4"></div><div class="route-link rl5"></div>
          <div class="route-node n1"></div><div class="route-node n2"></div><div class="route-node n3"></div><div class="route-node n4"></div><div class="route-node n5"></div><div class="route-node n6"></div><div class="route-node n7"></div><div class="route-node n8"></div><div class="route-node n9"></div><div class="route-core">CORE</div>
        </div>
        <div class="routing-indicators">
          <div class="routing-chip">Pathway availability<b>{pathway_state}</b></div><div class="routing-chip">Rerouting state<b>{rerouting_state}</b></div><div class="routing-chip">Disruption state<b>{disruption_state}</b></div><div class="routing-chip">Support condition<b>{support_state}</b></div>
        </div></div>
        <div class="routing-side"><h4>How to interpret this panel</h4><div class="routing-brief">Blue links: primary support pathways.<br>Red links: scenario rerouting pathways.<br>Muted gray links: inactive or lower-priority branches.</div><div class="routing-brief">This is a conceptual routing view for resilience thinking, not autonomous control or guaranteed protection.</div><h4>Illustrative Concept Indicators</h4><div class="routing-brief">Pathway availability: {pathway_state}<br>Rerouting state: {rerouting_state}<br>Support condition: {support_state}<br>Disruption condition: {disruption_state}</div><div class="routing-boundary">{CONCEPT_BOUNDARY_NOTE}</div></div>
      </div>
    </div>
    """)


def render_distributed_harvesting_buffering_concept(
    diversification_score=100.0,
    reserve_gain_hours=4.0,
    shortfall_reduction_pct=8.0,
    core_preservation_hours=24.0,
    height=720,
):
    # Infrastructure Resilience Layer: distributed energy buffering concept.
    diversification_score = clamp(float(diversification_score), 0.0, 100.0)
    reserve_gain_hours = max(float(reserve_gain_hours), 0.0)
    shortfall_reduction_pct = clamp(float(shortfall_reduction_pct), 0.0, 100.0)
    core_preservation_hours = max(float(core_preservation_hours), 0.0)
    diversification_state = concept_level_label(diversification_score, "High source diversity", "Moderate source diversity", "Limited source diversity")
    demand_relief_state = concept_level_label(shortfall_reduction_pct, "Visible demand relief", "Moderate demand relief", "Limited demand relief")

    _render_concept_html(f"""
    <style>
    .buffering-shell {{border:1px solid rgba(56,189,248,.22); border-radius:14px; background:linear-gradient(145deg, rgba(15,23,42,.86), rgba(8,47,73,.18)); padding:1.05rem; min-height:{max(int(height)-120,520)}px;}}
    .buffering-title {{font-size:clamp(1.35rem,1.9vw,2rem); font-weight:900; color:#F8FAFC; margin:0;}} .buffering-sub {{color:#A7B3C7; margin:.45rem 0 1rem 0; line-height:1.48;}}
    .buffering-grid {{display:grid; grid-template-columns:minmax(0,1.8fr) minmax(280px,.85fr); gap:1rem;}} .buffering-visual,.buffering-side {{border:1px solid rgba(148,163,184,.22); border-radius:14px; background:rgba(8,13,28,.56); padding:1rem;}}
    .buffering-map {{position:relative; min-height:365px; border:1px solid rgba(56,189,248,.16); border-radius:12px; background:linear-gradient(135deg, rgba(15,23,42,.94), rgba(8,47,73,.22)); overflow:hidden;}}
    .source-node,.buffer-node,.output-node {{position:absolute; border-radius:18px; border:2px solid rgba(96,165,250,.70); background:rgba(15,23,42,.72); display:grid; place-items:center; text-align:center; color:#F8FAFC; font-weight:900;}}
    .source-node {{left:10%; width:86px; height:86px; border-radius:999px;}} .source-node.solar{{top:16%; border-color:#F59E0B;}} .source-node.wind{{top:43%; border-color:#0EA5E9;}} .source-node.hydro{{top:70%; border-color:#2563EB;}}
    .buffer-node {{left:39%; top:32%; width:190px; height:128px;}} .output-node {{right:9%; top:38%; width:140px; height:96px; border-color:#34D399;}}
    .source-flow {{position:absolute; height:9px; border-radius:999px; transform-origin:left center; opacity:.86;}} .source-flow.fsolar{{left:20%; top:27%; width:22%; transform:rotate(22deg); background:#F59E0B;}} .source-flow.fwind{{left:20%; top:53%; width:23%; transform:rotate(-6deg); background:#0EA5E9;}} .source-flow.fhydro{{left:20%; top:78%; width:25%; transform:rotate(-28deg); background:#2563EB;}} .source-flow.fout{{left:58%; top:49%; width:24%; background:#16A34A;}}
    .buffering-indicators {{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.7rem; margin-top:.8rem;}} .buffering-chip {{border:1px solid rgba(56,189,248,.22); border-radius:10px; background:rgba(15,23,42,.60); padding:.65rem; color:#D7DEE9; font-size:.82rem;}} .buffering-chip b{{display:block; color:#F8FAFC; margin-top:.18rem;}}
    .buffering-side h4{{margin:.1rem 0 .65rem 0; color:#F8FAFC; font-size:1.04rem;}} .buffering-brief{{border-left:3px solid rgba(56,189,248,.70); padding-left:.72rem; color:#CBD5E1; line-height:1.5; font-size:.9rem; margin:.75rem 0 .9rem 0;}} .buffering-boundary{{padding:.72rem .78rem; border-radius:12px; background:rgba(245,158,11,.10); border:1px solid rgba(245,158,11,.24); color:#FDE68A; font-size:.82rem; line-height:1.45; margin-top:.8rem;}}
    @media(max-width:980px){{.buffering-grid{{grid-template-columns:1fr;}} .buffering-indicators{{grid-template-columns:1fr 1fr;}}}}
    </style>
    <div class="buffering-shell">
      <h2 class="buffering-title">Distributed Energy Buffering Concept</h2>
      <div class="buffering-sub">Conceptual multi-source energy buffering and critical-output support visualization. It shows scenario-based support indicators, not guaranteed infrastructure performance.</div>
      <div class="buffering-grid">
        <div class="buffering-visual"><div class="buffering-map">
          <div class="source-node solar">Solar</div><div class="source-node wind">Wind</div><div class="source-node hydro">Hydro</div>
          <div class="source-flow fsolar"></div><div class="source-flow fwind"></div><div class="source-flow fhydro"></div><div class="source-flow fout"></div>
          <div class="buffer-node">Buffer Pool<br><span style="font-size:.82rem;color:#93C5FD;">Multi-source balancing</span></div><div class="output-node">Critical Output<br><span style="font-size:.82rem;color:#86EFAC;">Support indicator</span></div>
        </div>
        <div class="buffering-indicators"><div class="buffering-chip">Source diversity state<b>{diversification_state}</b></div><div class="buffering-chip">Estimated scenario support duration<b>{reserve_gain_hours:.1f} h</b></div><div class="buffering-chip">Demand relief state<b>{demand_relief_state}</b></div><div class="buffering-chip">Estimated buffer support duration<b>{core_preservation_hours:.1f} h</b></div></div></div>
        <div class="buffering-side"><h4>How to interpret this panel</h4><div class="buffering-brief">Source paths represent solar, wind, hydro, and reserve inputs. The buffer pool is an illustrative balancing layer, and the priority stream represents critical-output support.</div><div class="buffering-brief">This panel supports scenario thinking about distributed buffering. It does not imply guaranteed core preservation or validated physical performance.</div><h4>Illustrative Concept Indicators</h4><div class="buffering-brief">Source diversity state: {diversification_state}<br>Estimated scenario support duration: {reserve_gain_hours:.1f} h<br>Estimated buffer support duration: {core_preservation_hours:.1f} h</div><div class="buffering-boundary">{CONCEPT_BOUNDARY_NOTE}</div></div>
      </div>
    </div>
    """)


def render_concept_lab_workspace():
    page_question(tr("tabs")[7])
    st.markdown(f'<div class="note">{tr("concept_note")}</div>', unsafe_allow_html=True)
    concept_tabs = st.tabs(tr("thermal_tabs"))
    base_damage_pct = round((sum(failure_ratios.values()) / len(failure_ratios)) * 100, 1)
    base_div_score = round(len([v for v in results["actual_mix_mw"].values() if v > 0]) / 4 * 100, 1)
    timeline_shortfall_num = timeline_results["hours_until_shortfall"] if timeline_results["hours_until_shortfall"] != "No Failure" else 999
    timeline_critical_num = timeline_results["hours_until_critical_failure"] if timeline_results["hours_until_critical_failure"] != "No Failure" else 999
    thermal_results = {
        "adjusted_demand": results["demand"] * 0.95 if thermal_concept_enabled else results["demand"],
        "adjusted_reserve_days": results.get("reserve_days_remaining", 0) + 1,
        "adjusted_hours_until_shortfall": timeline_shortfall_num + 4,
        "adjusted_hours_until_critical_failure": timeline_critical_num + 5,
        "thermal_demand_reduction_pct": 5.0,
        "buffer_state_pct": 75.0,
        "sink_utilization_pct": 60.0,
        "damage_ratio_pct": max(base_damage_pct - 2, 0),
        "diversification_score": min(base_div_score + 5, 100),
    }
    with concept_tabs[0]:
        concept_badge()
        render_thermal_principle_simulation(fresh_air_temp_c=fresh_air_temp_c, exhaust_air_temp_c=exhaust_air_temp_c, recovery_efficiency=recovery_efficiency, airflow_speed=thermal_animation_speed, height=820)
    with concept_tabs[1]:
        concept_badge()
        render_phase_change_buffer_concept(heat_load_mw=max(results["demand"] * 0.18, 1.0), buffer_state_pct=thermal_results["buffer_state_pct"], demand_reduction_pct=max(thermal_results["thermal_demand_reduction_pct"], 1.0), reserve_bonus_hours=4.0, height=720)
    with concept_tabs[2]:
        concept_badge()
        render_ground_thermal_sink_concept(cooling_offset_pct=4.0, sink_utilization_pct=thermal_results["sink_utilization_pct"], saturation_risk_pct=20.0, height=720)
    with concept_tabs[3]:
        concept_badge()
        availability = round((1 - max(failure_ratios.values())) * 100, 0)
        rerouting_efficiency = round(max(40.0, 100 - (sum(failure_ratios.values()) / len(failure_ratios)) * 100), 0)
        render_distributed_thermal_control_concept(node_availability_pct=availability, rerouting_efficiency_pct=rerouting_efficiency, damage_ratio_pct=thermal_results["damage_ratio_pct"], protected_core_pct=round(max(45.0, 100 - results["grid_dependency"]), 0), height=720)
    with concept_tabs[4]:
        concept_badge()
        core_hours = timeline_results["hours_until_critical_failure"] if timeline_results["hours_until_critical_failure"] != "No Failure" else 168
        render_distributed_harvesting_buffering_concept(diversification_score=thermal_results["diversification_score"], reserve_gain_hours=4.0, shortfall_reduction_pct=8.0, core_preservation_hours=float(core_hours), height=720)

# PRODUCT UI RESTRUCTURE START
# Results presentation only: calculations above remain unchanged.
def operational_risk_label():
    if results["shortfall"] >= 15 or results["grid_dependency"] >= 25:
        return tr("high_grid_instability_risk")
    if results["shortfall"] >= 5 or results["grid_dependency"] >= 10:
        return tr("supply_stress_detected")
    return tr("low_shortfall_risk")


def battery_status_label():
    if results["battery_levels"] <= max(inputs["battery_capacity"] * 0.25, 1):
        return tr("battery_reserve_declining")
    return tr("battery_reserve_available")


def renewable_status_label():
    if results["renewable_ratio"] >= 45:
        return tr("renewable_acceptable")
    return tr("renewable_watch")


def render_operational_summary_panel():
    # Decision Support Layer: concise operational state for non-technical users.
    summary_rows = [
        ("System", operational_risk_label()),
        ("Battery", battery_status_label()),
        ("Renewables", renewable_status_label()),
        ("Scenario", scenario_key.replace("_", " ").title()),
    ]
    st.markdown(
        """
        <div class="hero">
          <h3>Operational Summary</h3>
          <p>TAIVAS converts the selected scenario into a short resilience readout for decision review.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    for col, (label, value) in zip(cols, summary_rows):
        with col:
            mini_card(label, value)


def render_demand_supply_chart():
    chart_labels = [tr("demand"), tr("renewable"), tr("final"), tr("shortfall")]
    chart_values = [results["demand"], results["renewable_supply"], results["final_supply"], results["shortfall"]]
    chart_colors = ["#38BDF8", "#22C55E", "#60A5FA", "#F97316"]
    fig, ax = plt.subplots(figsize=(9.5, 3.2))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    ax.barh(chart_labels, chart_values, color=chart_colors, alpha=0.92)
    ax.invert_yaxis()
    ax.set_xlabel("MW")
    ax.set_title("Demand vs Supply", fontsize=14, pad=12)
    ax.grid(axis="x", alpha=0.22)
    ax.tick_params(axis="both", labelsize=11)
    max_value = max(chart_values) if chart_values else 1
    for i, value in enumerate(chart_values):
        ax.text(value + max_value * 0.015, i, f"{value:.2f}", va="center", fontsize=10, color="#E5E7EB")
    ax.set_xlim(0, max_value * 1.16 if max_value > 0 else 1)
    plt.tight_layout(pad=1.2)
    st.pyplot(fig, clear_figure=True)


def render_main_system_status():
    # Energy System Layer: demand, supply, energy gap, and system stability.
    st.subheader(tr("main_system_status"))
    # UI REFINEMENT START
    status_left, status_right = st.columns([0.9, 1.35])
    with status_left:
        metric_cols = st.columns(2)
        metric_cols[0].metric(tr("demand"), f"{results['demand']} MW", delta=f"{round(results['demand'] - baseline_results['demand'], 2)} vs baseline")
        metric_cols[1].metric(tr("final"), f"{results['final_supply']} MW", delta=f"{round(results['final_supply'] - baseline_results['final_supply'], 2)}")
        metric_cols = st.columns(2)
        metric_cols[0].metric(tr("shortfall"), f"{results['shortfall']} MW", delta=f"{round(results['shortfall'] - baseline_results['shortfall'], 2)}")
        metric_cols[1].metric(tr("eff"), f"{results['system_efficiency']}%")
    with status_right:
        render_demand_supply_chart()
    st.caption(tr("metric_help"))
    # UI REFINEMENT END


def render_battery_storage_status():
    # Energy System Layer: storage buffer and reserve behavior.
    st.subheader(tr("battery_storage_status"))
    cols = st.columns(3)
    cols[0].metric(tr("battery"), f"{results['battery_levels']} MWh")
    cols[1].metric(tr("reserve_days"), f"{results.get('reserve_days_remaining', 0)} days")
    cols[2].metric(tr("shortfall_hour"), timeline_results["hours_until_shortfall"])
    timeline_df = pd.DataFrame(timeline_results["rows"])
    if not timeline_df.empty:
        reserve_cols = [c for c in ["battery_level", "reserve_energy", "shortfall"] if c in timeline_df.columns]
        if reserve_cols:
            friendly_names = {
                "battery_level": "Battery Level",
                "reserve_energy": "Reserve Energy",
                "shortfall": "Energy Gap",
            }
            st.line_chart(timeline_df[reserve_cols].rename(columns=friendly_names))


def render_renewable_mix_summary():
    st.subheader(tr("renewable_mix"))
    mix_cols = st.columns(2)
    with mix_cols[0]:
        render_stable_donut_chart(results["actual_mix_pct"], results["renewable_ratio"], tr("actual_mix"))
    with mix_cols[1]:
        st.metric(tr("rr"), f"{results['renewable_ratio']}%")
        st.metric(tr("renewable"), f"{results['renewable_supply']} MW")
        st.metric(tr("dominant"), results["dominant_source"])


def render_context_cards():
    context_cols = st.columns(4)
    with context_cols[0]:
        mini_card("Location", f"{active_city}, {active_country}")
    with context_cols[1]:
        mini_card("Facility", facility_type)
    with context_cols[2]:
        mini_card("Climate Scenario", scenario_key.replace("_", " ").title())
    with context_cols[3]:
        mini_card("Mode", "Guided Dashboard")


def render_product_overview():
    render_operational_summary_panel()
    # UI-ONLY CHANGE START
    render_risk_tier_panel()
    # UI-ONLY CHANGE END
    render_context_cards()
    render_main_system_status()
    render_battery_storage_status()
    render_renewable_mix_summary()
    with st.expander(tr("view_detailed_analysis"), expanded=False):
        render_ai_recommendation_workspace()
        render_energy_security_workspace()


def render_product_scenario_analysis():
    scenario_tabs = st.tabs(["Comparison", "Visual Simulator", "Recommendations"])
    with scenario_tabs[0]:
        render_scenario_comparison_workspace()
    with scenario_tabs[1]:
        render_visual_simulator_workspace()
    with scenario_tabs[2]:
        render_ai_recommendation_workspace()


def render_product_advanced_analytics():
    st.markdown('<div class="note">Advanced analytics preserve the original technical workflow for analyst review.</div>', unsafe_allow_html=True)
    advanced_tabs = st.tabs(["Energy Mix", "Stress Test", "Energy Security", "Survival Timeline", "Concept Lab", "Export"])
    with advanced_tabs[0]:
        render_energy_mix_workspace()
    with advanced_tabs[1]:
        render_stress_test_workspace()
    with advanced_tabs[2]:
        render_energy_security_workspace()
    with advanced_tabs[3]:
        render_survival_timeline_workspace()
    with advanced_tabs[4]:
        render_concept_lab_workspace()
    with advanced_tabs[5]:
        render_export_center()
# PRODUCT UI RESTRUCTURE END


# -----------------------------------------------------------------------------
# Product-style Workspace Layer
# Major results are organized into three tabs to reduce vertical overload.
# -----------------------------------------------------------------------------
st.markdown('<div class="section-break"></div>', unsafe_allow_html=True)
product_tabs = st.tabs([tr("overview"), tr("scenario_analysis"), tr("advanced_analytics")])
with product_tabs[0]:
    render_product_overview()
with product_tabs[1]:
    render_product_scenario_analysis()
with product_tabs[2]:
    render_product_advanced_analytics()
