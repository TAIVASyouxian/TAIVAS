import ast
import copy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "taivas_control_center.py"
SOURCE = ENTRYPOINT.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _function_node(name):
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Function {name} was not found")


def _assignment_value(name):
    for node in ast.walk(TREE):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                return ast.literal_eval(node.value)
    raise AssertionError(f"Assignment {name} was not found")


def _assignment_dict_keys(name):
    for node in ast.walk(TREE):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            continue
        if not isinstance(node.value, ast.Dict):
            raise AssertionError(f"Assignment {name} is not a dictionary")
        return {
            ast.literal_eval(key)
            for key in node.value.keys
        }
    raise AssertionError(f"Assignment {name} was not found")


def _compiled_apply_extended_security():
    namespace = {
        "clamp": lambda value, minimum, maximum: max(
            minimum, min(maximum, value)
        )
    }
    node = _function_node("apply_extended_security")
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace["apply_extended_security"]


class ExtendedSecurityAssumptionTests(unittest.TestCase):
    def test_named_defaults_preserve_historical_values(self):
        self.assertEqual(
            _assignment_value("EXTENDED_SECURITY_ASSUMPTION_DEFAULTS"),
            {
                "fuel_price_shock": 0.20,
                "repair_crew_availability": 0.80,
                "spare_parts_delay_days": 7,
                "refill_uncertainty": 0.25,
                "single_point_failure_risk": 0.20,
            },
        )

    def test_default_named_assumptions_preserve_extended_security_output(self):
        defaults = _assignment_value("EXTENDED_SECURITY_ASSUMPTION_DEFAULTS")
        base = {
            "grid_dependency": 18.5,
            "reserve_days_remaining": 12.0,
            "recovery_time_estimate": 3.0,
        }
        actual = _compiled_apply_extended_security()(
            copy.deepcopy(base),
            **defaults,
        )

        penalty = (
            0.20 * 0.10
            + (1 - 0.80) * 0.16
            + min(7 / 30.0, 1.0) * 0.12
            + 0.25 * 0.18
            + 0.20 * 0.22
        )
        expected = copy.deepcopy(base)
        expected["extended_disruption_score"] = round(
            max(0, min(100, base["grid_dependency"] * 0.45 + penalty * 100)),
            2,
        )
        expected["spare_parts_risk"] = round(
            max(0, min(100, 7 * 3.2)),
            2,
        )
        expected["maintenance_readiness"] = round(
            max(0, min(100, 0.80 * 100 - 7 * 1.8)),
            2,
        )
        expected["refill_stability"] = round(
            max(0, min(100, (1 - 0.25) * 100)),
            2,
        )
        expected["single_point_pressure"] = round(0.20 * 100, 2)
        expected["reserve_days_remaining"] = max(
            0,
            round(base["reserve_days_remaining"] - penalty * 4.2, 1),
        )
        expected["recovery_time_estimate"] = max(
            1,
            round(base["recovery_time_estimate"] + penalty * 5 + 7 * 0.3, 1),
        )
        self.assertEqual(actual, expected)

    def test_runtime_call_uses_named_variables_not_numeric_literals(self):
        calls = [
            node
            for node in ast.walk(TREE)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "apply_extended_security"
        ]
        self.assertEqual(len(calls), 1)
        keyword_values = {
            keyword.arg: keyword.value
            for keyword in calls[0].keywords
        }
        for name in _assignment_value(
            "EXTENDED_SECURITY_ASSUMPTION_DEFAULTS"
        ):
            self.assertIn(name, keyword_values)
            self.assertIsInstance(keyword_values[name], ast.Name)
            self.assertEqual(keyword_values[name].id, name)

    def test_audit_summary_and_export_preserve_provenance(self):
        audit_source = ast.get_source_segment(
            SOURCE,
            _function_node("build_audit_trail_record"),
        )
        summary_source = ast.get_source_segment(
            SOURCE,
            _function_node("build_executive_summary_text"),
        )
        report_source = ast.get_source_segment(
            SOURCE,
            _function_node("build_simulation_report_text"),
        )
        generator_source = ast.get_source_segment(
            SOURCE,
            _function_node("generate_simulation_report_text"),
        )
        assumption_keys = _assignment_dict_keys(
            "extended_security_assumptions"
        )
        self.assertEqual(
            assumption_keys,
            set(_assignment_value("EXTENDED_SECURITY_ASSUMPTION_DEFAULTS")),
        )
        self.assertIn('"extended_security_assumptions"', audit_source)
        self.assertIn("dict(extended_security_assumptions)", audit_source)
        for name in assumption_keys:
            self.assertIn(name, summary_source)
            self.assertIn(name, report_source)
        self.assertIn(
            "extended_security_assumptions=extended_security_assumptions",
            generator_source,
        )
        self.assertIn(
            "TAIVAS model assumptions / user inputs",
            SOURCE,
        )
        self.assertIn(
            "Not sourced from RTE observations or ERA5 reanalysis data",
            SOURCE,
        )


if __name__ == "__main__":
    unittest.main()
