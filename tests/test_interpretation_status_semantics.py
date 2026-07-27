import ast
import unittest
from pathlib import Path


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


def _interpretation_profile(
    *,
    scenario="normal",
    empirical_enabled=False,
    findings=None,
    empirical_findings=None,
    metadata=None,
    model_inputs=None,
    observed_values=None,
):
    namespace = {
        "scenario_key": scenario,
        "EMPIRICAL_SIDEBAR_DISPLAY_MAP": {
            "matched": "Matched",
            "usable_with_spatial_scope_warning": (
                "Usable — spatial-scale warning applies"
            ),
            "not_provided_use_explicit_taivas_assumption": (
                "Not provided — TAIVAS assumption / user input"
            ),
            "ERA5 hourly time-series on single levels, Paris extract": (
                "ERA5 hourly reanalysis extract for Paris"
            ),
            "ERA5 Paris grid-point hourly observation": (
                "ERA5 hourly reanalysis extract for Paris"
            ),
        },
    }
    node = _function_node("interpretation_status_profile")
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace["interpretation_status_profile"](
        findings=[] if findings is None else findings,
        scenario=scenario,
        empirical_enabled=empirical_enabled,
        empirical_findings=[] if empirical_findings is None else empirical_findings,
        empirical_metadata_values={} if metadata is None else metadata,
        empirical_input_values={} if model_inputs is None else model_inputs,
        empirical_observed_values={} if observed_values is None else observed_values,
    )


def _complete_empirical_inputs():
    return {
        "timestamp": "2026-06-24 17:00:00",
        "country_key": "France",
        "city_key": "Paris",
        "lat": 48.8566,
        "lon": 2.3522,
        "population": 2100000.0,
        "temperature": 40.0214,
        "wind_speed": 0.547533,
        "solar_radiation": 638.311111,
        "precipitation": 0.0,
        "humidity": 22.735792,
    }


def _complete_observed_values():
    return {
        "observed_demand_mw": 9287.5,
        "observed_renewable_generation_mw": 407.0,
        "observed_external_support_mw": 8883.75,
    }


