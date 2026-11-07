"""WS4 paper evaluation, step 1: run every Monty-ARC v5 learning module once per task and cache its candidates.

Frozen code: imports arcmonty unchanged and reproduces monty_arc.candidates(task) (perspective 0 only) module by
module, so any module subset's vote can be recomputed offline (see ablate.py; equivalence checked by verify.py).

Cache: research/monty_eval/cache/<split>.jsonl, one line per task:
  {"task", "split", "grids": [unique predicted grids], "mods": {name: {"wall", "cpu", "err",
   "cands": [{"lm", "hyp", "ev", "p": [grid index per test input]}]}}}
Resumable: tasks already in the file are skipped.

usage: nice -n 10 python research/monty_eval/run_modules.py [--procs 8] split [split ...]
splits: agi2-eval agi1-eval agi2-train agi1-train  (new233 is a subset of agi2-train, see splits.py)
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import numpy as np  # noqa: E402

from arcmonty import behavior, monty_arc, symmetry  # noqa: E402
from arcmonty.data import load_split  # noqa: E402

CACHE = os.path.join(ROOT, "research", "monty_eval", "cache")
# display names, in monty_arc.MODULES order (the order matters: vote ties break by candidate order)
NAMES = {"symmetry": "self-model", "periodic": "periodic", "behavior": "behavior", "dynamics": "dynamics",
         "composition": "composition", "association": "association", "pattern": "pattern", "field": "field"}
MODULE_ORDER = [NAMES[m.__name__.split(".")[-1]] for m in monty_arc.MODULES]


def run_task(item):
    split, key, task = item
    # per-task cold caches: honest per-module timing (caches are pure memoisation keyed by grid content)
    symmetry._CACHE.clear()
    behavior._SEG_CACHE.clear()
    grids, index = [], {}

    def gid(a):
        a = np.ascontiguousarray(a)
        k = (a.shape, a.dtype.str, a.tobytes())
        if k not in index:
            index[k] = len(grids)
            grids.append(a.tolist())
        return index[k]

    mods = {}
    for m in monty_arc.MODULES:  # identical to monty_arc.candidates(task, perspectives=(0,))
        name = NAMES[m.__name__.split(".")[-1]]
        t0, c0 = time.perf_counter(), time.process_time()
        err, cands = None, []
        try:
            cands = m.candidates(task)
        except Exception as e:  # monty_arc.candidates swallows module exceptions the same way
            err, cands = repr(e)[:300], []
        wall, cpu = time.perf_counter() - t0, time.process_time() - c0
        rows = []
        for c in cands:
            rows.append(dict(lm=c["lm"], hyp=str(c.get("hyp", ""))[:400], ev=float(c["evidence"]),
                             p=[gid(np.rot90(p, 0)) for p in c["preds"]]))
        mods[name] = dict(wall=round(wall, 4), cpu=round(cpu, 4), err=err, cands=rows)
    return dict(task=key, split=split, grids=grids, mods=mods)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("splits", nargs="+")
    ap.add_argument("--procs", type=int, default=8)
    args = ap.parse_args()
    os.makedirs(CACHE, exist_ok=True)
    for split in args.splits:
        path = os.path.join(CACHE, f"{split}.jsonl")
        done, good, torn = set(), [], False
        if os.path.exists(path):
            with open(path) as fh:
                for line in fh:
                    try:
                        done.add(json.loads(line)["task"])
                        good.append(line if line.endswith("\n") else line + "\n")
                    except Exception:  # a torn line from a killed run: dropped and recomputed
                        torn = True
            if torn:
                with open(path, "w") as fh:
                    fh.writelines(good)
        tasks = load_split(split)
        todo = [(split, k, t) for k, t in tasks.items() if k not in done]
        print(f"{split}: {len(tasks)} tasks, {len(done)} cached, {len(todo)} to run", flush=True)
        if not todo:
            continue
        t0 = time.time()
        # heaviest-first is unknown; small chunks keep the pool balanced
        with mp.Pool(args.procs, maxtasksperchild=50) as pool, open(path, "a") as out:
            for n, row in enumerate(pool.imap_unordered(run_task, todo, chunksize=1), 1):
                out.write(json.dumps(row, separators=(",", ":")) + "\n")
                out.flush()
                if n % 50 == 0 or n == len(todo):
                    print(f"  {split} {n}/{len(todo)}  {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
