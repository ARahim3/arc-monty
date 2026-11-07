"""WS4 / FA-LOO step 2 (offline): fold-agreement leave-one-out on the frozen Monty-ARC v5 system.

Learner A = Monty-ARC (8 modules) + a vote rule, applied to a demo multiset; its output on a query is its top pooled
answer (variant "conf": answer only when the v5/P4 confident rule holds). For each task and test input t:
  fold i (i = 1..n): A_{-i} trained on the other n-1 demos and queried jointly on (x_i, x*_t)   [run_folds.py]
  (a) every A_{-i} predicts its held-out demo exactly;  (b) every A_{-i} gives the same test answer y_hat_t.
FA-LOO answers the task iff (a) and (b) hold for every test input. Under exchangeability of the n demos and the test
pair, P(answer and wrong) <= 1/(n+1) per test pair (jackknife+ tournament argument).

Vote rules: v5 = arcmonty.vote (pool / confident) unchanged; p4 = voters counted per module (perspective views of one
module are one voter) and evidence accumulates only across distinct modules (no same-module duplicate pooling).
usage: python research/monty_eval/faloo.py [--persp8 agi1-train]   -> results/faloo.json
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

from common import BASE_SPLITS, CACHE, MODULES, ROOT, cache_for, tasks_for  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402
from arcmonty import vote  # noqa: E402

RES = os.path.join(ROOT, "research", "monty_eval", "results")
CONF = vote.CONFIDENT


def same(a, b):
    return len(a) == len(b) and all(np.array_equal(x, y) for x, y in zip(a, b))


def pool_p4(cands):
    pooled = []
    for c in cands:
        mod = c["lm"].split("@")[0]
        for p in pooled:
            if same(p["preds"], c["preds"]):
                if mod not in p["mods"]:
                    p["evidence"] = max(p["evidence"], c["evidence"]) + 0.01 * min(p["evidence"], c["evidence"])
                    p["mods"].add(mod)
                else:
                    p["evidence"] = max(p["evidence"], c["evidence"])
                p["voters"].add(c["lm"])
                break
        else:
            pooled.append(dict(c, voters={c["lm"]}, mods={mod}))
    pooled.sort(key=lambda p: (-int(p["evidence"] >= CONF), -len(p["mods"]), -float(p["evidence"])))
    return pooled


def confident_p4(pooled):
    strong = sorted([p for p in pooled if p["evidence"] >= CONF], key=lambda p: -len(p["mods"]))
    return bool(strong) and (len(strong) == 1 or len(strong[0]["mods"]) >= 2 * len(strong[1]["mods"]))


def top(cands, rule, conf_only):
    """A's answer: the top pooled prediction list, or None (abstain)."""
    if rule == "v5":
        best = vote.pool(cands)
        if not best or (conf_only and not vote.confident(cands)):
            return None
    else:
        best = pool_p4(cands)
        if not best or (conf_only and not confident_p4(best)):
            return None
    return best[0]["preds"]


def build(rows, subset=None, persp=None):
    """Candidates from one or more cache rows ({grids, mods}); lm already tagged '@k' (fold caches) or not
    (run_modules cache: tag '@0'). Module order, then perspective-file order, as monty_arc.candidates."""
    out = []
    for k_row, row in enumerate(rows):
        grids = [np.array(g, dtype=np.int8) for g in row["grids"]]
        for m in MODULES:
            if subset is not None and m not in subset:
                continue
            for c in row["mods"].get(m, {"cands": []})["cands"]:
                lm = c["lm"] if "@" in c["lm"] else f"{c['lm']}@0"
                if persp is not None and int(lm.split("@")[1]) not in persp:
                    continue
                out.append(dict(lm=lm, hyp=c["hyp"], evidence=c["ev"], preds=[grids[i] for i in c["p"]]))
    return out


def reorder_by_persp(cands):
    """monty_arc.candidates loops perspectives outside modules: order by (perspective, module order)."""
    order = {m: j for j, m in enumerate(MODULES)}
    return sorted(cands, key=lambda c: (int(c["lm"].split("@")[1]), order[c["lm"].split("@")[0]]))


