"""TAIVAS Workflow Coordination Layer V3.

Pure business-logic helpers for semi-autonomous workflow coordination.
No Streamlit imports. No infrastructure control. Human review remains required.
"""


ALERT_ORDER = {
    "NORMAL": 0,
    "WATCH": 1,
    "WARNING": 2,
    "CRITICAL": 3,
}


def evaluate_alert_escalation(alert_state, monitoring_signals=None, drift=None, history=None):
    """Evaluate whether the current alert requires workflow escalation."""
    monitoring_signals = monitoring_signals or {}
    drift = drift or {}
    history = history or []
    current_alert = str(alert_state.get("alert_state", "NORMAL")).upper()
    current_level = ALERT_ORDER.get(current_alert, 0)

    repeated_shortfall = monitoring_signals.get("shortfall_trend", 0) > 0
    declining_storage = monitoring_signals.get("battery_trend", 0) < 0 or monitoring_signals.get("reserve_trend", 0) < 0
    sustained_drift = bool(drift.get("drift_detected"))
    prior_alerts = [str(item.get("alert_state", "")).upper() for item in history if isinstance(item, dict)]
    previous_level = max([ALERT_ORDER.get(item, 0) for item in prior_alerts], default=0)

    escalation_required = (
        current_level >= 2
        or current_level > previous_level
        or (current_level >= 1 and (repeated_shortfall or declining_storage or sustained_drift))
    )
    if current_alert == "CRITICAL":
        escalation_reason = "Critical alert state requires immediate human review."
    elif current_level > previous_level:
        escalation_reason = "Alert state increased compared with previous monitoring history."
    elif repeated_shortfall:
        escalation_reason = "Energy gap trend is increasing."
    elif declining_storage:
        escalation_reason = "Storage or reserve trend is declining."
    elif sustained_drift:
        escalation_reason = "Operational drift from baseline remains present."
    else:
        escalation_reason = "No workflow escalation required under current assumptions."

    return {
        "current_alert": current_alert,
        "previous_alert_level": previous_level,
        "current_alert_level": current_level,
        "escalation_required": escalation_required,
        "escalation_reason": escalation_reason,
    }


def generate_review_queue(alert_state, advisory, monitoring, drift, escalation):
    """Create operational review queue items."""
    queue = []
    alert = str(alert_state.get("alert_state", "NORMAL")).upper()
    queue.append({
        "Task": "Confirm scenario assumptions",
        "Status": "Pending Review",
        "Priority": "High" if alert in {"WARNING", "CRITICAL"} else "Normal",
        "Owner": "Human reviewer",
    })
    queue.append({
        "Task": "Review agentic advisory",
        "Status": "Advisory Generated",
        "Priority": "High" if advisory.get("risk_tier") in {"HIGH", "CRITICAL"} else "Normal",
        "Owner": "Operations / analyst",
    })
    if escalation.get("escalation_required"):
        queue.append({
            "Task": "Evaluate alert escalation",
            "Status": "Monitoring Escalated",
            "Priority": "High",
            "Owner": "Operations lead",
        })
    if drift.get("drift_detected"):
        queue.append({
            "Task": "Review baseline drift",
            "Status": "Human Review Required",
            "Priority": "High" if alert in {"WARNING", "CRITICAL"} else "Normal",
            "Owner": "Energy resilience analyst",
        })
    queue.append({
        "Task": "Approve, defer, or revise operational response",
        "Status": "Human Review Required",
        "Priority": "High" if alert in {"WARNING", "CRITICAL"} else "Normal",
        "Owner": "Qualified decision-maker",
    })
    return queue


def generate_executive_snapshot(context, alert_state, advisory, monitoring, drift, escalation):
    """Generate concise executive workflow snapshot."""
    location = f"{context.get('city', '-')}, {context.get('country', '-')}"
    scenario = str(context.get("scenario", "-")).replace("_", " ").title()
    alert = alert_state.get("alert_state", "NORMAL")
    risk = advisory.get("risk_tier", "LOW")
    summary = (
        f"TAIVAS V3 workflow reports {alert} monitoring status and {risk} advisory risk "
        f"for {location} under {scenario}. {escalation.get('escalation_reason')} "
        "Human confirmation is required before operational changes."
    )
    return {
        "location": location,
        "scenario": scenario,
        "alert_state": alert,
        "advisory_risk_tier": risk,
        "stress_stage": monitoring.get("stress_stage"),
        "drift_detected": drift.get("drift_detected", False),
        "escalation_required": escalation.get("escalation_required", False),
        "summary": summary,
    }


def create_operational_briefing(context, review_queue, executive_snapshot, monitoring_summary):
    """Create export-ready operational briefing text."""
    lines = [
        "# TAIVAS V3 Operational Workflow Briefing",
        "",
        f"- Location: {executive_snapshot.get('location')}",
        f"- Scenario: {executive_snapshot.get('scenario')}",
        f"- Alert State: {executive_snapshot.get('alert_state')}",
        f"- Advisory Risk Tier: {executive_snapshot.get('advisory_risk_tier')}",
        f"- Escalation Required: {executive_snapshot.get('escalation_required')}",
        "",
        "## Executive Snapshot",
        executive_snapshot.get("summary", ""),
        "",
        "## Monitoring Interpretation",
        monitoring_summary.get("daily_monitoring_summary", ""),
        "",
        "## Operational Review Queue",
    ]
    for item in review_queue:
        lines.append(f"- [{item.get('Status')}] {item.get('Task')} | Priority: {item.get('Priority')} | Owner: {item.get('Owner')}")
    lines.extend([
        "",
        "## Governance Boundary",
        "TAIVAS may recommend, organize, summarize, escalate, monitor, and prepare reports. "
        "It must not directly control infrastructure, self-authorize operational changes, or bypass human review.",
    ])
    return "\n".join(lines)


def build_operational_workflow(context, advisory, monitoring_state, recommendation_history=None):
    """Coordinate advisory, monitoring, drift, escalation, queue, and briefing."""
    recommendation_history = recommendation_history or []
    monitoring = monitoring_state.get("monitoring", {})
    alert = monitoring_state.get("alert", {})
    drift = monitoring_state.get("drift", {})
    monitoring_summary = monitoring_state.get("summary", {})
    escalation = evaluate_alert_escalation(alert, monitoring, drift, recommendation_history)
    review_queue = generate_review_queue(alert, advisory, monitoring, drift, escalation)
    executive_snapshot = generate_executive_snapshot(context, alert, advisory, monitoring, drift, escalation)
    briefing = create_operational_briefing(context, review_queue, executive_snapshot, monitoring_summary)
    workflow_timeline = [
        {"Step": "Scenario Selected", "Status": "Complete"},
        {"Step": "Monitoring Started", "Status": "Complete"},
        {"Step": "Drift Detected", "Status": "Review" if drift.get("drift_detected") else "No material drift"},
        {"Step": "Advisory Generated", "Status": "Complete"},
        {"Step": "Alert Escalation Evaluated", "Status": "Escalated" if escalation.get("escalation_required") else "No escalation"},
        {"Step": "Human Review Pending", "Status": "Required"},
        {"Step": "Export Generated", "Status": "Available"},
    ]
    history = recommendation_history + [{
        "alert_state": alert.get("alert_state"),
        "risk_tier": advisory.get("risk_tier"),
        "summary": executive_snapshot.get("summary"),
    }]
    return {
        "escalation": escalation,
        "review_queue": review_queue,
        "executive_snapshot": executive_snapshot,
        "workflow_timeline": workflow_timeline,
        "recommendation_history": history[-8:],
        "operational_briefing_markdown": briefing,
    }
