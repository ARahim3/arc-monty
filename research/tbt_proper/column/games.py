"""The same column on ARC-AGI-3 recordings: transitions read as data, no game code runs. Predict, then learn."""
import json
import multiprocessing as mp
import os
import sys
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "research", "arc3_wm"))
import numpy as np  # noqa: E402

import column as C  # noqa: E402
from common import games as all_games, load  # noqa: E402  (loads recorded npz; project code, runs no game)
from settings import GAME_ARMS, HORIZONS, LIBRARY_TRANSITIONS, ROLL_EVERY, STREAK, TUNING_GAMES  # noqa: E402
from wm2 import ui_mask  # noqa: E402


def named(which):
    names = all_games()
    tuning = [g for g in names if g.split("-")[0] in TUNING_GAMES]
    out = tuning if which == "tuning" else [g for g in names if g.split("-")[0] not in TUNING_GAMES]
    assert len(out) == (12 if which == "tuning" else 13) and which in ("tuning", "heldout")
    return out


def _main(d):
    return np.nonzero((d["branch"] == 0) & (d["action"] != 0))[0].tolist()


def _step(d, i):
    a = int(d["action"][i])
    return d["frame_t"][i], d["frame_t1"][i], a, (int(d["y"][i]), int(d["x"][i])) if a == 6 else None


def library_for(game, names, configs, common):
    """The same columns, kept across games: the first transitions of every other game."""
    lib = C.Population(configs, **common)
    for other in names:
        if other != game:
            d = load(other)
            for i in _main(d)[:LIBRARY_TRANSITIONS]:
                x, y, a, at = _step(d, i)
                for c in lib.cols:
                    c.learn(x, y, a, at)
            C._MEMO.clear()
    return lib


def run_game(game, configs, common=None, library=None, rollouts=False):
    common = common or {}
    d = load(game)
    ui = ui_mask(d)
    main = _main(d)
    pop = C.Population(configs, **common)
    if library is not None:
        for c, m in zip(pop.cols, library.cols):
            c.memory = m
    play = ~ui
    eq = lambda a, b: bool(np.array_equal(a[play], b[play]))
    rows, recent, uses = [], {}, {}
    for pos, i in enumerate(main):
        x, y, a, at = _step(d, i)
        preds = pop.predictions(x, a, at)
        order = pop.order(preds, x, a, at)
        best = order[0] if order else None
        p = preds[best] if best is not None else x
        changed = (x != y) & play
        said = pop.cols[best]._key(x, a, at) if best is not None else None
        conf = bool(best is not None and ((p != x) & play).any() and recent.get((best, said), [False])[-STREAK:] == [True] * STREAK)
        use = a if at is None else 600 + int(x[at])
        row = dict(game=game, i=i, col=eq(p, y), b0=not changed.any(), n_ch=int(changed.sum()), cc=int(((p == y) & changed).sum()), conf=conf,
                   uses=uses.get(use, 0), top=None if best is None else f"{pop.cols[best].kind}/R{pop.cols[best].reach}/p{len(pop.cols[best].poses)}")
        if rollouts and pos % ROLL_EVERY == 0:
            col, cur = pop.cols[best if best is not None else int(np.argmax(pop.hits))], x
            for h in range(1, max(HORIZONS) + 1):
                if pos + h - 1 >= len(main):
                    break
                j = main[pos + h - 1]
                if h > 1 and (d["level"][j] != d["level"][i] or not np.array_equal(d["frame_t"][j], d["frame_t1"][main[pos + h - 2]])):
                    break  # same level, no reset in between
                _, truth, aj, atj = _step(d, j)
                nxt = col.predict(cur, aj, atj)
                cur = cur if nxt is None else nxt
                if h in HORIZONS:
                    row[f"roll{h}"] = eq(cur, truth)
                    row[f"still{h}"] = eq(x, truth)
        for j, c in enumerate(pop.cols):
            if preds[j] is not None:
                recent.setdefault((j, c._key(x, a, at)), []).append(eq(preds[j], y))
        pop.observe(preds, x, y, a, at, ui)
        uses[use] = uses.get(use, 0) + 1
        rows.append(row)
        C._MEMO.clear()
    return rows


def _one(args):
    game, arm, names = args
    spec = GAME_ARMS[arm]
    t0 = time.time()
    common = spec.get("common", {})
    try:
        lib = library_for(game, names, spec["configs"], common) if spec.get("library") else None
        return run_game(game, spec["configs"], common, lib, spec.get("rollouts", False)), game, time.time() - t0
    except Exception as e:  # a crash leaves this game out of this arm, and is reported
        print("CRASH", arm, game, repr(e)[:200], flush=True)
        return [], game, time.time() - t0


def run_named_arm(arm, names, workers=4):
    rows = []
    with mp.Pool(workers, maxtasksperchild=1) as pool:
        for r, g, s in pool.imap_unordered(_one, [(g, arm, names) for g in names], chunksize=1):
            rows += r
            print(" ", arm, g.split("-")[0], round(s, 1), flush=True)
    rows.sort(key=lambda r: (r["game"], r["i"]))
    return rows


def summary(rows):
    ch = [r for r in rows if r["n_ch"] > 0]
    conf = [r for r in rows if r["conf"]]
    out = dict(n=len(rows), exact=round(float(np.mean([r["col"] for r in rows])), 4), b0=round(float(np.mean([r["b0"] for r in rows])), 4),
               changed=len(ch), on_changed=round(float(np.mean([r["col"] for r in ch])), 4),
               conf_cov=round(len(conf) / len(rows), 4), conf_prec=round(float(np.mean([r["col"] for r in conf])), 4) if conf else None)
    for h in HORIZONS:
        s = [r for r in rows if f"roll{h}" in r]
        if s:
            out[f"h{h}"] = (len(s), round(float(np.mean([r[f"roll{h}"] for r in s])), 4), round(float(np.mean([r[f"still{h}"] for r in s])), 4))
    return out
