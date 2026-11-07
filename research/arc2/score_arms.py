"""Score the TPU arms against the xhigh 16k baseline (sample 0, paired by task).
    python research/arc2/score_arms.py [arm ...]
"""
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from tri_sim import qwen_outcomes, cells, CH  # noqa: E402

MONTY_SOLVED = {"0934a4d8", "135a2760", "1818057f", "dbff022c"}   # Monty-ARC v5 solves on public eval
SOL = json.load(open(os.path.join(ROOT, "data/kaggle_format/agi2_eval_solutions.json")))


def direct_outcomes(path):
    out = {}
    for line in open(path):
        r = json.loads(line)
        if r.get("sample") != 0 or "error" in r:
            continue
        c = r.get("correct") or r.get("correct_repaired") or []
        out[r["task_id"]] = dict(v=False, vround=None, frac=(sum(c) / len(SOL[r["task_id"]])) if c else 0.0,
                                 cost=r["cost"], natural=r.get("natural_end"))
    return out


def natural_frac(path):
    n = t = 0
    for line in open(path):
        r = json.loads(line)
        for x in r.get("rounds", []):
            if "forced" in x:
                t += 1
                n += not x["forced"]
    return n / t if t else float("nan")


def row(name, Q, base=None, ids=None):
    ids = sorted(ids or Q)
    v = sum(Q[t]["v"] for t in ids)
    vc = sum(Q[t]["v"] * Q[t]["frac"] for t in ids)
    p1 = sum(Q[t]["frac"] for t in ids)
    cost = np.mean([Q[t]["cost"] for t in ids])
    tok = sum(Q[t]["cost"] for t in ids)
    small = [t for t in ids if cells(t) <= np.percentile([cells(x) for x in CH], 25)]
    s = (f"{name:26s} n={len(ids):3d} verified {v:3d} verified-correct {vc:5.1f} pass@1 {p1:5.1f} "
         f"mean cost {cost / 1e3:5.1f}k  verified-correct per M tok {vc / tok * 1e6:4.2f}  "
         f"small-quartile vc {sum(Q[t]['v'] * Q[t]['frac'] for t in small):4.1f}/{len(small)}")
    if base is not None:
        both = [t for t in ids if t in base]
        win = sum(1 for t in both if Q[t]["v"] * Q[t]["frac"] > base[t]["v"] * base[t]["frac"])
        loss = sum(1 for t in both if Q[t]["v"] * Q[t]["frac"] < base[t]["v"] * base[t]["frac"])
        s += f" | vs xhigh16k on same {len(both)}: +{win}/-{loss}, base vc {sum(base[t]['v'] * base[t]['frac'] for t in both):.1f}"
    return s


if __name__ == "__main__":
    base = qwen_outcomes()
    print(row("ps_xhigh_b16384 (base)", base))
    paths = sorted(glob.glob(os.path.join(ROOT, "llm/results/qwen38_*_*_b*.jsonl")))
    for p in paths:
        arm = os.path.basename(p)[7:-6]
        if arm.endswith("ids") or arm in ("ps_b16384", "direct_b32768") or (sys.argv[1:] and arm not in sys.argv[1:]):
            continue
        Q = direct_outcomes(p) if arm.startswith("direct") else qwen_outcomes(p)
        if not Q:
            continue
        print(row(arm, Q, base) + (f" natural-end rounds {natural_frac(p):.2f}" if arm.startswith("ps") else ""))
        if "hint" in arm:
            keep = [t for t in Q if t not in MONTY_SOLVED]
            print(row("  ...excl. Monty-solved", Q, base, keep))
