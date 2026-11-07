"""Symmetry learning module: recognise a grid's structure (mirror / rotation / translation symmetries) by
evidence over hypotheses, then predict occluded or corrupted cells by voting across the accepted hypotheses.

Monty analogue: hypotheses = poses of the grid relative to itself; evidence = agreement of observed cell pairs
under each pose; prediction of unobserved features = votes from every accepted pose hypothesis.
"""
import numpy as np


def _hypotheses(H, W):
    I, J = np.indices((H, W))
    for a in range(1, 2 * W - 2):
        yield ("mh", a), I, a - J
    for b in range(1, 2 * H - 2):
        yield ("mv", b), b - I, J
    for d in range(-(W - 2), H - 1):
        yield ("md", d), J + d, I - d
    for s in range(1, H + W - 2):
        yield ("ma", s), s - J, s - I
    for A in range(1, 2 * H - 2):
        for B in range(1, 2 * W - 2):
            yield ("r180", A, B), A - I, B - J
            if (A - B) % 2 == 0:
                yield ("r90", A, B), (A - B) // 2 + J, (A + B) // 2 - I
    for p in range(0, H):
        for q in range(-(W - 1), W):
            if p > 0 or q > 0:
                yield ("t", p, q), I + p, J + q


_CACHE = {}


def _stats(grid, known):
    """Evidence (agreement on informative cell pairs) for every symmetry hypothesis; cached per grid."""
    key = (grid.shape, grid.tobytes(), known.tobytes())
    if key in _CACHE:
        return _CACHE[key]
    H, W = grid.shape
    vals, counts = np.unique(grid[known], return_counts=True)
    bg = vals[np.argmax(counts)] if len(vals) else 0
    informative = known & (grid != bg)
    n_inf = max(1, informative.sum())
    out = []
    for name, I2, J2 in _hypotheses(H, W):
        inb = (I2 >= 0) & (I2 < H) & (J2 >= 0) & (J2 < W)
        I2c, J2c = np.clip(I2, 0, H - 1), np.clip(J2, 0, W - 1)
        valid = inb & known & known[I2c, J2c]
        pair_inf = valid & (informative | informative[I2c, J2c])
        support = int(pair_inf.sum())
        if support < 0.25 * n_inf or support < 4:
            continue
        agree = int((pair_inf & (grid == grid[I2c, J2c])).sum())
        if agree >= 0.8 * support:
            out.append((name, I2c, J2c, inb, agree, support))
    if len(_CACHE) > 2000:
        _CACHE.clear()
    _CACHE[key] = out
    return out


def accepted_hypotheses(grid, known, tau=1.0, kinds=None):
    """Return [(name, I2, J2, inb, weight)] for symmetries consistent with the known cells."""
    return [(n, I2, J2, inb, float(a)) for n, I2, J2, inb, a, s in _stats(grid, known)
            if a >= tau * s and (kinds is None or n[0][0] in kinds)]


def complete(grid, unknown, tau=1.0, kinds=None, repair=False, rounds=6):
    """Fill `unknown` cells (and, if repair, overwrite outvoted cells) using accepted symmetries."""
    g = grid.copy()
    known = ~unknown
    hyps = accepted_hypotheses(g, known, tau=tau, kinds=kinds)
    if not hyps:
        return None
    for _ in range(rounds):
        votes = np.zeros((10,) + g.shape)
        for _, I2, J2, inb, w in hyps:
            ok = inb & known[I2, J2]
            src = g[I2, J2]
            for c in np.unique(src[ok]):
                votes[c] += w * (ok & (src == c))
        has = votes.sum(0) > 0
        best = votes.argmax(0)
        fill = unknown & ~known & has
        changed = False
        if fill.any():
            g[fill] = best[fill]
            known = known | fill
            changed = True
        if repair:
            tot = votes.sum(0)
            strong = known & has & (best != g) & (votes.max(0) > 0.5 * tot)
            if strong.any():
                g[strong] = best[strong]
                changed = True
        if not changed:
            break
    if (unknown & ~known).any():
        return None
    return g


def _d8(a, k):
    a = a.T if k >= 4 else a
    return np.rot90(a, k % 4)


