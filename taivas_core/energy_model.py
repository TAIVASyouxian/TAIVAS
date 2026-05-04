"""
TAIVAS Core Energy Model V10.2

Independent, internationally aligned decision-support model.

Model basis:
- Solar: PVWatts / SAM-style simplified PV output
- Wind: IEC 61400-style power-curve concept
- Demand: ASHRAE-style heating/cooling degree-day load sensitivity
- Storage: standard energy-balance support logic
- Wildfire: energy-system impact layer, not wildfire propagation modeling

Important:
TAIVAS is a scenario-based decision-support simulator.
It is not a certified engineering design tool and does not provide guaranteed prediction.
"""

from __future__ import annotations

from typing import Dict, Any, Tuple


def clamp(value: float, low: float, high: float) -> float:
    try:
        value = float(value)
    except Exception:
        value = low
    return max(low, min(high, value))


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    try:
        denominator = float(denominator)
        if denominator == 0:
            return default
        return float(numerator) / denominator
    except Exception:
        return default


SCENARIO_PROFILES: Dict[str, Dict[str, float]] = {
    "normal": {
        "demand": 1.00, "solar": 1.00, "wind": 1.00, "geo": 1.00, "geothermal": 1.00,
        "hydro": 1.00, "battery": 1.00, "grid": 1.00, "transmission_loss": 0.02,
    },
    "heat_wave": {
        "demand": 1.18, "solar": 0.96, "wind": 0.92, "geo": 1.00, "geothermal": 1.00,
        "hydro": 0.94, "battery": 0.96, "grid": 1.08, "transmission_loss": 0.04,
    },
    "storm": {
        "demand": 1.10, "solar": 0.70, "wind": 0.82, "geo": 0.98, "geothermal": 0.98,
        "hydro": 0.96, "battery": 0.94, "grid": 1.18, "transmission_loss": 0.08,
    },
    "cold_wave": {
        "demand": 1.22, "solar": 0.82, "wind": 0.95, "geo": 1.02, "geothermal": 1.02,
        "hydro": 0.92, "battery": 0.93, "grid": 1.15, "transmission_loss": 0.05,
    },
    "blizzard": {
        "demand": 1.35, "solar": 0.48, "wind": 0.72, "geo": 1.03, "geothermal": 1.03,
        "hydro": 0.88, "battery": 0.88, "grid": 1.25, "transmission_loss": 0.10,
    },
    "typhoon": {
        "demand": 1.16, "solar": 0.55, "wind": 0.62, "geo": 0.98, "geothermal": 0.98,
        "hydro": 0.90, "battery": 0.90, "grid": 1.32, "transmission_loss": 0.14,
    },
    "wildfire": {
        "demand": 1.14, "solar": 0.65, "wind": 0.90, "geo": 0.99, "geothermal": 0.99,
        "hydro": 0.88, "battery": 0.91, "grid": 1.35, "transmission_loss": 0.16,
    },
}


MODEL_ALIGNMENT_NOTES = {
    "solar": "PVWatts / SAM-style simplified PV output: capacity × irradiance ratio × temperature derate × system-loss derate.",
    "wind": "IEC 61400-style wind-turbine power-curve concept with cut-in, rated, and cut-out behavior.",
    "demand": "ASHRAE-style heating/cooling degree-day load sensitivity.",
    "battery": "Standard storage energy-balance support logic.",
    "wildfire": "Wildfire is treated as an energy-system impact scenario: smoke attenuation, transmission disruption, and grid-isolation pressure. It is not a wildfire propagation model.",
    "limitation": "Decision-support simulation only; not a certified engineering model or guaranteed prediction system.",
}


def _scenario(scenario_key: str) -> Dict[str, float]:
    profile = dict(SCENARIO_PROFILES.get(str(scenario_key), SCENARIO_PROFILES["normal"]))
    # Backward compatibility: old code may expect both geo and geothermal.
    profile.setdefault("geo", profile.get("geothermal", 1.0))
    profile.setdefault("geothermal", profile.get("geo", 1.0))
    for key in ["demand", "solar", "wind", "geo", "geothermal", "hydro", "battery", "grid", "transmission_loss"]:
        profile.setdefault(key, 1.0 if key != "transmission_loss" else 0.02)
    return profile


