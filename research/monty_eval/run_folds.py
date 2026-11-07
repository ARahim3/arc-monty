"""WS4 / FA-LOO step 1: run the frozen Monty-ARC v5 modules on every leave-one-demo-out fold of every task and cache
each module's candidates (same format as run_modules.py), so fold-agreement LOO can be evaluated offline for any vote
rule (v5, cross-module/P4, module alone) and any perspective set.

Fold (i, t): train = demos minus demo i; queries = [x_i, x*_t] (held-out demo input, test input t). Querying the pair
jointly makes the fold model exactly M_{i,n+1} of the jackknife+ tournament argument.
Perspectives: each module runs on the D8 view k of the fold task and its predictions are mapped back, exactly as
monty_arc.candidates(task, perspectives) does (lm tagged "<name>@k").

Cache: research/monty_eval/cache/folds_p<tag>_<split>.jsonl, one line per task:
  {"task","split","n","T","folds":[{"i","t","grids","mods":{name:{"wall","cpu","err","cands":[{"lm","hyp","ev","p":[gx,gt]}]}}}]}
Resumable (tasks already in the file are skipped).
usage: nice -n 10 python research/monty_eval/run_folds.py --procs 4 --persp 0 split [split ...]
       --persp 1-7 for the extra perspectives (merged with p0 offline)
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
from run_modules import NAMES  # noqa: E402
from arcmonty import behavior, monty_arc, symmetry  # noqa: E402
from arcmonty.objects import d8  # noqa: E402

PERSP = (0,)


def run_modules_on(task, persp, gid):
    """Per-module candidates of monty_arc.candidates(task, persp), with timing."""
    mods = {}
    for k in persp:
        view = task if k == 0 else monty_arc._view(task, k)
        for m in monty_arc.MODULES:
            name = NAMES[m.__name__.split(".")[-1]]
            t0, c0 = time.perf_counter(), time.process_time()
            err, cands = None, []
            try:
                cands = m.candidates(view)
            except Exception as e:  # swallowed exactly as monty_arc.candidates does
                err, cands = repr(e)[:200], []
            rec = mods.setdefault(name, dict(wall=0.0, cpu=0.0, err=None, cands=[]))
            rec["wall"] += time.perf_counter() - t0
            rec["cpu"] += time.process_time() - c0
            rec["err"] = rec["err"] or err
            for c in cands:
                rec["cands"].append(dict(lm=f"{c['lm']}@{k}", hyp=str(c.get("hyp", ""))[:200], ev=float(c["evidence"]),
                                         p=[gid(d8(p, monty_arc._INV[k])) for p in c["preds"]]))
    for rec in mods.values():
        rec["wall"], rec["cpu"] = round(rec["wall"], 4), round(rec["cpu"], 4)
    return mods


def run_task(item):
    split, key, task = item
    pairs = task["train"]
    folds = []
    for i in range(len(pairs)):
        for t in range(len(task["test"])):
            symmetry._CACHE.clear()
            behavior._SEG_CACHE.clear()
            grids, index = [], {}

            def gid(a):
                a = np.ascontiguousarray(a)
                kk = (a.shape, a.dtype.str, a.tobytes())
                if kk not in index:
                    index[kk] = len(grids)
                    grids.append(a.tolist())
                return index[kk]

            fold = {"train": pairs[:i] + pairs[i + 1:], "test": [pairs[i][0], task["test"][t]]}
            folds.append(dict(i=i, t=t, grids=grids, mods=run_modules_on(fold, PERSP, gid)))
    return dict(task=key, split=split, n=len(pairs), T=len(task["test"]), folds=folds)


def _init(p):
    global PERSP
    PERSP = p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("splits", nargs="+")
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--persp", default="0")
    args = ap.parse_args()
    persp = tuple(range(int(args.persp.split("-")[0]), int(args.persp.split("-")[1]) + 1)) if "-" in args.persp \
        else tuple(int(x) for x in args.persp.split(","))
    tag = args.persp.replace(",", "_")
    for split in args.splits:
        path = os.path.join(CACHE, f"folds_p{tag}_{split}.jsonl")
        done, good, torn = set(), [], False
        if os.path.exists(path):
            for line in open(path):
                try:
                    done.add(json.loads(line)["task"])
                    good.append(line if line.endswith("\n") else line + "\n")
                except Exception:
                    torn = True
            if torn:
                open(path, "w").writelines(good)
        tasks = tasks_for(split)
        todo = [(split, k, t) for k, t in tasks.items() if k not in done]
        # longest tasks first (more demos, bigger grids) to keep the pool balanced at the end
        todo.sort(key=lambda x: -(len(x[2]["train"]) * len(x[2]["test"]) * max(i.size for i, _ in x[2]["train"])))
        print(f"{split} persp={persp}: {len(tasks)} tasks, {len(done)} cached, {len(todo)} to run", flush=True)
        if not todo:
            continue
        t0 = time.time()
        with mp.Pool(args.procs, initializer=_init, initargs=(persp,), maxtasksperchild=40) as pool, open(path, "a") as out:
            for n, row in enumerate(pool.imap_unordered(run_task, todo, chunksize=1), 1):
                out.write(json.dumps(row, separators=(",", ":")) + "\n")
                out.flush()
                if n % 50 == 0 or n == len(todo):
                    print(f"  {split} {n}/{len(todo)}  {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
