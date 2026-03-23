"""
TAIVAS geopolitics module
Helpers for modeling geopolitical energy-security shocks.
"""

from typing import Dict


GEOPOLITICAL_SCENARIOS: Dict[str, Dict[str, float]] = {
    "fuel_price_shock": {
        "fuel_price_index": 1.35,
        "shipping_access_factor": 1.00,
        "infrastructure_factor": 1.00,
        "import_penalty": 1.10,
    },
    "strait_disruption": {
        "fuel_price_index": 1.50,
        "shipping_access_factor": 0.72,
        "infrastructure_factor": 1.00,
        "import_penalty": 1.18,
    },
    "lng_terminal_attack": {
        "fuel_price_index": 1.42,
        "shipping_access_factor": 0.84,
        "infrastructure_factor": 0.78,
        "import_penalty": 1.15,
    },
    "regional_infrastructure_damage": {
        "fuel_price_index": 1.28,
        "shipping_access_factor": 0.88,
        "infrastructure_factor": 0.80,
        "import_penalty": 1.12,
    },
}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def get_geopolitical_profile(scenario_key: str) -> Dict[str, float]:
    return GEOPOLITICAL_SCENARIOS.get(
        scenario_key,
        {
            "fuel_price_index": 1.00,
            "shipping_access_factor": 1.00,
            "infrastructure_factor": 1.00,
            "import_penalty": 1.00,
        },
    )


def compute_import_disruption_score(
    oil_import_dependency: float,
    gas_import_dependency: float,
    lng_import_dependency: float,
    critical_shipping_dependency: float,
    geopolitical_profile: Dict[str, float],
) -> float:
    exposure = (
        oil_import_dependency * 0.25
        + gas_import_dependency * 0.25
        + lng_import_dependency * 0.25
        + critical_shipping_dependency * 0.25
    )

    severity = (
        (2.0 - geopolitical_profile["shipping_access_factor"]) * 0.45
        + (2.0 - geopolitical_profile["infrastructure_factor"]) * 0.25
        + (geopolitical_profile["fuel_price_index"] - 1.0) * 0.30
    )

    score = exposure * severity * 100
    return round(clamp(score, 0, 100), 2)


def apply_geopolitical_adjustment(
    base_results: Dict[str, float],
    geopolitical_profile: Dict[str, float],
    import_dependency: float,
    strategic_reserve_days: float,
    critical_load_share: float,
) -> Dict[str, float]:
    import_dependency = clamp(import_dependency, 0.0, 1.0)
    strategic_reserve_days = clamp(strategic_reserve_days, 0.0, 180.0)
    critical_load_share = clamp(critical_load_share, 0.0, 1.0)

    reserve_buffer = min(strategic_reserve_days / 30.0, 1.0)
    shortage_multiplier = geopolitical_profile["import_penalty"] * import_dependency * (1.0 - 0.35 * reserve_buffer)

    added_shortfall = base_results.get("demand", 0) * 0.08 * shortage_multiplier
    adjusted_shortfall = max(base_results.get("shortfall", 0), added_shortfall)
    adjusted_final_supply = max(base_results.get("final_supply", 0) - added_shortfall, 0)

    critical_load_coverage = clamp(
        100 - adjusted_shortfall * (0.45 + critical_load_share * 0.25),
        0,
        100,
    )

    fuel_cost_stress = round((geopolitical_profile["fuel_price_index"] - 1.0) * 100, 2)
    reserve_days_remaining = round(max(strategic_reserve_days - shortage_multiplier * 5.0, 0), 2)
    recovery_time_estimate = round(
        2 + (1.0 - geopolitical_profile["shipping_access_factor"]) * 10
        + (1.0 - geopolitical_profile["infrastructure_factor"]) * 8,
        1,
    )

    updated = dict(base_results)
    updated["final_supply"] = round(adjusted_final_supply, 2)
    updated["shortfall"] = round(adjusted_shortfall, 2)
    updated["critical_load_coverage"] = round(critical_load_coverage, 2)
    updated["fuel_cost_stress"] = fuel_cost_stress
    updated["reserve_days_remaining"] = reserve_days_remaining
    updated["recovery_time_estimate"] = recovery_time_estimate

    return updated
