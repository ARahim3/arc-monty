"""Figure 4 (optional): the named notebook, Tri v3, as a pipeline.

Content from research/paper/v8/paper.md, Section 9 only (the "confident" label is
the v5 heuristic of Appendix C, which the notebook's confident() implements:
evidence >= 0.99 and a 2:1 lead). Drawn new; it does not reuse
research/paper/figures/system_diagram.png.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import fig_style as S

S.setup()

W, H = 16.0, 7.95
fig = plt.figure(figsize=(W * S.CM, H * S.CM))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")

FS, LINE = 8, 0.37


def box(x0, y0, x1, y1, fc=S.SURFACE, ec=S.AXIS, lw=0.8, ls="-", z=2):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                                boxstyle="round,pad=0,rounding_size=0.12",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))


def text_block(x, y_top, items, ha="left"):
    """items: (text, weight, colour) top-down."""
    for k, (t, wt, c) in enumerate(items):
        ax.text(x, y_top - k * LINE, t, ha=ha, va="top", fontsize=FS,
                fontweight=wt, color=c, zorder=5)


def arrow(p0, p1, ls="-", color=S.INK2, cs=None):
    kw = dict(arrowstyle="-|>", mutation_scale=7, lw=0.8, color=color, ls=ls,
              shrinkA=0, shrinkB=0, zorder=3)
    if cs:
        kw["connectionstyle"] = cs
    ax.add_patch(FancyArrowPatch(p0, p1, **kw))


ax.text(0.15, 7.8, "Tri v3, the named notebook: offline on 4×L4 GPUs, 12 hours less a 10-minute buffer",
        ha="left", va="top", fontsize=FS + 1, fontweight="bold")

SX0, SX1 = 0.15, 8.55        # source boxes
MX0, MX1 = 9.35, 15.85       # merge box
I, P = S.INK, S.INK2

# Qwen
q = (5.35, 6.95)
box(SX0, q[0], SX1, q[1])
text_block(SX0 + 0.2, q[1] - 0.17, [
    ("Qwen3.8-27B program synthesis", "bold", I),
    ("GPU, first, up to 4.5 h", "normal", P),
    ("one sample per task, reverse alphabetical order; at most two", "normal", I),
    ("rounds of 16,384 thinking + 6,144 answer tokens; 10 s sandbox", "normal", I),
])

# NVARC
nv = (2.6, 4.7)
box(SX0, nv[0], SX1, nv[1])
text_block(SX0 + 0.2, nv[1] - 0.17, [
    ("NVARC fork", "bold", I),
    ("GPU, then until the deadline", "normal", P),
    ("mikelou1's public performance patch of the 33.89 baseline:", "normal", I),
    ("pretrained Qwen3-4B, per-task test-time training with 128", "normal", I),
    ("augmentations, depth-first decoding with 16, rescoring", "normal", I),
])
# skip arrow Qwen -> NVARC
arrow((SX0 + 0.6, q[0]), (SX0 + 0.6, nv[1]), ls=(0, (3, 2)))
ax.text(SX0 + 0.75, (q[0] + nv[1]) / 2, "NVARC skips tasks with a verified Qwen program",
        ha="left", va="center", fontsize=7.5, color=P)

# Monty-ARC
mo = (1.3, 2.25)
box(SX0, mo[0], SX1, mo[1])
text_block(SX0 + 0.2, mo[1] - 0.17, [
    ("Monty-ARC v5   ", "bold", I),
    ("the frozen code, one view, a 120 s per-task alarm", "normal", I),
])
ax.text(SX0 + 0.2 + 2.3, mo[1] - 0.17, "CPU, throughout", ha="left", va="top", fontsize=FS, color=P)

# Merge
mg = (1.3, 6.95)
box(MX0, mg[0], MX1, mg[1], ec=S.BLUE, lw=1.0)
order = [
    ("1", "verified Qwen output", I),
    ("2", "confident Monty-ARC answer", I),
    ("", "(v5 heuristic: evidence \u2265 0.99, 2:1 lead)", P),
    ("3", "NVARC's candidates", I),
    ("4", "unverified Qwen output, a verified", I),
    ("", "program's second grid, Monty-ARC guesses", I),
]
ax.text(MX0 + 0.25, mg[1] - 0.17, "Merge, per test output", ha="left", va="top",
        fontsize=FS, fontweight="bold")
ax.text(MX0 + 0.25, mg[1] - 0.17 - LINE, "in this order", ha="left", va="top", fontsize=FS, color=P)
y = mg[1] - 0.17 - 2.35 * LINE
for num, t, col in order:
    if num:
        y -= 0.24
        ax.text(MX0 + 0.35, y, num, ha="center", va="top", fontsize=FS, fontweight="bold", color=S.BLUE)
    ax.text(MX0 + 0.7, y, t, ha="left", va="top", fontsize=FS, color=col)
    y -= LINE
ax.plot([MX0 + 0.25, MX1 - 0.25], [y - 0.12] * 2, color=S.GRID, lw=0.6)
ax.text(MX0 + 0.25, y - 0.3, "Keep the first two distinct grids:", ha="left", va="top", fontsize=FS, fontweight="bold")
ax.text(MX0 + 0.25, y - 0.3 - LINE, "the two attempts submitted", ha="left", va="top", fontsize=FS, color=I)

for (y0, y1) in (q, nv, mo):
    arrow((SX1, (y0 + y1) / 2), (MX0, (y0 + y1) / 2))

# what is not in it
box(SX0, 0.2, MX1, 1.0, fc=S.GREY_TINT, ec=S.AXIS)
ax.text(SX0 + 0.2, 0.6, "Not in this notebook:", ha="left", va="center", fontsize=FS, fontweight="bold")
ax.text(SX0 + 3.2, 0.6,
        "FA-LOO, the rule of Sections 5–6, and the 2020 program. The certificate was evaluated offline.",
        ha="left", va="center", fontsize=FS)

S.save(fig, "fig4_named_notebook")
