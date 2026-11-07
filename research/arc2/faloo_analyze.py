"""Analyse FA-LOO for Qwen3.8 program synthesis (llm/results/qwen38_faloo_greedy_b16384.jsonl) -> research/arc2/faloo_qwen.json.

Per task (greedy, canonical demo order):
  full verified   A(D)'s final program reproduces every demo
  (a)             every fold program A(D minus i) predicts its held-out demo i
  (b)             all fold programs give the same output on every test input (non-empty)
  (c)             that output equals A(D)'s output
  FA-LOO          (a) and (b): answer = the fold consensus (the bound needs only these)
  FA-LOO + (c)    also (c); only removes answers, so the bound still holds; additionally requires A(D) verified
Baselines: plain (stochastic, temperature 1) verified samples from llm/results/qwen38_ps_b16384.jsonl (the 29/37 number)
and the replicate run; greedy full-data verified.
    python research/arc2/faloo_analyze.py
"""
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from faloo_qwen import OUT, PLAIN, learner_output, load_done  # noqa: E402

CH = json.load(open(os.path.join(ROOT, "data/kaggle_format/agi2_eval_challenges.json")))
SOL = json.load(open(os.path.join(ROOT, "data/kaggle_format/agi2_eval_solutions.json")))
AGI1_IN_EVAL = set()  # filled below if the monty eval notes list them


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def frac_correct(outs_by_test, tid):
    """outs_by_test: {t: grid}; fraction of the task's test outputs that are right (Kaggle per-task score)."""
    s = SOL[tid]
    return sum(outs_by_test.get(t) == s[t] for t in range(len(s))) / len(s)


def by_test(rec):
    out, ver, nok = learner_output(rec)
    if out is None:
        return None, ver
    d = {}
    for q, g in zip(rec["query_ids"], out):
        d[q] = g
    return d, ver


def plain_samples():
    """Stochastic plain PS samples: per task list of (verified, correct_frac)."""
    res = defaultdict(list)
    for f in PLAIN:
        if not os.path.exists(f):
            continue
        for line in open(f):
            r = json.loads(line)
            if "error" in r:
                continue
            rs = [x for x in r["rounds"] if "n_ok" in x]
            v = [x for x in rs if x.get("verified")]
            fr = (sum(v[0]["correct"]) / len(v[0]["correct"])) if v else None
            res[r["task_id"]].append((bool(v), fr, os.path.basename(f), r["sample"]))
    return res


