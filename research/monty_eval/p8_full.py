"""WS4 / FA-LOO §4: whole-task D8 perspective voting (8 views) on full data, re-voted offline from the per-module,
per-perspective cache: v5 rule vs P4 (one voter per module, no same-module or cross-view evidence accumulation).
Reproduces research/paper/data/agi1_train_p8.json (paper-writer's real 8-view run) as a check.
usage: python research/monty_eval/p8_full.py agi1-train  -> results/p8_full.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, ROOT, cache_for, tasks_for  # noqa: E402
from faloo import build, confident_p4, pool_p4, reorder_by_persp  # noqa: E402
from arcmonty import vote  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402


def conf_score(task, cands, rule):
    if rule == "v5":
        if not vote.confident(cands):
            return None
        return score_task(task, vote.attempts_from(task, cands, vote.CONFIDENT))
    best = pool_p4(cands)
    if not confident_p4(best):
        return None
    att = [[] for _ in task["test"]]
    for p in best:
        if p["evidence"] < vote.CONFIDENT:
            break
        for a, g in zip(att, p["preds"]):
            if len(a) < 2 and not any(np.array_equal(g, q) for q in a):
                a.append(g)
    return score_task(task, att)


def main(split):
    tasks, full = tasks_for(split), cache_for(split)
    extra = {json.loads(l)["task"]: json.loads(l) for l in open(os.path.join(CACHE, f"persp_p1-7_{split}.jsonl"))}
    ref = None
    rp = os.path.join(ROOT, "research", "paper", "data", f"{split.replace('-', '_')}_p8.json")
    if os.path.exists(rp):
        ref = {r["task"]: r for r in json.load(open(rp))["rows"]}
    out, mism = {}, []
    for name, rule, persp in (("v5 1 view", "v5", {0}), ("v5 8 views", "v5", None), ("P4 1 view", "p4", {0}),
                              ("P4 8 views", "p4", None)):
        ans, cor, wrong = 0, 0.0, []
        for k in sorted(tasks):
            if k not in extra:
                continue
            cands = reorder_by_persp(build([full[k], extra[k]], None, persp))
            s = conf_score(tasks[k], cands, rule)
            if s is not None:
                ans += 1
                cor += s
                if s < 1:
                    wrong.append(k)
            if ref and name == "v5 8 views" and k in ref and bool(ref[k]["confident"]) != (s is not None):
                mism.append(k)
        out[name] = dict(answered=ans, correct=cor, wrong=wrong)
        print(split, name, f"{cor:.0f}/{ans}", "wrong:", wrong, flush=True)
    out["check_vs_paper_writer_real_8view_run"] = dict(confident_flag_mismatches=mism, n=len(extra))
    print("mismatch vs real 8-view run:", mism)
    json.dump({split: out}, open(os.path.join(ROOT, "research", "monty_eval", "results", "p8_full.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "agi1-train")
