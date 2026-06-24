#!/usr/bin/env python3
"""
Generate the Vector Grove entity and economics flow diagram.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUTPUT_PATH = Path("assets/vector_grove_entity_flow.png")


COLORS = {
    "ink": "#111827",
    "muted": "#4b5563",
    "arrow": "#374151",
    "manager": "#f8c8d8",
    "fund": "#fbd5e4",
    "gp": "#fce7f3",
    "professor": "#cab2d6",
    "lab": "#d8f89a",
    "investor": "#a9d3f5",
    "vc": "#f6a0ad",
}


def draw_box(ax, xy, width, height, title, subtitle=None, fill="#ffffff", title_size=16):
    x, y = xy
    shadow = FancyBboxPatch(
        (x + 0.012, y - 0.012),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.01",
        linewidth=0,
        facecolor="#000000",
        alpha=0.12,
        zorder=1,
    )
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.01",
        linewidth=0.9,
        edgecolor="#e5e7eb",
        facecolor=fill,
        zorder=2,
    )
    ax.add_patch(shadow)
    ax.add_patch(box)
    ax.text(
        x + width / 2,
        y + height * 0.61,
        title,
        ha="center",
        va="center",
        fontsize=title_size,
        fontweight="bold" if title_size <= 13 else "normal",
        color=COLORS["ink"],
        zorder=3,
    )
    if subtitle:
        ax.text(
            x + width / 2,
            y + height * 0.25,
            subtitle,
            ha="center",
            va="center",
            fontsize=8.8,
            color=COLORS["muted"],
            linespacing=1.25,
            zorder=3,
        )


def arrow(ax, start, end, label=None, label_offset=(0, 0), rad=0.0):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=1.3,
        color=COLORS["arrow"],
        connectionstyle=f"arc3,rad={rad}",
        zorder=4,
    )
    ax.add_patch(patch)
    if label:
        mx = (start[0] + end[0]) / 2 + label_offset[0]
        my = (start[1] + end[1]) / 2 + label_offset[1]
        ax.text(
            mx,
            my,
            label,
            ha="center",
            va="center",
            fontsize=7.6,
            color=COLORS["muted"],
            linespacing=1.1,
            zorder=5,
        )


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11.0, 7.2), dpi=600)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Nodes
    draw_box(
        ax,
        (0.345, 0.585),
        0.31,
        0.16,
        "Vector Grove\nCapital Management, Inc.",
        "holds hedge fund intellectual property\ntrading strategies, risk controls, execution,\nresearch tools, data",
        COLORS["manager"],
        title_size=14.2,
    )
    draw_box(
        ax,
        (0.385, 0.305),
        0.23,
        0.125,
        "Vector Grove\nFund, LP",
        "Investment vehicle",
        COLORS["fund"],
        title_size=15,
    )
    draw_box(
        ax,
        (0.055, 0.610),
        0.22,
        0.12,
        "Professors",
        "domain experts / quant\nresearch collaborators",
        COLORS["professor"],
        title_size=14,
    )
    draw_box(
        ax,
        (0.745, 0.625),
        0.22,
        0.105,
        "University Research Labs",
        "funded by eligible\nstrategy economics",
        COLORS["lab"],
        title_size=10.5,
    )
    draw_box(
        ax,
        (0.395, 0.075),
        0.21,
        0.105,
        "Fund Investors",
        "endowments, family offices,\naccredited investors",
        COLORS["investor"],
        title_size=11.5,
    )
    draw_box(
        ax,
        (0.390, 0.850),
        0.22,
        0.105,
        "VC Strategic\nInvestors",
        "operating company equity",
        COLORS["vc"],
        title_size=11.5,
    )

    # Arrows
    arrow(ax, (0.275, 0.670), (0.345, 0.670))
    arrow(ax, (0.655, 0.670), (0.745, 0.670))
    arrow(ax, (0.475, 0.850), (0.475, 0.745), "equity\ninvestment", (-0.035, 0.000))
    arrow(ax, (0.525, 0.745), (0.525, 0.850), "equity\ngrowth", (0.038, 0.000))
    arrow(ax, (0.475, 0.585), (0.475, 0.430), "investment\nmanagement", (-0.040, -0.002))
    arrow(ax, (0.525, 0.430), (0.525, 0.585), "management and\nperformance fees", (0.061, -0.002))
    arrow(ax, (0.475, 0.180), (0.475, 0.305), "invest", (-0.036, 0.000))
    arrow(ax, (0.525, 0.305), (0.525, 0.180), "profit / NAV\nreturns", (0.044, 0.000))

    plt.tight_layout(pad=0.25)
    fig.savefig(OUTPUT_PATH, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()