class InterpretationStatusSemanticTests(unittest.TestCase):
    def test_general_normal_uses_complete_baseline_exploratory_status(self):
        profile = _interpretation_profile()
        self.assertEqual(profile["input_completeness"], "Complete")
        self.assertEqual(profile["interpretation_status"], "Baseline-oriented")
        self.assertEqual(
            profile["model_evidence_status"],
            "Exploratory — not empirically calibrated",
        )
        self.assertFalse(profile["statistical_confidence_claimed"])

    def test_general_extreme_is_scenario_sensitive_without_confidence_claim(self):
        profile = _interpretation_profile(scenario="typhoon")
        self.assertEqual(profile["interpretation_status"], "Scenario-sensitive")
        self.assertEqual(
            profile["model_evidence_status"],
            "Exploratory — not empirically calibrated",
        )
        self.assertFalse(profile["calibration_completed"])
        self.assertFalse(profile["external_validation_completed"])

    def test_empirical_mode_uses_descriptive_spatial_scale_status(self):
        profile = _interpretation_profile(
            scenario="heat_wave",
            empirical_enabled=True,
            metadata={
                "weather_match_status": "matched",
                "data_quality_flag": "usable_with_spatial_scope_warning",
                "capacity_data_status": (
                    "not_provided_use_explicit_taivas_assumption"
                ),
            },
            model_inputs=_complete_empirical_inputs(),
            observed_values=_complete_observed_values(),
        )
        self.assertEqual(profile["input_completeness"], "Complete")
        self.assertEqual(
            profile["interpretation_status"],
            "Descriptive empirical comparison",
        )
        self.assertEqual(
            profile["model_evidence_status"],
            "Spatial-scale warning — calibration not completed",
        )
        self.assertIn(
            "Installed capacity not verified",
            profile["capacity_verification_status"],
        )

    def test_matched_weather_does_not_claim_validation_or_calibration(self):
        profile = _interpretation_profile(
            scenario="heat_wave",
            empirical_enabled=True,
            metadata={"weather_match_status": "matched"},
            model_inputs=_complete_empirical_inputs(),
            observed_values=_complete_observed_values(),
        )
        self.assertIn(
            "Weather timestamp matched; this does not indicate model validation or calibration.",
            profile["display_notes"],
        )
        self.assertFalse(profile["calibration_completed"])
        self.assertFalse(profile["external_validation_completed"])

    def test_empirical_display_notes_state_required_boundaries(self):
        profile = _interpretation_profile(
            scenario="heat_wave",
            empirical_enabled=True,
            model_inputs=_complete_empirical_inputs(),
            observed_values=_complete_observed_values(),
        )
        notes = " ".join(profile["display_notes"])
        for phrase in (
            "Descriptive comparison only.",
            "Spatial scales differ",
            "Installed capacity not verified",
            "Model remains exploratory and uncalibrated.",
            "ERA5 weather values are used as model inputs.",
            "RTE electricity values are observational references only.",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, notes)

    def test_empirical_snapshot_notes_humanize_internal_metadata_codes(self):
        profile = _interpretation_profile(
            scenario="heat_wave",
            empirical_enabled=True,
            metadata={
                "data_quality_flag": "usable_with_spatial_scope_warning",
                "capacity_data_status": (
                    "not_provided_use_explicit_taivas_assumption"
                ),
            },
            model_inputs=_complete_empirical_inputs(),
            observed_values=_complete_observed_values(),
        )
        notes = " ".join(profile["display_notes"])
        self.assertIn("Usable — spatial-scale warning applies", notes)
        self.assertIn("Not provided — TAIVAS assumption / user input", notes)
        self.assertNotIn("usable_with_spatial_scope_warning", notes)
        self.assertNotIn(
            "not_provided_use_explicit_taivas_assumption",
            notes,
        )

    def test_missing_empirical_weather_requires_review(self):
        inputs = _complete_empirical_inputs()
        inputs["temperature"] = None
        profile = _interpretation_profile(
            scenario="heat_wave",
            empirical_enabled=True,
            model_inputs=inputs,
            observed_values=_complete_observed_values(),
        )
        self.assertEqual(profile["input_completeness"], "Review required")

    def test_empirical_error_finding_requires_review(self):
        profile = _interpretation_profile(
            scenario="heat_wave",
            empirical_enabled=True,
            empirical_findings=[{
                "severity": "Error",
                "area": "Observed comparison",
                "message": "Missing observed comparison value.",
            }],
            model_inputs=_complete_empirical_inputs(),
            observed_values=_complete_observed_values(),
        )
        self.assertEqual(profile["input_completeness"], "Review required")

    def test_general_mode_has_no_empirical_scope_notes(self):
        profile = _interpretation_profile(scenario="normal")
        notes = " ".join(profile["display_notes"])
        self.assertNotIn("Paris", notes)
        self.assertNotIn("Île-de-France", notes)
        self.assertEqual(profile["empirical_comparison_type"], "Not active")
        self.assertIsNone(profile["spatial_scope_warning"])

    def test_audit_has_new_interpretation_status_and_legacy_note(self):
        audit_source = _function_source("build_audit_trail_record")
        self.assertIn(
            "interpretation_status = interpretation_status_profile()",
            audit_source,
        )
        self.assertIn('"interpretation_status": interpretation_status', audit_source)
        self.assertIn('"confidence": confidence', audit_source)
        self.assertIn(
            "Legacy display identifier — not statistical confidence.",
            SOURCE,
        )

    def test_primary_ui_surfaces_use_three_status_labels(self):
        for function_name in (
            "render_confidence_panel",
            "render_data_quality_panel",
            "render_agentic_advisory_layer",
            "render_ai_recommendation_workspace",
            "render_failure_diagnostics_panel",
            "render_empirical_validation_snapshot",
        ):
            source = _function_source(function_name)
            with self.subTest(function=function_name):
                self.assertIn("Input Completeness", source)
                self.assertIn("Interpretation Status", source)
                self.assertIn("Model Evidence Status", source)

    def test_scenario_matrix_uses_new_status_columns(self):
        source = _function_source("scenario_comparison_matrix")
        self.assertIn('"Input Completeness"', source)
        self.assertIn('"Interpretation Status"', source)
        self.assertIn('"Model Evidence Status"', source)
        self.assertNotIn('"Confidence Level"', source)

    def test_txt_pdf_and_ppt_exports_use_new_status_labels(self):
        txt_source = _function_source("build_simulation_report_text")
        for phrase in (
            "Input Completeness",
            "Interpretation Status",
            "Model Evidence Status",
            "Statistical Confidence Claimed",
            "Calibration Completed",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, txt_source)
                self.assertIn(phrase, UTILITY_SOURCE)

    def test_executive_summary_uses_new_status_labels(self):
        source = _function_source("build_executive_summary_text")
        self.assertIn("Interpretation and Evidence Status", source)
        self.assertIn("Input Completeness", source)
        self.assertIn("Interpretation Status", source)
        self.assertIn("Model Evidence Status", source)

    def test_forbidden_confidence_claims_are_absent_from_active_surfaces(self):
        active_sources = "\n".join([
            _function_source("render_confidence_panel"),
            _function_source("render_data_quality_panel"),
            _function_source("scenario_comparison_matrix"),
            _function_source("build_executive_summary_text"),
            _function_source("render_ai_recommendation_workspace"),
            _function_source("render_empirical_validation_snapshot"),
            _function_source("build_simulation_report_text"),
            UTILITY_SOURCE,
        ])
        for phrase in (
            "High Confidence",
            "Medium Confidence",
            "Low Uncertainty",
            "Confidence Level",
            "Uncertainty Level",
            "Forecast Reliability",
            "Prediction accuracy",
            "Model confirmed by RTE",
            "ERA5/RTE validation passed",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, active_sources)


if __name__ == "__main__":
    unittest.main()
