"""Development only: the one column on static development splits. Refuses any other data."""
import argparse, glob, json, multiprocessing as mp, os, random, signal, sys, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
import numpy as np
from arcmonty.data import SPLITS, load_split
import column as C

def split_tasks(name):
    if name == "new233":
        ids = lambda p: {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(p, "*.json"))}
        keep = ids(SPLITS["agi2-train"]) - ids(SPLITS["agi1-train"]) - ids(SPLITS["agi1-eval"])
        return {k: v for k, v in load_split("agi2-train").items() if k in keep}
    return load_split(name)

def attempts(cands, n_tests, k=2):
    atts = [[] for _ in range(n_tests)]
    for c in cands:
        for t in range(n_tests):
            p = c["preds"][t]
            if c["usable"][t] and len(atts[t]) < k and not any(np.array_equal(p, q) for q in atts[t]):
                atts[t].append(p)
    return atts

class _TO(Exception): pass
def _alarm(*_): raise _TO()

CFG = None
def _init(cfg):
    global CFG
    CFG = cfg

def work(item):
    name, t = item
    signal.signal(signal.SIGALRM, _alarm); signal.alarm(CFG["timeout"])
    t0 = time.time()
    row = dict(task=name, n=len(t["train"]))
    try:
        cands = C.hold_out(CFG["configs"], t["train"], t["test"], **CFG["common"])
        gold = t["test_out"]
        atts = attempts(cands, len(gold))
        row["score"] = sum(any(np.array_equal(p, g) for p in a) for a, g in zip(atts, gold)) / len(gold)
        top = next((c for c in cands if all(c["usable"])), None)
        row["ev"] = None if top is None else top["ev"]
        row["top_ok"] = bool(top and all(np.array_equal(p, g) for p, g in zip(top["preds"], gold)))
        row["top"] = None if top is None else (top["cfg"]["kind"] + "/R" + str(top["cfg"]["reach"]) + "/p" + str(top["cfg"].get("poses", 1)) + "/" + str(top["frame"]))
        row["ncand"] = len(cands)
    except _TO:
        row.update(score=0.0, ev=None, top_ok=False, top=None, ncand=0, timeout=True)
    finally:
        signal.alarm(0)
    row["sec"] = round(time.time() - t0, 2)
    return row

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("split"); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--sensors", default="color,mask,objc,obj,objn,near,nearc,nears,nearsc")
    ap.add_argument("--reach", default="1,2,3,5"); ap.add_argument("--timeout", type=int, default=120); ap.add_argument("--tag", default=""); ap.add_argument("--poses", type=int, default=1); ap.add_argument("--d8", default=""); ap.add_argument("--d8reach", default="")
    a = ap.parse_args()
    assert a.split in ("agi1-train", "agi1-eval", "agi2-eval", "new233"), "development splits only"
    tasks = split_tasks(a.split)
    items = list(tasks.items()); random.Random(20261101).shuffle(items)
    if a.limit: items = items[:a.limit]
    configs = [dict(kind=s, reach=int(r)) for s in a.sensors.split(",") for r in a.reach.split(",")]
    if a.d8:
        configs += [dict(kind=s, reach=int(r), poses=8) for s in a.d8.split(",") for r in (a.d8reach or a.reach).split(",")]
    cfg = dict(configs=configs, timeout=a.timeout, common=dict(poses=a.poses) if a.poses > 1 else {})
    t0 = time.time(); rows = []
    with mp.Pool(a.workers, initializer=_init, initargs=(cfg,)) as pool:
        for r in pool.imap_unordered(work, items, chunksize=2): rows.append(r)
    os.makedirs(os.path.join(HERE, "dev"), exist_ok=True)
    out = os.path.join(HERE, "dev", f"static_{a.split}{'_' + a.tag if a.tag else ''}.jsonl")
    with open(out, "w") as fh:
        for r in rows: fh.write(json.dumps(r) + "\n")
    conf = [r for r in rows if r["ev"] is not None and r["ev"] >= 0.99]
    print(a.split, a.tag, "n", len(rows), "pass@2", round(sum(r["score"] for r in rows), 2), "conf", sum(r["top_ok"] for r in conf), "/", len(conf),
          "answered", sum(r["ncand"] > 0 for r in rows), "timeouts", sum(bool(r.get("timeout")) for r in rows), "mean s", round(float(np.mean([r["sec"] for r in rows])), 2),
          "max s", max(r["sec"] for r in rows), "wall", round(time.time() - t0, 1))
