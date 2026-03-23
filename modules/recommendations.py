"""
TAIVAS recommendations module
Rule-based recommendation helpers for dashboard explanation.
"""

from typing import Dict, List


def recommendation_lines(results: Dict[str, float], scenario_key: str) -> List[str]:
    lines: List[str] = []

    if results.get("shortfall", 0) > 0:
        lines.append("Increase storage and reserve capacity to reduce supply gaps under stressed conditions.")

    if results.get("grid_dependency", 0) > 15:
        lines.append("Grid dependency is elevated. Strengthen local diversified supply and backup planning.")

    if results.get("renewable_ratio", 100) < 60:
        lines.append("Renewable contribution is modest. Consider increasing solar, wind, hydro, or geothermal capacity.")

    if scenario_key in {"typhoon", "storm", "blizzard"}:
        lines.append("Severe-weather scenario selected. Prioritize resilience, backup dispatch, and critical-load continuity.")

    if scenario_key in {"fuel_price_shock", "strait_disruption", "lng_terminal_attack", "regional_infrastructure_damage"}:
        lines.append("Geopolitical stress detected. Review import exposure, reserve planning, and fuel diversification strategy.")

    if not lines:
        lines.append("System balance is currently stable. Maintain monitoring and compare against stress scenarios.")

    return lines
