"""Analysis for FA-LOO on sampling Qwen3.8-27B (plan: research/arc2/faloo_qwen_sampling.md section 0).

    python research/arc2/faloo_sampling_analyze.py --check-greedy     # must reproduce research/arc2/faloo_qwen.json exactly
    python research/arc2/faloo_sampling_analyze.py                    # stage 1 and stage 2 (whatever is complete)
    python research/arc2/faloo_sampling_analyze.py --selftest         # unit checks of the statistics

Units. Task level (primary, as faloo_analyze.py): one task = one unit, the multi-test tuple must agree, and a multi-test task
counts its fraction of test outputs right; Wilson on the rounded count, as faloo_analyze.py. Pair level (one test pair = one item,
as research/monty_heldout.md): (a) as above, (b) and (c) per test pair. CIs for pair-level numbers: percentile cluster bootstrap
by task, 10,000 resamples, fixed seed. No record is dropped: a task without all its folds is reported as incomplete.
"""
import argparse
import glob
import json
import math
import os
import random
import sys
import zlib
from collections import Counter, defaultdict
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "llm/results")
GREEDY = os.path.join(RESULTS, "qwen38_faloo_greedy_b16384.jsonl")
OLD_JSON = os.path.join(HERE, "faloo_qwen.json")
STAGE_FILES = {1: os.path.join(RESULTS, "qwen38_faloo_sampling_b32768.jsonl"),
               2: os.path.join(RESULTS, "qwen38_faloo_sampling_concept_b32768.jsonl"),
               "1b": os.path.join(RESULTS, "qwen38_faloo_sampling_plain_b32768.jsonl")}
GLOBAL_SEED = 20261101
OUT_JSON = os.path.join(HERE, "faloo_qwen_sampling.json")
CONCEPT_DIR = os.path.join(ROOT, "external/judge/conceptarc/repo/corpus")
BOOT = 10000
BOOT_SEED = 20261101


# ------------------------------------------------------------------------------------------------ data
def load_agi2():
    ch = json.load(open(os.path.join(ROOT, "data/kaggle_format/agi2_eval_challenges.json")))
    sol = json.load(open(os.path.join(ROOT, "data/kaggle_format/agi2_eval_solutions.json")))
    return ch, sol


def load_concept(path=CONCEPT_DIR):
    """ConceptARC corpus: JSON only. Task id = Group/File, as research/monty_heldout (without the #test suffix)."""
    ch, sol = {}, {}
    for f in sorted(glob.glob(os.path.join(path, "*", "*.json"))):
        d = json.load(open(f))
        tid = os.path.relpath(f, path)[:-5]
        ch[tid] = {"train": [{"input": p["input"], "output": p["output"]} for p in d["train"]],
                   "test": [{"input": p["input"]} for p in d["test"]]}
        sol[tid] = [p["output"] for p in d["test"]]
    return ch, sol


def gkey(g):
    return (len(g) * len(g[0]), len(g), len(g[0]), json.dumps(g))


def learner_output(rec):
    rounds = [r for r in rec.get("rounds", []) if "test_out" in r]
    if not rounds:
        return None, False, -1
    v = [r for r in rounds if r.get("verified")]
    r = v[0] if v else rounds[-1]
    return r["test_out"], bool(v), r.get("n_ok", -1)


def read_records(*paths):
    """First good record per (kind, task, fold), as load_done in faloo_qwen.py; returns (done, n_error_records)."""
    done, errs = {}, 0
    for path in paths:
        if not os.path.exists(path):
            continue
        for line in open(path):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "error" in r:
                errs += 1
                continue
            done.setdefault((r["kind"], r["task_id"], r["fold"]), r)
    return done, errs


def by_query(rec):
    out, ver, _ = learner_output(rec)
    if out is None:
        return None, ver
    return dict(zip(rec["query_ids"], out)), ver


# ------------------------------------------------------------------------------------------------ rows
def task_row(tid, done, ch, sol):
    """One row per task; same fields and definitions as faloo_analyze.py, plus per-pair fields."""
    n = len(ch[tid]["train"])
    nt = len(ch[tid]["test"])
    full = done.get(("full", tid, -1))
    row = dict(task=tid, n_demos=n, n_tests=nt, full_done=full is not None)
    if full is None:
        return row
    s = sol[tid]
    frac = lambda d: sum(d.get(t) == s[t] for t in range(nt)) / nt
    fo, fver = by_query(full)
    row["full_verified"] = fver
    row["full_correct"] = frac({int(q[5:]): g for q, g in fo.items() if q.startswith("test:")}) if fo else 0.0
    folds = [done.get(("fold", tid, i)) for i in range(n)]
    row["folds_done"] = sum(f is not None for f in folds)
    if row["folds_done"] != n:
        return row
    demos = sorted(ch[tid]["train"], key=lambda p: gkey(p["input"]))
    held, tests, per_test = [], [], [[] for _ in range(nt)]
    for i, f in enumerate(folds):
        d, _ = by_query(f)
        if d is None:
            held.append(False)
            tests.append(None)
            for t in range(nt):
                per_test[t].append(None)
            continue
        held.append(d.get("demo:%d" % i) == demos[i]["output"])
        tests.append(tuple(json.dumps(d.get("test:%d" % t)) for t in range(nt)))
        for t in range(nt):
            per_test[t].append(d.get("test:%d" % t))
    a = all(held)
    b = all(t is not None for t in tests) and len(set(tests)) == 1 and "null" not in tests[0]
    row.update(held_ok=sum(held), cond_a=a, cond_b=b)
    full_tests = tuple(json.dumps((fo or {}).get("test:%d" % t)) for t in range(nt))
    if b:
        cons = {t: json.loads(tests[0][t]) for t in range(nt)}
        row["consensus_correct"] = frac(cons)
        row["cond_c"] = full_tests == tests[0]
    else:
        row["cond_c"] = False
    row["faloo"] = a and b
    row["faloo_c"] = a and b and row["cond_c"] and fver
    agree_full = sum(t == full_tests for t in tests)
    row["folds_agree_with_full"] = agree_full
    row["relax_bc"] = bool(fver and agree_full == n)
    row["relax_major"] = bool(fver and agree_full * 2 > n)
    row["relax_a_minus1"] = bool(fver and sum(held) >= n - 1 and agree_full >= n - 1)
    for kind in ("rev", "rep"):
        r = done.get((kind, tid, -1))
        if r is not None:
            d, v = by_query(r)
            same = d is not None and fo is not None and all(d.get("test:%d" % t) == fo.get("test:%d" % t) for t in range(nt))
            row[kind + "_same_test_output"] = bool(same)
            row[kind + "_verified"] = v
    # pair level: (a) is per task; (b), (c) per test pair
    pairs = []
    for t in range(nt):
        fv = per_test[t]
        fgrid = (fo or {}).get("test:%d" % t)
        b_t = all(g is not None for g in fv) and all(g == fv[0] for g in fv)
        cons = fv[0] if b_t else None
        pairs.append(dict(
            fa=bool(a and b_t), fa_right=bool(a and b_t and cons == s[t]),
            fa_c=bool(a and b_t and fver and fgrid == cons), fa_c_right=bool(a and b_t and fver and fgrid == cons and cons == s[t]),
            a_only=bool(a and fgrid is not None), a_only_right=bool(a and fgrid is not None and fgrid == s[t]),
            ver=bool(fver), ver_right=bool(fver and fgrid == s[t]), full_right=bool(fgrid == s[t])))
    row["pairs"] = pairs
    return row


