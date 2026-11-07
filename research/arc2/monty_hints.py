"""Monty-ARC perception notes for an LLM prompt (no solving): sizes, colours, change sensor, object-centric
matching (D8-canonical shapes, as in Monty's object models), and whole-grid symmetry / periodicity.

    python research/arc2/monty_hints.py            # writes research/arc2/monty_hints.json for the 120 eval tasks
"""
import json
import os
import sys
from collections import Counter

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from arcmonty.objects import background, segment  # noqa: E402

MAX_OBJ = 40


def _sym(g):
    out = []
    if g.shape[0] > 1 and (g == g[::-1]).all():
        out.append("top-bottom mirror")
    if g.shape[1] > 1 and (g == g[:, ::-1]).all():
        out.append("left-right mirror")
    if (g == np.rot90(g, 2)).all() and not out:
        out.append("180-degree rotation")
    if g.shape[0] == g.shape[1] and g.shape[0] > 1:
        if (g == np.rot90(g, 1)).all():
            out.append("90-degree rotation")
        if (g == g.T).all():
            out.append("main-diagonal transpose")
    return out


def _period(g):
    """Smallest exact tiling period (py, px) of the whole grid, if smaller than the grid."""
    H, W = g.shape
    py = next((p for p in range(1, H) if (g[p:] == g[:-p]).all()), H)
    px = next((p for p in range(1, W) if (g[:, p:] == g[:, :-p]).all()), W)
    if (py < H or px < W) and py * px < H * W / 2:
        return py, px
    return None


def _objs(g, bg):
    objs = segment(g, "color8", bg)
    return objs


def _obj_summary(objs):
    if not objs:
        return "no objects"
    by_col = Counter(o.color for o in objs)
    sizes = sorted((o.size for o in objs), reverse=True)
    if len(objs) > 15:
        top = ", ".join(f"{c}: {n}" for c, n in by_col.most_common(4))
        return f"{len(objs)} objects (cluttered; most by colour {top}), largest sizes {sizes[:4]}"
    shapes = Counter(o.key_shape for o in objs)
    rep = max(shapes.values())
    s = f"{len(objs)} objects (" + ", ".join(f"{n}x colour {c}" for c, n in sorted(by_col.items())) + ")"
    s += f", sizes {sizes[:8]}{'...' if len(sizes) > 8 else ''}"
    if rep > 1 and len(objs) > 2:
        s += f", {len(shapes)} distinct shapes up to rotation/reflection (most common x{rep})"
    return s


def _match(oi, oo):
    """Match input objects to output objects by D8-canonical shape (Monty: object model x pose)."""
    if len(oi) > MAX_OBJ or len(oo) > MAX_OBJ:
        return None
    used, stats, moves = set(), Counter(), []
    for a in oi:
        best = None
        for j, b in enumerate(oo):
            if j in used or a.key_shape != b.key_shape:
                continue
            same_pos = (a.y0, a.x0) == (b.y0, b.x0) and a.mask.shape == b.mask.shape
            same_col = a.color == b.color
            same_pose = a.pose == b.pose
            rank = (same_pos, same_col, same_pose)
            if best is None or rank > best[0]:
                best = (rank, j, same_pos, same_col, same_pose)
        if best is None:
            stats["disappeared"] += 1
            continue
        _, j, sp, sc, spo = best
        used.add(j)
        if not sp:
            b = oo[j]
            moves.append((b.y0 - a.y0, b.x0 - a.x0))
        if sp and sc:
            stats["unchanged"] += 1
        elif sp:
            stats["recoloured in place"] += 1
        elif not spo:
            stats["rotated/reflected"] += 1
        else:
            stats["moved" if sc else "moved+recoloured"] += 1
    stats["new"] = len(oo) - len(used)
    out = {k: v for k, v in stats.items() if v}
    if moves and len(moves) <= 6:
        out["(displacements dy,dx: " + " ".join(f"{dy:+d},{dx:+d}" for dy, dx in moves) + ")"] = ""
    return out


