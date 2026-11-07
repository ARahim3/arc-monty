"""monty-heldout: plan check 4. The dev re-vote through my code reproduces numbers published in monty_ablations.md, monty_faloo.md,
frame_ablation.json and the lead addendum. usage: python verify_dev.py -> prints and adds V4 to results/verify.json"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import HERE, ROOT  # noqa: E402
from stats import load_dev, f, prec, bucket, BUCKETS  # noqa: E402

dev = load_dev()
cnt = lambda cfg, g: (lambda p: (round(p["correct"]), p["answered"]))(prec(dev, *dev.vec(cfg, g)))
loo1 = lambda o: o["top_ok"] if (o["top_ev"] is not None and o["top_ev"] >= 0.99) else None
exp = {("full", "fc"): (101, 102), ("full", "a"): (102, 104), ("full", "fa"): (101, 103), ("full", "v5"): (96, 98), ("full", "p4"): (97, 98)}
checks = {f"{c}:{r}": (cnt(c, f(r)), v) for (c, r), v in exp.items()}
FA = json.load(open(os.path.join(ROOT, "research", "paper", "data", "frame_ablation.json")))
for arm, cfg in (("canon", "beh:canon"), ("abs", "beh:abs"), ("both", "behavior alone")):
    p2 = sum(dev.rows[k]["cfg"][cfg]["0"]["p2"] for k in dev.keys)
    checks[f"frame {arm} pass2"] = (p2, FA[arm]["pass2"])
    checks[f"frame {arm} loo1"] = (cnt(cfg, loo1), (round(FA[arm]["loo1_correct"]), FA[arm]["loo1"]))
tab6 = {"full": (100, 104), "self-model alone": (9, 9), "behavior alone": (13, 16), "dynamics alone": (10, 10), "composition alone": (55, 56), "association alone": (3, 3), "pattern alone": (10, 11), "field alone": (1, 1), "periodic alone": (4, 4)}
for c, v in tab6.items():
    checks[f"table6 {c}"] = (cnt(c, loo1), v)
bad = {k: x for k, x in checks.items() if x[0] != x[1]}
res = dict(checked=len(checks), mismatches=bad)
print(res)
p = os.path.join(HERE, "results", "verify.json")
d = json.load(open(p))
d["V4_dev_numbers"] = res
json.dump(d, open(p, "w"), indent=1)
