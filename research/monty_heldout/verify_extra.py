"""monty-heldout: re-vote vs real runs on the extra sets: v5, pass@2 at 1 view and 8 views on a random sample, real role.
usage: python -I -B verify_extra.py -> adds V5 to results/verify.json"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import json
import os
import random
import sys

sys.path.insert(0, (_REPO + "/research/monty_heldout"))
from hl_common import HERE, ROOT, items_from_dir  # noqa: E402
from arcmonty import behavior, monty_arc, symmetry, vote  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402
from stats import load_dataset  # noqa: E402

X = os.path.join(ROOT, "external")
out = {}
for tag, path in (("mini", os.path.join(X, "heldout", "mini-arc", "data", "MiniARC")), ("oned", os.path.join(X, "heldout", "1d-arc", "dataset")), ("minimal", os.path.join(X, "judge", "conceptarc", "repo", "MinimalTasks"))):
    items = items_from_dir(path)
    base, p8 = load_dataset(tag, "base"), load_dataset(tag, "p8")
    random.seed(0)
    sample = random.sample(items, min(40, len(items)))
    bad = 0
    for k, pool in sample:
        tr, (x, y) = pool[:-1], pool[-1]
        task = {"test": [x], "test_out": [y]}
        for persp, row, cfg in (((0,), base, "full"), (tuple(range(8)), p8, "p8")):
            symmetry._CACHE.clear()
            behavior._SEG_CACHE.clear()
            C = monty_arc.candidates({"train": tr, "test": [x]}, perspectives=persp)
            conf = vote.confident(C)
            v5 = score_task(task, vote.attempts_from(task, C, vote.CONFIDENT)) if conf else None
            p2 = score_task(task, vote.attempts_from(task, C))
            o = row[k]["cfg"][cfg][str(len(pool) - 1)]
            bad += (o["v5"], o["p2"]) != (v5, p2)
    out[tag] = dict(sample=len(sample), checks=2 * len(sample), mismatches=bad)
print(out)
p = os.path.join(HERE, "results", "verify.json")
d = json.load(open(p))
d["V5_extra_sets_vs_real"] = out
json.dump(d, open(p, "w"), indent=1)
