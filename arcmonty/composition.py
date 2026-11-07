"""Composition learning module: the output grid is built from parts of the input (TBT compositional models).

Families (parameters inferred by evidence across demos; confidence = honest leave-one-out over a fixed
simplicity-ordered hypothesis list, as in the dynamics module):
  panels  - the input is several panels (sensors on one object); the output is their vote (AND/OR/XOR/...)
  select  - the output is one recognised object (picked by a property), optionally in another D8 pose
  down    - the output is a coarse view: each block of the input becomes one cell
  tile    - the output is the input tiled with a D8 pose per tile, upscaled, or its fractal self-product
"""
import itertools

import numpy as np

from arcmonty.objects import background, d8, segment


# ---------------------------------------------------------------- panels
def _panels(grid):
    """Split on uniform separator rows/cols (a colour filling a whole row/col); all panels must share a shape."""
    H, W = grid.shape
    for sep in np.unique(grid):
        rows = [r for r in range(H) if (grid[r] == sep).all()]
        cols = [c for c in range(W) if (grid[:, c] == sep).all()]
        if not rows and not cols:
            continue
        rb = _bands(rows, H)
        cb = _bands(cols, W)
        if len(rb) * len(cb) < 2:
            continue
        ps = [grid[a:b, c:d] for a, b in rb for c, d in cb]
        if len({p.shape for p in ps}) == 1 and ps[0].size > 0:
            return int(sep), ps
    return None, None


def _bands(seps, n):
    out, start = [], 0
    for s in sorted(seps) + [n]:
        if s > start:
            out.append((start, s))
        start = s + 1
    return out


OPS = {
    "and": lambda m: m.all(0), "or": lambda m: m.any(0), "xor": lambda m: m.sum(0) % 2 == 1,
    "nor": lambda m: ~m.any(0), "one": lambda m: m.sum(0) == 1, "notall": lambda m: m.any(0) & ~m.all(0),
}


def _panels_predict(grid, p):
    sep, ps = _panels(grid)
    if ps is None or len(ps) != p["n"]:
        return None
    stack = np.stack(ps)
    bg = p["pbg"]
    if p["op"] == "overlay":
        out = np.full(ps[0].shape, bg, dtype=grid.dtype)
        for k in reversed(p["order"]):
            m = stack[k] != bg
            out[m] = stack[k][m]
        return out
    mask = OPS[p["op"]](stack != bg)
    return np.where(mask, p["color"], p["obg"]).astype(grid.dtype)


def _panels_hypotheses(pairs):
    n_set, cols, obgs = set(), set(), set()
    for i, o in pairs:
        sep, ps = _panels(i)
        if ps is None or ps[0].shape != o.shape:
            return
        n_set.add(len(ps))
        cols |= set(np.unique(o).tolist())
        obgs.add(background(o))
    if len(n_set) != 1:
        return
    n = n_set.pop()
    pbgs = sorted({0} | {background(np.concatenate([q.ravel() for q in _panels(i)[1]]).reshape(1, -1)) for i, _ in pairs})
    for pbg in pbgs:
        for op in OPS:
            for color in sorted(cols):
                for obg in sorted(obgs | {0}):
                    if color != obg:
                        yield dict(fam="panels", n=n, op=op, color=color, obg=obg, pbg=pbg)
        if n <= 4:
            for order in itertools.permutations(range(n)):
                yield dict(fam="panels", n=n, op="overlay", order=list(order), pbg=pbg)


# ---------------------------------------------------------------- select one object
PROPS = {
    "size": lambda o, g: o.size, "bbox": lambda o, g: o.mask.size, "ncol": lambda o, g: len(np.unique(o.patch[o.mask])),
    "top": lambda o, g: -o.y0, "left": lambda o, g: -o.x0, "density": lambda o, g: o.size / o.mask.size,
    "holes": lambda o, g: o.holes, "sym": lambda o, g: int(o.symmetric),
}


def _crop(grid, o, mode, bg):
    h, w = o.mask.shape
    if mode == "full":
        return grid[o.y0:o.y0 + h, o.x0:o.x0 + w].copy()
    return np.where(o.mask, grid[o.y0:o.y0 + h, o.x0:o.x0 + w], bg).astype(grid.dtype)


def _select(grid, p):
    bg = background(grid)
    objs = segment(grid, p["seg"], bg=bg)
    if len(objs) < 2:
        return None
    if p["rule"] in ("max", "min"):
        vals = np.array([PROPS[p["prop"]](o, grid) for o in objs], dtype=float)
        v = vals.max() if p["rule"] == "max" else vals.min()
        idx = np.flatnonzero(vals == v)
        if len(idx) != 1:
            return None
        o = objs[idx[0]]
    else:  # odd one out: the only object whose shape (or colour) differs from all others
        keys = [o.key_shape if p["prop"] == "shape" else o.color for o in objs]
        uniq = [k for k in keys if keys.count(k) == 1]
        if len(uniq) != 1:
            return None
        o = objs[keys.index(uniq[0])]
    return d8(_crop(grid, o, p["crop"], bg), p["k"])


def _select_hypotheses(pairs):
    if not all(o.size < i.size for i, o in pairs):
        return
    for seg in ("color8", "multi8", "color4"):
        for crop in ("full", "mask"):
            for k in range(8):
                for prop in PROPS:
                    for rule in ("max", "min"):
                        yield dict(fam="select", seg=seg, crop=crop, k=k, prop=prop, rule=rule)
                for prop in ("shape", "color"):
                    yield dict(fam="select", seg=seg, crop=crop, k=k, prop=prop, rule="odd")


