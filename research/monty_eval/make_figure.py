"""WS4: research/paper/figures/module_contributions.png: per-module contribution of Monty-ARC v5.

Two small multiples (own x scales, both from zero): ARC-AGI-1 (train + eval, 800 distinct tasks) and ARC-AGI-2
(public eval 120 + new-in-AGI-2 training 233). Per module: tasks solved by the module alone (light) and tasks the
full system loses when the module is removed (dark). Palette: blue ordinal steps 250/550 (validated, light surface).
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = json.load(open(os.path.join(ROOT, "research", "monty_eval", "results", "ablation_raw.json")))
MODULES = ["composition", "behavior", "pattern", "dynamics", "self-model", "periodic", "association", "field"]
LIGHT, DARK = "#86b6ef", "#1c5cab"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"


def union(splits, name):
    out = set()
    for s in splits:
        out |= {(s if s != "new233" else "agi2-train", k) for k in R[s]["subsets"][name]["solved"]}
    return out


def panel(ax, splits, title):
    full = union(splits, "full")
    alone = [len(union(splits, f"{m} alone")) for m in MODULES]
    lost = [len(full - union(splits, f"-{m}")) for m in MODULES]
    y = list(range(len(MODULES)))[::-1]
    ax.barh([v + 0.2 for v in y], alone, height=0.33, color=LIGHT, label="solves alone", zorder=2)
    ax.barh([v - 0.2 for v in y], lost, height=0.33, color=DARK, label="lost when removed", zorder=2)
    top = max(alone + lost)
    for yy, a, l in zip(y, alone, lost):
        ax.text(a + top * 0.015, yy + 0.2, str(a), va="center", ha="left", fontsize=7.5, color=INK2)
        ax.text(l + top * 0.015, yy - 0.2, str(l), va="center", ha="left", fontsize=7.5, color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels(MODULES, fontsize=9, color=INK)
    ax.set_xlim(0, top * 1.15)
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.tick_params(axis="x", labelsize=8, colors=MUTED, length=0)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.6, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.set_xlabel("tasks (pass@2)", fontsize=8, color=MUTED)
    ax.set_title(f"{title}\nfull system solves {len(full)}", fontsize=9.5, color=INK, loc="left")
    ax.set_facecolor(SURF)


def main():
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), dpi=220, sharey=True)
    fig.patch.set_facecolor(SURF)
    panel(axes[0], ["agi1-train", "agi1-eval"], "ARC-AGI-1 train + eval (800 tasks)")
    panel(axes[1], ["agi2-eval", "new233"], "ARC-AGI-2 eval + new training (353 tasks)")
    h, l = axes[0].get_legend_handles_labels()
    fig.text(0.012, 0.975, "Monty-ARC v5: what each learning module contributes", ha="left", va="top",
             fontsize=10.5, color=INK, fontweight="bold")
    fig.legend(h, l, loc="upper left", ncol=2, frameon=False, fontsize=8.5, bbox_to_anchor=(0.005, 0.925),
               handlelength=1.2, columnspacing=1.2)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    out = os.path.join(ROOT, "research", "paper", "figures", "module_contributions.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, facecolor=SURF)
    print("wrote", out)


if __name__ == "__main__":
    main()
