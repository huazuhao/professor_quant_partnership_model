#!/usr/bin/env python3
"""
Generate the university partnership structure memo PDF.
"""

from pathlib import Path
import re
from textwrap import wrap

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


SOURCE_PATH = Path("UNIVERSITY_PARTNERSHIP_STRUCTURE_MEMO.md")
OUTPUT_PATH = Path("university_partnership_structure_memo.pdf")
LETTER_SIZE = (8.5, 11)

COLORS = {
    "ink": "#111827",
    "muted": "#4b5563",
    "heading": "#0f766e",
    "rule": "#d1d5db",
    "code_bg": "#f8fafc",
    "caption": "#374151",
}

DIAGRAM_COLORS = {
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

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


class MemoPdf:
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.pdf = PdfPages(output_path)
        self.page_number = 0
        self.fig = None
        self.ax = None
        self.y = 0.0
        self.in_code_block = False
        self.code_buffer = []

    def __enter__(self):
        self.new_page()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.save_page()
        self.pdf.close()

    def new_page(self):
        if self.fig is not None:
            self.save_page()
        self.page_number += 1
        self.fig = plt.figure(figsize=LETTER_SIZE, facecolor="white")
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis("off")
        self.y = 0.91
        self.header_footer()

    def save_page(self):
        if self.fig is not None:
            self.pdf.savefig(self.fig)
            plt.close(self.fig)
            self.fig = None
            self.ax = None

    def header_footer(self):
        assert self.ax is not None
        self.ax.text(
            0.075,
            0.965,
            "University Partnership Structure Memo",
            fontsize=9.2,
            color=COLORS["muted"],
            ha="left",
            va="top",
        )
        self.ax.plot([0.075, 0.925], [0.947, 0.947], color=COLORS["rule"], linewidth=0.8)
        self.ax.plot([0.075, 0.925], [0.06, 0.06], color=COLORS["rule"], linewidth=0.8)
        self.ax.text(
            0.925,
            0.038,
            f"Page {self.page_number}",
            fontsize=8.8,
            color=COLORS["muted"],
            ha="right",
            va="bottom",
        )

    def ensure_space(self, needed: float):
        if self.y - needed < 0.085:
            self.new_page()

    def text(self, value: str, size: float, weight="normal", color=None, indent=0.0, width=94, leading=1.34):
        color = color or COLORS["ink"]
        lines = []
        for paragraph in value.split("\n"):
            lines.extend(wrap(paragraph, width=width) or [""])
        line_height = size / 780 * leading
        block_height = line_height * max(1, len(lines))
        self.ensure_space(block_height + 0.012)
        assert self.ax is not None
        self.ax.text(
            0.075 + indent,
            self.y,
            "\n".join(lines).replace("$", r"\$"),
            fontsize=size,
            fontweight=weight,
            color=color,
            ha="left",
            va="top",
            linespacing=leading,
        )
        self.y -= block_height

    def heading(self, value: str, level: int):
        if level == 1:
            self.ensure_space(0.09)
            self.text(value, size=22, weight="bold", color=COLORS["ink"], width=62, leading=1.1)
            self.y -= 0.016
        elif level == 2:
            self.ensure_space(0.055)
            self.y -= 0.010
            self.text(value, size=14.5, weight="bold", color=COLORS["heading"], width=76, leading=1.15)
            self.y -= 0.004
        else:
            self.ensure_space(0.044)
            self.y -= 0.006
            self.text(value, size=11.8, weight="bold", color=COLORS["ink"], width=82, leading=1.15)
            self.y -= 0.002

    def bullet(self, value: str):
        wrapped = wrap(value, width=87)
        line_height = 10.2 / 780 * 1.30
        self.ensure_space(line_height * max(1, len(wrapped)) + 0.008)
        assert self.ax is not None
        self.ax.text(0.092, self.y, u"\u2022", fontsize=10.5, color=COLORS["muted"], ha="left", va="top")
        self.ax.text(
            0.112,
            self.y,
            "\n".join(wrapped).replace("$", r"\$"),
            fontsize=10.2,
            color=COLORS["ink"],
            ha="left",
            va="top",
            linespacing=1.30,
        )
        self.y -= line_height * max(1, len(wrapped))

    def code(self, lines):
        lines = lines or [""]
        line_height = 9.5 / 780 * 1.25
        self.ensure_space(line_height * len(lines) + 0.026)
        assert self.ax is not None
        height = line_height * len(lines) + 0.020
        rect = plt.Rectangle(
            (0.085, self.y - height + 0.005),
            0.83,
            height,
            facecolor=COLORS["code_bg"],
            edgecolor=COLORS["rule"],
            linewidth=0.8,
        )
        self.ax.add_patch(rect)
        self.ax.text(
            0.102,
            self.y - 0.006,
            "\n".join(lines).replace("$", r"\$"),
            fontsize=9.5,
            family="DejaVu Sans Mono",
            color=COLORS["muted"],
            ha="left",
            va="top",
            linespacing=1.25,
        )
        self.y -= height + 0.006

    def image(self, image_path: Path, alt_text: str):
        if not image_path.exists():
            self.text(f"[Missing image: {image_path}]", size=9.8, color=COLORS["muted"])
            return

        if image_path.name == "vector_grove_entity_flow.png":
            self.entity_flow_diagram(alt_text)
            return

        img = plt.imread(image_path)
        img_height, img_width = img.shape[:2]
        aspect = img_height / img_width
        width = 0.85
        height = min(width * aspect, 0.54)

        self.ensure_space(height + 0.045)
        assert self.ax is not None
        left = 0.075
        top = self.y
        self.ax.imshow(
            img,
            extent=(left, left + width, top - height, top),
            aspect="auto",
            zorder=1,
        )
        self.y -= height + 0.010
        if alt_text:
            self.text(alt_text, size=8.8, color=COLORS["caption"], width=92, leading=1.22)
            self.y -= 0.004

    def entity_flow_diagram(self, alt_text: str):
        width = 0.85
        height = 0.54

        self.ensure_space(height + 0.050)
        assert self.ax is not None

        left = 0.075
        bottom = self.y - height

        def tx(x):
            return left + x * width

        def ty(y):
            return bottom + y * height

        def draw_box(x, y, w, h, title, subtitle=None, fill="#ffffff", title_size=13.0):
            shadow = FancyBboxPatch(
                (tx(x + 0.012), ty(y - 0.012)),
                w * width,
                h * height,
                boxstyle="round,pad=0.006,rounding_size=0.007",
                linewidth=0,
                facecolor="#000000",
                alpha=0.12,
                zorder=1,
            )
            box = FancyBboxPatch(
                (tx(x), ty(y)),
                w * width,
                h * height,
                boxstyle="round,pad=0.006,rounding_size=0.007",
                linewidth=0.7,
                edgecolor="#e5e7eb",
                facecolor=fill,
                zorder=2,
            )
            self.ax.add_patch(shadow)
            self.ax.add_patch(box)
            self.ax.text(
                tx(x + w / 2),
                ty(y + h * 0.61),
                title,
                ha="center",
                va="center",
                fontsize=title_size,
                fontweight="bold" if title_size <= 11.5 else "normal",
                color=DIAGRAM_COLORS["ink"],
                linespacing=1.08,
                zorder=3,
            )
            if subtitle:
                self.ax.text(
                    tx(x + w / 2),
                    ty(y + h * 0.25),
                    subtitle,
                    ha="center",
                    va="center",
                    fontsize=7.0,
                    color=DIAGRAM_COLORS["muted"],
                    linespacing=1.18,
                    zorder=3,
                )

        def arrow(start, end, label=None, label_offset=(0, 0), rad=0.0):
            patch = FancyArrowPatch(
                (tx(start[0]), ty(start[1])),
                (tx(end[0]), ty(end[1])),
                arrowstyle="-|>",
                mutation_scale=11,
                linewidth=1.0,
                color=DIAGRAM_COLORS["arrow"],
                connectionstyle=f"arc3,rad={rad}",
                zorder=4,
            )
            self.ax.add_patch(patch)
            if label:
                self.ax.text(
                    tx((start[0] + end[0]) / 2 + label_offset[0]),
                    ty((start[1] + end[1]) / 2 + label_offset[1]),
                    label,
                    ha="center",
                    va="center",
                    fontsize=6.3,
                    color=DIAGRAM_COLORS["muted"],
                    linespacing=1.05,
                    zorder=5,
                )

        draw_box(
            0.345,
            0.585,
            0.31,
            0.16,
            "Vector Grove\nCapital Management, Inc.",
            "holds hedge fund intellectual property\ntrading strategies, risk controls, execution,\nresearch tools, data",
            DIAGRAM_COLORS["manager"],
            12.2,
        )
        draw_box(
            0.385,
            0.305,
            0.23,
            0.125,
            "Vector Grove\nFund, LP",
            "Investment vehicle",
            DIAGRAM_COLORS["fund"],
            12.4,
        )
        draw_box(
            0.055,
            0.610,
            0.22,
            0.12,
            "Professors",
            "domain experts / quant\nresearch collaborators",
            DIAGRAM_COLORS["professor"],
            11.2,
        )
        draw_box(
            0.745,
            0.625,
            0.22,
            0.105,
            "University Research Labs",
            "funded by eligible\nstrategy economics",
            DIAGRAM_COLORS["lab"],
            8.4,
        )
        draw_box(
            0.395,
            0.075,
            0.21,
            0.105,
            "Fund Investors",
            "endowments, family offices,\naccredited investors",
            DIAGRAM_COLORS["investor"],
            9.5,
        )
        draw_box(
            0.390,
            0.850,
            0.22,
            0.105,
            "VC Strategic\nInvestors",
            "operating company equity",
            DIAGRAM_COLORS["vc"],
            9.6,
        )

        arrow((0.275, 0.670), (0.345, 0.670))
        arrow((0.655, 0.670), (0.745, 0.670))
        arrow((0.475, 0.850), (0.475, 0.745), "equity\ninvestment", (-0.035, 0.000))
        arrow((0.525, 0.745), (0.525, 0.850), "equity\ngrowth", (0.038, 0.000))
        arrow((0.475, 0.585), (0.475, 0.430), "investment\nmanagement", (-0.040, -0.002))
        arrow((0.525, 0.430), (0.525, 0.585), "management and\nperformance fees", (0.061, -0.002))
        arrow((0.475, 0.180), (0.475, 0.305), "invest", (-0.036, 0.000))
        arrow((0.525, 0.305), (0.525, 0.180), "profit / NAV\nreturns", (0.044, 0.000))

        self.y -= height + 0.010
        if alt_text:
            self.text(alt_text, size=8.8, color=COLORS["caption"], width=92, leading=1.22)
            self.y -= 0.004

    def blank(self):
        self.y -= 0.012


def parse_markdown_line(line: str, doc: MemoPdf):
    stripped = line.rstrip()
    if stripped.startswith("```"):
        if doc.in_code_block:
            doc.code(doc.code_buffer)
            doc.code_buffer = []
            doc.in_code_block = False
            doc.blank()
        else:
            doc.code_buffer = []
            doc.in_code_block = True
        return
    if doc.in_code_block:
        doc.code_buffer.append(stripped)
        return
    if not stripped:
        doc.blank()
        return
    if stripped.startswith("# "):
        doc.heading(stripped[2:].strip(), 1)
        return
    if stripped.startswith("## "):
        doc.heading(stripped[3:].strip(), 2)
        return
    if stripped.startswith("### "):
        doc.heading(stripped[4:].strip(), 3)
        return
    if stripped.startswith("- "):
        doc.bullet(stripped[2:].strip())
        return
    image_match = re.match(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)", stripped)
    if image_match:
        doc.image(Path(image_match.group("path")), image_match.group("alt").strip())
        return
    if stripped[0].isdigit() and ". " in stripped[:4]:
        doc.bullet(stripped.split(". ", 1)[1].strip())
        return
    doc.text(stripped, size=10.7, color=COLORS["ink"], width=91)


def main():
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(SOURCE_PATH)

    lines = SOURCE_PATH.read_text(encoding="utf-8").splitlines()
    with MemoPdf(OUTPUT_PATH) as doc:
        for line in lines:
            parse_markdown_line(line, doc)
    print(f"Wrote {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()
