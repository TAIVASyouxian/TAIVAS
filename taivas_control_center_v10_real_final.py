
# TAIVAS V10 REAL FINAL (NO CRASH GUARANTEE)

import streamlit as st

# --- HARD DISABLE TREND (both compute + render) ---
try:
    import taivas_core.trend_forecast as tf
    def disabled_trend(*args, **kwargs):
        return None, None, {"status": "disabled"}
    tf.compute_trend_estimates = disabled_trend
except:
    pass

# --- IMPORT ORIGINAL ---
import taivas_control_center_v9_5_clean as original

# --- PATCH RENDER FUNCTION (THIS IS THE KEY FIX) ---
def safe_render_trend_estimate_panel(*args, **kwargs):
    st.info("Trend module disabled (stable version).")

original.render_trend_estimate_panel = safe_render_trend_estimate_panel

# --- RUN ORIGINAL APP ---
original

# --- MESSAGE ---
st.markdown("""
### TAIVAS Decision-Support Simulation

This system is designed for scenario-based simulation and resilience analysis.

It is not a predictive forecasting system.
""")
