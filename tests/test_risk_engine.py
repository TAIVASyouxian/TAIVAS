import unittest

from core.risk_engine import calculate_risk_tier


class RiskEngineTests(unittest.TestCase):
    def test_normal_no_shortfall_is_low(self):
        self.assertEqual(calculate_risk_tier(0, 100), "Low")

    def test_moderate_shortfall_is_elevated(self):
        self.assertEqual(calculate_risk_tier(2, 100), "Elevated")

    def test_high_shortfall_threshold(self):
        self.assertEqual(calculate_risk_tier(10, 100), "High")

    def test_critical_shortfall_threshold(self):
        self.assertEqual(calculate_risk_tier(20, 100), "Critical")


if __name__ == "__main__":
    unittest.main()
