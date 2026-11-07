"""SPIKE, not a system. One generic feature-at-location column, for a feasibility check only.

The same class is instantiated with different sensors; nothing else differs between levels:
  color   cell colour                               (morphology column)
  mask    background / not background               (morphology without colour: "features only add")
  obj     child object ID + location in the child's canonical D8 frame  (object ID as a feature, one level up)
  objc    the same, with the child's colour in its ID
  objn    how many objects in the scene share this child's shape + location in the child's frame
          (a 1-D frame traversed once per object: counting as path integration)

Movement: a hypothesis (stored location, pose) is extended ring by ring. On exact data, sequential evidence over
that path is the same as asking for the longest context whose hash matches, so the rings are hashed in advance
(iterated neighbourhood hashing; equal balls give equal hashes). This is the batch form of the sequential filter.

The model stores, at each stored context, the next sensation: what the sensor reads after moving from the input
layer to the output layer there. The next sensation is stored in every form that explains it: SAME, an absolute
colour, or a displacement (the colour at p + d in the input, a behaviour in the column's own frame).
"""
import zlib

import numpy as np
from scipy.ndimage import label

SAME = 10
PTR = 100
P = 3
OUT = np.uint64(0xDEADBEEFCAFEF00D)
_S8 = np.ones((3, 3), int)
RMAX = 8
_C1, _C2, _C3 = np.uint64(0xFF51AFD7ED558CCD), np.uint64(0x9E3779B97F4A7C15), np.uint64(0xC4CEB9FE1A85EC53)
_POINTERS = sorted([(dy, dx) for dy in range(-P, P + 1) for dx in range(-P, P + 1) if (dy, dx) != (0, 0)],
                   key=lambda d: (abs(d[0]) + abs(d[1]), d))


def d8(a, k):
    a = np.rot90(a, k % 4)
    return np.fliplr(a) if k >= 4 else a


def d8_inv(a, k):
    if k >= 4:
        a = np.fliplr(a)
    return np.rot90(a, -(k % 4))


def _mix(a, b):
    a = np.asarray(a, dtype=np.uint64)
    with np.errstate(over="ignore"):
        x = (a ^ b) * _C1
        x = x ^ (x >> np.uint64(33))
        x = (x + _C2) * _C3
    return x ^ (x >> np.uint64(29))


def rings(init, rmax=RMAX):
    """labels[r][y, x] = hash of everything within Manhattan distance r of (y, x); off-grid is a feature."""
    out = [_mix(init.astype(np.uint64), np.uint64(11))]
    for _ in range(rmax):
        L = out[-1]
        Q = np.pad(L, 1, constant_values=OUT)
        H = _mix(L, np.uint64(3))
        for n in (Q[:-2, 1:-1], Q[2:, 1:-1], Q[1:-1, :-2], Q[1:-1, 2:]):  # fixed order: oriented, pose comes from D8
            H = _mix(H, n)
        out.append(H)
    return out


def background(g):
    v, c = np.unique(g, return_counts=True)
    return int(v[np.argmax(c)])


def objects(g):
    bg = background(g)
    res = []
    for c in np.unique(g):
        if int(c) == bg:
            continue
        lab, n = label(g == c, structure=_S8)
        for i in range(1, n + 1):
            res.append(lab == i)
    return res


def canonical(mask):
    ys, xs = np.nonzero(mask)
    y0, x0 = int(ys.min()), int(xs.min())
    m = mask[y0:ys.max() + 1, x0:xs.max() + 1]
    best = None
    for k in range(8):
        t = d8(m, k)
        enc = (t.shape, t.tobytes())
        if best is None or enc < best[0]:
            best = (enc, k)
    k = best[1]
    t = d8(m, k)
    loc = d8_inv(np.arange(t.size).reshape(t.shape), k)
    sid = np.uint64(zlib.crc32(repr(best[0][0]).encode() + best[0][1]))
    return sid, loc, y0, x0


