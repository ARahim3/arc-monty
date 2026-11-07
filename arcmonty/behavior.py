"""Behaviour learning module: learn what happens around each object *in that object's own reference frame*
(D8-canonicalised pose), keyed by object type, and apply it to the objects of the test input.

Monty analogue: a behaviour model stored separately from morphology, in an object-centric reference frame, so
it transfers to objects at any position and orientation. Evidence = every observed cell of every demo pair must
be predicted (consistency), plus leave-one-out prediction of whole held-out demos (generalisation).
"""
import itertools

import numpy as np
from scipy.ndimage import distance_transform_cdt

from arcmonty.objects import background, segment, to_frame, from_frame

SAME, SELF = ("same",), ("self",)
SEGS = ("color8", "multi8", "color4")
KEYS = ("any", "color", "size", "holes", "sym", "shape", "shape_color")
FRAMES = ("canon", "abs")
RADII = (0, 1, 2, 4, 30)
OWNERSHIP = ("nearest", "union")  # a cell is explained by its unique nearest object, or by every object within R


def _key(o, key):
    if key == "any":
        return 0
    if key == "color":
        return o.color
    if key == "size":
        return o.size
    if key == "holes":
        return o.holes
    if key == "sym":
        return o.symmetric
    if key == "shape":
        return o.key_shape
    return o.key_shape, o.canon.tobytes()


_SEG_CACHE = {}
AMBIG = ("ambig",)


def _scene(grid, seg):
    """Objects plus each object's chessboard-distance map (every object within R of a cell is a column for it)."""
    k = (grid.tobytes(), grid.shape, seg)
    if k in _SEG_CACHE:
        return _SEG_CACHE[k]
    objs = segment(grid, seg, bg=background(grid))
    if not objs or len(objs) > 60:
        res = (objs, None)
    else:
        res = (objs, np.stack([distance_transform_cdt(~_full_mask(grid.shape, o), metric="chessboard") for o in objs]))
    if len(_SEG_CACHE) > 4000:
        _SEG_CACHE.clear()
    _SEG_CACHE[k] = res
    return res


def _full_mask(shape, o):
    m = np.zeros(shape, dtype=bool)
    m[o.cells] = True
    return m


def _frame_coords(o, ys, xs, frame):
    if frame == "canon":
        return to_frame(o, ys, xs)
    return ys - o.y0, xs - o.x0


def _encode(out_c, in_c, o):
    if out_c == in_c:
        return SAME
    if o.color >= 0 and out_c == o.color:
        return SELF
    return int(out_c)


def _decode(v, o):
    return o.color if v == SELF else v


def _cells(dists, idx, R, own):
    m = dists[idx] <= R
    if own == "nearest" and len(dists) > 1:
        order = np.sort(dists, axis=0)
        m &= (dists[idx] == order[0]) & (order[0] < order[1])
    return np.nonzero(m)


def learn(pairs, seg, key, frame, R, own="union"):
    """Behaviour model {obj_key: {(u, v): value}}: what the output shows at each location of the object's frame.
    A location seen both changed and unchanged (or with different changes) is ambiguous: this object type alone
    does not explain it, so it predicts nothing there (another column may)."""
    obs = {}
    for inp, out in pairs:
        objs, dists = _scene(inp, seg)
        if dists is None:
            return None
        changed = inp != out
        covered = np.zeros(inp.shape, dtype=bool)
        for idx, o in enumerate(objs):
            ys, xs = _cells(dists, idx, R, own)
            covered[ys, xs] = True
            us, vs = _frame_coords(o, ys, xs, frame)
            table = obs.setdefault(_key(o, key), {})
            for u, v, y, x in zip(us.tolist(), vs.tolist(), ys.tolist(), xs.tolist()):
                table.setdefault((u, v), set()).add(_encode(out[y, x], inp[y, x], o))
        if (changed & ~covered).any():
            return None
    return {k: {loc: (next(iter(vals)) if len(vals) == 1 else AMBIG) for loc, vals in table.items()}
            for k, table in obs.items()}


def predict(model, grid, seg, key, frame, R, own="union"):
    """Every object within R votes for changes at its cells; a predicted change outweighs 'no change';
    conflicting changes are resolved by majority (ties -> no prediction)."""
    objs, dists = _scene(grid, seg)
    if dists is None:
        return None, 0
    votes = {}
    unseen = 0
    for idx, o in enumerate(objs):
        table = model.get(_key(o, key))
        if table is None:
            unseen += 1
            continue
        ys, xs = _cells(dists, idx, R, own)
        us, vs = _frame_coords(o, ys, xs, frame)
        for u, v, y, x in zip(us.tolist(), vs.tolist(), ys.tolist(), xs.tolist()):
            val = table.get((u, v), SAME)
            if val is not SAME and val != SAME and val != AMBIG:
                votes.setdefault((y, x), []).append(_decode(val, o))
    out = grid.copy()
    for (y, x), vals in votes.items():
        cs, ns = np.unique(vals, return_counts=True)
        top = ns.argmax()
        if (ns == ns[top]).sum() == 1:
            out[y, x] = cs[top]
    return out, unseen


def candidates(task):
    """Hypotheses (segmentation, object key, frame, radius, ownership) that reproduce every demo; evidence =
    fraction of demos predicted when held out (leave-one-out), i.e. Monty-style prediction of unseen observations."""
    pairs = task["train"]
    if not all(i.shape == o.shape for i, o in pairs) or all(np.array_equal(i, o) for i, o in pairs):
        return []
    out = []
    for seg, key, frame, R, own in itertools.product(SEGS, KEYS, FRAMES, RADII, OWNERSHIP):
        if own == "union" and R > 2:  # every object would cover most of the grid: uninformative and slow
            continue
        model = learn(pairs, seg, key, frame, R, own)
        if model is None:
            continue
        if any(not np.array_equal(predict(model, i, seg, key, frame, R, own)[0], o) for i, o in pairs):
            continue
        preds = [predict(model, t, seg, key, frame, R, own) for t in task["test"]]
        if any(p is None or unseen > 0 for p, unseen in preds):
            continue
        loo = 0
        for j in range(len(pairs)):
            m = learn(pairs[:j] + pairs[j + 1:], seg, key, frame, R, own)
            if m is not None:
                p, unseen = predict(m, pairs[j][0], seg, key, frame, R, own)
                loo += p is not None and unseen == 0 and np.array_equal(p, pairs[j][1])
        out.append(dict(lm="behavior", hyp=f"{seg}/{key}/{frame}/R{R}/{own}", preds=[p for p, _ in preds],
                        evidence=loo / len(pairs)))
    return out


def solve(task):
    from arcmonty.vote import attempts_from
    return attempts_from(task, candidates(task))
