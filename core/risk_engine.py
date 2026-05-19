"""Core TAIVAS risk helpers.

This module is intentionally framework-independent so risk logic can be reused
by Streamlit, APIs, scheduled workers, or tests.
"""


def safe_div(numerator, denominator):
    try:
        denominator = float(denominator)
        if denominator == 0:
            return 0.0
        return float(numerator) / denominator
    except Exception:
        return 0.0


def calculate_risk_tier(shortfall, demand):
    """Risk tier based on unmet demand ratio.

    Preserves the existing TAIVAS V3 formula:
    Low when no shortfall, then Elevated/High/Critical by shortfall share.
    """
    try:
        shortfall = float(shortfall)
        demand = float(demand)
    except Exception:
        return "Low"
    if shortfall <= 0:
        return "Low"
    shortfall_ratio = safe_div(shortfall, demand)
    if shortfall_ratio < 0.05:
        return "Elevated"
    if shortfall_ratio < 0.15:
        return "High"
    return "Critical"
