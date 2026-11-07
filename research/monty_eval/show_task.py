"""Print an ARC task compactly (demos side by side, test truth) with Monty-ARC v5's cached candidates and attempts.

usage: python research/monty_eval/show_task.py <split> <task_id> [--no-monty] [--max-cands 6]
Colours: '.'=0, 1-9 digits. Grids are printed input | output, one demo after another.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

from common import MODULES, build_cands, cache_for, tasks_for  # noqa: E402
from arcmonty.vote import attempts_from, confident, pool  # noqa: E402


def rows(g):
    return ["".join(".123456789"[v] if v else "." for v in r) for r in np.asarray(g)]


def side(*grids, gap="   "):
    rs = [rows(g) for g in grids]
    h = max(len(r) for r in rs)
    w = [len(r[0]) if r else 0 for r in rs]
    out = []
    for y in range(h):
        out.append(gap.join((r[y] if y < len(r) else " " * w[i]) for i, r in enumerate(rs)))
    return "\n".join(out)


def diff_stats(pred, truth):
    pred, truth = np.asarray(pred), np.asarray(truth)
    if pred.shape != truth.shape:
        return f"shape {pred.shape} vs truth {truth.shape}"
    bad = int((pred != truth).sum())
    return f"{bad} wrong cells of {truth.size} ({100 * (1 - bad / truth.size):.1f}% cell accuracy)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("split")
    ap.add_argument("task")
    ap.add_argument("--no-monty", action="store_true")
    ap.add_argument("--max-cands", type=int, default=6)
    a = ap.parse_args()
    task = tasks_for(a.split)[a.task]
    for j, (i, o) in enumerate(task["train"]):
        print(f"--- demo {j}: {i.shape} -> {o.shape}")
        print(side(i, o))
    for j, t in enumerate(task["test"]):
        tr = task["test_out"][j] if j < len(task["test_out"]) else None
        print(f"--- test {j}: {t.shape} -> {None if tr is None else tr.shape}  (input | truth)")
        print(side(t, tr) if tr is not None else side(t))
    if a.no_monty:
        return
    row = cache_for(a.split)[a.task]
    print("--- Monty-ARC v5 per module: n candidates (max evidence), wall s")
    for m in MODULES:
        c = row["mods"][m]["cands"]
        ev = max((x["ev"] for x in c), default=None)
        print(f"  {m:12s} {len(c):4d} cands  max_ev={ev}  {row['mods'][m]['wall']:.2f}s"
              + (f"  ERR {row['mods'][m]['err']}" if row["mods"][m]["err"] else ""))
    cands = build_cands(row)
    best = pool(cands)
    print(f"--- pooled hypotheses: {len(best)}; confident={confident(cands)}")
    for p in best[:a.max_cands]:
        print(f"  ev={p['evidence']:.3f} voters={sorted(p['voters'])} hyp={p['hyp'][:160]}")
        for j, g in enumerate(p["preds"]):
            if j < len(task["test_out"]):
                print("     test", j, diff_stats(g, task["test_out"][j]))
    att = attempts_from(task, cands)
    for j, at in enumerate(att):
        for k, g in enumerate(at):
            print(f"--- test {j} attempt {k + 1}: {diff_stats(g, task['test_out'][j]) if j < len(task['test_out']) else ''}")
            print(side(g, task["test_out"][j]) if j < len(task["test_out"]) else side(g))


if __name__ == "__main__":
    main()
