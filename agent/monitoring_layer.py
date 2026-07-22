"""TAIVAS Operational Monitoring Layer V2.

Pure helper functions for decision-support monitoring. These functions do not
import Streamlit and do not modify simulation outputs.
"""


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _safe_div(numerator, denominator):
    denominator = _safe_float(denominator)
    if denominator == 0:
        return 0.0
    return _safe_float(numerator) / denominator


def monitor_operational_risk(history_data, current_state):
    """Evaluate lightweight trend signals from timeline/history rows.

    Returns a structured dictionary only. This is monitoring support, not a
    prediction or autonomous control instruction.
    """
    history_data = history_data or []
    current_shortfall = _safe_float(current_state.get("shortfall"))
    current_battery = _safe_float(current_state.get("battery_levels"))
    current_renewable_ratio = _safe_float(current_state.get("renewable_ratio"))
    current_grid_dependency = _safe_float(current_state.get("grid_dependency"))

    recent_rows = history_data[-6:] if len(history_data) >= 6 else history_data
    shortfall_values = [_safe_float(row.get("shortfall")) for row in recent_rows]
    battery_values = [_safe_float(row.get("battery_level", row.get("battery_levels", current_battery))) for row in recent_rows]
    reserve_values = [_safe_float(row.get("reserve_energy", 0.0)) for row in recent_rows]

    shortfall_trend = 0.0
    battery_trend = 0.0
    reserve_trend = 0.0
    if len(shortfall_values) >= 2:
        shortfall_trend = shortfall_values[-1] - shortfall_values[0]
    if len(battery_values) >= 2:
        battery_trend = battery_values[-1] - battery_values[0]
    if len(reserve_values) >= 2:
        reserve_trend = reserve_values[-1] - reserve_values[0]

    if current_shortfall > 0 and shortfall_trend > 0:
        stress_stage = "Increasing Stress"
    elif current_shortfall > 0 or current_grid_dependency >= 15:
        stress_stage = "High Stress"
    elif current_battery <= 0:
        stress_stage = "Critical Risk"
    else:
        stress_stage = "Stable"

    stress_timeline = [
        {"Stage": "Current", "State": stress_stage},
        {"Stage": "Storage", "State": "Declining" if battery_trend < 0 else "Holding"},
        {"Stage": "Reserve", "State": "Declining" if reserve_trend < 0 else "Holding"},
        {"Stage": "Energy Gap", "State": "Increasing" if shortfall_trend > 0 else "Not increasing"},
    ]

    return {
        "shortfall_trend": round(shortfall_trend, 2),
        "battery_trend": round(battery_trend, 2),
        "reserve_trend": round(reserve_trend, 2),
        "renewable_ratio_current": round(current_renewable_ratio, 2),
        "grid_dependency_current": round(current_grid_dependency, 2),
        "stress_stage": stress_stage,
        "stress_timeline": stress_timeline,
    }


def build_alert_state(current_state, monitoring_signals=None):
    """Build NORMAL/WATCH/WARNING/CRITICAL alert state."""
    monitoring_signals = monitoring_signals or {}
    demand = _safe_float(current_state.get("demand"))
    shortfall = _safe_float(current_state.get("shortfall"))
    battery = _safe_float(current_state.get("battery_levels"))
    battery_capacity = max(_safe_float(current_state.get("battery_capacity")), 0.0)
    grid_dependency = _safe_float(current_state.get("grid_dependency"))
    renewable_ratio = _safe_float(current_state.get("renewable_ratio"))
    shortfall_ratio = _safe_div(shortfall, demand)
    battery_ratio = _safe_div(battery, battery_capacity) if battery_capacity > 0 else 1.0
    shortfall_trend = _safe_float(monitoring_signals.get("shortfall_trend"))

    if shortfall_ratio >= 0.15 or battery_ratio < 0.15:
        return {
            "alert_state": "CRITICAL",
            "reason": "Severe modeled energy gap or dangerously low storage buffer.",
            "review_priority": "Immediate human review of critical load, storage, and backup support.",
        }
    if shortfall_trend > 0 or shortfall_ratio >= 0.05 or grid_dependency >= 25:
        return {
            "alert_state": "WARNING",
            "reason": "Modeled energy gap or External Support Need Proxy is increasing.",
            "review_priority": "Review energy gap, External Support Need Proxy, and storage reserve assumptions.",
        }
    if renewable_ratio < 35 or grid_dependency >= 10 or battery_ratio < 0.5:
        return {
            "alert_state": "WATCH",
            "reason": "Operational monitoring signals indicate reduced margin or elevated dependency.",
            "review_priority": "Monitor renewable contribution, battery reserve, and External Support Need Proxy.",
        }
    return {
        "alert_state": "NORMAL",
        "reason": "No significant operational monitoring alert under current assumptions.",
        "review_priority": "Continue routine scenario review and preserve reserve margin.",
    }


