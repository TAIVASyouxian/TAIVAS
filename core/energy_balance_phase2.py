"""Dimensionally explicit TAIVAS energy-balance helpers.

The functions in this module are framework-independent. Power quantities use
megawatts (MW), battery state uses megawatt-hours (MWh), and energy transfers
are calculated over an explicit simulation interval in hours.
"""

from __future__ import annotations

from typing import Any, Mapping

from core.risk_engine import calculate_risk_tier


SIMULATION_INTERVAL_HOURS = 1.0
BATTERY_CHARGE_SHARE = 0.30
BATTERY_DISPATCH_CAPACITY_SHARE = 0.35


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator not in (0, 0.0) else 0.0


def normalize_mix(parts: Mapping[str, float]) -> dict[str, float]:
    total = sum(max(float(value), 0.0) for value in parts.values())
    if total <= 0:
        return {key: 0.0 for key in parts}
    return {key: max(float(value), 0.0) / total for key, value in parts.items()}


def calculate_system_performance_score(demand_mw: float, energy_gap_mw: float) -> float | None:
    """Return percentage of modeled demand served, or None when demand is zero."""
    demand_mw = float(demand_mw)
    if demand_mw <= 0:
        return None
    unmet_demand_ratio = clamp(float(energy_gap_mw) / demand_mw, 0.0, 1.0)
    served_demand_ratio = 1.0 - unmet_demand_ratio
    return 100.0 * clamp(served_demand_ratio, 0.0, 1.0)


def update_battery_state(
    *,
    battery_current_mwh: float,
    battery_capacity_mwh: float,
    renewable_surplus_power_mw: float,
    shortage_power_mw: float,
    scenario_battery_factor: float,
    battery_availability: float,
    lag_penalty: float,
    loss_rate: float,
    interval_hours: float = SIMULATION_INTERVAL_HOURS,
    charge_share: float = BATTERY_CHARGE_SHARE,
    dispatch_capacity_share: float = BATTERY_DISPATCH_CAPACITY_SHARE,
) -> dict[str, float]:
    """Update battery energy state using explicit MW-to-MWh conversion.

    The existing 30% surplus contribution, 35% capacity dispatch limit, and 4%
    transfer-loss assumption are retained. Loss is applied to accepted charging
    energy plus discharged energy over the interval.
    """
    interval_hours = max(float(interval_hours), 0.0)
    capacity_mwh = max(float(battery_capacity_mwh), 0.0)
    current_mwh = clamp(float(battery_current_mwh), 0.0, capacity_mwh)
    loss_rate = clamp(float(loss_rate), 0.0, 1.0)

    requested_charge_power_mw = max(float(renewable_surplus_power_mw), 0.0) * max(float(charge_share), 0.0)
    requested_charge_energy_mwh = requested_charge_power_mw * interval_hours
    headroom_mwh = max(capacity_mwh - current_mwh, 0.0)
    max_gross_charge_mwh = headroom_mwh / (1.0 - loss_rate) if loss_rate < 1.0 else 0.0
    charge_energy_mwh = min(requested_charge_energy_mwh, max_gross_charge_mwh)

    shortage_energy_mwh = max(float(shortage_power_mw), 0.0) * interval_hours
    dispatch_limit_energy_mwh = (
        capacity_mwh
        * max(float(dispatch_capacity_share), 0.0)
        * clamp(float(scenario_battery_factor), 0.0, 1.5)
        * clamp(float(battery_availability), 0.0, 1.0)
        * clamp(float(lag_penalty), 0.0, 1.0)
    )
    max_discharge_with_loss_mwh = current_mwh / (1.0 + loss_rate) if loss_rate < 1.0 else 0.0
    discharge_energy_mwh = min(shortage_energy_mwh, dispatch_limit_energy_mwh, max_discharge_with_loss_mwh)

    loss_energy_mwh = (charge_energy_mwh + discharge_energy_mwh) * loss_rate
    next_mwh = clamp(current_mwh + charge_energy_mwh - discharge_energy_mwh - loss_energy_mwh, 0.0, capacity_mwh)
    discharge_power_mw = discharge_energy_mwh / interval_hours if interval_hours > 0 else 0.0
    charge_power_mw = charge_energy_mwh / interval_hours if interval_hours > 0 else 0.0

    return {
        "battery_current_mwh": current_mwh,
        "battery_capacity_mwh": capacity_mwh,
        "charge_power_mw": charge_power_mw,
        "charge_energy_mwh": charge_energy_mwh,
        "discharge_power_mw": discharge_power_mw,
        "discharge_energy_mwh": discharge_energy_mwh,
        "loss_energy_mwh": loss_energy_mwh,
        "battery_next_mwh": next_mwh,
        "interval_hours": interval_hours,
    }


