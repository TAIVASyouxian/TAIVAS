import unittest

from core.energy_balance_phase2 import (
    calculate_system_performance_score,
    update_battery_state,
)


class BatteryUnitConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.common = {
            "scenario_battery_factor": 1.0,
            "battery_availability": 1.0,
            "lag_penalty": 1.0,
            "loss_rate": 0.04,
            "interval_hours": 1.0,
        }

    def test_zero_stored_energy_cannot_discharge(self):
        result = update_battery_state(
            battery_current_mwh=0.0,
            battery_capacity_mwh=100.0,
            renewable_surplus_power_mw=0.0,
            shortage_power_mw=25.0,
            **self.common,
        )
        self.assertEqual(result["discharge_energy_mwh"], 0.0)
        self.assertEqual(result["battery_next_mwh"], 0.0)

    def test_zero_capacity_battery_cannot_charge_or_discharge(self):
        result = update_battery_state(
            battery_current_mwh=10.0,
            battery_capacity_mwh=0.0,
            renewable_surplus_power_mw=50.0,
            shortage_power_mw=50.0,
            **self.common,
        )
        self.assertEqual(result["charge_energy_mwh"], 0.0)
        self.assertEqual(result["discharge_energy_mwh"], 0.0)
        self.assertEqual(result["battery_next_mwh"], 0.0)

    def test_full_battery_does_not_accept_surplus_charge(self):
        result = update_battery_state(
            battery_current_mwh=100.0,
            battery_capacity_mwh=100.0,
            renewable_surplus_power_mw=40.0,
            shortage_power_mw=0.0,
            **self.common,
        )
        self.assertEqual(result["charge_energy_mwh"], 0.0)
        self.assertEqual(result["battery_next_mwh"], 100.0)

    def test_surplus_charging_applies_one_hour_conversion_and_loss(self):
        result = update_battery_state(
            battery_current_mwh=20.0,
            battery_capacity_mwh=100.0,
            renewable_surplus_power_mw=10.0,
            shortage_power_mw=0.0,
            **self.common,
        )
        self.assertAlmostEqual(result["charge_power_mw"], 3.0)
        self.assertAlmostEqual(result["charge_energy_mwh"], 3.0)
        self.assertAlmostEqual(result["loss_energy_mwh"], 0.12)
        self.assertAlmostEqual(result["battery_next_mwh"], 22.88)

    def test_shortage_discharge_is_energy_bounded(self):
        result = update_battery_state(
            battery_current_mwh=10.0,
            battery_capacity_mwh=100.0,
            renewable_surplus_power_mw=0.0,
            shortage_power_mw=50.0,
            **self.common,
        )
        self.assertLessEqual(result["discharge_energy_mwh"] + result["loss_energy_mwh"], 10.0 + 1e-9)
        self.assertGreaterEqual(result["battery_next_mwh"], 0.0)

    def test_capacity_bounds_are_enforced(self):
        result = update_battery_state(
            battery_current_mwh=120.0,
            battery_capacity_mwh=100.0,
            renewable_surplus_power_mw=100.0,
            shortage_power_mw=0.0,
            **self.common,
        )
        self.assertEqual(result["battery_current_mwh"], 100.0)
        self.assertEqual(result["battery_next_mwh"], 100.0)

    def test_one_hour_mw_to_mwh_conversion(self):
        result = update_battery_state(
            battery_current_mwh=50.0,
            battery_capacity_mwh=100.0,
            renewable_surplus_power_mw=0.0,
            shortage_power_mw=5.0,
            **self.common,
        )
        self.assertAlmostEqual(result["discharge_power_mw"], result["discharge_energy_mwh"])

    def test_charge_and_dispatch_limits_are_preserved(self):
        charge = update_battery_state(
            battery_current_mwh=0.0,
            battery_capacity_mwh=100.0,
            renewable_surplus_power_mw=100.0,
            shortage_power_mw=0.0,
            **self.common,
        )
        discharge = update_battery_state(
            battery_current_mwh=100.0,
            battery_capacity_mwh=100.0,
            renewable_surplus_power_mw=0.0,
            shortage_power_mw=100.0,
            **self.common,
        )
        self.assertAlmostEqual(charge["charge_power_mw"], 30.0)
        self.assertAlmostEqual(discharge["discharge_energy_mwh"], 35.0)

    def test_nearly_empty_battery_cannot_overdeliver(self):
        result = update_battery_state(
            battery_current_mwh=0.5,
            battery_capacity_mwh=100.0,
            renewable_surplus_power_mw=0.0,
            shortage_power_mw=100.0,
            **self.common,
        )
        self.assertLessEqual(result["discharge_energy_mwh"] + result["loss_energy_mwh"], 0.5 + 1e-9)
        self.assertGreaterEqual(result["battery_next_mwh"], 0.0)

    def test_repeatability(self):
        kwargs = dict(
            battery_current_mwh=50.0,
            battery_capacity_mwh=100.0,
            renewable_surplus_power_mw=0.0,
            shortage_power_mw=12.0,
            **self.common,
        )
        self.assertEqual(update_battery_state(**kwargs), update_battery_state(**kwargs))


class SystemPerformanceScoreTests(unittest.TestCase):
    def test_fully_served_demand_is_one_hundred_percent(self):
        self.assertEqual(calculate_system_performance_score(100.0, 0.0), 100.0)

    def test_normalized_score_is_percentage_of_demand_served(self):
        self.assertEqual(calculate_system_performance_score(100.0, 10.0), 90.0)

    def test_score_is_scale_invariant(self):
        self.assertEqual(calculate_system_performance_score(100.0, 10.0), calculate_system_performance_score(1000.0, 100.0))

    def test_zero_demand_is_not_applicable(self):
        self.assertIsNone(calculate_system_performance_score(0.0, 0.0))

    def test_no_supply_is_zero_percent(self):
        self.assertEqual(calculate_system_performance_score(100.0, 100.0), 0.0)

    def test_oversupply_or_negative_gap_is_bounded_at_one_hundred(self):
        self.assertEqual(calculate_system_performance_score(100.0, -10.0), 100.0)

    def test_gap_larger_than_demand_is_bounded_at_zero(self):
        self.assertEqual(calculate_system_performance_score(100.0, 150.0), 0.0)

    def test_old_and_new_scores_differ_by_demand_scale(self):
        """Retain the historical regression-test name without executing the removed rule."""
        self.assertEqual(calculate_system_performance_score(100.0, 10.0), 90.0)
        self.assertEqual(calculate_system_performance_score(1000.0, 10.0), 99.0)


if __name__ == "__main__":
    unittest.main()
