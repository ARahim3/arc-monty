"""One column, repeated. Not Monty, and no Monty code runs. Nothing in this file knows what kind of data it is on.

A column learns transitions (x, y) under a motor command: at each sensed context it counts what was sensed next, in
every form that explains it (unchanged, an absolute colour, a displacement within the input). It predicts one rule only:
for each cell, the stored contexts under that command with the most counted evidence along a path decide. Columns differ
in one thing only, their sensor (and how far along the path they read). A population ranks its columns by how well each
predicted transitions it had not learned, and answers with the best ones.
"""
import zlib

import numpy as np
from scipy.ndimage import distance_transform_cdt, label

_C1, _C2, _C3 = np.uint64(0xFF51AFD7ED558CCD), np.uint64(0x9E3779B97F4A7C15), np.uint64(0xC4CEB9FE1A85EC53)
OFFGRID = np.uint64(0xDEADBEEF)
_S8 = np.ones((3, 3), int)
_MEMO = {}


def _memo(key, make):
    if key not in _MEMO:
        if len(_MEMO) > 1500:
            _MEMO.clear()
        _MEMO[key] = make()
    return _MEMO[key]


def mix(a, b):
    a = np.asarray(a, dtype=np.uint64)
    with np.errstate(over="ignore"):
        x = (a ^ b) * _C1
        x = x ^ (x >> np.uint64(33))
        x = (x + _C2) * _C3
    return x ^ (x >> np.uint64(29))


def d8(a, k):
    a = np.rot90(a, k % 4)
    return np.fliplr(a) if k >= 4 else a


def d8_inv(a, k):
    return np.rot90(np.fliplr(a) if k >= 4 else a, -(k % 4))


# ------------------------------------------------------------------ sensors: the only thing that differs between columns
def background(g):
    v, c = np.unique(g, return_counts=True)
    return int(v[np.argmax(c)])


def objects(g):
    bg, res = background(g), []
    for c in np.unique(g):
        if int(c) != bg:
            lab, n = label(g == c, structure=_S8)
            res += [lab == i for i in range(1, n + 1)]
    return res


def canonical(patch):
    """The D8 pose that gives this shape its canonical encoding, and the shape's ID."""
    best = min((((t := d8(patch, k)).shape, t.tobytes()), k) for k in range(8))
    return best[1], np.uint64(zlib.crc32(repr(best[0][0]).encode() + best[0][1]))


def child_sensor(g, kind):
    """Each object's cells read as: child ID (shape; with colour for objc; how many share the shape for objn) + location
    in the child's canonical frame. Cells outside objects read the same blank."""
    objs = objects(g)
    if not objs or len(objs) > 80:
        return None
    init, ids, counts = np.full(g.shape, np.uint64(7), dtype=np.uint64), [], {}
    for m in objs:
        ys, xs = np.nonzero(m)
        y0, x0 = int(ys.min()), int(xs.min())
        p = m[y0:ys.max() + 1, x0:xs.max() + 1]
        k, sid = canonical(p)
        loc = d8_inv(np.arange(p.size).reshape(d8(p, k).shape), k)
        ids.append((ys, xs, y0, x0, sid, loc))
        counts[int(sid)] = counts.get(int(sid), 0) + 1
    for ys, xs, y0, x0, sid, loc in ids:
        base = dict(obj=sid, objc=mix(sid, np.uint64(int(g[ys[0], xs[0]]) + 100)),
                    objn=np.uint64(min(counts[int(sid)], 6) + 1000))[kind]
        init[ys, xs] = mix(mix(base, np.uint64(5)), loc[ys - y0, xs - x0].astype(np.uint64))
    return init


