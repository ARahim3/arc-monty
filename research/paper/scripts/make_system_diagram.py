"""System diagram for the writeup: Monty-ARC's pipeline (top) and the hybrid merge inside the Kaggle notebook (bottom).

Palette matches the cover (tools/make_cover.py): surface #fcfcfb, ink #0b0b0b; categorical slots 1-3 of the
reference palette identify the three columns (Monty-ARC blue, Qwen orange, NVARC aqua). Text always wears ink tokens.
Usage: python research/paper/scripts/make_system_diagram.py  ->  research/paper/figures/system_diagram.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "figures", "system_diagram.png")
SURFACE, INK, INK2, MUTED, RULE = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#d9d8d3"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
TINT = {BLUE: "#e8f0fb", ORANGE: "#fdeee7", AQUA: "#e5f6ef", None: "#f3f2ef"}

fig = plt.figure(figsize=(16, 9), dpi=100)
fig.patch.set_facecolor(SURFACE)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis("off")


def box(x, y, w, h, title, body=None, color=None, title_size=14, body_size=11, lw=1.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.12", linewidth=lw,
                                edgecolor=color or RULE, facecolor=TINT[color]))
    ty = y + h - 0.22
    ax.text(x + 0.18, ty, title, ha="left", va="top", fontsize=title_size, fontweight="bold", color=INK)
    if body:
        ax.text(x + 0.18, ty - 0.36 - 0.04 * title_size / 14, body, ha="left", va="top", fontsize=body_size,
                color=INK2, linespacing=1.35)


def arrow(x0, y0, x1, y1, color=MUTED, lw=2.0, style="-|>", rad=0.0):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=16, linewidth=lw,
                                 color=color, connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))


# ------------------------------------------------------------------ header
ax.text(0.45, 8.6, "Monty-ARC: learning modules that vote, and know when they know", ha="left", va="top",
        fontsize=24, fontweight="bold", color=INK)
ax.text(0.45, 8.02, "Top: one task, solved on CPU in ~1-2 s with no training data.  Bottom: the Kaggle notebook, "
        "where Monty-ARC is one column beside two neural solvers.", ha="left", va="top", fontsize=13, color=INK2)

# ------------------------------------------------------------------ top row: the Monty-ARC pipeline
Y0, H = 4.3, 3.15
box(0.45, Y0, 2.35, H, "ARC task", "2-5 demo pairs\n(input -> output)\n+ test input(s)\n\nno pretraining,\nno other tasks", None)
box(3.15, Y0, 2.75, H, "Sensor module",
    "objects: 4/8-connected,\nsingle- or multi-colour\n\neach at a D8-canonical\npose (object-centric\nreference frame)\n\n"
    "change sensor:\ninput <-> output diff", BLUE)

# learning modules: 8 columns
LX, LW = 6.25, 4.55
box(LX, Y0, LW, H, "8 learning modules (columns)", None, BLUE)
mods = [("self-model", "symmetry, local self-similarity"), ("periodic", "toroidal frames"),
        ("behavior", "change in object frame"), ("dynamics", "ray / move / fill / connect"),
        ("composition", "panels vote, select, tile"), ("association", "templates, in-task legends"),
        ("pattern", "recognise-and-act"), ("field", "marker-anchored location code")]
cw, ch = 2.08, 0.47
for i, (name, desc) in enumerate(mods):
    cx = LX + 0.15 + (i % 2) * (cw + 0.09)
    cy = Y0 + H - 1.02 - (i // 2) * (ch + 0.08)
    ax.add_patch(FancyBboxPatch((cx, cy), cw, ch, boxstyle="round,pad=0,rounding_size=0.07", linewidth=1.0,
                                edgecolor=BLUE, facecolor=SURFACE))
    ax.text(cx + 0.1, cy + ch - 0.08, name, ha="left", va="top", fontsize=10.5, fontweight="bold", color=INK)
    ax.text(cx + 0.1, cy + 0.07, desc, ha="left", va="bottom", fontsize=8.6, color=INK2)
ax.text(LX + 0.18, Y0 + 0.24, "each: hypotheses x frame -> fit all demos -> LOO evidence",
        ha="left", va="center", fontsize=10, color=INK)

box(11.15, Y0, 2.15, H, "Voting",
    "identical output\ngrids pool evidence\nacross modules\n\nconfident only if\nLOO evidence = 1.0\nand it out-votes\n"
    "rivals >= 2:1", BLUE)
box(13.65, Y0, 1.95, H, "2 attempts",
    "1: best hypothesis\n2: strongest one\n    that disagrees\n(hypothesis-testing\npolicy)\n\n+ confident flag\nor abstain", BLUE)
for xa, xb in ((2.8, 3.15), (5.9, 6.25), (10.8, 11.15), (13.3, 13.65)):
    arrow(xa, Y0 + H / 2, xb, Y0 + H / 2, color=INK2)

# LOO explanation strip
ax.text(0.45, Y0 - 0.14, "Leave-one-out (LOO) evidence: learn the rule from all demos but one, predict the held-out demo, "
        "repeat for each demo.\nThis is Monty's \"predict the next sensation\" test, applied to whole demonstrations.",
        ha="left", va="top", fontsize=10.5, color=MUTED, linespacing=1.35)


def elbow(points, color, lw=1.6):
    xs, ys = zip(*points[:-1])
    ax.plot(xs, ys, color=color, linewidth=lw, solid_capstyle="round", solid_joinstyle="round")
    arrow(points[-2][0], points[-2][1], points[-1][0], points[-1][1], color=color, lw=lw)


# ------------------------------------------------------------------ bottom row: the hybrid notebook
BY, BH = 0.5, 2.45
ax.text(0.45, BY + BH + 0.42, "Kaggle notebook (12 h, 4x L4, offline)", ha="left", va="center", fontsize=14,
        fontweight="bold", color=INK)
box(0.45, BY, 3.3, BH, "Qwen3.8-27B (GPU)",
    "program synthesis, <=2 rounds\nwith cell-diff feedback\n\na program counts as verified\nif it reproduces every demo",
    ORANGE)
box(4.05, BY, 3.3, BH, "NVARC public fork (GPU)",
    "Qwen3-4B + per-task LoRA\ntest-time training,\naugmentation rescoring\n\nskips Qwen-verified tasks", AQUA)
box(7.65, BY, 3.15, BH, "Monty-ARC (CPU)",
    "runs in the background\nthe whole time (nice 19)\n\nconfident answers\n+ best guesses", BLUE)
box(11.15, BY, 3.0, BH, "Merge, per test output",
    "1  verified Qwen program\n2  confident Monty-ARC\n3  NVARC candidates\n4  unverified Qwen,\n    Monty-ARC guesses\n"
    "first 2 distinct grids kept", None)
ax.text(14.5, BY + BH / 2 + 0.25, "pass@2", ha="left", va="center", fontsize=13, fontweight="bold", color=INK)
ax.text(14.5, BY + BH / 2 - 0.15, "submission", ha="left", va="center", fontsize=11, color=INK2)
arrow(14.15, BY + BH / 2, 14.45, BY + BH / 2, color=INK2)
# columns -> merge, along a bus under the boxes
BUS = 0.22
for x, c in ((2.1, ORANGE), (5.7, AQUA), (9.225, BLUE)):
    ax.plot([x, x], [BY, BUS], color=c, linewidth=1.6, solid_capstyle="round")
ax.plot([2.1, 12.65], [BUS, BUS], color=INK2, linewidth=1.6, solid_capstyle="round")
arrow(12.65, BUS, 12.65, BY, color=INK2, lw=1.6)
# the Monty-ARC pipeline's output is the Monty-ARC column
elbow([(14.6, Y0), (14.6, 3.62), (9.9, 3.62), (9.9, BY + BH)], BLUE)
fig.savefig(OUT, facecolor=SURFACE)
print("saved", os.path.abspath(OUT))
