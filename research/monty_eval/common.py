"""Shared helpers for the WS4 evaluation: splits (incl. new233), cache loading, candidate reconstruction."""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import numpy as np  # noqa: E402

from arcmonty.data import SPLITS, load_split  # noqa: E402

CACHE = os.path.join(ROOT, "research", "monty_eval", "cache")
MODULES = ["self-model", "periodic", "behavior", "dynamics", "composition", "association", "pattern", "field"]
BASE_SPLITS = ["agi2-eval", "agi1-eval", "agi2-train", "agi1-train"]
ALL_SPLITS = BASE_SPLITS + ["new233"]


def _ids(path):
    return {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(path, "*.json"))}


def new233_ids():
    """ARC-AGI-2 training tasks whose id is in neither ARC-AGI-1 split (the 767 others hold the same pairs as the
    ARC-AGI-1 task of that id, reordered / re-split). This is the definition behind the 233-task "new in ARC-AGI-2" subset."""
    ids = _ids(SPLITS["agi2-train"]) - _ids(SPLITS["agi1-train"]) - _ids(SPLITS["agi1-eval"])
    assert len(ids) == 233, len(ids)
    return ids


def tasks_for(split):
    if split == "new233":
        keep = new233_ids()
        return {k: t for k, t in load_split("agi2-train").items() if k in keep}
    return load_split(split)


def cache_for(split):
    src = "agi2-train" if split == "new233" else split
    rows = {}
    with open(os.path.join(CACHE, f"{src}.jsonl")) as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            rows[r["task"]] = r
    if split == "new233":
        keep = new233_ids()
        rows = {k: r for k, r in rows.items() if k in keep}
    return rows


def build_cands(row, subset=None):
    """Candidates exactly as monty_arc.candidates(task) returns them, restricted to `subset` (module names);
    the original module order and within-module order are preserved."""
    grids = [np.array(g, dtype=np.int8) for g in row["grids"]]
    out = []
    for m in MODULES:
        if subset is not None and m not in subset:
            continue
        for c in row["mods"][m]["cands"]:
            out.append(dict(lm=f"{c['lm']}@0", hyp=c["hyp"], evidence=c["ev"], preds=[grids[i] for i in c["p"]],
                            module=m))
    return out


def subsets():
    """name -> module set: full, leave-one-module-out, module alone."""
    s = {"full": set(MODULES)}
    for m in MODULES:
        s[f"-{m}"] = set(MODULES) - {m}
    for m in MODULES:
        s[f"{m} alone"] = {m}
    return s