# ------------------------------------------------------------------------------------------------ statistics
def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def clopper_pearson(k, n, alpha=0.05):
    """Exact interval by bisection on the binomial tail (no scipy on the laptop venv assumed)."""
    if n == 0:
        return (float("nan"), float("nan"))

    def tail_ge(p, k):
        return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))

    def tail_le(p, k):
        return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))

    lo = 0.0
    if k > 0:
        a, b = 0.0, 1.0
        for _ in range(80):
            m = (a + b) / 2
            a, b = (a, m) if tail_ge(m, k) > alpha / 2 else (m, b)
        lo = (a + b) / 2
    hi = 1.0
    if k < n:
        a, b = 0.0, 1.0
        for _ in range(80):
            m = (a + b) / 2
            a, b = (m, b) if tail_le(m, k) > alpha / 2 else (a, m)
        hi = (a + b) / 2
    return (lo, hi)


def hypergeom_le(V, W, C, x):
    """P(X <= x): X = wrong tasks in a uniformly random C-subset of V tasks of which W are wrong."""
    return sum(comb(W, i) * comb(V - W, C - i) for i in range(0, x + 1)) / comb(V, C) if C <= V else float("nan")


def auroc(scores_right, scores_wrong):
    if not scores_right or not scores_wrong:
        return float("nan")
    return sum((a > b) + 0.5 * (a == b) for a in scores_right for b in scores_wrong) / (len(scores_right) * len(scores_wrong))


def auroc_exact_p(scores_right, scores_wrong):
    """Exact one-sided permutation p (H1: right tasks score higher), ties by midranks, by dynamic programming on rank sums."""
    vals = scores_right + scores_wrong
    N, k = len(vals), len(scores_right)
    if not scores_right or not scores_wrong:
        return float("nan")
    order = sorted(vals)
    ranks2 = {}                                                   # doubled midrank per value, an integer
    i = 0
    while i < N:
        j = i
        while j + 1 < N and order[j + 1] == order[i]:
            j += 1
        ranks2[order[i]] = (i + 1) + (j + 1)
        i = j + 1
    obs = sum(ranks2[v] for v in scores_right)
    counts = [defaultdict(int) for _ in range(k + 1)]
    counts[0][0] = 1
    for v in vals:
        r = ranks2[v]
        for m in range(k - 1, -1, -1):
            for s, c in list(counts[m].items()):
                counts[m + 1][s + r] += c
    total = sum(counts[k].values())
    return sum(c for s, c in counts[k].items() if s >= obs) / total


def boot_ci(tasks, stat, B=BOOT, seed=BOOT_SEED):
    """Percentile cluster bootstrap by task. stat(list_of_rows) -> number or None (undefined resample: skipped)."""
    rng = random.Random(seed)
    out = []
    n = len(tasks)
    for _ in range(B):
        v = stat(rng.choices(tasks, k=n))
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            out.append(v)
    out.sort()
    if not out:
        return (float("nan"), float("nan"))
    return (out[int(0.025 * len(out))], out[min(len(out) - 1, int(0.975 * len(out)))])


# ------------------------------------------------------------------------------------------------ summaries
def rate(rows, sel, key, n_cov=None):
    xs = [r for r in rows if sel(r)]
    k = sum(r[key] for r in xs)
    d = dict(answered=len(xs), correct=round(k, 2), precision=(k / len(xs) if xs else float("nan")), ci95=wilson(round(k), len(xs)))
    if n_cov:
        d["coverage"] = len(xs) / n_cov
    d["fully_right"] = sum(r[key] == 1 for r in xs)
    return d


def summary_old_format(rows):
    """The summary fields of faloo_qwen.json, for the reproduction check."""
    s = {
        "greedy_full_verified": rate(rows, lambda r: r.get("full_verified"), "full_correct"),
        "faloo_(a)(b)": rate(rows, lambda r: r.get("faloo"), "consensus_correct"),
        "faloo_+(c)": rate(rows, lambda r: r.get("faloo_c"), "consensus_correct"),
        "relaxed_(b)(c)_no_heldout": rate(rows, lambda r: r.get("relax_bc"), "full_correct"),
        "relaxed_majority_folds_agree": rate(rows, lambda r: r.get("relax_major"), "full_correct"),
        "relaxed_all_but_one_fold": rate(rows, lambda r: r.get("relax_a_minus1"), "full_correct"),
        "greedy_verified_but_not_certified": rate(rows, lambda r: r.get("full_verified") and "faloo_c" in r and not r["faloo_c"], "full_correct"),
        "tasks_with_full_run": sum(r["full_done"] for r in rows),
        "tasks_with_all_folds": sum(1 for r in rows if r.get("folds_done") == r["n_demos"]),
        "rev_same_output": [sum(r.get("rev_same_test_output", False) for r in rows), sum("rev_same_test_output" in r for r in rows)],
        "rep_same_output": [sum(r.get("rep_same_test_output", False) for r in rows), sum("rep_same_test_output" in r for r in rows)],
    }
    byn = {}
    for nd in sorted({r["n_demos"] for r in rows}):
        xs = [r for r in rows if r["n_demos"] == nd and r.get("full_verified") and "faloo_c" in r]
        byn[str(nd)] = dict(greedy_verified_with_folds=len(xs), greedy_correct=sum(r["full_correct"] for r in xs),
                            certified=sum(r["faloo_c"] for r in xs),
                            certified_correct=sum(r.get("consensus_correct", 0) for r in xs if r["faloo_c"]),
                            bound=round(1 / (nd + 1), 3))
    s["by_n_demos"] = byn
    return s


def verified_analysis(rows):
    """Primary comparisons within verified tasks that have all folds: hypergeometric rejection test and AUROC."""
    V = [r for r in rows if r.get("full_verified") and r.get("folds_done") == r["n_demos"]]
    wrong = [r for r in V if r["full_correct"] < 1]
    right = [r for r in V if r["full_correct"] == 1]
    cert = [r for r in V if r.get("faloo_c")]
    kept = [r for r in cert if r["full_correct"] < 1]
    res = dict(verified=len(V), verified_right_fraction=round(sum(r["full_correct"] for r in V), 2), fully_right=len(right),
               not_fully_right=len(wrong), certified=len(cert), wrong_kept=len(kept), wrong_rejected=len(wrong) - len(kept))
    res["hypergeom_p_kept_or_fewer"] = hypergeom_le(len(V), len(wrong), len(cert), len(kept)) if V else float("nan")
    res["hypergeom_note"] = "P(a uniformly random subset of the certified size keeps <= the observed number of not-fully-right tasks)"
    sr = [r["held_ok"] / r["n_demos"] for r in right]
    sw = [r["held_ok"] / r["n_demos"] for r in wrong]
    res["auroc_held_rate_vs_fully_right"] = auroc(sr, sw)
    res["auroc_exact_one_sided_p"] = auroc_exact_p(sr, sw)
    if V:
        def st(xs):
            a = [r["held_ok"] / r["n_demos"] for r in xs if r["full_correct"] == 1]
            b = [r["held_ok"] / r["n_demos"] for r in xs if r["full_correct"] < 1]
            return auroc(a, b)
        res["auroc_ci95_bootstrap"] = boot_ci(V, st)
    thr = {}
    for t in (1.0, 0.75, 2 / 3, 0.5, 1 / 3, 0.01):
        S = [r for r in V if r["held_ok"] / r["n_demos"] >= t]
        thr["%.2f" % t] = dict(answered=len(S), right=round(sum(r["full_correct"] for r in S), 2), wrong_kept=sum(r["full_correct"] < 1 for r in S))
    res["held_rate_thresholds_descriptive"] = thr
    res["verified_tasks"] = [dict(task=r["task"], n=r["n_demos"], held=r["held_ok"], right=r["full_correct"], certified=bool(r.get("faloo_c"))) for r in V]
    return res


