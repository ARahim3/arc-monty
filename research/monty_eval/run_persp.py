"""WS4 / FA-LOO optional: full-data per-module candidates under the extra D8 perspectives 1..7 (perspective 0 is in
cache/<split>.jsonl), so whole-task perspective voting (v5 with perspectives=range(8)) can be re-voted offline.
Writes cache/persp_p1-7_<split>.jsonl ({task, grids, mods}); resumable.
usage: nice -n 10 python research/monty_eval/run_persp.py --procs 4 agi1-train
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse  # noqa: E402
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

from common import CACHE, tasks_for  # noqa: E402
from run_folds import run_modules_on  # noqa: E402
from arcmonty import behavior, symmetry  # noqa: E402


def run_task(item):
    split, key, task = item
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

    return dict(task=key, split=split, grids=grids, mods=run_modules_on(task, tuple(range(1, 8)), gid))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("splits", nargs="+")
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    for split in a.splits:
        path = os.path.join(CACHE, f"persp_p1-7_{split}.jsonl")
        done = set()
        if os.path.exists(path):
            good = []
            for line in open(path):
                try:
                    done.add(json.loads(line)["task"])
                    good.append(line if line.endswith("\n") else line + "\n")
                except Exception:
                    pass
            open(path, "w").writelines(good)
        tasks = tasks_for(split)
        todo = [(split, k, t) for k, t in tasks.items() if k not in done]
        print(split, len(todo), "to run", flush=True)
        t0 = time.time()
        with mp.Pool(a.procs, maxtasksperchild=40) as pool, open(path, "a") as out:
            for n, row in enumerate(pool.imap_unordered(run_task, todo, chunksize=1), 1):
                out.write(json.dumps(row, separators=(",", ":")) + "\n")
                out.flush()
                if n % 50 == 0 or n == len(todo):
                    print(f"  {split} {n}/{len(todo)} {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
