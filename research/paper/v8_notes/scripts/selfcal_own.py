"""v8 revision, post hoc: label-free estimate by rotating roles among the demonstrations only. Test input and test output are never used.
For a task with n >= 3 demonstrations and each demonstration a as "test": folds b != a train on demos minus {a, b} and answer queries {x_b, x_a};
full-data model trains on demos minus {a} and answers x_a. Rules: (a)+(b), and (a)+(b)+(c). Frozen arcmonty imported unchanged; at most 4 workers.
usage: selfcal_own.py TAG DIR > row file in ../selfcal/"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import glob, itertools, json, multiprocessing as mp, os, sys, time
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(v, "1")
ROOT = _REPO
sys.path.insert(0, ROOT)
import numpy as np
from arcmonty.data import _task
from arcmonty import behavior, monty_arc, symmetry, vote
def top(train, q):
    symmetry._CACHE.clear(); behavior._SEG_CACHE.clear()
    b = vote.pool(monty_arc.candidates({"train": train, "test": q}))
    return None if not b else b[0]["preds"]
def same(a, b):
    return a.shape == b.shape and bool(np.array_equal(a, b))
def one(item):
    k, D = item
    n = len(D); F = {}
    for a, b in itertools.combinations(range(n), 2):
        p = top([D[j] for j in range(n) if j not in (a, b)], [D[b][0], D[a][0]])
        F[(a, b)] = None if p is None else (p[0], p[1])
        F[(b, a)] = None if p is None else (p[1], p[0])
    roles = []
    for a in range(n):
        ok, T, E = True, [], True
        for b in range(n):
            if b == a:
                continue
            p = F[(a, b)]
            if p is None:
                ok = E = False
                continue
            if not same(p[0], D[b][1]):
                ok = E = False
            if same(p[1], D[a][1]):
                E = False
            T.append(p[1])
        agree = ok and len(T) == n - 1 and all(same(T[0], x) for x in T[1:])
        right = bool(agree and same(T[0], D[a][1]))
        c = False
        if agree:
            f = top([D[j] for j in range(n) if j != a], [D[a][0]])
            c = f is not None and same(f[0], T[0])
        roles.append(dict(a=bool(ok), ab=bool(agree), abc=bool(c), right=right, E=bool(E)))
    return dict(task=k, n=n, roles=roles)
if __name__ == "__main__":
    tag, path = sys.argv[1], os.path.join(ROOT, sys.argv[2])
    items = []
    for f in sorted(glob.glob(os.path.join(path, "**", "*.json"), recursive=True)):
        try:
            t = _task(json.load(open(f)))
        except Exception:
            continue
        if t["test_out"] and len(t["train"]) >= 3:
            items.append((os.path.relpath(f, path)[:-5], t["train"]))
    os.makedirs(os.path.join(ROOT, "research/paper/v8_notes/selfcal"), exist_ok=True)
    t0 = time.time()
    with mp.Pool(4, maxtasksperchild=40) as p, open(os.path.join(ROOT, f"research/paper/v8_notes/selfcal/{tag}.jsonl"), "w") as fh:
        for r in p.imap_unordered(one, items, chunksize=1):
            fh.write(json.dumps(r) + "\n")
    print(tag, len(items), "tasks", round(time.time() - t0), "s", flush=True)
