"""monty-heldout: two figures for the paper. usage: python make_figures.py
research/paper/figures/heldout_precision_by_rule.png, research/paper/figures/heldout_modules.png"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import HERE, ROOT  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

FIG = os.path.join(ROOT, "research", "paper", "figures")
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
LIGHT, DARK = "#86b6ef", "#1c5cab"


def load(tag):
    p = os.path.join(HERE, "results", f"{tag}_analysis.json")
    return json.load(open(p)) if os.path.exists(p) else None


C, M, O = load("concept"), load("mini"), load("oned")
RULES = [("Fit to demos only", "fit"), ("v5 heuristic", "v5"), ("FA-LOO + (c)", "fc")]
SERIES = [("Development, 1,147 tasks", "#2a78d6", "o", lambda r: C["rules"][r]["dev"]),
          ("ConceptARC, real test role", "#eb6834", "s", lambda r: C["rules"][r]["real"]),
          ("ConceptARC, demo roles", "#1baf7a", "D", lambda r: C["rules"][r]["demo"])]
if M:
    SERIES.append(("Mini-ARC, real test role", "#eda100", "^", lambda r: M["rules"][r]["real"]))
if O:
    SERIES.append(("1D-ARC, real test role (18 types)", "#e87ba4", "v", lambda r: O["rules"][r]["real"]))


def counts(p):
    return f"{p['correct']:.0f}/{p['answered']}"


def fig_precision():
    n = len(SERIES)
    fig, ax = plt.subplots(figsize=(7.2, 0.55 + 0.27 * n * len(RULES) + 0.45), dpi=220)
    fig.patch.set_facecolor(SURF)
    ax.set_facecolor(SURF)
    gap = 0.26
    yt, yl = [], []
    for i, (lab, r) in enumerate(RULES):
        y0 = (len(RULES) - 1 - i) * (n * gap + 0.42)
        yt.append(y0 + (n - 1) * gap / 2)
        yl.append(lab)
        for j, (sn, col, mk, get) in enumerate(SERIES):
            p = get(r)
            if not p["answered"]:
                continue
            y = y0 + (n - 1 - j) * gap
            lo, hi = p["ci"]
            ax.plot([100 * lo, 100 * hi], [y, y], color=col, linewidth=1.6, solid_capstyle="round", zorder=2, clip_on=False)
            ax.scatter([100 * p["precision"]], [y], s=34, marker=mk, color=col, edgecolor=SURF, linewidth=0.8, zorder=3, clip_on=False, label=sn if i == 0 else None)
            ax.text(103, y, f"{100 * p['precision']:.0f}%  ({counts(p)})", va="center", ha="left", fontsize=7.5, color=INK2)
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=9.5, color=INK)
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 20))
    ax.set_xticklabels([f"{v}%" for v in range(0, 101, 20)], fontsize=8, color=MUTED)
    ax.tick_params(axis="both", length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.6, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.set_xlabel("Precision of confident answers; lines are 95% cluster-bootstrap intervals", fontsize=8, color=MUTED)
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, 1.13), ncol=min(3, n), fontsize=7.5, frameon=False, handletextpad=0.2, columnspacing=1.0)
    fig.subplots_adjust(left=0.17, right=0.84, top=0.88, bottom=0.12)
    fig.savefig(os.path.join(FIG, "heldout_precision_by_rule.png"), facecolor=SURF)
    plt.close(fig)


ORDER = ["composition", "dynamics", "behavior", "self-model", "periodic", "pattern", "association", "field"]


def fig_modules():
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.4), dpi=220, sharey=True, gridspec_kw=dict(width_ratios=[1, 1.25]))
    fig.patch.set_facecolor(SURF)
    y = list(range(len(ORDER)))[::-1]
    mt = C["modules"]["real"]
    alone = [mt[m]["alone"] for m in ORDER]
    lost = [mt[m]["lost"] for m in ORDER]
    a.barh([v + 0.2 for v in y], alone, height=0.33, color=LIGHT, label="solves when run alone", zorder=2)
    a.barh([v - 0.2 for v in y], lost, height=0.33, color=DARK, label="lost when removed", zorder=2)
    top = max(alone + lost)
    for yy, p, q in zip(y, alone, lost):
        a.text(p + top * 0.02, yy + 0.2, str(p), va="center", fontsize=7.5, color=INK2)
        a.text(q + top * 0.02, yy - 0.2, str(q), va="center", fontsize=7.5, color=INK2)
    a.set_yticks(y)
    a.set_yticklabels(ORDER, fontsize=9, color=INK)
    a.set_xlim(0, top * 1.18)
    a.set_xlabel("ConceptARC pairs solved (system: 58 of 480)", fontsize=8, color=MUTED)
    a.legend(loc="lower right", fontsize=7.5, frameon=False)
    dv = C["modules"]["dev"]
    for yy, m in zip(y, ORDER):
        for off, p, col, mk in ((0.17, dv[m]["loo1"], "#2a78d6", "o"), (-0.17, mt[m]["loo1"], "#eb6834", "s")):
            if p["answered"]:
                lo, hi = p["ci"]
                b.plot([100 * lo, 100 * hi], [yy + off, yy + off], color=col, linewidth=1.6, solid_capstyle="round", zorder=2, clip_on=False)
                b.scatter([100 * p["precision"]], [yy + off], s=30, marker=mk, color=col, edgecolor=SURF, linewidth=0.8, zorder=3, clip_on=False)
                b.text(104, yy + off, counts(p), va="center", fontsize=7.5, color=INK2)
            else:
                b.text(104, yy + off, "0/0", va="center", fontsize=7.5, color=MUTED)
    b.scatter([], [], s=30, marker="o", color="#2a78d6", label="development, 1,147 tasks")
    b.scatter([], [], s=30, marker="s", color="#eb6834", label="ConceptARC, real test role")
    b.set_xlim(0, 100)
    b.set_xticks(range(0, 101, 25))
    b.set_xticklabels([f"{v}%" for v in range(0, 101, 25)])
    b.set_xlabel("Precision of top answer at evidence >= 0.99", fontsize=8, color=MUTED)
    b.legend(loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=2, fontsize=7.5, frameon=False, handletextpad=0.2)
    for ax in (a, b):
        ax.set_facecolor(SURF)
        ax.tick_params(axis="x", labelsize=8, colors=MUTED, length=0)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color=GRID, linewidth=0.6, zorder=0)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#c3c2b7")
    fig.subplots_adjust(left=0.13, right=0.92, top=0.9, bottom=0.14, wspace=0.14)
    fig.savefig(os.path.join(FIG, "heldout_modules.png"), facecolor=SURF)
    plt.close(fig)


if __name__ == "__main__":
    fig_precision()
    fig_modules()
    print("figures written")
