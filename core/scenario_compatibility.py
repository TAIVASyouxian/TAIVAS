"""Scenario compatibility guardrails for TAIVAS.

This module is validation-only. It does not change scenario formulas or
simulation outputs. It only helps the UI present plausible regional choices and
labels hypothetical stress tests clearly.
"""


ALL_SCENARIOS = ["normal", "heat_wave", "storm", "cold_wave", "blizzard", "typhoon"]

COUNTRY_SCENARIO_MAP = {
    "Taiwan": ["normal", "heat_wave", "storm", "typhoon"],
    "Sweden": ["normal", "cold_wave", "blizzard", "storm", "heat_wave"],
    "Finland": ["normal", "cold_wave", "blizzard", "storm", "heat_wave"],
    "Germany": ["normal", "heat_wave", "cold_wave", "storm"],
    "Iceland": ["normal", "cold_wave", "blizzard", "storm"],
    "Norway": ["normal", "cold_wave", "blizzard", "storm", "heat_wave"],
    "Denmark": ["normal", "storm", "cold_wave", "heat_wave"],
    "United Kingdom": ["normal", "storm", "cold_wave", "heat_wave"],
    "Ireland": ["normal", "storm", "cold_wave", "heat_wave"],
    "Spain": ["normal", "heat_wave", "storm"],
    "Italy": ["normal", "heat_wave", "storm", "cold_wave"],
    "Portugal": ["normal", "heat_wave", "storm"],
    "France": ["normal", "heat_wave", "cold_wave", "storm"],
    "Netherlands": ["normal", "storm", "cold_wave", "heat_wave"],
    "Belgium": ["normal", "storm", "cold_wave", "heat_wave"],
    "Austria": ["normal", "cold_wave", "blizzard", "storm", "heat_wave"],
    "Switzerland": ["normal", "cold_wave", "blizzard", "storm", "heat_wave"],
    "Poland": ["normal", "cold_wave", "blizzard", "storm", "heat_wave"],
    "Czech Republic": ["normal", "cold_wave", "storm", "heat_wave"],
    "USA": ["normal", "heat_wave", "storm", "cold_wave", "blizzard"],
}


def _normalize_mode(mode):
    mode = str(mode or "General Mode").strip().lower()
    if "advanced" in mode:
        return "Advanced Stress Testing"
    return "General Mode"


def get_allowed_scenarios(country, city=None, mode="General Mode"):
    """Return scenario keys allowed for the selected country/city and mode."""
    normalized_mode = _normalize_mode(mode)
    if normalized_mode == "Advanced Stress Testing":
        return list(ALL_SCENARIOS)
    return list(COUNTRY_SCENARIO_MAP.get(str(country), ALL_SCENARIOS))


def evaluate_scenario_plausibility(country, city, scenario):
    """Return HIGH/MEDIUM/LOW plausibility for a country/city/scenario pair."""
    scenario = str(scenario)
    allowed = COUNTRY_SCENARIO_MAP.get(str(country))
    if scenario == "normal":
        return {
            "plausibility": "HIGH",
            "is_plausible": True,
            "reason": "Normal baseline scenario is available for all locations.",
        }
    if allowed is None:
        return {
            "plausibility": "MEDIUM",
            "is_plausible": True,
            "reason": "No regional compatibility profile is defined, so TAIVAS allows the scenario with general decision-support caution.",
        }
    if scenario in allowed:
        return {
            "plausibility": "HIGH",
            "is_plausible": True,
            "reason": "Scenario is regionally plausible for the selected location profile.",
        }
    return {
        "plausibility": "LOW",
        "is_plausible": False,
        "reason": "This scenario is not typical for the selected location and should be interpreted as a hypothetical stress test, not a normal regional risk.",
    }


def build_scenario_warning(country, city, scenario, mode="General Mode"):
    """Build user-facing warning metadata for scenario compatibility."""
    normalized_mode = _normalize_mode(mode)
    evaluation = evaluate_scenario_plausibility(country, city, scenario)
    if evaluation["plausibility"] == "LOW":
        return {
            "show_warning": True,
            "label": "Scenario Plausibility: LOW",
            "message": evaluation["reason"],
            "mode_note": "Low historical plausibility scenario. This is for advanced stress testing only." if normalized_mode == "Advanced Stress Testing" else "",
        }
    if evaluation["plausibility"] == "MEDIUM":
        return {
            "show_warning": True,
            "label": "Scenario Plausibility: MEDIUM",
            "message": evaluation["reason"],
            "mode_note": "Interpret as a generalized scenario because no country-specific compatibility profile is available.",
        }
    return {
        "show_warning": False,
        "label": "Scenario Plausibility: HIGH",
        "message": evaluation["reason"],
        "mode_note": "",
    }
