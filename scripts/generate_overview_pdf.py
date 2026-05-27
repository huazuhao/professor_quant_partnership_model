#!/usr/bin/env python3
"""
Generate the public PDF overview for the professor quant partnership model.
"""

from pathlib import Path
from textwrap import wrap

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUTPUT_PATH = Path("professor_quant_partnership_model_overview.pdf")

COLORS = {
    "ink": "#111827",
    "muted": "#374151",
    "blue": "#e8f2ff",
    "green": "#eaf8ef",
    "yellow": "#fff4d7",
    "red": "#ffecec",
    "violet": "#f1efff",
    "teal": "#0f766e",
    "line": "#1f2937",
}


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def escape_text(value: str) -> str:
    return value.replace("$", r"\$")


def new_page():
    fig = plt.figure(figsize=(8.5, 11), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def add_text(
    ax,
    x,
    y,
    value,
    size=12,
    weight="normal",
    color=None,
    ha="left",
    va="top",
    width=None,
    line_spacing=1.35,
):
    color = color or COLORS["ink"]
    if width:
        lines = []
        for paragraph in value.split("\n"):
            lines.extend(wrap(paragraph, width=width) or [""])
        value = "\n".join(lines)
    ax.text(
        x,
        y,
        escape_text(value),
        fontsize=size,
        fontweight=weight,
        color=color,
        ha=ha,
        va=va,
        linespacing=line_spacing,
    )


def add_box(ax, x, y, w, h, title, body="", fill="#ffffff", metric=None):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=1.6,
        edgecolor=COLORS["line"],
        facecolor=fill,
    )
    ax.add_patch(patch)
    add_text(ax, x + 0.025, y + h - 0.028, title, size=13, weight="bold")
    if metric:
        add_text(ax, x + 0.025, y + h - 0.075, metric, size=20, weight="bold")
        add_text(ax, x + 0.14, y + h - 0.072, body, size=10.5, color=COLORS["muted"], width=32)
    elif body:
        wrap_width = max(14, int(w * 95))
        add_text(ax, x + 0.025, y + h - 0.07, body, size=10.5, color=COLORS["muted"], width=wrap_width)


def add_arrow(ax, start, end, rad=0.0):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=18,
            linewidth=1.8,
            color=COLORS["line"],
            connectionstyle=f"arc3,rad={rad}",
        )
    )


