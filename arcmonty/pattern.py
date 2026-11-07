"""Recognise-and-act learning module: object recognition in clutter, then a behaviour on each recognised instance.

Learning: each connected group of changed cells in a demo is an object instance; its model is the input pattern
that must be present (on the changed cells, the whole bounding box, or the box plus a 1-cell margin) and the output
written on the changed cells. Models are canonicalised under D8; an instance matching a stored model merges into it,
otherwise it becomes a new model (Monty: "no match -> new object"). Inference: every model in every D8 pose is
matched at every location (exhaustive evidence); exact matches act. Evidence: demos reproduced exactly (no spurious
matches), then leave-one-out prediction of held-out demos.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.ndimage import label

from arcmonty.objects import d8

CTX = ("mask", "bbox", "margin")
WILD = -1  # cell not constrained by the model


def _instances(i, o, ctx):
    changed = i != o
    lab, n = label(changed, structure=np.ones((3, 3)))
    H, W = i.shape
    out = []
    for r in range(1, n + 1):
        ys, xs = np.nonzero(lab == r)
        m = 1 if ctx == "margin" else 0
        y0, y1, x0, x1 = ys.min() - m, ys.max() + 1 + m, xs.min() - m, xs.max() + 1 + m
        if y0 < 0 or x0 < 0 or y1 > H or x1 > W or (y1 - y0) * (x1 - x0) > 100:
            return None
        cm = lab[y0:y1, x0:x1] == r
        pat_in = i[y0:y1, x0:x1].astype(np.int16).copy()
        if ctx == "mask":
            pat_in[~cm] = WILD
        pat_out = np.where(cm, o[y0:y1, x0:x1], WILD).astype(np.int16)
        out.append((pat_in, pat_out))
    return out


def _canon(pat_in, pat_out):
    best = None
    for k in range(8):
        a, b = d8(pat_in, k), d8(pat_out, k)
        key = (a.shape, a.tobytes(), b.tobytes())
        if best is None or key < best[0]:
            best = (key, a, b)
    return best


def learn(pairs, ctx):
    lib = {}
    for i, o in pairs:
        inst = _instances(i, o, ctx)
        if inst is None:
            return None
        for pat_in, pat_out in inst:
            key, a, b = _canon(pat_in, pat_out)
            lib[key] = (a, b)
        if len(lib) > 12:
            return None
    return list(lib.values()) or None


def predict(lib, grid):
    out = grid.copy()
    written = np.zeros(grid.shape, dtype=bool)
    for a0, b0 in lib:
        for k in range(8):
            a, b = d8(a0, k), d8(b0, k)
            h, w = a.shape
            if h > grid.shape[0] or w > grid.shape[1]:
                continue
            win = sliding_window_view(grid, (h, w))
            care = a != WILD
            hit = ((win == a) | ~care).all(axis=(2, 3))
            for y, x in zip(*np.nonzero(hit)):
                act = b != WILD
                region = out[y:y + h, x:x + w]
                prev = written[y:y + h, x:x + w]
                new = b[act].astype(grid.dtype)
                if (prev[act] & (region[act] != new)).any():
                    return None  # two recognised instances disagree about a cell
                region[act] = new
                prev[act] = True
    return out


def candidates(task):
    pairs = task["train"]
    if not all(i.shape == o.shape for i, o in pairs) or all(np.array_equal(i, o) for i, o in pairs):
        return []
    out = []
    for ctx in CTX:
        lib = learn(pairs, ctx)
        if lib is None:
            continue
        if any((p := predict(lib, i)) is None or not np.array_equal(p, o) for i, o in pairs):
            continue
        preds = [predict(lib, t) for t in task["test"]]
        if any(p is None for p in preds) or all(np.array_equal(p, t) for p, t in zip(preds, task["test"])):
            continue  # nothing recognised in the test input: abstain
        loo = 0
        for j in range(len(pairs)):
            sub = learn(pairs[:j] + pairs[j + 1:], ctx)
            if sub is not None:
                p = predict(sub, pairs[j][0])
                loo += p is not None and np.array_equal(p, pairs[j][1])
        out.append(dict(lm="pattern", hyp=f"pattern/{ctx}/{len(lib)}models", preds=preds, evidence=loo / len(pairs)))
    return out
