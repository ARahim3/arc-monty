"""SPIKE: do models persist usefully across static tasks? Development data only.

Library: every context from the demos of all 400 ARC-AGI-1 training tasks, with what followed it.
Test:    the 400 ARC-AGI-1 evaluation tasks, same-size only, same column.
  own   the column learns from this task's demos alone
  lib   the same, except that where its own evidence is weak (below 75% of the possible, fixed in advance),
        an exact match in the library answers instead
Outcome: tasks solved in each arm, and how many answers at leave-one-out 1.0 are right. No concept labels exist on
this data, so this is the general case, not the within-concept case the full experiment would use.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from arcmonty.data import load_split  # noqa: E402  (read-only: a task loader)

import column as C  # noqa: E402

SENSORS = ("color", "mask")
REACH = (2, 3)
TAU = 0.75
LIB = {}


def row_hash(W):
    h = np.zeros(W.shape[0], dtype=np.uint64)
    for j in range(W.shape[1]):
        h = C._mix(h, W[:, j])
    return h


def build_library():
    train = load_split("agi1-train")
    for kind in SENSORS:
        for R in REACH:
            lib = {}
            for t in train.values():
                for inp, out in t["train"]:
                    if inp.shape != out.shape:
                        continue
                    init = C.sensor(inp, kind)
                    U, tabs, _ = C.store(init, inp, out, R)
                    for h, tab in zip(row_hash(U).tolist(), tabs):
                        d = lib.setdefault(h, {})
                        for e, c in tab.items():
                            d[e] = d.get(e, 0) + c
            LIB[(kind, R)] = lib
    print("library", {k: len(v) for k, v in LIB.items()}, flush=True)


def predict(stored, g, init, R, lib):
    U = np.concatenate([s[0] for s in stored])
    T_ = [t for s in stored for t in s[1]]
    wt = stored[0][2]
    W, _ = C.windows(init, R)
    Q, inv = C._unique_rows(W)
    sim = np.zeros((len(Q), len(U)))
    for j in range(Q.shape[1]):
        sim += (Q[:, j][:, None] == U[:, j][None, :]) * wt[j]
    top = sim.max(axis=1)
    hs = row_hash(Q).tolist() if lib is not None else None
    enc = np.full(len(Q), -1, dtype=np.int32)
    used = 0
    for i in range(len(Q)):
        hits = [T_[s] for s in np.nonzero(sim[i] >= top[i] - 1e-9)[0].tolist()]
        c = C.choose(hits)
        if lib is not None and top[i] < TAU * wt.sum() and hs[i] in lib:
            c = C.choose([lib[hs[i]]])
            used += 1
        enc[i] = -1 if c is None else c
    return C.apply_encoding(g, enc[inv].reshape(g.shape)).astype(np.int8), used


def run(task, use_lib):
    pairs = task["train"]
    if not all(i.shape == o.shape for i, o in pairs):
        return []
    cands = []
    for kind in SENSORS:
        for R in REACH:
            lib = LIB[(kind, R)] if use_lib else None
            st = [C.store(C.sensor(i, kind), i, o, R) for i, o in pairs]
            loo = 0
            if len(pairs) > 1:
                for j, (i, o) in enumerate(pairs):
                    p, _ = predict(st[:j] + st[j + 1:], i, C.sensor(i, kind), R, lib)
                    loo += np.array_equal(p, o)
            preds, used = [], 0
            for t in task["test"]:
                p, u = predict(st, t, C.sensor(t, kind), R, lib)
                preds.append(p)
                used += u
            if all(np.array_equal(p, t) for p, t in zip(preds, task["test"])):
                continue
            cands.append(dict(ev=loo / len(pairs), preds=preds, used=used, h=f"{kind}/R{R}"))
    return cands


def score(task, cands):
    atts = [[] for _ in task["test"]]
    for c in sorted(cands, key=lambda c: -c["ev"]):
        for a, p in zip(atts, c["preds"]):
            if len(a) < 2 and not any(np.array_equal(p, q) for q in a):
                a.append(p)
    gold = task["test_out"]
    s = sum(any(np.array_equal(p, g) for p in a) for a, g in zip(atts, gold)) / len(gold)
    top = sorted(cands, key=lambda c: -c["ev"])[0] if cands else None
    ok = bool(top and all(np.array_equal(p, g) for p, g in zip(top["preds"], gold)))
    return s, (top["ev"] if top else None), ok


def work(item):
    name, task = item
    a = score(task, run(task, False))
    cl = run(task, True)
    b = score(task, cl)
    return dict(task=name, own=a[0], own_ev=a[1], own_ok=a[2], lib=b[0], lib_ev=b[1], lib_ok=b[2],
                lib_cells=sum(c["used"] for c in cl))


if __name__ == "__main__":
    t0 = time.time()
    build_library()
    tasks = load_split("agi1-eval")
    items = [(k, v) for k, v in tasks.items() if all(i.shape == o.shape for i, o in v["train"]) and
             max(i.size for i, _ in v["train"]) <= 400]
    print("tasks", len(items), flush=True)
    rows = [work(it) for it in items]  # one process: the library is a global, and macOS spawns workers
    own, lib = sum(r["own"] for r in rows), sum(r["lib"] for r in rows)
    gain = [r["task"] for r in rows if r["lib"] > r["own"]]
    loss = [r["task"] for r in rows if r["lib"] < r["own"]]
    conf = lambda p: (sum(bool(r[p + "_ev"] is not None and r[p + "_ev"] >= 0.99 and r[p + "_ok"]) for r in rows),
                      sum(bool(r[p + "_ev"] is not None and r[p + "_ev"] >= 0.99) for r in rows))
    out = dict(tasks=len(rows), own=own, lib=lib, gained=gain, lost=loss, conf_own=conf("own"), conf_lib=conf("lib"),
               median_cells_answered_by_library=float(np.median([r["lib_cells"] for r in rows])),
               wall=round(time.time() - t0, 1))
    json.dump(dict(summary=out, rows=rows), open(os.path.join(HERE, "results", "persist.json"), "w"))
    print(json.dumps(out, indent=1))
