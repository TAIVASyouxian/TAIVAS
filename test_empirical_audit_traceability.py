import ast
import unittest
from pathlib import Path

from data.empirical_validation import build_empirical_validation_snapshot


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
    for node in TREE.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Assignment {name} was not found")


def _compile_function(name, namespace):
    node = _function_node(name)
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace[name]


def _safe_str(value, default="Not available"):
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


MODEL_FIELDS = (
    "timestamp",
    "country_key",
    "city_key",
    "lat",
    "lon",
    "population",
    "temperature",
    "wind_speed",
    "solar_radiation",
    "precipitation",
    "humidity",
)


def _display_map():
    return {
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
        "RTE eCO2mix Île-de-France daily real-time exports, consolidated by TAIVAS workflow": (
            "RTE eCO2mix Île-de-France regional observation"
        ),
        "RTE eCO2mix Île-de-France regional observation": (
            "RTE eCO2mix Île-de-France regional observation"
        ),
    }


def _audit_builder():
    namespace = {
        "TAIVAS_WEATHER_INPUT_COLUMNS": MODEL_FIELDS,
        "EMPIRICAL_SIDEBAR_DISPLAY_MAP": _display_map(),
        "EMPIRICAL_RTE_SCOPE_LABEL": _assignment_value(
            "EMPIRICAL_RTE_SCOPE_LABEL"
        ),
        "EMPIRICAL_TAIVAS_SCOPE_LABEL": _assignment_value(
            "EMPIRICAL_TAIVAS_SCOPE_LABEL"
        ),
        "EMPIRICAL_SPATIAL_SCOPE_BOUNDARY": _assignment_value(
            "EMPIRICAL_SPATIAL_SCOPE_BOUNDARY"
        ),
        "EMPIRICAL_BUNDLED_DATASET_CLASSIFICATION": _assignment_value(
            "EMPIRICAL_BUNDLED_DATASET_CLASSIFICATION"
        ),
        "safe_str": _safe_str,
    }
    return _compile_function(
        "build_empirical_validation_audit_record",
        namespace,
    )


def _classification_builder():
    return _compile_function(
        "build_data_classification_rows",
        {"DATA_CLASSIFICATION_LABELS": {
            "demo": "Demo Data",
            "user": "User Input",
            "public": "Public Data",
            "estimated": "Estimated Data",
            "verified": "Verified Data",
            "simulated": "Simulated Scenario Data",
        }},
    )


def _empirical_executive_summary_builder():
    return _compile_function(
        "build_empirical_executive_summary_lines",
        {},
    )


