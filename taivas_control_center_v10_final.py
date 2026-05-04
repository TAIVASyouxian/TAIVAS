
# TAIVAS V10 FINAL (EXTERNAL VERSION)

import streamlit as st

# --- Feature Flags (External Clean Version) ---
FEATURE_FLAGS = {
    "trend": False,
    "concept_lab": True,
}

# --- Safe Wrapper ---
def safe_run(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except:
        return None

# --- Disable trend completely ---
try:
    import taivas_core.trend_forecast as tf
    def disabled_trend(*args, **kwargs):
        return None, None, {"status": "disabled"}
    tf.compute_trend_estimates = disabled_trend
except:
    pass

# --- Import original system ---
from taivas_main_original import *

# --- External Notice ---
st.markdown("""
### TAIVAS Decision-Support Simulation

This system is designed for scenario-based simulation and resilience analysis under extreme climate and energy disruption conditions.

It is not a predictive forecasting system.
""")
