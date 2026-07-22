"""Integration checks for the documented TAIVAS Streamlit entry point.

The Streamlit module executes UI code at import time, so these tests load the
official wrapper function from its abstract syntax tree (AST). This verifies the
actual function shipped in ``taivas_control_center.py`` without mocking a full
Streamlit session.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest

from core.energy_balance_phase2 import (
    SIMULATION_INTERVAL_HOURS,
    calculate_system_performance_score,
    compute_energy_supply_core,
)


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "taivas_control_center.py"


def _entrypoint_tree() -> ast.Module:
    return ast.parse(ENTRYPOINT.read_text(encoding="utf-8-sig"), filename=str(ENTRYPOINT))


def _literal_assignment(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{name} was not found in the official entry point")


def _official_compute_function():
    tree = _entrypoint_tree()
    function_node = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "compute_energy_supply"
    )
    scenarios = _literal_assignment(tree, "SCENARIOS")
    facility_factors = _literal_assignment(tree, "FACILITY_DEMAND_FACTORS")
    namespace = {
        "SCENARIOS": scenarios,
        "FACILITY_DEMAND_FACTORS": facility_factors,
        "facility_demand_factor": lambda name: facility_factors.get(str(name), 1.0),
        "compute_energy_supply_core": compute_energy_supply_core,
        "SIMULATION_INTERVAL_HOURS": SIMULATION_INTERVAL_HOURS,
        "DEMAND_PER_CAPITA_MW": _literal_assignment(tree, "DEMAND_PER_CAPITA_MW"),
        "SOLAR_EFFICIENCY": _literal_assignment(tree, "SOLAR_EFFICIENCY"),
        "WIND_EFFICIENCY": _literal_assignment(tree, "WIND_EFFICIENCY"),
        "GEOTHERMAL_AVAILABILITY_FACTOR": _literal_assignment(tree, "GEOTHERMAL_AVAILABILITY_FACTOR"),
        "BATTERY_ROUND_TRIP_LOSS_RATE": _literal_assignment(tree, "BATTERY_ROUND_TRIP_LOSS_RATE"),
    }
    module = ast.Module(body=[function_node], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace["compute_energy_supply"], namespace


class OfficialEntrypointAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.official_compute, self.namespace = _official_compute_function()
        self.inputs = {
            "country_key": "Finland",
            "city_key": "Helsinki",
            "lat": 60.1699,
            "lon": 24.9384,
            "temperature": 5.0,
            "wind_speed": 8.0,
            "solar_radiation": 250.0,
            "precipitation": 30.0,
            "humidity": 75.0,
            "population": 664000,
            "solar_capacity": 40.0,
            "wind_capacity": 30.0,
            "geothermal_capacity": 10.0,
            "hydro_capacity": 20.0,
            "battery_capacity": 20.0,
            "battery_current": 20.0,
            "grid_support": 0.0,
            "facility_type": "Hospital",
        }
        self.failure_ratios = {
            "solar": 0.0,
            "wind": 0.0,
            "geothermal": 0.0,
            "hydro": 0.0,
            "battery": 0.0,
        }

    def _direct_core(self, scenario_key: str):
        return compute_energy_supply_core(
            inputs=self.inputs,
            scenario_key=scenario_key,
            scenario=self.namespace["SCENARIOS"][scenario_key],
            failure_ratios=self.failure_ratios,
            reserve_recovery_lag_days=0,
            facility_factor=self.namespace["FACILITY_DEMAND_FACTORS"]["Hospital"],
            demand_per_capita_mw=self.namespace["DEMAND_PER_CAPITA_MW"],
            solar_efficiency=self.namespace["SOLAR_EFFICIENCY"],
            wind_efficiency=self.namespace["WIND_EFFICIENCY"],
            geothermal_availability_factor=self.namespace["GEOTHERMAL_AVAILABILITY_FACTOR"],
            battery_loss_rate=self.namespace["BATTERY_ROUND_TRIP_LOSS_RATE"],
            interval_hours=SIMULATION_INTERVAL_HOURS,
        )

    def test_official_wrapper_calls_authoritative_core_with_explicit_interval(self):
        tree = _entrypoint_tree()
        function_node = next(
            node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "compute_energy_supply"
        )
        calls = [node for node in ast.walk(function_node) if isinstance(node, ast.Call)]
        core_call = next(
            call for call in calls if isinstance(call.func, ast.Name) and call.func.id == "compute_energy_supply_core"
        )
        interval = next(keyword.value for keyword in core_call.keywords if keyword.arg == "interval_hours")
        self.assertIsInstance(interval, ast.Name)
        self.assertEqual(interval.id, "SIMULATION_INTERVAL_HOURS")

    def test_all_official_scenarios_match_direct_core_outputs(self):
        for scenario_key in self.namespace["SCENARIOS"]:
            with self.subTest(scenario=scenario_key):
                official = self.official_compute(self.inputs, scenario_key, self.failure_ratios, 0)
                self.assertEqual(official, self._direct_core(scenario_key))

    def test_helsinki_hospital_blizzard_matches_manuscript_fixture(self):
        output = self.official_compute(self.inputs, "blizzard", self.failure_ratios, 0)
        expected = {
            "demand": 38.11,
            "renewable_supply": 26.19,
            "battery_discharge": 5.95,
            "battery_levels": 13.81,
            "final_supply": 32.14,
            "shortfall": 5.97,
            "system_performance_score": 84.33,
            "external_support_need_proxy": 15.67,
            "risk_tier": "Critical",
            "simulation_interval_hours": 1.0,
        }
        for key, value in expected.items():
            self.assertEqual(output[key], value, key)

    def test_legacy_scale_dependent_score_is_absent_from_official_path(self):
        source = ENTRYPOINT.read_text(encoding="utf-8-sig")
        core_source = (ROOT / "core" / "energy_balance_phase2.py").read_text(encoding="utf-8-sig")
        self.assertNotIn("shortfall * 0.55", source)
        self.assertNotIn("energy_gap_mw) * 0.55", core_source)

    def test_disabled_geopolitical_extension_preserves_core_outputs(self):
        tree = _entrypoint_tree()
        function_node = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "apply_geopolitical_shock_to_results"
        )
        namespace = {
            "clamp": lambda value, low, high: max(low, min(high, value)),
            "safe_div": lambda numerator, denominator: numerator / denominator if denominator else 0.0,
            "calculate_system_performance_score": calculate_system_performance_score,
            "SIMULATION_INTERVAL_HOURS": SIMULATION_INTERVAL_HOURS,
        }
        module = ast.Module(body=[function_node], type_ignores=[])
        ast.fix_missing_locations(module)
        exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
        core_output = self.official_compute(self.inputs, "blizzard", self.failure_ratios, 0)
        output = namespace["apply_geopolitical_shock_to_results"](
            core_output,
            {
                "event_type": "None",
                "risk_level": "Low",
                "supply_penalty_pct": 0.0,
                "demand_penalty_pct": 0.0,
                "grid_stress_index": 0.0,
                "price_spike_index": 0.0,
                "oil_supply_disruption_percent": 0.0,
            },
        )
        for key, value in core_output.items():
            self.assertEqual(output[key], value, key)


if __name__ == "__main__":
    unittest.main()