def near_sensor(g, kind):
    """Each cell's location in the canonical frame of its nearest object, with that object's ID (or none)."""
    objs = objects(g)
    if not objs or len(objs) > 60:
        return None
    dists = np.stack([distance_transform_cdt(~m, metric="chessboard") for m in objs])
    near = dists.argmin(axis=0)
    second = np.sort(dists, axis=0)[1] if len(objs) > 1 else np.full(g.shape, 10 ** 6)
    init = np.zeros(g.shape, dtype=np.uint64)
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    for i, m in enumerate(objs):
        ys, xs = np.nonzero(m)
        y0, x0, y1, x1 = int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max())
        k, sid = canonical(m[y0:y1 + 1, x0:x1 + 1])
        col = np.uint64(int(g[ys[0], xs[0]]) + 100)
        base = dict(near=np.uint64(1), nearc=col, nears=sid, nearsc=mix(sid, col))[kind]
        sel = near == i
        u, v, H, W = yy[sel] - y0, xx[sel] - x0, y1 - y0, x1 - x0
        for _ in range(k % 4):  # rot90 counterclockwise: (u, v) -> (W - v, u); locations may lie outside the object
            u, v, H, W = W - v, u, W, H
        if k >= 4:
            v = W - v
        loc = (u.astype(np.int64) + 64) * 256 + (v.astype(np.int64) + 64)
        init[sel] = mix(mix(base, np.uint64(9)), loc.astype(np.uint64))
    init[dists.min(axis=0) == second] = np.uint64(13)
    return init


def relative(shape, y, x):
    """Location relative to a point (a click, or where something last changed) out to 8 cells; beyond that, one label."""
    dy, dx = np.mgrid[0:shape[0], 0:shape[1]]
    dy, dx = np.round(dy - y).astype(np.int64), np.round(dx - x).astype(np.int64)
    return np.where((np.abs(dy) <= 8) & (np.abs(dx) <= 8), (dy + 8) * 17 + dx + 8, 999).astype(np.uint64)


def sensor(g, part):
    if part == "color":
        return g.astype(np.uint64) + np.uint64(1)
    if part == "mask":
        return (g != background(g)).astype(np.uint64) + np.uint64(20)
    return near_sensor(g, part) if part.startswith("near") else child_sensor(g, part)


COLOURED = ("color", "objc", "nearc", "nearsc")  # sensors that read colour; the others are colour-free, clicks included


# ------------------------------------------------------------------ forms of the next sensation
SAME, COLOUR, POINTER = 0, 1, 17  # colours 0..15 occupy 1..16
_POINTERS = sorted({(dy, dx) for dy in range(-3, 4) for dx in range(-3, 4) if (dy, dx) != (0, 0)} |
                   {p for d in (4, 5, 6, 8) for p in ((-d, 0), (d, 0), (0, -d), (0, d))},
                   key=lambda d: (abs(d[0]) + abs(d[1]), d))
POSE = POINTER + len(_POINTERS)
N_FORMS = POSE + 7


def _poses(x):
    res = [np.flipud(x), np.fliplr(x), np.rot90(x, 2)]
    return res + [x.T, np.rot90(x, 2).T, np.rot90(x, 1), np.rot90(x, 3)] if x.shape[0] == x.shape[1] else res


def _shifted(x, dy, dx):
    """The input read at (y + dy, x + dx) for every cell; -1 off the grid."""
    h, w = x.shape
    src = np.full((h, w), -1, dtype=np.int16)
    y0, y1, x0, x1 = max(0, dy), min(h, h + dy), max(0, dx), min(w, w + dx)
    if y1 > y0 and x1 > x0:
        src[y0 - dy:y1 - dy, x0 - dx:x1 - dx] = x[y0:y1, x0:x1]
    return src


def explain(x, y, displacement=True):
    """(cells, forms) boolean: which forms explain each cell's next sensation."""
    E = np.zeros((x.size, N_FORMS), dtype=bool)
    E[:, SAME] = (x == y).ravel()
    for c in np.unique(y).tolist():
        E[:, COLOUR + c] = (y == c).ravel()
    if displacement:
        for i, d in enumerate(_POINTERS):
            E[:, POINTER + i] = (_shifted(x, *d) == y).ravel()
        for i, im in enumerate(_poses(x)):
            E[:, POSE + i] = (im == y).ravel()
    return E


