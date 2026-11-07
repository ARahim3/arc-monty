"""Pass@2 scoring (the Kaggle metric): a test output counts if either attempt matches exactly."""
import time

import numpy as np


def score_task(task, attempts):
    """attempts: list (one per test input) of lists of up to 2 grids. Returns fraction of test outputs solved."""
    hits = 0
    for i, truth in enumerate(task["test_out"]):
        cands = attempts[i] if i < len(attempts) else []
        hits += any(c is not None and np.array_equal(np.asarray(c), truth) for c in cands[:2])
    return hits / max(1, len(task["test_out"]))


def run(solver, tasks, verbose=False):
    t0 = time.time()
    per_task = {}
    for k, task in tasks.items():
        try:
            attempts = solver(task)
        except Exception as e:  # a solver bug on one task must not kill the run
            if verbose:
                print(k, "ERROR", repr(e))
            attempts = []
        per_task[k] = score_task(task, attempts)
        if verbose and per_task[k] > 0:
            print(f"solved {k} ({per_task[k]:.2f})")
    total = sum(per_task.values())
    print(f"score {total:.2f}/{len(tasks)} = {100 * total / len(tasks):.2f}%  ({time.time() - t0:.1f}s)")
    return per_task
