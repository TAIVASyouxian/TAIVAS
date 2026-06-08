import os

import pandas as pd
import streamlit as st

from analytics import init_analytics_db, read_analytics_summary, read_latest_events


def _configured_access_key():
    try:
        return st.secrets.get("TAIVAS_ANALYTICS_ACCESS_KEY", None)
    except Exception:
        return os.getenv("TAIVAS_ANALYTICS_ACCESS_KEY")


st.set_page_config(page_title="TAIVAS Analytics Dashboard", layout="wide")
st.title("TAIVAS Analytics Dashboard")
st.caption("Internal anonymous testing analytics. No names, emails, IP addresses, or cookies are collected.")

access_key = _configured_access_key()
if not access_key:
    st.warning(
        "Analytics dashboard is locked. Set TAIVAS_ANALYTICS_ACCESS_KEY in Streamlit Secrets "
        "or environment variables to view this internal page."
    )
    st.stop()

entered_key = st.text_input("Access key", type="password")
if entered_key != access_key:
    st.info("Enter the internal analytics access key to view anonymous testing events.")
    st.stop()

init_analytics_db()

summary_rows = read_analytics_summary()
latest_rows = read_latest_events(limit=200)

summary_df = pd.DataFrame(
    summary_rows,
    columns=["source", "campaign", "event_name", "event_count", "unique_visitors"],
)
latest_df = pd.DataFrame(
    latest_rows,
    columns=[
        "ts",
        "visitor_id",
        "source",
        "campaign",
        "event_name",
        "country",
        "city",
        "scenario",
        "details_json",
    ],
)

st.subheader("Summary")
if summary_df.empty:
    st.info("No analytics events recorded yet.")
else:
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

st.subheader("Latest Events")
if latest_df.empty:
    st.info("No latest events to display.")
else:
    st.dataframe(latest_df, use_container_width=True, hide_index=True)