def notes(task):
    tr = [(np.array(p["input"]), np.array(p["output"])) for p in task["train"]]
    te = [np.array(t["input"]) for t in task["test"]]
    L = []
    # sizes
    rel = []
    for i, o in tr:
        if i.shape == o.shape:
            rel.append("same")
        elif o.shape[0] % i.shape[0] == 0 and o.shape[1] % i.shape[1] == 0:
            rel.append(f"x{o.shape[0] // i.shape[0]},x{o.shape[1] // i.shape[1]}")
        elif i.shape[0] % o.shape[0] == 0 and i.shape[1] % o.shape[1] == 0:
            rel.append(f"/{i.shape[0] // o.shape[0]},/{i.shape[1] // o.shape[1]}")
        else:
            rel.append(f"{i.shape[0]}x{i.shape[1]}->{o.shape[0]}x{o.shape[1]}")
    if all(r == "same" for r in rel):
        L.append("Size: every output has the same size as its input.")
    elif len(set(o.shape for _, o in tr)) == 1:
        L.append(f"Size: every output is {tr[0][1].shape[0]}x{tr[0][1].shape[1]} regardless of the input size ({', '.join(rel)}).")
    else:
        L.append("Size (input->output per example): " + "; ".join(rel) + ".")
    # colours
    ci = set().union(*[set(np.unique(i)) for i, _ in tr])
    co = set().union(*[set(np.unique(o)) for _, o in tr])
    bgs = Counter(background(i) for i, _ in tr)
    s = f"Colours: background {bgs.most_common(1)[0][0]}"
    if co - ci:
        s += f"; colours that appear only in outputs: {sorted(int(c) for c in co - ci)}"
    if ci - co:
        s += f"; colours that never survive into outputs: {sorted(int(c) for c in ci - co)}"
    L.append(s + ".")
    # change sensor (same-size pairs)
    same = [(i, o) for i, o in tr if i.shape == o.shape]
    if same:
        fr, kinds = [], Counter()
        for i, o in same:
            d = i != o
            fr.append(d.mean())
            for a, b in zip(i[d], o[d]):
                kinds[(int(a), int(b))] += 1
        top = ", ".join(f"{a}->{b}" for (a, b), _ in kinds.most_common(5))
        bgc = bgs.most_common(1)[0][0]
        add_only = all(a == bgc for a, _ in kinds)
        L.append(f"Changes: {100 * min(fr):.0f}-{100 * max(fr):.0f}% of cells change; most frequent recolourings {top}"
                 + (" (output only paints over background: nothing is erased or moved)" if add_only and kinds else "") + ".")
    # objects + matching
    for n, (i, o) in enumerate(tr[:4], 1):
        bg_i, bg_o = background(i), background(o)
        oi, oo = _objs(i, bg_i), _objs(o, bg_o)
        line = f"Example {n}: input {_obj_summary(oi)}; output {_obj_summary(oo)}"
        if i.shape == o.shape:
            m = _match(oi, oo)
            if m:
                line += "; input->output object matching (same shape up to rotation/reflection): " + ", ".join(
                    (f"{v} {k}" if v != "" else k) for k, v in m.items())
        L.append(line + ".")
    for j, t in enumerate(te, 1):
        L.append(f"Test input {j}: {_obj_summary(_objs(t, background(t)))}.")
    # symmetry / periodicity
    syms = []
    for n, (i, o) in enumerate(tr, 1):
        for name, g in (("input", i), ("output", o)):
            s = _sym(g)
            p = _period(g)
            if s or p:
                syms.append(f"ex{n} {name}: " + ", ".join(s + ([f"tiles with period {p[0]}x{p[1]}"] if p else [])))
    if syms:
        L.append("Exact whole-grid symmetries: " + "; ".join(syms[:8]) + ".")
    else:
        L.append("No exact whole-grid mirror/rotation symmetry or tiling in any example grid.")
    return "\n".join("- " + x for x in L)


HINT_HEADER = ("## Perception notes\nAutomatic object-centric analysis of the examples (connected single-colour "
               "objects, 8-connected; shapes compared up to rotation/reflection). It can be incomplete or "
               "misleading; trust the grids over these notes.\n")


if __name__ == "__main__":
    ch = json.load(open(os.path.join(ROOT, "data/kaggle_format/agi2_eval_challenges.json")))
    out = {}
    for k, t in sorted(ch.items()):
        try:
            out[k] = HINT_HEADER + notes(t)
        except Exception as e:  # never block a task
            out[k] = ""
            print(k, "failed", e)
    json.dump(out, open(os.path.join(ROOT, "research/arc2/monty_hints.json"), "w"), indent=0)
    lens = [len(v) for v in out.values()]
    print(len(out), "hints; chars median", sorted(lens)[len(lens) // 2], "max", max(lens))
    print(out[sorted(out)[0]])
    print(out[sorted(out)[5]])
