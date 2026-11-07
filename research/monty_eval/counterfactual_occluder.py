"""WS4 outlook estimate (analysis only, not part of v5): how many tasks would the frozen self-model inference solve if
its occluder sensor accepted "every cell of the colour that vanishes from input to output" instead of "the single
colour forming one solid rectangle"? Reuses symmetry.complete / local_complete unchanged; same acceptance rule as
symmetry.candidates (a config must reproduce every demo; then predict the test).
"""
import json
import multiprocessing as mp
import os
import sys

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

from common import ALL_SPLITS, ROOT, cache_for, tasks_for, build_cands  # noqa: E402
from arcmonty import symmetry  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402
from arcmonty.vote import attempts_from  # noqa: E402


def fill(grid, c, cfg):
    kw = {k: v for k, v in cfg.items() if k != "local"}
    unknown = grid == c
    if not unknown.any() or unknown.all():
        return None
    return symmetry.local_complete(grid, unknown) if cfg.get("local") else symmetry.complete(grid, unknown, **kw)


def one(args):
    split, key, task = args
    pairs = task["train"]
    if not all(i.shape == o.shape for i, o in pairs):
        return key, None
    gone = None
    for i, o in pairs:
        g = set(np.unique(i[i != o]).tolist())
        gone = g if gone is None else gone & g
    for c in sorted(gone or []):
        for cfg in symmetry.CONFIGS[:5]:
            if all((p := fill(i, c, cfg)) is not None and np.array_equal(p, o) for i, o in pairs):
                preds = [fill(t, c, cfg) for t in task["test"]]
                if all(p is not None for p in preds):
                    return key, dict(color=c, cfg=str(cfg), preds=[p.tolist() for p in preds])
    return key, None


def main():
    out = {}
    with mp.Pool(8) as pool:
        for split in ALL_SPLITS:
            tasks, rows = tasks_for(split), cache_for(split)
            res = dict(pool.map(one, [(split, k, t) for k, t in tasks.items()], chunksize=2))
            new_solved, fp = [], []
            for k, r in res.items():
                if r is None:
                    continue
                task = tasks[k]
                ok = score_task(task, [[np.array(p)] for p in r["preds"]])
                base = score_task(task, attempts_from(task, build_cands(rows[k])))
                (new_solved if ok >= 1 and base < 1 else fp if ok < 1 else []).append(k)
            out[split] = dict(fires=sum(r is not None for r in res.values()), new_solves=sorted(new_solved),
                              wrong=sorted(fp))
            print(split, out[split], flush=True)
    with open(os.path.join(ROOT, "research", "monty_eval", "results", "counterfactual_occluder.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