def add_title_page(pdf):
    fig, ax = new_page()
    add_text(ax, 0.08, 0.94, "Professor Quant Partnership Model", size=25, weight="bold")
    add_text(
        ax,
        0.08,
        0.90,
        "A simulation of an LLM-enabled funding model for university research labs",
        size=13.5,
        color=COLORS["muted"],
    )
    add_text(
        ax,
        0.08,
        0.865,
        "Repository: https://github.com/huazuhao/professor_quant_partnership_model",
        size=10.5,
        color=COLORS["muted"],
    )

    readme_intro = [
        (
            "This repository studies a new research-lab funding model made possible by the rapid "
            "improvement of LLM coding."
        ),
        (
            "University labs in mathematics, statistics, optimization, simulation, computational "
            "modeling, and related STEM fields already have the talent systematic hedge funds rely on. "
            "The old bottleneck was implementation: turning a research idea into clean data, backtests, "
            "diagnostics, risk controls, deployment code, and monitoring usually took more engineering "
            "time than a short sabbatical or research leave could support."
        ),
        (
            "LLM-assisted coding changes that. A 6-12 month sabbatical or one-year leave can now be "
            "enough for professors to help invent or improve systematic trading strategies. If validated "
            "strategies are traded, part of the profits can fund the contributing labs over the following years."
        ),
        (
            "In the current simulation, this loop can start with $20M of initial capital and grow into a "
            "$1B+ fund. The median 10-year investor outcome is about 3x capital, roughly 140-150 professors "
            "or labs participate, and five-year lab compensation is above $1M at the median."
        ),
    ]
    y = 0.815
    for idx, paragraph in enumerate(readme_intro):
        add_text(
            ax,
            0.08,
            y,
            paragraph,
            size=12.5 if idx == 0 else 11.7,
            weight="bold" if idx == 3 else "normal",
            color=COLORS["teal"] if idx == 3 else COLORS["muted"],
            width=92,
        )
        y -= 0.095 if idx in (0, 2) else 0.155

    add_text(ax, 0.08, 0.19, "What the simulation tests", size=15, weight="bold")
    add_text(
        ax,
        0.08,
        0.16,
        "Whether focused professor research, LLM-accelerated implementation, fund infrastructure, "
        "strategy profits, and recurring lab support can become a large alternative funding channel "
        "for universities.",
        size=11.5,
        color=COLORS["muted"],
        width=92,
    )
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_funding_loop_page(pdf):
    fig, ax = new_page()
    add_text(ax, 0.08, 0.94, "The Funding Loop", size=23, weight="bold")
    add_text(ax, 0.08, 0.90, "A short research leave becomes strategy development, fund infrastructure, and recurring lab support.", size=12, color=COLORS["muted"])

    y = 0.52
    add_box(ax, 0.07, y, 0.18, 0.11, "Professors", "Math, stats, optimization, simulation", COLORS["blue"])
    add_box(ax, 0.31, y, 0.18, 0.11, "LLM coding", "Faster prototypes, tests, iteration", COLORS["green"])
    add_box(ax, 0.55, y, 0.18, 0.11, "Strategies", "Invented, improved, validated", COLORS["yellow"])
    add_box(ax, 0.78, y, 0.15, 0.11, "Fund", "Trades validated systems", COLORS["violet"])
    add_arrow(ax, (0.25, y + 0.055), (0.31, y + 0.055))
    add_arrow(ax, (0.49, y + 0.055), (0.55, y + 0.055))
    add_arrow(ax, (0.73, y + 0.055), (0.78, y + 0.055))

    add_box(ax, 0.18, 0.28, 0.27, 0.12, "Lab funding", "Direct strategy-professor payouts plus safety-net support", COLORS["red"])
    add_box(ax, 0.58, 0.28, 0.29, 0.12, "6-12 month leave", "A short sabbatical can support several years of lab funding", COLORS["blue"])
    add_arrow(ax, (0.855, y), (0.73, 0.40), rad=0.2)
    add_arrow(ax, (0.58, 0.34), (0.45, 0.34))
    add_arrow(ax, (0.18, 0.34), (0.13, y), rad=-0.25)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_accounting_page(pdf):
    fig, ax = new_page()
    add_text(ax, 0.08, 0.94, "Current Simulated Accounting", size=23, weight="bold")
    add_text(ax, 0.08, 0.90, "Performance compensation is paid only after investor drawdowns are recovered.", size=12.5, color=COLORS["muted"])
    add_box(ax, 0.15, 0.78, 0.70, 0.085, "Quarterly fund NAV", "Strategies produce net trading P&L. Losses reduce NAV first.", COLORS["blue"])
    add_arrow(ax, (0.50, 0.775), (0.50, 0.72))
    add_box(ax, 0.15, 0.62, 0.70, 0.085, "Management fee", "charged quarterly", COLORS["yellow"], metric="0.25%")
    add_arrow(ax, (0.50, 0.615), (0.50, 0.56))
    add_box(
        ax,
        0.15,
        0.44,
        0.70,
        0.105,
        "Investor high-water mark test",
        "Investor cohorts must recover prior drawdowns. No performance allocation is paid below net HWM.",
        COLORS["green"],
    )
    add_arrow(ax, (0.50, 0.435), (0.50, 0.38))
    add_box(
        ax,
        0.21,
        0.28,
        0.58,
        0.10,
        "Performance pool",
        "above-HWM profits at crystallization",
        COLORS["violet"],
        metric="20%",
    )
    add_arrow(ax, (0.50, 0.275), (0.28, 0.17), rad=-0.12)
    add_arrow(ax, (0.50, 0.275), (0.72, 0.17), rad=0.12)
    add_box(ax, 0.08, 0.07, 0.36, 0.10, "Strategy professors", "Paid by strategy ownership weights", COLORS["blue"], metric="50%")
    add_box(ax, 0.56, 0.07, 0.36, 0.10, "Safety net", "Guarantees up to $1M support", COLORS["red"], metric="50%")
    add_text(ax, 0.08, 0.025, "Eligible profits after HWM: 80% fund/investors, 10% strategy professors, 10% safety net.", size=10.5, color=COLORS["muted"])
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_results_page(pdf):
    fig, ax = new_page()
    add_text(ax, 0.08, 0.94, "Current Simulation Results", size=23, weight="bold")
    add_text(ax, 0.08, 0.90, "Baseline batch run: 100 paths, 40 quarters, seed 42.", size=12.5, color=COLORS["muted"])
    rows = [
        ("Initial capital", "$20M"),
        ("Final fund AUM after 10 years", "about $1.27B median"),
        ("10-year investor outcome", "about 3x capital"),
        ("Professors/labs after 10 years", "138.5 median"),
        ("Five-year professor/lab compensation", "$1.34M median"),
        ("Five-year compensation, p75", "$1.63M"),
        ("Five-year compensation, p90", "$2.00M"),
        ("$100 reference investment ending value", "$302.52 median"),
    ]
    x0, y0, w, row_h = 0.08, 0.80, 0.84, 0.072
    left_w = 0.54
    right_x = x0 + left_w + 0.03
    ax.add_patch(FancyBboxPatch((x0, y0), w, row_h, boxstyle="square,pad=0", facecolor=COLORS["green"], edgecolor=COLORS["line"], linewidth=1.1))
    add_text(ax, x0 + 0.025, y0 + row_h / 2, "Metric", size=12, weight="bold", va="center")
    add_text(ax, right_x, y0 + row_h / 2, "Current baseline result", size=12, weight="bold", va="center")
    for i, (metric, value) in enumerate(rows):
        yrow = y0 - (i + 1) * row_h
        fill = "#ffffff" if i % 2 == 0 else "#f8fafc"
        ax.add_patch(FancyBboxPatch((x0, yrow), w, row_h, boxstyle="square,pad=0", facecolor=fill, edgecolor="#d1d5db", linewidth=0.8))
        add_text(ax, x0 + 0.025, yrow + row_h / 2, metric, size=11.2, color=COLORS["muted"], va="center")
        add_text(ax, right_x, yrow + row_h / 2, value, size=11.5, weight="bold", va="center")
    add_text(ax, 0.08, 0.12, "Interpretation", size=15, weight="bold")
    add_text(
        ax,
        0.08,
        0.09,
        "These are simulation outputs, not forecasts. The purpose is to test whether the economic loop "
        "is internally coherent and whether the scale of the research-funding impact is large enough to "
        "justify deeper investigation.",
        size=11.5,
        color=COLORS["muted"],
        width=92,
    )
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_chart_page(pdf, image_path: str, title: str):
    fig, ax = new_page()
    add_text(ax, 0.08, 0.94, title, size=23, weight="bold")
    path = Path(image_path)
    if path.exists():
        image_ax = fig.add_axes([0.06, 0.34, 0.88, 0.40])
        image_ax.imshow(plt.imread(path))
        image_ax.axis("off")
    else:
        add_text(ax, 0.08, 0.82, f"Missing chart: {image_path}", size=12, color=COLORS["muted"])
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main():
    with PdfPages(OUTPUT_PATH) as pdf:
        add_title_page(pdf)
        add_funding_loop_page(pdf)
        add_accounting_page(pdf)
        add_results_page(pdf)
        add_chart_page(pdf, "batch_plot1_investment_value_distribution.png", "Chart 1: Investor Outcome Distribution")
        add_chart_page(pdf, "batch_plot2_5year_compensation_distribution.png", "Chart 2: Five-Year Professor/Lab Compensation")
        add_chart_page(pdf, "batch_plot3_final_aum_distribution.png", "Chart 3: Final Fund AUM")
        add_chart_page(pdf, "batch_plot4_total_author_count_distribution.png", "Chart 4: Total Professors/Labs")
        add_chart_page(pdf, "batch_plot5_paid_author_count_distribution.png", "Chart 5: Paid Professors/Labs")
    print(f"Wrote {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()