def child_sensor(g, kind):
    objs = objects(g)
    if not objs or len(objs) > 80:
        return None
    init = np.full(g.shape, np.uint64(7), dtype=np.uint64)
    ids = [(m, *canonical(m)) for m in objs]
    counts = {}
    for _, sid, *_ in ids:
        counts[int(sid)] = counts.get(int(sid), 0) + 1
    for m, sid, loc, y0, x0 in ids:
        ys, xs = np.nonzero(m)
        l = loc[ys - y0, xs - x0].astype(np.uint64)
        if kind == "obj":
            base = sid
        elif kind == "objc":
            base = _mix(sid, np.uint64(int(g[ys[0], xs[0]]) + 100))
        elif kind == "objn":
            base = np.uint64(min(counts[int(sid)], 6) + 1000)
        else:
            raise ValueError(kind)
        init[ys, xs] = _mix(_mix(base, np.uint64(5)), l)
    return init


def near_sensor(g, kind):
    """Each cell's location in the canonical frame of its nearest object, with that object's ID (or none).
    This is the theory's data structure: features stored at locations in an object's own reference frame."""
    from scipy.ndimage import distance_transform_cdt
    objs = objects(g)
    if not objs or len(objs) > 60:
        return None
    h, w = g.shape
    dists = np.stack([distance_transform_cdt(~m, metric="chessboard") for m in objs])
    near = dists.argmin(axis=0)
    second = np.sort(dists, axis=0)[1] if len(objs) > 1 else np.full(g.shape, 10 ** 6)
    tie = (dists.min(axis=0) == second)
    init = np.zeros(g.shape, dtype=np.uint64)
    yy, xx = np.mgrid[0:h, 0:w]
    for i, m in enumerate(objs):
        ys, xs = np.nonzero(m)
        y0, x0, y1, x1 = int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max())
        patch = m[y0:y1 + 1, x0:x1 + 1]
        best = None
        for k in range(8):
            t = d8(patch, k)
            enc = (t.shape, t.tobytes())
            if best is None or enc < best[0]:
                best = (enc, k)
        k = best[1]
        sid = np.uint64(zlib.crc32(repr(best[0][0]).encode() + best[0][1]))
        col = np.uint64(int(g[ys[0], xs[0]]) + 100)
        base = {"near": np.uint64(1), "nearc": col, "nears": sid, "nearsc": _mix(sid, col)}[kind]
        sel = near == i
        # location relative to the object, in its canonical pose; (u, v) can lie outside the object
        u, v = yy[sel] - y0, xx[sel] - x0
        H, W = y1 - y0, x1 - x0
        for _ in range(k % 4):  # rot90 counterclockwise: (u, v) -> (H' - v, u)
            u, v, H, W = W - v, u, W, H
        if k >= 4:
            v = W - v
        loc = (u.astype(np.int64) + 64) * 256 + (v.astype(np.int64) + 64)
        init[sel] = _mix(_mix(base, np.uint64(9)), loc.astype(np.uint64))
    init[tie] = np.uint64(13)
    return init


def sensor(g, kind):
    if kind.startswith("near"):
        return near_sensor(g, kind)
    if kind == "color":
        return g.astype(np.uint64) + np.uint64(1)
    if kind == "mask":
        return (g != background(g)).astype(np.uint64) + np.uint64(20)
    return child_sensor(g, kind)


MIRROR = 50  # 50..: the colour at this cell's image under a pose of the whole grid


def _pose_images(inp):
    res = [np.flipud(inp), np.fliplr(inp), np.rot90(inp, 2)]
    if inp.shape[0] == inp.shape[1]:
        res += [inp.T, np.rot90(inp, 2).T, np.rot90(inp, 1), np.rot90(inp, 3)]
    return res


