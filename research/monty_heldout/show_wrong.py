"""monty-heldout: one PNG per wrong answer (real role) with demos, test input, truth and prediction, plus the voters' hypotheses.
usage: python show_wrong.py DIR TAG  -> results/wrong_<TAG>/<name>.png and results/wrong_<TAG>/cases.json"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import CACHE, HERE, h, items_from_dir  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
import numpy as np  # noqa: E402
from rules import build, module_name  # noqa: E402
from arcmonty import vote  # noqa: E402

CM = ListedColormap(["#000000", "#0074D9", "#FF4136", "#2ECC40", "#FFDC00", "#AAAAAA", "#F012BE", "#FF851B", "#7FDBFF", "#870C25"])
DIR, TAG = sys.argv[1], sys.argv[2]
out = os.path.join(HERE, "results", f"wrong_{TAG}")
os.makedirs(out, exist_ok=True)
A = json.load(open(os.path.join(HERE, "results", f"{TAG}_analysis.json")))
wrong = set(A["wrong"]["v5"]) | set(A["wrong"]["fc"]) | set(A["wrong"]["a"])
items = dict(items_from_dir(DIR))
cache = {}
for line in open(os.path.join(CACHE, f"{TAG}_p0.jsonl")):
    r = json.loads(line)
    if r["task"] in wrong:
        r["_np"] = [np.array(g, dtype=np.int8) for g in r["grids"]]
        cache[r["task"]] = r


def draw(ax, g, title):
    ax.imshow(g, cmap=CM, vmin=0, vmax=9)
    ax.set_title(title, fontsize=7)
    ax.set_xticks(np.arange(-.5, g.shape[1]), [])
    ax.set_yticks(np.arange(-.5, g.shape[0]), [])
    ax.grid(color="#555555", linewidth=0.3)
    ax.tick_params(length=0)


cases = {}
for k in sorted(wrong):
    pool = items[k]
    m = len(pool)
    C = build([cache[k]], f"F{m-1}", views={0})
    best = vote.pool(C)
    top = best[0]
    x, y = pool[-1]
    att = vote.attempts_from({"test": [x]}, C, vote.CONFIDENT)[0]
    hyps = [c["hyp"] for c in C if np.array_equal(c["preds"][0], top["preds"][0])][:8]
    cases[k] = dict(in_v5=k in A["wrong"]["v5"], in_fc=k in A["wrong"]["fc"], in_a=k in A["wrong"]["a"], top_ev=round(float(top["evidence"]), 3), voters=sorted(top["voters"]),
                    n_voting_hyps=sum(np.array_equal(c["preds"][0], top["preds"][0]) for c in C), hyps=hyps, n_strong=sum(p["evidence"] >= .99 for p in best),
                    n_distinct=len(best), demos=m - 1, diff_cells=int((top["preds"][0] != y).sum()) if top["preds"][0].shape == y.shape else None)
    n = m + 2
    cols = max(n - 1, 4)
    fig, ax = plt.subplots(2, cols, figsize=(1.7 * cols, 3.6), dpi=70)
    for a in ax.ravel():
        a.axis("off")
    for j, (i, o) in enumerate(pool[:-1]):
        for r, g, t in ((0, i, f"demo {j} in"), (1, o, f"demo {j} out")):
            ax[r, j].axis("on")
            draw(ax[r, j], g, t)
    for r, g, t in ((0, x, "test in"), (1, y, "truth")):
        ax[r, m - 1].axis("on")
        draw(ax[r, m - 1], g, t)
    ax[1, m].axis("on")
    draw(ax[1, m], top["preds"][0], "Monty top")
    if len(att) > 1:
        ax[0, m].axis("on")
        draw(ax[0, m], att[1], "attempt 2")
    fig.suptitle(f"{k}  ev={top['evidence']:.2f} voters={sorted(top['voters'])[:4]}", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(out, k.replace("/", "_").replace("#", "_") + ".png"))
    plt.close(fig)
json.dump(cases, open(os.path.join(out, "cases.json"), "w"), indent=1)
print(len(cases), "cases")
