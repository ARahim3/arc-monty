"""Licence, size, quality and exact overlap of candidate fresh sets, before any solver sees them. JSON only; prints no grids.
usage: python -I -B fresh_check.py  -> results/fresh_check.json"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))  # repo root
import collections, glob, hashlib, json, os, sys
ROOT = _REPO
sys.path.insert(0, ROOT)
import numpy as np
from arcmonty.data import SPLITS
FRESH = os.path.join(ROOT, "external/tbt_fresh/repo/dataset")
SETS = ("arc-community", "nosound", "dbigham", "Sequence_ARC", "arc-dataset-tama", "IPARC", "PQA")
EARLIER = {"dev (ARC-AGI-1, ARC-AGI-2)": list(SPLITS.values()),
           "ConceptARC corpus": [os.path.join(ROOT, "external/judge/conceptarc/repo/corpus")],
           "MinimalTasks": [os.path.join(ROOT, "external/judge/conceptarc/repo/MinimalTasks")],
           "Mini-ARC": [os.path.join(ROOT, "external/heldout/mini-arc/data")],
           "1D-ARC": [os.path.join(ROOT, "external/heldout/1d-arc/dataset")]}

def gh(g):
    a = np.array(g, dtype=np.int8)
    return hashlib.md5(str(a.shape).encode() + a.tobytes()).hexdigest()

def canon(g):
    """Input up to D8 and colour renaming: first-appearance colour map on each pose; smallest hash."""
    a, best = np.array(g, dtype=np.int8), None
    for k in range(8):
        t = np.rot90(a, k % 4)
        t = np.fliplr(t) if k >= 4 else t
        _, first, inv = np.unique(t, return_index=True, return_inverse=True)
        rank = np.argsort(np.argsort(first))[inv].reshape(t.shape).astype(np.int8)
        h = hashlib.md5(str(rank.shape).encode() + rank.tobytes()).hexdigest()
        best = h if best is None or h < best else best
    return best

def load(path):
    out = {}
    for fn in sorted(glob.glob(os.path.join(path, "**", "*.json"), recursive=True)):
        try:
            raw = json.load(open(fn))
            if isinstance(raw, dict) and "train" in raw and "test" in raw:
                out[os.path.relpath(fn, path)] = raw
        except Exception:
            out[os.path.relpath(fn, path)] = None
    return out

def pairs(raw):
    return [(gh(p["input"]), gh(p["output"])) for p in list(raw["train"]) + list(raw["test"]) if "output" in p]

earlier = {}
for name, paths in EARLIER.items():
    ps, ins, cins = set(), set(), set()
    for p in paths:
        for raw in load(p).values():
            if raw:
                pp = pairs(raw)
                ps.update(pp); ins.update(i for i, _ in pp)
                cins.update(canon(x["input"]) for x in list(raw["train"]) + list(raw["test"]))
    earlier[name] = dict(pairs=ps, inputs=ins, canon=cins)
    print(name, "pairs", len(ps), file=sys.stderr)
report, seen = {}, {}
for s in SETS:
    tasks = load(os.path.join(FRESH, s, "data"))
    bad = [k for k, r in tasks.items() if r is None]
    tasks = {k: r for k, r in tasks.items() if r}
    rep = dict(json_files=len(tasks) + len(bad), unreadable=len(bad))
    tp, ntest, ndemo, wide, badval, noout, h = [], collections.Counter(), collections.Counter(), 0, 0, 0, collections.Counter()
    for k, r in tasks.items():
        tp.append(pairs(r))
        ntest[len(r["test"])] += 1; ndemo[len(r["train"])] += 1
        noout += any("output" not in p for p in r["test"])
        gs = [g for p in list(r["train"]) + list(r["test"]) for g in (p["input"], p.get("output", [[0]]))]
        wide += any(len(g) > 30 or len(g[0]) > 30 for g in gs)
        badval += any(int(np.max(g)) > 9 for g in gs)
        for p in r["train"]:
            h[(len(p["input"]), len(p["input"][0]))] += 1
    flat = {x for pp in tp for x in pp}
    rep.update(tasks=len(tasks), distinct_pairs=len(flat), test_pairs=sum(sum(1 for p in r["test"] if "output" in p) for r in tasks.values()),
               tests_per_task=dict(sorted(ntest.items())), demos_per_task=dict(sorted(ndemo.items())), tasks_wider_30=wide, tasks_colour_over_9=badval, tasks_no_test_output=noout,
               same_size_tasks=sum(all(len(p["input"]) == len(p["output"]) and len(p["input"][0]) == len(p["output"][0]) for p in r["train"]) for r in tasks.values()),
               commonest_sizes=[(str(a), b) for a, b in h.most_common(4)], names=sorted(os.path.basename(k)[:-5] for k in tasks)[:6],
               median_cells=float(np.median([np.size(p["input"]) for r in tasks.values() for p in r["train"]])))
    dup = collections.Counter(tuple(sorted(pp)) for pp in tp)
    rep["duplicate_tasks_within_set"] = sum(c - 1 for c in dup.values() if c > 1)
    rep["overlap"] = {}
    for name, e in earlier.items():
        cin = {canon(x["input"]) for r in tasks.values() for x in list(r["train"]) + list(r["test"])}
        rep["overlap"][name] = dict(pairs_shared=len(flat & e["pairs"]), tasks_any_pair=sum(any(x in e["pairs"] for x in pp) for pp in tp),
                                    tasks_any_input=sum(any(x[0] in e["inputs"] for x in pp) for pp in tp), inputs_up_to_d8_colour=len(cin & e["canon"]), distinct_inputs_canon=len(cin))
    rep["tasks_sharing_a_pair"] = {name: sorted(k[:-5] for k, pp in zip(tasks, tp) if any(x in e["pairs"] for x in pp)) for name, e in earlier.items()}
    rep["tasks_sharing_an_input"] = {name: sorted(k[:-5] for k, pp in zip(tasks, tp) if any(x[0] in e["inputs"] for x in pp)) for name, e in earlier.items()}
    rep["overlap_with_other_fresh"] = {o: len(flat & seen[o]) for o in seen}
    seen[s] = flat
    report[s] = rep
    print(s, json.dumps(rep), flush=True)
os.makedirs(os.path.join(ROOT, "research/tbt_proper/column/results"), exist_ok=True)
json.dump(report, open(os.path.join(ROOT, "research/tbt_proper/column/results/fresh_check.json"), "w"), indent=1)