def by_n_table(rows):
    """Results by number of demos; joint = sum over answered tasks of (1 - fraction right) / tasks with all folds, against 1/(n+1)."""
    out = {}
    cc = [r for r in rows if r.get("folds_done") == r["n_demos"] and r.get("full_done")]
    for nd in sorted({r["n_demos"] for r in cc}):
        xs = [r for r in cc if r["n_demos"] == nd]
        V = [r for r in xs if r["full_verified"]]
        ab = [r for r in xs if r["faloo"]]
        abc = [r for r in xs if r["faloo_c"]]
        out[str(nd)] = dict(tasks=len(xs), verified=len(V), verified_right=round(sum(r["full_correct"] for r in V), 2),
                            ab_answered=len(ab), ab_right=round(sum(r["consensus_correct"] for r in ab), 2),
                            abc_answered=len(abc), abc_right=round(sum(r["consensus_correct"] for r in abc), 2),
                            joint_ab=sum(1 - r["consensus_correct"] for r in ab) / len(xs),
                            joint_abc=sum(1 - r["consensus_correct"] for r in abc) / len(xs),
                            bound=1 / (nd + 1))
    xs = cc
    if xs:
        out["all"] = dict(tasks=len(xs), joint_ab=sum(1 - r["consensus_correct"] for r in xs if r["faloo"]) / len(xs),
                          joint_abc=sum(1 - r["consensus_correct"] for r in xs if r["faloo_c"]) / len(xs),
                          bound_mean=sum(1 / (r["n_demos"] + 1) for r in xs) / len(xs))
    return out


def pair_table(rows):
    """Pair-level rule table with cluster bootstrap CIs by task (units of research/monty_heldout.md Table 1)."""
    cc = [r for r in rows if "pairs" in r]
    items = sum(len(r["pairs"]) for r in cc)
    rules = {"fa_c": "FA-LOO (a)+(b)+(c)", "fa": "FA-LOO (a)+(b)", "a_only": "(a) + A(D)'s answer", "ver": "verified only (fit to demos)"}
    out = dict(items=items, clusters=len(cc), rules={})
    for k, name in rules.items():
        ans = sum(p[k] for r in cc for p in r["pairs"])
        rig = sum(p[k + "_right"] for r in cc for p in r["pairs"])

        def st(xs, k=k):
            a = sum(p[k] for r in xs for p in r["pairs"])
            return (sum(p[k + "_right"] for r in xs for p in r["pairs"]) / a) if a else None
        d = dict(name=name, answered=ans, right=rig, precision=(rig / ans if ans else float("nan")),
                 ci95_cluster=boot_ci(cc, st) if ans else (float("nan"), float("nan")),
                 coverage=ans / items if items else float("nan"), joint=(ans - rig) / items if items else float("nan"),
                 tasks_answered=sum(any(p[k] for p in r["pairs"]) for r in cc),
                 tasks_with_wrong=sum(any(p[k] and not p[k + "_right"] for p in r["pairs"]) for r in cc))
        ta = sum(1 for r in cc if any(p[k] for p in r["pairs"]))
        tr = sum(1 for r in cc if any(p[k] for p in r["pairs"]) and all(p[k + "_right"] for p in r["pairs"] if p[k]))
        d["tasks_all_right_clopper_pearson"] = (tr, ta, clopper_pearson(tr, ta))
        out["rules"][k] = d
    out["full_right_any"] = dict(right=sum(p["full_right"] for r in cc for p in r["pairs"]), of=items)
    out["worst_case_mean"] = (sum(len(r["pairs"]) / (r["n_demos"] + 1) for r in cc) / items) if items else float("nan")
    return out


def tokens(done):
    t = defaultdict(int)
    n = Counter()
    rounds = Counter()
    forced = fr = 0
    for (kind, _, _), r in done.items():
        t[kind] += r.get("gen_tokens", 0)
        n[kind] += 1
        for x in r.get("rounds", []):
            rounds[kind] += 1
            fr += 1
            forced += bool(x.get("forced"))
    return dict(gen_tokens_by_kind=dict(t), jobs_by_kind=dict(n), rounds_by_kind=dict(rounds), gen_tokens_total=sum(t.values()),
                forced_round_fraction=(forced / fr if fr else float("nan")))


def analyse(done, ch, sol, errors=0, label=""):
    rows = [task_row(t, done, ch, sol) for t in sorted(ch)]
    complete = [r for r in rows if r.get("full_done") and r.get("folds_done") == r["n_demos"]]
    N = len(complete)
    res = dict(label=label, tasks_in_set=len(ch), tasks_complete=N, error_records_seen=errors)
    res["expected_jobs"] = sum(1 + len(ch[t]["train"]) for t in ch)
    res["jobs_done"] = len([k for k in done if k[0] in ("full", "fold")])
    res["tests_in_set"] = sum(len(ch[t]["test"]) for t in ch)
    cover_rows = complete
    res["task_level"] = dict(
        verified_only=rate(cover_rows, lambda r: r.get("full_verified"), "full_correct", N),
        ab=rate(cover_rows, lambda r: r.get("faloo"), "consensus_correct", N),
        abc=rate(cover_rows, lambda r: r.get("faloo_c"), "consensus_correct", N),
        verified_not_certified=rate(cover_rows, lambda r: r.get("full_verified") and not r["faloo_c"], "full_correct"),
        ab_not_verified=rate(cover_rows, lambda r: r.get("faloo") and not r.get("full_verified"), "consensus_correct"))
    res["relaxed_descriptive"] = {k: rate(cover_rows, lambda r, k=k: r.get(k), "full_correct", N) for k in ("relax_bc", "relax_major", "relax_a_minus1")}
    res["verified_analysis"] = verified_analysis(rows)
    res["by_n"] = by_n_table(rows)
    res["pair_level"] = pair_table(rows)
    res["tokens"] = tokens(done)
    fv = [r for r in complete if r["full_verified"]]
    res["fold_held_out_rate"] = dict(all_tasks=[sum(r["held_ok"] for r in complete), sum(r["n_demos"] for r in complete)],
                                     verified_tasks=[sum(r["held_ok"] for r in fv), sum(r["n_demos"] for r in fv)])
    res["full_right_any_task_level"] = round(sum(r.get("full_correct", 0) for r in complete), 2)
    res["rows"] = rows
    return res


def compare_greedy(new, old):
    """Descriptive: same tasks, sampling at 32k per round vs greedy at 16k per round."""
    nr = {r["task"]: r for r in new["rows"]}
    or_ = {r["task"]: r for r in old["rows"]}
    both = [t for t in nr if t in or_ and nr[t].get("folds_done") == nr[t]["n_demos"] and or_[t].get("folds_done") == or_[t]["n_demos"]]
    v_new = {t for t in both if nr[t]["full_verified"]}
    v_old = {t for t in both if or_[t]["full_verified"]}
    c_new = {t for t in both if nr[t]["faloo_c"]}
    c_old = {t for t in both if or_[t]["faloo_c"]}
    return dict(tasks=len(both), verified_sampling=len(v_new), verified_greedy=len(v_old), verified_both=len(v_new & v_old),
                precision_verified_sampling=sum(nr[t]["full_correct"] for t in v_new) / max(1, len(v_new)),
                precision_verified_greedy=sum(or_[t]["full_correct"] for t in v_old) / max(1, len(v_old)),
                certified_sampling=sorted(c_new), certified_greedy=sorted(c_old), certified_both=sorted(c_new & c_old),
                ab_sampling=sum(nr[t]["faloo"] for t in both), ab_greedy=sum(or_[t]["faloo"] for t in both),
                held_rate_sampling=sum(nr[t]["held_ok"] for t in both) / max(1, sum(nr[t]["n_demos"] for t in both)),
                held_rate_greedy=sum(or_[t]["held_ok"] for t in both) / max(1, sum(or_[t]["n_demos"] for t in both)),
                full_right_sampling=sum(nr[t]["full_correct"] for t in both), full_right_greedy=sum(or_[t]["full_correct"] for t in both))