def faloo_task(task, fold_rows, rule, conf_only, subset=None, persp=None):
    """Returns (answered, score, fold_detail). fold_rows: list over folds of [row, row...] (perspective files)."""
    n, T = len(task["train"]), len(task["test"])
    by = {(f[0]["i"], f[0]["t"]): f for f in fold_rows}
    answers, why = [], None
    for t in range(T):
        tests = []
        for i in range(n):
            cands = reorder_by_persp(build(by[(i, t)], subset, persp))
            p = top(cands, rule, conf_only)
            if p is None:
                why = why or "fold abstains"
                return False, None, why, None
            if not np.array_equal(p[0], task["train"][i][1]):
                return False, None, "(a) fold mispredicts held-out demo", None
            tests.append(p[1])
        if not all(np.array_equal(tests[0], q) for q in tests[1:]):
            return False, None, "(b) fold models disagree on test", None
        answers.append(tests[0])
    return True, score_task(task, [[a] for a in answers]), "answer", answers


def load_folds(split, tag):
    src = "agi2-train" if split == "new233" else split
    path = os.path.join(CACHE, f"folds_p{tag}_{src}.jsonl")
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path):
        try:
            r = json.loads(line)
        except Exception:
            continue
        out[r["task"]] = r
    return out


def full_answer(task, row_list, rule, persp=None):
    cands = reorder_by_persp(build(row_list, None, persp))
    if rule == "v5":
        conf = vote.confident(cands)
        s = score_task(task, vote.attempts_from(task, cands, CONF)) if conf else None
    else:
        best = pool_p4(cands)
        conf = confident_p4(best)
        s = None
        if conf:
            att = [[] for _ in task["test"]]
            for p in best:
                if p["evidence"] < CONF:
                    break
                for a, g in zip(att, p["preds"]):
                    if len(a) < 2 and not any(np.array_equal(g, q) for q in a):
                        a.append(g)
            s = score_task(task, att)
    return conf, s


def evaluate(split, variants, persp_tags=("0",), persp=None):
    tasks = tasks_for(split)
    folds = [load_folds(split, tag) for tag in persp_tags]
    full = cache_for(split)
    full_extra = {}
    if len(persp_tags) > 1:
        p = os.path.join(CACHE, f"persp_p1-7_{'agi2-train' if split == 'new233' else split}.jsonl")
        if os.path.exists(p):
            for line in open(p):
                r = json.loads(line)
                full_extra[r["task"]] = r
    keys = [k for k in sorted(tasks) if all(k in f for f in folds) and (len(persp_tags) == 1 or k in full_extra)]
    res = {}
    for name, (rule, conf_only, subset) in variants.items():
        rows = []
        for k in keys:
            task = tasks[k]
            fr = []
            for f0 in folds[0][k]["folds"]:
                group = [f0] + [next(g for g in f[k]["folds"] if g["i"] == f0["i"] and g["t"] == f0["t"]) for f in folds[1:]]
                fr.append(group)
            ans, sc, why, answers = faloo_task(task, fr, rule, conf_only, subset, persp)
            frows = [full[k]] + ([full_extra[k]] if full_extra else [])
            conf, cs = full_answer(task, frows, rule if rule == "p4" else "v5", persp) if subset is None else (None, None)
            agree = None
            if ans:  # (c) the full-data model's top answer equals the fold answer
                fp = top(reorder_by_persp(build(frows, subset, persp)), rule, False)
                agree = fp is not None and all(np.array_equal(a, b) for a, b in zip(answers, fp))
            rows.append(dict(task=k, n=len(task["train"]), answered=ans, score=sc, why=why, conf=conf, conf_score=cs,
                             agree_full=agree))
        res[name] = rows
    return res, len(keys), len(tasks)


