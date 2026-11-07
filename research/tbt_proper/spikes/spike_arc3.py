"""SPIKE: the same column on ARC-AGI-3, from transitions already recorded (research/arc3_wm/data). Runs no game code.
Tuning-half games only (arc3_agent/v7/split.py); the 13 held-out games are never opened.

Questions:
 1. Online next-frame prediction, playfield: does a generic action-conditioned column reach the existing baselines
    (B0 no change, B1rel object-relative repeat, Monty-ARC columns) on the same transitions?
 2. Cold start: on the first use of an action in a game, does a library from the other games help (persisting models)?
 3. Hypothesis-driven action: at recorded probe states (every action tried once from one state), does the action where
    the column's top-2 hypotheses disagree most yield more surprise than a random or a least-used action?
"""
import json
import os
import random
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "research", "arc3_wm"))

import column as C  # noqa: E402
from common import load, games  # noqa: E402  (project code: loads recorded npz)
from wm2 import ui_mask  # noqa: E402

TUNING = ("lp85", "s5i5", "su15", "vc33", "g50t", "ls20", "tr87", "ar25", "bp35", "cd82", "sc25", "sk48")
RMAX = 6
SAME = 16
AX = [(dy, dx) for d in (1, 2, 3, 4, 5, 6, 8) for dy, dx in ((-d, 0), (d, 0), (0, -d), (0, d))]
PTR = 100


def explain(a, b):
    res = [(SAME, a == b)]
    for c in np.unique(b[a != b]) if (a != b).any() else []:
        res.append((int(c), b == c))
    if (a != b).any():
        h, w = a.shape
        for i, (dy, dx) in enumerate(AX):
            src = np.full((h, w), -1, dtype=np.int16)
            y0, y1 = max(0, dy), min(h, h + dy)
            x0, x1 = max(0, dx), min(w, w + dx)
            src[y0 - dy:y1 - dy, x0 - dx:x1 - dx] = a[y0:y1, x0:x1]
            res.append((PTR + i, src == b))
    return res


def decode(a, nexts):
    res = a.astype(np.int16).copy()
    m = (nexts >= 0) & (nexts < 16)
    res[m] = nexts[m]
    h, w = a.shape
    for e in np.unique(nexts[nexts >= PTR]):
        dy, dx = AX[int(e) - PTR]
        ys, xs = np.nonzero(nexts == e)
        sy, sx = ys + dy, xs + dx
        ok = (sy >= 0) & (sy < h) & (sx >= 0) & (sx < w)
        res[ys[ok], xs[ok]] = a[sy[ok], sx[ok]]
    return res


def choose(h):
    tot = h[-1]
    full = [e for e, c in h.items() if e != -1 and c == tot]
    if full:
        return min(full, key=lambda e: (0 if e == SAME else 1 if e < 16 else 2, e))
    rest = [(c, e) for e, c in h.items() if e != -1]
    if not rest:
        return None
    rest.sort(key=lambda t: (-t[0], t[1]))
    return rest[0][1] if len(rest) == 1 or rest[0][0] > rest[1][0] else None


def key_of(action, y, x, frame):
    if action == 6:
        return 600 + int(frame[y, x])
    return int(action)


def init_labels(frame, key, y, x, kind):
    base = frame.astype(np.uint64) + np.uint64(1) if kind == "color" else \
        (frame != C.background(frame)).astype(np.uint64) + np.uint64(20)
    if key >= 600:  # a click: the sensor is at the click, so cells near it are sensed in a click-centred frame
        yy, xx = np.mgrid[0:64, 0:64]
        rel = (np.clip(yy - y, -8, 8) + 8) * 17 + (np.clip(xx - x, -8, 8) + 8)
        base = C._mix(base, rel.astype(np.uint64) + np.uint64(5000))
    return C.rings(C._mix(base, np.uint64(key + 77)), RMAX)


class Col:
    def __init__(self, kind):
        self.kind = kind
        self.t = [{} for _ in range(RMAX + 1)]

    def learn(self, frame, nxt, key, y, x):
        labs = init_labels(frame, key, y, x, self.kind)
        ex = explain(frame, nxt)
        for r, L in enumerate(labs):
            t = self.t[r]
            u, c = np.unique(L, return_counts=True)
            for lb, n in zip(u.tolist(), c.tolist()):
                d = t.setdefault(lb, {-1: 0})
                d[-1] += n
            for e, m in ex:
                u, c = np.unique(L[m], return_counts=True)
                for lb, n in zip(u.tolist(), c.tolist()):
                    d = t[lb]
                    d[e] = d.get(e, 0) + n

    def nexts(self, frame, key, y, x, rcap=RMAX, min_r=0):
        labs = init_labels(frame, key, y, x, self.kind)
        out = np.full(frame.shape, -1, dtype=np.int32)
        seen = np.zeros(frame.shape, bool)
        todo = np.ones(frame.shape, bool)
        for r in range(rcap, min_r - 1, -1):
            if not todo.any():
                break
            ys, xs = np.nonzero(todo)
            u, inv = np.unique(labs[r][ys, xs], return_inverse=True)
            enc = np.full(len(u), -2, dtype=np.int32)
            for i, lb in enumerate(u.tolist()):
                h = self.t[r].get(lb)
                if h:
                    c = choose(h)
                    enc[i] = -1 if c is None else c
            e = enc[inv]
            hit = e != -2
            out[ys[hit], xs[hit]] = e[hit]
            seen[ys[hit], xs[hit]] = True
            todo[ys[hit], xs[hit]] = False
        return out, seen