def local_complete(grid, unknown, ring=3, delta=0.08, min_ctx=12):
    """Fill `unknown` from the grid's own self-similar parts: hypotheses are (D8 pose, translation) of the
    grid relative to itself, scored only on the observed context ring around the hole; the hypotheses
    within `delta` of the best context agreement vote on every hidden cell."""
    from scipy.ndimage import binary_dilation

    H, W = grid.shape
    ctx = binary_dilation(unknown, iterations=ring) & ~unknown
    ys, xs = np.nonzero(ctx | unknown)
    hyps = []
    for k in range(8):
        TX, TM = _d8(grid, k), _d8(unknown, k)
        h, w = TX.shape
        for dy in range(-h + 1, h):
            yy = ys + dy
            iny = (yy >= 0) & (yy < h)
            if iny.sum() < 0.5 * len(ys):
                continue
            for dx in range(-w + 1, w):
                if k == 0 and dy == 0 and dx == 0:
                    continue
                xx = xs + dx
                inb = iny & (xx >= 0) & (xx < w)
                if inb.sum() < 0.5 * len(ys):
                    continue
                oy, ox, yy2, xx2 = ys[inb], xs[inb], yy[inb], xx[inb]
                src_known = ~TM[yy2, xx2]
                c = ctx[oy, ox] & src_known
                n = c.sum()
                if n < min_ctx:
                    continue
                agree = (grid[oy, ox][c] == TX[yy2, xx2][c]).mean()
                m = unknown[oy, ox] & src_known
                if m.any():
                    hyps.append((agree, oy[m], ox[m], TX[yy2[m], xx2[m]]))
    if not hyps:
        return None
    best = max(h[0] for h in hyps)
    if best < 0.75:
        return None
    votes = np.zeros((10, H, W))
    for agree, oy, ox, vals in hyps:
        if agree >= best - delta:
            np.add.at(votes, (vals, oy, ox), agree ** 4)
    g = grid.copy()
    has = votes.sum(0) > 0
    if (unknown & ~has).any():
        return None
    g[unknown] = votes.argmax(0)[unknown]
    return g


def _solid_rect_colors(grid):
    """Colours whose cells form exactly one solid rectangle (typical occluder)."""
    out = []
    for c in np.unique(grid):
        ys, xs = np.nonzero(grid == c)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        if len(ys) == (y1 - y0 + 1) * (x1 - x0 + 1) and len(ys) < grid.size:
            out.append((int(c), (y0, y1 + 1, x0, x1 + 1)))
    return out


def _mask_candidates(inp, fixed_color=None):
    rects = _solid_rect_colors(inp)
    if fixed_color is not None:
        return [(c, r) for c, r in rects if c == fixed_color]
    return rects


CONFIGS = [
    dict(tau=1.0, kinds=None, repair=False),
    dict(tau=1.0, kinds={"m"}, repair=False),
    dict(tau=1.0, kinds={"r"}, repair=False),
    dict(tau=1.0, kinds={"t"}, repair=False),
    dict(tau=1.0, kinds=None, repair=False, local=True),
    dict(tau=0.9, kinds=None, repair=True),
    dict(tau=0.8, kinds=None, repair=True),
]


def _predict(inp, mode, mask_rule, cfg):
    kw = {k: v for k, v in cfg.items() if k != "local"}
    if mode == "repair":
        if cfg.get("local"):
            return None
        return complete(inp, np.zeros_like(inp, dtype=bool), **kw)
    cands = _mask_candidates(inp, mask_rule)
    if len(cands) != 1:
        return None
    c, (y0, y1, x0, x1) = cands[0]
    unknown = inp == c
    if cfg.get("local"):
        g = local_complete(inp, unknown)
    else:
        g = complete(inp, unknown, **kw)
    if g is None:
        return None
    return g if mode == "fill" else g[y0:y1, x0:x1]


def candidates(task):
    """Every configuration that reproduces all demos, with its test predictions. Evidence = number of demos."""
    pairs = task["train"]
    modes = []
    if all(i.shape == o.shape for i, o in pairs):
        modes += ["fill", "repair"]
    modes.append("crop")
    colors = None
    for i, _ in pairs:
        cs = {c for c, _ in _solid_rect_colors(i)}
        colors = cs if colors is None else colors & cs
    mask_rules = [c for c in sorted(colors or [])] + [None]
    out = []
    for mode in modes:
        for mask_rule in ([None] if mode == "repair" else mask_rules):
            for cfg in CONFIGS:
                if mode != "repair" and cfg["repair"]:
                    continue
                if any(not np.array_equal(p, o) if (p := _predict(i, mode, mask_rule, cfg)) is not None
                       and p.shape == o.shape else True for i, o in pairs):
                    continue
                preds = [_predict(t, mode, mask_rule, cfg) for t in task["test"]]
                if all(p is not None for p in preds):
                    out.append(dict(lm="self-model", hyp=f"{mode}/{mask_rule}/{cfg}", preds=preds, evidence=1.0))
                if len(out) >= 4:
                    return out
    return out


def solve(task):
    from arcmonty.vote import attempts_from
    return attempts_from(task, candidates(task))