def summarise(rows):
    a = [r for r in rows if r["answered"]]
    c = [r for r in rows if r["conf"]]
    keep = [r["task"] for r in rows if r["answered"] and r["conf"]]
    s = dict(n=len(rows), faloo_answered=len(a), faloo_correct=round(sum(r["score"] for r in a), 2),
             faloo_precision=round(sum(r["score"] for r in a) / len(a), 4) if a else None,
             faloo_wrong=[r["task"] for r in a if r["score"] < 1],
             conf_answered=len(c), conf_correct=round(sum(r["conf_score"] for r in c), 2) if c else 0,
             conf_wrong=[r["task"] for r in c if r["conf_score"] < 1],
             both=len(keep), both_correct=round(sum(r["score"] for r in a if r["conf"]), 2),
             conf_dropped=[(r["task"], r["why"], r["conf_score"]) for r in rows if r["conf"] and not r["answered"]],
             faloo_new=[(r["task"], r["score"]) for r in rows if r["answered"] and not r["conf"]],
             why=dict(collections.Counter(r["why"] for r in rows)),
             fa_c=dict(answered=sum(1 for r in a if r["agree_full"]),
                       correct=round(sum(r["score"] for r in a if r["agree_full"]), 2),
                       wrong=[r["task"] for r in a if r["agree_full"] and r["score"] < 1]),
             fa_and_conf=dict(answered=sum(1 for r in a if r["conf"]), correct=round(sum(r["score"] for r in a if r["conf"]), 2)),
             fa_or_conf=dict(answered=sum(1 for r in rows if r["answered"] or r["conf"]),
                             correct=round(sum((r["score"] if r["answered"] else r["conf_score"]) for r in rows
                                               if r["answered"] or r["conf"]), 2)),
             joint_error_rate=round(sum(1 - r["score"] for r in a) / len(rows), 5) if rows else None,
             mean_bound=round(float(np.mean([1 / (r["n"] + 1) for r in rows])), 4) if rows else None,
             by_n={})
    for nn in sorted({r["n"] for r in rows}):
        rr = [r for r in rows if r["n"] == nn]
        aa = [r for r in rr if r["answered"]]
        cc = [r for r in rr if r["conf"]]
        s["by_n"][str(nn)] = dict(tasks=len(rr), faloo=f"{sum(r['score'] for r in aa):.0f}/{len(aa)}",
                                  conf=f"{sum(r['conf_score'] for r in cc):.0f}/{len(cc)}", bound=round(1 / (nn + 1), 3))
    return s


VARIANTS = {
    "v5-top": ("v5", False, None),
    "v5-conf": ("v5", True, None),
    "p4-top": ("p4", False, None),
    "p4-conf": ("p4", True, None),
}
VARIANTS.update({f"{m} alone": ("v5", False, {m}) for m in MODULES})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", nargs="*", default=BASE_SPLITS + ["new233"])
    ap.add_argument("--persp8", nargs="*", default=[])
    ap.add_argument("--out", default=os.path.join(RES, "faloo.json"))
    args = ap.parse_args()
    out = {"p1": {}, "p8": {}}
    for split in args.splits:
        res, n_done, n_all = evaluate(split, VARIANTS)
        out["p1"][split] = dict(n_cached=n_done, n_split=n_all, rows=res,
                                summary={name: summarise(rows) for name, rows in res.items()})
        sm = out["p1"][split]["summary"]
        print(f"{split} ({n_done}/{n_all} tasks) " + " | ".join(
            f"{v}: FA {sm[v]['faloo_correct']:.0f}/{sm[v]['faloo_answered']}" + (f" conf {sm[v]['conf_correct']:.0f}/{sm[v]['conf_answered']}" if v[:2] in ('v5', 'p4') else "")
            for v in ("v5-top", "v5-conf", "p4-top", "p4-conf")), flush=True)
    for split in args.persp8:
        v8 = {k: VARIANTS[k] for k in ("v5-top", "v5-conf", "p4-top", "p4-conf")}
        res, n_done, n_all = evaluate(split, v8, persp_tags=("0", "1-7"))
        out["p8"][split] = dict(n_cached=n_done, n_split=n_all, rows=res,
                                summary={name: summarise(rows) for name, rows in res.items()})
        sm = out["p8"][split]["summary"]
        print(f"[p8] {split} ({n_done}/{n_all}) " + " | ".join(
            f"{v}: FA {sm[v]['faloo_correct']:.0f}/{sm[v]['faloo_answered']} conf {sm[v]['conf_correct']:.0f}/{sm[v]['conf_answered']}" for v in v8), flush=True)
    json.dump(out, open(args.out, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
