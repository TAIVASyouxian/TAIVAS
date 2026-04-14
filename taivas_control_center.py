from io import StringIO

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from modules.charts import make_donut_chart
from modules.recommendations import recommendation_lines
from modules.energy_security import apply_energy_security_layer, ENERGY_SECURITY_SCENARIOS
from modules.survival_timeline import simulate_survival_timeline
from thermal_principle_component import render_thermal_principle_simulation
from concept_lab_components import (
    render_phase_change_buffer_concept,
    render_ground_thermal_sink_concept,
    render_distributed_thermal_control_concept,
    render_distributed_harvesting_buffering_concept,
)