def detect_operational_drift(current_state, baseline_state):
    """Detect baseline-vs-current operational drift."""
    drift_items = []
    current_demand = _safe_float(current_state.get("demand"))
    baseline_demand = _safe_float(baseline_state.get("demand"))
    current_stability = _safe_float(current_state.get("system_efficiency"))
    baseline_stability = _safe_float(baseline_state.get("system_efficiency"))
    current_grid = _safe_float(current_state.get("grid_dependency"))
    baseline_grid = _safe_float(baseline_state.get("grid_dependency"))
    current_gap = _safe_float(current_state.get("shortfall"))
    baseline_gap = _safe_float(baseline_state.get("shortfall"))
    current_renewable = _safe_float(current_state.get("renewable_supply"))
    baseline_renewable = _safe_float(baseline_state.get("renewable_supply"))

    demand_delta_pct = _safe_div(current_demand - baseline_demand, abs(baseline_demand)) * 100 if baseline_demand else 0.0
    renewable_delta_pct = _safe_div(current_renewable - baseline_renewable, abs(baseline_renewable)) * 100 if baseline_renewable else 0.0
    grid_delta = current_grid - baseline_grid
    stability_delta = current_stability - baseline_stability
    gap_delta = current_gap - baseline_gap

    if abs(demand_delta_pct) >= 5:
        drift_items.append(f"Demand changed by {demand_delta_pct:+.1f}% from baseline.")
    if abs(renewable_delta_pct) >= 5:
        drift_items.append(f"Renewable supply changed by {renewable_delta_pct:+.1f}% from baseline.")
    if grid_delta >= 5:
        drift_items.append(f"External Support Need Proxy increased by {grid_delta:+.1f} percentage points.")
    if stability_delta <= -5:
        drift_items.append(f"System Performance Score decreased by {stability_delta:+.1f} percentage points.")
    if gap_delta > 0:
        drift_items.append(f"Energy gap increased by {gap_delta:+.2f} MW.")

    return {
        "demand_delta_pct": round(demand_delta_pct, 2),
        "renewable_delta_pct": round(renewable_delta_pct, 2),
        "grid_dependency_delta": round(grid_delta, 2),
        "system_stability_delta": round(stability_delta, 2),
        "energy_gap_delta_mw": round(gap_delta, 2),
        "drift_detected": bool(drift_items),
        "drift_items": drift_items or ["No material operational drift detected from baseline under current assumptions."],
    }


def generate_monitoring_summary(context, current_state, baseline_state, monitoring_signals, alert_state, drift):
    """Generate export-ready monitoring summary text and data."""
    location = f"{context.get('city', '-')}, {context.get('country', '-')}"
    scenario = str(context.get("scenario", "-")).replace("_", " ").title()
    summary = (
        f"TAIVAS monitoring layer reports {alert_state.get('alert_state')} for {location} under {scenario}. "
        f"{alert_state.get('reason')} Human review is required before operational changes."
    )
    report_markdown = "\n".join([
        "# TAIVAS Operational Monitoring Report",
        "",
        f"- Location: {location}",
        f"- Scenario: {scenario}",
        f"- Alert State: {alert_state.get('alert_state')}",
        f"- Stress Stage: {monitoring_signals.get('stress_stage')}",
        "",
        "## Monitoring Summary",
        summary,
        "",
        "## What changed from baseline?",
        *[f"- {item}" for item in drift.get("drift_items", [])],
        "",
        "## Recommended Review Priority",
        alert_state.get("review_priority", "Human review required."),
        "",
        "## Safety Boundary",
        "Operational monitoring only. This report is decision support and does not guarantee real-world outcomes or control infrastructure.",
    ])
    return {
        "daily_monitoring_summary": summary,
        "executive_risk_snapshot": {
            "location": location,
            "scenario": scenario,
            "alert_state": alert_state.get("alert_state"),
            "stress_stage": monitoring_signals.get("stress_stage"),
            "review_priority": alert_state.get("review_priority"),
        },
        "report_markdown": report_markdown,
    }
