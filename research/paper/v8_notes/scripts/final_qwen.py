"""Final pass recount, own code: Qwen on re-arc, the retry rule and its replication, ranking at k samples, failing folds, plan timing.
Reads raw JSONL and task JSON only; imports nothing from the project."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, os, glob, random, math, sys
from collections import defaultdict, Counter
from math import comb
ROOT = _REPO
RES = ROOT + "/llm/results/"
GC = ROOT + "/research/generator_control/raw/"

def dumps(g): return None if g is None else json.dumps(g, separators=(",", ":"))
def gkey(g): return (len(g) * len(g[0]), len(g), len(g[0]), json.dumps(g))

def read(path):
    """Earliest-started good record per (kind,task,fold)."""
    best = {}
    n = err = 0
    for line in open(path, errors="replace"):
        try: r = json.loads(line)
        except Exception: continue
        n += 1
        if "error" in r: err += 1; continue
        k = (r["kind"], r["task_id"], r["fold"])
        if k not in best or r.get("started_at", 0) < best[k].get("started_at", 0): best[k] = r
    return best, n, err

def out(rec):
    """-> dict query id -> grid (grids may be None), verified flag, has-a-program flag."""
    rounds = [x for x in rec.get("rounds", []) if "test_out" in x]
    if not rounds: return None, False
    v = [x for x in rounds if x.get("verified")]
    x = v[0] if v else rounds[-1]
    return dict(zip(rec["query_ids"], x["test_out"])), bool(v)

def load_agi2():
    ch = json.load(open(ROOT + "/data/kaggle_format/agi2_eval_challenges.json"))
    so = json.load(open(ROOT + "/data/kaggle_format/agi2_eval_solutions.json"))
    return {t: dict(train=ch[t]["train"], test=[dict(input=x["input"], output=so[t][i]) for i, x in enumerate(ch[t]["test"])]) for t in ch}

def load_concept():
    base = ROOT + "/external/judge/conceptarc/repo/corpus"
    T = {}
    for f in sorted(glob.glob(base + "/*/*.json")):
        d = json.load(open(f)); T[os.path.relpath(f, base)[:-5]] = dict(train=d["train"], test=d["test"])
    return T

def load_rearc():
    T = {}
    for f in sorted(glob.glob(ROOT + "/research/generator_control/data/tasks/*.json")):
        d = json.load(open(f)); T[os.path.basename(f)[:-5]] = dict(train=d["train"], test=d["test"])
    return T

def sorted_demos(task): return sorted(task["train"], key=lambda p: gkey(p["input"]))

def score_task(task, full, folds):
    """Task level, all test outputs must agree. -> dict"""
    demos = sorted_demos(task); n = len(demos); nt = len(task["test"])
    truth = [p["output"] for p in task["test"]]
    fo, fv = out(full) if full else (None, False)
    fg = [fo.get("test:%d" % k) if fo else None for k in range(nt)]
    rate = lambda g: sum(dumps(g[k]) == dumps(truth[k]) and g[k] is not None for k in range(nt)) / nt
    row = dict(n=n, nt=nt, verified=fv, full=rate(fg), a=False, b=False, c=False, cons=None)
    held = []; tests = []
    for i in range(n):
        d, v = out(folds[i]) if folds.get(i) else (None, False)
        held.append(bool(d) and dumps(d.get("demo:%d" % i)) == dumps(demos[i]["output"]) and d.get("demo:%d" % i) is not None)
        tests.append(None if not d else tuple(dumps(d.get("test:%d" % k)) for k in range(nt)))
    a = all(held)
    b = all(x is not None for x in tests) and len(set(tests)) == 1 and None not in tests[0]
    row["a"] = a; row["b"] = b
    if b:
        row["cons"] = sum(tests[0][k] == dumps(truth[k]) for k in range(nt)) / nt
        row["c"] = tuple(dumps(g) for g in fg) == tests[0]
    return row

def hyper_le(N, K, n, k):
    """P(X <= k), X hypergeometric: drawing n of N with K wrong."""
    return sum(comb(K, i) * comb(N - K, n - i) for i in range(0, k + 1) if n - i >= 0) / comb(N, n)

def boot(items, stat, B=10000, seed=0):
    r = random.Random(seed); m = len(items); v = []
    for _ in range(B):
        s = [items[r.randrange(m)] for _ in range(m)]
        x = stat(s)
        if x is not None: v.append(x)
    v.sort()
    return v[int(.025 * len(v))], v[min(len(v) - 1, int(.975 * len(v)))]

print("=== 1. re-arc, Qwen, real role")
TR = load_rearc()
M, n, e = read(GC + "gc_qwen_main.jsonl")
print("tasks", len(TR), "records", n, "errors", e)
rows = {}
FH = {}
for t, task in TR.items():
    rows[t] = score_task(task, M[("full", t, -1)], {i: M.get(("fold", t, i)) for i in range(3)})
    demos = sorted_demos(task); tr = task["test"][0]["output"]
    FH[t] = []
    for i in range(3):
        d, v = out(M[("fold", t, i)])
        h = int(bool(d) and d.get("demo:%d" % i) is not None and dumps(d["demo:%d" % i]) == dumps(demos[i]["output"]))
        g = d.get("test:0") if d else None
        tt = int(g is not None and dumps(g) == dumps(tr))
        FH[t].append(dict(h=h, t=tt, v=v, has=g is not None))
R = list(rows.values())
ver = [r for r in R if r["verified"]]
print("top (has answer)", sum(r["full"] == 1 for r in R), "fit", sum(r["full"] == 1 for r in ver), len(ver))
ab = [r for r in R if r["a"] and r["b"]]
abc = [r for r in ab if r["c"] and r["verified"]]
print("(a)", sum(1 for r in R if r["a"]), "(a)+(b)", sum(r["cons"] == 1 for r in ab), len(ab), "(a)+(b)+(c)", sum(r["cons"] == 1 for r in abc), len(abc))
L = [int(r["a"] and r["b"] and r["c"] and r["verified"]) for r in R]
print("coverage", 100 * sum(L) / 200, "CI", [100 * x for x in boot(L, lambda s: sum(s) / len(s))], "floor", 100 * (1 - .25 / (sum(L) / 200)))
lo, hi = boot(L, lambda s: sum(s) / len(s))
print("floor interval", 100 * (1 - .25 / lo), 100 * (1 - .25 / hi))
print("joint wrong", sum(1 for r in abc if r["cons"] != 1), "of 200; CP upper", 100 * (1 - .025 ** (1 / 200)))
FL = list(FH.values())
hbar = sum(f["h"] for x in FL for f in x) / 600; tbar = sum(f["t"] for x in FL for f in x) / 600
ht = lambda s: 100 * sum(f["h"] - f["t"] for x in s for f in x) / sum(len(x) for x in s)
print("h", 100 * hbar, "t", 100 * tbar, "h-t", ht(FL), "CI", boot(FL, ht))
print("discordant h only / t only", sum(f["h"] and not f["t"] for x in FL for f in x), sum(f["t"] and not f["h"] for x in FL for f in x))
# Stops
vw = [r for r in ver if r["full"] < 1]
print("verified wrong", len(vw), "stopped by (a)", sum(not r["a"] for r in vw), "(b)", sum(r["a"] and not r["b"] for r in vw), "(c)", sum(r["a"] and r["b"] and not r["c"] for r in vw))
print("P(random 107 of 171 avoids all 12)", hyper_le(len(ver), len(vw), len(abc), 0))
print("rejected right", sum(1 for r in ver if r["full"] == 1 and not (r["a"] and r["b"] and r["c"])), "of", sum(r["full"] == 1 for r in ver))
# Split as P1: fold programs verified on what they saw, with a test answer
def split(FL, cond):
    P = [f for x in FL for f in x if cond(f) and f["h"]]; Q = [f for x in FL for f in x if cond(f) and not f["h"]]
    return sum(f["t"] for f in P), len(P), sum(f["t"] for f in Q), len(Q)
def diffsplit(s, cond):
    a, b, c, d = split(s, cond)
    return None if b == 0 or d == 0 else 100 * (a / b - c / d)
def within(s, cond):
    v = []
    for x in s:
        P = [f["t"] for f in x if cond(f) and f["h"]]; Q = [f["t"] for f in x if cond(f) and not f["h"]]
        if P and Q: v.append(100 * (sum(P) / len(P) - sum(Q) / len(Q)))
    return (sum(v) / len(v), len(v)) if v else (None, 0)
for name, cond in (("verified on what they saw", lambda f: f["v"] and f["has"]), ("with a test answer", lambda f: f["has"])):
    a, b, c, d = split(FL, cond)
    print(name, a, b, c, d, "diff", 100 * (a / b - c / d), boot(FL, lambda s: diffsplit(s, cond)), "within", within(FL, cond), boot(FL, lambda s: within(s, cond)[0]))

print("=== 2. re-arc, Qwen, rotation")
ROT, n, e = read(GC + "gc_qwen_rot.jsonl")
print("rot records", n, "err", e)
PAIRS = [(0, 1), (0, 2), (1, 2)]
def exact_p(D):
    """Exact two-sided role test: D[t][r], real role index 3. Convolution over tasks with uniform role."""
    dist = {0: 1.0}
    for row in D:
        nd = defaultdict(float)
        for s_, p in dist.items():
            for d in row: nd[s_ + d] += p / len(row)
        dist = nd
    obs = sum(row[3] for row in D)
    return obs, sum(p for s_, p in dist.items() if abs(s_) >= abs(obs) - 1e-9)
D = []; ans = wr = 0; per_role_ans = Counter(); per_role_wr = Counter(); ev_tasks = Counter(); real_ev = 0; notev = 0; ident = 0; cov_per = []
for t, task in TR.items():
    demos = sorted_demos(task); P = demos + [task["test"][0]]; y = [dumps(p["output"]) for p in P]
    M_ = {}
    for i in range(3):
        d, _ = out(M[("fold", t, i)])
        M_[frozenset((i, 3))] = {i: dumps(d.get("demo:%d" % i)) if d else None, 3: dumps(d.get("test:0")) if d else None}
    for k, (i, j) in enumerate(PAIRS):
        d, _ = out(ROT[("rot", t, k)])
        M_[frozenset((i, j))] = {i: dumps(d.get("demo:%d" % i)) if d else None, j: dumps(d.get("demo:%d" % j)) if d else None}
    row = []; evs = 0; tans = 0
    for r in range(4):
        others = [i for i in range(4) if i != r]
        h = [int(M_[frozenset((i, r))][i] == y[i]) for i in others]
        tt = [int(M_[frozenset((i, r))][r] == y[r]) for i in others]
        row.append(sum(h) - sum(tt))
        a = all(h)
        g = [M_[frozenset((i, r))][r] for i in others]
        b = all(x is not None for x in g) and len(set(g)) == 1
        ev = all(h) and not any(tt)
        evs += ev
        if r == 3: real_ev += ev
        if a and b:
            ans += 1; per_role_ans[r] += 1; tans += 1
            if g[0] != y[r]:
                wr += 1; per_role_wr[r] += 1
                if not ev: notev += 1
    if sum(row) != 0: ident += 1
    D.append(row); ev_tasks[min(evs, 2)] += 1; cov_per.append(tans / 4)
obs, p = exact_p(D)
print("identity broken", ident, "tasks with 0/1/2+ events", dict(ev_tasks), "on real role", real_ev, "expected", sum(ev_tasks[k] * k for k in (1,)) / 4)
print("mean h-t real role", 100 * obs / 600, "exact two-sided p", p)
print("role-avg (a)+(b)", ans - wr, ans, "precision", 100 * (ans - wr) / ans, "wrong not event", notev, "per role ans", dict(per_role_ans), "per role wrong", dict(per_role_wr))
c = sum(cov_per) / 200; lo, hi = boot(cov_per, lambda s: sum(s) / len(s))
print("role-avg coverage", 100 * c, 100 * lo, 100 * hi, "floor", 100 * (1 - .25 / c), "role-avg joint", 100 * wr / 800)

print("=== 3. retry rule, first run (post hoc), ARC-AGI-2 eval")
A2 = load_agi2()
S1, n, e = read(RES + "qwen38_faloo_sampling_b32768.jsonl")
RET, n2, e2 = read(GC + "gc_qwen_retry.jsonl")
print("stage 1 records", n, "err", e, "retry records", n2, "err", e2, "distinct", len(RET))
def tally(rows):
    ver = [r for r in rows if r["verified"]]
    wrong = [r for r in ver if r["full"] < 1]
    abc = [r for r in ver if r["a"] and r["b"] and r["c"]]
    kept = [r for r in abc if r["full"] < 1 or r["cons"] < 1]
    return dict(verified=len(ver), verified_right=sum(r["full"] for r in ver), wrong=len(wrong), abc=len(abc), abc_right=sum(r["cons"] for r in abc), wrong_kept=len(kept),
                p=hyper_le(len(ver), len(wrong), len(abc), len(kept)), ab=sum(1 for r in ver if r["a"] and r["b"]), ab_right=sum(r["cons"] for r in ver if r["a"] and r["b"]))
base = {t: score_task(A2[t], S1[("full", t, -1)], {i: S1.get(("fold", t, i)) for i in range(len(A2[t]["train"]))}) for t in A2}
print("stage 1", tally(base.values()), "ab all tasks", sum(1 for r in base.values() if r["a"] and r["b"]), sum(r["cons"] == 1 for r in base.values() if r["a"] and r["b"]))
retried = {}; st = Counter(); toks = 0
for t in A2:
    folds = {}
    fv = out(S1[("full", t, -1)])[1]
    for i in range(len(A2[t]["train"])):
        rec = S1[("fold", t, i)]
        chosen = rec
        if fv and not out(rec)[1]:
            st["not fitting"] += 1
            for att in (1, 2):
                r = RET.get(("retry", t, i * 100 + att))
                if r is None: continue
                st["run"] += 1; toks += r.get("gen_tokens", 0)
                if out(r)[1]:
                    st["fit%d" % att] += 1; chosen = r; break
        folds[i] = chosen
    retried[t] = score_task(A2[t], S1[("full", t, -1)], folds)
print("retry", tally(retried.values()), dict(st), "tokens", toks, "ab all", sum(1 for r in retried.values() if r["a"] and r["b"]), sum(r["cons"] == 1 for r in retried.values() if r["a"] and r["b"]))
print("coverage of 120", 100 * tally(retried.values())["abc"] / 120, 100 * tally(base.values())["abc"] / 120)
print("retry answer tasks", sorted(t for t, r in retried.items() if r["verified"] and r["a"] and r["b"] and r["c"]))

print("=== 4. replication (planned)")
PL, n, e = read(RES + "qwen38_faloo_sampling_plain_b32768.jsonl")
REP, n3, e3 = read(GC + "gc_qwen_rep.jsonl")
print("plain", n, e, "rep", n3, e3)
tasks = [t for t in A2 if out(PL[("plain", t, 1)])[1]]
print("verified plain 1 tasks", len(tasks))
rw = {}; r0 = {}; st = Counter(); toks = 0
for t in tasks:
    fw = {}; f0 = {}
    for i in range(len(A2[t]["train"])):
        first = REP[("rep", t, i * 100)]
        st["first"] += 1; st["runs"] += 1; toks += first.get("gen_tokens", 0)
        f0[i] = first; ch_ = first
        if out(first)[1]:
            st["first_fit"] += 1
        else:
            for att in (1, 2):
                r = REP.get(("rep", t, i * 100 + att))
                if r is None: continue
                st["runs"] += 1; toks += r.get("gen_tokens", 0)
                if out(r)[1]:
                    st["fit%d" % att] += 1; ch_ = r; break
        fw[i] = ch_
    full = PL[("plain", t, 1)]
    rw[t] = score_task(A2[t], full, fw); r0[t] = score_task(A2[t], full, f0)
print("rep with retries", tally(rw.values()), "coverage", 100 * tally(rw.values())["abc"] / 120, dict(st), "tokens", toks)
print("rep no retries", tally(r0.values()), "coverage", 100 * tally(r0.values())["abc"] / 120)
a = {t for t, r in retried.items() if r["verified"] and r["a"] and r["b"] and r["c"]}; b = {t for t, r in rw.items() if r["a"] and r["b"] and r["c"]}
print("overlap of first run's 15 and rep's 16:", len(a & b), "verified on both", len(set(tasks) & {t for t in A2 if out(S1[('full', t, -1)])[1]}))

print("=== 5. failing folds on right verified tasks that FA-LOO rejects")
CO = load_concept()
S2, n, e = read(RES + "qwen38_faloo_sampling_concept_b32768.jsonl")
for name, T, S in (("ARC-AGI-2", A2, S1), ("ConceptARC", CO, S2)):
    cause = Counter(); fc = Counter(); right = rej = 0
    for t, task in T.items():
        r = score_task(task, S[("full", t, -1)], {i: S.get(("fold", t, i)) for i in range(len(task["train"]))})
        if not (r["verified"] and r["full"] == 1): continue
        right += 1
        if r["a"] and r["b"] and r["c"]: continue
        rej += 1
        cause["(a)" if not r["a"] else "(b)" if not r["b"] else "(c)"] += 1
        demos = sorted_demos(task)
        for i in range(len(demos)):
            rec = S[("fold", t, i)]
            d, v = out(rec)
            h = bool(d) and d.get("demo:%d" % i) is not None and dumps(d["demo:%d" % i]) == dumps(demos[i]["output"])
            if not h:
                fc["no program" if d is None else "no fit n-1" if not v else "fit, missed held-out"] += 1
    print(name, "right", right, "rejected", rej, dict(cause), "failing folds", dict(fc))

print("=== 6. ranking at k samples per task, ARC-AGI-2, 32k logged runs")
def runs_of(t, k):
    q = A2[t]; nt = len(q["test"])
    R = []
    recs = [S1[("full", t, -1)]] + [PL[key] for key in sorted((x for x in PL if x[1] == t), key=lambda x: x[2])]
    for rec in recs[:k]:
        d, v = out(rec)
        R.append(dict(g=[dumps(d.get("test:%d" % j)) if d and d.get("test:%d" % j) is not None else None for j in range(nt)], v=v))
    return R
def top2(L):
    s = []
    for x in L:
        if x not in s: s.append(x)
        if len(s) == 2: break
    return s
def evalk(k, seed=0):
    rng = random.Random(seed); res = Counter(); per = defaultdict(dict); crowded = tot = 0
    for t in sorted(A2):
        q = A2[t]; nt = len(q["test"]); R = runs_of(t, k)
        sc = Counter()
        for j in range(nt):
            tr = dumps(q["test"][j]["output"]); tot += 1
            V = [r["g"][j] for r in R if r["v"] and r["g"][j] is not None]
            U = [r["g"][j] for r in R if not r["v"] and r["g"][j] is not None]
            all_ = V + U
            crowded += len(set(all_)) > 2
            sc["ver"] += tr in top2(V + U)
            sc["unv"] += tr in top2(U + V)
            sh = all_[:]; rng.shuffle(sh); sc["rnd"] += tr in top2(sh)
            sc["oracle"] += tr in all_
        for a_, v in sc.items():
            res[a_] += v / nt; per[a_][t] = v / nt
    return res, per, crowded, tot
for k in (1, 2, 3, 4):
    res, per, cr, tot = evalk(k)
    rnd = [evalk(k, s)[0]["rnd"] for s in range(100, 140)]
    print("k", k, {a_: round(b_, 2) for a_, b_ in res.items()}, "random mean", round(sum(rnd) / 40, 2), "min", round(min(rnd), 1), "max", round(max(rnd), 1), "crowded", cr, "of", tot)
    if k == 4:
        p_ = [(per["ver"][t], per["unv"][t]) for t in sorted(A2)]
        print(" verified - unverified", sum(a_ - b_ for a_, b_ in p_), boot(p_, lambda s: sum(a_ - b_ for a_, b_ in s)))
        p_ = [(per["oracle"][t], per["ver"][t]) for t in sorted(A2)]
        print(" oracle - verified", sum(a_ - b_ for a_, b_ in p_), boot(p_, lambda s: sum(a_ - b_ for a_, b_ in s)))
# distribution of k=4 on single-test tasks
single = [t for t in A2 if len(A2[t]["test"]) == 1]
rights = {t: [r["g"][0] == dumps(A2[t]["test"][0]["output"]) for r in runs_of(t, 4)] for t in single}
print("single-test tasks", len(single), "with 4 samples", sum(len(v) == 4 for v in rights.values()), "by # right", dict(Counter(sum(v) for v in rights.values())))
ps = [sum(v) / 4 for v in rights.values()]
pbar = sum(ps) / len(ps)
print("mean rate", pbar, "expected none if independent at the same rate", len(ps) * (1 - pbar) ** 4, "all four", len(ps) * pbar ** 4)
# Reach curve: greedy 1..4 samples
print("=== 7. plan timing")
S1raw = [json.loads(l) for l in open(RES + "qwen38_faloo_sampling_b32768.jsonl")]
import datetime as dt
start = min(r["started_at"] for r in S1raw)
add2 = dt.datetime(2026, 10, 31, 23, 6, tzinfo=dt.timezone.utc).timestamp()
print("first start", dt.datetime.fromtimestamp(start, dt.timezone.utc), "jobs", len(S1raw), "finished by addendum 2", sum(r["finished_at"] <= add2 for r in S1raw), "minutes", (add2 - start) / 60)
print("resumed from checkpoint", sum(r.get("resumed_from_round", 0) > 0 for r in S1raw), "started more than once: see .ckpt/.claims")

print("=== 8. re-arc minus other sets, held-out minus test (independent bootstraps)")
def fold_ht(T, S):
    out_ = {}
    for t, task in T.items():
        demos = sorted_demos(task); nt = len(task["test"]); L = []
        for i in range(len(demos)):
            rec = S.get(("fold", t, i))
            d, v = out(rec) if rec else (None, False)
            h = int(bool(d) and d.get("demo:%d" % i) is not None and dumps(d["demo:%d" % i]) == dumps(demos[i]["output"]))
            tr = sum(int(bool(d) and d.get("test:%d" % k) is not None and dumps(d["test:%d" % k]) == dumps(task["test"][k]["output"])) for k in range(nt)) / nt
            L.append(h - tr)
        out_[t] = L
    return list(out_.values())
ffht = lambda s: 100 * sum(x for L in s for x in L) / sum(len(L) for L in s)
Fre = fold_ht(TR, M); Fa2 = fold_ht(A2, S1); Fco = fold_ht(CO, S2)
print("h-t re-arc", ffht(Fre), "AGI2", ffht(Fa2), boot(Fa2, ffht), "Concept", ffht(Fco), boot(Fco, ffht))
def diffboot(X, Y, B=10000, seed=0):
    rng = random.Random(seed); v = []
    for _ in range(B):
        a_ = [X[rng.randrange(len(X))] for _ in X]; b_ = [Y[rng.randrange(len(Y))] for _ in Y]
        v.append(ffht(a_) - ffht(b_))
    v.sort(); return v[int(.025 * B)], v[int(.975 * B)]
print("re-arc minus AGI2", ffht(Fre) - ffht(Fa2), diffboot(Fre, Fa2)); print("re-arc minus Concept", ffht(Fre) - ffht(Fco), diffboot(Fre, Fco))

print("=== 9. FA-LOO minus fit, Qwen, bootstrap by task")
def fit_diff(rows):
    def stat(s):
        V = [r for r in s if r["verified"]]; A_ = [r for r in s if r["verified"] and r["a"] and r["b"] and r["c"]]
        if not V or not A_: return None
        return 100 * (sum(r["cons"] for r in A_) / len(A_) - sum(r["full"] for r in V) / len(V))
    return stat(rows), boot(rows, stat)
base_con = [score_task(CO[t], S2[("full", t, -1)], {i: S2.get(("fold", t, i)) for i in range(len(CO[t]["train"]))}) for t in CO]
print("AGI2", fit_diff(list(base.values())), "Concept", fit_diff(base_con), "re-arc", fit_diff(list(rows.values())), "AGI2 retry", fit_diff(list(retried.values())))
print("Concept tasks: verified", sum(r["verified"] for r in base_con), "right", sum(r["full"] for r in base_con if r["verified"]), "abc", sum(1 for r in base_con if r["verified"] and r["a"] and r["b"] and r["c"]))

print("=== 10. token multiples, ARC-AGI-2")
full_tok = sum(S1[("full", t, -1)].get("gen_tokens", 0) for t in A2)
vt = [t for t in A2 if out(S1[("full", t, -1)])[1]]
fold_all = sum(S1[k].get("gen_tokens", 0) for k in S1 if k[0] == "fold")
fold_v = sum(S1[k].get("gen_tokens", 0) for k in S1 if k[0] == "fold" and k[1] in vt)
ret_tok = sum(r.get("gen_tokens", 0) for k, r in RET.items())
print("full tokens", full_tok, "all folds ratio", (full_tok + fold_all) / full_tok, "folds on verified ratio", (full_tok + fold_v) / full_tok, "with retries (55 used)", (full_tok + fold_v + 3427983) / full_tok, "n folds verified tasks", sum(1 for k in S1 if k[0] == "fold" and k[1] in vt))

print("=== 11. per-run verified precision, 16k runs, and merge orders from the notebook-mode Monty cache")
Mcache = json.load(open(ROOT + "/research/paper/judge_v8b/audit/out/monty_agi2_eval_notebook.json"))
def samples(fn):
    by = defaultdict(dict)
    for line in open(RES + fn):
        r = json.loads(line); by[r["task_id"]][r["sample"]] = r
    return by
P = samples("qwen38_ps_b16384.jsonl"); X = samples("qwen38_ps_xhigh_b16384.jsonl")
pool_r = pool_n = 0
for name, by in (("P", P), ("X", X)):
    for s in (0, 1):
        n_ = c_ = 0.0
        for t, d in by.items():
            if s not in d: continue
            v = [x for x in d[s]["rounds"] if x.get("verified")]
            if v:
                tr_ = [p["output"] for p in A2[t]["test"]]
                n_ += 1; c_ += sum(dumps(g) == dumps(tr_[i]) for i, g in enumerate(v[0]["test_out"])) / len(tr_)
        pool_r += c_; pool_n += n_
        print(name, s, "verified", n_, "right", round(c_, 2), round(100 * c_ / max(1, n_), 1))
print("pooled", round(pool_r, 2), pool_n, round(100 * pool_r / pool_n, 1))
def pools(by, t, k, samp):
    """Tiers as the notebook's summarize(): every round's output, ranked inside a tier by (verified count, best n_ok)."""
    S_ = {}
    for j in samp:
        r = by[t].get(j)
        if not r: continue
        for x in r["rounds"]:
            to = x.get("test_out")
            if not to or k >= len(to) or to[k] is None: continue
            key = dumps(to[k]); a_ = S_.get(key, (0, -1))
            S_[key] = (a_[0] + bool(x.get("verified")), max(a_[1], x.get("n_ok", -1)))
    R_ = sorted(S_, key=lambda z: S_[z], reverse=True)
    V = [z for z in R_ if S_[z][0] > 0]; U = [z for z in R_ if S_[z][0] == 0]
    C = [dumps(g) for g in (Mcache[t]["confident"][k] if k < len(Mcache[t]["confident"]) else [])]
    G = [dumps(g) for g in (Mcache[t]["guesses"][k] if k < len(Mcache[t]["guesses"]) else [])]
    return dict(V=V, U=U, C=C, G=G)
def merge_score(by, order, samp, rng=None):
    s_ = 0.0
    for t in A2:
        tr_ = [p["output"] for p in A2[t]["test"]]
        for k in range(len(tr_)):
            pl = pools(by, t, k, samp); seen = []
            L_ = [g for o in order for g in pl[o]]
            if rng is not None: rng.shuffle(L_)
            for g in L_:
                if g not in seen and len(seen) < 2: seen.append(g)
            s_ += (dumps(tr_[k]) in seen) / len(tr_)
    return s_
for nm, by, samp in (("one sample", P, [0]), ("replicate", X, [0]), ("two samples", P, [0, 1])):
    rs = [merge_score(by, list("VUCG"), samp, random.Random(i)) for i in range(40)]
    crowded = sum(len(set(sum(pools(by, t, k, samp).values(), []))) > 2 for t in A2 for k in range(len(A2[t]["test"])))
    print(nm, "precision", merge_score(by, list("VCUG"), samp), "conf ignored", merge_score(by, list("VUG"), samp), "reversed GCUV", merge_score(by, list("GCUV"), samp), "guesses only first GVCU", merge_score(by, list("GVCU"), samp),
          "unverified before verified UVCG", merge_score(by, list("UVCG"), samp), "Qwen alone", merge_score(by, list("VU"), samp), "random", round(sum(rs) / 40, 1), min(rs), max(rs), "crowded", crowded)

print("=== 12. retried folds that came to fit, first run")
fit_ = pred = pred_right = miss_right = 0.0
for t in A2:
    if not out(S1[("full", t, -1)])[1]: continue
    demos = sorted_demos(A2[t]); nt = len(A2[t]["test"])
    for i in range(len(demos)):
        if out(S1[("fold", t, i)])[1]: continue
        for att in (1, 2):
            r = RET.get(("retry", t, i * 100 + att))
            if r is None: continue
            d, v = out(r)
            if v:
                fit_ += 1
                h = d.get("demo:%d" % i) is not None and dumps(d["demo:%d" % i]) == dumps(demos[i]["output"])
                tr = sum(d.get("test:%d" % k) is not None and dumps(d["test:%d" % k]) == dumps(A2[t]["test"][k]["output"]) for k in range(nt)) / nt
                if h: pred += 1; pred_right += tr
                else: miss_right += tr
                break
print("fit", fit_, "predict held-out", pred, "of those right on test", pred_right, "miss", fit_ - pred, "right", miss_right)
