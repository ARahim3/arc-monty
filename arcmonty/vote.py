"""Voting across learning modules: identical predictions pool their evidence; the two attempts are the
strongest hypothesis and the strongest one that disagrees with it (Monty's hypothesis-testing policy)."""
import numpy as np

CONFIDENT = 0.99


def pool(cands):
    """Merge candidates with identical predictions; evidence adds (capped), voters are recorded."""
    pooled = []
    for c in cands:
        for p in pooled:
            if len(p["preds"]) == len(c["preds"]) and all(np.array_equal(a, b) for a, b in zip(p["preds"], c["preds"])):
                p["evidence"] = max(p["evidence"], c["evidence"]) + 0.01 * min(p["evidence"], c["evidence"])
                p["voters"].add(c["lm"])
                break
        else:
            pooled.append(dict(c, voters={c["lm"]}))
    pooled.sort(key=lambda p: (-int(p["evidence"] >= CONFIDENT), -len(p["voters"]), -float(p["evidence"])))
    return pooled


def attempts_from(task, cands, min_evidence=0.0):
    attempts = [[] for _ in task["test"]]
    for p in pool(cands):
        if p["evidence"] < min_evidence:
            break
        for a, g in zip(attempts, p["preds"]):
            if len(a) < 2 and not any(np.array_equal(g, q) for q in a):
                a.append(g)
    return attempts


def confident(cands):
    """Consensus rule: the best fully-evidenced answer must out-vote every conflicting fully-evidenced answer
    by at least 2:1 (votes = distinct module@perspective columns producing it)."""
    best = pool(cands)
    strong = [p for p in best if p["evidence"] >= CONFIDENT]
    if not strong:
        return False
    strong.sort(key=lambda p: -len(p["voters"]))
    return len(strong) == 1 or len(strong[0]["voters"]) >= 2 * len(strong[1]["voters"])
