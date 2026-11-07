"""generator_control: frozen Monty-ARC v5 on the re-arc tasks, every role and fold, one view. A wrapper only: the worker is
research/monty_heldout/run_cache.py `run`, unchanged, and arcmonty/ is imported unchanged. Resumable.
    nice -n 15 .venv/bin/python -I -B research/generator_control/monty/run_monty.py [--procs 4]
Writes monty/cache/rearc_p0.jsonl (one line per item), in the format of run_cache.py."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))  # repo root
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

ROOT = _REPO
HERE = os.path.join(ROOT, "research", "generator_control")
sys.path.insert(0, os.path.join(ROOT, "research", "monty_heldout"))
import run_cache as RC  # noqa: E402
from hl_common import items_from_dir, read_done  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    assert a.procs <= 4
    path = os.path.join(HERE, "monty", "cache", "rearc_p0.jsonl")
    done = read_done(path)
    items = items_from_dir(os.path.join(HERE, "data", "tasks"))
    assert len(items) == 200 and all(len(p) == 4 for _, p in items)
    todo = [x for x in items if x[0] not in done]
    todo.sort(key=lambda x: len(x[1]) ** 2 * max(i.size for i, _ in x[1]))
    print(path, len(items), "items", len(done), "done", len(todo), "todo", flush=True)
    t0 = time.time()
    if not todo:
        return
    with mp.Pool(a.procs, initializer=RC._init, initargs=((0,), None), maxtasksperchild=30) as pool, open(path, "a") as fh:
        for n, r in enumerate(pool.imap_unordered(RC.run, todo, chunksize=1), 1):
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
            fh.flush()
            print(n, len(todo), r["task"], r["cpu"], round(time.time() - t0), flush=True)
    print("finished", round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
