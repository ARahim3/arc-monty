"""monty-heldout step 2: offline re-vote of every configuration from the per-module cache (frozen vote code).
usage: python revote.py TAG {base|p8} [--procs 8]  -> results/TAG_<set>.jsonl (one line per item: cfg -> role -> outcome)"""
import argparse
import json
import multiprocessing as mp
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl_common import CACHE, HERE, MODULES  # noqa: E402
import numpy as np  # noqa: E402
from rules import build, faloo_role, full_outcome, top_of  # noqa: E402

RES = os.path.join(HERE, "results")


def configs(which):
    allm = set(MODULES)
    if which == "base":
        c = {"full": {}}
        c.update({f"-{m}": dict(modules=allm - {m}) for m in MODULES})
        c.update({f"{m} alone": dict(modules={m}) for m in MODULES})
        c.update({"sys:canon": dict(frames={"canon"}), "sys:abs": dict(frames={"abs"}), "sys:global": dict(glob=True),
                  "beh:canon": dict(modules={"behavior"}, frames={"canon"}), "beh:abs": dict(modules={"behavior"}, frames={"abs"}),
                  "beh:global": dict(modules={"behavior"}, glob=True)})
        return c
    return {"p8": dict(views=None), "p8:behavior": dict(views=None, modules={"behavior"})}


def index(path):
    idx, off = {}, 0
    with open(path, "rb") as fh:
        for line in fh:
            idx[json.loads(line)["task"]] = off
            off += len(line)
    return idx


def load(path, off):
    with open(path, "rb") as fh:
        fh.seek(off)
        r = json.loads(fh.readline())
    r["_np"] = [np.array(g, dtype=np.int8) for g in r["grids"]]
    return r


def pool_grids(key, row_pool):
    return row_pool


def one(arg):
    key, pool, files, which = arg
    rows = [load(p, o) for p, o in files["main"]]
    grows = [load(p, o) for p, o in files.get("global", [])]
    m = len(pool)
    out = {}
    for name, cfg in configs(which).items():
        kw = dict(modules=cfg.get("modules"), frames=cfg.get("frames"), views=cfg.get("views", {0}))
        if which == "p8":
            kw["views"] = None
        if cfg.get("glob"):
            kw["behavior_rows"] = grows
        res = {}
        for a in range(m):
            x, y = pool[a]
            task = {"test": [x], "test_out": [y]}
            C = build(rows, f"F{a}", **kw)
            o = full_outcome(task, C)
            top5 = top_of(C, "v5")
            top4 = top_of(C, "p4")
            for rule, y_full, tag in (("v5", top5, ""), ("p4", top4, "4")):
                ft = {}
                for b in range(m):
                    if b == a:
                        continue
                    ft[b] = top_of(build(rows, f"{a},{b}", **kw), rule)
                r = faloo_role(None if y_full is None else y_full[0], y, ft, {b: pool[b][1] for b in range(m) if b != a})
                o["a" + tag], o["fa" + tag], o["fc" + tag], o["why" + tag] = r["a"], r["fa"], r["fc"], r["why"]
                if rule == "v5" and name == "full" and which == "base":
                    from hl_common import h
                    o["fold_h"] = {str(b): (None if p is None else [h(p[0]), h(p[1])]) for b, p in ft.items()}
                    o["full_h"] = None if y_full is None else h(y_full[0])
            res[str(a)] = o
        out[name] = res
    return dict(task=key, m=m, cfg=out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("tag")
    ap.add_argument("which", choices=["base", "p8"])
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    from hl_common import items_from_dir, read_done
    os.makedirs(RES, exist_ok=True)
    items = dict(items_from_dir(a.dir))
    main_paths = [os.path.join(CACHE, f"{a.tag}_p0.jsonl")]
    if a.which == "p8":
        main_paths.append(os.path.join(CACHE, f"{a.tag}_p1-7.jsonl"))
    idxs = [(p, index(p)) for p in main_paths]
    gp = os.path.join(CACHE, f"{a.tag}_p0_global.jsonl")
    gi = (gp, index(gp)) if a.which == "base" else None
    out = os.path.join(RES, f"{a.tag}_{a.which}.jsonl")
    done = read_done(out)
    todo = []
    for k, pool in items.items():
        if k in done or not all(k in ix for _, ix in idxs):
            continue
        f = {"main": [(p, ix[k]) for p, ix in idxs]}
        if gi:
            f["global"] = [(gi[0], gi[1][k])]
        todo.append((k, pool, f, a.which))
    print(out, len(items), "items", len(done), "done", len(todo), "todo", flush=True)
    with mp.Pool(a.procs, maxtasksperchild=50) as p, open(out, "a") as fh:
        for n, r in enumerate(p.imap_unordered(one, todo, chunksize=1), 1):
            fh.write(json.dumps(r, separators=(",", ":"), default=float) + "\n")
            fh.flush()
            if n % 40 == 0 or n == len(todo):
                print(n, len(todo), flush=True)


if __name__ == "__main__":
    main()
