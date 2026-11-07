"""The population on static tasks, one item per test pair. Every column's answers are kept, for the full demos and for each
fold, so every arm and rule is computed offline from one run (arms are subsets of columns, ranks do not change).

Row per item: full = [[column, frame, evidence, answer hash or None, right, fits all demos]...] in rank order;
folds = {b: [[column, frame, evidence, test hash or None, right on test, predicts held-out demo]...]} in rank order.
A task with one demonstration has no usable fold.
"""
import hashlib
import json
import multiprocessing as mp
import os
import signal
import sys
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import column as C  # noqa: E402
from settings import BUDGET, CONFIGS  # noqa: E402


def gh(a):
    a = np.ascontiguousarray(a).astype(np.int8)
    return hashlib.md5(str(a.shape).encode() + a.tobytes()).hexdigest()[:10]


class _TO(Exception):
    pass


def _alarm(*_):
    raise _TO()


def run_task(name, demos, tests, golds, folds=True, library=None, budget=BUDGET):
    """All test pairs of one task. tests, golds: lists. Returns one row per test pair."""
    t0 = time.time()
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(budget)
    rows = [dict(task=f"{name}#{i}", m=len(demos) + 1, n=len(demos), full=[], folds={}) for i in range(len(tests))]
    try:
        memo = {}
        cands = C.hold_out(CONFIGS, demos, tests, memo=memo, library=library)
        for c in cands:
            fits = all(p is not None and np.array_equal(p, y) for p, y in ((c["col"].predict(x), y) for x, y in demos))
            for i, g in enumerate(golds):
                p = c["preds"][i]
                ok = c["usable"][i]
                rows[i]["full"].append([c["index"], str(c["frame"]), round(c["ev"], 4), gh(p) if ok else None,
                                        bool(ok and np.array_equal(p, g)), fits])
        if folds and len(demos) > 1:
            for b, (xb, yb) in enumerate(demos):
                rest = demos[:b] + demos[b + 1:]
                fc = C.hold_out(CONFIGS, rest, list(tests) + [xb], memo=memo)
                for c in fc:
                    pb, okb = c["preds"][-1], c["usable"][-1]
                    held = bool(okb and np.array_equal(pb, yb))
                    for i, g in enumerate(golds):
                        p, ok = c["preds"][i], c["usable"][i]
                        rows[i]["folds"].setdefault(str(b), []).append(
                            [c["index"], str(c["frame"]), round(c["ev"], 4), gh(p) if ok else None,
                             bool(ok and np.array_equal(p, g)), held])
    except _TO:
        for r in rows:
            r.update(full=[], folds={}, timeout=True)
    except Exception as e:  # a crash counts as no answer, and is reported
        for r in rows:
            r.update(full=[], folds={}, error=repr(e)[:200])
    finally:
        signal.alarm(0)
    for r in rows:
        r["sec"] = round((time.time() - t0) / len(rows), 2)
    return rows


def _work(item):
    return run_task(*item)


def run_items(tasks, out, workers=4, chunk=1):
    """tasks: dict name -> task (train, test, test_out). Resumable: finished tasks in `out` are skipped."""
    done = set()
    if os.path.exists(out):
        for line in open(out):
            try:
                done.add(json.loads(line)["task"].split("#")[0])
            except Exception:
                pass
    todo = [(k, t["train"], t["test"], t["test_out"]) for k, t in tasks.items() if k not in done and t["test_out"]]
    t0 = time.time()
    with mp.Pool(workers, maxtasksperchild=20) as pool, open(out, "a") as fh:
        for n, rows in enumerate(pool.imap_unordered(_work, todo, chunksize=chunk), 1):
            for r in rows:
                fh.write(json.dumps(r, separators=(",", ":")) + "\n")
            fh.flush()
            if n % 100 == 0 or n == len(todo):
                print(os.path.basename(out), n, "/", len(todo), round(time.time() - t0), "s", flush=True)


# ------------------------------------------------------------------ offline rules on one row; `keep` = allowed column indices
def _top(cands, keep):
    return next((c for c in cands if c[0] in keep and c[3] is not None), None)


def pass2(row, keep):
    seen, ok = [], False
    for c in row["full"]:
        if c[0] in keep and c[3] is not None and c[3] not in seen:
            seen.append(c[3])
            ok = ok or c[4]
            if len(seen) == 2:
                break
    return float(ok)


def rules(row, keep):
    """Everything S4 needs for one item under one arm."""
    top = _top(row["full"], keep)
    out = dict(pass2=pass2(row, keep), top_right=None if top is None else bool(top[4]), top_ev=None if top is None else top[2],
               fit=None if top is None or not top[5] else bool(top[4]))
    folds = {b: _top(v, keep) for b, v in row["folds"].items()}
    out["fold_programs"] = [[bool(c[5]), bool(c[4])] for c in folds.values() if c is not None]
    n = row["n"]
    if n < 2 or len(folds) < n or top is None or any(c is None for c in folds.values()):
        out["a"] = out["fa"] = out["fc"] = None
        return out
    a_ok = all(c[5] for c in folds.values())
    answers = {c[3] for c in folds.values()}
    right = next(iter(folds.values()))[4]
    out["a"] = bool(top[4]) if a_ok else None
    out["fa"] = bool(right) if a_ok and len(answers) == 1 else None
    out["fc"] = bool(right) if a_ok and len(answers) == 1 and top[3] in answers else None
    return out


# ------------------------------------------------------------------ persisting models: E2, one set with concept groups
def library_for(tasks):
    """The same columns, kept across tasks: every labelled same-size pair of these tasks, demos and test pairs."""
    cols = [C.Column(**c) for c in CONFIGS]
    for t in tasks:
        for x, y in list(t["train"]) + list(zip(t["test"], t["test_out"])):
            if x.shape == y.shape:
                for c in cols:
                    c.learn(x, y)
    return cols


def _work_library(item):
    name, t, others = item
    return run_task(name, t["train"], t["test"], t["test_out"], folds=False, library=library_for(others))


def run_library(tasks, chooser, out, workers=4):
    """tasks: dict key -> task. chooser(key) -> keys of the library's tasks. Resumable."""
    done = set()
    if os.path.exists(out):
        done = {json.loads(line)["task"].split("#")[0] for line in open(out)}
    todo = [(k, t, [tasks[o] for o in chooser(k)]) for k, t in tasks.items() if k not in done]
    t0 = time.time()
    with mp.Pool(workers, maxtasksperchild=10) as pool, open(out, "a") as fh:
        for n, rows in enumerate(pool.imap_unordered(_work_library, todo, chunksize=1), 1):
            for r in rows:
                fh.write(json.dumps(r, separators=(",", ":")) + "\n")
            fh.flush()
            if n % 40 == 0 or n == len(todo):
                print(os.path.basename(out), n, "/", len(todo), round(time.time() - t0), "s", flush=True)