def main():
    done = load_done(OUT)
    for k, v in load_done(OUT.replace(".jsonl", "_C.jsonl")).items():   # phase C ran in a second process
        done.setdefault(k, v)
    tasks = sorted(CH)
    rows = []
    for tid in tasks:
        n = len(CH[tid]["train"])
        nt = len(CH[tid]["test"])
        full = done.get(("full", tid, -1))
        row = dict(task=tid, n_demos=n, n_tests=nt, full_done=full is not None)
        if full is None:
            rows.append(row)
            continue
        fo, fver = by_test(full)
        row["full_verified"] = fver
        row["full_correct"] = frac_correct({int(q[5:]): g for q, g in (fo or {}).items() if q.startswith("test:")}, tid) if fo else 0.0
        folds = [done.get(("fold", tid, i)) for i in range(n)]
        row["folds_done"] = sum(f is not None for f in folds)
        if row["folds_done"] == n:
            held, tests = [], []
            for i, f in enumerate(folds):
                d, _ = by_test(f)
                if d is None:
                    held.append(False)
                    tests.append(None)
                    continue
                demos = sorted(CH[tid]["train"], key=lambda p: (len(p["input"]) * len(p["input"][0]), len(p["input"]),
                                                                len(p["input"][0]), json.dumps(p["input"])))
                held.append(d.get("demo:%d" % i) == demos[i]["output"])
                tests.append(tuple(json.dumps(d.get("test:%d" % t)) for t in range(nt)))
            a = all(held)
            b = all(t is not None for t in tests) and len(set(tests)) == 1 and "null" not in tests[0]
            row.update(held_ok=sum(held), cond_a=a, cond_b=b)
            if b:
                cons = {t: json.loads(tests[0][t]) for t in range(nt)}
                row["consensus_correct"] = frac_correct(cons, tid)
                full_tests = tuple(json.dumps((fo or {}).get("test:%d" % t)) for t in range(nt))
                row["cond_c"] = full_tests == tests[0]
            else:
                row["cond_c"] = False
            row["faloo"] = a and b
            row["faloo_c"] = a and b and row["cond_c"] and fver
            # relaxed rules (no 1/(n+1) guarantee), for the precision/coverage trade-off
            full_tests = tuple(json.dumps((fo or {}).get("test:%d" % t)) for t in range(nt))
            agree_full = sum(t == full_tests for t in tests)
            row["folds_agree_with_full"] = agree_full
            row["relax_bc"] = bool(fver and agree_full == n)                    # (b)+(c), held-out not required
            row["relax_major"] = bool(fver and agree_full * 2 > n)              # majority of folds reproduce A(D)'s test output
            row["relax_a_minus1"] = bool(fver and sum(held) >= n - 1 and agree_full >= n - 1)
        for kind in ("rev", "rep"):
            r = done.get((kind, tid, -1))
            if r is not None:
                d, v = by_test(r)
                same = d is not None and fo is not None and all(d.get("test:%d" % t) == fo.get("test:%d" % t) for t in range(nt))
                row[kind + "_same_test_output"] = bool(same)
                row[kind + "_verified"] = v
        rows.append(row)

    def rate(sel, key):
        xs = [r for r in rows if sel(r)]
        k = sum(r[key] for r in xs)
        return dict(answered=len(xs), correct=round(k, 2), precision=(k / len(xs) if xs else float("nan")),
                    ci95=wilson(round(k), len(xs)))

    ps = plain_samples()
    orig = [(v, fr) for t, xs in ps.items() for v, fr, f, s in xs if f == "qwen38_ps_b16384.jsonl" and v]
    allv = [(v, fr) for t, xs in ps.items() for v, fr, f, s in xs if v]
    k_o = sum(fr for _, fr in orig)
    k_a = sum(fr for _, fr in allv)
    summary = {
        "plain_verified_samples_original": dict(answered=len(orig), correct=k_o, precision=k_o / max(1, len(orig)),
                                                ci95=wilson(round(k_o), len(orig))),
        "plain_verified_samples_all": dict(answered=len(allv), correct=k_a, precision=k_a / max(1, len(allv)),
                                           ci95=wilson(round(k_a), len(allv))),
        "greedy_full_verified": rate(lambda r: r.get("full_verified"), "full_correct"),
        "faloo_(a)(b)": rate(lambda r: r.get("faloo"), "consensus_correct"),
        "faloo_+(c)": rate(lambda r: r.get("faloo_c"), "consensus_correct"),
        "relaxed_(b)(c)_no_heldout": rate(lambda r: r.get("relax_bc"), "full_correct"),
        "relaxed_majority_folds_agree": rate(lambda r: r.get("relax_major"), "full_correct"),
        "relaxed_all_but_one_fold": rate(lambda r: r.get("relax_a_minus1"), "full_correct"),
        "greedy_verified_but_not_certified": rate(lambda r: r.get("full_verified") and "faloo_c" in r and not r["faloo_c"], "full_correct"),
        "tasks_with_full_run": sum(r["full_done"] for r in rows),
        "tasks_with_all_folds": sum(1 for r in rows if r.get("folds_done") == r["n_demos"]),
        "rev_same_output": [sum(r.get("rev_same_test_output", False) for r in rows), sum("rev_same_test_output" in r for r in rows)],
        "rep_same_output": [sum(r.get("rep_same_test_output", False) for r in rows), sum("rep_same_test_output" in r for r in rows)],
    }
    # stochastic-verified task set (the lead's population): FA-LOO coverage there
    pv = {t for t, xs in ps.items() if any(v for v, *_ in xs)}
    summary["plain_verified_tasks"] = len(pv)
    summary["faloo_c_within_plain_verified_tasks"] = rate(lambda r: r["task"] in pv and r.get("faloo_c"), "consensus_correct")
    summary["plain_verified_tasks_with_all_folds"] = sum(1 for r in rows if r["task"] in pv and r.get("folds_done") == r["n_demos"])
    byn = {}
    for nd in sorted({r["n_demos"] for r in rows}):
        xs = [r for r in rows if r["n_demos"] == nd and r.get("full_verified") and "faloo_c" in r]
        byn[nd] = dict(greedy_verified_with_folds=len(xs), greedy_correct=sum(r["full_correct"] for r in xs),
                       certified=sum(r["faloo_c"] for r in xs),
                       certified_correct=sum(r.get("consensus_correct", 0) for r in xs if r["faloo_c"]),
                       bound=round(1 / (nd + 1), 3))
    summary["by_n_demos"] = byn
    json.dump(dict(summary=summary, tasks=rows), open(os.path.join(HERE, "faloo_qwen.json"), "w"), indent=1)
    for k, v in summary.items():
        print(f"{k:42s} {v}")
    print()
    print("task      n  tests full_ver full_ok folds held_ok (a) (b) (c) FA-LOO+(c) cons_ok rev_same rep_same plain_ver")
    for r in rows:
        if not r.get("full_verified") and r["task"] not in pv and not r.get("faloo"):
            continue
        print(f"{r['task']} {r['n_demos']:2d} {r['n_tests']:3d}   {str(r.get('full_verified', '-')):5s} {r.get('full_correct', 0):5.2f} "
              f"{r.get('folds_done', 0):3d}/{r['n_demos']} {r.get('held_ok', '-')!s:>5} {str(r.get('cond_a', '-'))[:1]:>3} "
              f"{str(r.get('cond_b', '-'))[:1]:>3} {str(r.get('cond_c', '-'))[:1]:>3} {str(r.get('faloo_c', '-'))[:1]:>6} "
              f"{r.get('consensus_correct', '-')!s:>8} {str(r.get('rev_same_test_output', '-'))[:1]:>6} "
              f"{str(r.get('rep_same_test_output', '-'))[:1]:>7} {sum(v for v, *_ in ps.get(r['task'], []))}/{len(ps.get(r['task'], []))}")


if __name__ == "__main__":
    main()
