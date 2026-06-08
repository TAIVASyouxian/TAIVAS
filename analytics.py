import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st


ANALYTICS_DB_PATH = Path(os.getenv("TAIVAS_ANALYTICS_DB", "taivas_analytics.sqlite3"))


def _utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_query_param(name, default=""):
    try:
        value = st.query_params.get(name, default)
        if isinstance(value, list):
            return str(value[0]) if value else default
        return str(value) if value is not None else default
    except Exception:
        return default


def get_tracking_context():
    """Return anonymous visitor/source context without cookies, IP, email, or PII."""
    try:
        if "taivas_visitor_id" not in st.session_state:
            st.session_state["taivas_visitor_id"] = f"anon_{uuid.uuid4().hex[:12]}"
        return {
            "visitor_id": st.session_state.get("taivas_visitor_id", "anon_unknown"),
            "source": _safe_query_param("source", "direct") or "direct",
            "campaign": _safe_query_param("campaign", "none") or "none",
        }
    except Exception:
        return {"visitor_id": "anon_unavailable", "source": "unknown", "campaign": "unknown"}


def init_analytics_db():
    """Create the anonymous analytics table. Fail silently to protect the main app."""
    try:
        with sqlite3.connect(ANALYTICS_DB_PATH) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS taivas_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    visitor_id TEXT,
                    source TEXT,
                    campaign TEXT,
                    event_name TEXT NOT NULL,
                    country TEXT,
                    city TEXT,
                    scenario TEXT,
                    details_json TEXT
                )
                """
            )
            conn.commit()
    except Exception:
        return None


def log_event(event_name, country=None, city=None, scenario=None, details=None):
    """Log one anonymous event. Tracking errors never interrupt TAIVAS."""
    try:
        init_analytics_db()
        context = get_tracking_context()
        details_json = json.dumps(details or {}, ensure_ascii=False, default=str)
        with sqlite3.connect(ANALYTICS_DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO taivas_events (
                    ts, visitor_id, source, campaign, event_name,
                    country, city, scenario, details_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _utc_timestamp(),
                    context.get("visitor_id"),
                    context.get("source"),
                    context.get("campaign"),
                    str(event_name),
                    country,
                    city,
                    scenario,
                    details_json,
                ),
            )
            conn.commit()
    except Exception:
        return None


def log_once(event_name, once_key=None, country=None, city=None, scenario=None, details=None):
    """Log an event only once per Streamlit session to avoid rerun duplication."""
    try:
        key = f"taivas_logged_once_{once_key or event_name}"
        if st.session_state.get(key):
            return
        log_event(event_name, country=country, city=city, scenario=scenario, details=details)
        st.session_state[key] = True
    except Exception:
        return None


def read_analytics_summary():
    try:
        init_analytics_db()
        with sqlite3.connect(ANALYTICS_DB_PATH) as conn:
            return conn.execute(
                """
                SELECT
                    COALESCE(source, 'unknown') AS source,
                    COALESCE(campaign, 'unknown') AS campaign,
                    event_name,
                    COUNT(*) AS event_count,
                    COUNT(DISTINCT visitor_id) AS unique_visitors
                FROM taivas_events
                GROUP BY source, campaign, event_name
                ORDER BY event_count DESC, event_name ASC
                """
            ).fetchall()
    except Exception:
        return []


def read_latest_events(limit=100):
    try:
        init_analytics_db()
        with sqlite3.connect(ANALYTICS_DB_PATH) as conn:
            return conn.execute(
                """
                SELECT
                    ts, visitor_id, source, campaign, event_name,
                    country, city, scenario, details_json
                FROM taivas_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
    except Exception:
        return []
