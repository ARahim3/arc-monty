"""Development only: run every step of the plan on development data, to test the code and give development numbers.
Games: the 12 tuning games, every arm. Static: development splits under the names of the plan's strata.
usage: python dry_run.py games | static | monty | library | analyse  -> dev/dry/"""
import json
import os
import random
import subprocess
import sys
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import data_sets as DS  # noqa: E402

ROOT = DS.ROOT
OUT = os.path.join(HERE, "dev", "dry")
DEV = {"arc-community": os.path.join(ROOT, "data/arc-agi-1/data/evaluation"),
       "tama": os.path.join(ROOT, "data/arc-agi-1/data/training")}
SAMPLE = 80


def dev_tasks(name):
    t = DS.load_tasks(DEV[name])
    keys = sorted(t)
    random.Random(7).shuffle(keys)
    return {k: t[k] for k in keys[:SAMPLE]}


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "games"), exist_ok=True)
    step = sys.argv[1]
    if step == "games":
        import games as G
        from settings import GAME_ARMS, WORKERS
        for arm in sys.argv[2:] or GAME_ARMS:
            p = os.path.join(OUT, "games", f"{arm}.json")
            if not os.path.exists(p):
                t0 = time.time()
                rows = G.run_named_arm(arm, G.named("tuning"), WORKERS)
                json.dump(rows, open(p, "w"))
                print(arm, G.summary(rows), round(time.time() - t0), "s", flush=True)
    elif step == "static":
        import static as S
        from settings import WORKERS
        for name in DEV:
            S.run_items(dev_tasks(name), os.path.join(OUT, f"static_{name}.jsonl"), WORKERS)
    elif step == "monty":
        import numpy as np  # noqa: F401
        from settings import WORKERS
        for name in DEV:
            tmp = os.path.join(OUT, f"_keys_{name}.json")
            json.dump(sorted(dev_tasks(name)), open(tmp, "w"))
            subprocess.run([sys.executable, "-B", os.path.join(HERE, "monty_fresh.py"), DEV[name], name, "--procs", str(WORKERS), "--out", OUT, "--keys", tmp], check=True)
    elif step == "analyse":
        import analyse as A
        from settings import GAME_ARMS
        import games as G
        clusters = {n: DS.SETS[n][1] for n in DS.SETS}
        out = dict(games=A.games_analysis(G.named("tuning"), GAME_ARMS, OUT))
        out["sets"] = {n: A.static_set([n], clusters, OUT)[0] for n in DEV}
        json.dump(A.jsonable(out), open(os.path.join(OUT, "analysis_dry.json"), "w"), indent=1, default=float)
        print(json.dumps({k: {f: v[f] for f in ("diff", "ci", "n") if f in v} for k, v in out["games"].items() if isinstance(v, dict) and "diff" in v}, indent=0))
        for n, r in out["sets"].items():
            print(n, {k: r[k] for k in ("items", "column_pass2", "monty_pass2", "S1 ratio", "S1 ratio ci", "S1 overlap", "S4 between tasks", "S4 within task", "held-out minus test, mean")})
            print({k: r[k]["line"] for k in r if k.startswith("rule ") and "line" in r[k]})
            print({k: v for k, v in r["monty"].items()})