def compare_monty(new):
    """Stage 2 next to Monty's Table 1 (research/monty_heldout.md, real role), plus overlap per test pair (descriptive)."""
    base = os.path.join(ROOT, "research/monty_heldout/results")
    an = json.load(open(os.path.join(base, "concept_analysis.json")))["rules"]
    table = {}
    for k, name in (("fc", "FA-LOO + (c)"), ("fa", "FA-LOO (a)+(b)"), ("a", "(a) only"), ("v5", "v5 heuristic"), ("fit", "fit to demos only")):
        x = an[k]["real"]
        table[name] = dict(correct=x["correct"], answered=x["answered"], precision=x["precision"], ci=x["ci"], tasks_answered=x["tasks_answered"], tasks_wrong=x["tasks_wrong"],
                           coverage=x["answered"] / 480, joint=(x["answered"] - x["correct"]) / 480)
    monty = {}
    for line in open(os.path.join(base, "concept_base.jsonl")):
        r = json.loads(line)
        t, ti = r["task"].split("#")
        monty[(t, int(ti))] = r["cfg"]["full"][str(r["m"] - 1)]["fc"]
    assert sum(v is not None for v in monty.values()) == 44 and sum(bool(v) for v in monty.values()) == 35
    both = both_right = q_only = q_only_right = m_only = m_only_right = 0
    cmp_items = 0
    tasks_q, tasks_m = set(), set()
    for r in new["rows"]:
        if "pairs" not in r:
            continue
        for t, p in enumerate(r["pairs"]):
            cmp_items += 1
            mv = monty.get((r["task"], t))
            q = p["fa_c"]
            if q:
                tasks_q.add(r["task"])
            if mv is not None:
                tasks_m.add(r["task"])
            if q and mv is not None:
                both += 1
                both_right += bool(p["fa_c_right"] and mv)
            elif q:
                q_only += 1
                q_only_right += p["fa_c_right"]
            elif mv is not None:
                m_only += 1
                m_only_right += bool(mv)
    return dict(monty_table=table, overlap=dict(items=cmp_items, both=both, both_both_right=both_right, qwen_only=q_only, qwen_only_right=q_only_right,
                                                monty_only=m_only, monty_only_right=m_only_right, tasks_qwen=len(tasks_q), tasks_monty=len(tasks_m),
                                                tasks_both=len(tasks_q & tasks_m)))


def verify_run(path, done, ch, out_base, expected=None):
    """Record checks: counts per kind and task, one record per job in the file, query ids, settings, seed labels, error records."""
    raw = []
    if os.path.exists(path):
        for line in open(path):
            try:
                raw.append(json.loads(line))
            except Exception:
                pass
    keys = Counter((r.get("kind"), r.get("task_id"), r.get("fold")) for r in raw)
    good = [r for r in raw if "error" not in r]
    res = dict(records=len(raw), error_records=len(raw) - len(good), duplicate_keys=sum(v > 1 for v in keys.values()), kinds=dict(Counter(r["kind"] for r in good)))
    per = Counter(r["task_id"] for r in good)
    exp = expected or (lambda t: 1 + len(ch[t]["train"]))
    res["tasks_with_expected_records"] = sum(per[t] == exp(t) for t in ch)
    res["tasks_missing_jobs"] = sorted(t for t in ch if per[t] != exp(t))[:30]
    bad_q = 0
    for r in good:
        n_t = len(ch[r["task_id"]]["test"])
        want = {"test:%d" % t for t in range(n_t)} | ({"demo:%d" % r["fold"]} if r["kind"] == "fold" else set())
        bad_q += set(r["query_ids"]) != want
    res["records_with_wrong_query_ids"] = bad_q
    res["decoding"] = dict(Counter(r.get("decoding") for r in good))
    res["sampling"] = dict(Counter(json.dumps(r.get("sampling"), sort_keys=True) for r in good))
    res["budget"] = dict(Counter(r.get("budget") for r in good))
    res["seed_sent"] = dict(Counter(r.get("seed_sent") for r in good))
    seeds = [x["seed"] for r in good for x in r.get("rounds", []) if "seed" in x]
    res["seed_labels"] = [len(seeds), len(set(seeds))]
    rnds = [x for r in good for x in r.get("rounds", [])]
    res["rounds_total"] = len(rnds)
    res["rounds_skipped_for_context"] = sum("skipped" in x for x in rnds)
    res["rounds_with_error"] = sum("error" in x for x in rnds)
    res["max_prompt_len"] = max((x.get("prompt_len", 0) for x in rnds), default=0)
    res["rounds_without_code"] = sum(x.get("code", "x") is None for x in rnds)
    res["max_rounds"] = max((len(r["rounds"]) for r in good), default=0)
    res["vms"] = dict(Counter(r.get("vm") for r in good))
    # restarts: a job started more than once (claim lines from every VM), or continued from a checkpoint after a killed round
    starts = Counter()
    for f in glob.glob(out_base + ".claims_*.txt"):
        for line in open(f):
            p = line.split()
            if len(p) == 5:
                starts[(p[0], p[1], int(p[2]))] += 1
    res["jobs_started_more_than_once"] = sum(v > 1 for v in starts.values())
    res["job_starts_total"] = sum(starts.values())
    res["jobs_resumed_from_checkpoint"] = sum(r.get("resumed_from_round", 0) > 0 for r in good)
    restarted = {r["task_id"] for r in good if starts[(r["kind"], r["task_id"].replace(" ", "_"), r["fold"])] > 1 or r.get("resumed_from_round", 0) > 0}
    res["tasks_with_a_restarted_job"] = len(restarted)
    return res, restarted


def sensitivity_no_restart(rows, restarted):
    """Descriptive: the primary task-level table on tasks where no job was restarted."""
    xs = [r for r in rows if r["task"] not in restarted and r.get("full_done") and r.get("folds_done") == r["n_demos"]]
    N = len(xs)
    return dict(tasks=N, verified_only=rate(xs, lambda r: r.get("full_verified"), "full_correct", N), ab=rate(xs, lambda r: r.get("faloo"), "consensus_correct", N),
                abc=rate(xs, lambda r: r.get("faloo_c"), "consensus_correct", N))


# ------------------------------------------------------------------------------------------------ plan addendum 2
def run_view(rec, tid, ch, sol):
    """One run: outputs on the test inputs, verified flag, test fraction right, tokens; for a fold also h (held-out right) and vh."""
    nt = len(sol[tid])
    out, ver, _ = learner_output(rec)
    if "query_ids" in rec:
        d = dict(zip(rec["query_ids"], out)) if out is not None else {}
    else:                                           # old plain files: test_out in test order, no query ids
        d = {"test:%d" % t: g for t, g in enumerate(out)} if out is not None else {}
    tests = [d.get("test:%d" % t) for t in range(nt)]
    v = dict(ver=ver, tests=tests, t=sum(tests[t] == sol[tid][t] for t in range(nt)) / nt, tokens=rec.get("gen_tokens", 0), kind=rec.get("kind", "plain"))
    if rec.get("kind") == "fold":
        demos = sorted(ch[tid]["train"], key=lambda p: gkey(p["input"]))
        v["h"] = bool(out is not None and d.get("demo:%d" % rec["fold"]) == demos[rec["fold"]]["output"])
        v["vh"] = bool(ver and v["h"])
    return v


def fold_views(done, ch, sol):
    """Per task with all folds done: list of fold views (canonical fold index order)."""
    out = {}
    for t in sorted(ch):
        n = len(ch[t]["train"])
        recs = [done.get(("fold", t, i)) for i in range(n)]
        if all(r is not None for r in recs):
            out[t] = [run_view(r, t, ch, sol) for r in recs]
    return out


