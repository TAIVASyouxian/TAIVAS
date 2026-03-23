"""
TAIVAS charts module
Reusable chart helpers for Streamlit dashboard rendering.
"""

from typing import Dict

import matplotlib.pyplot as plt


def make_donut_chart(mix_pct: Dict[str, float], renewable_ratio: float):
    labels = list(mix_pct.keys())
    values = [mix_pct[k] for k in labels]

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    wedges, _ = ax.pie(
        values,
        startangle=90,
        wedgeprops=dict(width=0.36, edgecolor="white", linewidth=1.5),
        labels=None,
    )

    ax.text(0, 0.08, "Renewable", ha="center", va="center", fontsize=20, weight="bold", color="white")
    ax.text(0, -0.08, f"{renewable_ratio:.1f}%", ha="center", va="center", fontsize=17, weight="bold", color="white")

    legend_labels = [f"{label} — {value:.1f}%" for label, value in zip(labels, values)]
    legend = ax.legend(
        wedges,
        legend_labels,
        loc="center left",
        bbox_to_anchor=(0.98, 0.5),
        frameon=False,
        fontsize=12,
    )
    for text in legend.get_texts():
        text.set_color("white")

    ax.set_title("Renewable Energy Mix", fontsize=18, pad=16, color="white")
    ax.axis("equal")
    plt.subplots_adjust(left=0.04, right=0.80, top=0.90, bottom=0.06)
    return fig