def compute_energy_supply_core(
    *,
    inputs: Mapping[str, Any],
    scenario_key: str,
    scenario: Mapping[str, float],
    failure_ratios: Mapping[str, float],
    reserve_recovery_lag_days: int,
    facility_factor: float,
    demand_per_capita_mw: float,
    solar_efficiency: float,
    wind_efficiency: float,
    geothermal_availability_factor: float,
    battery_loss_rate: float,
    interval_hours: float = SIMULATION_INTERVAL_HOURS,
) -> dict[str, Any]:
    """Run the audited deterministic TAIVAS balance with explicit units."""
    temperature = clamp(float(inputs["temperature"]), -30.0, 55.0)
    wind_speed = clamp(float(inputs["wind_speed"]), 0.0, 40.0)
    solar_radiation = clamp(float(inputs["solar_radiation"]), 0.0, 1200.0)
    precipitation = clamp(float(inputs["precipitation"]), 0.0, 500.0)
    humidity = clamp(float(inputs["humidity"]), 0.0, 100.0)
    population = int(clamp(float(inputs["population"]), 1000.0, 50000000.0))
    solar_capacity = clamp(float(inputs["solar_capacity"]), 0.0, 5000.0)
    wind_capacity = clamp(float(inputs["wind_capacity"]), 0.0, 5000.0)
    geothermal_capacity = clamp(float(inputs["geothermal_capacity"]), 0.0, 5000.0)
    hydro_capacity = clamp(float(inputs["hydro_capacity"]), 0.0, 5000.0)
    battery_capacity_mwh = clamp(float(inputs["battery_capacity"]), 0.0, 10000.0)

    base_demand_mw = population * float(demand_per_capita_mw)
    heat_stress = max(0.0, temperature - 24.0) * 0.012
    cold_stress = max(0.0, 10.0 - temperature) * 0.010
    weather_factor = clamp(float(scenario.get("demand", 1.0)) * (1.0 + heat_stress + cold_stress), 0.65, 2.25)
    demand_mw = base_demand_mw * weather_factor * float(facility_factor)

    solar_resource_factor = clamp(solar_radiation / 1000.0, 0.0, 1.20)
    wind_resource_factor = clamp(wind_speed / 12.0, 0.0, 1.50)
    hydro_availability_factor = clamp(0.45 + precipitation / 500.0 * 0.35, 0.15, 0.95)
    solar_availability = 1.0 - clamp(float(failure_ratios.get("solar", 0.0)), 0.0, 1.0)
    wind_availability = 1.0 - clamp(float(failure_ratios.get("wind", 0.0)), 0.0, 1.0)
    geo_availability = 1.0 - clamp(float(failure_ratios.get("geothermal", 0.0)), 0.0, 1.0)
    hydro_availability = 1.0 - clamp(float(failure_ratios.get("hydro", 0.0)), 0.0, 1.0)
    battery_availability = 1.0 - clamp(float(failure_ratios.get("battery", 0.0)), 0.0, 1.0)

    solar_supply_mw = solar_capacity * solar_resource_factor * float(solar_efficiency) * float(scenario.get("solar", 1.0)) * solar_availability
    wind_supply_mw = wind_capacity * wind_resource_factor * float(wind_efficiency) * float(scenario.get("wind", 1.0)) * wind_availability
    hydro_supply_mw = hydro_capacity * hydro_availability_factor * float(scenario.get("hydro", 1.0)) * hydro_availability
    geothermal_supply_mw = geothermal_capacity * float(geothermal_availability_factor) * geo_availability
    renewable_supply_mw = solar_supply_mw + wind_supply_mw + hydro_supply_mw + geothermal_supply_mw

    lag_penalty = max(0.70, 1.0 - max(int(reserve_recovery_lag_days), 0) * 0.015)
    battery = update_battery_state(
        battery_current_mwh=inputs.get("battery_current", battery_capacity_mwh),
        battery_capacity_mwh=battery_capacity_mwh,
        renewable_surplus_power_mw=max(renewable_supply_mw - demand_mw, 0.0),
        shortage_power_mw=max(demand_mw - renewable_supply_mw, 0.0),
        scenario_battery_factor=float(scenario.get("battery", 1.0)),
        battery_availability=battery_availability,
        lag_penalty=lag_penalty,
        loss_rate=battery_loss_rate,
        interval_hours=interval_hours,
    )

    grid_support_mw = clamp(float(inputs.get("grid_support", 0.0)), 0.0, demand_mw)
    final_supply_mw = renewable_supply_mw + battery["discharge_power_mw"] + grid_support_mw
    energy_gap_mw = max(demand_mw - final_supply_mw, 0.0)
    unmet_demand_ratio = safe_div(energy_gap_mw, demand_mw) if demand_mw > 0 else 0.0
    system_performance_score = calculate_system_performance_score(demand_mw, energy_gap_mw)
    external_support_need_proxy = unmet_demand_ratio * 100.0 if demand_mw > 0 else 0.0
    risk_tier = calculate_risk_tier(energy_gap_mw, demand_mw)
    renewable_ratio = safe_div(renewable_supply_mw, final_supply_mw) * 100.0 if final_supply_mw > 0 else 0.0

    actual_mix_raw = {
        "Solar": solar_supply_mw,
        "Wind": wind_supply_mw,
        "Geothermal": geothermal_supply_mw,
        "Hydro": hydro_supply_mw,
    }
    installed_mix_raw = {
        "Solar": solar_capacity,
        "Wind": wind_capacity,
        "Geothermal": geothermal_capacity,
        "Hydro": hydro_capacity,
    }
    actual_mix_pct = {key: value * 100.0 for key, value in normalize_mix(actual_mix_raw).items()}
    installed_mix_pct = {key: value * 100.0 for key, value in normalize_mix(installed_mix_raw).items()}
    capacity_factors = {
        "Solar": round(clamp(solar_resource_factor * float(solar_efficiency), 0.0, 1.0) * 100.0, 1),
        "Wind": round(clamp(wind_resource_factor * float(wind_efficiency), 0.0, 1.0) * 100.0, 1),
        "Geothermal": round(float(geothermal_availability_factor) * 100.0, 1),
        "Hydro": round(hydro_availability_factor * 100.0, 1),
    }
    dominant_source = max(actual_mix_raw, key=actual_mix_raw.get) if renewable_supply_mw > 0 else "None"
    score_value = round(system_performance_score, 2) if system_performance_score is not None else None

    return {
        "demand": round(demand_mw, 2),
        "renewable_supply": round(renewable_supply_mw, 2),
        "final_supply": round(final_supply_mw, 2),
        "battery_levels": round(battery["battery_next_mwh"], 2),
        "shortfall": round(energy_gap_mw, 2),
        "renewable_ratio": round(renewable_ratio, 2),
        "system_efficiency": score_value,
        "grid_dependency": round(external_support_need_proxy, 2),
        "system_performance_score": score_value,
        "external_support_need_proxy": round(external_support_need_proxy, 2),
        "unmet_demand_ratio": round(unmet_demand_ratio, 6),
        "risk_tier": risk_tier,
        "grid_support": round(grid_support_mw, 2),
        "battery_discharge": round(battery["discharge_power_mw"], 2),
        "battery_discharge_energy_mwh": round(battery["discharge_energy_mwh"], 4),
        "battery_charge": round(battery["charge_power_mw"], 2),
        "battery_charge_energy_mwh": round(battery["charge_energy_mwh"], 4),
        "battery_losses_mwh": round(battery["loss_energy_mwh"], 4),
        "battery_current_mwh": round(battery["battery_current_mwh"], 4),
        "simulation_interval_hours": float(interval_hours),
        "actual_mix_pct": actual_mix_pct,
        "installed_mix_pct": installed_mix_pct,
        "actual_mix_mw": {key: round(value, 2) for key, value in actual_mix_raw.items()},
        "installed_mix_mw": {key: round(value, 2) for key, value in installed_mix_raw.items()},
        "capacity_factors": capacity_factors,
        "dominant_source": dominant_source,
        "humidity_input_pct": humidity,
    }