def p1_heldout_inside(fv):
    """P1: fold programs verified on their n-1 demos; precision on test of those predicting the held-out demo vs those missing it."""
    tasks = [t for t, xs in fv.items() if any(x["ver"] for x in xs)]
    rows = [[x for x in fv[t] if x["ver"]] for t in tasks]

    def stats(rs):
        hit = [x["t"] for r in rs for x in r if x["h"]]
        miss = [x["t"] for r in rs for x in r if not x["h"]]
        return hit, miss

    hit, miss = stats(rows)
    allp = hit + miss

    def diff(rs):
        a, b = stats(rs)
        return (sum(a) / len(a) - sum(b) / len(b)) if a and b else None

    within = [(sum(x["t"] for x in r if x["h"]) / max(1, sum(x["h"] for x in r)), sum(x["t"] for x in r if not x["h"]) / max(1, sum(not x["h"] for x in r)))
              for r in rows if any(x["h"] for x in r) and any(not x["h"] for x in r)]
    hit_t = [sum(x["t"] for x in r if x["h"]) / sum(x["h"] for x in r) for r in rows if any(x["h"] for x in r)]
    miss_t = [sum(x["t"] for x in r if not x["h"]) / sum(not x["h"] for x in r) for r in rows if any(not x["h"] for x in r)]
    paired_rows = [p for p in within]

    def pd(ps):
        return sum(a - b for a, b in ps) / len(ps) if ps else None

    return dict(tasks=len(tasks), programs=len(allp), precision=(sum(allp) / len(allp) if allp else float("nan")),
                predict_held=dict(programs=len(hit), right=round(sum(hit), 2), precision=(sum(hit) / len(hit) if hit else float("nan"))),
                miss_held=dict(programs=len(miss), right=round(sum(miss), 2), precision=(sum(miss) / len(miss) if miss else float("nan"))),
                difference=diff(rows), difference_ci=boot_ci(rows, diff) if rows else (float("nan"), float("nan")),
                per_task=dict(tasks_with_hit=len(hit_t), mean_precision_hit=(sum(hit_t) / len(hit_t) if hit_t else float("nan")),
                              tasks_with_miss=len(miss_t), mean_precision_miss=(sum(miss_t) / len(miss_t) if miss_t else float("nan")),
                              tasks_with_both=len(paired_rows), mean_paired_difference=pd(paired_rows),
                              paired_ci=boot_ci(paired_rows, pd) if paired_rows else (float("nan"), float("nan"))))


def sign_p(a, b):
    n = a + b
    if n == 0:
        return float("nan")
    k = min(a, b)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def p2_exchangeability(fv):
    """P2: per fold h (held-out right), t (fraction of test outputs right). Exchangeability + symmetry: E[h] = E[t]."""
    tasks = list(fv)
    rows = [fv[t] for t in tasks]
    F = sum(len(r) for r in rows)
    h = sum(x["h"] for r in rows for x in r)
    t = sum(x["t"] for r in rows for x in r)
    d1 = sum(x["h"] * (1 - x["t"]) for r in rows for x in r)
    d2 = sum((not x["h"]) * x["t"] for r in rows for x in r)
    up = sum(sum(x["h"] - x["t"] for x in r) > 1e-12 for r in rows)
    down = sum(sum(x["h"] - x["t"] for x in r) < -1e-12 for r in rows)

    def md(rs):
        n = sum(len(r) for r in rs)
        return sum(x["h"] - x["t"] for r in rs for x in r) / n if n else None

    def dd(rs):
        return sum(x["h"] * (1 - x["t"]) - (not x["h"]) * x["t"] for r in rs for x in r)

    def rh(rs):
        n = sum(len(r) for r in rs)
        return sum(x["h"] for r in rs for x in r) / n if n else None

    def rt(rs):
        n = sum(len(r) for r in rs)
        return sum(x["t"] for r in rs for x in r) / n if n else None

    return dict(tasks=len(tasks), folds=F, held_right=h, test_right=round(t, 2), held_rate=h / F if F else float("nan"), test_rate=t / F if F else float("nan"),
                held_rate_ci=boot_ci(rows, rh) if rows else None, test_rate_ci=boot_ci(rows, rt) if rows else None,
                difference=(h - t) / F if F else float("nan"), difference_ci=boot_ci(rows, md) if rows else None,
                discordant_held_only=round(d1, 2), discordant_test_only=round(d2, 2), discordant_difference=round(d1 - d2, 2),
                discordant_difference_ci=boot_ci(rows, dd) if rows else None, tasks_held_more=up, tasks_test_more=down, sign_test_two_sided=sign_p(up, down))


def p3_order(tid, n):
    return sorted(range(n), key=lambda i: zlib.crc32(f"{GLOBAL_SEED}|p3|{tid}|{i}".encode()))


def pass2_ranked(runs, nt, sol_t, first=None):
    """pass@2 for one task. runs: list of (rank, tests), lower rank first, run order within a rank; first two distinct non-null grids per
    test output. `first`: grids that go ahead of everything (a certified answer)."""
    hit = 0
    order = sorted(runs, key=lambda r: r[0])                # stable: keeps run order
    for t in range(nt):
        cands = list(first[t:t + 1]) if first else []
        cands += [r[1][t] for r in order]
        top = []
        for g in cands:
            if g is not None and g not in top:
                top.append(g)
            if len(top) == 2:
                break
        hit += sol_t[t] in top
    return hit / nt


def pass2_task(runs, nt, sol_t, first=None):
    """Two tiers, as the plan's text: runs = (is_verified, tests); verified first, then the others."""
    return pass2_ranked([(0 if v else 1, g) for v, g in runs], nt, sol_t, first)


def tier3(x):
    """Sensitivity (the lead's old-data script): verified-and-held, then verified on n-1 but missing the held-out demo, then the rest."""
    if x.get("kind") == "fold":
        return 0 if x["vh"] else (1 if x["ver"] else 2)
    return 0 if x["ver"] else 2


def plain_views(tid, done, ch, sol, samples=(1, 2, 3)):
    runs = []
    r0 = done.get(("full", tid, -1))
    if r0 is not None:
        runs.append(run_view(r0, tid, ch, sol))
    for k in samples:
        r = done.get(("plain", tid, k))
        if r is not None:
            runs.append(run_view(r, tid, ch, sol))
    return runs


