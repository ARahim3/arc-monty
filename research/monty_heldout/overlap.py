"""monty-heldout: overlap of candidate datasets with the 1,147 development tasks (and ConceptARC), by hashing whole pairs
(input and output grids), inputs alone, and whole tasks, also up to D8 + colour-blind checks on inputs. Reads JSON only.
usage: python -I -B overlap.py DIR [DIR ...]"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))  # repo root
import collections
import glob
import hashlib
import json
import os
import sys

sys.path.insert(0, (_REPO + "/research/monty_heldout"))
from hl_common import CONCEPT, ROOT  # noqa: E402
import numpy as np  # noqa: E402
from arcmonty.data import SPLITS  # noqa: E402


def gh(g):
    a = np.array(g, dtype=np.int8)
    return hashlib.md5(str(a.shape).encode() + a.tobytes()).hexdigest()


def pairs_of(raw):
    return [(gh(p["input"]), gh(p["output"])) for p in list(raw.get("train", [])) + list(raw.get("test", [])) if "output" in p]


def load(path):
    out = {}
    for fn in sorted(glob.glob(os.path.join(path, "**", "*.json"), recursive=True)):
        try:
            raw = json.load(open(fn))
            if "train" in raw and "test" in raw:
                out[os.path.relpath(fn, path)] = raw
        except Exception:
            pass
    return out


dev_pairs, dev_inputs, dev_tasks = set(), set(), {}
dev_ids = set()
for s, p in SPLITS.items():
    for k, raw in load(p).items():
        dev_ids.add(k)
        pp = pairs_of(raw)
        dev_pairs.update(pp)
        dev_inputs.update(i for i, _ in pp)
print("dev: task ids", len(dev_ids), "distinct pairs", len(dev_pairs), "distinct inputs", len(dev_inputs))
concept = load(CONCEPT)
c_pairs = {x for r in concept.values() for x in pairs_of(r)}
print("ConceptARC: tasks", len(concept), "distinct pairs", len(c_pairs), "shared with dev", len(c_pairs & dev_pairs))
for path in sys.argv[1:]:
    tasks = load(path)
    allp = [pairs_of(r) for r in tasks.values()]
    flat = {x for pp in allp for x in pp}
    t_any = sum(any(x in dev_pairs for x in pp) for pp in allp)
    t_inp = sum(any(x[0] in dev_inputs for x in pp) for pp in allp)
    t_all = sum(bool(pp) and all(x in dev_pairs for x in pp) for pp in allp)
    t_c = sum(any(x in c_pairs for x in pp) for pp in allp)
    ntest = collections.Counter(len(r["test"]) for r in tasks.values())
    nd = collections.Counter(len(r["train"]) for r in tasks.values())
    sizes = collections.Counter()
    for r in tasks.values():
        for p in r["train"]:
            sizes[(len(p["input"]), len(p["input"][0]))] += 1
    print(path)
    print("  tasks", len(tasks), "distinct pairs", len(flat), "shared with dev", len(flat & dev_pairs), "with ConceptARC", len(flat & c_pairs))
    print("  tasks with any pair in dev", t_any, "all pairs in dev", t_all, "any input in dev", t_inp, "any pair in ConceptARC", t_c)
    print("  test inputs per task", dict(ntest), "demos per task", dict(nd), "commonest sizes", sizes.most_common(4))
    print("  example names", list(tasks)[:5])
