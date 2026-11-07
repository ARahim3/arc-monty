"""Coverage, calibrated precision and timing of Monty-ARC per split.

any-answer: pass@2 when Monty-ARC always answers (pure submission).
confident (single view): fully evidenced consensus in the task's own frame only.
confident (D8): fully evidenced consensus pooled over the 8 D8 perspectives (used by the hybrid merge).
"""
import collections
import multiprocessing as mp
import sys
import time

import numpy as np

from arcmonty import monty_arc
from arcmonty.data import load_split
from arcmonty.evaluate import score_task
from arcmonty.vote import attempts_from, confident, pool


def _one(args):
    key, task = args
    t0 = time.time()
    cands = monty_arc.candidates(task)
    dt = time.time() - t0
    c0 = [c for c in cands if c["lm"].endswith("@0")]
    s_all = score_task(task, attempts_from(task, cands))
    single = score_task(task, attempts_from(task, c0, 0.99)) if confident(c0) else None
    d8 = score_task(task, attempts_from(task, cands, 0.99)) if confident(cands) else None
    best = pool(cands)
    lms = sorted({v.split("@")[0] for v in best[0]["voters"]}) if best and s_all > 0 else []
    return key, bool(best), s_all, single, d8, dt, lms


if __name__ == "__main__":
    for split in sys.argv[1:]:
        tasks = load_split(split)
        with mp.Pool(12) as pool_:
            res = pool_.map(_one, list(tasks.items()), chunksize=1)
        n = len(tasks)
        total = sum(r[2] for r in res)
        sg = [r[3] for r in res if r[3] is not None]
        d8 = [r[4] for r in res if r[4] is not None]
        ts = np.array([r[5] for r in res])
        by_lm = collections.Counter(l for r in res if r[2] > 0 for l in r[6])
        print(f"{split:11s} n={n:4d} | pass@2 {total:5.1f} ({100 * total / n:5.2f}%) answered={sum(r[1] for r in res):4d} | "
              f"confident single {sum(sg):.0f}/{len(sg)} | D8 {sum(d8):.0f}/{len(d8)} | "
              f"sec/task mean {ts.mean():.1f} p90 {np.percentile(ts, 90):.1f} max {ts.max():.0f} | by module {dict(by_lm)}",
              flush=True)
        print("   solved:", " ".join(r[0] for r in res if r[2] > 0), flush=True)
