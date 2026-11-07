"""Run everything fixed in the plan, in the plan's order. Opens test data only if the frozen hashes match; resumable.
usage: python -I -B run_all.py [games|static|monty|library] ... (default: all). At most 4 workers."""
import json
import os
import random
import subprocess
import sys
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import freeze  # noqa: E402
import data_sets as DS  # noqa: E402
import games as G  # noqa: E402
import static as S  # noqa: E402
from settings import E2_LIBRARY_SIZE, GAME_ARMS, SET_ORDER, WORKERS  # noqa: E402

RES = os.path.join(HERE, "results")


def run_games():
    os.makedirs(os.path.join(RES, "games"), exist_ok=True)
    names = G.named("heldout")
    for arm in GAME_ARMS:
        out = os.path.join(RES, "games", f"{arm}.json")
        if os.path.exists(out):
            continue
        t0 = time.time()
        rows = G.run_named_arm(arm, names, WORKERS)
        json.dump(rows, open(out, "w"))
        print("games", arm, G.summary(rows), round(time.time() - t0), "s", flush=True)


def run_static():
    for name in SET_ORDER:
        S.run_items(DS.load_tasks(name), os.path.join(RES, f"static_{name}.jsonl"), WORKERS)


def run_monty():
    for name in SET_ORDER:
        if DS.SETS[name][2].startswith("fresh"):
            subprocess.run([sys.executable, "-I", "-B", os.path.join(HERE, "monty_fresh.py"), name, name, "--procs", str(WORKERS)], check=True)


def run_library():
    tasks = DS.load_tasks("concept")
    groups = {}
    for k in tasks:
        groups.setdefault(k.split("/")[0], []).append(k)

    def same(k):
        return [o for o in groups[k.split("/")[0]] if o != k]

    def other(k):
        pool = sorted(o for o in tasks if o.split("/")[0] != k.split("/")[0])
        return random.Random(zlib.crc32(k.encode())).sample(pool, E2_LIBRARY_SIZE)

    S.run_library(tasks, same, os.path.join(RES, "library_same.jsonl"), WORKERS)
    S.run_library(tasks, other, os.path.join(RES, "library_other.jsonl"), WORKERS)


if __name__ == "__main__":
    rec = freeze.check()
    print("frozen code verified", rec["code_sha256"][:16], "frozen at", rec["frozen_at_utc"], flush=True)
    os.makedirs(RES, exist_ok=True)
    steps = dict(games=run_games, static=run_static, monty=run_monty, library=run_library)
    for s in sys.argv[1:] or list(steps):
        t0 = time.time()
        steps[s]()
        print("step", s, "done", round(time.time() - t0), "s", flush=True)
