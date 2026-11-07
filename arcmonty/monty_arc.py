"""Monty-ARC: run every learning module under every D8 perspective of the task, vote, answer (or abstain)."""
import numpy as np

from arcmonty import association, behavior, composition, dynamics, field, pattern, periodic, symmetry
from arcmonty.objects import d8
from arcmonty.vote import attempts_from, confident

MODULES = (symmetry, periodic, behavior, dynamics, composition, association, pattern, field)
_INV = {0: 0, 1: 3, 2: 2, 3: 1, 4: 4, 5: 5, 6: 6, 7: 7}  # d8(d8(a, k), _INV[k]) == a


def _view(task, k):
    return {
        "train": [(d8(i, k), d8(o, k)) for i, o in task["train"]],
        "test": [d8(t, k) for t in task["test"]],
    }


def candidates(task, perspectives=(0,)):
    """Every module already enumerates D8 pose hypotheses internally, so by default the task is seen from its own
    frame only; extra whole-task D8 perspectives multiply compute and inflate false confidence (measured)."""
    out = []
    for k in perspectives:
        view = task if k == 0 else _view(task, k)
        for m in MODULES:
            try:
                cands = m.candidates(view)
            except Exception:  # one module failing must not silence the others
                continue
            for c in cands:
                preds = [np.ascontiguousarray(d8(p, _INV[k])) for p in c["preds"]]
                out.append(dict(c, preds=preds, lm=f"{c['lm']}@{k}"))
    return out


def solve(task):
    return attempts_from(task, candidates(task))


def solve_confident(task):
    """High-precision mode for merging with a neural solver: answer only on a fully evidenced consensus."""
    cands = candidates(task)
    if not confident(cands):
        return [[] for _ in task["test"]]
    return attempts_from(task, cands, min_evidence=0.99)
