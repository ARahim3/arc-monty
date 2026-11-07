"""Read-only evaluation of Monty-ARC (frozen arcmonty/ code) on a split or the ARC-AGI-2-only training subset.

Usage: python research/paper/scripts/subset_eval.py <split|agi2-only> <perspectives: 1|8> <nproc> <out.json>
  agi2-only = ARC-AGI-2 training tasks that appear in neither ARC-AGI-1 split (233 tasks): a held-out check that
  avoids tuning on the public eval. perspectives=8 re-enables whole-task D8 perspective voting (dropped in v1).
Per task it records: answered, pass@2 score, confident (consensus rule) and its pass@2, top-answer evidence, the
modules voting for the top answer, and CPU seconds.
"""
import glob
import json
import multiprocessing as mp
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from arcmonty import monty_arc  # noqa: E402
from arcmonty.data import SPLITS, load_split  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402
from arcmonty.vote import attempts_from, confident, pool  # noqa: E402

PERSP = (0,)


def _ids(split):
    return {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(SPLITS[split], "*.json"))}


def _one(item):
    key, task = item
    t0 = time.time()
    cands = monty_arc.candidates(task, perspectives=PERSP)
    dt = time.time() - t0
    best = pool(cands)
    s_all = score_task(task, attempts_from(task, cands))
    conf = confident(cands)
    s_conf = score_task(task, attempts_from(task, cands, 0.99)) if conf else None
    top = best[0] if best else None
    return dict(task=key, answered=bool(best), pass2=s_all, confident=conf, conf_pass2=s_conf,
                top_evidence=round(float(top["evidence"]), 3) if top else None,
                top_correct=score_task(task, [[g] for g in top["preds"]]) if top else None,
                top_modules=sorted({v.split("@")[0] for v in top["voters"]}) if top else [], sec=round(dt, 2))


def _init(p):
    global PERSP
    PERSP = p


if __name__ == "__main__":
    name, n_persp, nproc, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    persp = tuple(range(8)) if n_persp == 8 else (0,)
    if name == "agi2-only":
        keep = _ids("agi2-train") - _ids("agi1-train") - _ids("agi1-eval")
        tasks = {k: t for k, t in load_split("agi2-train").items() if k in keep}
    else:
        tasks = load_split(name)
    with mp.Pool(nproc, initializer=_init, initargs=(persp,)) as p:
        rows = p.map(_one, list(tasks.items()), chunksize=1)
    json.dump(dict(split=name, perspectives=list(persp), n=len(tasks), rows=rows), open(out, "w"))
    n = len(rows)
    tot = sum(r["pass2"] for r in rows)
    cf = [r for r in rows if r["confident"]]
    print(f"{name} persp={len(persp)} n={n} pass@2 {tot:.1f} ({100 * tot / n:.2f}%) answered={sum(r['answered'] for r in rows)} "
          f"confident {sum(r['conf_pass2'] for r in cf):.0f}/{len(cf)} sec mean {sum(r['sec'] for r in rows) / n:.2f} "
          f"max {max(r['sec'] for r in rows):.0f}")
    print("solved:", " ".join(r["task"] for r in rows if r["pass2"] > 0))
