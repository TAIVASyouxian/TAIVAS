import unittest

from core.scenario_compatibility import (
    get_allowed_scenarios,
    evaluate_scenario_plausibility,
    build_scenario_warning,
    get_geological_hazard_module_note,
)


class ScenarioCompatibilityTests(unittest.TestCase):
    def test_taiwan_does_not_show_blizzard_general_mode(self):
        self.assertNotIn("blizzard", get_allowed_scenarios("Taiwan", "Taipei", "General Mode"))

    def test_taiwan_can_show_blizzard_advanced_with_low_warning(self):
        self.assertIn("blizzard", get_allowed_scenarios("Taiwan", "Taipei", "Advanced Stress Testing"))
        warning = build_scenario_warning("Taiwan", "Taipei", "blizzard", "Advanced Stress Testing")
        self.assertTrue(warning["show_warning"])
        self.assertEqual(warning["label"], "Scenario Plausibility: LOW")

    def test_sweden_can_show_blizzard_general_mode(self):
        self.assertIn("blizzard", get_allowed_scenarios("Sweden", "Stockholm", "General Mode"))

    def test_germany_can_show_cold_wave_and_storm(self):
        allowed = get_allowed_scenarios("Germany", "Berlin", "General Mode")
        self.assertIn("cold_wave", allowed)
        self.assertIn("storm", allowed)

    def test_unknown_country_falls_back_safely(self):
        allowed = get_allowed_scenarios("Unknown", "Unknown City", "General Mode")
        self.assertIn("normal", allowed)
        evaluation = evaluate_scenario_plausibility("Unknown", "Unknown City", "typhoon")
        self.assertEqual(evaluation["plausibility"], "MEDIUM")

    def test_geological_hazards_are_not_selectable(self):
        for mode in ["General Mode", "Advanced Stress Testing"]:
            allowed = get_allowed_scenarios("Taiwan", "Taipei", mode)
            self.assertNotIn("earthquake", allowed)
            self.assertNotIn("volcanic_eruption", allowed)
        self.assertIn("planned but not enabled", get_geological_hazard_module_note())


if __name__ == "__main__":
    unittest.main()
