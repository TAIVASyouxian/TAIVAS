"""Audit export helpers for TAIVAS."""

import json


def audit_record_to_json(record):
    """Serialize an audit record with stable formatting."""
    return json.dumps(record, indent=2, ensure_ascii=False)
