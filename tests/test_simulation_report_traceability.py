import ast
import unittest
from pathlib import Path

from core.energy_balance_phase2 import SIMULATION_INTERVAL_HOURS, compute_energy_supply_core


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "taivas_control_center.py"
SOURCE = ENTRYPOINT.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _function_node(name):
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Function {name} was not found")


def _assignment_namespace(names):
    selected = []
    for node in TREE.body:
        if not isinstance(node, ast.Assign):
            continue
        target_names = {target.id for target in node.targets if isinstance(target, ast.Name)}
        if target_names & set(names):
            selected.append(node)
    namespace = {}
    module = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace


def _report_namespace():
    names = [
        "format_system_performance_score",
        "format_report_number",
        "format_simulation_interval",
        "build_simulation_report_text",
    ]
    namespace = {"SIMULATION_INTERVAL_HOURS": SIMULATION_INTERVAL_HOURS}
    module = ast.Module(body=[_function_node(name) for name in names], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace


class SimulationReportTraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.constants = _assignment_namespace(
            {
                "SCENARIOS",
                "FACILITY_DEMAND_FACTORS",
                "DEMAND_PER_CAPITA_MW",
                "SOLAR_EFFICIENCY",
                "WIND_EFFICIENCY",
                "GEOTHERMAL_AVAILABILITY_FACTOR",
                "BATTERY_ROUND_TRIP_LOSS_RATE",
                "MANUSCRIPT_FIXTURE_INPUTS",
            }
        )
        cls.report = _report_namespace()
        cls.no_failures = {
            "solar": 0.0,
            "wind": 0.0,
            "geothermal": 0.0,
            "hydro": 0.0,
            "battery": 0.0,
        }

    def _run_core(self, inputs, scenario_key, facility_type, lag_days):
        c = self.constants
        return compute_energy_supply_core(
            inputs=inputs,
            scenario_key=scenario_key,
            scenario=c["SCENARIOS"][scenario_key],
            failure_ratios=self.no_failures,
            reserve_recovery_lag_days=lag_days,
            facility_factor=c["FACILITY_DEMAND_FACTORS"][facility_type],
            demand_per_capita_mw=c["DEMAND_PER_CAPITA_MW"],
            solar_efficiency=c["SOLAR_EFFICIENCY"],
            wind_efficiency=c["WIND_EFFICIENCY"],
            geothermal_availability_factor=c["GEOTHERMAL_AVAILABILITY_FACTOR"],
            battery_loss_rate=c["BATTERY_ROUND_TRIP_LOSS_RATE"],
            interval_hours=SIMULATION_INTERVAL_HOURS,
        )

    def _build_report(self, inputs, results, scenario_key, facility_type, lag_days):
        return self.report["build_simulation_report_text"](
            generated_at="2026-07-22 12:00:00",
            country=inputs["country_key"],
            city=inputs["city_key"],
            scenario=scenario_key,
            facility=facility_type,
            runtime_inputs=inputs,
            runtime_results=results,
            applied_reserve_recovery_lag_days=lag_days,
            authoritative_risk_tier=results["risk_tier"],
            comparison_records=[],
            alerts=[],
            recommendations=[],
            decision_logs=[],
            model_limitation="Scenario-based estimate only.",
        )

    def test_manuscript_fixture_report_contains_traceability_values(self):
        preset = self.constants["MANUSCRIPT_FIXTURE_INPUTS"]
        inputs = {
            "country_key": preset["country"],
            "city_key": preset["city"],
            "lat": preset["lat"],
            "lon": preset["lon"],
            "temperature": preset["temperature"],
            "wind_speed": preset["wind_speed"],
            "solar_radiation": preset["solar_radiation"],
            "precipitation": preset["precipitation"],
            "humidity": preset["humidity"],
            "population": preset["population"],
            "solar_capacity": preset["solar_capacity"],
            "wind_capacity": preset["wind_capacity"],
            "geothermal_capacity": preset["geothermal_capacity"],
            "hydro_capacity": preset["hydro_capacity"],
            "battery_capacity": preset["battery_capacity"],
            "battery_current": preset["battery_current"],
            "grid_support": preset["grid_support"],
            "facility_type": preset["facility_type"],
        }
        results = self._run_core(inputs, "blizzard", "Hospital", 0)
        report = self._build_report(inputs, results, "blizzard", "Hospital", 0)

        expected_lines = [
            "- Initial Battery State: 20 MWh",
            "- Battery Capacity: 20 MWh",
            "- Reserve Recovery Lag: 0 days",
            "- Battery Contribution: 5.95 MW",
            "- Battery Remaining: 13.81 MWh",
            "- Risk Tier: Critical",
            "- System Performance Score: 84.33%",
            "- External Support Need Proxy: 15.67%",
            "- Simulation Interval: 1 hour",
        ]
        for line in expected_lines:
            self.assertIn(line, report)

    def test_non_manuscript_report_values_are_generated_dynamically(self):
        inputs = {
            "country_key": "Taiwan",
            "city_key": "Taipei",
            "lat": 25.033,
            "lon": 121.5654,
            "temperature": 36.0,
            "wind_speed": 2.0,
            "solar_radiation": 800.0,
            "precipitation": 2.0,
            "humidity": 80.0,
            "population": 1_000_000,
            "solar_capacity": 20.0,
            "wind_capacity": 10.0,
            "geothermal_capacity": 0.0,
            "hydro_capacity": 5.0,
            "battery_capacity": 100.0,
            "battery_current": 70.0,
            "grid_support": 0.0,
            "facility_type": "Hospital",
        }
        results = self._run_core(inputs, "heat_wave", "Hospital", 4)
        report = self._build_report(inputs, results, "heat_wave", "Hospital", 4)
        number = self.report["format_report_number"]

        self.assertIn("- Initial Battery State: 70 MWh", report)
        self.assertIn("- Battery Capacity: 100 MWh", report)
        self.assertIn("- Reserve Recovery Lag: 4 days", report)
        self.assertIn(f"- Battery Contribution: {number(results['battery_discharge'])} MW", report)
        self.assertIn(f"- Battery Remaining: {number(results['battery_levels'])} MWh", report)
        self.assertIn(f"- Risk Tier: {results['risk_tier']}", report)
        self.assertNotIn("- Battery Contribution: 5.95 MW", report)
        self.assertNotIn("- Battery Remaining: 13.81 MWh", report)

    def test_primary_export_passes_current_runtime_state_to_report_builder(self):
        source = ast.get_source_segment(SOURCE, _function_node("generate_simulation_report_text"))
        self.assertIn("runtime_inputs=inputs", source)
        self.assertIn("runtime_results=results", source)
        self.assertIn(
            "applied_reserve_recovery_lag_days=reserve_recovery_lag_days",
            source,
        )
        self.assertIn(
            "authoritative_risk_tier=authoritative_risk_tier_for_results(results)",
            source,
        )


if __name__ == "__main__":
    unittest.main()