def decode(x, enc):
    """The next frame from each cell's chosen form; -1 (no answer) and SAME keep the input."""
    out = x.astype(np.int16).copy()
    m = (enc >= COLOUR) & (enc < POINTER)
    out[m] = enc[m] - COLOUR
    if (enc >= POSE).any():
        for i, im in enumerate(_poses(x)):
            m = enc == POSE + i
            out[m] = im[m]
    for e in np.unique(enc[(enc >= POINTER) & (enc < POSE)]).tolist():
        m = enc == e
        src = _shifted(x, *_POINTERS[e - POINTER])
        m &= src >= 0
        out[m] = src[m]
    return out.astype(np.int8)


def choose(C, tot):
    """One context's next sensation: the first form (SAME, colour, shortest displacement) that explains every occurrence,
    else a strict plurality, else no answer. C: (contexts, forms), tot: occurrences."""
    full = C == tot[:, None]
    enc = np.where(full.any(axis=1), full.argmax(axis=1), -1)
    for i in np.nonzero(enc < 0)[0].tolist():
        top = np.partition(C[i], -2)[-2:]
        if top[1] > top[0]:
            enc[i] = int(C[i].argmax())
    return enc


# ------------------------------------------------------------------ the column
def path(reach):
    """Offsets along the path out to a reach, nearest first, and the evidence each is worth."""
    o = sorted(((dy, dx) for dy in range(-reach, reach + 1) for dx in range(-reach, reach + 1)
                if abs(dy) + abs(dx) <= reach), key=lambda d: (abs(d[0]) + abs(d[1]), d))
    return o, np.array([1.0 / (1 + abs(dy) + abs(dx)) for dy, dx in o])


def _contexts(init, reach):
    """Unique contexts: labels along the path around each cell, a 64-bit hash of each ball around the cell (rows: contexts,
    last column: the whole context), and the cell -> context map."""
    h, w = init.shape
    o, _ = path(reach)
    Q = np.pad(init.astype(np.uint64), reach, constant_values=OFFGRID)
    W = np.stack([Q[reach + dy:reach + dy + h, reach + dx:reach + dx + w].ravel() for dy, dx in o], axis=1)
    H, balls, d = np.zeros(W.shape[0], dtype=np.uint64), [], [abs(a) + abs(b) for a, b in o] + [reach + 1]
    for j in range(W.shape[1]):
        H = mix(H, W[:, j])
        if d[j + 1] != d[j]:
            balls.append(H)
    u, first, inv = np.unique(H, return_index=True, return_inverse=True)
    return W[first].astype(np.uint32), np.stack(balls, axis=1)[first], inv.ravel()


class _Store:
    """Stored contexts under one motor command, deduplicated, with counts of every form and of occurrences."""

    def __init__(self, width, reach):
        self.n, self.index, self.noop = 0, {}, False
        self.U = np.zeros((256, width), dtype=np.uint32)
        self.C = np.zeros((256, N_FORMS), dtype=np.int32)
        self.tot = np.zeros(256, dtype=np.int32)
        self.ball = [{} for _ in range(reach)]  # stored contexts sharing each ball around the centre: speeds up the search

    def rows(self, balls, contexts):
        ids = self.find(balls)
        new = np.nonzero(ids < 0)[0]
        if len(new):
            if self.n + len(new) > len(self.U):
                cap = 2 * (self.n + len(new))
                self.U = np.resize(self.U, (cap, self.U.shape[1]))
                self.C = np.concatenate([self.C[:self.n], np.zeros((cap - self.n, N_FORMS), dtype=np.int32)])
                self.tot = np.concatenate([self.tot[:self.n], np.zeros(cap - self.n, dtype=np.int32)])
            ids[new] = np.arange(self.n, self.n + len(new))
            self.U[self.n:self.n + len(new)] = contexts[new]
            self.index.update(zip(balls[new, -1].tolist(), ids[new].tolist()))
            for r, d in enumerate(self.ball):
                for h, i in zip(balls[new, r].tolist(), ids[new].tolist()):
                    d.setdefault(h, []).append(i)
            self.n += len(new)
        return ids

    def find(self, balls):
        return np.fromiter((self.index.get(h, -1) for h in balls[:, -1].tolist()), dtype=np.int64, count=len(balls))

    def sharing(self, ball, r):
        return self.ball[r].get(int(ball[r]), ()) if r >= 0 else range(self.n)


