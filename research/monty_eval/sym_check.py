"""WS4 / FA-LOO: is Monty-ARC v5 symmetric in its demo multiset (an assumption of the 1/(n+1) bound)?
Re-runs the frozen system with the demo order reversed and compares the top pooled answer, the attempts and the
confident flag with the cached original-order run.  -> results/sym_check.json
usage: nice -n 10 python research/monty_eval/sym_check.py agi2-eval agi1-eval
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import sys  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

from common import ROOT, build_cands, cache_for, tasks_for  # noqa: E402
from arcmonty import monty_arc  # noqa: E402
from arcmonty.vote import attempts_from, confident, pool  # noqa: E402


def same(a, b):
    return len(a) == len(b) and all(np.array_equal(x, y) for x, y in zip(a, b))


def one(args):
    key, task, row = args
    rev = dict(task, train=task["train"][::-1])
    c_rev = monty_arc.candidates(rev)
    c_org = build_cands(row)
    b_rev, b_org = pool(c_rev), pool(c_org)
    top_same = (not b_rev and not b_org) or (bool(b_rev) and bool(b_org) and same(b_rev[0]["preds"], b_org[0]["preds"]))
    att_same = all(same(x, y) for x, y in zip(attempts_from(task, c_rev), attempts_from(task, c_org)))
    return key, dict(top_same=bool(top_same), attempts_same=bool(att_same), conf_same=confident(c_rev) == confident(c_org),
                     n_hyp=(len(b_org), len(b_rev)))


if __name__ == "__main__":
    out = {}
    with mp.Pool(4) as p:
        for split in sys.argv[1:]:
            tasks, rows = tasks_for(split), cache_for(split)
            res = dict(p.map(one, [(k, tasks[k], rows[k]) for k in tasks], chunksize=2))
            out[split] = dict(n=len(res), top_same=sum(r["top_same"] for r in res.values()),
                              attempts_same=sum(r["attempts_same"] for r in res.values()),
                              conf_same=sum(r["conf_same"] for r in res.values()),
                              differ=sorted(k for k, r in res.items() if not (r["top_same"] and r["conf_same"])))
            print(split, out[split], flush=True)
    json.dump(out, open(os.path.join(ROOT, "research", "monty_eval", "results", "sym_check.json"), "w"), indent=1)
