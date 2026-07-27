import ast
import unittest
from pathlib import Path

from core.risk_engine import calculate_risk_tier


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "taivas_control_center.py"
UTILITY_TOOLKIT = ROOT / "taivas_utility_toolkit.py"
SOURCE = ENTRYPOINT.read_text(encoding="utf-8")
UTILITY_SOURCE = UTILITY_TOOLKIT.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _function_node(name):
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Function {name} was not found")


def _function_source(name):
    return ast.get_source_segment(SOURCE, _function_node(name))


def _function_calls(name):
    return {
        node.func.id
        for node in ast.walk(_function_node(name))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }


def _authoritative_tier(shortfall, demand, stored_tier=None):
    namespace = {"calculate_risk_tier": calculate_risk_tier}
    node = _function_node("authoritative_risk_tier_for_results")
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    result = {"shortfall": shortfall, "demand": demand}
    if stored_tier is not None:
        result["risk_tier"] = stored_tier
    return namespace["authoritative_risk_tier_for_results"](result)


def _risk_terminology():
    selected = []
    for node in TREE.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Name)
            and target.id == "RISK_TIER_TERMINOLOGY"
            for target in node.targets
        ):
            selected.append(node)
    namespace = {}
    module = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace["RISK_TIER_TERMINOLOGY"]


class RiskTierDisplaySemanticTests(unittest.TestCase):
    def test_zero_gap_is_low(self):
        self.assertEqual(_authoritative_tier(0.0, 100.0), "Low")

    def test_positive_ratio_below_five_percent_is_elevated(self):
        self.assertEqual(_authoritative_tier(4.99, 100.0), "Elevated")

    def test_five_percent_boundary_is_high(self):
        self.assertEqual(_authoritative_tier(5.0, 100.0), "High")

    def test_ratio_between_five_and_fifteen_percent_is_high(self):
        self.assertEqual(_authoritative_tier(14.99, 100.0), "High")

    def test_fifteen_percent_boundary_is_critical(self):
        self.assertEqual(_authoritative_tier(15.0, 100.0), "Critical")

    def test_ratio_above_fifteen_percent_is_critical(self):
        self.assertEqual(_authoritative_tier(15.01, 100.0), "Critical")

    def test_same_absolute_gap_can_produce_different_tiers(self):
        self.assertEqual(_authoritative_tier(5.0, 200.0), "Elevated")
        self.assertEqual(_authoritative_tier(5.0, 50.0), "High")
        helper_source = _function_source("authoritative_risk_tier_for_results")
        self.assertNotIn("build_status_label", helper_source)
        self.assertNotIn("(5, 15)", helper_source)

    def test_overview_uses_authoritative_tier(self):
        self.assertIn(
            "authoritative_risk_tier_for_results",
            _function_calls("render_emergency_brief"),
        )
        self.assertIn("TAIVAS Risk Tier", _function_source("render_emergency_brief"))

    def test_empirical_snapshot_uses_authoritative_tier(self):
        renderer = _function_source("render_empirical_validation_snapshot")
        self.assertIn("authoritative_risk_tier_for_results(results)", renderer)
        self.assertNotIn('taivas_snapshot["risk_tier"]', renderer)

    def test_explainable_advisory_uses_authoritative_tier(self):
        self.assertIn(
            "authoritative_risk_tier_for_results",
            _function_calls("generate_agentic_advisory"),
        )

    def test_diagnostics_uses_authoritative_tier(self):
        source = _function_source("generate_diagnostic_summary")
        self.assertIn("authoritative_risk_tier_for_results(results)", source)
        self.assertIn("TAIVAS Risk Tier is", source)

    def test_audit_preserves_authoritative_source_and_definition(self):
        terminology = _risk_terminology()
        self.assertEqual(
            terminology,
            {
                "source": "core.risk_engine.calculate_risk_tier",
                "display_source": "authoritative_risk_tier_for_results",
                "definition": "Classification based on modeled unmet-demand ratio.",
                "tiers": {
                    "Low": "No modeled energy gap",
                    "Elevated": "Unmet-demand ratio greater than 0% and below 5%",
                    "High": "Unmet-demand ratio from 5% to below 15%",
                    "Critical": "Unmet-demand ratio of 15% or higher",
                },
            },
        )
        audit_source = _function_source("build_audit_trail_record")
        self.assertIn(
            "authoritative_tier = authoritative_risk_tier_for_results(results)",
            audit_source,
        )
        self.assertIn('"risk_tier": {', audit_source)
        self.assertIn('"value": authoritative_tier', audit_source)
        self.assertIn('audit_simulation_outputs["risk_tier"] = authoritative_tier', audit_source)

    def test_kpi_reference_uses_four_authoritative_tiers(self):
        source = _function_source("render_kpi_reference_panel")
        self.assertIn("Low / Elevated / High / Critical", source)
        self.assertNotIn("Low / Moderate / High / Critical", source)
        self.assertIn("Modeled demand and modeled energy gap.", source)

    def test_executive_txt_pdf_and_ppt_use_authoritative_tier(self):
        executive_source = _function_source("build_executive_summary_text")
        txt_source = _function_source("generate_simulation_report_text")
        toolkit_context_source = _function_source("render_product_utility_toolkit")
        self.assertIn("authoritative_risk_tier_for_results(results)", executive_source)
        self.assertIn("authoritative_risk_tier_for_results(results)", txt_source)
        self.assertIn("authoritative_risk_tier_for_results(results)", toolkit_context_source)
        self.assertIn("TAIVAS Risk Tier", UTILITY_SOURCE)
        self.assertNotIn('["Risk Level",', UTILITY_SOURCE)

    def test_geopolitical_stress_does_not_override_risk_tier(self):
        helper_source = _function_source("authoritative_risk_tier_for_results")
        self.assertNotIn("geopolitical", helper_source.lower())
        self.assertIn("Geopolitical Stress Level", SOURCE)
        self.assertNotIn("Geopolitical Risk Level", SOURCE)

    def test_operational_signal_is_not_labeled_as_risk_tier(self):
        signal_source = _function_source("operational_stress_signal")
        summary_source = _function_source("render_operational_summary_panel")
        self.assertNotIn("Risk Tier", signal_source)
        self.assertIn("Operational Stress Signal", summary_source)
        with self.assertRaises(AssertionError):
            _function_node("operational_risk_label")

    def test_general_demo_and_empirical_modes_share_authoritative_logic(self):
        helper_source = _function_source("authoritative_risk_tier_for_results")
        self.assertNotIn("demo_mode", helper_source)
        self.assertNotIn("empirical_active", helper_source)
        self.assertIn(
            "authoritative_risk_tier_for_results(results)",
            _function_source("render_empirical_validation_snapshot"),
        )
        self.assertIn(
            "authoritative_risk_tier_for_results(results)",
            _function_source("render_emergency_brief"),
        )

    def test_plain_language_severity_maps_from_authoritative_tier_only(self):
        source = _function_source("plain_language_severity")
        self.assertIn("authoritative_risk_tier_for_results(results)", source)
        self.assertIn('"Low": "stable"', source)
        self.assertIn('"Elevated": "mildly stressed"', source)
        self.assertIn('"High": "high stress"', source)
        self.assertIn('"Critical": "critical stress"', source)
        self.assertNotIn('results["shortfall"]', source)
        self.assertNotIn('results["grid_dependency"]', source)


if __name__ == "__main__":
    unittest.main()
