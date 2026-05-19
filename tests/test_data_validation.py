import unittest
from io import StringIO

import pandas as pd

from data.csv_loader import read_csv_with_warnings
from data.validation_utils import validate_uploaded_dataframe


class DataValidationTests(unittest.TestCase):
    def test_malformed_csv_falls_back_with_warning(self):
        df, warnings = read_csv_with_warnings(StringIO('"unclosed'))
        self.assertIsNone(df)
        self.assertTrue(warnings)

    def test_empty_dataframe_validation(self):
        findings = validate_uploaded_dataframe(pd.DataFrame())
        self.assertEqual(findings[0]["Severity"], "High")

    def test_invalid_numeric_column_warning(self):
        df = pd.DataFrame({"population": ["not-a-number"]})
        findings = validate_uploaded_dataframe(df)
        self.assertTrue(any("population" in finding["Finding"] for finding in findings))


if __name__ == "__main__":
    unittest.main()
