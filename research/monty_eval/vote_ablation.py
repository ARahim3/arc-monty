"""WS4: counterfactual vote rules on the frozen v5 candidates (analysis only; the published system is unchanged).

Variants of the confident-answer rule, each reported as confident answers / correct / precision per split:
  v5            : published rule (vote.confident; pooled evidence >= 0.99 and >= 2:1 vote over conflicting strong answers)
  no-consensus  : any pooled answer with evidence >= 0.99 (drop the 2:1 rule)
  cross-module  : evidence accumulates only across distinct modules (a module's duplicate hypotheses add nothing)
  fit-only      : no leave-one-out: every candidate (all fit every demo) gets evidence 1.0, then the v5 rule
  threshold t   : v5 rule with the evidence threshold t in (0.5, 0.75, 0.9)
Also pass@2 of the always-answer submission under the cross-module rule (it can change the attempt order).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

from common import ALL_SPLITS, ROOT, build_cands, cache_for, tasks_for  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402


def pool(cands, cross_only=False, thr=0.99):
    pooled = []
    for c in cands:
        for p in pooled:
            if len(p["preds"]) == len(c["preds"]) and all(np.array_equal(a, b) for a, b in zip(p["preds"], c["preds"])):
                if not cross_only or c["lm"] not in p["voters"]:
                    p["evidence"] = max(p["evidence"], c["evidence"]) + 0.01 * min(p["evidence"], c["evidence"])
                else:
                    p["evidence"] = max(p["evidence"], c["evidence"])
                p["voters"].add(c["lm"])
                break
        else:
            pooled.append(dict(c, voters={c["lm"]}))
    pooled.sort(key=lambda p: (-int(p["evidence"] >= thr), -len(p["voters"]), -float(p["evidence"])))
    return pooled


def attempts(task, pooled, min_ev=0.0):
    out = [[] for _ in task["test"]]
    for p in pooled:
        if p["evidence"] < min_ev:
            break
        for a, g in zip(out, p["preds"]):
            if len(a) < 2 and not any(np.array_equal(g, q) for q in a):
                a.append(g)
    return out


def conf_answer(task, cands, thr=0.99, cross_only=False, consensus=True):
    best = pool(cands, cross_only, thr)
    strong = [p for p in best if p["evidence"] >= thr]
    if not strong:
        return None
    s = sorted(strong, key=lambda p: -len(p["voters"]))
    if consensus and not (len(s) == 1 or len(s[0]["voters"]) >= 2 * len(s[1]["voters"])):
        return None
    return score_task(task, attempts(task, best, thr))


def main():
    res = {}
    for split in ALL_SPLITS:
        rows, tasks = cache_for(split), tasks_for(split)
        acc = {}
        for k, row in rows.items():
            task = tasks[k]
            cands = build_cands(row)
            fit = [dict(c, evidence=1.0) for c in cands]
            variants = {
                "v5": conf_answer(task, cands),
                "no-consensus": conf_answer(task, cands, consensus=False),
                "cross-module": conf_answer(task, cands, cross_only=True),
                "fit-only": conf_answer(task, fit),
                "fit-only, no-consensus": conf_answer(task, fit, consensus=False),
                "threshold 0.9": conf_answer(task, cands, thr=0.9),
                "threshold 0.75": conf_answer(task, cands, thr=0.75),
                "threshold 0.5": conf_answer(task, cands, thr=0.5),
            }
            for name, v in variants.items():
                a = acc.setdefault(name, [0, 0.0, []])
                if v is not None:
                    a[0] += 1
                    a[1] += v
                    if v < 1:
                        a[2].append(k)
            s_cross = score_task(task, attempts(task, pool(cands, cross_only=True)))
            acc.setdefault("pass2 cross-module (always answer)", [0, 0.0, []])[1] += s_cross
        res[split] = {name: dict(answered=a[0], correct=round(a[1], 2),
                                 precision=round(a[1] / a[0], 4) if a[0] else None, wrong=a[2])
                      for name, a in acc.items()}
        print(split, {n: f"{v['correct']:.0f}/{v['answered']}" for n, v in res[split].items()}, flush=True)
    with open(os.path.join(ROOT, "research", "monty_eval", "results", "vote_ablation.json"), "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