class Column:
    def __init__(self, kind="color", reach=3, motor=True, displacement=True, frame=None, memory=None, tau=0.75, poses=1):
        self.kind, self.reach, self.motor, self.displacement = kind, reach, motor, displacement
        self.poses = range(poses)
        self.frame, self.memory, self.tau = frame, memory, tau
        o, self.w = path(reach)
        d = np.array([abs(a) + abs(b) for a, b in o])
        self.rings = [np.nonzero(d == r)[0] for r in range(reach + 1)]
        self.ring_w = [self.w[i] for i in self.rings]
        self.left = self.w.sum() - np.cumsum([r.sum() for r in self.ring_w])  # evidence still unread after each ring
        self.stores, self.last_change = {}, None

    def _resample(self, x):
        if self.frame is None:
            return x
        name, a, b = self.frame
        if name == "up":
            return np.repeat(np.repeat(x, a, 0), b, 1)
        if name == "tile":
            return np.tile(x, (a, b))
        return x[::a, ::b] if x.shape[0] % a == 0 and x.shape[1] % b == 0 else None

    def _sense(self, x, at):
        """Labels per cell, from each part of the sensor; the motor signal adds the click-centred frame."""
        init = None
        for part in self.kind.split("+"):
            if part == "moving":
                s = None if self.last_change is None else relative(x.shape, *self.last_change) + np.uint64(9000)
                if s is None:
                    continue
            else:
                key = (x.tobytes(), x.shape, part)
                s = _memo(key, lambda: sensor(x, part))
                if s is None:
                    return None
            init = s if init is None else mix(init, s)
        if at is not None and self.motor:
            init = mix(init, relative(x.shape, *at) + np.uint64(5000))
        return init

    def _context(self, x, at):
        key = (x.tobytes(), x.shape, self.kind, self.reach, at if self.motor else None,
               self.last_change if "moving" in self.kind else None)
        return _memo(key, lambda: None if (i := self._sense(x, at)) is None else _contexts(i, self.reach))

    def _key(self, x, action, at):
        """The motor command. A click also says what it landed on, as far as this sensor can tell."""
        if not self.motor:
            return 0
        if at is None:
            return action
        return 600 + (int(x[at]) if self.kind.split("+")[0] in COLOURED else int(x[at] != background(x)))

    def learn(self, x, y, action=0, at=None, ignore=None):
        x = self._resample(x)
        ctx = self._context(x, at)
        if ctx is not None:
            Q, B, inv = ctx
            s = self.stores.setdefault(self._key(x, action, at), _Store(Q.shape[1], self.reach))
            E = _memo((x.tobytes(), y.tobytes(), x.shape, self.displacement), lambda: explain(x, y, self.displacement))
            order = np.argsort(inv, kind="stable")
            starts = np.searchsorted(inv[order], np.arange(len(Q)))
            ids = s.rows(B, Q)
            s.C[ids] += np.add.reduceat(E[order].astype(np.int32), starts, axis=0)
            s.tot[ids] += np.bincount(inv, minlength=len(Q)).astype(np.int32)
            s.noop = s.noop or bool(np.array_equal(x, y))
        changed = x != y if ignore is None else (x != y) & ~ignore
        if changed.any():
            ys, xs = np.nonzero(changed)
            self.last_change = (float(ys.mean()), float(xs.mean()))

    def _search(self, s, q, ball):
        """The stored contexts with most evidence for q, among those that match the sensation here. Exact, not a heuristic:
        start from a context sharing q's longest ball; one that differs at ring k loses at least 1 / (1 + k), so if the start
        lost less than that, every winner shares ball k. The rest drop out along the path once they cannot reach the best."""
        r = next((r for r in range(self.reach - 1, -1, -1) if s.sharing(ball, r)), -1)
        if r < 0:
            return None, 0.0
        floor = float((s.U[s.sharing(ball, r)[0]] == q) @ self.w)
        lost = self.w.sum() - floor
        k = next((k for k in range(self.reach - 1, 0, -1) if 1.0 / (1 + k) > lost + 1e-9), 0)
        alive = np.fromiter(s.sharing(ball, min(k, r)), dtype=np.int64)
        sim = np.zeros(len(alive))
        for idx, wt, left in zip(self.rings, self.ring_w, self.left):
            sim = sim + ((s.U[alive[:, None], idx] == q[idx]) @ wt)
            keep = sim + left >= max(floor, sim.max()) - 1e-9
            alive, sim = alive[keep], sim[keep]
        return alive, float(sim.max())

    def encode(self, x, action=0, at=None, only=None):
        """Per cell: the chosen form (-1 = no answer) and the evidence behind it. None if the sensor reads nothing."""
        ctx = self._context(x, at)
        if ctx is None:
            return None
        Q, B, inv = ctx
        s = self.stores.get(self._key(x, action, at))
        enc, ev = np.full(len(Q), -1, dtype=np.int32), np.zeros(len(Q))
        if s is not None:
            rows = s.find(B)
            hit = rows >= 0
            enc[hit], ev[hit] = choose(s.C[rows[hit]], s.tot[rows[hit]]), self.w.sum()
            need = ~hit if only is None else ~hit & (np.bincount(inv[only.ravel()], minlength=len(Q)) > 0)
            for i in np.nonzero(need)[0].tolist():
                top, ev[i] = self._search(s, Q[i], B[i])
                if top is not None:
                    enc[i] = choose(s.C[top].sum(axis=0)[None], s.tot[top].sum(keepdims=True))[0]
        enc, ev = enc[inv].reshape(x.shape), ev[inv].reshape(x.shape)
        if self.memory is not None:  # persisting models: where this task's own evidence is weak, memory may answer
            weak = ev < self.tau * self.w.sum()
            mem = self.memory.encode(x, action, at, only=weak) if weak.any() else None
            if mem is not None:
                take = weak & (mem[1] > ev)
                enc, ev = np.where(take, mem[0], enc), np.where(take, mem[1], ev)
        return enc, ev

    def predict(self, x, action=0, at=None):
        """The predicted next frame, or None if the sensor reads nothing."""
        x = self._resample(x)
        if x is None:
            return None
        V, S = [], []
        for k in self.poses:  # the query read in each pose; per cell the poses with most evidence decide
            T, a = d8(x, k), at
            if at is not None and k:
                m = np.zeros(x.shape, bool)
                m[at] = True
                a = tuple(int(v[0]) for v in np.nonzero(d8(m, k)))
            e = self.encode(T, action, a)
            if e is None:
                return None
            V.append(d8_inv(decode(T, e[0]), k))
            S.append(d8_inv(e[1], k))
        if len(V) == 1:
            return V[0]
        V, S = np.stack(V), np.stack(S)
        cand = S >= S.max(axis=0) - 1e-9
        N = np.stack([((V == c) & cand).sum(axis=0) for c in range(16)])
        return np.where((N == N.max(axis=0)).sum(axis=0) == 1, N.argmax(axis=0), x).astype(np.int8)

    def is_answer(self, pred, x, action=0, at=None):
        """Predicting no change is an answer only if no change has been seen under this command."""
        x = self._resample(x)
        if pred is None or x is None:
            return False
        s = self.stores.get(self._key(x, action, at))
        return not np.array_equal(pred, x) or (s is not None and s.noop)