def p3_same_token(done, ch, sol, caps=(2, 3, 4)):
    """Plan addendum 2: same number of runs per task, plain arm vs fold arm. Only tasks with all of both arms' logged runs enter."""
    tasks = [t for t in sorted(ch) if ("full", t, -1) in done and all(("fold", t, i) in done for i in range(len(ch[t]["train"])))
             and all(("plain", t, k) in done for k in (1, 2, 3))]
    res = dict(tasks=len(tasks))
    per = {}
    for t in tasks:
        n = len(ch[t]["train"])
        nt = len(sol[t])
        pv = plain_views(t, done, ch, sol)
        fv = [run_view(done[("fold", t, i)], t, ch, sol) for i in p3_order(t, n)]
        fu = run_view(done[("full", t, -1)], t, ch, sol)
        per[t] = dict(n=n, nt=nt, plain=pv, fold=[fu] + fv)
    for c in caps:
        rows = []
        for t in tasks:
            d = per[t]
            b = min(d["n"] + 1, c)
            pr = d["plain"][:b]
            fr = d["fold"][:b]
            sp = pass2_task([(x["ver"], x["tests"]) for x in pr], d["nt"], sol[t])
            sf = pass2_task([(x.get("vh", x["ver"]), x["tests"]) for x in fr], d["nt"], sol[t])
            s3 = pass2_ranked([(tier3(x), x["tests"]) for x in fr], d["nt"], sol[t])
            rows.append(dict(task=t, plain=sp, fold=sf, fold3=s3, tp=sum(x["tokens"] for x in pr), tf=sum(x["tokens"] for x in fr), runs=b))
        res[f"cap{c}"] = dict(plain=round(sum(r["plain"] for r in rows), 2), fold=round(sum(r["fold"] for r in rows), 2),
                              fold_three_tier_sensitivity=round(sum(r["fold3"] for r in rows), 2),
                              difference_three_tier_ci=boot_ci(rows, lambda xs: sum(r["fold3"] - r["plain"] for r in xs)),
                              difference=round(sum(r["fold"] - r["plain"] for r in rows), 2),
                              difference_ci=boot_ci(rows, lambda xs: sum(r["fold"] - r["plain"] for r in xs)),
                              tasks_fold_better=sum(r["fold"] > r["plain"] for r in rows), tasks_plain_better=sum(r["plain"] > r["fold"] for r in rows),
                              tokens_plain=sum(r["tp"] for r in rows), tokens_fold=sum(r["tf"] for r in rows), mean_runs=sum(r["runs"] for r in rows) / len(rows))
    # the certificate at full budget
    rows = [task_row(t, done, ch, sol) for t in tasks]
    small = [r for r in rows if r["n_demos"] <= 3]
    res["certificate_cap4_n_le_3"] = dict(tasks=len(small), abc=rate(small, lambda r: r.get("faloo_c"), "consensus_correct", len(small)),
                                          ab=rate(small, lambda r: r.get("faloo"), "consensus_correct", len(small)))
    res["certificate_all_tasks_n_plus_1_runs"] = dict(tasks=len(rows), abc=rate(rows, lambda r: r.get("faloo_c"), "consensus_correct", len(rows)),
                                                      ab=rate(rows, lambda r: r.get("faloo"), "consensus_correct", len(rows)))
    return res


def yield_and_precision(tasks, plain_of, fold_of):
    """plain_of[t], fold_of[t]: run views. Per-run yield on tasks where sample 0 did not verify; precision over all tasks."""
    un = [t for t in tasks if not plain_of[t]["s0_ver"]]
    P = [plain_of[t]["resamples"] for t in un]
    F = [fold_of[t] for t in un]

    def tally(rs, key):
        n = sum(len(r) for r in rs)
        v = sum(x[key] for r in rs for x in r)
        k = sum(x["t"] for r in rs for x in r if x[key])
        return dict(runs=n, verified=v, verified_rate=v / n if n else float("nan"), right=round(k, 2), precision=k / v if v else float("nan"), right_per_run=k / n if n else float("nan"))

    pairs = list(zip(P, F))

    def dy(ps):
        a = [p for p, _ in ps]
        b = [f for _, f in ps]
        na, nb = sum(len(r) for r in a), sum(len(r) for r in b)
        return (sum(x["t"] for r in b for x in r if x["vh"]) / nb - sum(x["t"] for r in a for x in r if x["ver"]) / na) if na and nb else None

    y = dict(tasks=len(un), plain=tally(P, "ver"), fold=tally(F, "vh"), fold_minus_plain_right_per_run=dy(pairs), ci=boot_ci(pairs, dy) if pairs else None)
    allp = [plain_of[t]["all"] for t in tasks]
    allf = [fold_of[t] for t in tasks]
    both = list(zip(allp, allf))

    def pr(rs, key):
        v = sum(x[key] for r in rs for x in r)
        return sum(x["t"] for r in rs for x in r if x[key]) / v if v else None

    def dp(ps):
        a = pr([p for p, _ in ps], "ver")
        b = pr([f for _, f in ps], "vh")
        return b - a if a is not None and b is not None else None

    prec = dict(plain_verified=tally(allp, "ver"), fold_verified_and_held=tally(allf, "vh"),
                plain_ci=boot_ci(allp, lambda r: pr(r, "ver")) if allp else None, fold_ci=boot_ci(allf, lambda r: pr(r, "vh")) if allf else None,
                fold_minus_plain=dp(both), fold_minus_plain_ci=boot_ci(both, dp) if both else None)
    return y, prec


def replay(done, ch, sol, budgets_k=(32, 64, 96, 128, 160, 192, 224, 256, 288, 320)):
    """Descriptive replay of logged runs at fixed mean token budgets (plan addendum 2). A replay on a seen split, not a forecast."""
    tasks = [t for t in sorted(ch, key=lambda t: zlib.crc32(f"{GLOBAL_SEED}|order|{t}".encode()))
             if ("full", t, -1) in done and all(("fold", t, i) in done for i in range(len(ch[t]["train"]))) and all(("plain", t, k) in done for k in (1, 2, 3))]
    rows = {t: task_row(t, done, ch, sol) for t in tasks}

    def seq(policy, t):
        pv = plain_views(t, done, ch, sol)
        if policy in ("i", "ii"):
            return [(x["ver"], x, False) for x in pv]
        n = len(ch[t]["train"])
        fv = [run_view(done[("fold", t, i)], t, ch, sol) for i in p3_order(t, n)]
        return [(pv[0]["ver"], pv[0], False)] + [(x["vh"], x, False) for x in fv[:-1]] + [(fv[-1]["vh"], fv[-1], bool(rows[t]["faloo_c"]))] + [(x["ver"], x, False) for x in pv[1:]]

    out = {}
    for policy in ("i", "ii", "iii"):
        seqs = {t: seq(policy, t) for t in tasks}
        pos = {t: 0 for t in tasks}
        stopped = set()
        spent = 0
        budgets = [b * 1000 * len(tasks) for b in budgets_k]
        res = []

        def score():
            s = 0.0
            for t in tasks:
                used = seqs[t][:pos[t]]
                runs = [(u[0], u[1]["tests"]) for u in used]
                first = None
                if any(u[2] for u in used):
                    first = next(u[1]["tests"] for u in used if u[2])              # the certified consensus (a fold's output; (b) makes them equal)
                s += pass2_task(runs, len(sol[t]), sol[t], first) if runs else 0.0
            return s

        bi = 0
        progress = True
        while bi < len(budgets) and progress:
            progress = False
            for t in tasks:
                if t in stopped or pos[t] >= len(seqs[t]):
                    continue
                u = seqs[t][pos[t]]
                pos[t] += 1
                spent += u[1]["tokens"]
                progress = True
                if policy == "ii" and u[0]:
                    stopped.add(t)
                if policy == "iii" and u[2]:
                    stopped.add(t)
                while bi < len(budgets) and spent >= budgets[bi]:
                    res.append(dict(budget_k_per_task=budgets_k[bi], score=round(score(), 2), tokens=spent, tasks_stopped=len(stopped)))
                    bi += 1
        exhausted = bi < len(budgets)
        out[policy] = dict(table=res, logged_runs_ran_out=exhausted, final=dict(score=round(score(), 2), tokens=spent, tokens_per_task_k=round(spent / max(1, len(tasks)) / 1000, 1), tasks_stopped=len(stopped)))
    out["note"] = "Descriptive replay of logged runs on a seen split, not a forecast."
    return out


def old_plain_views(ch, sol):
    """Old stochastic plain samples at 16k (the files of faloo_qwen.PLAIN), for checking the code against the lead's old numbers."""
    res = defaultdict(list)
    for f in ("qwen38_ps_b16384.jsonl", "qwen38_ps_xhigh_b16384.jsonl"):
        for line in open(os.path.join(RESULTS, f)):
            r = json.loads(line)
            if "error" in r or r["task_id"] not in ch:
                continue
            res[r["task_id"]].append(run_view(r, r["task_id"], ch, sol))
    return res


