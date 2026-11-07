"""Periodic learning module: toroidal reference frames (TBP future work: "repeating patterns").

A region is modelled in a reference frame that wraps around with period (py, px); every cell's prediction is the
majority colour of its phase (all cells sharing its position modulo the period). Regions are the whole grid, the
panels between separator lines, or the interiors of single-colour frames. Uses:
  repair - overwrite cells that disagree with their phase (corrupted periodic patterns)
  extend - fill background cells from their phase (continue a pattern into empty space)
The period is the smallest one whose phase model explains the observed cells within a tolerance (evidence).
Parameters are fitted on all demos; confidence = honest leave-one-out over the ordered hypothesis list.
"""
import numpy as np
from scipy.ndimage import label

from arcmonty.objects import background


def _period_model(region, known, tol, min_obs=3):
    """Period with the fewest disagreements among those whose every phase is observed >= min_obs times (so the
    phase majority is meaningful); ties go to the smaller period. Accepted if disagreements <= tol * observed."""
    h, w = region.shape
    n = int(known.sum())
    if n == 0:
        return None
    Y, X = np.indices((h, w))
    vals = region[known].astype(np.int64)
    best = None
    for py in range(1, h + 1):
        for px in range(1, w + 1):
            area = py * px
            if area * min_obs > h * w:
                continue
            phase = (Y % py) * px + (X % px)
            counts = np.bincount(phase[known] * 10 + vals, minlength=area * 10).reshape(area, 10)
            if (counts.sum(1) < min_obs).any():
                continue
            bad = n - int(counts.max(1).sum())
            key = (bad, area)
            if best is None or key < best[0]:
                best = (key, counts.argmax(1)[phase])
    if best is None or best[0][0] > tol * n:
        return None
    return best[1]


def _regions(grid, mode):
    H, W = grid.shape
    if mode == "grid":
        return [(slice(0, H), slice(0, W))]
    out = []
    if mode == "panels":
        for sep in np.unique(grid):
            rows = [r for r in range(H) if (grid[r] == sep).all()]
            cols = [c for c in range(W) if (grid[:, c] == sep).all()]
            if not rows and not cols:
                continue
            rb, start = [], 0
            for s in sorted(rows) + [H]:
                if s > start:
                    rb.append((start, s))
                start = s + 1
            cb, start = [], 0
            for s in sorted(cols) + [W]:
                if s > start:
                    cb.append((start, s))
                start = s + 1
            if len(rb) * len(cb) >= 2:
                return [(slice(a, b), slice(c, d)) for a, b in rb for c, d in cb]
        return []
    # frames: interiors of single-colour rectangular rings
    for c in np.unique(grid):
        lab, n = label(grid == c)
        for r in range(1, n + 1):
            ys, xs = np.nonzero(lab == r)
            y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
            if y1 - y0 < 2 or x1 - x0 < 2:
                continue
            ring = np.zeros((y1 - y0 + 1, x1 - x0 + 1), dtype=bool)
            ring[0] = ring[-1] = True
            ring[:, 0] = ring[:, -1] = True
            if (lab[y0:y1 + 1, x0:x1 + 1] == r)[ring].all():
                out.append((slice(y0 + 1, y1), slice(x0 + 1, x1)))
    # innermost frames only: a region containing another frame's interior is not itself a pattern
    def inside(a, b):
        return a[0].start >= b[0].start and a[0].stop <= b[0].stop and a[1].start >= b[1].start and a[1].stop <= b[1].stop
    return [b for b in out if not any(a is not b and inside(a, b) for a in out)]


def _apply(grid, p):
    try:
        out = grid.copy()
        bg = background(grid)
        regs = _regions(grid, p["regions"])
        if not regs:
            return None
        for sy, sx in regs:
            reg = grid[sy, sx]
            hole = bg if p.get("hole") is None else p["hole"]
            known = np.ones(reg.shape, dtype=bool) if p["use"] == "repair" else reg != hole
            if p["use"] == "extend" and not known.any():
                continue
            pred = _period_model(reg, known, p["tol"], min_obs=3 if p["use"] == "repair" else 1)
            if pred is None:
                if p["use"] == "repair":
                    continue
                return None
            if p["use"] == "repair":
                out[sy, sx] = pred
            else:
                o = out[sy, sx]
                o[~known] = pred[~known]
        return out
    except Exception:
        return None


def _hypotheses(pairs):
    holes = None  # colours that vanish from input to output: the occluder / empty colour
    for i, o in pairs:
        gone = set(np.unique(i[i != o]).tolist())
        holes = gone if holes is None else holes & gone
    for use in ("repair", "extend"):
        for regions in ("frames", "panels", "grid"):
            if use == "repair":
                for tol in (0.05, 0.15):
                    yield dict(fam="periodic", use=use, regions=regions, tol=tol)
            else:
                for hole in [None] + sorted(holes or []):
                    yield dict(fam="periodic", use=use, regions=regions, tol=0.0, hole=hole)


def candidates(task):
    pairs = task["train"]
    if not all(i.shape == o.shape for i, o in pairs) or all(np.array_equal(i, o) for i, o in pairs):
        return []
    hyps, fits = [], []
    for p in _hypotheses(pairs):
        row = []
        for i, o in pairs:
            q = _apply(i, p)
            row.append(q is not None and np.array_equal(q, o))
        hyps.append(p)
        fits.append(row)
    fits = np.array(fits, dtype=bool)
    n = len(pairs)
    loo = 0
    for j in range(n):
        rest = np.delete(fits, j, axis=1).all(axis=1) if n > 1 else np.ones(len(hyps), dtype=bool)
        first = np.flatnonzero(rest)
        loo += int(len(first) > 0 and bool(fits[first[0], j]))
    out = []
    for h in np.flatnonzero(fits.all(axis=1)):
        preds = [_apply(t, hyps[h]) for t in task["test"]]
        if any(q is None for q in preds):
            continue
        out.append(dict(lm="periodic", hyp=str(hyps[h]), preds=preds, evidence=float(loo / n)))
    return out
