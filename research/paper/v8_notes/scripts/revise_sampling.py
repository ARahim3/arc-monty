"""v8 revision: own re-derivation of the planned Qwen run (sampling, 32k per round, 120 public-eval tasks; stages 1 and 1b).
Does not import faloo_sampling_analyze.py; definitions follow the plan in research/arc2/faloo_qwen_sampling.md. Read-only, single process.
Output: ../revise_sampling.txt, ../revise_sampling.json"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, json, math, zlib
import numpy as np
from scipy import stats as st
R = (_REPO + "/")
CH = json.load(open(R + "data/kaggle_format/agi2_eval_challenges.json"))
SOL = json.load(open(R + "data/kaggle_format/agi2_eval_solutions.json"))
J = {}
def canon(d):
    return sorted(d, key=lambda p: (len(p["input"]) * len(p["input"][0]), len(p["input"]), len(p["input"][0]), json.dumps(p["input"])))
REC = {}
errs = 0
for f in ("qwen38_faloo_sampling_b32768.jsonl", "qwen38_faloo_sampling_plain_b32768.jsonl"):
    for l in open(R + "llm/results/" + f):
        r = json.loads(l)
        if "error" in r:
            errs += 1
            continue
        REC.setdefault((r["kind"], r["task_id"], r["fold"]), r)
print("records", collections.Counter(k[0] for k in REC), "errors", errs, "tokens by kind", {k: sum(v["gen_tokens"] for kk, v in REC.items() if kk[0] == k) for k in ("full", "fold", "plain")})
def view(r):
    t = r["task_id"]; nt = len(SOL[t])
    rs = [x for x in r.get("rounds", []) if "test_out" in x]
    if rs:
        v = [x for x in rs if x.get("verified")]
        x = v[0] if v else rs[-1]
        d = dict(zip(r["query_ids"], x["test_out"]))
        ver = bool(v)
    else:
        d, ver = {}, False
    tests = [d.get(f"test:{k}") for k in range(nt)]
    out = dict(ver=ver, tests=tests, right=sum(tests[k] == SOL[t][k] for k in range(nt)) / nt, tokens=r["gen_tokens"], kind=r["kind"], fold=r["fold"])
    if r["kind"] == "fold":
        out["held"] = d.get(f"demo:{r['fold']}") == canon(CH[t]["train"])[r["fold"]]["output"]
        out["vh"] = out["ver"] and out["held"]
    return out
T = sorted(CH)
FULL = {t: view(REC[("full", t, -1)]) for t in T}
FOLD = {t: [view(REC[("fold", t, i)]) for i in range(len(CH[t]["train"]))] for t in T}
PL = {t: [FULL[t]] + [view(REC[("plain", t, k)]) for k in (1, 2, 3)] for t in T}
print("tasks", len(T), "folds", sum(len(v) for v in FOLD.values()), "mean worst case", round(100 * np.mean([1 / (len(CH[t]["train"]) + 1) for t in T]), 2))
def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * (c + h), 1)
def boot(cl_fn, tasks, B=10000, seed=0):
    rng = np.random.default_rng(seed)
    n = len(tasks); out = []
    idx = rng.integers(0, n, size=(B, n))
    for row in idx:
        v = cl_fn([tasks[i] for i in row])
        if v is not None:
            out.append(v)
    return (float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)))
# ---- certificate
ver = [t for t in T if FULL[t]["ver"]]
vr = sum(FULL[t]["right"] for t in ver)
print(f"verified {len(ver)}, right {vr:.2f}, {100*vr/len(ver):.1f}%; Wilson unrounded {wilson(vr,len(ver))}, rounded {wilson(round(vr),len(ver))}")
def folds_ok(t):
    return all(x["held"] for x in FOLD[t])
def agree(t):
    a = [json.dumps(x["tests"]) for x in FOLD[t]]
    return len(set(a)) == 1 and all(g is not None for g in FOLD[t][0]["tests"])
AB = [t for t in T if folds_ok(t) and agree(t)]
ABC = [t for t in AB if FULL[t]["ver"] and FULL[t]["tests"] == FOLD[t][0]["tests"]]
abr = sum(FOLD[t][0]["right"] for t in AB); abcr = sum(FOLD[t][0]["right"] for t in ABC)
print(f"(a)+(b) {len(AB)} right {abr}; Wilson {wilson(abr,len(AB))}; (a)+(b)+(c) {len(ABC)} right {abcr}; Wilson {wilson(abcr,len(ABC))}; coverage {100*len(ABC)/120:.1f}%")
A_ = [t for t in T if folds_ok(t)]
aall = [t for t in A_ if FULL[t]["right"] == 1]
print(f"(a) with A(D)'s answer: {len(A_)} tasks, all right {len(aall)}, not all right {[ (t, round(FULL[t]['right'],2), FULL[t]['ver']) for t in A_ if FULL[t]['right']<1 ]}")
print("verified and every fold held and wrong:", [t for t in ver if folds_ok(t) and FULL[t]["right"] < 1], "| (a)+(b) without (c):", [t for t in AB if t not in ABC], [FOLD[t][0]["right"] for t in AB if t not in ABC])
W = [t for t in ver if FULL[t]["right"] < 1]; RR = [t for t in ver if FULL[t]["right"] == 1]
kept = [t for t in ABC if t in W]
p = math.comb(len(ver) - len(W), len(ABC)) / math.comb(len(ver), len(ABC))
print(f"not fully right {len(W)}; kept {len(kept)}; fully right {len(RR)}; rejected right {len([t for t in RR if t not in ABC])}; random avoid p {p:.4f}")
J["cert"] = dict(ver=len(ver), right=vr, ab=len(AB), abc=len(ABC), wrong=len(W), p=p)
# AUROC with exact permutation p
rate = {t: sum(x["held"] for x in FOLD[t]) / len(FOLD[t]) for t in ver}
def auroc(ts):
    a = [rate[t] for t in ts if FULL[t]["right"] == 1]; b = [rate[t] for t in ts if FULL[t]["right"] < 1]
    if not a or not b:
        return None
    return sum((x > y) + .5 * (x == y) for x in a for y in b) / (len(a) * len(b))
au = auroc(ver)
ci = boot(auroc, ver)
ranks = st.rankdata([rate[t] for t in ver])
dr = [int(round(2 * r)) for r in ranks]
Rn = len(RR); N = len(ver)
dp = [collections.Counter() for _ in range(Rn + 1)]; dp[0][0] = 1
for v in dr:
    for k in range(Rn - 1, -1, -1):
        for s, c in dp[k].items():
            dp[k + 1][s + v] += c
total = sum(dp[Rn].values())
obs = sum(d for d, t in zip(dr, ver) if FULL[t]["right"] == 1)
pv = sum(c for s, c in dp[Rn].items() if s >= obs) / total
print(f"AUROC {au:.3f} [{ci[0]:.2f}, {ci[1]:.2f}]; exact one-sided p {pv:.4f}; right {Rn}, wrong {N-Rn}")
J["auroc"] = dict(a=au, ci=ci, p=pv)
print(f"joint: wrong among (a)+(b)+(c): {sum(1-FOLD[t][0]['right'] for t in ABC)}, among (a)+(b): {sum(1-FOLD[t][0]['right'] for t in AB)} of 120")
# ---- P1
vf = [(t, x) for t in T for x in FOLD[t] if x["ver"]]
hx = [x for _, x in vf if x["held"]]; mx = [x for _, x in vf if not x["held"]]
pr = lambda xs: sum(x["right"] for x in xs) / len(xs)
print(f"P1: verified fold programs {len(vf)} in {len({t for t,_ in vf})} tasks, {100*pr([x for _,x in vf]):.1f}%; predict {len(hx)}, {100*pr(hx):.1f}%; miss {len(mx)}, {100*pr(mx):.1f}%")
by = collections.defaultdict(list)
for t, x in vf:
    by[t].append(x)
ts = sorted(by)
C = np.array([[sum(x["right"] for x in by[t] if x["held"]), sum(x["held"] for x in by[t]), sum(x["right"] for x in by[t] if not x["held"]), sum(not x["held"] for x in by[t])] for t in ts], float)
Wm = np.random.default_rng(0).multinomial(len(ts), np.full(len(ts), 1 / len(ts)), size=10000)
with np.errstate(invalid="ignore", divide="ignore"):
    d = (Wm @ C[:, 0]) / (Wm @ C[:, 1]) - (Wm @ C[:, 2]) / (Wm @ C[:, 3])
d = d[~np.isnan(d)]
print(f"  difference {100*(C[:,0].sum()/C[:,1].sum()-C[:,2].sum()/C[:,3].sum()):+.1f} [{100*np.percentile(d,2.5):+.1f}, {100*np.percentile(d,97.5):+.1f}]")
both = [t for t in ts if any(x["held"] for x in by[t]) and any(not x["held"] for x in by[t])]
pd_ = np.array([np.mean([x["right"] for x in by[t] if x["held"]]) - np.mean([x["right"] for x in by[t] if not x["held"]]) for t in both])
Wb = np.random.default_rng(0).multinomial(len(both), np.full(len(both), 1 / len(both)), size=10000)
bb = (Wb @ pd_) / len(both)
print(f"  within {len(both)} tasks with both kinds: {100*pd_.mean():+.1f} [{100*np.percentile(bb,2.5):+.1f}, {100*np.percentile(bb,97.5):+.1f}]")
J["p1"] = dict(n=len(vf), held=len(hx), miss=len(mx), ph=pr(hx), pm=pr(mx))
# ---- P2
H = np.array([sum(x["held"] for x in FOLD[t]) for t in T], float); Te = np.array([sum(x["right"] for x in FOLD[t]) for t in T]); Nn = np.array([len(FOLD[t]) for t in T], float)
Aa = np.array([sum(1 - x["right"] for x in FOLD[t] if x["held"]) for t in T]); Bb = np.array([sum(x["right"] for x in FOLD[t] if not x["held"]) for t in T])
Wm = np.random.default_rng(0).multinomial(120, np.full(120, 1 / 120), size=10000)
dd = (Wm @ (H - Te)) / (Wm @ Nn)
sg = H - Te
more, less = int((sg > 1e-9).sum()), int((sg < -1e-9).sum())
print(f"P2: folds {int(Nn.sum())}; held {H.sum():.0f} ({100*H.sum()/Nn.sum():.1f}%), test {Te.sum():.2f} ({100*Te.sum()/Nn.sum():.1f}%), diff {100*(H.sum()-Te.sum())/Nn.sum():+.1f} [{100*np.percentile(dd,2.5):+.1f}, {100*np.percentile(dd,97.5):+.1f}]; held-only {Aa.sum():.2f}, test-only {Bb.sum():.2f}; tasks {more}:{less}, sign p {st.binomtest(more,more+less,.5).pvalue:.4f}")
sing = [i for i, t in enumerate(T) if len(SOL[t]) == 1]; mult = [i for i, t in enumerate(T) if len(SOL[t]) > 1]
print(f"  single-test {H[sing].sum():.0f} vs {Te[sing].sum():.1f} of {Nn[sing].sum():.0f}; multi-test {H[mult].sum():.0f} vs {Te[mult].sum():.1f} of {Nn[mult].sum():.0f}")
# ---- P3
def order(t, n):
    return sorted(range(n), key=lambda i: zlib.crc32(f"20261101|p3|{t}|{i}".encode()))
def p2(runs, t):
    hit = 0
    for k in range(len(SOL[t])):
        top = []
        for _, tests in sorted(runs, key=lambda r: r[0]):
            g = tests[k]
            if g is not None and g not in top:
                top.append(g)
            if len(top) == 2:
                break
        hit += SOL[t][k] in top
    return hit / len(SOL[t])
for c in (2, 3, 4):
    rows = []
    for t in T:
        n = len(CH[t]["train"]); b = min(n + 1, c)
        pl = PL[t][:b]
        fo = [FULL[t]] + [FOLD[t][i] for i in order(t, n)]; fo = fo[:b]
        sp = p2([(0 if x["ver"] else 1, x["tests"]) for x in pl], t)
        sf = p2([(0 if x.get("vh", x["ver"]) else 1, x["tests"]) for x in fo], t)
        s3 = p2([((0 if x["vh"] else (1 if x["ver"] else 2)) if x["kind"] == "fold" else (0 if x["ver"] else 2), x["tests"]) for x in fo], t)
        rows.append((sp, sf, s3, sum(x["tokens"] for x in pl), sum(x["tokens"] for x in fo)))
    a = np.array(rows)
    dv = a[:, 1] - a[:, 0]
    ci = np.percentile(Wm @ dv, [2.5, 97.5])
    print(f"P3 c={c}: plain {a[:,0].sum():.2f}, fold {a[:,1].sum():.2f}, minus {dv.sum():+.2f} [{ci[0]:+.1f}, {ci[1]:+.1f}]; better fold {int((dv>0).sum())}, plain {int((dv<0).sum())}; three tiers {a[:,2].sum():.2f}; tokens {a[:,3].sum()/1e6:.1f}M / {a[:,4].sum()/1e6:.1f}M")
# ---- per-run precision, all tasks
Q = [[sum(x["right"] for x in PL[t] if x["ver"]), sum(x["ver"] for x in PL[t]), sum(x["right"] for x in FOLD[t] if x["vh"]), sum(x["vh"] for x in FOLD[t])] for t in T]
Q = np.array(Q, float)
with np.errstate(invalid="ignore", divide="ignore"):
    pa = (Wm @ Q[:, 0]) / (Wm @ Q[:, 1]); pb = (Wm @ Q[:, 2]) / (Wm @ Q[:, 3])
print(f"per run: plain verified {Q[:,0].sum():.2f}/{Q[:,1].sum():.0f} = {100*Q[:,0].sum()/Q[:,1].sum():.1f}% [{100*np.percentile(pa,2.5):.1f}, {100*np.percentile(pa,97.5):.1f}]; fold vh {Q[:,2].sum():.1f}/{Q[:,3].sum():.0f} = {100*Q[:,2].sum()/Q[:,3].sum():.1f}% [{100*np.percentile(pb,2.5):.1f}, {100*np.percentile(pb,97.5):.1f}]; diff {100*(Q[:,2].sum()/Q[:,3].sum()-Q[:,0].sum()/Q[:,1].sum()):+.1f} [{100*np.percentile(pb-pa,2.5):+.1f}, {100*np.percentile(pb-pa,97.5):+.1f}]")
# ---- hard tasks
hard = [t for t in T if not FULL[t]["ver"]]
Y = []
for t in hard:
    pl = PL[t][1:]; fo = FOLD[t]
    Y.append([len(pl), sum(x["ver"] for x in pl), sum(x["right"] for x in pl if x["ver"]), len(fo), sum(x["vh"] for x in fo), sum(x["right"] for x in fo if x["vh"])])
Y = np.array(Y, float)
Wh = np.random.default_rng(0).multinomial(len(hard), np.full(len(hard), 1 / len(hard)), size=10000)
dy = (Wh @ Y[:, 5]) / (Wh @ Y[:, 3]) - (Wh @ Y[:, 2]) / (Wh @ Y[:, 0])
print(f"hard tasks {len(hard)}: plain runs {Y[:,0].sum():.0f}, verified {Y[:,1].sum():.0f}, {100*Y[:,2].sum()/Y[:,1].sum():.1f}%, right {Y[:,2].sum():.1f}; folds {Y[:,3].sum():.0f}, vh {Y[:,4].sum():.0f}, {100*Y[:,5].sum()/Y[:,4].sum():.1f}%, right {Y[:,5].sum():.1f}; right per run diff {Y[:,5].sum()/Y[:,3].sum()-Y[:,2].sum()/Y[:,0].sum():+.3f} [{np.percentile(dy,2.5):+.3f}, {np.percentile(dy,97.5):+.3f}]")
# ---- cost
full = sum(FULL[t]["tokens"] for t in T); folds = sum(x["tokens"] for t in T for x in FOLD[t])
fv = sum(x["tokens"] for t in ver for x in FOLD[t]); nf = sum(len(FOLD[t]) for t in ver)
ee = ec = 0
for t in ver:
    for x in FOLD[t]:
        ee += x["tokens"]; ec += 1
        if not x["held"]:
            break
mn = np.mean([len(CH[t]["train"]) for t in T]); mv = np.mean([len(CH[t]["train"]) for t in ver])
print(f"cost: full {full/1e6:.2f}M; folds {folds/1e6:.2f}M -> {(full+folds)/full:.2f}x; on {len(ver)} verified tasks {nf} folds -> {(full+fv)/full:.2f}x; early exit {ec} folds -> {(full+ee)/full:.2f}x; v {len(ver)/120:.3f}, mean n {mn:.2f}, 1+vn {1+len(ver)/120*mn:.2f}, mean n on verified {mv:.2f}")
print(f"tokens per run: full {full/120/1e3:.1f}k, fold {folds/359/1e3:.1f}k, plain {sum(v['gen_tokens'] for k,v in REC.items() if k[0]=='plain')/360/1e3:.1f}k")
# ---- replay
TO = sorted(T, key=lambda t: zlib.crc32(f"20261101|order|{t}".encode()))
def seq(pol, t):
    if pol in ("i", "ii"):
        return [(x["ver"], x, False) for x in PL[t]]
    n = len(CH[t]["train"])
    fo = [FOLD[t][i] for i in order(t, n)]
    last_cert = t in ABC
    return [(FULL[t]["ver"], FULL[t], False)] + [(x["vh"], x, False) for x in fo[:-1]] + [(fo[-1]["vh"], fo[-1], last_cert)] + [(x["ver"], x, False) for x in PL[t][1:]]
for pol in ("i", "ii", "iii"):
    S = {t: seq(pol, t) for t in TO}; pos = {t: 0 for t in TO}; stop = set(); spent = 0
    budgets = [b * 1000 * 120 for b in (32, 64, 96, 128, 160, 192, 224, 256, 288, 320)]; bi = 0; res = []
    def score():
        s = 0
        for t in TO:
            used = S[t][:pos[t]]
            if not used:
                continue
            runs = [(0 if u[0] else 1, u[1]["tests"]) for u in used]
            cert = next((u[1]["tests"] for u in used if u[2]), None)
            if cert is not None:
                runs = [(-1, cert)] + runs
            s += p2(runs, t)
        return s
    prog = True
    while bi < len(budgets) and prog:
        prog = False
        for t in TO:
            if t in stop or pos[t] >= len(S[t]):
                continue
            u = S[t][pos[t]]; pos[t] += 1; spent += u[1]["tokens"]; prog = True
            if (pol == "ii" and u[0]) or (pol == "iii" and u[2]):
                stop.add(t)
            while bi < len(budgets) and spent >= budgets[bi]:
                res.append((budgets[bi] // 120000, round(score(), 2))); bi += 1
    print(f"replay {pol}: {res}; final {score():.2f} at {spent/120/1e3:.0f}k per task; stopped {len(stop)}")
json.dump(J, open(R + "research/paper/v8_notes/revise_sampling.json", "w"), indent=1, default=float)
# ---- (a) with the full-data answer: tasks that have an answer at all
withans = [t for t in A_ if any(g is not None for g in FULL[t]["tests"])]
print("(a) passes:", len(A_), "with a full-data answer:", len(withans), "all right:", sum(FULL[t]["right"] == 1 for t in withans), "| no answer:", [t for t in A_ if t not in withans])
print("first sample unverified tasks", len(hard), "| verified tasks where folds all held but no agreement or no match:", [(t, agree(t), FULL[t]["tests"] == FOLD[t][0]["tests"]) for t in ver if folds_ok(t) and t not in ABC])
