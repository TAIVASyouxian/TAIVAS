"""
TAIVAS recommendations module
Rule-based recommendations for resilience and energy security interpretation.
"""

from typing import Dict, List


def recommendation_lines(results: Dict[str, float], energy_security_scenario: str = "normal") -> List[str]:
    lines: List[str] = []

    shortfall = float(results.get("shortfall", 0.0))
    renewable_ratio = float(results.get("renewable_ratio", 0.0))
    battery_levels = float(results.get("battery_levels", 0.0))
    grid_dependency = float(results.get("grid_dependency", 0.0))
    import_disruption_score = float(results.get("import_disruption_score", 0.0))
    reserve_days_remaining = float(results.get("reserve_days_remaining", 0.0))
    critical_load_coverage = float(results.get("critical_load_coverage", 100.0))
    recovery_time_estimate = float(results.get("recovery_time_estimate", 0.0))

    if shortfall <= 0:
        lines.append("System balance is currently stable under the selected scenario. Maintain monitoring and compare against more severe weather and security conditions.")
    else:
        lines.append(f"Current modeled shortfall is {shortfall:.2f} MW. Consider increasing dispatchable support, storage, or reducing demand in survival mode.")

    if renewable_ratio < 60:
        lines.append(f"Renewable ratio is {renewable_ratio:.1f}%, which suggests weaker self-reliance. Review solar, wind, hydro, and geothermal balance for this scenario.")
    else:
        lines.append(f"Renewable ratio remains {renewable_ratio:.1f}%, indicating comparatively strong renewable contribution in the current setup.")

    if battery_levels < 0.2 * max(battery_levels + results.get("shortfall", 0.0), 1.0):
        lines.append("Battery headroom is limited after dispatch. Consider increasing battery capacity or reducing early-hour discharge pressure.")
    else:
        lines.append("Battery reserve remains available after dispatch, which improves near-term resilience against follow-on shocks.")

    if grid_dependency > 15:
        lines.append(f"Grid dependency is {grid_dependency:.1f}%, which may become a vulnerability during external disruption. Test lower-import or higher-storage configurations.")
    else:
        lines.append(f"Grid dependency is relatively low at {grid_dependency:.1f}%, which supports resilience under constrained external supply conditions.")

    if import_disruption_score >= 60:
        lines.append(f"Import disruption exposure is high at {import_disruption_score:.1f}%. Strengthen strategic reserves and stress-test shipping and infrastructure bottlenecks.")
    elif import_disruption_score >= 35:
        lines.append(f"Import disruption exposure is moderate at {import_disruption_score:.1f}%. Compare this setup against a more conservative reserve strategy.")
    else:
        lines.append(f"Import disruption exposure remains manageable at {import_disruption_score:.1f}% under the selected energy security scenario.")

    if reserve_days_remaining < 7:
        lines.append(f"Reserve endurance is low at {reserve_days_remaining:.1f} days. Consider raising strategic reserve days or lowering import dependence.")
    else:
        lines.append(f"Reserve endurance is {reserve_days_remaining:.1f} days, giving the system a workable security buffer.")

    if critical_load_coverage < 100:
        lines.append(f"Critical-load coverage falls to {critical_load_coverage:.1f}%. Prioritize medical, heating, water, and communications loads in degraded operation mode.")
    else:
        lines.append("Critical-load coverage remains intact in the current simulation, which is favorable for essential-service continuity.")

    if recovery_time_estimate >= 7:
        lines.append(f"Estimated recovery time is {recovery_time_estimate:.1f} days. Build contingency plans for prolonged disruption and slower restoration.")
    else:
        lines.append(f"Estimated recovery time is {recovery_time_estimate:.1f} days under the selected disruption profile.")

    if energy_security_scenario not in ("normal", ""):
        lines.append(f"The active energy security scenario is '{energy_security_scenario}', so all recommendations should be interpreted within that disruption context.")

    return lines