def game_rows(game):
    d = load(game)
    ui = ui_mask(d)
    main = np.nonzero((d["branch"] == 0) & (d["action"] != 0))[0]
    probes = np.nonzero((d["branch"] == 1) & (d["action"] != 0))[0]
    return d, ui, main, probes


def eq_play(pred, truth, ui):
    return bool(np.array_equal(pred[~ui], truth[~ui]))


def run_online(game, library=None, use_probes=False):
    d, ui, main, probes = game_rows(game)
    col = Col("color")
    uses = {}
    rows = []
    for i in main.tolist():
        ft, f1, a, y, x = d["frame_t"][i], d["frame_t1"][i], int(d["action"][i]), int(d["y"][i]), int(d["x"][i])
        key = key_of(a, y, x, ft)
        n, seen = col.nexts(ft, key, y, x)
        p = decode(ft, n)
        changed = ft != f1
        changed[ui] = False
        row = dict(game=game, i=i, key=key, uses=uses.get(key, 0), n_ch=int(changed.sum()),
                   col=eq_play(p, f1, ui), b0=not changed.any(),
                   cc=int(((p == f1) & changed).sum()))
        if library is not None:
            q = n.copy()
            nl, sl = library.nexts(ft, key, y, x, min_r=1)
            take = (~seen) | ((n == -1) & sl)
            q[take & sl] = nl[take & sl]
            pl = decode(ft, q)
            row["lib"] = eq_play(pl, f1, ui)
            row["lib_cc"] = int(((pl == f1) & changed).sum())
        rows.append(row)
        col.learn(ft, f1, key, y, x)
        uses[key] = uses.get(key, 0) + 1
    return rows


def run_probes(game, seed=0):
    """Replay: main trajectory teaches. At each probe state we hold every action's true outcome."""
    d, ui, main, probes = game_rows(game)
    rng = random.Random(seed)
    col = Col("color")
    uses = {}
    # group probes by the state they branch from
    groups = {}
    for i in probes.tolist():
        groups.setdefault(int(d["step"][i]), []).append(i)
    res = []
    for i in main.tolist():
        s = int(d["step"][i])
        if s in groups and len(groups[s]) >= 2:
            items = []
            for j in groups[s]:
                ft, f1, a, y, x = d["frame_t"][j], d["frame_t1"][j], int(d["action"][j]), int(d["y"][j]), int(d["x"][j])
                key = key_of(a, y, x, ft)
                top, _ = col.nexts(ft, key, y, x)
                low, _ = col.nexts(ft, key, y, x, rcap=1)
                pt, pl = decode(ft, top), decode(ft, low)
                dis = int(((pt != pl) & ~ui).sum())
                changed = (ft != f1) & ~ui
                items.append(dict(dis=dis, surprise=not eq_play(pt, f1, ui), noop=not changed.any(),
                                  uses=uses.get(key, 0), n_ch=int(changed.sum()), pred_change=int(((pt != ft) & ~ui).sum())))
            ht = max(items, key=lambda t: (t["dis"], rng.random()))
            lu = min(items, key=lambda t: (t["uses"], rng.random()))
            pc = max(items, key=lambda t: (t["pred_change"], rng.random()))
            res.append(dict(game=game, n=len(items), r_surprise=float(np.mean([t["surprise"] for t in items])),
                            r_noop=float(np.mean([t["noop"] for t in items])),
                            ht_surprise=ht["surprise"], ht_noop=ht["noop"], ht_dis=ht["dis"],
                            lu_surprise=lu["surprise"], lu_noop=lu["noop"],
                            pc_surprise=pc["surprise"], pc_noop=pc["noop"], any_dis=any(t["dis"] > 0 for t in items)))
        ft, f1, a, y, x = d["frame_t"][i], d["frame_t1"][i], int(d["action"][i]), int(d["y"][i]), int(d["x"][i])
        key = key_of(a, y, x, ft)
        col.learn(ft, f1, key, y, x)
        uses[key] = uses.get(key, 0) + 1
    return res


def main():
    names = [g for g in games() if g.split("-")[0] in TUNING]
    assert len(names) == 12
    t0 = time.time()
    # library: a colour-free column over the other games' main trajectories
    lib_rows, online = [], []
    for g in names:
        online += run_online(g)
    print("online done", round(time.time() - t0, 1), flush=True)
    for g in names:
        lib = Col("mask")
        # learn the library on colour-free frames of the OTHER games
        for o in names:
            if o == g:
                continue
            d, ui, main_, _ = game_rows(o)
            for i in main_.tolist()[:80]:
                a, y, x = int(d["action"][i]), int(d["y"][i]), int(d["x"][i])
                lib.learn(d["frame_t"][i], d["frame_t1"][i], key_of(a, y, x, d["frame_t"][i]) if a != 6 else 600, y, x)
        lib_rows += run_online(g, library=_Wrapped(lib))
        print("library", g, round(time.time() - t0, 1), flush=True)
    probes = []
    for g in names:
        probes += run_probes(g)
    out = os.path.join(HERE, "results")
    json.dump(dict(online=online, lib=lib_rows, probes=probes), open(os.path.join(out, "arc3_spike.json"), "w"))
    print("done", round(time.time() - t0, 1))


class _Wrapped:
    """Library column asked with a colour-free click key (colours differ between games)."""

    def __init__(self, col):
        self.col = col

    def nexts(self, frame, key, y, x, rcap=RMAX, min_r=1):
        return self.col.nexts(frame, 600 if key >= 600 else key, y, x, rcap=rcap, min_r=min_r)


if __name__ == "__main__":
    main()