# ---------------------------------------------------------------- downscale
def _down(grid, p):
    H, W = grid.shape
    a, b = p["a"], p["b"]
    if H % a or W % b:
        return None
    bg = background(grid)
    blocks = grid.reshape(H // a, a, W // b, b).transpose(0, 2, 1, 3).reshape(H // a, W // b, a * b)
    out = np.zeros((H // a, W // b), dtype=grid.dtype)
    for y in range(H // a):
        for x in range(W // b):
            v = blocks[y, x]
            if p["rule"] == "majority":
                c, n = np.unique(v, return_counts=True)
                out[y, x] = c[n.argmax()]
            else:  # any non-background colour (must be unique)
                c = np.unique(v[v != bg])
                if len(c) > 1:
                    return None
                out[y, x] = c[0] if len(c) else bg
    return out


def _down_hypotheses(pairs):
    ratios = {(i.shape[0] // o.shape[0], i.shape[1] // o.shape[1]) for i, o in pairs
              if i.shape[0] % o.shape[0] == 0 and i.shape[1] % o.shape[1] == 0}
    if len(ratios) != 1:
        return
    a, b = ratios.pop()
    if a * b <= 1:
        return
    for rule in ("majority", "any"):
        yield dict(fam="down", a=a, b=b, rule=rule)


# ---------------------------------------------------------------- tile / upscale / fractal
def _tile(grid, p):
    if p["mode"] == "up":
        return np.kron(grid, np.ones((p["a"], p["b"]), dtype=grid.dtype))
    if p["mode"] == "fractal":
        bg = background(grid) if p["bg"] is None else p["bg"]
        m = (grid != bg).astype(grid.dtype)
        out = np.kron(m, grid)
        if p["inv"]:
            out = np.kron(1 - m, grid)
        h, w = grid.shape
        big = np.kron(m if not p["inv"] else 1 - m, np.ones((h, w), dtype=grid.dtype))
        return np.where(big > 0, out, bg).astype(grid.dtype)
    rows = []
    for r in range(p["a"]):
        rows.append(np.concatenate([d8(grid, p["ks"][r][c]) for c in range(p["b"])], axis=1))
    return np.concatenate(rows, axis=0)


def _tile_hypotheses(pairs):
    ratios = {(o.shape[0] // i.shape[0], o.shape[1] // i.shape[1]) for i, o in pairs
              if o.shape[0] % i.shape[0] == 0 and o.shape[1] % i.shape[1] == 0}
    if len(ratios) != 1:
        return
    a, b = ratios.pop()
    if a * b <= 1:
        return
    yield dict(fam="tile", mode="up", a=a, b=b)
    sq = all(i.shape[0] == i.shape[1] for i, _ in pairs)
    if all((a, b) == i.shape for i, _ in pairs):
        for inv in (False, True):
            for bg in (None, 0):
                yield dict(fam="tile", mode="fractal", inv=inv, bg=bg)
    # per-tile pose: the D8 poses consistent with every demo, smallest one kept
    if len({i.shape for i, _ in pairs}) and all(o.shape == (i.shape[0] * a, i.shape[1] * b) for i, o in pairs):
        ks = []
        for r in range(a):
            row = []
            for c in range(b):
                ok = set(range(8))
                for i, o in pairs:
                    h, w = i.shape
                    tile = o[r * h:(r + 1) * h, c * w:(c + 1) * w]
                    ok &= {k for k in range(8) if d8(i, k).shape == tile.shape and np.array_equal(d8(i, k), tile)}
                if not ok:
                    return
                row.append(min(ok))
            ks.append(row)
        yield dict(fam="tile", mode="pose", a=a, b=b, ks=ks)


# ---------------------------------------------------------------- fixed-corner crop
def _corner(grid, p):
    h, w = p["h"], p["w"]
    H, W = grid.shape
    if h > H or w > W:
        return None
    y = 0 if p["corner"][0] == "t" else H - h
    x = 0 if p["corner"][1] == "l" else W - w
    return grid[y:y + h, x:x + w].copy()


def _corner_hypotheses(pairs):
    shapes = {o.shape for _, o in pairs}
    if len(shapes) != 1 or not all(o.size < i.size for i, o in pairs):
        return
    h, w = shapes.pop()
    for corner in ("tl", "tr", "bl", "br"):
        yield dict(fam="corner", h=h, w=w, corner=corner)


PREDICT = {"panels": _panels_predict, "select": _select, "down": _down, "tile": _tile, "corner": _corner}


def _apply(grid, p):
    try:
        return PREDICT[p["fam"]](grid, p)
    except Exception:
        return None


def candidates(task, max_hyps=4000):
    pairs = task["train"]
    hyps, fits = [], []
    for gen in (_tile_hypotheses, _corner_hypotheses, _down_hypotheses, _panels_hypotheses, _select_hypotheses):
        for p in gen(pairs) or []:
            if len(hyps) >= max_hyps:
                break
            row = []
            for i, o in pairs:
                q = _apply(i, p)
                row.append(q is not None and q.shape == o.shape and np.array_equal(q, o))
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
        out.append(dict(lm="composition", hyp=str(hyps[h]), preds=preds, evidence=float(loo / n)))
        if len(out) >= 8:
            break
    return out
