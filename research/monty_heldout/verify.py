"""monty-heldout: checks that the cache + offline re-vote are exact. usage: python verify.py"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import CACHE, CONCEPT, HERE, ROOT, h, items_from_dir  # noqa: E402
import numpy as np  # noqa: E402
from arcmonty import behavior, monty_arc, symmetry, vote  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402

SC = os.path.join(ROOT, "research", "paper", "review_scratch")
R = {}
for line in open(os.path.join(HERE, "results", "concept_base.jsonl")):
    r = json.loads(line)
    R[r["task"]] = r
out = {}

# V1a: rotate_concept.jsonl, every fold and full answer
rot = [json.loads(l) for l in open(os.path.join(SC, "rotate_concept.jsonl"))]
bad_f = bad_full = n_f = n_full = 0
for r in rot:
    c = R[r["task"]]["cfg"]["full"]
    for a in range(r["m"]):
        o = c[str(a)]
        n_full += 1
        bad_full += o["full_h"] != r["full"][str(a)]
        for b in range(r["m"]):
            if b == a:
                continue
            n_f += 1
            bad_f += o["fold_h"][str(b)] != r["folds"][f"{a},{b}"]
out["V1a_rotate_concept"] = dict(folds=n_f, fold_mismatches=bad_f, fulls=n_full, full_mismatches=bad_full)

# V1b: concept_full.jsonl (v5, fit, p2, has) on the real role
bad = 0
for line in open(os.path.join(SC, "concept_full.jsonl")):
    r = json.loads(line)
    o = R[r["task"]]["cfg"]["full"][str(R[r["task"]]["m"] - 1)]
    bad += (o["v5"], o["fit"], o["p2"], o["has"]) != (r["v5"], r["fit"], r["p2"], r["has"])
out["V1b_concept_full"] = dict(items=480, mismatches=bad)

# V2: frame filter vs a real run with behavior.FRAMES monkeypatched (ConceptARC, real role, full data, behaviour alone)
items = items_from_dir(CONCEPT)
from rules import build  # noqa: E402
cache = {}
for line in open(os.path.join(CACHE, "concept_p0.jsonl")):
    r = json.loads(line)
    r["_np"] = [np.array(g, dtype=np.int8) for g in r["grids"]]
    cache[r["task"]] = r
mis = {"canon": 0, "abs": 0}
n = 0
for k, pool in items:
    m = len(pool)
    tr, x = pool[:-1], pool[-1][0]
    for fr in ("canon", "abs"):
        behavior.FRAMES = (fr,)
        symmetry._CACHE.clear()
        behavior._SEG_CACHE.clear()
        real = behavior.candidates({"train": tr, "test": [x]})
        off = build([cache[k]], f"F{m-1}", modules={"behavior"}, frames={fr}, views={0})
        ok = len(real) == len(off) and all(a["hyp"] == b["hyp"] and abs(a["evidence"] - b["evidence"]) < 1e-9 and h(a["preds"][0]) == h(b["preds"][0]) for a, b in zip(real, off))
        mis[fr] += not ok
    n += 1
behavior.FRAMES = ("canon", "abs")
out["V2_frame_filter_vs_real"] = dict(items=n, mismatches=mis)

# V3: 8-view re-vote vs real monty_arc.candidates(perspectives=range(8)) on a random sample
if os.path.exists(os.path.join(HERE, "results", "concept_p8.jsonl")):
    P8 = {}
    for line in open(os.path.join(HERE, "results", "concept_p8.jsonl")):
        r = json.loads(line)
        P8[r["task"]] = r
    random.seed(0)
    sample = random.sample(items, 60)
    bad = 0
    for k, pool in sample:
        tr, (x, y) = pool[:-1], pool[-1]
        symmetry._CACHE.clear()
        behavior._SEG_CACHE.clear()
        C = monty_arc.candidates({"train": tr, "test": [x]}, perspectives=tuple(range(8)))
        task = {"test": [x], "test_out": [y]}
        o = P8[k]["cfg"]["p8"][str(len(pool) - 1)]
        conf = vote.confident(C)
        v5 = score_task(task, vote.attempts_from(task, C, vote.CONFIDENT)) if conf else None
        p2 = score_task(task, vote.attempts_from(task, C))
        bad += (o["v5"], o["p2"]) != (v5, p2)
    out["V3_p8_vs_real"] = dict(sample=len(sample), mismatches=bad)
json.dump(out, open(os.path.join(HERE, "results", "verify.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