def check_addendum_on_greedy():
    """Own code against the lead's numbers on the OLD files (research/paper/v8_notes/lead_holdback.txt)."""
    ch, sol = load_agi2()
    done, _ = read_records(GREEDY)
    fv = fold_views(done, ch, sol)
    a = p1_heldout_inside(fv)
    b = p2_exchangeability(fv)
    assert a["tasks"] == 54 and a["programs"] == 86 and a["predict_held"]["programs"] == 57 and a["miss_held"]["programs"] == 29, a
    assert round(a["precision"] * 100, 1) == 54.3 and round(a["predict_held"]["precision"] * 100, 1) == 78.1 and round(a["miss_held"]["precision"] * 100, 1) == 7.5, a
    assert abs(a["difference"] - 0.7060) < 0.0005, a      # 78.07 - 7.47 = 70.60; the lead's +70.5 is the centre of his bootstrap, same CI up to seed
    assert b["folds"] == 359 and b["held_right"] == 71 and round(b["held_rate"] * 100, 1) == 19.8 and round(b["test_rate"] * 100, 1) == 14.5, b
    assert round(b["discordant_held_only"], 1) == 23.0 and round(b["discordant_test_only"], 1) == 4.2, b
    assert b["tasks_held_more"] == 17 and b["tasks_test_more"] == 4, b
    pv = old_plain_views(ch, sol)
    tasks = sorted(t for t in ch if len(pv[t]) >= 3)
    assert len(tasks) == 114
    allr = lambda t: [run_view(done[("full", t, -1)], t, ch, sol)] + fv[t]
    s_all = sum(pass2_task([(x.get("vh", x["ver"]), x["tests"]) for x in allr(t)], len(sol[t]), sol[t]) for t in tasks)
    s_pl3 = sum(pass2_task([(x["ver"], x["tests"]) for x in pv[t][:3]], len(sol[t]), sol[t]) for t in tasks)
    un = [t for t in ch if not run_view(done[("full", t, -1)], t, ch, sol)["ver"]]
    pr = [x for t in un for x in pv[t]]
    fr = [x for t in un for x in fv[t]]
    old = dict(p1=a, p2=b, pass2_full_plus_folds=s_all, pass2_first3_plain=s_pl3,
               yield_plain=(len(pr), sum(x["ver"] for x in pr), sum(x["t"] for x in pr if x["ver"])),
               yield_fold=(len(fr), sum(x["vh"] for x in fr), sum(x["t"] for x in fr if x["vh"])))
    print("addendum check on old greedy: P1", a["programs"], round(a["precision"], 3), a["predict_held"], a["miss_held"], round(a["difference"], 3), a["difference_ci"])
    print("  P2", round(b["held_rate"], 3), round(b["test_rate"], 3), round(b["difference"], 3), b["difference_ci"], b["discordant_held_only"], b["discordant_test_only"],
          b["discordant_difference_ci"], b["tasks_held_more"], b["tasks_test_more"], round(b["sign_test_two_sided"], 4))
    print("  pass@2 full+folds", s_all, "(lead 31.0); first 3 plain", s_pl3, "(lead 31.5), of", len(tasks))
    print("  yield plain", old["yield_plain"], "(lead 354, 32, 14.5); fold", old["yield_fold"], "(lead 301, 26, 18.5)")
    s_three = sum(pass2_ranked([(tier3(x), x["tests"]) for x in allr(t)], len(sol[t]), sol[t]) for t in tasks)
    # the lead's script keeps folds in file order (finish order, which depends on the run), so reproduce that too
    file_order = defaultdict(list)
    for line in open(GREEDY):
        r = json.loads(line)
        if r.get("kind") == "fold":
            file_order[r["task_id"]].append(run_view(r, r["task_id"], ch, sol))
    s_three_file = sum(pass2_ranked([(tier3(x), x["tests"]) for x in [run_view(done[("full", t, -1)], t, ch, sol)] + file_order[t]], len(sol[t]), sol[t]) for t in tasks)
    print("  fold arm: two tiers, canonical fold order", s_all, "; three tiers, canonical", s_three, "; three tiers, file order", s_three_file, "(lead 31.0)")
    assert abs(s_all - 33.5) < 1e-9 and abs(s_three - 33.0) < 1e-9 and abs(s_three_file - 31.0) < 1e-9
    # the lead's plain 31.5 treats a last round without code as no program; faloo_analyze.py (and this file) use the last round WITH a program
    def lead_view(r, tid):
        nt = len(sol[tid])
        rounds = [x for x in r.get("rounds", []) if "n_ok" in x]
        v = [x for x in rounds if x.get("verified")]
        c = v[0] if v else (rounds[-1] if rounds else None)
        if c is None or "test_out" not in c:
            return (False, [None] * nt)
        return (bool(v), (c["test_out"] + [None] * nt)[:nt])
    lp = defaultdict(list)
    for f in ("qwen38_ps_b16384.jsonl", "qwen38_ps_xhigh_b16384.jsonl"):
        for line in open(os.path.join(RESULTS, f)):
            r = json.loads(line)
            if "error" not in r and r["task_id"] in ch:
                lp[r["task_id"]].append(lead_view(r, r["task_id"]))
    s_lead = sum(pass2_task(lp[t][:3], len(sol[t]), sol[t]) for t in tasks)
    print("  first 3 plain with the lead's no-code rule:", s_lead, "(lead 31.5)")
    assert abs(s_pl3 - 31.0) < 1e-9 and abs(s_lead - 31.5) < 1e-9
    assert old["yield_plain"][:2] == (354, 32) and abs(old["yield_plain"][2] - 14.5) < 1e-9
    assert old["yield_fold"][:2] == (301, 26) and abs(old["yield_fold"][2] - 18.5) < 1e-9
    return old


# ------------------------------------------------------------------------------------------------ checks
def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [strip(v) for v in o]
    if isinstance(o, float):
        return round(o, 10)
    return o


def check_greedy():
    """Run the analysis code on the greedy file and compare with research/arc2/faloo_qwen.json: every summary field and every row."""
    ch, sol = load_agi2()
    done, errs = read_records(GREEDY, GREEDY.replace(".jsonl", "_C.jsonl"))
    rows = [task_row(t, done, ch, sol) for t in sorted(ch)]
    old = json.load(open(OLD_JSON))
    mine = summary_old_format(rows)
    bad = []
    for k, v in mine.items():
        w = old["summary"][k]
        if isinstance(v, dict) and "fully_right" in v:
            v = {a: b for a, b in v.items() if a != "fully_right"}
        if strip(v) != strip(w):
            bad.append((k, v, w))
    orow = {r["task"]: r for r in old["tasks"]}
    nrows = 0
    for r in rows:
        w = orow[r["task"]]
        rr = {a: b for a, b in r.items() if a != "pairs"}
        if strip(rr) != strip(w):
            bad.append((r["task"], rr, w))
        nrows += 1
    va = verified_analysis(rows)
    print("greedy reproduction: summary fields", len(mine), "rows", nrows, "mismatches", len(bad))
    for b in bad[:10]:
        print("  MISMATCH", b)
    print("hypergeom (V, W, C, kept) =", (va["verified"], va["not_fully_right"], va["certified"], va["wrong_kept"]),
          "p =", round(va["hypergeom_p_kept_or_fewer"], 4), "(paper: 0.19)")
    print("AUROC =", round(va["auroc_held_rate_vs_fully_right"], 3), "exact p =", round(va["auroc_exact_one_sided_p"], 4), "(paper: 0.91, 0.002)")
    assert not bad, "analysis does not reproduce faloo_qwen.json"
    assert abs(va["hypergeom_p_kept_or_fewer"] - 3003 / 15504) < 1e-12
    print("record counts:", Counter(k[0] for k in done), "error records:", errs)
    return dict(summary_fields=len(mine), rows=nrows, mismatches=0, hypergeom=va["hypergeom_p_kept_or_fewer"],
                auroc=va["auroc_held_rate_vs_fully_right"], auroc_p=va["auroc_exact_one_sided_p"])


