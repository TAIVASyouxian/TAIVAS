import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "taivas_control_center.py"
UTILITY_TOOLKIT = ROOT / "taivas_utility_toolkit.py"
SOURCE = ENTRYPOINT.read_text(encoding="utf-8")
UTILITY_SOURCE = UTILITY_TOOLKIT.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

DISPLAY_NAME = "Renewable Supply-to-Demand Ratio"


def _function_node(name):
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Function {name} was not found")


def _function_source(name):
    return ast.get_source_segment(SOURCE, _function_node(name))


def _compile_function(name, namespace=None):
    namespace = dict(namespace or {})
    node = _function_node(name)
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace[name]


def _indicator_findings(simulation_results):
    helper = _compile_function(
        "build_indicator_range_findings",
        {"RENEWABLE_RATIO_DISPLAY_NAME": DISPLAY_NAME},
    )
    return helper(simulation_results)


def _data_quality_status(findings):
    return _compile_function("data_quality_status")(findings)


def _terminology():
    selected_nodes = []
    for node in TREE.body:
        if not isinstance(node, ast.Assign):
            continue
        target_names = {
            target.id
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        if target_names & {
            "RENEWABLE_RATIO_DISPLAY_NAME",
            "RENEWABLE_RATIO_TERMINOLOGY",
        }:
            selected_nodes.append(node)
    namespace = {}
    module = ast.Module(body=selected_nodes, type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace["RENEWABLE_RATIO_TERMINOLOGY"]


class RenewableRatioSemanticTests(unittest.TestCase):
    def test_108_28_is_valid_and_does_not_require_review(self):
        findings = _indicator_findings({
            "renewable_ratio": 108.28,
            "system_efficiency": 90.0,
            "grid_dependency": 10.0,
        })
        self.assertEqual(findings, [])
        self.assertNotEqual(
            _data_quality_status(findings)[0],
            "Data Requires Review",
        )

    def test_133_58_is_valid_and_does_not_require_review(self):
        findings = _indicator_findings({
            "renewable_ratio": 133.58,
            "system_efficiency": 90.0,
            "grid_dependency": 10.0,
        })
        self.assertEqual(findings, [])
        self.assertNotEqual(
            _data_quality_status(findings)[0],
            "Data Requires Review",
        )

    def test_negative_renewable_ratio_is_high(self):
        findings = _indicator_findings({
            "renewable_ratio": -0.01,
            "system_efficiency": 90.0,
            "grid_dependency": 10.0,
        })
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["Severity"], "High")
        self.assertEqual(findings[0]["Area"], DISPLAY_NAME)

    def test_system_performance_above_100_remains_high(self):
        findings = _indicator_findings({
            "renewable_ratio": 133.58,
            "system_efficiency": 100.01,
            "grid_dependency": 10.0,
        })
        self.assertTrue(any(
            finding["Severity"] == "High"
            and finding["Area"] == "System Performance Score"
            for finding in findings
        ))

    def test_external_support_above_100_remains_high(self):
        findings = _indicator_findings({
            "renewable_ratio": 133.58,
            "system_efficiency": 90.0,
            "grid_dependency": 100.01,
        })
        self.assertTrue(any(
            finding["Severity"] == "High"
            and finding["Area"] == "External Support Need Proxy"
            for finding in findings
        ))

    def test_ratio_above_100_is_not_clamped(self):
        simulation_results = {
            "renewable_ratio": 133.58,
            "system_efficiency": 90.0,
            "grid_dependency": 10.0,
        }
        _indicator_findings(simulation_results)
        self.assertEqual(simulation_results["renewable_ratio"], 133.58)
        self.assertNotIn(
            "min(100",
            _function_source("build_indicator_range_findings"),
        )

    def test_empirical_snapshot_uses_precise_ratio_names(self):
        renderer = _function_source("render_empirical_validation_snapshot")
        self.assertIn(
            "TAIVAS renewable supply-to-demand ratio",
            renderer,
        )
        self.assertIn(
            "RTE renewable generation-to-demand ratio",
            renderer,
        )
        self.assertNotIn('"TAIVAS renewable share"', renderer)
        self.assertNotIn('"RTE renewable share"', renderer)
        self.assertIn("definitions and spatial scales differ", renderer)

    def test_audit_preserves_legacy_key_and_precise_semantics(self):
        terminology = _terminology()
        self.assertEqual(terminology, {
            "internal_key": "renewable_ratio",
            "display_name": DISPLAY_NAME,
            "definition": (
                "Modeled renewable supply divided by modeled demand, "
                "expressed as a percentage."
            ),
            "interpretation": (
                "Values above 100% indicate modeled renewable supply exceeds "
                "modeled demand under the selected assumptions."
            ),
            "boundary": (
                "This is not the renewable share of observed regional "
                "generation and is not constrained to 100%."
            ),
        })
        audit_source = _function_source("build_audit_trail_record")
        self.assertIn(
            '"renewable_ratio": dict(RENEWABLE_RATIO_TERMINOLOGY)',
            audit_source,
        )

    def test_general_and_empirical_modes_share_one_validation_semantic(self):
        helper_source = _function_source("build_indicator_range_findings")
        self.assertNotIn("empirical_active", helper_source)
        general_findings = _indicator_findings({
            "renewable_ratio": 108.28,
            "system_efficiency": 90.0,
            "grid_dependency": 10.0,
        })
        empirical_findings = _indicator_findings({
            "renewable_ratio": 108.28,
            "system_efficiency": 90.0,
            "grid_dependency": 10.0,
        })
        self.assertEqual(general_findings, empirical_findings)

    def test_all_required_presentations_and_exports_use_new_name(self):
        for function_name in (
            "render_public_risk_communication_summary",
            "scenario_comparison_matrix",
            "generate_agentic_advisory",
            "render_kpi_reference_panel",
            "build_executive_summary_text",
            "scenario_comparison_metrics",
            "compare_baseline_vs_scenario",
        ):
            with self.subTest(function=function_name):
                self.assertIn(
                    "RENEWABLE_RATIO_DISPLAY_NAME",
                    _function_source(function_name),
                )
        self.assertIn(
            "Renewable Supply-to-Demand Ratio",
            _function_source("build_simulation_report_text"),
        )
        renewable_mix_source = _function_source(
            "render_renewable_mix_summary"
        )
        self.assertIn('tr("rr")', renewable_mix_source)
        self.assertIn(
            "Modeled renewable supply divided by modeled demand",
            renewable_mix_source,
        )
        self.assertIn(
            '"rr": RENEWABLE_RATIO_DISPLAY_NAME',
            SOURCE,
        )
        self.assertIn(DISPLAY_NAME, UTILITY_SOURCE)
        self.assertNotIn('"Renewable Ratio"', UTILITY_SOURCE)


if __name__ == "__main__":
    unittest.main()
