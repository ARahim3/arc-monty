"""monty-heldout: behaviour module with the monkeypatched 'global' frame on the 1,147 development tasks (full data + every
fold), the comparator for the global arm. Dev is already seen, so this is no held-out use. Resumable.
usage: nice -n 15 python dev_global.py [--procs 8] -> cache/dev_global.jsonl"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import CACHE, read_done  # noqa: E402
import numpy as np  # noqa: E402
from make_tables import distinct_items  # noqa: E402  (research/monty_eval)
import run_cache  # noqa: E402
from arcmonty import behavior, symmetry  # noqa: E402


def run(item):
    split, key, task = item
    pairs = task["train"]
    grids, index = [], {}

    def gid(a):
        a = np.ascontiguousarray(a)
        kk = (a.shape, a.dtype.str, a.tobytes())
        if kk not in index:
            index[kk] = len(grids)
            grids.append(a.tolist())
        return index[kk]

    def one(tr, q):
        symmetry._CACHE.clear()
        behavior._SEG_CACHE.clear()
        return run_cache._behaviour_only({"train": tr, "test": q}, (0,), gid)

    full = one(pairs, task["test"])
    folds = []
    for i in range(len(pairs)):
        for t in range(len(task["test"])):
            folds.append(dict(i=i, t=t, mods=one(pairs[:i] + pairs[i + 1:], [pairs[i][0], task["test"][t]])))
    return dict(task=key, split=split, grids=grids, mods=full, folds=folds)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    path = os.path.join(CACHE, "dev_global.jsonl")
    done = read_done(path)
    todo = [(s, k, t) for s, k, _, t in distinct_items() if k not in done]
    print(len(todo), "todo", flush=True)
    t0 = time.time()
    with mp.Pool(a.procs, initializer=run_cache._init, initargs=((0,), "global"), maxtasksperchild=100) as p, open(path, "a") as fh:
        for n, r in enumerate(p.imap_unordered(run, todo, chunksize=2), 1):
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
            fh.flush()
            if n % 200 == 0 or n == len(todo):
                print(n, len(todo), round(time.time() - t0), flush=True)