def selftest():
    assert abs(hypergeom_le(20, 5, 5, 0) - comb(15, 5) / comb(20, 5)) < 1e-12
    assert abs(sum(comb(5, i) * comb(15, 5 - i) for i in range(6)) / comb(20, 5) - 1) < 1e-12
    assert auroc([1, 1], [0, 0]) == 1.0 and auroc([0.5], [0.5]) == 0.5
    # exact p against brute force, with ties
    import itertools
    r, w = [1.0, 1.0, 0.5, 0.5, 2 / 3, 1 / 3], [0.0, 0.5, 1 / 3, 0.0]
    obs = auroc(r, w)
    vals = r + w
    ge = tot = 0
    for idx in itertools.combinations(range(len(vals)), len(r)):
        a = [vals[i] for i in idx]
        b = [vals[i] for i in range(len(vals)) if i not in idx]
        ge += auroc(a, b) >= obs - 1e-12
        tot += 1
    assert abs(auroc_exact_p(r, w) - ge / tot) < 1e-12, (auroc_exact_p(r, w), ge / tot)
    lo, hi = clopper_pearson(11, 18)
    assert abs(lo - 0.36) < 0.01 and abs(hi - 0.83) < 0.01, (lo, hi)      # research/monty_heldout: 11 of 18, [36, 83]
    # concept loader: 160 tasks, 480 pairs, as the plan
    ch, sol = load_concept()
    assert len(ch) == 160 and sum(len(v) for v in sol.values()) == 480
    assert all("output" not in q for t in ch.values() for q in t["test"])
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-greedy", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    if a.check_greedy:
        check_greedy()
        check_addendum_on_greedy()
        return
    selftest()
    chk = check_greedy()
    ch1, sol1 = load_agi2()
    res = dict(greedy_reproduction=chk)
    done_g, _ = read_records(GREEDY, GREEDY.replace(".jsonl", "_C.jsonl"))
    old = analyse(done_g, ch1, sol1, label="greedy 16k (reference)")
    res["greedy_reference"] = {k: v for k, v in old.items() if k != "rows"}
    done1, e1 = read_records(STAGE_FILES[1])
    s1 = analyse(done1, ch1, sol1, e1, "stage 1: ARC-AGI-2 public eval")
    res["stage1"] = s1
    v1, rst1 = verify_run(STAGE_FILES[1], done1, ch1, STAGE_FILES[1].replace(".jsonl", ""))
    s1["record_checks"] = v1
    s1["no_restart_sensitivity"] = sensitivity_no_restart(s1["rows"], rst1)
    res["greedy_vs_sampling"] = compare_greedy(s1, old)
    fv1 = fold_views(done1, ch1, sol1)
    s1["P1"] = p1_heldout_inside(fv1)
    s1["P2"] = p2_exchangeability(fv1)
    res["addendum2_check_on_old_greedy"] = check_addendum_on_greedy()
    if os.path.exists(STAGE_FILES["1b"]):
        doneb, eb = read_records(STAGE_FILES["1b"])
        vb, _ = verify_run(STAGE_FILES["1b"], doneb, ch1, STAGE_FILES["1b"].replace(".jsonl", ""), expected=lambda t: 3)
        comb_done = dict(done1)
        comb_done.update(doneb)
        s1b = dict(record_checks=vb, error_records_seen=eb, tokens=tokens(doneb), jobs_done=len(doneb), jobs_expected=360)
        s1b["P3"] = p3_same_token(comb_done, ch1, sol1)
        tasks = [t for t in sorted(ch1) if t in fv1 and ("full", t, -1) in comb_done and all(("plain", t, k) in comb_done for k in (1, 2, 3))]
        plain_of = {}
        for t in tasks:
            pv = plain_views(t, comb_done, ch1, sol1)
            plain_of[t] = dict(s0_ver=pv[0]["ver"], resamples=pv[1:], all=pv)
        y, prc = yield_and_precision(tasks, plain_of, {t: fv1[t] for t in tasks})
        s1b["yield"] = y
        s1b["precision"] = prc
        s1b["replay_descriptive"] = replay(comb_done, ch1, sol1)
        s0 = [plain_views(t, comb_done, ch1, sol1)[0] for t in tasks]
        s13 = [x for t in tasks for x in plain_views(t, comb_done, ch1, sol1)[1:]]
        ff = [x for t in tasks for x in fv1[t]]
        def rr(xs):
            return dict(runs=len(xs), verified=sum(x["ver"] for x in xs), verified_rate=sum(x["ver"] for x in xs) / len(xs), test_rate=sum(x["t"] for x in xs) / len(xs),
                        tokens_per_run=sum(x["tokens"] for x in xs) / len(xs))
        s1b["per_run_rates_descriptive"] = dict(sample0=rr(s0), samples1to3=rr(s13), folds=rr(ff))
        s1b["tasks_with_all_runs"] = len(tasks)
        res["stage1b"] = s1b
    if os.path.exists(STAGE_FILES[2]):
        ch2, sol2 = load_concept()
        done2, e2 = read_records(STAGE_FILES[2])
        s2 = analyse(done2, ch2, sol2, e2, "stage 2: ConceptARC corpus")
        res["stage2"] = s2
        v2, rst2 = verify_run(STAGE_FILES[2], done2, ch2, STAGE_FILES[2].replace(".jsonl", ""))
        s2["record_checks"] = v2
        s2["no_restart_sensitivity"] = sensitivity_no_restart(s2["rows"], rst2)
        s2["monty_comparison"] = compare_monty(s2)
        fv2 = fold_views(done2, ch2, sol2)
        s2["P1"] = p1_heldout_inside(fv2)
        s2["P2"] = p2_exchangeability(fv2)
    def clean(o):                                        # strict JSON: NaN becomes null
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, float) and math.isnan(o):
            return None
        return o
    json.dump(clean(res), open(OUT_JSON, "w"), indent=1)
    for st in ("stage1", "stage2"):
        if st not in res:
            continue
        R = res[st]
        print(f"\n=== {R['label']}: tasks complete {R['tasks_complete']}/{R['tasks_in_set']}; jobs {R['jobs_done']}/{R['expected_jobs']}; "
              f"tokens {R['tokens']['gen_tokens_total']:,}; forced rounds {R['tokens']['forced_round_fraction']:.3f}")
        for k, v in R["task_level"].items():
            print(f"  task {k:25s} {v}")
        va = dict(R["verified_analysis"])
        va.pop("verified_tasks", None)
        print("  verified analysis:", va)
        print("  by n:", json.dumps(R["by_n"]))
        for k, v in R["pair_level"]["rules"].items():
            print(f"  pair {k:8s} {v}")
        print("  pair other:", {k: v for k, v in R["pair_level"].items() if k != "rules"})
        print("  held-out:", R["fold_held_out_rate"], "A(D) right, any:", R["full_right_any_task_level"])
        print("  record checks:", R["record_checks"])
        print("  no-restart sensitivity:", R["no_restart_sensitivity"])
        print("  P1:", R["P1"])
        print("  P2:", R["P2"])
        if "monty_comparison" in R:
            print("  monty:", R["monty_comparison"])
    print("\ngreedy vs sampling:", res["greedy_vs_sampling"])
    if "stage1b" in res:
        print("\n=== stage 1b:", {k: res["stage1b"][k] for k in ("jobs_done", "jobs_expected", "tasks_with_all_runs", "tokens", "record_checks")})
        print("P3:", json.dumps(res["stage1b"]["P3"]))
        print("per-run rates:", res["stage1b"]["per_run_rates_descriptive"])
        print("yield:", res["stage1b"]["yield"])
        print("precision:", res["stage1b"]["precision"])
        print("replay:", json.dumps(res["stage1b"]["replay_descriptive"]))


if __name__ == "__main__":
    main()
