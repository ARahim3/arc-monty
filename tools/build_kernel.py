"""Build the self-contained Kaggle kernel for Monty-ARC: embeds arcmonty/*.py and a CPU driver."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES = ["__init__.py", "objects.py", "symmetry.py", "behavior.py", "dynamics.py", "composition.py", "association.py", "pattern.py", "periodic.py", "field.py", "vote.py", "monty_arc.py"]

DRIVER = r'''
import json, os, sys, time, signal, multiprocessing as mp
import numpy as np

PKG = os.environ.get("MONTY_PKG_DIR", "/kaggle/working/_pkg")
os.makedirs(os.path.join(PKG, "arcmonty"), exist_ok=True)
for name, src in SOURCES.items():
    with open(os.path.join(PKG, "arcmonty", name), "w") as fh:
        fh.write(src)
sys.path.insert(0, PKG)

def _find_challenges():
    if os.environ.get("ARC_CHALLENGES"):
        return os.environ["ARC_CHALLENGES"]
    import glob
    for d in ("/kaggle/input/competitions/arc-prize-2026-arc-agi-2", "/kaggle/input/arc-prize-2026-arc-agi-2"):
        for n in ("arc-agi_test_challenges.json", "arc-agi_test-challenges.json"):
            if os.path.exists(os.path.join(d, n)):
                return os.path.join(d, n)
    hits = sorted(glob.glob("/kaggle/input/**/*test*challenges*.json", recursive=True))
    if not hits:
        raise FileNotFoundError("no test challenges file under /kaggle/input")
    return hits[0]


CHALLENGES = _find_challenges()
OUT = os.environ.get("ARC_SUBMISSION", "/kaggle/working/submission.json")
PER_TASK_SECONDS = int(os.environ.get("ARC_TASK_SECONDS", "120"))


def _alarm(signum, frame):
    raise TimeoutError


def solve_one(item):
    key, raw = item
    from arcmonty import monty_arc
    g = lambda x: np.array(x, dtype=np.int8)
    task = {"train": [(g(p["input"]), g(p["output"])) for p in raw["train"]], "test": [g(p["input"]) for p in raw["test"]]}
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(PER_TASK_SECONDS)
    try:
        attempts = monty_arc.solve(task)
    except Exception:
        attempts = [[] for _ in task["test"]]
    finally:
        signal.alarm(0)
    out = []
    for t, a in zip(task["test"], attempts):
        a = [x.tolist() for x in a[:2]]
        while len(a) < 2:
            a.append(t.tolist())  # abstained: placeholder (never scored correct, keeps the format valid)
        out.append({"attempt_1": a[0], "attempt_2": a[1]})
    return key, out


if __name__ == "__main__":
    t0 = time.time()
    with open(CHALLENGES) as fh:
        challenges = json.load(fh)
    with mp.Pool(max(1, os.cpu_count() or 1)) as pool:
        results = dict(pool.map(solve_one, list(challenges.items()), chunksize=1))
    sub = {k: results.get(k) or [{"attempt_1": [[0]], "attempt_2": [[0]]} for _ in challenges[k]["test"]] for k in challenges}
    with open(OUT, "w") as fh:
        json.dump(sub, fh)
    print(f"wrote {OUT}: {len(sub)} tasks in {time.time() - t0:.0f}s")
'''


def main(out_path):
    sources = {}
    for m in MODULES:
        with open(os.path.join(ROOT, "arcmonty", m)) as fh:
            sources[m] = fh.read()
    header = '"""Monty-ARC: a Thousand-Brains-style solver for ARC-AGI-2 (CPU only, no training).\n\n' \
             'Learning modules: self-model (symmetry / self-similarity with evidence) and behavior (object-centric\n' \
             'change models with leave-one-out evidence), voted across the 8 D8 perspectives."""\n'
    with open(out_path, "w") as fh:
        fh.write(header)
        fh.write("SOURCES = " + repr(sources) + "\n")
        fh.write(DRIVER)
    print("built", out_path, os.path.getsize(out_path), "bytes")


if __name__ == "__main__":
    main(os.path.join(ROOT, "kaggle", "monty-arc", "monty_arc_kernel.py"))
