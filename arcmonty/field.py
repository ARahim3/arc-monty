"""Field learning module: output colour as a function of location in a reference frame anchored on a marker.

TBT: features are stored at locations in a reference frame; here the frame is anchored on a unique marker cell and
the location code is a scalar of the displacement (row, column, ring, Manhattan or diagonal index), optionally
periodic (mod k), like a grid-cell module, which lets the model extrapolate beyond the locations seen in the demos.
Parameters (anchor rule, code, period, write mask) are fitted on all demos; confidence = honest leave-one-out.
"""
import numpy as np

CODES = {
    "row": lambda dy, dx: dy, "col": lambda dy, dx: dx, "absrow": lambda dy, dx: np.abs(dy),
    "abscol": lambda dy, dx: np.abs(dx), "ring": lambda dy, dx: np.maximum(np.abs(dy), np.abs(dx)),
    "manhattan": lambda dy, dx: np.abs(dy) + np.abs(dx), "diag": lambda dy, dx: dx - dy,
    "anti": lambda dy, dx: dx + dy, "absdiag": lambda dy, dx: np.abs(dx - dy), "absanti": lambda dy, dx: np.abs(dx + dy),
}
PERIODS = (None, 2, 3, 4, 5, 6, 7, 8, 9, 10)


def _anchor(grid, color):
    if color == "uniq":  # the single cell whose colour occurs exactly once (any colour)
        vals, cnt = np.unique(grid, return_counts=True)
        if (cnt == 1).sum() != 1:
            return None
        color = int(vals[cnt == 1][0])
    ys, xs = np.nonzero(grid == color)
    return (int(ys[0]), int(xs[0])) if len(ys) == 1 else None


def _codes(grid, anchor, code, period):
    H, W = grid.shape
    Y, X = np.indices((H, W))
    c = CODES[code](Y - anchor[0], X - anchor[1])
    return c % period if period else c


def _learn(pairs, p):
    """abs: table code -> colour.  cycle: a cyclic colour order S (length = period), entered at the anchor's colour."""
    table = {}
    for i, o in pairs:
        a = _anchor(i, p["anchor"])
        if a is None:
            return None
        c = _codes(i, a, p["code"], p["period"])
        m = np.ones(i.shape, dtype=bool) if p["write"] == "all" else (i == p["bgc"])
        if p["cmode"] == "cycle":
            if not p["period"]:
                return None
            start = int(i[a])
            local = {}
            for v, col in zip(c[m].tolist(), o[m].tolist()):
                if local.setdefault(v, col) != col:
                    return None
            if local.get(0) != start or len(local) != p["period"]:
                return None
            cyc = [local[k] for k in range(p["period"])]
            if len(set(cyc)) != len(cyc):
                return None
            if table:  # same cycle up to rotation
                ref = table["cycle"]
                if set(ref) != set(cyc):
                    return None
                r = ref.index(start)
                if ref[r:] + ref[:r] != cyc:
                    return None
            else:
                table["cycle"] = cyc
        else:
            for v, col in zip(c[m].tolist(), o[m].tolist()):
                if table.setdefault(v, col) != col:
                    return None
        if p["write"] != "all" and not np.array_equal(i[~m], o[~m]):
            return None
    return table


def _predict(table, grid, p):
    a = _anchor(grid, p["anchor"])
    if a is None:
        return None
    c = _codes(grid, a, p["code"], p["period"])
    m = np.ones(grid.shape, dtype=bool) if p["write"] == "all" else (grid == p["bgc"])
    out = grid.copy()
    vals = c[m].tolist()
    if p["cmode"] == "cycle":
        cyc = table["cycle"]
        start = int(grid[a])
        if start not in cyc:
            return None
        r = cyc.index(start)
        out[m] = [cyc[(r + v) % len(cyc)] for v in vals]
        return out
    if any(v not in table for v in vals):
        return None  # location never observed and not covered by a periodic code: abstain
    out[m] = [table[v] for v in vals]
    return out


def _hypotheses(pairs):
    uniq = None  # colours that occur exactly once in every demo input: anchor candidates
    for i, _ in pairs:
        vals, cnt = np.unique(i, return_counts=True)
        u = set(vals[cnt == 1].tolist())
        uniq = u if uniq is None else uniq & u
    bgs = None
    for i, _ in pairs:
        vals, cnt = np.unique(i, return_counts=True)
        b = {int(vals[cnt.argmax()])}
        bgs = b if bgs is None else bgs & b
    for anchor in sorted(uniq or [], key=str) + ["uniq"]:
        for write in ("bg", "all"):
            for code in CODES:
                for period in PERIODS:
                    for cmode in ("abs", "cycle"):
                        if cmode == "cycle" and not period:
                            continue
                        for bgc in (sorted(bgs or []) if write == "bg" else [None]):
                            yield dict(anchor=anchor, write=write, code=code, period=period, cmode=cmode, bgc=bgc)


def candidates(task):
    pairs = task["train"]
    if not all(i.shape == o.shape for i, o in pairs) or all(np.array_equal(i, o) for i, o in pairs):
        return []
    hyps, fits = [], []
    for p in _hypotheses(pairs):
        row = []
        for j, (i, o) in enumerate(pairs):
            t = _learn([pairs[j]], p)
            q = None if t is None else _predict(t, i, p)
            row.append(q is not None and np.array_equal(q, o))
        if not all(row):
            continue
        hyps.append(p)
        fits.append(row)
    out = []
    n = len(pairs)
    for p in hyps:
        table = _learn(pairs, p)
        if table is None:
            continue
        preds = [_predict(table, t, p) for t in task["test"]]
        if any(q is None for q in preds):
            continue
        loo = 0
        for j in range(n):
            t = _learn(pairs[:j] + pairs[j + 1:], p)
            q = None if t is None else _predict(t, pairs[j][0], p)
            loo += q is not None and np.array_equal(q, pairs[j][1])
        out.append(dict(lm="field", hyp=str(p), preds=preds, evidence=loo / n))
        if len(out) >= 4:
            break
    return out
