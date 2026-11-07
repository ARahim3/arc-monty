"""Judge v8c pass 1 recounts, own code. Imports nothing from the project's analysis scripts or the judge's audit;
reads raw JSONL, task JSON and (section 7) this pass's own Monty-ARC run, v8c_monty_nb.json.
    cd <root> && .venv/bin/python -I -B research/paper/v8_notes/scripts/v8c_qwen.py > research/paper/v8_notes/v8c_qwen.txt
Sections
 1. FA-LOO for Qwen as 5.1 writes it, (a)+(b)+(c) with (c) = the full run's output equals the folds' answer, against the
    rule the Qwen plans use, where (c) also needs the full run to verify. re-arc, ARC-AGI-2 stage 1, ConceptARC stage 2,
    ConceptARC one-input run.
 2. Table C7, Qwen per pair: plain (a) with and without the full run verifying.
 3. Retried folds that came to fit, post hoc add-on and planned replication (Table 6 recomputed as a check).
 4. Table 3 / C9 row for the one-input run: held-out split, between and within tasks, own bootstrap.
 5. Table 8: random orders, exact expectation and 5th-95th percentile of 100,000 orders; Section 7's unsolved tasks.
 6. Section 9: the notebook's own merge on the 16k one-sample runs, Qwen alone and with Monty-ARC.
Scoring: a run's output is its first verified round, else its last round with output (research/arc2/faloo_qwen.py);
a multi-test task scores the fraction of its test outputs right; demonstrations are indexed in canonical order."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import glob
import itertools
import json
import os
import random
from collections import Counter, defaultdict
from math import comb

import numpy as np

ROOT = _REPO
RES = ROOT + "/llm/results/"
RAW = ROOT + "/research/generator_control/raw/"


def dumps(g):
    return None if g is None else json.dumps(g, separators=(",", ":"))


def gkey(g):
    return (len(g) * len(g[0]), len(g), len(g[0]), json.dumps(g))


def load(path):
    """(kind, task, fold) -> record; the earliest-started record if a key repeats (the plans' rule)."""
    best = {}
    for line in open(path, errors="replace"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if "error" in r:
            continue
        k = (r.get("kind"), r["task_id"], r.get("fold"))
        if k not in best or r.get("started_at", 0) < best[k].get("started_at", 0):
            best[k] = r
    return best


def output(rec):
    """-> (query id -> grid, fit). Fit: some round reproduced every demonstration it was shown."""
    if rec is None:
        return {}, False
    rs = [x for x in rec.get("rounds", []) if "test_out" in x]
    if not rs:
        return {}, False
    v = [x for x in rs if x.get("verified")]
    x = v[0] if v else rs[-1]
    return dict(zip(rec["query_ids"], x["test_out"])), bool(v)


def eq(a, b):
    return a is not None and b is not None and dumps(a) == dumps(b)


def demos(task):
    return sorted(task["train"], key=lambda p: gkey(p["input"]))


def load_agi2():
    ch = json.load(open(ROOT + "/data/kaggle_format/agi2_eval_challenges.json"))
    so = json.load(open(ROOT + "/data/kaggle_format/agi2_eval_solutions.json"))
    return {t: dict(train=ch[t]["train"], test=[dict(input=x["input"], output=so[t][i]) for i, x in enumerate(ch[t]["test"])]) for t in ch}


def load_dir(pattern, base):
    T = {}
    for f in sorted(glob.glob(pattern)):
        d = json.load(open(f))
        T[os.path.relpath(f, base)[:-5]] = dict(train=d["train"], test=d["test"])
    return T


def fold_view(task, full, folds, tests=None):
    """Everything the rules need for one task. folds: i -> record. tests: test indices shown (default all)."""
    n = len(task["train"]); D = demos(task)
    tests = list(range(len(task["test"]))) if tests is None else tests
    fo, fv = output(full)
    F = [output(folds.get(i)) for i in range(n)]
    a = all(i in folds for i in range(n)) and all(eq(F[i][0].get("demo:%d" % i), D[i]["output"]) for i in range(n))
    per = []
    for t in tests:
        outs = [F[i][0].get("test:%d" % t) for i in range(n)]
        agree = n > 0 and all(o is not None for o in outs) and len({dumps(o) for o in outs}) == 1
        cons = outs[0] if agree else None
        fu = fo.get("test:%d" % t)
        truth = task["test"][t]["output"]
        per.append(dict(agree=agree, c=agree and eq(fu, cons), cons_right=eq(cons, truth), full=fu, full_right=eq(fu, truth)))
    return dict(a=a, fv=fv, per=per, F=F, D=D, n=n)


def task_level(T, S, kind_full=("full", -1)):
    """Task-level FA-LOO counts. S: loaded records with kinds full/fold."""
    rows = []
    for t, task in sorted(T.items()):
        full = S.get((kind_full[0], t, kind_full[1]))
        folds = {k[2]: r for k, r in S.items() if k[0] == "fold" and k[1] == t}
        v = fold_view(task, full, folds)
        b = all(p["agree"] for p in v["per"])
        c = all(p["c"] for p in v["per"])
        score = sum(p["cons_right"] for p in v["per"]) / len(v["per"])
        rows.append(dict(t=t, ab=v["a"] and b, lit=v["a"] and b and c, ver=v["a"] and b and c and v["fv"], fv=v["fv"], score=score,
                         full_score=sum(p["full_right"] for p in v["per"]) / len(v["per"])))
    return rows


def show_task(name, rows):
    N = len(rows)
    for lab in ("lit", "ver", "ab"):
        ans = [r for r in rows if r[lab]]
        right = round(sum(r["score"] for r in ans), 2)
        print("  %s %s: %s/%d right, coverage %.1f%% of %d" % (name, {"lit": "(a)+(b)+(c) as 5.1 writes it", "ver": "(a)+(b)+(c), full run verified",
              "ab": "(a)+(b)"}[lab], int(right) if right == int(right) else right, len(ans), 100 * len(ans) / N, N))
    extra = [r["t"] for r in rows if r["lit"] and not r["ver"]]
    print("  tasks answered only when the full run need not verify:", extra)


print("=== 1. FA-LOO as written (5.1) vs with the full run verified (the Qwen plans)")
RE = load_dir(ROOT + "/research/generator_control/data/tasks/*.json", ROOT + "/research/generator_control/data/tasks")
GM = load(RAW + "gc_qwen_main.jsonl")
print("re-arc: tasks", len(RE), "records", len(GM), Counter(k[0] for k in GM))
rows_re = task_level(RE, GM)
show_task("re-arc", rows_re)
for r in rows_re:
    if r["lit"] and not r["ver"]:
        v = fold_view(RE[r["t"]], GM[("full", r["t"], -1)], {k[2]: x for k, x in GM.items() if k[0] == "fold" and k[1] == r["t"]})
        print("   ", r["t"], "full run fit:", v["fv"], "full output right:", v["per"][0]["full_right"], "folds' answer right:", v["per"][0]["cons_right"])
A2 = load_agi2()
S1 = load(RES + "qwen38_faloo_sampling_b32768.jsonl")
rows_a2 = task_level(A2, S1)
show_task("ARC-AGI-2", rows_a2)

CA = load_dir(ROOT + "/external/judge/conceptarc/repo/corpus/*/*.json", ROOT + "/external/judge/conceptarc/repo/corpus")
S2 = load(RES + "qwen38_faloo_sampling_concept_b32768.jsonl")
C1 = load(RAW + "gc_qwen_c1.jsonl")


def pair_level(T, S, tests_of=None):
    R = []
    for t, task in sorted(T.items()):
        full = S.get(("full", t, -1))
        folds = {k[2]: r for k, r in S.items() if k[0] == "fold" and k[1] == t}
        v = fold_view(task, full, folds, tests_of(task) if tests_of else None)
        for p in v["per"]:
            R.append(dict(t=t, a=v["a"], fv=v["fv"], **p))
    return R


def frac(xs, right):
    return "%d/%d" % (sum(x[right] for x in xs), len(xs))


P2 = pair_level(CA, S2)
P1 = pair_level(CA, C1, lambda task: [0])
for name, P in (("ConceptARC (all test inputs shown)", P2), ("ConceptARC, one-input run", P1)):
    N = len(P)
    lit = [p for p in P if p["a"] and p["c"]]
    ver = [p for p in lit if p["fv"]]
    print("  %s, per pair: as written %s (%.1f%%); full run verified %s (%.1f%%); of %d pairs; tasks as written %d, verified %d" % (
        name, frac(lit, "cons_right"), 100 * len(lit) / N, frac(ver, "cons_right"), 100 * len(ver) / N, N,
        len({p["t"] for p in lit}), len({p["t"] for p in ver})))

print("\n=== 2. Table C7, Qwen, ConceptARC per pair (all test inputs shown)")
ab = [p for p in P2 if p["a"] and p["agree"]]
pa = [p for p in P2 if p["a"] and p["full"] is not None]
pav = [p for p in pa if p["fv"]]
fit = [p for p in P2 if p["fv"]]
print("  FA-LOO (a)+(b)+(c), full run verified:", frac([p for p in P2 if p["a"] and p["c"] and p["fv"]], "cons_right"))
print("  (a)+(b):", frac(ab, "cons_right"))
print("  plain (a), the full run's output wherever (a) holds:", frac(pa, "full_right"), "%.1f%%" % (100 * sum(p["full_right"] for p in pa) / len(pa)))
print("  plain (a), full run also verified:", frac(pav, "full_right"), "%.1f%%" % (100 * sum(p["full_right"] for p in pav) / len(pav)))
print("  fit (full run verified):", frac(fit, "full_right"))
print("  plain (a) answered with an unverified full run:", [(p["t"], p["full_right"]) for p in pa if not p["fv"]])

print("\n=== 3. Retry rule: folds that came to fit (task level, fraction of test outputs)")


def retry_eval(task, full, attempts):
    """attempts: i -> [first, retry1, retry2] records (missing ones omitted). Returns per-task rule results and fold infos."""
    n = len(task["train"]); D = demos(task); nt = len(task["test"])
    fo, fv = output(full)
    res = {}
    for use in (False, True):
        chosen, infos = [], []
        for i in range(n):
            att = attempts.get(i, [])
            c = att[0] if att else None
            came = False
            if use and att and not output(att[0])[1]:
                for r in att[1:]:
                    if output(r)[1]:
                        c, came = r, True
                        break
            o = output(c)[0]
            h = eq(o.get("demo:%d" % i), D[i]["output"])
            ts = sum(eq(o.get("test:%d" % t), task["test"][t]["output"]) for t in range(nt)) / nt
            chosen.append(o)
            infos.append(dict(came=came, h=h, ts=ts))
        a = all(x["h"] for x in infos)
        outs = [tuple(dumps(o.get("test:%d" % t)) for t in range(nt)) for o in chosen]
        b = n > 0 and all(x is not None for x in outs[0]) and len(set(outs)) == 1
        c = b and tuple(dumps(fo.get("test:%d" % t)) for t in range(nt)) == outs[0]
        score = sum(eq(chosen[0].get("test:%d" % t), task["test"][t]["output"]) for t in range(nt)) / nt if b else 0
        fscore = sum(eq(fo.get("test:%d" % t), task["test"][t]["output"]) for t in range(nt)) / nt
        res[use] = dict(cert=fv and a and b and c, score=score, fv=fv, fscore=fscore, infos=infos)
    return res


RT = load(RAW + "gc_qwen_retry.jsonl")
RP = load(RAW + "gc_qwen_rep.jsonl")
PL = load(RES + "qwen38_faloo_sampling_plain_b32768.jsonl")
retry_by = defaultdict(dict)
for (k, t, f), r in RT.items():
    retry_by[t][(f // 100, f % 100)] = r
rep_by = defaultdict(dict)
for (k, t, f), r in RP.items():
    rep_by[t][(f // 100, f % 100)] = r


def summarize(label, results):
    ver = [r for r in results if r["fv"]]
    cert = [r for r in results if r["cert"]]
    wrong = [r for r in ver if r["fscore"] < 1]
    kept = [r for r in cert if r["score"] < 1]
    Nv, W, m, k = len(ver), len(wrong), len(cert), len(kept)
    p = sum(comb(W, j) * comb(Nv - W, m - j) for j in range(k + 1)) / comb(Nv, m) if m else float("nan")
    print("  %s: FA-LOO %s/%d, coverage %.1f%%, verified %d, verified-but-wrong %d, kept %d, p = %.4f" % (
        label, round(sum(r["score"] for r in cert), 2), m, 100 * m / 120, Nv, W, k, p))


def came_stats(label, results):
    xs = [x for r in results if r["fv"] for x in r["infos"] if x["came"]]
    pr = [x for x in xs if x["h"]]; ms = [x for x in xs if not x["h"]]
    print("  %s: retried folds that came to fit %d; predict held-out %d, right on test %.2f; miss %d, right on test %.2f" % (
        label, len(xs), len(pr), sum(x["ts"] for x in pr), len(ms), sum(x["ts"] for x in ms)))
    print("     two-test tasks among them:", sum(1 for r in results if r["fv"] for x in r["infos"] if x["came"] and x["ts"] not in (0, 1)),
          "folds with a fractional test score")


first_res, rep_res = [], []
for t, task in sorted(A2.items()):
    n = len(task["train"])
    att = {i: [S1.get(("fold", t, i))] + [retry_by[t][(i, a)] for a in (1, 2) if (i, a) in retry_by[t]] for i in range(n)}
    att = {i: [x for x in v if x is not None] for i, v in att.items()}
    first_res.append(retry_eval(task, S1.get(("full", t, -1)), att))
    full_rep = PL.get(("plain", t, 1))
    if output(full_rep)[1]:
        att = {i: [rep_by[t][(i, a)] for a in (0, 1, 2) if (i, a) in rep_by[t]] for i in range(n)}
        rep_res.append(retry_eval(task, full_rep, att))
    else:
        rep_res.append({u: dict(cert=False, score=0, fv=False, fscore=0, infos=[]) for u in (False, True)})
summarize("first runs", [r[False] for r in first_res])
summarize("first runs + retries (post hoc)", [r[True] for r in first_res])
summarize("replication, no retries", [r[False] for r in rep_res])
summarize("replication + retries (planned)", [r[True] for r in rep_res])
came_stats("post hoc add-on", [r[True] for r in first_res])
came_stats("planned replication", [r[True] for r in rep_res])

print("\n=== 4. Held-out split, one-input run (Table 3 / C9 row): verified fold programs, right on test input 1")
pred, miss, within = [], [], []
for t, task in sorted(CA.items()):
    n = len(task["train"]); D = demos(task)
    pt, mt = [], []
    for i in range(n):
        o, fitf = output(C1.get(("fold", t, i)))
        if not fitf:
            continue
        right = eq(o.get("test:0"), task["test"][0]["output"])
        (pt if eq(o.get("demo:%d" % i), D[i]["output"]) else mt).append(right)
    pred += pt; miss += mt
    if pt and mt:
        within.append(sum(pt) / len(pt) - sum(mt) / len(mt))
print("  predict %d/%d = %.1f%%; miss %d/%d = %.1f%%; between %+.1f" % (sum(pred), len(pred), 100 * sum(pred) / len(pred), sum(miss), len(miss),
      100 * sum(miss) / len(miss), 100 * (sum(pred) / len(pred) - sum(miss) / len(miss))))
rng = random.Random(0)
bw = []
by_task = defaultdict(lambda: ([], []))
for t, task in sorted(CA.items()):
    D = demos(task)
    for i in range(len(task["train"])):
        o, fitf = output(C1.get(("fold", t, i)))
        if fitf:
            by_task[t][0 if eq(o.get("demo:%d" % i), D[i]["output"]) else 1].append(eq(o.get("test:0"), task["test"][0]["output"]))
keys = sorted(by_task)
for _ in range(10000):
    s = [by_task[keys[rng.randrange(len(keys))]] for _ in keys]
    p_ = [x for a, _ in s for x in a]; m_ = [x for _, b in s for x in b]
    bw.append(100 * (sum(p_) / len(p_) - sum(m_) / len(m_)))
bw.sort()
ww = []
for _ in range(10000):
    s = [within[rng.randrange(len(within))] for _ in within]
    ww.append(100 * sum(s) / len(s))
ww.sort()
print("  between interval [%.1f, %.1f]; within %+.1f over %d tasks [%.1f, %.1f] (own bootstrap, seed 0)" % (
    bw[250], bw[9749], 100 * sum(within) / len(within), len(within), ww[250], ww[9749]))

print("\n=== 5. Table 8: candidate order at k samples per task, ARC-AGI-2, 32k logged runs")


def runs_of(t, k):
    recs = [S1.get(("full", t, -1))] + [PL[x] for x in sorted((x for x in PL if x[1] == t), key=lambda x: x[2])]
    return [output(r) for r in recs[:k] if r is not None]


def top2(L):
    s = []
    for x in L:
        if x not in s:
            s.append(x)
        if len(s) == 2:
            break
    return s


def p_random(L, tr):
    """Exact chance that the truth is among the first two distinct grids of a uniformly shuffled candidate list."""
    if not L:
        return 0.0
    perms = list(itertools.permutations(range(len(L))))
    return sum(tr in top2([L[i] for i in p]) for p in perms) / len(perms)


rng_np = np.random.default_rng(20261103)
for k in (1, 2, 3, 4):
    tot = Counter(); ps, ws = [], []; crowded = 0
    for t, task in sorted(A2.items()):
        R = runs_of(t, k); nt = len(task["test"])
        for j in range(nt):
            tr = dumps(task["test"][j]["output"])
            V = [dumps(o.get("test:%d" % j)) for o, f in R if f and o.get("test:%d" % j) is not None]
            U = [dumps(o.get("test:%d" % j)) for o, f in R if not f and o.get("test:%d" % j) is not None]
            crowded += len(set(V + U)) > 2
            tot["verified first"] += (tr in top2(V + U)) / nt
            tot["unverified first"] += (tr in top2(U + V)) / nt
            tot["perfect"] += (tr in V + U) / nt
            ps.append(p_random(V + U, tr)); ws.append(1 / nt)
    ps, ws = np.array(ps), np.array(ws)
    draws = (rng_np.random((100000, len(ps))) < ps) @ ws
    print("  k=%d %s; random: exact mean %.2f, 5th-95th percentile of 100,000 orders %.2f-%.2f (median %.2f); crowded %d of %d" % (
        k, {a: round(b, 2) for a, b in tot.items()}, float(ps @ ws), np.percentile(draws, 5), np.percentile(draws, 95), np.median(draws), crowded, len(ps)))
    print("     Table 8 random cell, mean (5th, 95th percentile): %.1f (%.1f, %.1f)" % (float(ps @ ws), np.percentile(draws, 5), np.percentile(draws, 95)))

single = [t for t, task in A2.items() if len(task["test"]) == 1]
R4 = {t: runs_of(t, 4) for t in single}
s4 = [t for t in single if len(R4[t]) == 4]
right = {t: [eq(o.get("test:0"), A2[t]["test"][0]["output"]) for o, f in R4[t]] for t in s4}
vf = {}
for t in s4:
    tr = dumps(A2[t]["test"][0]["output"])
    V = [dumps(o.get("test:0")) for o, f in R4[t] if f and o.get("test:0") is not None]
    U = [dumps(o.get("test:0")) for o, f in R4[t] if not f and o.get("test:0") is not None]
    vf[t] = tr in top2(V + U)
never = [t for t in s4 if not any(right[t])]
unsolved = [t for t in s4 if not vf[t]]
pbar = sum(sum(v) for v in right.values()) / (4 * len(s4))
print("  single-test tasks %d, with four samples %d: solved by no sample %d, by all four %d; unsolved by verified-first %d, of which never solved %d" % (
    len(single), len(s4), len(never), sum(all(v) for v in right.values()), len(unsolved), len([t for t in unsolved if t in never])))
print("  one common rate %.3f: expected none %.1f, all four %.2f" % (pbar, len(s4) * (1 - pbar) ** 4, len(s4) * pbar ** 4))

print("\n=== 6. Section 9: the notebook's merge (cell 13, no NVARC) on the 16k one-sample runs")
MON = json.load(open(ROOT + "/research/paper/v8_notes/v8c_monty_nb.json"))
EMPTY = [[0]]


def samples(fn):
    by = defaultdict(dict)
    for line in open(RES + fn):
        r = json.loads(line)
        by[r["task_id"]][r["sample"]] = r
    return by


def qwen_summary(rec, nt):
    """The notebook's summarize(): rank each test output's grids by (verified rounds, best n_ok); attempt, alt."""
    progs = [x for x in (rec or {}).get("rounds", []) if "test_out" in x]
    outs = []
    for j in range(nt):
        score, grids = {}, {}
        for p in progs:
            g = p["test_out"][j] if j < len(p["test_out"]) else None
            if g is None:
                continue
            k = json.dumps(g)
            grids[k] = g
            s = score.get(k, (0, -1))
            score[k] = (s[0] + bool(p.get("verified")), max(s[1], p.get("n_ok", -1)))
        ranked = [grids[k] for k in sorted(score, key=lambda k: score[k], reverse=True)]
        outs.append({"attempt": ranked[0] if ranked else None, "alt": ranked[1] if len(ranked) > 1 else None})
    return {"verified": any(p.get("verified") for p in progs), "outputs": outs}


def merge(q, m, ti, use_monty):
    cands = []
    qo = q["outputs"][ti]
    if q["verified"] and qo.get("attempt"):
        cands.append(qo["attempt"])
    ms = (m.get("confident") or [])[ti] if use_monty and ti < len(m.get("confident") or []) else []
    if ms:
        cands.append(ms[0])
    extra = []
    if qo.get("attempt") and not q["verified"]:
        extra.append(qo["attempt"])
    if q["verified"] and qo.get("alt"):
        extra.append(qo["alt"])
    if use_monty:
        extra += (m.get("guesses") or [])[ti] if ti < len(m.get("guesses") or []) else []
    final = []
    for g in cands + extra:
        if g and g != EMPTY and g not in final:
            final.append(g)
        if len(final) == 2:
            break
    return final


for label, fn in (("run 1 (qwen38_ps_b16384, sample 0)", "qwen38_ps_b16384.jsonl"), ("run 2 (qwen38_ps_xhigh_b16384, sample 0)", "qwen38_ps_xhigh_b16384.jsonl")):
    by = samples(fn)
    sc = Counter(); conf_used = 0
    for t, task in sorted(A2.items()):
        nt = len(task["test"])
        q = qwen_summary(by[t].get(0), nt)
        m = MON.get(t, {})
        for ti in range(nt):
            tr = task["test"][ti]["output"]
            sc["Qwen alone"] += (tr in merge(q, m, ti, False)) / nt
            sc["with Monty-ARC"] += (tr in merge(q, m, ti, True)) / nt
            conf_used += bool((m.get("confident") or [[]] * nt)[ti]) if ti < len(m.get("confident") or []) else 0
    print("  %s: %s; Monty-ARC confident on %d test outputs" % (label, {a: round(b, 2) for a, b in sc.items()}, conf_used))
old = ROOT + "/research/paper/judge_v8b/audit/out/monty_agi2_eval_notebook.json"
if os.path.exists(old):
    O = json.load(open(old))
    same = sum(1 for t in A2 if dumps(O.get(t, {}).get("confident")) == dumps(MON.get(t, {}).get("confident")) and dumps(O.get(t, {}).get("guesses")) == dumps(MON.get(t, {}).get("guesses")))
    print("  this run's Monty-ARC outputs equal the earlier notebook-mode cache on %d of %d tasks" % (same, len(A2)))