def _sample_record():
    model_inputs = {
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
    observed = {
        "observed_demand_mw": 9287.5,
        "observed_renewable_generation_mw": 407.0,
        "observed_local_generation_mw": 407.0,
        "observed_external_support_mw": 8883.75,
        "observed_battery_net_mw": -0.25,
        "observed_import_dependency_pct": 95.65115,
    }
    metadata = {
        "capacity_data_status": (
            "not_provided_use_explicit_taivas_assumption"
        ),
        "capacity_source": "Not available in current RTE / ERA5 extracts",
        "model_spatial_scope": "Paris-scale TAIVAS profile",
        "electricity_data_scope": "RTE eCO2mix Île-de-France region",
        "weather_data_scope": "ERA5 Paris grid-point hourly observation",
        "weather_match_status": "matched",
        "data_quality_flag": "usable_with_spatial_scope_warning",
        "source_rte": "RTE eCO2mix",
        "source_era5": (
            "ERA5 hourly time-series on single levels, Paris extract"
        ),
    }
    return {
        "record_id": "France|Paris|2026-06-24 17:00:00|159",
        "selector_label": "France / Paris / 2026-06-24 17:00:00",
        "model_inputs": model_inputs,
        "observed": observed,
        "capacity_provenance": {
            "battery_capacity": {
                "csv_value": None,
                "classification": "TAIVAS assumption / user input",
            }
        },
        "metadata": metadata,
    }


class EmpiricalAuditTraceabilityTests(unittest.TestCase):
    def test_empirical_classification_uses_required_provenance(self):
        rows = _classification_builder()(True, False)
        classifications = {
            row["Area"]: row["Classification"]
            for row in rows
        }
        self.assertEqual(
            classifications,
            {
                "ERA5 weather inputs": "Public reanalysis data",
                "RTE observed electricity reference": (
                    "Public observational data"
                ),
                "TAIVAS installed-capacity assumptions": (
                    "User input / model assumption"
                ),
                "TAIVAS simulation outputs": "Estimated / simulated data",
                "Rule-based interpretation": "Estimated interpretation",
            },
        )
        classification_values = {
            row["Classification"]
            for row in rows
        }
        self.assertNotIn("Demo Data", classification_values)
        self.assertNotIn("User Input", classification_values)

    def test_empirical_audit_contains_complete_traceability(self):
        record = _sample_record()
        audit = _audit_builder()(
            True,
            record,
            record["model_inputs"],
            record["observed"],
            record["metadata"],
        )
        required_fields = {
            "enabled",
            "record_id",
            "selector_label",
            "timestamp",
            "weather_source",
            "electricity_source",
            "weather_inputs_used_by_model",
            "observed_reference",
            "electricity_data_scope",
            "weather_data_scope",
            "weather_match_status",
            "data_quality_flag",
            "capacity_data_status",
            "capacity_source",
            "model_spatial_scope",
            "spatial_scope_boundary",
        }
        self.assertTrue(required_fields.issubset(audit))
        self.assertEqual(
            audit["electricity_data_scope"],
            "RTE = Île-de-France regional electricity observation",
        )
        self.assertEqual(
            audit["model_spatial_scope"],
            "TAIVAS = Paris-scale decision-support simulation",
        )
        self.assertEqual(
            audit["spatial_scope_boundary"],
            "Absolute MW values are not directly scale-equivalent.",
        )
        self.assertEqual(
            audit["raw_metadata"]["data_quality_flag"],
            "usable_with_spatial_scope_warning",
        )
        self.assertEqual(
            audit["display_metadata"]["data_quality_flag"],
            "Usable — spatial-scale warning applies",
        )
        self.assertEqual(
            audit["raw_metadata"]["weather_data_scope"],
            "ERA5 Paris grid-point hourly observation",
        )
        self.assertEqual(
            audit["weather_data_scope"],
            "ERA5 hourly reanalysis extract for Paris",
        )
        self.assertEqual(
            audit["display_metadata"]["weather_data_scope"],
            "ERA5 hourly reanalysis extract for Paris",
        )
        self.assertEqual(
            audit["display_metadata"]["source_era5"],
            "ERA5 hourly reanalysis extract for Paris",
        )

    def test_executive_summary_contains_selected_empirical_context(self):
        record = _sample_record()
        lines = _empirical_executive_summary_builder()(
            True,
            record,
            record["metadata"],
            record["observed"],
            {
                **_display_map(),
                "RTE eCO2mix": (
                    "RTE eCO2mix Île-de-France regional observation"
                ),
            },
        )
        summary = "\n".join(lines)
        for expected in (
            "Observed Data Comparison Context",
            "- Selected Timestamp: 2026-06-24 17:00:00",
            "- ERA5 Weather Source: ERA5 hourly reanalysis extract for Paris",
            "- RTE Electricity Source: RTE eCO2mix Île-de-France regional observation",
            "- TAIVAS Model Scope: Paris-scale decision-support simulation",
            "- Observation Scope: Île-de-France regional electricity observation",
            "- Spatial Boundary: Absolute MW values are not directly scale-equivalent.",
            "- Capacity Verification: Installed capacity not verified — TAIVAS assumption / user input",
            "- Comparison Type: Descriptive empirical comparison only",
            "Selected RTE Observation",
            "- Observed Demand: 9287.5 MW",
            "- Observed Renewable Generation: 407.0 MW",
            "- Observed Local Generation: 407.0 MW",
            "- Observed Physical Exchange: 8883.75 MW",
            "- Observed Battery Net: -0.25 MW",
            "- Observed Import Dependency: 95.65115%",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, summary)

        helper_source = ast.get_source_segment(
            SOURCE,
            _function_node("build_empirical_executive_summary_lines"),
        )
        for forbidden in (
            "compute_energy_supply",
            "failure_ratios",
            "risk calculation",
            "battery calculation",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, helper_source)

        executive_source = ast.get_source_segment(
            SOURCE,
            _function_node("build_executive_summary_text"),
        )
        self.assertIn(
            "build_empirical_executive_summary_lines(",
            executive_source,
        )
        self.assertIn(
            "observed_values=empirical_observed",
            executive_source,
        )

    def test_general_mode_executive_summary_has_no_empirical_context(self):
        lines = _empirical_executive_summary_builder()(
            False,
            {},
            {},
            {},
            {},
        )
        self.assertEqual(lines, [])

    def test_selected_timestamp_and_snapshot_share_one_record(self):
        record = _sample_record()
        audit = _audit_builder()(
            True,
            record,
            record["model_inputs"],
            record["observed"],
            record["metadata"],
        )
        snapshot = build_empirical_validation_snapshot(
            record,
            {
                "demand": 100.0,
                "renewable_supply": 60.0,
                "battery_discharge": 10.0,
                "battery_levels": 20.0,
                "external_support_need_proxy": 30.0,
                "system_performance_score": 70.0,
                "risk_tier": "High",
            },
        )
        self.assertEqual(
            audit["timestamp"],
            snapshot["selected_observation"]["timestamp"],
        )
        self.assertEqual(
            audit["observed_reference"]["observed_demand_mw"],
            snapshot["rte"]["observed_demand_mw"],
        )

    def test_observed_values_do_not_enter_model_or_input_values(self):
        record = _sample_record()
        audit = _audit_builder()(
            True,
            record,
            record["model_inputs"],
            record["observed"],
            record["metadata"],
        )
        self.assertTrue(
            all(
                not key.startswith("observed_")
                for key in audit["weather_inputs_used_by_model"]
            )
        )
        self.assertTrue(
            all(
                key.startswith("observed_")
                for key in audit["observed_reference"]
            )
        )
        audit_source = ast.get_source_segment(
            SOURCE,
            _function_node("build_audit_trail_record"),
        )
        self.assertIn('"input_values": dict(inputs)', audit_source)
        self.assertNotIn(
            '"input_values": dict(empirical_observed)',
            audit_source,
        )

    def test_bundled_empirical_dataset_is_not_a_user_upload(self):
        audit_source = ast.get_source_segment(
            SOURCE,
            _function_node("build_audit_trail_record"),
        )
        self.assertIn(
            '"bundled_empirical_dataset_is_user_upload": False',
            audit_source,
        )
        self.assertIn(
            "Bundled public reanalysis and observational reference data",
            SOURCE,
        )

    def test_general_mode_audit_remains_safe_and_classification_unchanged(self):
        rows = _classification_builder()(False, False)
        self.assertEqual(rows[0]["Area"], "Location and population")
        self.assertEqual(rows[3]["Area"], "Uploaded CSV")
        self.assertEqual(rows[3]["Classification"], "Demo Data")

        audit = _audit_builder()(False, {}, {}, {}, {})
        self.assertFalse(audit["enabled"])
        self.assertIsNone(audit["record_id"])
        self.assertEqual(audit["weather_inputs_used_by_model"], {})
        self.assertEqual(audit["observed_reference"], {})


if __name__ == "__main__":
    unittest.main()