def explanations(inp, out):
    """(encoding, boolean map of cells it explains) for every form of the next sensation."""
    res = [(SAME, inp == out)]
    for c in np.unique(out):
        res.append((int(c), out == c))
    for i, im in enumerate(_pose_images(inp)):
        m = im == out
        if m.any():
            res.append((MIRROR + i, m))
    h, w = inp.shape
    for i, (dy, dx) in enumerate(_POINTERS):
        src = np.full((h, w), -1, dtype=np.int16)
        y0, y1 = max(0, dy), min(h, h + dy)
        x0, x1 = max(0, dx), min(w, w + dx)
        if y1 <= y0 or x1 <= x0:
            continue
        src[y0 - dy:y1 - dy, x0 - dx:x1 - dx] = inp[y0:y1, x0:x1]
        m = src == out
        if m.any():
            res.append((PTR + i, m))
    return res


def demo_table(labels, inp, out):
    """One stored demo: for each depth, context hash -> {encoding: count}, plus '-n' = occurrences."""
    tabs = []
    expl = explanations(inp, out)
    for L in labels:
        t = {}
        u, c = np.unique(L, return_counts=True)
        for lb, n in zip(u.tolist(), c.tolist()):
            t[lb] = {-1: n}
        for e, m in expl:
            u, c = np.unique(L[m], return_counts=True)
            for lb, n in zip(u.tolist(), c.tolist()):
                t[lb][e] = n
        tabs.append(t)
    return tabs


def choose(hits):
    """The next sensation for one context, given the demos that stored it: an encoding that explains every
    occurrence, preferring SAME, then colour, then the shortest displacement; else a strict majority; else None."""
    tot, merged = 0, {}
    for h in hits:
        for e, c in h.items():
            if e == -1:
                tot += c
            else:
                merged[e] = merged.get(e, 0) + c
    full = [e for e, c in merged.items() if c == tot]
    if full:
        return min(full, key=lambda e: (0 if e == SAME else 1 if e < 10 else 2 if e >= PTR else 3, e))
    if not merged:
        return None
    best = sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(best) == 1 or best[0][1] > best[1][1]:
        return best[0][0]
    return None


def apply_encoding(g, nexts):
    """Decode next sensations in the frame of g; -1 keeps the input."""
    res = g.astype(np.int16).copy()
    m = (nexts >= 0) & (nexts < 10)
    res[m] = nexts[m]
    h, w = g.shape
    if ((nexts >= MIRROR) & (nexts < PTR)).any():
        for i, im in enumerate(_pose_images(g)):
            m = nexts == MIRROR + i
            res[m] = im[m]
    for e in np.unique(nexts[nexts >= PTR]):
        dy, dx = _POINTERS[int(e) - PTR]
        ys, xs = np.nonzero(nexts == e)
        sy, sx = ys + dy, xs + dx
        ok = (sy >= 0) & (sy < h) & (sx >= 0) & (sx < w)
        res[ys[ok], xs[ok]] = g[sy[ok], sx[ok]]
    return res


def predict(tables, g, labels_per_pose, poses, rcap):
    """tables: demo tables to use. Longest matching context wins, per cell, across poses (most evidence)."""
    best_depth = np.full(g.shape, -1, dtype=np.int16)
    votes = []
    for k, labels in zip(poses, labels_per_pose):
        T = d8(g, k)
        nexts = np.full(T.shape, -1, dtype=np.int32)
        depth = np.full(T.shape, -1, dtype=np.int16)
        todo = np.ones(T.shape, bool)
        for r in range(rcap, -1, -1):
            if not todo.any():
                break
            ys, xs = np.nonzero(todo)
            vals = labels[r][ys, xs]
            u, inv = np.unique(vals, return_inverse=True)
            enc = np.full(len(u), -2, dtype=np.int32)
            for i, lb in enumerate(u.tolist()):
                hits = [t[r][lb] for t in tables if lb in t[r]]
                if hits:
                    c = choose(hits)
                    enc[i] = -1 if c is None else c
            e = enc[inv]
            hit = e != -2
            nexts[ys[hit], xs[hit]] = e[hit]
            depth[ys[hit], xs[hit]] = r
            todo[ys[hit], xs[hit]] = False
        res = d8_inv(apply_encoding(T, nexts), k)
        votes.append((res, d8_inv(depth, k)))
    if len(votes) == 1:
        return votes[0][0].astype(np.int8)
    D = np.stack([d for _, d in votes])
    R = np.stack([r for r, _ in votes])
    top = D.max(axis=0)
    out = g.astype(np.int16).copy()
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            cand = R[D[:, y, x] == top[y, x], y, x]
            vals, cnt = np.unique(cand, return_counts=True)
            if (cnt == cnt.max()).sum() == 1:
                out[y, x] = vals[cnt.argmax()]
    return out.astype(np.int8)


