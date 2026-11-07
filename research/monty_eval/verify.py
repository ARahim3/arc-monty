"""WS4: check that offline subset voting (cache + vote.py) equals real Monty-ARC runs with a restricted module list.

1. Real runs: monty_arc.MODULES is monkeypatched (inside each worker; the package is not edited) to a subset and
   monty_arc.solve(task) is compared, attempt by attempt and grid by grid, with attempts_from() on the cached
   candidates of the same subset. Subsets: full, -behavior, -composition, behavior alone, {self-model, periodic,
   association}.
2. The offline full system is compared with the published local report research/report_v1e.txt (solved lists).
usage: python research/monty_eval/verify.py [split ...]   (default: agi2-eval agi1-eval)
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

from common import BASE_SPLITS, MODULES, ROOT, build_cands, cache_for, tasks_for  # noqa: E402
from arcmonty import monty_arc  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402
from arcmonty.vote import attempts_from  # noqa: E402

ORIG = monty_arc.MODULES
BY_NAME = dict(zip(MODULES, ORIG))
CHECK = {"full": MODULES, "-behavior": [m for m in MODULES if m != "behavior"],
         "-composition": [m for m in MODULES if m != "composition"], "behavior alone": ["behavior"],
         "self-model+periodic+association": ["self-model", "periodic", "association"]}


def same(a, b):
    return len(a) == len(b) and all(len(x) == len(y) and all(np.array_equal(p, q) for p, q in zip(x, y))
                                    for x, y in zip(a, b))


def one(args):
    key, task, row = args
    out = {}
    for name, mods in CHECK.items():
        monty_arc.MODULES = tuple(BY_NAME[m] for m in MODULES if m in mods)
        real = monty_arc.solve(task)
        off = attempts_from(task, build_cands(row, set(mods)))
        out[name] = same(real, off)
    monty_arc.MODULES = ORIG
    return key, out


def report_solved():
    txt = open(os.path.join(ROOT, "research", "report_v1e.txt")).read().splitlines()
    out, cur = {}, None
    for line in txt:
        m = re.match(r"^(\S+)\s+n=", line)
        if m:
            cur = m.group(1)
        elif line.strip().startswith("solved:") and cur:
            out[cur] = set(line.split(":", 1)[1].split())
    return out


if __name__ == "__main__":
    splits = sys.argv[1:] or ["agi2-eval", "agi1-eval"]
    summary = {}
    with mp.Pool(8) as p:
        for split in splits:
            rows, tasks = cache_for(split), tasks_for(split)
            res = dict(p.imap_unordered(one, [(k, tasks[k], rows[k]) for k in tasks], chunksize=1))
            summary[split] = {name: dict(match=sum(r[name] for r in res.values()), n=len(res),
                                         mismatched=sorted(k for k, r in res.items() if not r[name]))
                              for name in CHECK}
            print(split, {n: f"{v['match']}/{v['n']}" for n, v in summary[split].items()}, flush=True)
    rep = report_solved()
    summary["vs_report_v1e"] = {}
    for split in BASE_SPLITS:
        try:
            rows, tasks = cache_for(split), tasks_for(split)
        except FileNotFoundError:
            continue
        if set(tasks) - set(rows):
            continue
        solved = {k for k in tasks if score_task(tasks[k], attempts_from(tasks[k], build_cands(rows[k]))) > 0}
        summary["vs_report_v1e"][split] = dict(offline=len(solved), report=len(rep.get(split, ())),
                                               only_offline=sorted(solved - rep.get(split, set())),
                                               only_report=sorted(rep.get(split, set()) - solved))
        print("vs report_v1e", split, summary["vs_report_v1e"][split], flush=True)
    os.makedirs(os.path.join(ROOT, "research", "monty_eval", "results"), exist_ok=True)
    with open(os.path.join(ROOT, "research", "monty_eval", "results", "verify.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
