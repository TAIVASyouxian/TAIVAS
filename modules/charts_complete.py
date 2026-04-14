"""
TAIVAS charts module
Reusable chart helpers for Streamlit dashboard rendering.
"""

from typing import Dict, Optional

import matplotlib.pyplot as plt


def make_donut_chart(mix_pct: Dict[str, float], renewable_ratio: float, title: Optional[str] = None):
    labels = list(mix_pct.keys())
    values = [max(float(mix_pct.get(k, 0.0)), 0.0) for k in labels]

    if sum(values) <= 0:
        labels = ["No Output"]
        values = [100.0]

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    wedges, _ = ax.pie(
        values,
        startangle=90,
        wedgeprops=dict(width=0.36, edgecolor="white", linewidth=1.5),
        labels=None,
    )

    center_color = "#1f2937"
    text_top = "Renewable" if labels != ["No Output"] else "No Supply"
    ax.text(0, 0.08, text_top, ha="center", va="center", fontsize=18, weight="bold", color=center_color)
    ax.text(0, -0.08, f"{renewable_ratio:.1f}%", ha="center", va="center", fontsize=16, weight="bold", color=center_color)

    legend_labels = [f"{label} — {value:.1f}%" for label, value in zip(labels, values)]
    legend = ax.legend(
        wedges,
        legend_labels,
        loc="center left",
        bbox_to_anchor=(0.98, 0.5),
        frameon=False,
        fontsize=11,
    )
    for text in legend.get_texts():
        text.set_color("#1f2937")

    ax.set_title(title or "Renewable Energy Mix", fontsize=17, pad=16, color="#111827")
    ax.axis("equal")
    plt.subplots_adjust(left=0.04, right=0.80, top=0.90, bottom=0.06)
    return fig
