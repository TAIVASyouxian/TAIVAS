import copy
import hashlib
import unittest
from pathlib import Path

import pandas as pd

from data.empirical_validation import (
    CAPACITY_COLUMNS,
    build_empirical_records,
    build_empirical_validation_snapshot,
    capacity_provenance_from_record,
    format_observed_mw_for_display,
    model_inputs_from_record,
    read_empirical_validation_csv,
    select_empirical_record,
    validate_empirical_dataframe,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGING_CSV = (
    PROJECT_ROOT
    / "samples"
    / "TAIVAS_Paris_Heatwave_2026_staging.csv"
)


class EmpiricalValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataframe, cls.load_warnings = read_empirical_validation_csv(
            STAGING_CSV
        )
        cls.records = build_empirical_records(cls.dataframe)

    def test_staging_csv_has_310_rows(self):
        self.assertEqual(self.load_warnings, [])
        self.assertEqual(len(self.dataframe), 310)
        self.assertEqual(len(self.records), 310)

    def test_timestamp_has_310_unique_values(self):
        timestamps = pd.to_datetime(
            self.dataframe["timestamp"], errors="coerce"
        )
        self.assertEqual(int(timestamps.notna().sum()), 310)
        self.assertEqual(int(timestamps.nunique()), 310)

    def test_observed_fields_never_enter_model_payload(self):
        payload = model_inputs_from_record(
            self.dataframe.iloc[0].to_dict()
        )
        self.assertFalse(
            any(key.startswith("observed_") for key in payload)
        )
        self.assertTrue(
            all(
                not key.startswith("observed_")
                for record in self.records
                for key in record["model_inputs"]
            )
        )

    def test_blank_capacities_remain_missing_and_assumption_labeled(self):
        row = self.dataframe.iloc[0].to_dict()
        provenance = capacity_provenance_from_record(row)
        for column in CAPACITY_COLUMNS:
            self.assertTrue(pd.isna(self.dataframe[column]).all())
            self.assertIsNone(provenance[column]["csv_value"])
            self.assertEqual(
                provenance[column]["label"],
                "TAIVAS assumption / user input",
            )
            self.assertFalse(provenance[column]["observed"])

        snapshot = build_empirical_validation_snapshot(
            self.records[0], self._sample_results()
        )
        self.assertEqual(
            snapshot["capacity"]["installed_capacity_label"],
            "TAIVAS assumption / user input",
        )
        self.assertEqual(
            snapshot["capacity"]["capacity_source"],
            "Not available in current RTE / ERA5 extracts",
        )

    def test_empirical_weather_fields_map_exactly(self):
        row = self.dataframe.iloc[0].to_dict()
        payload = model_inputs_from_record(row)
        for column in (
            "temperature",
            "wind_speed",
            "solar_radiation",
            "precipitation",
            "humidity",
        ):
            self.assertEqual(payload[column], float(row[column]))

    def test_non_first_timestamp_selects_exact_weather_row(self):
        record = self._select_timestamp("2026-06-24 17:00:00")
        self.assertEqual(
            record["model_inputs"]["temperature"],
            40.0214,
        )
        self.assertEqual(
            record["model_inputs"]["wind_speed"],
            0.547533,
        )
        self.assertEqual(
            record["model_inputs"]["solar_radiation"],
            638.311111,
        )
        self.assertEqual(record["model_inputs"]["precipitation"], 0.0)
        self.assertEqual(
            record["model_inputs"]["humidity"],
            22.735792,
        )

    def test_switching_timestamps_updates_all_weather_inputs(self):
        weather_columns = (
            "temperature",
            "wind_speed",
            "solar_radiation",
            "precipitation",
            "humidity",
        )
        timestamps = (
            "2026-06-18 02:00:00",
            "2026-06-24 17:00:00",
            "2026-06-30 23:00:00",
        )
        previous_weather = None
        for timestamp in timestamps:
            record = self._select_timestamp(timestamp)
            source_row = self.dataframe.loc[
                pd.to_datetime(self.dataframe["timestamp"])
                == pd.Timestamp(timestamp)
            ].iloc[0]
            current_weather = tuple(
                record["model_inputs"][column]
                for column in weather_columns
            )
            expected_weather = tuple(
                float(source_row[column])
                for column in weather_columns
            )
            self.assertEqual(current_weather, expected_weather)
            if previous_weather is not None:
                self.assertNotEqual(current_weather, previous_weather)
            previous_weather = current_weather

    def test_timestamp_weather_and_observed_snapshot_share_one_row(self):
        timestamp = "2026-06-24 17:00:00"
        record = self._select_timestamp(timestamp)
        source_row = self.dataframe.loc[
            pd.to_datetime(self.dataframe["timestamp"])
            == pd.Timestamp(timestamp)
        ].iloc[0]
        snapshot = build_empirical_validation_snapshot(
            record,
            self._sample_results(),
        )

        self.assertEqual(
            snapshot["selected_observation"]["timestamp"],
            timestamp,
        )
        for column in (
            "temperature",
            "wind_speed",
            "solar_radiation",
            "precipitation",
            "humidity",
        ):
            self.assertEqual(
                snapshot["selected_observation"][column],
                float(source_row[column]),
            )
        for column, value in record["observed"].items():
            expected = source_row[column]
            if pd.isna(expected):
                self.assertIsNone(value)
            else:
                self.assertEqual(value, float(expected))

    def test_observed_local_generation_remains_an_unscaled_mw_value(self):
        record = self._select_timestamp("2026-06-24 17:00:00")
        snapshot = build_empirical_validation_snapshot(
            record,
            self._sample_results(),
        )
        rte = snapshot["rte"]

        self.assertEqual(rte["observed_demand_mw"], 9287.5)
        self.assertEqual(rte["observed_renewable_generation_mw"], 407.0)
        self.assertEqual(rte["observed_local_generation_mw"], 407.0)
        self.assertEqual(rte["observed_external_support_mw"], 8883.75)
        self.assertEqual(rte["observed_battery_net_mw"], -0.25)
        self.assertEqual(rte["observed_import_dependency_pct"], 95.65115)
        self.assertEqual(
            format_observed_mw_for_display(
                rte["observed_local_generation_mw"]
            ),
            "407.0 MW",
        )
        self.assertNotEqual(
            format_observed_mw_for_display(
                rte["observed_local_generation_mw"]
            ),
            "4.07 MW",
        )

    def test_missing_weather_row_is_rejected(self):
        invalid = self.dataframe.iloc[[0]].copy()
        invalid.loc[invalid.index[0], "temperature"] = None
        findings = validate_empirical_dataframe(invalid)
        self.assertTrue(
            any(
                finding["severity"] == "Error"
                and "temperature" in finding["message"]
                for finding in findings
            )
        )
        self.assertEqual(build_empirical_records(invalid), [])

    def test_general_mode_has_no_empirical_snapshot(self):
        results = self._sample_results()
        self.assertIsNone(
            build_empirical_validation_snapshot(None, results)
        )

    def test_comparison_snapshot_does_not_modify_results(self):
        results = self._sample_results()
        before = copy.deepcopy(results)
        snapshot = build_empirical_validation_snapshot(
            self.records[0], results
        )
        self.assertEqual(results, before)
        self.assertEqual(snapshot["taivas"]["simulated_demand_mw"], 100.0)
        self.assertNotIn("accuracy", snapshot)
        self.assertNotIn("calibration", snapshot)

    def test_authoritative_core_files_are_unchanged(self):
        expected_hashes = {
            "core/energy_balance_phase2.py": (
                "c0f162b6c8b8f481cf915dc2eacd048f"
                "2e510f58382c7c4c581043b752633c5f"
            ),
            "core/risk_engine.py": (
                "c6ffb77dc58401e0613a1ae42c2389e7"
                "5bcca6ec33b20b4c3db6a0b9f5fbe381"
            ),
        }
        for relative_path, expected_hash in expected_hashes.items():
            actual_hash = hashlib.sha256(
                (PROJECT_ROOT / relative_path).read_bytes()
            ).hexdigest()
            self.assertEqual(actual_hash, expected_hash)

    @staticmethod
    def _sample_results():
        return {
            "demand": 100.0,
            "renewable_supply": 60.0,
            "battery_discharge": 10.0,
            "battery_levels": 20.0,
            "external_support_need_proxy": 30.0,
            "system_performance_score": 70.0,
            "risk_tier": "High",
        }

    def _select_timestamp(self, timestamp):
        label = next(
            record["selector_label"]
            for record in self.records
            if record["model_inputs"]["timestamp"] == timestamp
        )
        selected = select_empirical_record(self.records, label)
        self.assertIsNotNone(selected)
        return selected


if __name__ == "__main__":
    unittest.main()