# ------------------------------------------------------------------ a population of columns
def frames_for(pairs):
    """Reference frames linking output cells to input cells: the same frame, or a generic resampling of the input."""
    if all(i.shape == o.shape for i, o in pairs):
        return [None]
    rs = {(o.shape[0] / i.shape[0], o.shape[1] / i.shape[1]) for i, o in pairs}
    if len(rs) != 1:
        return []
    ry, rx = next(iter(rs))
    if ry >= 1 and rx >= 1 and ry == int(ry) and rx == int(rx):
        return [("up", int(ry), int(rx)), ("tile", int(ry), int(rx))]
    if ry <= 1 and rx <= 1 and 1 / ry == int(1 / ry) and 1 / rx == int(1 / rx):
        return [("down", int(1 / ry), int(1 / rx))]
    return []


class Population:
    """Ordered stream: each transition is predicted before it is learned. Unordered demos: by columns that learned the
    others (``hold_out``). Either way evidence for a column is how often it predicted what it had not learned."""

    def __init__(self, configs, **common):
        self.cols = [Column(**c, **common) for c in configs]
        self.hits, self.seen = np.zeros(len(self.cols)), 0

    def predictions(self, x, action=0, at=None):
        return [c.predict(x, action, at) for c in self.cols]

    def order(self, preds, x, action=0, at=None):
        """Columns with an answer, best evidence first, ties in configuration order."""
        rank = np.argsort(-self.hits, kind="stable").tolist()
        return [i for i in rank if self.cols[i].is_answer(preds[i], x, action, at)]

    def observe(self, preds, x, y, action=0, at=None, ignore=None):
        """Score every column's prediction of this transition, then let it learn."""
        keep = None if ignore is None else ~ignore
        for i, (c, p) in enumerate(zip(self.cols, preds)):
            if p is not None and p.shape == y.shape:
                self.hits[i] += bool(np.array_equal(p, y) if keep is None else np.array_equal(p[keep], y[keep]))
            c.learn(x, y, action, at, ignore)
        self.seen += 1


