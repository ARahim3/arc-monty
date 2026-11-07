"""Association learning module: symbols defined inside the task (templates, legends) - ARC-AGI-2's
"symbolic interpretation". Monty analogue: recognise an object by matching it, under any D8 pose, against
models learned from the same scene; the matched model's associated feature (colour) is the prediction.

Families (parameters fitted on all demos; confidence = honest leave-one-out over the ordered hypothesis list):
  template - every object of the source colour takes the colour of the other object with the same shape (D8)
  legend   - adjacent colour pairs inside a compact key define a map a -> b; recolour or fill holes by it
"""
import numpy as np
from scipy.ndimage import binary_fill_holes, label

from arcmonty.objects import background, segment


def _canon_mask(o, pose_free):
    return o.key_shape if pose_free else (o.mask.shape, o.mask.tobytes())


# ---------------------------------------------------------------- template recolour
def _template(grid, p):
    bg = background(grid)
    objs = segment(grid, "color8", bg=bg)
    out = grid.copy()
    lib = {}
    for o in objs:
        if o.color != p["src"]:
            lib.setdefault(_canon_mask(o, p["pose_free"]), set()).add(o.color)
    for o in objs:
        if o.color != p["src"]:
            continue
        cols = lib.get(_canon_mask(o, p["pose_free"]))
        if not cols:
            if p["strict"]:
                return None
            continue
        if len(cols) != 1:
            return None
        out[o.cells] = next(iter(cols))
    return out


def _template_hypotheses(pairs):
    srcs = None
    for i, o in pairs:
        ch = np.unique(i[i != o])
        srcs = set(ch.tolist()) if srcs is None else srcs & set(ch.tolist())
    for src in sorted(srcs or []):
        for pose_free in (True, False):
            for strict in (True, False):
                yield dict(fam="template", src=src, pose_free=pose_free, strict=strict)


# ---------------------------------------------------------------- legend map
def _legend_map(grid, bg, square="cols"):
    """Colour pairs (a, b) that sit side by side in 2-cell objects or in rows/cols of a compact key block."""
    m = {}
    lab, n = label(grid != bg, structure=np.ones((3, 3)))
    for r in range(1, n + 1):
        ys, xs = np.nonzero(lab == r)
        h, w = int(np.ptp(ys)) + 1, int(np.ptp(xs)) + 1
        block = grid[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        if (block == bg).any() or len(ys) > 20:
            continue
        if w == 2 and (h != 2 or square == "rows"):
            pairs = [(block[y, 0], block[y, 1]) for y in range(h)]
        elif h == 2:
            pairs = [(block[0, x], block[1, x]) for x in range(w)]
        else:
            continue
        for a, b in pairs:
            if m.get(int(a), int(b)) != int(b):
                return None
            m[int(a)] = int(b)
    return m


def _legend(grid, p):
    bg = background(grid)
    mp_ = _legend_map(grid, bg, p["square"])
    if not mp_:
        return None
    inv = {}
    for a, b in mp_.items():
        inv.setdefault(b, a)
    objs = segment(grid, "color8", bg=bg)
    if p["dir"] == "auto":  # the key side is the one that names the shapes actually present
        shape_cols = {o.color for o in objs if o.size > 1}
        if len(shape_cols & set(inv)) > len(shape_cols & set(mp_)):
            mp_ = inv
    elif p["dir"] == "rev":
        mp_ = inv
    out = grid.copy()
    for o in objs:
        if o.color not in mp_ or o.size <= 1:
            continue
        if p["act"] == "recolor":
            out[o.cells] = mp_[o.color]
        else:
            full = np.zeros(grid.shape, dtype=bool)
            full[o.cells] = True
            holes = binary_fill_holes(full) & ~full & (grid == bg)
            out[holes] = mp_[o.color]
    return out


def _legend_hypotheses(pairs):
    for act in ("fill", "recolor"):
        for d in ("auto", "fwd", "rev"):
            for square in ("cols", "rows"):
                yield dict(fam="legend", act=act, dir=d, square=square)


PREDICT = {"template": _template, "legend": _legend}


def _apply(grid, p):
    try:
        return PREDICT[p["fam"]](grid, p)
    except Exception:
        return None


def candidates(task, max_hyps=500):
    pairs = task["train"]
    if not all(i.shape == o.shape for i, o in pairs) or all(np.array_equal(i, o) for i, o in pairs):
        return []
    hyps, fits = [], []
    for gen in (_template_hypotheses, _legend_hypotheses):
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
        out.append(dict(lm="association", hyp=str(hyps[h]), preds=preds, evidence=float(loo / n)))
        if len(out) >= 4:
            break
    return out
