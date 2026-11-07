"""Development check of the Monty wrapper: monty_fresh.run on development tasks with one test pair, against the rows
research/monty_heldout/results/dev_base.jsonl recorded earlier (same frozen code). Single process. usage: python -I -B dev_wrappers.py [N]"""
import json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import monty_fresh as M
from arcmonty.data import load_split
ROOT = M.ROOT
rows = {}
for line in open(os.path.join(ROOT, "research/monty_heldout/results/dev_base.jsonl")):
    r = json.loads(line)
    rows[(r["split"], r["task"])] = r["cfg"]["full"]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
tasks = load_split("agi1-eval")
keys = sorted(k for k in tasks if ("agi1-eval", k) in rows and len(tasks[k]["test"]) == 1)
random.Random(3).shuffle(keys)
bad = n = 0
for k in keys[:N]:
    t = tasks[k]
    got = M.run((k + "#0", list(t["train"]) + [(t["test"][0], t["test_out"][0])]))["cfg"]["full"][str(len(t["train"]))]
    want = rows[("agi1-eval", k)]
    for f in ("p2", "top_ok", "v5", "fit", "a", "fa", "fc", "top_ev"):
        n += 1
        if got.get(f) != want.get(f) and not (isinstance(want.get(f), float) and isinstance(got.get(f), (int, float)) and abs(want[f] - got[f]) < 1e-3):
            bad += 1
            print("differs", k, f, got.get(f), want.get(f), flush=True)
print("fields compared", n, "differ", bad, "tasks", min(N, len(keys)))
