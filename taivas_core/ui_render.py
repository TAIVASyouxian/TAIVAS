import matplotlib.pyplot as plt
import streamlit as st


def mini_card(label: str, value: str):
    st.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)


def page_question(tab_label: str, tr, page_questions: dict, lang: str):
    st.markdown(f'<div class="question"><b>{tr("page_answers")}</b> {page_questions[lang][tab_label]}</div>', unsafe_allow_html=True)


def concept_badge(tr):
    st.markdown(f'<div class="badge">{tr("concept_badge")}</div>', unsafe_allow_html=True)


def render_capacity_factor_chart(capacity_factors, tr, lang: str):
    labels = list(capacity_factors.keys())
    values = [capacity_factors[k] for k in labels]
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    ax.barh(labels, values)
    ax.set_xlabel("Capacity Factor (%)" if lang == "English" else "容量因子 (%)")
    ax.set_xlim(0, 100)
    ax.set_title(tr("capacity_factors"))
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)


def render_delta_chart(delta_df, tr):
    fig, ax = plt.subplots(figsize=(8.8, 4.0))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    metric_col = tr("metric") if tr("metric") in delta_df.columns else "Metric"
    delta_col = tr("delta") if tr("delta") in delta_df.columns else "Delta"
    ax.barh(delta_df[metric_col], delta_df[delta_col])
    ax.axvline(0, linewidth=1.0)
    ax.set_title(tr("baseline_vs_selected"))
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)


def render_critical_load_chart(df, tr):
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    col = f"{tr('demand')} (MW)"
    ax.bar(df["Category"], df[col])
    ax.set_ylabel(col)
    ax.set_title(tr("critical_breakdown"))
    ax.grid(axis="y", alpha=0.22)
    plt.xticks(rotation=15)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)


def render_forecast_chart(multistep_df, tr, build_forecast_chart_df):
    st.subheader(tr("forecast_chart"))
    st.markdown(f'<div class="note">{tr("forecast_chart_note")}</div>', unsafe_allow_html=True)
    chart_df = build_forecast_chart_df(multistep_df)
    if not chart_df.empty:
        st.line_chart(chart_df)
