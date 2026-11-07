"""monty-heldout step 1: cache per-module candidates of frozen v5 for every role and fold of every item.

For an item with pool = demos + one test pair (m pairs; role a = m-1 is the real test role):
  run "F<a>"   : train = pool minus a,    queries [x_a]            (full-data system when a plays test)
  run "<a>,<b>": train = pool minus a, b, queries [x_b, x_a]       (fold model M_ab of the tournament)
exactly as paper-judge's rotate.py, but per module and per D8 perspective, so any vote rule, module subset or frame
restriction can be re-voted offline. Resumable (one JSON line per item).

--arm global re-runs only the behaviour module with a monkeypatched frame "global" (absolute grid coordinates, no object
anchor); nothing in arcmonty/ is edited.
usage: nice -n 15 python run_cache.py DIR TAG --persp 0|1-7 [--arm global] [--procs 8]
       writes cache/TAG_p<persp>[_<arm>].jsonl
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import CACHE, h, items_from_dir, read_done  # noqa: E402
import numpy as np  # noqa: E402
from run_folds import run_modules_on  # noqa: E402  (research/monty_eval)
from run_modules import NAMES  # noqa: E402
from arcmonty import behavior, monty_arc, symmetry  # noqa: E402
from arcmonty.objects import d8  # noqa: E402

PERSP = (0,)
ARM = None
_ORIG = behavior._frame_coords


def _coords_global(o, ys, xs, frame):
    if frame == "global":
        return ys, xs
    return _ORIG(o, ys, xs, frame)


def _init(persp, arm):
    global PERSP, ARM
    PERSP, ARM = persp, arm
    if arm == "global":
        behavior.FRAMES = ("global",)
        behavior._frame_coords = _coords_global


def _behaviour_only(task, persp, gid):
    """Behaviour module only, same bookkeeping as run_folds.run_modules_on."""
    rec = dict(wall=0.0, cpu=0.0, err=None, cands=[])
    for k in persp:
        view = task if k == 0 else monty_arc._view(task, k)
        c0 = time.process_time()
        try:
            cands = behavior.candidates(view)
        except Exception as e:
            cands = []
            rec["err"] = rec["err"] or repr(e)[:200]
        rec["cpu"] += time.process_time() - c0
        for c in cands:
            rec["cands"].append(dict(lm=f"{c['lm']}@{k}", hyp=str(c.get("hyp", ""))[:200], ev=float(c["evidence"]),
                                     p=[gid(d8(p, monty_arc._INV[k])) for p in c["preds"]]))
    rec["cpu"] = round(rec["cpu"], 4)
    return {"behavior": rec}


def run(item):
    key, pool = item
    t0 = time.process_time()
    m = len(pool)
    grids, index = [], {}

    def gid(a):
        a = np.ascontiguousarray(a)
        kk = (a.shape, a.dtype.str, a.tobytes())
        if kk not in index:
            index[kk] = len(grids)
            grids.append(a.tolist())
        return index[kk]

    def one(train, queries):
        symmetry._CACHE.clear()
        behavior._SEG_CACHE.clear()
        task = {"train": train, "test": queries}
        return _behaviour_only(task, PERSP, gid) if ARM else run_modules_on(task, PERSP, gid)

    runs = {}
    for a in range(m):
        runs[f"F{a}"] = one([pool[j] for j in range(m) if j != a], [pool[a][0]])
        for b in range(m):
            if b != a:
                runs[f"{a},{b}"] = one([pool[j] for j in range(m) if j not in (a, b)], [pool[b][0], pool[a][0]])
    return dict(task=key, m=m, truth=[h(o) for _, o in pool], grids=grids, runs=runs, cpu=round(time.process_time() - t0, 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("tag")
    ap.add_argument("--persp", default="0")
    ap.add_argument("--arm", default=None)
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    persp = tuple(range(int(a.persp.split("-")[0]), int(a.persp.split("-")[1]) + 1)) if "-" in a.persp else (int(a.persp),)
    path = os.path.join(CACHE, f"{a.tag}_p{a.persp}" + (f"_{a.arm}" if a.arm else "") + ".jsonl")
    done = read_done(path)
    items = items_from_dir(a.dir)
    todo = [x for x in items if x[0] not in done]
    todo.sort(key=lambda x: len(x[1]) ** 2 * max(i.size for i, _ in x[1]))
    print(path, len(items), "items", len(done), "done", len(todo), "todo", flush=True)
    if not todo:
        return
    t0 = time.time()
    with mp.Pool(a.procs, initializer=_init, initargs=(persp, a.arm), maxtasksperchild=30) as pool, open(path, "a") as fh:
        for n, r in enumerate(pool.imap_unordered(run, todo, chunksize=1), 1):
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
            fh.flush()
            if n % 40 == 0 or n == len(todo):
                print(n, len(todo), round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
