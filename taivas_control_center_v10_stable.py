
# TAIVAS V10 STABLE FINAL (NO TREND SAFE VERSION)

import streamlit as st

# --- Disable trend safely ---
try:
    import taivas_core.trend_forecast as tf
    def disabled_trend(*args, **kwargs):
        return None, None, {"status": "disabled"}
    tf.compute_trend_estimates = disabled_trend
except:
    pass

# --- Import original system ---
from taivas_control_center_v9_5_clean import *

# --- Patch: prevent trend panel crash ---
def safe_render_trend_panel(trend_df, forecast_df, meta):
    if trend_df is None:
        st.info("Trend module disabled (decision-support mode).")
        return
    if hasattr(trend_df, "empty") and trend_df.empty:
        st.info("No trend data available.")
        return
    try:
        for _ , row in trend_df.iterrows():
            pass
    except:
        st.info("Trend module disabled due to data inconsistency.")

# --- External Notice ---
st.markdown("""
### TAIVAS Decision-Support Simulation

This system is designed for scenario-based simulation and resilience analysis under extreme climate and energy disruption conditions.

It is not a predictive forecasting system.
""")
