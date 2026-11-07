"""Judge v8c pass 1: frozen Monty-ARC v5 in the named notebook's mode on the 120 ARC-AGI-2 public-evaluation tasks.
Re-implements the notebook's per-task cell (kaggle/tri/monty-arc-qwen-nvarc.ipynb, read only): one view (the default
perspectives=(0,)), all test inputs of a task together, a 120 s alarm, confident() then attempts_from() at 0.99, and
up to two guesses. Imports only the frozen arcmonty package; writes no file under arcmonty/ (run with -B).
    cd <root> && .venv/bin/python -B research/paper/v8_notes/scripts/v8c_monty_nb.py
Output: research/paper/v8_notes/v8c_monty_nb.json  {task: {"confident": [...per test], "guesses": [...per test]}}"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, os, signal, sys, time
from multiprocessing import Pool
import numpy as np
ROOT = _REPO
sys.path.insert(0, ROOT)
OUT = ROOT + "/research/paper/v8_notes/v8c_monty_nb.json"

def _alarm(*a):
    raise TimeoutError

def one(item):
    key, raw = item
    from arcmonty import monty_arc
    from arcmonty.vote import attempts_from, confident
    g = lambda x: np.array(x, dtype=np.int8)
    task = {"train": [(g(p["input"]), g(p["output"])) for p in raw["train"]], "test": [g(p["input"]) for p in raw["test"]]}
    signal.signal(signal.SIGALRM, _alarm); signal.alarm(120)
    t0 = time.time()
    try:
        cands = monty_arc.candidates(task)
        conf = confident(cands)
        best = attempts_from(task, cands)
        sure = attempts_from(task, cands, 0.99) if conf else [[] for _ in task["test"]]
        status = "ok"
    except Exception as e:
        best, sure, status = [], [], type(e).__name__
    finally:
        signal.alarm(0)
    return key, {"confident": [[a.tolist() for a in x[:1]] for x in sure],
                 "guesses": [[a.tolist() for a in x[:2]] for x in best], "status": status, "secs": round(time.time() - t0, 2)}

if __name__ == "__main__":
    ch = json.load(open(ROOT + "/data/kaggle_format/agi2_eval_challenges.json"))
    t0 = time.time()
    with Pool(6) as p:
        res = dict(p.imap_unordered(one, sorted(ch.items()), chunksize=1))
    json.dump(res, open(OUT, "w"))
    from collections import Counter
    print("tasks", len(res), Counter(v["status"] for v in res.values()), "wall %.0f s" % (time.time() - t0),
          "confident on", sum(any(v["confident"]) for v in res.values()))