def hold_out(configs, demos, queries, memo=None, library=None, **common):
    """One static task. Each column, in each frame the demos allow, gets evidence from predicting each demo after learning
    the others, then learns them all and answers the queries. Returns candidates in rank order, ties in configuration
    order. library: {column index: Column} of persisting models, or None."""
    memo = {} if memo is None else memo
    ids = tuple(id(d) for d in demos)
    by_id = dict(zip(ids, demos))
    cands = []

    def trained(i, cfg, frame, keep):
        key = (i, frame, frozenset(keep))
        if key not in memo:
            c = Column(frame=frame, memory=None if library is None else library[i], **cfg, **common)
            for k in keep:
                c.learn(*by_id[k])
            memo[key] = c
        return memo[key]

    for frame in frames_for(demos):
        for i, cfg in enumerate(configs):
            hits = 0
            if len(demos) > 1:
                for j, (x, y) in enumerate(demos):
                    p = trained(i, cfg, frame, ids[:j] + ids[j + 1:]).predict(x)
                    hits += p is not None and np.array_equal(p, y)
            c = trained(i, cfg, frame, ids)
            preds = [c.predict(q) for q in queries]
            usable = [c.is_answer(p, q) for p, q in zip(preds, queries)]
            if any(usable):
                cands.append(dict(ev=hits / len(demos), index=i, cfg=cfg, frame=frame, preds=preds, usable=usable, col=c))
    cands.sort(key=lambda c: -c["ev"])
    return cands
