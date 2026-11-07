"""Cover image for the writeup: precision of Monty-ARC's top answer by leave-one-out evidence (1,920 tasks)."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURFACE, INK, INK2, MUTED, SERIES = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#2a78d6"

rows = json.load(open(os.path.join(ROOT, "research", "calibration.json")))
buckets = [("all held-out\ndemos predicted", lambda e: e >= 0.99), ("most\n(50–99%)", lambda e: 0.5 <= e < 0.99),
           ("some\n(1–49%)", lambda e: 0 < e < 0.5), ("none", lambda e: e <= 0)]
stats = []
for name, f in buckets:
    sel = [r for r in rows if f(r["evidence"])]
    stats.append((name, len(sel), sum(r["correct"] for r in sel)))

fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
w = 0.56
for x, (name, n, c) in enumerate(stats):
    p = c / n if n else 0
    h = p * 100
    if h >= 3:
        ax.add_patch(FancyBboxPatch((x - w / 2, 0), w, h, boxstyle="round,pad=0,rounding_size=0.06",
                                    mutation_aspect=35, linewidth=0, facecolor=SERIES))
    else:  # an empty bucket: a flat baseline mark instead of a sliver of a rounded bar
        ax.plot([x - w / 2, x + w / 2], [0.4, 0.4], color=SERIES, linewidth=3, solid_capstyle="round")
    ax.text(x, h + 2.2, f"{100 * p:.0f}%", ha="center", va="bottom", fontsize=30, fontweight="bold", color=INK)
    ax.text(x, -9, name, ha="center", va="top", fontsize=17, color=INK2, linespacing=1.25)
    ax.text(x, h + 14.5, f"{c:.0f} of {n} answers", ha="center", va="bottom", fontsize=14, color=MUTED)
ax.set_xlim(-0.6, len(stats) - 0.4)
ax.set_ylim(0, 122)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=13, color=MUTED)
ax.yaxis.grid(True, color="#e6e5e1", linewidth=1)
ax.set_axisbelow(True)
ax.set_xticks([])
for s in ("top", "right", "left", "bottom"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)
fig.text(0.06, 0.93, "Monty-ARC knows when it knows", fontsize=34, fontweight="bold", color=INK, ha="left")
fig.text(0.06, 0.875, "Share of correct top answers by leave-one-out evidence, over 1,920 ARC-AGI-1 and ARC-AGI-2 tasks",
         fontsize=16, color=INK2, ha="left")
fig.text(0.515, 0.085, "Held-out demonstrations predicted by the rule learned from the other demonstrations",
         fontsize=14, color=MUTED, ha="center")
fig.text(0.06, 0.022, "Thousand-Brains-style learning modules: object-centric reference frames, evidence over pose "
         "hypotheses, voting. No training data, CPU only.", fontsize=13, color=MUTED, ha="left")
plt.subplots_adjust(left=0.06, right=0.97, top=0.80, bottom=0.25)
out = os.path.join(ROOT, "research", "figures", "cover_calibration.png")
fig.savefig(out, facecolor=SURFACE)
print("saved", out, [(n, c, round(c / n, 3)) for _, n, c in stats])
