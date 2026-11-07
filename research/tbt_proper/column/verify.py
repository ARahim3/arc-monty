"""Checks after the runs, read-only on frozen code: (1) frozen hash; (2) an independent re-score of a random sample of items from raw JSON,
in a fresh process; (3) one held-out game re-run, row by row; (4) how many items are trivial for a memory: test input equals a demo input.
usage: python -I -B verify.py -> results/verify.json"""
import json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import column as C, data_sets as DS, freeze, games as G, static as S
from settings import CONFIGS, SET_ORDER
RES = os.path.join(HERE, "results")
out = dict(frozen=freeze.check()["code_sha256"])
rng = random.Random(20261102)
out["rescore"] = {}
for name in SET_ORDER:
    rows = {json.loads(l)["task"]: json.loads(l) for l in open(os.path.join(RES, f"static_{name}.jsonl"))}
    tasks = DS.load_tasks(name)
    keys = sorted(tasks)
    rng.shuffle(keys)
    agree = n = 0
    for k in keys[:12]:
        t = tasks[k]
        cands = C.hold_out(CONFIGS, t["train"], t["test"])
        for i, gold in enumerate(t["test_out"]):
            seen = []
            for c in cands:
                if c["usable"][i] and not any(np.array_equal(c["preds"][i], q) for q in seen):
                    seen.append(c["preds"][i])
                if len(seen) == 2:
                    break
            mine = float(any(np.array_equal(p, gold) for p in seen))
            n += 1
            agree += mine == S.pass2(rows[f"{k}#{i}"], set(range(len(CONFIGS))))
    out["rescore"][name] = f"{agree}/{n}"
    print(name, out["rescore"][name], flush=True)
    both = dup = solved_dup = 0
    for k, t in tasks.items():
        for i, x in enumerate(t["test"]):
            if any(np.array_equal(x, a) for a, _ in t["train"]):
                dup += 1
                solved_dup += S.pass2(rows[f"{k}#{i}"], set(range(len(CONFIGS))))
    out.setdefault("test_input_equals_a_demo_input", {})[name] = dict(items=dup, column_solves=solved_dup, of=len(rows))
g = G.named("heldout")[0]
fresh = G.run_game(g, [dict(kind="color", reach=6)])
old = [r for r in json.load(open(os.path.join(RES, "games", "single.json"))) if r["game"] == g]
out["game_rerun"] = dict(game=g, rows=len(fresh), same=sum(a == b for a, b in zip(fresh, old)))
json.dump(out, open(os.path.join(RES, "verify.json"), "w"), indent=1)
print(json.dumps(out, indent=0))
