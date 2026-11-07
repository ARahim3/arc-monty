"""WS4 step 2: recompute the Monty-ARC v5 vote offline for every module subset (full, leave-one-module-out,
module alone) on every split, from the per-module candidate cache written by run_modules.py.

Valid because (checked in vote.py / monty_arc.py, and empirically by verify.py): each module's candidates depend
only on the task (pure functions; caches are memoisation keyed by grid content; no clocks, randomness or early exit
across modules), and the vote / attempt-2 policy is a deterministic function of the ordered candidate list.
The only time effect in the published notebook is the per-task 120 s SIGALRM of the Kaggle driver (reported apart).

Writes research/monty_eval/results/ablation_raw.json (metrics + per-task outcome sets) and per_task_full.jsonl.
usage: python research/monty_eval/ablate.py
"""
import collections
import json
import multiprocessing as mp
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

from common import ALL_SPLITS, MODULES, ROOT, build_cands, cache_for, subsets, tasks_for  # noqa: E402
from arcmonty.evaluate import score_task  # noqa: E402
from arcmonty.vote import CONFIDENT, attempts_from, confident, pool  # noqa: E402

OUT = os.path.join(ROOT, "research", "monty_eval", "results")
SUBSETS = subsets()


def bucket(e):
    return "1.0" if e >= 0.99 else ("[0.5,1)" if e >= 0.5 else ("(0,0.5)" if e > 0 else "0"))


def eval_cands(task, cands):
    att = attempts_from(task, cands)
    s2 = score_task(task, att)
    s1 = score_task(task, [a[:1] for a in att])
    best = pool(cands)
    conf = confident(cands)
    cs = score_task(task, attempts_from(task, cands, CONFIDENT)) if conf else None
    top = best[0] if best else None
    top_ok = score_task(task, [[g] for g in top["preds"]]) if top else None
    return dict(s2=s2, s1=s1, ans=bool(best), conf=conf, cs=cs,
                top_ev=None if top is None else float(top["evidence"]), top_ok=top_ok,
                top_mods=sorted({v.split("@")[0] for v in top["voters"]}) if top else [],
                n_strong=sum(p["evidence"] >= CONFIDENT for p in best))


def one(args):
    split, key, row, task = args
    res = {name: eval_cands(task, build_cands(row, sub)) for name, sub in SUBSETS.items()}
    times = {m: (row["mods"][m]["wall"], row["mods"][m]["cpu"]) for m in MODULES}
    errs = {m: row["mods"][m]["err"] for m in MODULES if row["mods"][m]["err"]}
    ncand = {m: len(row["mods"][m]["cands"]) for m in MODULES}
    return split, key, res, times, errs, ncand


