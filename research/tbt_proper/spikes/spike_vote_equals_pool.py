"""SPIKE: on exact data, Monty-style voting ends where pooling ends, and a full view ends the race on step one.

Objects come from ARC-AGI-1 training input grids (development data). Each object is a model. The system must say which
model it is sensing and at which pose/offset. Hypothesis = (model, D8 pose, translation). A column senses one cell per
step through its own patch; a vote passes a column's surviving hypotheses to the others; the shared frame makes the
displacement correction a no-op, as in Monty's vote (a hypothesis names the same object placement for every column).

Checks:
 A. After every step, the intersection of N columns' surviving hypotheses == the set one column would hold if it had
    received all N columns' observations directly (pooling). Asserted on every trial.
 B. Cells read until one placement survives, by policy: random walk, hypothesis-testing (read where the top two
    surviving hypotheses disagree), with 1, 2, 4, 8 sensors. A full view costs one step and reads every cell.
Output: results/vote_equals_pool.json
"""
import json
import os
import random
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from arcmonty.data import load_split  # noqa: E402  (read-only: a task loader)

import column as C  # noqa: E402


def models_from(grid):
    res = []
    for m in C.objects(grid):
        ys, xs = np.nonzero(m)
        if m.sum() < 3:
            continue
        p = np.where(m[ys.min():ys.max() + 1, xs.min():xs.max() + 1], grid[ys.min():ys.max() + 1, xs.min():xs.max() + 1], -1)
        res.append(p.astype(np.int8))
    return res


def hypotheses(models, grid_shape):
    H = []
    h, w = grid_shape
    for mi, m in enumerate(models):
        seen = set()
        for k in range(8):
            t = C.d8(m, k)
            enc = (t.shape, t.tobytes())
            if enc in seen:
                continue
            seen.add(enc)
            for dy in range(h - t.shape[0] + 1):
                for dx in range(w - t.shape[1] + 1):
                    H.append((mi, k, dy, dx))
    return H


def stack_predictions(H, models, shape, bg):
    """Predicted grid for every hypothesis: the model placed on background."""
    P = np.full((len(H), *shape), bg, dtype=np.int8)
    cache = {}
    for i, (mi, k, dy, dx) in enumerate(H):
        t = cache.setdefault((mi, k), C.d8(models[mi], k))
        v = P[i, dy:dy + t.shape[0], dx:dx + t.shape[1]]
        v[t >= 0] = t[t >= 0]
    return P


def trial(models, shape, bg, n_sensors, policy, rng):
    H = hypotheses(models, shape)
    if not 2 <= len(H) <= 6000:
        return None
    P = stack_predictions(H, models, shape, bg)
    truth_i = rng.randrange(len(H))
    truth = P[truth_i]
    columns = [np.ones(len(H), bool) for _ in range(n_sensors)]
    pooled = np.ones(len(H), bool)
    # all hypotheses equal to the truth on every cell count as one placement (sensorimotor symmetric)
    same_as_truth = (P == truth).all(axis=(1, 2))
    reads, steps = 0, 0
    pos = [(rng.randrange(shape[0]), rng.randrange(shape[1])) for _ in range(n_sensors)]
    visited = set()
    while True:
        steps += 1
        for s in range(n_sensors):
            voted = np.logical_and.reduce(columns)
            alive = np.nonzero(voted)[0]
            if policy == "hyp" and len(alive) >= 2:
                a, b = alive[0], alive[-1]
                for c in alive[1:]:
                    if not (P[a] == P[c]).all():
                        b = c
                        break
                dis = np.argwhere(P[a] != P[b])
                y, x = map(int, dis[rng.randrange(len(dis))]) if len(dis) else pos[s]
            else:
                y, x = pos[s]
                for _ in range(40):
                    dy, dx = rng.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                    y2, x2 = y + dy, x + dx
                    if 0 <= y2 < shape[0] and 0 <= x2 < shape[1]:
                        y, x = y2, x2
                        if (y, x) not in visited:
                            break
            pos[s] = (y, x)
            visited.add((y, x))
            reads += 1
            obs = truth[y, x]
            columns[s] &= P[:, y, x] == obs
            pooled &= P[:, y, x] == obs
        voted = np.logical_and.reduce(columns)
        assert np.array_equal(voted, pooled), "vote differs from pooling"
        if (voted == same_as_truth).all():
            return dict(reads=reads, steps=steps, H=len(H), cells=int(shape[0] * shape[1]))
        if steps > 4000:
            return None


def main():
    tasks = load_split("agi1-train")
    rng = random.Random(20261101)
    names = sorted(tasks)
    rng.shuffle(names)
    rows = []
    n_trials = 0
    for name in names:
        g = tasks[name]["train"][0][0]
        if g.shape[0] > 14 or g.shape[1] > 14:
            continue
        ms = models_from(g)
        if len(ms) < 2:
            continue
        ms = ms[:6]
        for policy in ("walk", "hyp"):
            for n in (1, 2, 4, 8):
                r = trial(ms, g.shape, C.background(g), n, policy, random.Random(zlib.crc32(f"{name}/{policy}/{n}".encode())))
                if r:
                    r.update(task=name, policy=policy, n=n)
                    rows.append(r)
                    n_trials += 1
        if len({r["task"] for r in rows}) >= 60:
            break
    summary = {}
    for policy in ("walk", "hyp"):
        for n in (1, 2, 4, 8):
            s = [r for r in rows if r["policy"] == policy and r["n"] == n]
            summary[f"{policy}/{n}"] = dict(trials=len(s), median_reads=float(np.median([r["reads"] for r in s])),
                                            median_steps=float(np.median([r["steps"] for r in s])),
                                            median_cells=float(np.median([r["cells"] for r in s])))
    out = dict(assertion="vote == pool held after every step of every trial", trials=n_trials,
               tasks=len({r["task"] for r in rows}), summary=summary)
    json.dump(out, open(os.path.join(HERE, "results", "vote_equals_pool.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
