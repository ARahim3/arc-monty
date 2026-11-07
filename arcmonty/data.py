"""Load ARC tasks (GitHub per-task JSON folders or Kaggle challenges/solutions files) as numpy grids."""
import glob
import json
import os

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SPLITS = {
    "agi2-train": os.path.join(ROOT, "arc-agi-2/data/training"),
    "agi2-eval": os.path.join(ROOT, "arc-agi-2/data/evaluation"),
    "agi1-train": os.path.join(ROOT, "arc-agi-1/data/training"),
    "agi1-eval": os.path.join(ROOT, "arc-agi-1/data/evaluation"),
}


def _task(raw):
    g = lambda x: np.array(x, dtype=np.int8)
    return {
        "train": [(g(p["input"]), g(p["output"])) for p in raw["train"]],
        "test": [g(p["input"]) for p in raw["test"]],
        "test_out": [g(p["output"]) for p in raw["test"] if "output" in p],
    }


def load_split(name):
    tasks = {}
    for f in sorted(glob.glob(os.path.join(SPLITS[name], "*.json"))):
        with open(f) as fh:
            tasks[os.path.basename(f)[:-5]] = _task(json.load(fh))
    return tasks


def load_kaggle(challenges_path, solutions_path=None):
    with open(challenges_path) as fh:
        ch = json.load(fh)
    sol = {}
    if solutions_path and os.path.exists(solutions_path):
        with open(solutions_path) as fh:
            sol = json.load(fh)
    tasks = {}
    for k, raw in ch.items():
        t = _task(raw)
        if k in sol:
            t["test_out"] = [np.array(o, dtype=np.int8) for o in sol[k]]
        tasks[k] = t
    return tasks


def show(grid):
    return "\n".join("".join(".123456789"[v] if v else "." for v in row) for row in grid)
