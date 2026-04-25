"""Export and audit helpers for TAIVAS.

This module keeps CSV/TXT/JSON export packaging outside the Streamlit UI file.
It does not perform Streamlit rendering; the main app still owns download buttons.
"""

from __future__ import annotations

import json
from io import StringIO
from typing import Any, Callable

import pandas as pd


def dataframe_to_csv_text(df: pd.DataFrame) -> str:
    """Return a CSV string from a DataFrame without exposing buffer logic in the UI."""
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


def build_executive_summary_text(
    *,
    demo_mode: str,
    active_city: str,
    active_country: str,
    facility_type: str,
    scenario_key: str,
    energy_security_scenario: str,
    results: dict[str, Any],
    timeline_results: dict[str, Any],
    geopolitical_shock: dict[str, Any],
) -> str:
    """Build the plain-text executive summary downloaded from the Export Center."""
    lines = [
        "TAIVAS Executive Summary",
        "========================",
        f"Demo Mode: {demo_mode}",
        f"Location: {active_city}, {active_country}",
        f"Facility: {facility_type}",
        f"Weather Scenario: {scenario_key}",
        f"Energy Security Scenario: {energy_security_scenario}",
        "",
        "Core Metrics",
        f"- Demand: {results['demand']} MW",
        f"- Renewable Supply: {results['renewable_supply']} MW",
        f"- Final Supply: {results['final_supply']} MW",
        f"- Shortfall: {results['shortfall']} MW",
        f"- Battery Remaining: {results['battery_levels']} MWh",
        f"- System Efficiency: {results['system_efficiency']}%",
        f"- Grid Dependency: {results['grid_dependency']}%",
        "",
        "Risk Notes",
        f"- Geopolitical Risk Level: {geopolitical_shock.get('risk_level', 'N/A')}",
        f"- Oil/Gas Supply Disruption: {geopolitical_shock.get('oil_supply_disruption_percent', 0)}%",
        f"- Estimated Hours Until Shortfall: {timeline_results.get('hours_until_shortfall')}",
        f"- Estimated Hours Until Critical Failure: {timeline_results.get('hours_until_critical_failure')}",
        "",
        "Model Limitation",
        "TAIVAS is a decision-support simulator. It does not guarantee real-world outcomes and does not replace engineering, grid-operator, legal, security, or emergency-management validation.",
    ]
    return "\n".join(lines)


def build_audit_trail_json(
    *,
    version: str,
    demo_mode: str,
    active_country: str,
    active_city: str,
    facility_type: str,
    scenario_key: str,
    results: dict[str, Any],
    timeline_results: dict[str, Any],
    geopolitical_shock: dict[str, Any],
) -> str:
    """Build a JSON audit trail for Pro/Enterprise-style traceability."""
    audit_payload = {
        "version": version,
        "demo_mode": demo_mode,
        "country": active_country,
        "city": active_city,
        "facility_type": facility_type,
        "scenario_key": scenario_key,
        "results": results,
        "timeline": timeline_results,
        "geopolitical_shock": geopolitical_shock,
        "model_limitation": "Decision-support simulation only; not a prediction or guarantee.",
    }
    return json.dumps(audit_payload, indent=2, ensure_ascii=False)


def build_export_payloads(
    *,
    comparison_df: pd.DataFrame,
    reason_chain_rows: list[dict[str, Any]],
    demo_mode: str,
    active_city: str,
    active_country: str,
    facility_type: str,
    scenario_key: str,
    energy_security_scenario: str,
    results: dict[str, Any],
    timeline_results: dict[str, Any],
    geopolitical_shock: dict[str, Any],
    version: str = "V4 Export Split",
) -> dict[str, str]:
    """Package all downloadable export content in one place."""
    return {
        "scenario_csv": dataframe_to_csv_text(comparison_df),
        "reason_csv": dataframe_to_csv_text(pd.DataFrame(reason_chain_rows)),
        "summary_txt": build_executive_summary_text(
            demo_mode=demo_mode,
            active_city=active_city,
            active_country=active_country,
            facility_type=facility_type,
            scenario_key=scenario_key,
            energy_security_scenario=energy_security_scenario,
            results=results,
            timeline_results=timeline_results,
            geopolitical_shock=geopolitical_shock,
        ),
        "audit_json": build_audit_trail_json(
            version=version,
            demo_mode=demo_mode,
            active_country=active_country,
            active_city=active_city,
            facility_type=facility_type,
            scenario_key=scenario_key,
            results=results,
            timeline_results=timeline_results,
            geopolitical_shock=geopolitical_shock,
        ),
    }
