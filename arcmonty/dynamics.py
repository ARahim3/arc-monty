"""Dynamic behaviour learning module: behaviours with a stopping condition, which Monty's static models lack.

Families (each a behaviour model whose parameters are inferred by evidence across the demos):
  ray   - every object of a type emits rays (directions in the grid frame) in a colour until a border/obstacle
  move  - every object of a type moves in a direction until it touches an obstacle or the border (gravity)
  fill  - background regions enclosed by objects (holes) are filled with a colour
Evidence is the same as the other modules: reproduce every demo, then leave-one-out prediction of held-out demos.
"""
import itertools

import numpy as np
from scipy.ndimage import label

from arcmonty.objects import background, segment

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
DIR_SETS = {
    "N": [0], "S": [1], "W": [2], "E": [3], "NS": [0, 1], "WE": [2, 3], "orth": [0, 1, 2, 3],
    "diag": [4, 5, 6, 7], "all8": list(range(8)),
}


def _key(o, key):
    if key == "any":
        return 0
    if key == "color":
        return o.color
    if key == "size1":
        return o.size == 1
    return o.key_shape


# ---------------------------------------------------------------- ray
def _ray_predict(grid, p):
    bg = background(grid)
    objs = segment(grid, p["seg"], bg=bg)
    out = grid.copy()
    H, W = grid.shape
    for o in objs:
        if p["who"] is not None and _key(o, p["key"]) != p["who"]:
            continue
        col = o.color if p["color"] == "self" else p["color"]
        if col < 0:
            return None
        ys, xs = o.cells
        cells = set(zip(ys.tolist(), xs.tolist()))
        for d in DIR_SETS[p["dirs"]]:
            dy, dx = DIRS[d]
            for y, x in cells:
                yy, xx = y + dy, x + dx
                if (yy, xx) in cells:
                    continue
                while 0 <= yy < H and 0 <= xx < W:
                    if grid[yy, xx] != bg:
                        if p["stop"] == "obstacle":
                            break
                    else:
                        out[yy, xx] = col
                    yy += dy
                    xx += dx
    return out


def _ray_hypotheses(pairs):
    segs = ("color8",)
    whos = set()
    for i, o in pairs:
        for ob in segment(i, "color8", bg=background(i)):
            ch = (i != o)
            ys, xs = ob.cells
            whos.add(("color", ob.color))
            whos.add(("size1", ob.size == 1))
    out_cols = set()
    for i, o in pairs:
        out_cols |= set(np.unique(o[i != o]).tolist())
    colors = ["self"] + sorted(out_cols)
    for seg, (key, who), color, dirs, stop in itertools.product(
            segs, [("any", None)] + sorted(whos, key=str), colors, DIR_SETS, ("obstacle", "through")):
        yield dict(fam="ray", seg=seg, key=key, who=who, color=color, dirs=dirs, stop=stop)


# ---------------------------------------------------------------- move (gravity)
def _move_predict(grid, p):
    bg = background(grid)
    objs = segment(grid, p["seg"], bg=bg)
    movers = [o for o in objs if _key(o, p["key"]) == p["who"]] if p["who"] is not None else objs
    if not movers:
        return grid.copy()
    dy, dx = DIRS[p["dir"]]
    H, W = grid.shape
    out = grid.copy()
    for o in movers:
        out[o.cells] = bg
    # move the objects closest to the destination side first, so they stack
    order = sorted(movers, key=lambda o: -(o.cells[0].mean() * dy + o.cells[1].mean() * dx))
    for o in order:
        ys, xs = o.cells
        vals = grid[ys, xs]
        k = 0
        while True:
            ny, nx = ys + dy * (k + 1), xs + dx * (k + 1)
            if (ny < 0).any() or (ny >= H).any() or (nx < 0).any() or (nx >= W).any():
                break
            if (out[ny, nx] != bg).any():
                break
            k += 1
        out[ys + dy * k, xs + dx * k] = vals
    return out


