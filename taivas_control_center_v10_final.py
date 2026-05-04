# TAIVAS V10 FINAL - External stable wrapper
import streamlit as st

# Disable trend/forecast safely. TAIVAS is positioned as decision-support simulation, not prediction.
try:
    import taivas_core.trend_forecast as tf
    def disabled_trend(*args, **kwargs):
        return None, None, {"status": "disabled"}
    tf.compute_trend_estimates = disabled_trend
except Exception:
    pass

from taivas_control_center_v9_5_clean import *

st.markdown("""
### TAIVAS Decision-Support Simulation

This system is designed for scenario-based simulation and resilience analysis under extreme climate and energy disruption conditions.

It is not a predictive forecasting system.
""")
