"""Final pass, own code: direct run of frozen arcmonty on the unseen sets, real role only.
Per fold: top answer on [x_i, x_test]; same with queries swapped; same with demonstrations reversed. Premise (S) on the unseen sets.
Also records h, t per fold for the fold-level split. Imports arcmonty read-only; writes no bytecode. 3 workers."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import os, sys, json, glob, time
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[v] = "1"
sys.dont_write_bytecode = True
ROOT = _REPO
sys.path.insert(0, ROOT)
import numpy as np
import multiprocessing as mp
from arcmonty import monty_arc, vote, symmetry, behavior
SETS = {"concept": "external/judge/conceptarc/repo/corpus", "mini": "external/heldout/mini-arc/data/MiniARC",
        "oned": "external/heldout/1d-arc/dataset", "minimal": "external/judge/conceptarc/repo/MinimalTasks"}
A = lambda x: np.array(x, dtype=np.int8)
def items(tag):
    base = os.path.join(ROOT, SETS[tag]); out = []
    for f in sorted(glob.glob(base + "/**/*.json", recursive=True)):
        try:
            raw = json.load(open(f))
            tr = [(A(p["input"]), A(p["output"])) for p in raw["train"]]
            te = [(A(p["input"]), A(p["output"])) for p in raw["test"] if "output" in p]
        except Exception:
            continue
        k = os.path.relpath(f, base)[:-5]
        for ti, (x, y) in enumerate(te):
            out.append((f"{k}#{ti}", tr, x, y))
    return out
def top(train, queries):
    symmetry._CACHE.clear(); behavior._SEG_CACHE.clear()
    C = monty_arc.candidates({"train": train, "test": queries}, perspectives=(0,))
    if not C: return None
    b = vote.pool(C)
    return b[0]["preds"] if b else None
def eq(a, b): return a is not None and b is not None and np.array_equal(a, b)
def one(arg):
    key, tr, x, y = arg
    n = len(tr); folds = []
    for i in range(n):
        S = [tr[j] for j in range(n) if j != i]
        xi, yi = tr[i]
        p = top(S, [xi, x]); q = top(S, [x, xi]); r = top(S[::-1], [xi, x])
        none = (p is None, q is None, r is None)
        sq = (p is None and q is None) or (p is not None and q is not None and eq(p[0], q[1]) and eq(p[1], q[0]))
        sd = (p is None and r is None) or (p is not None and r is not None and eq(p[0], r[0]) and eq(p[1], r[1]))
        folds.append(dict(i=i, has=p is not None, h=int(p is not None and eq(p[0], yi)), t=int(p is not None and eq(p[1], y)), sq=bool(sq), sd=bool(sd)))
    return dict(key=key, n=n, folds=folds)
if __name__ == "__main__":
    out_dir = sys.argv[1]
    for tag in sys.argv[2:]:
        it = items(tag)
        path = f"{out_dir}/s_{tag}.jsonl"
        done = set()
        if os.path.exists(path):
            done = {json.loads(l)["key"] for l in open(path)}
        todo = [a for a in it if a[0] not in done]
        print(tag, len(it), "todo", len(todo), time.strftime("%H:%M:%S"), flush=True)
        with mp.Pool(3) as pool, open(path, "a") as fh:
            for r in pool.imap_unordered(one, todo, chunksize=2):
                fh.write(json.dumps(r) + "\n"); fh.flush()
        print(tag, "done", time.strftime("%H:%M:%S"), flush=True)
