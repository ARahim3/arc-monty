"""WS4 failure analysis, data part: confident-but-wrong answers (all splits), answered-but-wrong near misses and
structural descriptors of unsolved tasks (agi2-eval, new233).  Needs ablate.py output.
Writes research/monty_eval/results/failure_data.json.
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

from common import ALL_SPLITS, MODULES, ROOT, build_cands, cache_for, tasks_for  # noqa: E402
from arcmonty.objects import background, segment  # noqa: E402
from arcmonty.vote import CONFIDENT, attempts_from, confident, pool  # noqa: E402

RES = os.path.join(ROOT, "research", "monty_eval", "results")


def cell_acc(pred, truth):
    pred, truth = np.asarray(pred), np.asarray(truth)
    if pred.shape != truth.shape:
        return None
    return float((pred == truth).mean())


def descriptors(task):
    pairs = task["train"]
    d = {}
    rel = set()
    for i, o in pairs:
        rel.add("same" if i.shape == o.shape else ("smaller" if o.size < i.size else ("larger" if o.size > i.size else "reshaped")))
    d["shape_rel"] = "/".join(sorted(rel))
    d["out_shape_fixed"] = len({o.shape for _, o in pairs}) == 1
    d["in_cells_mean"] = float(np.mean([i.size for i, _ in pairs]))
    d["n_demos"] = len(pairs)
    d["n_test"] = len(task["test"])
    d["n_colors_in"] = int(np.mean([len(np.unique(i)) for i, _ in pairs]))
    d["out_colors_subset"] = all(set(np.unique(o)) <= set(np.unique(i)) for i, o in pairs)
    objs = [len(segment(i, "multi8", bg=background(i))) for i, _ in pairs]
    d["n_objects_in"] = float(np.mean(objs))
    if rel == {"same"}:
        fr, add, rec, era = [], True, True, True
        for i, o in pairs:
            bg = background(i)
            ch = i != o
            fr.append(float(ch.mean()))
            add &= bool((i[ch] == bg).all())          # only background cells change (drawing)
            era &= bool((o[ch] == bg).all())          # only cells erased to background
            rec &= bool(((i[ch] != bg) & (o[ch] != bg)).all())  # only recolouring of foreground
        d["changed_frac"] = round(float(np.mean(fr)), 3)
        d["change_kind"] = "add-only" if add else ("erase-only" if era else ("recolour-only" if rec else "mixed"))
    else:
        # is each output a subgrid of its input (crop)?
        def is_crop(i, o):
            H, W = i.shape
            h, w = o.shape
            if h > H or w > W:
                return False
            from numpy.lib.stride_tricks import sliding_window_view
            return bool((sliding_window_view(i, (h, w)) == o).all(axis=(2, 3)).any())
        d["crop"] = all(is_crop(i, o) for i, o in pairs)
    return d


def main():
    per = collections.defaultdict(dict)
    with open(os.path.join(RES, "per_task_full.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            per[r["split"]][r["task"]] = r
    out = dict(confident_wrong=[], answered_wrong={}, unsolved={}, solved={})
    for split in ALL_SPLITS:
        if split not in per:
            continue
        rows, tasks = cache_for(split), tasks_for(split)
        for k, r in per[split].items():
            f = r["full"]
            if f["conf"] and f["cs"] < 1:
                cands = build_cands(rows[k])
                best = pool(cands)
                strong = [dict(ev=round(p["evidence"], 3), voters=sorted(p["voters"]), hyp=p["hyp"][:200],
                               acc=[cell_acc(g, t) for g, t in zip(p["preds"], tasks[k]["test_out"])])
                          for p in best if p["evidence"] >= CONFIDENT]
                out["confident_wrong"].append(dict(split=split, task=k, score=f["cs"], strong=strong))
        if split not in ("agi2-eval", "new233"):
            continue
        aw, un, so = [], [], []
        for k, r in per[split].items():
            task = tasks[k]
            f = r["full"]
            if f["s2"] >= 1:
                so.append(dict(task=k, top_mods=f["top_mods"], top_ev=f["top_ev"], conf=f["conf"]))
                continue
            d = descriptors(task)
            d.update(task=k, partial=f["s2"], answered=f["ans"],
                     alone_answered=[m for m in MODULES if r["alone_ans"][m]])
            if f["ans"]:
                cands = build_cands(rows[k])
                best = pool(cands)
                att = attempts_from(task, cands)
                accs = [[cell_acc(g, task["test_out"][j]) for g in a] for j, a in enumerate(att)]
                d.update(top_mods=f["top_mods"], top_ev=f["top_ev"], conf=f["conf"], n_hyps=len(best),
                         top_hyp=best[0]["hyp"][:200], attempt_acc=accs,
                         best_acc=max((x for a in accs for x in a if x is not None), default=None),
                         wrong_cells=[[None if x is None else int(round((1 - x) * task["test_out"][j].size)) for x in a]
                                      for j, a in enumerate(accs)])
                aw.append(d)
            un.append(d)
        out["answered_wrong"][split] = aw
        out["unsolved"][split] = un
        out["solved"][split] = so
        print(split, "solved", len(so), "unsolved", len(un), "answered-but-wrong", len(aw), flush=True)
    print("confident wrong:", [(c["split"], c["task"]) for c in out["confident_wrong"]])
    with open(os.path.join(RES, "failure_data.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))


if __name__ == "__main__":
    main()
