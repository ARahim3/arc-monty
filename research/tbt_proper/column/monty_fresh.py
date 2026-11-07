"""Frozen Monty-ARC v5 on a fresh set: arcmonty/ imported unchanged, real test role only, one view, as research/monty_heldout/.
For an item with demos + one test pair: the full-data run and one fold run per demo; rules from monty_heldout/rules.py.
usage: python -I -B monty_fresh.py SET TAG [--procs 4] -> results/monty_TAG.jsonl (resumable)"""
import argparse, json, multiprocessing as mp, os, sys, time
ROOT = "/Users/abdurrahim/Codes/arc_monty"
sys.path.insert(0, os.path.join(ROOT, "research", "monty_heldout"))
from hl_common import h, read_done  # noqa: E402  (sets single-thread env, loads task parser)
import numpy as np  # noqa: E402
from run_folds import run_modules_on  # noqa: E402  (research/monty_eval)
from rules import build, faloo_role, full_outcome, top_of  # noqa: E402
from arcmonty import behavior, symmetry  # noqa: E402

RES = os.path.join(ROOT, "research", "tbt_proper", "column", "results")


def run(item):
    key, pool = item
    t0 = time.process_time()
    m, grids, index = len(pool), [], {}

    def gid(a):
        a = np.ascontiguousarray(a)
        kk = (a.shape, a.dtype.str, a.tobytes())
        if kk not in index:
            index[kk] = len(grids)
            grids.append(a.copy())
        return index[kk]

    def one(train, queries):
        symmetry._CACHE.clear()
        behavior._SEG_CACHE.clear()
        return run_modules_on({"train": train, "test": queries}, (0,), gid)

    a = m - 1
    x, y = pool[a]
    runs = {f"F{a}": one(pool[:a], [x])}
    for b in range(a):
        runs[f"{a},{b}"] = one([pool[j] for j in range(a) if j != b], [pool[b][0], x])
    row = dict(runs=runs, _np=grids)
    C = build([row], f"F{a}", views={0})
    o = full_outcome({"test": [x], "test_out": [y]}, C)
    top = top_of(C, "v5")
    folds = {b: top_of(build([row], f"{a},{b}", views={0}), "v5") for b in range(a)}
    r = faloo_role(None if top is None else top[0], y, folds, {b: pool[b][1] for b in range(a)})
    o.update(a=r["a"], fa=r["fa"], fc=r["fc"], why=r["why"])
    o["fold_programs"] = [[bool(np.array_equal(p[0], pool[b][1])), bool(np.array_equal(p[1], y))] for b, p in folds.items() if p is not None]
    return dict(task=key, m=m, cfg={"full": {str(a): o}}, cpu=round(time.process_time() - t0, 2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source"); ap.add_argument("tag"); ap.add_argument("--procs", type=int, default=4); ap.add_argument("--out", default=RES); ap.add_argument("--keys", default="")
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from data_sets import items_of
    items = items_of(a.source)
    if a.keys:  # development dry run only: a sample of tasks
        keep = set(json.load(open(a.keys)))
        items = [x for x in items if x[0].split("#")[0] in keep]
    os.makedirs(a.out, exist_ok=True)
    out = os.path.join(a.out, f"monty_{a.tag}.jsonl")
    done = read_done(out)
    todo = [x for x in items if x[0] not in done]
    todo.sort(key=lambda x: len(x[1]) * max(i.size for i, _ in x[1]))
    print(out, len(items), "items", len(done), "done", len(todo), "todo", flush=True)
    t0 = time.time()
    with mp.Pool(a.procs, maxtasksperchild=30) as pool, open(out, "a") as fh:
        for n, r in enumerate(pool.imap_unordered(run, todo, chunksize=1), 1):
            fh.write(json.dumps(r, separators=(",", ":"), default=float) + "\n")
            fh.flush()
            if n % 100 == 0 or n == len(todo):
                print(n, len(todo), round(time.time() - t0), flush=True)
