import json
import unittest

from export.audit_export import audit_record_to_json


class AuditExportTests(unittest.TestCase):
    def test_audit_json_schema_minimum(self):
        record = {
            "audit_id": "taivas-test",
            "simulation_outputs": {"shortfall": 0},
            "model_boundary": "Decision-support only.",
        }
        parsed = json.loads(audit_record_to_json(record))
        self.assertIn("audit_id", parsed)
        self.assertIn("simulation_outputs", parsed)
        self.assertIn("model_boundary", parsed)


if __name__ == "__main__":
    unittest.main()
