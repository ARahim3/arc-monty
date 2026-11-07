"""SPIKE analysis: one column against Monty-ARC v5 on development data, from per-task files."""
import json
import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
mont = {}
for line in open(os.path.join(ROOT, "research", "monty_eval", "results", "per_task_full.jsonl")):
    r = json.loads(line)
    mont[(r["split"], r["task"])] = r
SENS = ("color", "mask", "objc", "obj", "objn", "near", "nearc", "nears", "nearsc")
for split in ("agi1-train", "agi1-eval", "new233", "agi2-eval"):
    p = os.path.join(HERE, "results", f"counted_{split}.jsonl")
    if not os.path.exists(p):
        continue
    rows = [json.loads(l) for l in open(p)]
    if not rows:
        continue
    col = {r["task"]: r for r in rows}
    n = len(rows)
    sc = sum(r["score"] for r in rows)
    ms = sum(mont[(split, t)]["full"]["s2"] for t in col)
    both = sum(min(col[t]["score"], mont[(split, t)]["full"]["s2"]) for t in col)
    conly = [t for t in col if col[t]["score"] > mont[(split, t)]["full"]["s2"]]
    monly = [t for t in col if col[t]["score"] < mont[(split, t)]["full"]["s2"]]
    print(f"\n{split}: tasks {n}, timeouts {sum(bool(r.get('timeout')) for r in rows)}, answered {sum(r.get('n_cands', 0) > 0 for r in rows)}, "
          f"mean s {np.mean([r['sec'] for r in rows]):.2f}")
    print(f"  pass@2 sum: column {sc:.1f}, Monty v5 {ms:.1f}, both {both:.1f}; column only {len(conly)} tasks, Monty only {len(monly)} tasks")
    for lo, hi, name in ((0.99, 1.1, "LOO = 1"), (0.5, 0.99, "LOO in [.5, 1)"), (-0.1, 0.5, "LOO < .5")):
        s = [r for r in rows if r.get("best_ev") is not None and lo <= r["best_ev"] < hi]
        print(f"  top answer {name}: {sum(r['top_right'] for r in s)}/{len(s)}")
    if conly:
        print("  column-only:", conly[:40])
    # one sensor alone, and the ablations of levels
    by = {k: sum(r.get("by_kind", {}).get(k, 0) for r in rows) for k in SENS}
    print("  each sensor alone:", {k: round(v, 1) for k, v in by.items()})
    best = lambda ks: sum(max([r.get("by_kind", {}).get(k, 0) for k in ks] or [0]) for r in rows)
    print("  best single sensor per task, so more than two attempts, do not quote; level 1 (color, mask):", round(best(("color", "mask")), 1),
          "| + object ID (obj, objc):", round(best(("color", "mask", "obj", "objc")), 1),
          "| + object frame (near*):", round(best(("color", "mask", "obj", "objc", "near", "nearc", "nears", "nearsc")), 1),
          "| + count (objn):", round(best(SENS), 1))
    print("  frames used by right tops:", Counter(r["best_h"].split("/")[0] for r in rows if r.get("top_right")))

# ---- fair ablation: every arm has two attempts in all, ranked by leave-one-out
print("\nFair ablation of sensors, two attempts per arm (CI by task)")
ARMS = (("cells only", "color+mask"), ("+ object ID", "color+mask+obj+objc"),
        ("+ object frame", "color+mask+obj+objc+near+nearc+nears+nearsc"), ("+ count (all)", None))
rng = np.random.default_rng(0)
for split in ("agi1-train", "agi1-eval", "new233"):
    rows = {}
    for name, suf in ARMS:
        p = os.path.join(HERE, "results", f"counted_{split}" + (f"_{suf}" if suf else "") + ".jsonl")
        if os.path.exists(p):
            rows[name] = {r["task"]: r for r in map(json.loads, open(p))}
    if len(rows) < 2:
        continue
    base = rows["cells only"]
    line = f"{split}:"
    for name, _ in ARMS:
        if name not in rows:
            continue
        tot = sum(r["score"] for r in rows[name].values())
        conf = [r for r in rows[name].values() if r.get("best_ev") is not None and r["best_ev"] >= 0.99]
        line += f" | {name} {tot:.1f} (LOO 1: {sum(r['top_right'] for r in conf)}/{len(conf)})"
        if name != "cells only":
            d = np.array([rows[name][t]["score"] - base[t]["score"] for t in base])
            b = [d[rng.integers(0, len(d), len(d))].sum() for _ in range(4000)]
            line += f" diff {d.sum():+.1f} [{np.percentile(b, 2.5):+.1f}, {np.percentile(b, 97.5):+.1f}]"
    print(line)
