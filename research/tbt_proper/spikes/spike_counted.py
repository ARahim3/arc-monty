"""SPIKE: the same column with counted evidence (Monty's form) instead of all-or-nothing contexts.
Development data only. Same-size tasks only. Writes results/counted_<split>.jsonl. Task order is seeded."""
import argparse
import glob
import json
import multiprocessing as mp
import os
import random
import signal
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from arcmonty.data import SPLITS, load_split  # noqa: E402  (read-only: a task loader)

import column as C  # noqa: E402

SENSORS = ("color", "mask", "objc", "obj", "objn", "near", "nearc", "nears", "nearsc")
REACH = (1, 2, 3, 5)
POSES = {"id": (0,), "d8": tuple(range(8))}


def frames_for(pairs):
    """Reference-frame hypotheses linking output cells to input cells: a generic resampling of the input."""
    fr = []
    if all(i.shape == o.shape for i, o in pairs):
        return [("same", lambda g: g)]
    rs = {(o.shape[0] / i.shape[0], o.shape[1] / i.shape[1]) for i, o in pairs}
    if len(rs) != 1:
        return []
    ry, rx = next(iter(rs))
    if ry >= 1 and rx >= 1 and ry == int(ry) and rx == int(rx):
        ry, rx = int(ry), int(rx)
        fr.append(("up", lambda g: np.repeat(np.repeat(g, ry, 0), rx, 1)))
        fr.append(("tile", lambda g: np.tile(g, (ry, rx))))
    if ry <= 1 and rx <= 1 and (1 / ry) == int(1 / ry) and (1 / rx) == int(1 / rx):
        ky, kx = int(1 / ry), int(1 / rx)
        fr.append(("down", lambda g: g[::ky, ::kx] if g.shape[0] % ky == 0 and g.shape[1] % kx == 0 else None))
    return fr


def run_task(task, sensors=SENSORS, poses_used=POSES, reach=REACH):
    res = []
    for name, f in frames_for(task["train"]):
        p2 = [(f(i), o) for i, o in task["train"]]
        t2 = [f(t) for t in task["test"]]
        if any(i is None or i.shape != o.shape for i, o in p2) or any(t is None for t in t2):
            continue
        for c in run_frame(p2, t2, sensors, poses_used, reach, name != "same"):
            c["h"] = name + "/" + c["h"]
            res.append(c)
    return res


def run_frame(pairs, test, sensors, poses_used, reach, allow_identity):
    task = dict(train=pairs, test=test)
    cache, cands = {}, []
    prev_id_loo = None

    def init(g, kind, k):
        key = (g.tobytes(), g.shape, kind, k)
        if key not in cache:
            cache[key] = C.sensor(C.d8(g, k), kind)
        return cache[key]

    for kind in sensors:
        if any(init(i, kind, 0) is None for i, _ in pairs):
            continue
        big = max(max(i.size for i, _ in pairs), max(t.size for t in task["test"])) > 225
        prev_loo = None
        for R in reach:
            if big and prev_loo == 0 and R == reach[-1]:  # speed only, on large grids; uses no test label
                continue
            st = [C.store(init(i, kind, 0), i, o, R) for i, o in pairs]
            for pname, poses in poses_used.items():
                if big and pname == "d8" and prev_id_loo == 0:  # speed only, on large grids; uses no test label
                    continue
                ins = lambda g: [init(g, kind, k) for k in poses]
                if any(x is None for t in task["test"] for x in ins(t)) or \
                        any(x is None for i, _ in pairs for x in ins(i)):
                    continue
                loo = 0
                if len(pairs) > 1:
                    for j, (i, o) in enumerate(pairs):
                        loo += np.array_equal(C.predict_counted(st[:j] + st[j + 1:], i, ins(i), poses, R), o)
                if pname == "id":
                    prev_id_loo = loo
                    prev_loo = loo
                preds = [C.predict_counted(st, t, ins(t), poses, R) for t in task["test"]]
                if not allow_identity and all(np.array_equal(p, t) for p, t in zip(preds, task["test"])):
                    continue  # in the same frame, predicting no change at all is not an answer
                cands.append(dict(h=f"{kind}/{pname}/R{R}", kind=kind, ev=loo / len(pairs), preds=preds))
    return cands



def attempts(task, cands):
    atts = [[] for _ in task["test"]]
    for c in sorted(cands, key=lambda c: -c["ev"]):
        for a, p in zip(atts, c["preds"]):
            if len(a) < 2 and not any(np.array_equal(p, q) for q in a):
                a.append(p)
    return atts


class _TO(Exception):
    pass


def _alarm(*_):
    raise _TO()


def work(args):
    name, task, sensors = args
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(90)
    t0 = time.time()
    row = dict(task=name, same_size=all(i.shape == o.shape for i, o in task["train"]))
    try:
        cands = run_task(task, sensors)
        gold = task["test_out"]
        scores = [any(np.array_equal(p, g) for p in a) for a, g in zip(attempts(task, cands), gold)]
        top = sorted(cands, key=lambda c: -c["ev"])[0] if cands else None
        ok = lambda c: all(np.array_equal(p, g) for p, g in zip(c["preds"], gold))
        row.update(n_cands=len(cands), score=sum(scores) / len(gold), best_ev=top["ev"] if top else None,
                   best_h=top["h"] if top else None, top_right=bool(top and ok(top)),
                   by_kind={k: sum(any(np.array_equal(p, g) for p in a) for a, g in zip(
                       attempts(task, [c for c in cands if c["kind"] == k]), gold)) / len(gold) for k in sensors},
                   sec=time.time() - t0)
    except _TO:
        row.update(n_cands=0, score=0.0, timeout=True, sec=time.time() - t0)
    finally:
        signal.alarm(0)
    return row


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("split")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sensors", default="", help="comma list; a fair ablation: still two attempts in all")
    a = ap.parse_args()
    assert a.split in ("agi1-train", "agi1-eval", "agi2-eval", "new233"), "development splits only"
    if a.split == "new233":
        ids = lambda p: {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(p, "*.json"))}
        keep = ids(SPLITS["agi2-train"]) - ids(SPLITS["agi1-train"]) - ids(SPLITS["agi1-eval"])
        tasks = {k: v for k, v in load_split("agi2-train").items() if k in keep}
    else:
        tasks = load_split(a.split)
    sensors = tuple(a.sensors.split(",")) if a.sensors else SENSORS
    items = [(k, v, sensors) for k, v in tasks.items()]
    random.Random(20261101).shuffle(items)
    if a.limit:
        items = items[:a.limit]
    suffix = "_" + "+".join(sensors) if a.sensors else ""
    out = os.path.join(HERE, "results", f"counted_{a.split}{suffix}.jsonl")
    t0 = time.time()
    with mp.Pool(a.workers) as pool, open(out, "w") as fh:
        rows = []
        for r in pool.imap_unordered(work, items, chunksize=2):
            rows.append(r)
            fh.write(json.dumps(r) + "\n")
            fh.flush()
    print(a.split, "n", len(rows), "same-size", sum(r["same_size"] for r in rows),
          "pass@2 sum", round(sum(r["score"] for r in rows), 2),
          "answered", sum(r.get("n_cands", 0) > 0 for r in rows),
          "timeouts", sum(bool(r.get("timeout")) for r in rows),
          "mean s", round(float(np.mean([r["sec"] for r in rows])), 2),
          "wall", round(time.time() - t0, 1))
