"""SPIKE: switches on the same column, tuning-half ARC-AGI-3 games only, recorded transitions only (no game code runs).

Arms (one thing changes per arm):
  full       action + local context + next sensation in all its forms
  nomove     the motor signal removed: the column is not told which action was taken
  noptr      next sensation stored only as SAME or a colour (no displacement, so no behaviour in the column's frame)
  ego        adds each cell's location relative to where something last changed (a location in a moving frame)
  r1, r3     reach capped: how much of the path is sensed
Also: calibrated answers (coverage and precision, non-identity) and open-loop rollouts (path integration: apply the
action sequence with no new sensation, compare with the real frame k steps later).
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "research", "arc3_wm"))

import column as C  # noqa: E402
import spike_arc3 as A  # noqa: E402
from common import games  # noqa: E402

RMAX = A.RMAX


class Arm(A.Col):
    def __init__(self, name):
        super().__init__("color")
        self.name = name
        self.ego = None

    def labels(self, frame, key, y, x):
        k = 0 if self.name == "nomove" else key
        base = frame.astype(np.uint64) + np.uint64(1)
        if key >= 600 and self.name != "nomove":
            yy, xx = np.mgrid[0:64, 0:64]
            rel = (np.clip(yy - y, -8, 8) + 8) * 17 + (np.clip(xx - x, -8, 8) + 8)
            base = C._mix(base, rel.astype(np.uint64) + np.uint64(5000))
        if self.name == "ego" and self.ego is not None:
            yy, xx = np.mgrid[0:64, 0:64]
            rel = (np.clip(yy - self.ego[0], -8, 8) + 8) * 17 + (np.clip(xx - self.ego[1], -8, 8) + 8)
            base = C._mix(base, rel.astype(np.uint64) + np.uint64(9000))
        if self.name == "nearobj":  # location in the canonical frame of the nearest object (the theory's own structure)
            near = C.near_sensor(frame, "nears")
            if near is not None:
                base = C._mix(base, near)
        return C.rings(C._mix(base, np.uint64(k + 77)), RMAX)

    def learn(self, frame, nxt, key, y, x):
        labs = self.labels(frame, key, y, x)
        ex = A.explain(frame, nxt)
        if self.name == "noptr":
            ex = [(e, m) for e, m in ex if e < A.PTR]
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

    def nexts_conf(self, frame, key, y, x, rcap=RMAX):
        labs = self.labels(frame, key, y, x)
        out = np.full(frame.shape, -1, dtype=np.int32)
        sure = np.zeros(frame.shape, bool)
        todo = np.ones(frame.shape, bool)
        for r in range(rcap, -1, -1):
            if not todo.any():
                break
            ys, xs = np.nonzero(todo)
            u, inv = np.unique(labs[r][ys, xs], return_inverse=True)
            enc = np.full(len(u), -2, dtype=np.int32)
            ok = np.zeros(len(u), bool)
            for i, lb in enumerate(u.tolist()):
                h = self.t[r].get(lb)
                if h:
                    c = A.choose(h)
                    enc[i] = -1 if c is None else c
                    ok[i] = c is not None and h.get(c, 0) == h[-1] and h[-1] >= 3
            e = enc[inv]
            hit = e != -2
            out[ys[hit], xs[hit]] = e[hit]
            sure[ys[hit], xs[hit]] = ok[inv][hit]
            todo[ys[hit], xs[hit]] = False
        return out, sure


def online(game, arm, rcap=RMAX, horizons=(2, 4, 8)):
    d, ui, main, _ = A.game_rows(game)
    col = Arm(arm)
    rows = []
    main = main.tolist()
    for pos, i in enumerate(main):
        ft, f1, a, y, x = d["frame_t"][i], d["frame_t1"][i], int(d["action"][i]), int(d["y"][i]), int(d["x"][i])
        key = A.key_of(a, y, x, ft)
        n, sure = col.nexts_conf(ft, key, y, x, rcap)
        p = A.decode(ft, n)
        changed = (ft != f1) & ~ui
        pred_change = (p != ft) & ~ui
        conf = bool(pred_change.any() and sure[pred_change].all())
        row = dict(game=game, i=i, col=A.eq_play(p, f1, ui), b0=not changed.any(), n_ch=int(changed.sum()),
                   cc=int(((p == f1) & changed).sum()), conf=conf)
        # open-loop rollouts from here, every 12th step, on the same level and no reset in between
        if arm == "full" and pos % 12 == 0:
            cur = ft
            for h in range(1, max(horizons) + 1):
                if pos + h - 1 >= len(main):
                    break
                j = main[pos + h - 1]
                if h > 1 and (d["level"][j] != d["level"][i] or int(d["action"][j]) == 0):
                    break
                aj, yj, xj = int(d["action"][j]), int(d["y"][j]), int(d["x"][j])
                kj = A.key_of(aj, yj, xj, cur)
                nj, _ = col.nexts_conf(cur, kj, yj, xj)
                cur = A.decode(cur, nj)
                if h in horizons:
                    truth = d["frame_t1"][j]
                    row[f"roll{h}"] = A.eq_play(cur, truth, ui)
                    row[f"still{h}"] = A.eq_play(ft, truth, ui)
        rows.append(row)
        col.learn(ft, f1, key, y, x)
        if changed.any():
            ys, xs = np.nonzero(changed)
            col.ego = (float(ys.mean()), float(xs.mean()))
    return rows


if __name__ == "__main__":
    names = [g for g in games() if g.split("-")[0] in A.TUNING]
    assert len(names) == 12
    res = {}
    t0 = time.time()
    only = sys.argv[1:] or None
    plan = (("full", RMAX), ("nomove", RMAX), ("noptr", RMAX), ("ego", RMAX), ("r1", 1), ("r3", 3), ("nearobj", RMAX))
    for arm, rcap in plan:
        if only and arm not in only:
            continue
        rows = []
        name = arm
        for g in names:
            rows += online(g, "full" if arm in ("r1", "r3") else arm, rcap)
        res[name] = rows
        print(name, round(time.time() - t0, 1), flush=True)
    out = "arc3_switches.json" if not only else "arc3_switches_" + "_".join(only) + ".json"
    json.dump(res, open(os.path.join(HERE, "results", out), "w"))