def _failure(failure_ratios: Dict[str, float], *names: str) -> float:
    if not failure_ratios:
        return 0.0
    for name in names:
        if name in failure_ratios:
            return clamp(failure_ratios.get(name, 0.0), 0.0, 1.0)
    return 0.0


def _base_demand_mw(inputs: Dict[str, Any]) -> float:
    population = max(float(inputs.get("population", 100000)), 1.0)
    # Conservative city/facility proxy. This is a stress-testing scale, not full city load.
    return max(population / 18000.0, 1.0)


def _degree_day_demand(base_demand: float, temperature: float, humidity: float, precipitation: float, scenario: Dict[str, float]) -> float:
    comfort_low, comfort_high = 18.0, 26.0
    cooling = max(temperature - comfort_high, 0.0)
    heating = max(comfort_low - temperature, 0.0)
    humidity_stress = max(humidity - 70.0, 0.0) * 0.002
    rain_stress = min(max(precipitation, 0.0) / 300.0, 1.0) * 0.04
    load_multiplier = 1.0 + cooling * 0.025 + heating * 0.030 + humidity_stress + rain_stress
    return base_demand * load_multiplier * scenario["demand"]


def _pvwatts_solar_output(capacity_mw: float, solar_radiation: float, temperature: float, scenario: Dict[str, float], scenario_key: str, failure_ratio: float) -> float:
    capacity_mw = max(float(capacity_mw), 0.0)
    irradiance_ratio = clamp(float(solar_radiation) / 1000.0, 0.0, 1.25)
    module_temp = float(temperature) + (float(solar_radiation) / 800.0) * 20.0
    temp_derate = clamp(1.0 - max(module_temp - 25.0, 0.0) * 0.0035, 0.70, 1.05)
    system_loss_derate = 0.86
    wildfire_smoke_derate = 0.82 if scenario_key == "wildfire" else 1.0
    return max(
        0.0,
        capacity_mw * irradiance_ratio * temp_derate * system_loss_derate
        * scenario["solar"] * wildfire_smoke_derate * (1.0 - failure_ratio)
    )


def _wind_power_curve_output(capacity_mw: float, wind_speed: float, scenario: Dict[str, float], scenario_key: str, failure_ratio: float) -> float:
    capacity_mw = max(float(capacity_mw), 0.0)
    v = max(float(wind_speed), 0.0)
    cut_in, rated, cut_out = 3.0, 12.0, 25.0
    if v < cut_in or v >= cut_out:
        curve_factor = 0.0
    elif v < rated:
        curve_factor = ((v - cut_in) / (rated - cut_in)) ** 3
    else:
        curve_factor = 1.0
    curtailment = 1.0
    if scenario_key in {"storm", "typhoon"} and v >= 20:
        curtailment = 0.70
    return max(0.0, capacity_mw * curve_factor * scenario["wind"] * curtailment * (1.0 - failure_ratio))


def _firm_output(capacity_mw: float, capacity_factor: float, scenario_factor: float, failure_ratio: float) -> float:
    return max(0.0, float(capacity_mw) * capacity_factor * scenario_factor * (1.0 - failure_ratio))