# --- Counted evidence (Monty's form): a stored location gains evidence for every feature that matches along the
# path; a mismatch earns nothing. No all-or-nothing context. Same column, same sensors, same next sensations.

def offsets(R):
    o = [(dy, dx) for dy in range(-R, R + 1) for dx in range(-R, R + 1) if abs(dy) + abs(dx) <= R]
    w = np.array([1.0 / (1 + abs(dy) + abs(dx)) for dy, dx in o])
    return o, w


def windows(init, R):
    """(cells, path steps) array of sensed labels along the path around each cell; off-grid is one more feature."""
    h, w = init.shape
    Q = np.pad(init.astype(np.uint64), R, constant_values=OUT)
    o, wt = offsets(R)
    W = np.stack([Q[R + dy:R + dy + h, R + dx:R + dx + w].ravel() for dy, dx in o], axis=1)
    return W, wt


def _unique_rows(W):
    """Unique rows by a 64-bit row hash (much faster than np.unique(axis=0); collisions are negligible here)."""
    h = np.zeros(W.shape[0], dtype=np.uint64)
    for j in range(W.shape[1]):
        h = _mix(h, W[:, j])
    _, first, inv = np.unique(h, return_index=True, return_inverse=True)
    return W[first], inv.ravel()


def store(init, inp, out, R):
    """One demo: unique contexts and, for each, counts of every explanation of the next sensation."""
    W, wt = windows(init, R)
    U, inv = _unique_rows(W)
    tables = [{-1: 0} for _ in range(len(U))]
    for i, n in zip(*np.unique(inv, return_counts=True)):
        tables[int(i)][-1] = int(n)
    for e, m in explanations(inp, out):
        idx, cnt = np.unique(inv[m.ravel()], return_counts=True)
        for i, n in zip(idx.tolist(), cnt.tolist()):
            tables[i][e] = n
    return U, tables, wt


def predict_counted(stored, g, inits, poses, R):
    """stored: list of store() results. For each query context, the stored contexts with most evidence decide."""
    U = np.concatenate([s[0] for s in stored])
    T_ = [t for s in stored for t in s[1]]
    wt = stored[0][2]
    votes, scores = [], []
    for k, init in zip(poses, inits):
        T = d8(g, k)
        W, _ = windows(init, R)
        Q, inv = _unique_rows(W)
        sim = np.zeros((len(Q), len(U)))
        for j in range(Q.shape[1]):
            sim += (Q[:, j][:, None] == U[:, j][None, :]) * wt[j]
        top = sim.max(axis=1)
        enc = np.full(len(Q), -1, dtype=np.int32)
        for i in range(len(Q)):
            hits = [T_[s] for s in np.nonzero(sim[i] >= top[i] - 1e-9)[0].tolist()]
            c = choose(hits)
            enc[i] = -1 if c is None else c
        nexts = enc[inv].reshape(T.shape)
        votes.append(d8_inv(apply_encoding(T, nexts), k))
        scores.append(d8_inv(top[inv].reshape(T.shape), k))
    if len(votes) == 1:
        return votes[0].astype(np.int8)
    S, V = np.stack(scores), np.stack(votes)
    best = S.max(axis=0)
    out = g.astype(np.int16).copy()
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            cand = V[S[:, y, x] >= best[y, x] - 1e-9, y, x]
            vals, cnt = np.unique(cand, return_counts=True)
            if (cnt == cnt.max()).sum() == 1:
                out[y, x] = vals[cnt.argmax()]
    return out.astype(np.int8)