def _move_hypotheses(pairs):
    whos = set()
    for i, _ in pairs:
        for ob in segment(i, "color8", bg=background(i)):
            whos.add(("color", ob.color))
    for seg in ("color8", "multi8"):
        for (key, who) in [("any", None)] + sorted(whos, key=str):
            if seg == "multi8" and key == "color":
                continue
            for d in range(4):
                yield dict(fam="move", seg=seg, key=key, who=who, dir=d)


# ---------------------------------------------------------------- fill enclosed background
def _fill_predict(grid, p):
    bg = background(grid)
    free = grid == bg
    lab, n = label(free, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]) if p["conn"] == 4 else np.ones((3, 3)))
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
    out = grid.copy()
    for r in range(1, n + 1):
        if r in border:
            continue
        m = lab == r
        if p["color"] == "encloser":
            ring = np.zeros_like(m)
            ring[:-1] |= m[1:]
            ring[1:] |= m[:-1]
            ring[:, :-1] |= m[:, 1:]
            ring[:, 1:] |= m[:, :-1]
            cols = np.unique(grid[ring & ~m])
            cols = cols[cols != bg]
            if len(cols) != 1:
                return None
            out[m] = cols[0]
        else:
            out[m] = p["color"]
    return out


def _fill_hypotheses(pairs):
    cols = set()
    for i, o in pairs:
        cols |= set(np.unique(o[i != o]).tolist())
    for conn in (4, 8):
        for color in ["encloser"] + sorted(cols):
            yield dict(fam="fill", conn=conn, color=color)


# ---------------------------------------------------------------- connect aligned same-colour cells
def _connect_predict(grid, p):
    bg = background(grid)
    out = grid.copy()
    H, W = grid.shape
    src = p["src"]
    ys, xs = np.nonzero(grid == src)
    pts = list(zip(ys.tolist(), xs.tolist()))
    dirs = [(0, 1), (1, 0)] + ([(1, 1), (1, -1)] if p["diag"] else [])
    S = set(pts)
    for y, x in pts:
        for dy, dx in dirs:
            yy, xx, path = y + dy, x + dx, []
            while 0 <= yy < H and 0 <= xx < W and (yy, xx) not in S:
                if grid[yy, xx] != bg and p["block"]:
                    path = None
                    break
                path.append((yy, xx))
                yy += dy
                xx += dx
            if path and 0 <= yy < H and 0 <= xx < W and (yy, xx) in S:
                for a, b in path:
                    if grid[a, b] == bg or not p["block"]:
                        out[a, b] = p["color"]
    return out


def _connect_hypotheses(pairs):
    srcs, cols = None, set()
    for i, o in pairs:
        cs = set(np.unique(i).tolist()) - {background(i)}
        srcs = cs if srcs is None else srcs & cs
        cols |= set(np.unique(o[i != o]).tolist())
    for src in sorted(srcs or []):
        for color in sorted(cols):
            for diag in (False, True):
                for block in (True, False):
                    yield dict(fam="connect", src=src, color=color, diag=diag, block=block)


PREDICT = {"ray": _ray_predict, "move": _move_predict, "fill": _fill_predict, "connect": _connect_predict}


def _apply(grid, p):
    try:
        return PREDICT[p["fam"]](grid, p)
    except Exception:
        return None


def candidates(task, max_hyps=3000):
    """Fit every hypothesis to every demo (consistency matrix), keep full fits, and score the learner by honest
    leave-one-out: for each held-out demo, the first hypothesis (simplicity order) fitting the other demos must
    also predict the held-out one."""
    pairs = task["train"]
    if not all(i.shape == o.shape for i, o in pairs) or all(np.array_equal(i, o) for i, o in pairs):
        return []
    hyps, fits = [], []
    for gen in (_fill_hypotheses, _connect_hypotheses, _move_hypotheses, _ray_hypotheses):
        for p in gen(pairs):
            if len(hyps) >= max_hyps:
                break
            row = []
            for i, o in pairs:
                q = _apply(i, p)
                row.append(q is not None and np.array_equal(q, o))
            hyps.append(p)
            fits.append(row)
    if not hyps:
        return []
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
        out.append(dict(lm="dynamics", hyp=str(hyps[h]), preds=preds, evidence=float(loo / n)))
        if len(out) >= 8:
            break
    return out