def compute_energy_supply(
    inputs: Dict[str, Any],
    scenario_key: str = "normal",
    failure_ratios: Dict[str, float] | None = None,
    reserve_recovery_lag_days: float = 0,
) -> Dict[str, Any]:
    """Compute TAIVAS scenario energy results.

    Signature intentionally matches earlier TAIVAS versions for compatibility:
    compute_energy_supply(inputs, scenario_key, failure_ratios, reserve_recovery_lag_days)
    """
    failure_ratios = failure_ratios or {}
    scenario_key = str(scenario_key or "normal")
    scenario = _scenario(scenario_key)

    temperature = float(inputs.get("temperature", 25.0))
    humidity = float(inputs.get("humidity", 60.0))
    precipitation = float(inputs.get("precipitation", 0.0))
    wind_speed = float(inputs.get("wind_speed", 4.0))
    solar_radiation = float(inputs.get("solar_radiation", 500.0))

    solar_capacity = float(inputs.get("solar_capacity", 0.0))
    wind_capacity = float(inputs.get("wind_capacity", 0.0))
    geothermal_capacity = float(inputs.get("geothermal_capacity", inputs.get("geo_capacity", 0.0)))
    hydro_capacity = float(inputs.get("hydro_capacity", 0.0))
    battery_capacity = float(inputs.get("battery_capacity", 0.0))

    demand = _degree_day_demand(
        _base_demand_mw(inputs),
        temperature,
        humidity,
        precipitation,
        scenario,
    )

    solar_supply = _pvwatts_solar_output(
        solar_capacity,
        solar_radiation,
        temperature,
        scenario,
        scenario_key,
        _failure(failure_ratios, "solar", "solar_failure_ratio"),
    )
    wind_supply = _wind_power_curve_output(
        wind_capacity,
        wind_speed,
        scenario,
        scenario_key,
        _failure(failure_ratios, "wind", "wind_failure_ratio"),
    )

    # Conservative firm-capacity factors. These are scenario stress-test assumptions.
    geo_supply = _firm_output(
        geothermal_capacity,
        0.88,
        scenario["geo"],
        _failure(failure_ratios, "geothermal", "geo", "geothermal_failure_ratio"),
    )
    hydro_supply = _firm_output(
        hydro_capacity,
        0.52,
        scenario["hydro"],
        _failure(failure_ratios, "hydro", "hydro_failure_ratio"),
    )

    renewable_supply_before_loss = solar_supply + wind_supply + geo_supply + hydro_supply
    transmission_loss = clamp(scenario.get("transmission_loss", 0.02), 0.0, 0.40)
    renewable_supply = renewable_supply_before_loss * (1.0 - transmission_loss)

    available_battery = max(
        0.0,
        battery_capacity * scenario["battery"] * (1.0 - _failure(failure_ratios, "battery", "battery_failure_ratio")),
    )
    pre_storage_shortfall = max(0.0, demand - renewable_supply)

    # Battery support: use only a portion of remaining storage in a one-step dashboard calculation.
    # Reserve-recovery lag reduces how aggressively storage can be assumed available.
    lag_factor = clamp(1.0 - float(reserve_recovery_lag_days or 0) * 0.015, 0.50, 1.0)
    discharge_support = min(pre_storage_shortfall, available_battery * 0.22 * lag_factor)
    battery_after = max(0.0, available_battery - discharge_support / 0.90)

    final_supply = renewable_supply + discharge_support
    shortfall = max(0.0, demand - final_supply)

    grid_dependency = clamp(safe_div(shortfall, demand) * 100.0 * scenario["grid"], 0.0, 100.0)
    renewable_ratio = clamp(safe_div(renewable_supply, max(final_supply, 1e-9)) * 100.0, 0.0, 100.0)
    system_efficiency = clamp(100.0 - grid_dependency * 0.65 - transmission_loss * 100.0 * 0.35, 0.0, 100.0)

    source_outputs = {
        "Solar": solar_supply * (1.0 - transmission_loss),
        "Wind": wind_supply * (1.0 - transmission_loss),
        "Geothermal": geo_supply * (1.0 - transmission_loss),
        "Hydro": hydro_supply * (1.0 - transmission_loss),
    }
    total_source = sum(source_outputs.values())
    actual_mix_pct = {
        name: round(safe_div(value, total_source) * 100.0, 2) if total_source > 0 else 0.0
        for name, value in source_outputs.items()
    }

    return {
        "demand": round(demand, 2),
        "solar_supply": round(source_outputs["Solar"], 2),
        "wind_supply": round(source_outputs["Wind"], 2),
        "geothermal_supply": round(source_outputs["Geothermal"], 2),
        "hydro_supply": round(source_outputs["Hydro"], 2),
        "renewable_supply": round(renewable_supply, 2),
        "final_supply": round(final_supply, 2),
        "battery_levels": round(battery_after, 2),
        "shortfall": round(shortfall, 2),
        "renewable_ratio": round(renewable_ratio, 2),
        "system_efficiency": round(system_efficiency, 2),
        "grid_dependency": round(grid_dependency, 2),
        "actual_mix_pct": actual_mix_pct,
        "source_outputs": {k: round(v, 2) for k, v in source_outputs.items()},
        "transmission_loss_pct": round(transmission_loss * 100.0, 2),
        "scenario_key": scenario_key,
        "model_alignment_notes": MODEL_ALIGNMENT_NOTES,
        "model_limitation": MODEL_ALIGNMENT_NOTES["limitation"],
    }
