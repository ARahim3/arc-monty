"""Calibration data for the paper: top-answer correctness vs leave-one-out evidence, per split and module."""
import json
import multiprocessing as mp
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from arcmonty import monty_arc  # noqa: E402
from arcmonty.data import load_split  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402
from arcmonty.vote import pool  # noqa: E402


def one(item):
    split, key, task = item
    best = pool(monty_arc.candidates(task))
    if not best:
        return None
    top = best[0]
    ok = score_task(task, [[g] for g in top["preds"]])
    return dict(split=split, task=key, evidence=round(float(top["evidence"]), 3), correct=ok,
                module=sorted({v.split("@")[0] for v in top["voters"]}), n_strong=sum(p["evidence"] >= 0.99 for p in best))


if __name__ == "__main__":
    items = [(s, k, t) for s in ("agi2-eval", "agi1-eval", "agi2-train", "agi1-train") for k, t in load_split(s).items()]
    with mp.Pool(12) as p:
        rows = [r for r in p.map(one, items, chunksize=2) if r]
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "calibration.json")
    json.dump(rows, open(out, "w"))
    import collections
    b = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        e = r["evidence"]
        k = "1.0" if e >= 0.99 else ("[0.5,1)" if e >= 0.5 else ("(0,0.5)" if e > 0 else "0"))
        b[k][0] += 1
        b[k][1] += r["correct"]
    for k in ("1.0", "[0.5,1)", "(0,0.5)", "0"):
        n, c = b[k]
        print(f"LOO evidence {k:8s}: top answers {n:4d}, correct {c:5.1f} ({100 * c / max(1, n):.0f}%)")
