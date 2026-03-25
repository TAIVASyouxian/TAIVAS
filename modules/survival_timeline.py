"""
TAIVAS V1.3 survival timeline module
Minimal viable time-sequence simulator for estimating how long the system can hold.
"""

from typing import Dict, List


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def build_hourly_demand_profile(
    base_demand: float,
    simulation_hours: int = 24,
    weather_scenario: str = "normal",
) -> List[float]:
    simulation_hours = int(clamp(simulation_hours, 1, 168))
    demand_profile: List[float] = []

    scenario_multiplier = {
        "normal": 1.00,
        "heat_wave": 1.15,
        "storm": 1.06,
        "cold_wave": 1.12,
        "blizzard": 1.18,
        "typhoon": 1.10,
    }.get(weather_scenario, 1.00)

    daily_shape = [
        0.88, 0.85, 0.83, 0.82, 0.84, 0.88,
        0.95, 1.02, 1.08, 1.12, 1.15, 1.18,
        1.20, 1.18, 1.16, 1.14, 1.12, 1.10,
        1.08, 1.06, 1.02, 0.98, 0.94, 0.90,
    ]

    for h in range(simulation_hours):
        hour_in_day = h % 24
        demand_profile.append(round(base_demand * daily_shape[hour_in_day] * scenario_multiplier, 2))

    return demand_profile


def build_hourly_supply_profile(
    renewable_supply: float,
    simulation_hours: int = 24,
    weather_scenario: str = "normal",
    primary_supply_failure_ratio: float = 0.0,
) -> List[float]:
    simulation_hours = int(clamp(simulation_hours, 1, 168))
    primary_supply_failure_ratio = clamp(primary_supply_failure_ratio, 0.0, 1.0)

    supply_profile: List[float] = []

    scenario_multiplier = {
        "normal": 1.00,
        "heat_wave": 1.03,
        "storm": 0.86,
        "cold_wave": 0.90,
        "blizzard": 0.72,
        "typhoon": 0.65,
    }.get(weather_scenario, 1.00)

    daily_shape = [
        0.28, 0.26, 0.24, 0.23, 0.25, 0.30,
        0.42, 0.58, 0.72, 0.84, 0.93, 0.98,
        1.00, 0.98, 0.94, 0.88, 0.78, 0.66,
        0.54, 0.44, 0.36, 0.32, 0.30, 0.29,
    ]

    for h in range(simulation_hours):
        hour_in_day = h % 24
        gross_supply = renewable_supply * daily_shape[hour_in_day] * scenario_multiplier
        net_supply = gross_supply * (1.0 - primary_supply_failure_ratio)
        supply_profile.append(round(max(net_supply, 0.0), 2))

    return supply_profile


def simulate_survival_timeline(
    demand: float,
    renewable_supply: float,
    battery_capacity: float,
    strategic_reserve_days: float,
    critical_load_share: float,
    weather_scenario: str = "normal",
    simulation_hours: int = 24,
    primary_supply_failure_ratio: float = 0.0,
    reserve_energy_per_day: float = 120.0,
    survival_mode: str = "full_load",
) -> Dict[str, object]:
    simulation_hours = int(clamp(simulation_hours, 1, 168))
    critical_load_share = clamp(critical_load_share, 0.0, 1.0)
    primary_supply_failure_ratio = clamp(primary_supply_failure_ratio, 0.0, 1.0)

    demand_profile = build_hourly_demand_profile(
        base_demand=demand,
        simulation_hours=simulation_hours,
        weather_scenario=weather_scenario,
    )
    supply_profile = build_hourly_supply_profile(
        renewable_supply=renewable_supply,
        simulation_hours=simulation_hours,
        weather_scenario=weather_scenario,
        primary_supply_failure_ratio=primary_supply_failure_ratio,
    )

    battery_level = max(battery_capacity, 0.0)
    reserve_energy = max(strategic_reserve_days, 0.0) * max(reserve_energy_per_day, 0.0)

    hours_until_shortfall = None
    hours_until_critical_failure = None
    battery_depletion_hour = None
    reserve_depletion_hour = None

    rows: List[Dict[str, float]] = []

    for hour in range(simulation_hours):
        raw_demand = demand_profile[hour]
        target_demand = raw_demand if survival_mode == "full_load" else raw_demand * critical_load_share

        renewable_now = supply_profile[hour]
        remaining_gap = max(target_demand - renewable_now, 0.0)

        battery_used = min(battery_level, remaining_gap)
        battery_level -= battery_used
        remaining_gap -= battery_used

        reserve_used = min(reserve_energy, remaining_gap)
        reserve_energy -= reserve_used
        remaining_gap -= reserve_used

        final_hourly_supply = renewable_now + battery_used + reserve_used
        shortfall_now = max(target_demand - final_hourly_supply, 0.0)

        critical_demand = raw_demand * critical_load_share

        if shortfall_now > 0 and hours_until_shortfall is None:
            hours_until_shortfall = hour

        if final_hourly_supply < critical_demand and hours_until_critical_failure is None:
            hours_until_critical_failure = hour

        if battery_level <= 0 and battery_depletion_hour is None:
            battery_depletion_hour = hour

        if reserve_energy <= 0 and reserve_depletion_hour is None:
            reserve_depletion_hour = hour

        rows.append(
            {
                "hour": hour,
                "raw_demand": round(raw_demand, 2),
                "target_demand": round(target_demand, 2),
                "renewable_supply": round(renewable_now, 2),
                "battery_used": round(battery_used, 2),
                "reserve_used": round(reserve_used, 2),
                "final_supply": round(final_hourly_supply, 2),
                "shortfall": round(shortfall_now, 2),
                "battery_level": round(battery_level, 2),
                "reserve_energy": round(reserve_energy, 2),
            }
        )

    if hours_until_shortfall is None:
        hours_until_shortfall = simulation_hours

    if hours_until_critical_failure is None:
        hours_until_critical_failure = simulation_hours

    if battery_depletion_hour is None:
        battery_depletion_hour = simulation_hours

    if reserve_depletion_hour is None:
        reserve_depletion_hour = simulation_hours

    survival_mode_duration = min(hours_until_shortfall, hours_until_critical_failure)

    return {
        "rows": rows,
        "hours_until_shortfall": hours_until_shortfall,
        "hours_until_critical_failure": hours_until_critical_failure,
        "battery_depletion_hour": battery_depletion_hour,
        "reserve_depletion_hour": reserve_depletion_hour,
        "survival_mode_duration": survival_mode_duration,
    }
