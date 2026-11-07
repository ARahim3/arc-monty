"""monty-heldout: the same rules and configurations on the 1,147 development tasks, from the existing caches
(research/monty_eval/cache; read-only) plus cache/dev_global.jsonl. Unit = task, as in monty_ablations.md / monty_faloo.md.
usage: nice -n 15 python dev_compare.py [--procs 8] -> results/dev_base.jsonl"""
import argparse
import json
import multiprocessing as mp
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import CACHE, HERE, MODULES  # noqa: E402
import numpy as np  # noqa: E402
from faloo import load_folds  # noqa: E402
from make_tables import distinct_items  # noqa: E402
from rules import full_outcome, faloo_role, top_of, module_name  # noqa: E402

_F = {}
_G = {}


def shim(row, mods=None):
    """(lm tags + grids) of one dev cache row into the format of rules.build."""
    r = dict(_np=[np.array(g, dtype=np.int8) for g in row["grids"]], runs={"R": {}})
    src = mods if mods is not None else row["mods"]
    for m, rec in src.items():
        cs = []
        for c in rec["cands"]:
            lm = c["lm"] if "@" in c["lm"] else f"{c['lm']}@0"
            cs.append(dict(c, lm=lm))
        r["runs"]["R"][m] = dict(cands=cs)
    return r


def configs():
    allm = set(MODULES)
    c = {"full": {}}
    c.update({f"-{m}": dict(modules=allm - {m}) for m in MODULES})
    c.update({f"{m} alone": dict(modules={m}) for m in MODULES})
    c.update({"sys:canon": dict(frames={"canon"}), "sys:abs": dict(frames={"abs"}), "sys:global": dict(glob=True),
              "beh:canon": dict(modules={"behavior"}, frames={"canon"}), "beh:abs": dict(modules={"behavior"}, frames={"abs"}),
              "beh:global": dict(modules={"behavior"}, glob=True)})
    return c


def _init():
    global _F, _G
    from common import BASE_SPLITS  # noqa
    for s in ("agi1-train", "agi1-eval", "agi2-train", "agi2-eval"):
        _F[s] = load_folds(s, "0")
    with open(os.path.join(CACHE, "dev_global.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            _G[r["task"]] = r


def one(arg):
    from rules import build
    split, key, row, task = arg
    src = "agi2-train" if split == "new233" else split
    frow = _F[src][key]
    groww = _G[key]
    base = shim(row)
    gbase = shim(groww)
    folds = {(f["i"], f["t"]): shim(f) for f in frow["folds"]}
    gfolds = {(f["i"], f["t"]): shim(dict(grids=groww["grids"]), f["mods"]) for f in groww["folds"]}
    n, T = len(task["train"]), len(task["test"])
    out = {}
    for name, cfg in configs().items():
        kw = dict(modules=cfg.get("modules"), frames=cfg.get("frames"), views={0})
        C = build([base], "R", behavior_rows=[gbase] if cfg.get("glob") else None, **kw)
        o = full_outcome(task, C)
        for rule, tag in (("v5", ""), ("p4", "4")):
            y_full = top_of(C, rule)
            res = []
            for t in range(T):
                ft = {}
                for i in range(n):
                    Cf = build([folds[(i, t)]], "R", behavior_rows=[gfolds[(i, t)]] if cfg.get("glob") else None, **kw)
                    ft[i] = top_of(Cf, rule)
                res.append(faloo_role(None if y_full is None else y_full[t], task["test_out"][t], ft, {i: task["train"][i][1] for i in range(n)}))
            for fld in ("a", "fa", "fc"):
                vals = [r[fld] for r in res]
                o[fld + tag] = None if any(v is None for v in vals) else sum(vals) / len(vals)
        out[name] = o
    return dict(task=key, split=split, n=n, T=T, cfg=out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    items = distinct_items()
    path = os.path.join(HERE, "results", "dev_base.jsonl")
    open(path, "w").close()
    with mp.Pool(a.procs, initializer=_init, maxtasksperchild=200) as p, open(path, "a") as fh:
        for n, r in enumerate(p.imap_unordered(one, items, chunksize=2), 1):
            fh.write(json.dumps(r, separators=(",", ":"), default=float) + "\n")
            if n % 200 == 0 or n == len(items):
                print(n, len(items), flush=True)
