"""
TAIVAS V1.3 energy security layer
Directly pluggable helpers for import dependency, reserve days,
critical load coverage, and geopolitical disruption scenarios.
"""

from typing import Dict, Tuple


ENERGY_SECURITY_SCENARIOS: Dict[str, Dict[str, float]] = {
    "normal": {
        "fuel_price_index": 1.00,
        "shipping_access_factor": 1.00,
        "infrastructure_factor": 1.00,
        "import_penalty": 1.00,
    },
    "fuel_price_shock": {
        "fuel_price_index": 1.35,
        "shipping_access_factor": 1.00,
        "infrastructure_factor": 1.00,
        "import_penalty": 1.08,
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
    "compound_crisis": {
        "fuel_price_index": 1.60,
        "shipping_access_factor": 0.65,
        "infrastructure_factor": 0.72,
        "import_penalty": 1.25,
    },
    "high_risk": {
        "fuel_price_index": 1.45,
        "shipping_access_factor": 0.76,
        "infrastructure_factor": 0.82,
        "import_penalty": 1.16,
    },
    "severe_disruption": {
        "fuel_price_index": 1.72,
        "shipping_access_factor": 0.58,
        "infrastructure_factor": 0.66,
        "import_penalty": 1.30,
    },
}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def get_energy_security_profile(scenario_key: str) -> Dict[str, float]:
    return ENERGY_SECURITY_SCENARIOS.get(scenario_key, ENERGY_SECURITY_SCENARIOS["normal"])


def compute_import_disruption_score(
    import_dependency: float,
    shipping_dependency: float,
    profile: Dict[str, float],
) -> float:
    import_dependency = clamp(import_dependency, 0.0, 1.0)
    shipping_dependency = clamp(shipping_dependency, 0.0, 1.0)

    exposure = import_dependency * 0.65 + shipping_dependency * 0.35
    severity = (
        (2.0 - profile["shipping_access_factor"]) * 0.45
        + (2.0 - profile["infrastructure_factor"]) * 0.25
        + (profile["fuel_price_index"] - 1.0) * 0.30
    )
    return round(clamp(exposure * severity * 100, 0, 100), 2)


def compute_reserve_days_remaining(
    strategic_reserve_days: float,
    import_dependency: float,
    profile: Dict[str, float],
    reserve_recovery_lag_days: float = 0.0,
) -> float:
    strategic_reserve_days = clamp(strategic_reserve_days, 0.0, 365.0)
    import_dependency = clamp(import_dependency, 0.0, 1.0)
    reserve_recovery_lag_days = clamp(reserve_recovery_lag_days, 0.0, 60.0)

    daily_draw = profile["import_penalty"] * (0.55 + import_dependency * 0.75)
    days_remaining = strategic_reserve_days / daily_draw if daily_draw > 0 else strategic_reserve_days
    days_remaining -= reserve_recovery_lag_days * 0.15
    return round(max(days_remaining, 0.0), 2)


def compute_fuel_cost_stress(profile: Dict[str, float]) -> float:
    return round(max((profile["fuel_price_index"] - 1.0) * 100, 0.0), 2)


def compute_critical_load_coverage(
    final_supply: float,
    demand: float,
    critical_load_share: float,
) -> float:
    demand = max(demand, 0.0)
    final_supply = max(final_supply, 0.0)
    critical_load_share = clamp(critical_load_share, 0.0, 1.0)

    critical_demand = demand * critical_load_share
    if critical_demand <= 0:
        return 100.0
    coverage = (final_supply / critical_demand) * 100
    return round(clamp(coverage, 0, 100), 2)


def estimate_recovery_time(
    profile: Dict[str, float],
    infrastructure_damage_ratio: float,
    reserve_recovery_lag_days: float = 0.0,
) -> float:
    infrastructure_damage_ratio = clamp(infrastructure_damage_ratio, 0.0, 1.0)
    reserve_recovery_lag_days = clamp(reserve_recovery_lag_days, 0.0, 60.0)
    days = (
        2.0
        + (1.0 - profile["shipping_access_factor"]) * 8.0
        + (1.0 - profile["infrastructure_factor"]) * 7.0
        + infrastructure_damage_ratio * 10.0
        + reserve_recovery_lag_days * 0.25
    )
    return round(days, 1)


def apply_energy_security_layer(
    base_results: Dict[str, float],
    scenario_key: str,
    import_dependency: float,
    strategic_reserve_days: float,
    critical_load_share: float,
    shipping_dependency: float = 0.8,
    infrastructure_damage_ratio: float = 0.0,
    reserve_recovery_lag_days: float = 0.0,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    profile = get_energy_security_profile(scenario_key)

    import_disruption_score = compute_import_disruption_score(
        import_dependency=import_dependency,
        shipping_dependency=shipping_dependency,
        profile=profile,
    )

    reserve_days_remaining = compute_reserve_days_remaining(
        strategic_reserve_days=strategic_reserve_days,
        import_dependency=import_dependency,
        profile=profile,
        reserve_recovery_lag_days=reserve_recovery_lag_days,
    )

    fuel_cost_stress = compute_fuel_cost_stress(profile)

    critical_load_coverage = compute_critical_load_coverage(
        final_supply=base_results.get("final_supply", 0.0),
        demand=base_results.get("demand", 0.0),
        critical_load_share=critical_load_share,
    )

    recovery_time_estimate = estimate_recovery_time(
        profile=profile,
        infrastructure_damage_ratio=infrastructure_damage_ratio,
        reserve_recovery_lag_days=reserve_recovery_lag_days,
    )

    updated = dict(base_results)
    updated["import_disruption_score"] = import_disruption_score
    updated["reserve_days_remaining"] = reserve_days_remaining
    updated["fuel_cost_stress"] = fuel_cost_stress
    updated["critical_load_coverage"] = critical_load_coverage
    updated["recovery_time_estimate"] = recovery_time_estimate
    updated["reserve_recovery_lag_days"] = round(clamp(reserve_recovery_lag_days, 0.0, 60.0), 1)

    return updated, profile