def summarise(split, per):
    """per: key -> (res, times, errs, ncand)."""
    n = len(per)
    out = dict(n=n, subsets={}, timing={}, errors={})
    solved = {name: sorted(k for k, v in per.items() if v[0][name]["s2"] > 0) for name in SUBSETS}
    for name in SUBSETS:
        r = [v[0][name] for v in per.values()]
        conf = [x for x in r if x["conf"]]
        out["subsets"][name] = dict(
            pass2=round(sum(x["s2"] for x in r), 3), pass2_pct=round(100 * sum(x["s2"] for x in r) / n, 2),
            pass1=round(sum(x["s1"] for x in r), 3), tasks_solved=len(solved[name]),
            answered=sum(x["ans"] for x in r), confident=len(conf),
            confident_correct=round(sum(x["cs"] for x in conf), 3),
            precision=round(sum(x["cs"] for x in conf) / len(conf), 4) if conf else None,
            solved=solved[name])
    full = set(solved["full"])
    alone = {m: set(solved[f"{m} alone"]) for m in MODULES}
    union_alone = set().union(*alone.values())
    out["full_vs_union_alone"] = dict(full=len(full), union_alone=len(union_alone),
                                      lost_by_vote=sorted(union_alone - full), gained_by_vote=sorted(full - union_alone))
    out["modules"] = {}
    for m in MODULES:
        others = set().union(*(alone[j] for j in MODULES if j != m))
        loo = set(solved[f"-{m}"])
        out["modules"][m] = dict(
            alone_solved=len(alone[m]), unique=sorted(alone[m] - others),
            loo_lost=sorted(full - loo), loo_gained=sorted(loo - full),
            in_full_top=sum(1 for k, v in per.items() if v[0]["full"]["s2"] > 0 and m in v[0]["full"]["top_mods"]))
    for m in MODULES:
        w = np.array([v[1][m][0] for v in per.values()])
        c = np.array([v[1][m][1] for v in per.values()])
        out["timing"][m] = dict(wall_mean=round(float(w.mean()), 3), wall_median=round(float(np.median(w)), 3),
                                wall_p90=round(float(np.percentile(w, 90)), 3), wall_max=round(float(w.max()), 2),
                                cpu_mean=round(float(c.mean()), 3), cpu_p90=round(float(np.percentile(c, 90)), 3),
                                cpu_max=round(float(c.max()), 2), cpu_total=round(float(c.sum()), 1))
    tot_w = np.array([sum(v[1][m][0] for m in MODULES) for v in per.values()])
    tot_c = np.array([sum(v[1][m][1] for m in MODULES) for v in per.values()])
    keys = list(per)
    out["timing"]["total"] = dict(wall_mean=round(float(tot_w.mean()), 3), wall_median=round(float(np.median(tot_w)), 3),
                                  wall_p90=round(float(np.percentile(tot_w, 90)), 3), wall_max=round(float(tot_w.max()), 2),
                                  cpu_mean=round(float(tot_c.mean()), 3), cpu_max=round(float(tot_c.max()), 2),
                                  over_60s=[keys[i] for i in np.flatnonzero(tot_w > 60)],
                                  over_120s=[keys[i] for i in np.flatnonzero(tot_w > 120)])
    for v_key, v in per.items():
        for m, e in v[2].items():
            out["errors"].setdefault(m, []).append([v_key, e])
    # calibration by module (module alone: its own top answer) and full system (top answer, attributed to voters)
    cal = {}
    for m in ["full"] + MODULES:
        name = "full" if m == "full" else f"{m} alone"
        b = collections.defaultdict(lambda: [0, 0.0])
        for v in per.values():
            x = v[0][name]
            if x["top_ev"] is None:
                continue
            b[bucket(x["top_ev"])][0] += 1
            b[bucket(x["top_ev"])][1] += x["top_ok"]
        cal[m] = {k: [b[k][0], round(b[k][1], 3)] for k in ("1.0", "[0.5,1)", "(0,0.5)", "0")}
    # full-system top answers by voting module (an answer voted by k modules counts once for each)
    byvoter = {m: collections.defaultdict(lambda: [0, 0.0]) for m in MODULES}
    for v in per.values():
        x = v[0]["full"]
        if x["top_ev"] is None:
            continue
        for m in x["top_mods"]:
            byvoter[m][bucket(x["top_ev"])][0] += 1
            byvoter[m][bucket(x["top_ev"])][1] += x["top_ok"]
    cal["full_by_voter"] = {m: {k: [byvoter[m][k][0], round(byvoter[m][k][1], 3)] for k in ("1.0", "[0.5,1)", "(0,0.5)", "0")}
                            for m in MODULES}
    out["calibration"] = cal
    out["ncand_mean"] = {m: round(float(np.mean([v[3][m] for v in per.values()])), 2) for m in MODULES}
    return out


def main(splits=ALL_SPLITS, procs=8):
    os.makedirs(OUT, exist_ok=True)
    results, per_task_rows = {}, []
    with mp.Pool(procs) as p:
        for split in splits:
            rows, tasks = cache_for(split), tasks_for(split)
            missing = sorted(set(tasks) - set(rows))
            if missing:
                print(f"{split}: {len(missing)} tasks missing from cache, skipping split", flush=True)
                continue
            per = {}
            for s, key, res, times, errs, ncand in p.imap_unordered(
                    one, [(split, k, rows[k], tasks[k]) for k in tasks], chunksize=2):
                per[key] = (res, times, errs, ncand)
            per = dict(sorted(per.items()))
            results[split] = summarise(split, per)
            for key, (res, times, errs, ncand) in per.items():
                per_task_rows.append(dict(split=split, task=key, full=res["full"],
                                          alone={m: res[f"{m} alone"]["s2"] for m in MODULES},
                                          alone_ans={m: res[f"{m} alone"]["ans"] for m in MODULES},
                                          loo={m: res[f"-{m}"]["s2"] for m in MODULES},
                                          times=times, errs=errs, ncand=ncand))
            f = results[split]["subsets"]["full"]
            print(f"{split:10s} n={results[split]['n']:4d} full pass@2 {f['pass2']:6.1f} ({f['pass2_pct']:5.2f}%) "
                  f"answered {f['answered']:4d} confident {f['confident_correct']:.0f}/{f['confident']}", flush=True)
    with open(os.path.join(OUT, "ablation_raw.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    with open(os.path.join(OUT, "per_task_full.jsonl"), "w") as fh:
        for r in per_task_rows:
            fh.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:] or ALL_SPLITS)
