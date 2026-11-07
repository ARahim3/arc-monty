"""generator_control: offline re-vote of frozen Monty-ARC v5 from the per-module cache, config "full", every role, same rule code as
research/monty_heldout/revote.py (imports rules.py and arcmonty unchanged; that script's other configs are not needed here).
    .venv/bin/python -I -B research/generator_control/monty/revote_gc.py [--procs 4]
Writes monty/results/rearc_base.jsonl: {task, m, truth: [h(y_r)], cfg: {full: {r: outcome}}, swap_diffs}. swap_diffs counts M_ab whose answers
change when the order of the two queries is swapped (a check of (S)). Role m-1 is the real test role."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))  # repo root
import json
import multiprocessing as mp
import os
import sys

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
sys.path.insert(0, os.path.join(ROOT, "research", "monty_heldout"))
from hl_common import h, items_from_dir  # noqa: E402
import numpy as np  # noqa: E402
from rules import build, faloo_role, full_outcome, top_of  # noqa: E402

CACHE = os.path.join(HERE, "monty", "cache", "rearc_p0.jsonl")
OUT = os.path.join(HERE, "monty", "results", "rearc_base.jsonl")
_POOLS = {}


def _init():
    _POOLS.update(dict(items_from_dir(os.path.join(HERE, "data", "tasks"))))


def one(line):
    row = json.loads(line)
    row["_np"] = [np.array(g, dtype=np.int8) for g in row["grids"]]
    key = row["task"]
    pool = _POOLS[key]
    rows = [row]
    m = len(pool)
    kw = dict(modules=None, frames=None, views={0})
    res = {}
    swap = 0
    for a in range(m):
        x, y = pool[a]
        task = {"test": [x], "test_out": [y]}
        C = build(rows, f"F{a}", **kw)
        o = full_outcome(task, C)
        top5 = top_of(C, "v5")
        ft = {b: top_of(build(rows, f"{a},{b}", **kw), "v5") for b in range(m) if b != a}
        r = faloo_role(None if top5 is None else top5[0], y, ft, {b: pool[b][1] for b in range(m) if b != a})
        o["a"], o["fa"], o["fc"], o["why"] = r["a"], r["fa"], r["fc"], r["why"]
        o["fold_h"] = {str(b): (None if p is None else [h(p[0]), h(p[1])]) for b, p in ft.items()}
        o["full_h"] = None if top5 is None else h(top5[0])
        res[str(a)] = o
    for a in range(m):
        for b in range(a + 1, m):
            p, q = res[str(a)]["fold_h"][str(b)], res[str(b)]["fold_h"][str(a)]
            # role a, fold b: [answer at x_b, answer at x_a]; role b, fold a: [answer at x_a, answer at x_b]
            if (p is None) != (q is None) or (p is not None and (p[0] != q[1] or p[1] != q[0])):
                swap += 1
    return dict(task=key, m=m, truth=[h(y) for _, y in pool], cfg={"full": res}, swap_diffs=swap)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(CACHE) as fh:
        lines = fh.readlines()
    print(len(lines), "cached items", flush=True)
    with mp.Pool(4, initializer=_init, maxtasksperchild=50) as p, open(OUT + ".tmp", "w") as fh:
        for n, r in enumerate(p.imap_unordered(one, lines, chunksize=1), 1):
            fh.write(json.dumps(r, separators=(",", ":"), default=float) + "\n")
            if n % 40 == 0 or n == len(lines):
                print(n, len(lines), flush=True)
    os.replace(OUT + ".tmp", OUT)


if __name__ == "__main__":
    main()
