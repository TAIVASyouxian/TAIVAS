import ast
import unittest
from pathlib import Path

from core.energy_balance_phase2 import SIMULATION_INTERVAL_HOURS, compute_energy_supply_core
from core.risk_engine import calculate_risk_tier


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "taivas_control_center.py"
SOURCE = ENTRYPOINT.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _function_node(name):
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Function {name} was not found")


def _function_call_names(name):
    calls = set()
    for node in ast.walk(_function_node(name)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            calls.add(node.func.id)
    return calls


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


def _compiled_functions(names, namespace=None):
    namespace = dict(namespace or {})
    module = ast.Module(body=[_function_node(name) for name in names], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace


class DeployedUiAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        constants = _assignment_namespace(
            {
                "SCENARIOS",
                "FACILITY_DEMAND_FACTORS",
                "DEMAND_PER_CAPITA_MW",
                "SOLAR_EFFICIENCY",
                "WIND_EFFICIENCY",
                "GEOTHERMAL_AVAILABILITY_FACTOR",
                "BATTERY_ROUND_TRIP_LOSS_RATE",
                "MANUSCRIPT_FIXTURE_DEMO_NAME",
                "MANUSCRIPT_FIXTURE_INPUTS",
                "DEMO_RESERVE_RECOVERY_LAG_DEFAULTS",
            }
        )
        cls.constants = constants
        cls.inputs = {
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
        cls.failure_ratios = {
            "solar": 0.0,
            "wind": 0.0,
            "geothermal": 0.0,
            "hydro": 0.0,
            "battery": 0.0,
        }

    def _run_fixture(self, lag_days):
        c = self.constants
        return compute_energy_supply_core(
            inputs=self.inputs,
            scenario_key="blizzard",
            scenario=c["SCENARIOS"]["blizzard"],
            failure_ratios=self.failure_ratios,
            reserve_recovery_lag_days=lag_days,
            facility_factor=c["FACILITY_DEMAND_FACTORS"]["Hospital"],
            demand_per_capita_mw=c["DEMAND_PER_CAPITA_MW"],
            solar_efficiency=c["SOLAR_EFFICIENCY"],
            wind_efficiency=c["WIND_EFFICIENCY"],
            geothermal_availability_factor=c["GEOTHERMAL_AVAILABILITY_FACTOR"],
            battery_loss_rate=c["BATTERY_ROUND_TRIP_LOSS_RATE"],
            interval_hours=SIMULATION_INTERVAL_HOURS,
        )

    def test_lag_three_reproduces_deployed_battery_result(self):
        result = self._run_fixture(3)
        self.assertEqual(result["battery_discharge"], 5.68)
        self.assertEqual(result["battery_levels"], 14.09)
        self.assertEqual(result["final_supply"], 31.87)
        self.assertEqual(result["shortfall"], 6.24)

    def test_lag_zero_reproduces_manuscript_fixture(self):
        result = self._run_fixture(0)
        expected = {
            "demand": 38.11,
            "renewable_supply": 26.19,
            "battery_discharge": 5.95,
            "final_supply": 32.14,
            "shortfall": 5.97,
            "battery_levels": 13.81,
            "system_performance_score": 84.33,
            "external_support_need_proxy": 15.67,
            "risk_tier": "Critical",
        }
        for key, value in expected.items():
            self.assertEqual(result[key], value, key)

    def test_manuscript_preset_matches_authoritative_fixture(self):
        preset_name = self.constants["MANUSCRIPT_FIXTURE_DEMO_NAME"]
        preset = self.constants["MANUSCRIPT_FIXTURE_INPUTS"]
        for key, value in {
            "country": "Finland",
            "city": "Helsinki",
            "lat": 60.1699,
            "lon": 24.9384,
            "population": 664000,
            "facility_type": "Hospital",
            "scenario_key": "blizzard",
            "temperature": 5.0,
            "wind_speed": 8.0,
            "solar_radiation": 250.0,
            "precipitation": 30.0,
            "humidity": 75.0,
            "solar_capacity": 40.0,
            "wind_capacity": 30.0,
            "geothermal_capacity": 10.0,
            "hydro_capacity": 20.0,
            "battery_capacity": 20.0,
            "battery_current": 20.0,
            "grid_support": 0.0,
            "reserve_recovery_lag_days": 0,
        }.items():
            self.assertEqual(preset[key], value, key)
        self.assertEqual(self.constants["DEMO_RESERVE_RECOVERY_LAG_DEFAULTS"][preset_name], 0)

    def test_visible_lag_is_passed_unchanged_to_core(self):
        wrapper = _function_node("compute_energy_supply")
        core_calls = [
            node for node in ast.walk(wrapper)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "compute_energy_supply_core"
        ]
        self.assertEqual(len(core_calls), 1)
        lag_keyword = next(
            keyword for keyword in core_calls[0].keywords
            if keyword.arg == "reserve_recovery_lag_days"
        )
        self.assertIsInstance(lag_keyword.value, ast.Name)
        self.assertEqual(lag_keyword.value.id, "reserve_recovery_lag_days")
        self.assertNotIn(
            'reserve_recovery_lag_days = preset.get("reserve_recovery_lag_days"',
            SOURCE,
        )

    def test_scenario_brief_preserves_critical_tier(self):
        namespace = _compiled_functions(
            ["authoritative_risk_tier_for_results", "friendly_risk_level"],
            {
                "calculate_risk_tier": calculate_risk_tier,
                "results": {"risk_tier": "Critical", "shortfall": 16.0, "demand": 100.0},
            },
        )
        self.assertEqual(namespace["friendly_risk_level"](), "Critical")

    def test_major_risk_displays_use_authoritative_tier(self):
        self.assertIn("friendly_risk_level", _function_call_names("render_emergency_brief"))
        self.assertIn("authoritative_risk_tier_for_results", _function_call_names("operational_risk_tier_for_display"))
        self.assertIn("authoritative_risk_tier_for_results", _function_call_names("generate_risk_alerts"))
        self.assertIn("authoritative_risk_tier_for_results", _function_call_names("generate_agentic_advisory"))
        executive_source = ast.get_source_segment(SOURCE, _function_node("build_executive_summary_text"))
        self.assertIn("advisory['risk_tier']", executive_source)

    def test_obsolete_external_dependency_phrase_is_absent(self):
        self.assertNotIn("external power dependency", SOURCE.lower())

    def test_new_external_support_driver_triggers_recommendation(self):
        namespace = _compiled_functions(
            ["generate_diagnostic_recommendations"],
            {
                "rank_shortfall_drivers": lambda: [
                    {"Driver": "External Support Need Proxy increase"}
                ]
            },
        )
        recommendations = namespace["generate_diagnostic_recommendations"]()
        self.assertIn(
            "Review the External Support Need Proxy and backup-supply assumptions.",
            recommendations,
        )


if __name__ == "__main__":
    unittest.main()
