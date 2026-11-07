"""Run a solver over a split in parallel and report pass@2.  usage: python -m arcmonty.bench <module> <split> [<split> ...]"""
import importlib
import multiprocessing as mp
import sys
import time

from arcmonty.data import load_split
from arcmonty.evaluate import score_task


def _one(args):
    modname, key, task = args
    mod = importlib.import_module(modname)
    t0 = time.time()
    try:
        attempts = mod.solve(task)
        err = None
    except Exception as e:  # keep the sweep alive; report the failure
        attempts, err = [], repr(e)
    return key, score_task(task, attempts), time.time() - t0, err, sum(len(a) > 0 for a in attempts)


def bench(modname, split, procs=12):
    tasks = load_split(split)
    t0 = time.time()
    with mp.Pool(procs) as pool:
        res = pool.map(_one, [(modname, k, t) for k, t in tasks.items()], chunksize=1)
    solved = [(k, s) for k, s, _, _, _ in res if s > 0]
    answered = sum(1 for r in res if r[4] > 0)
    errs = [(k, e) for k, _, _, e, _ in res if e]
    total = sum(s for _, s, _, _, _ in res)
    slow = sorted(res, key=lambda r: -r[2])[:3]
    print(f"{modname} {split}: {total:.2f}/{len(tasks)} = {100 * total / len(tasks):.2f}%  answered={answered} "
          f"errors={len(errs)} wall={time.time() - t0:.0f}s slowest={[(k, round(t)) for k, _, t, _, _ in slow]}")
    print("   solved:", " ".join(k for k, _ in solved))
    if errs:
        print("   first errors:", errs[:3])
    return res


if __name__ == "__main__":
    for split in sys.argv[2:]:
        bench(sys.argv[1], split)
