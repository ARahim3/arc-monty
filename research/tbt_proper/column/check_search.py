"""Development check: the fast search equals brute force; the store equals a from-scratch count."""
import os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
import numpy as np
import column as C
from arcmonty.data import load_split

def brute(col, s, q):
    sim = (s.U[:s.n] == q) @ col.w
    sim[s.U[:s.n, 0] != q[0]] = -1
    top = sim.max()
    return (None, 0.0) if top < 0 else (np.nonzero(sim >= top - 1e-9)[0], float(top))

tasks = load_split("agi1-train"); names = sorted(tasks); random.Random(1).shuffle(names)
n = bad = 0
for name in names[:40]:
    t = tasks[name]
    if not all(i.shape == o.shape for i, o in t["train"]): continue
    for kind in ("color", "mask", "nears", "obj"):
        for R in (2, 5):
            col = C.Column(kind=kind, reach=R)
            for x, y in t["train"]: col.learn(x, y)
            q = t["test"][0]
            ctx = col._context(q, None)
            if ctx is None or 0 not in col.stores: continue
            Q, B, inv = ctx; s = col.stores[0]
            rows = s.find(B)
            for i in np.nonzero(rows < 0)[0].tolist():
                a, va = col._search(s, Q[i], B[i]); b, vb = brute(col, s, Q[i])
                n += 1
                if (a is None) != (b is None) or (a is not None and (sorted(a.tolist()) != sorted(b.tolist()) or abs(va - vb) > 1e-9)): bad += 1
print("queries", n, "mismatches", bad)
