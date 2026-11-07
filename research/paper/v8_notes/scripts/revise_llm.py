"""v8 revision: own re-derivation of the Qwen findings, greedy FA-LOO run and plain runs. Written without importing lead_holdback*.py.
Output ../revise_llm.txt, ../revise_llm.json. Read-only; single process."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, json, math, os, random
import numpy as np
from scipy import stats as st
R = (_REPO + "/")
CH = json.load(open(R + "data/kaggle_format/agi2_eval_challenges.json"))
SOL = json.load(open(R + "data/kaggle_format/agi2_eval_solutions.json"))
J = {}
def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * (c - h), 100 * (c + h))
def canon(demos):
    return sorted(demos, key=lambda p: (len(p["input"]) * len(p["input"][0]), len(p["input"]), len(p["input"][0]), json.dumps(p["input"])))
# one record per (kind, task, fold), first occurrence, both files of the greedy run
G = {}
for f in ("qwen38_faloo_greedy_b16384.jsonl", "qwen38_faloo_greedy_b16384_C.jsonl"):
    for l in open(R + "llm/results/" + f):
        r = json.loads(l)
        if "error" in r:
            continue
        G.setdefault((r["kind"], r["task_id"], r["fold"]), r)
print("records", collections.Counter(k[0] for k in G))
def final(r):
    rs = [x for x in r.get("rounds", []) if "test_out" in x]
    if not rs:
        return None, False
    v = [x for x in rs if x.get("verified")]
    x = v[0] if v else rs[-1]
    return dict(zip(r["query_ids"], x["test_out"])), bool(v)
FULL, FOLD = {}, collections.defaultdict(list)
for t in sorted(CH):
    nt = len(SOL[t]); n = len(CH[t]["train"]); demos = canon(CH[t]["train"])
    o, v = final(G[("full", t, -1)])
    tests = [None if o is None else o.get(f"test:{i}") for i in range(nt)]
    FULL[t] = dict(ver=v, tests=tests, right=sum(tests[i] == SOL[t][i] for i in range(nt)) / nt, cost=G[("full", t, -1)]["cost"])
    for i in range(n):
        r = G[("fold", t, i)]
        o, v = final(r)
        tests = [None if o is None else o.get(f"test:{k}") for k in range(nt)]
        held = bool(o is not None and o.get(f"demo:{i}") == demos[i]["output"])
        FOLD[t].append(dict(i=i, ver=v, held=held, tests=tests, right=sum(tests[k] == SOL[t][k] for k in range(nt)) / nt, cost=r["cost"]))
tasks = sorted(FULL)
allf = [x for t in tasks for x in FOLD[t]]
print("folds", len(allf), "full", len(FULL))
# ---- C. prediction inside fold programs
vf = [(t, x) for t in tasks for x in FOLD[t] if x["ver"]]
hx = [(t, x) for t, x in vf if x["held"]]; mx = [(t, x) for t, x in vf if not x["held"]]
pr = lambda xs: sum(x["right"] for _, x in xs) / len(xs)
print(f"fold programs verified on what they saw: {len(vf)} programs in {len({t for t,_ in vf})} tasks, right {sum(x['right'] for _,x in vf):.1f}, {100*pr(vf):.1f}%")
print(f"  predict held-out: {len(hx)} in {len({t for t,_ in hx})} tasks, right {sum(x['right'] for _,x in hx):.1f}, {100*pr(hx):.1f}%")
print(f"  miss it: {len(mx)} in {len({t for t,_ in mx})} tasks, right {sum(x['right'] for _,x in mx):.1f}, {100*pr(mx):.1f}%")
by = collections.defaultdict(list)
for t, x in vf:
    by[t].append(x)
ts = sorted(by); rng = np.random.default_rng(0)
C = np.array([[sum(x["right"] for x in by[t] if x["held"]), sum(1 for x in by[t] if x["held"]), sum(x["right"] for x in by[t] if not x["held"]), sum(1 for x in by[t] if not x["held"])] for t in ts], float)
W = rng.multinomial(len(ts), np.full(len(ts), 1 / len(ts)), size=10000)
with np.errstate(invalid="ignore", divide="ignore"):
    d = (W @ C[:, 0]) / (W @ C[:, 1]) - (W @ C[:, 2]) / (W @ C[:, 3])
d = d[~np.isnan(d)]
est = C[:, 0].sum() / C[:, 1].sum() - C[:, 2].sum() / C[:, 3].sum()
print(f"  difference {100*est:+.1f} [{100*np.percentile(d,2.5):+.1f}, {100*np.percentile(d,97.5):+.1f}] over {len(ts)} tasks")
J["lift"] = dict(n=len(vf), held=len(hx), miss=len(mx), p_all=pr(vf), p_held=pr(hx), p_miss=pr(mx), diff=est, ci=(np.percentile(d, 2.5), np.percentile(d, 97.5)), tasks=len(ts))
# fold that passes vs plain verified full-data run, one fold per task in expectation
fv = [t for t in tasks if FULL[t]["ver"]]
print(f"full-data verified {len(fv)}, right {sum(FULL[t]['right'] for t in fv)}, wilson {wilson(sum(FULL[t]['right'] for t in fv), len(fv))}")
A = np.zeros((len(tasks), 4))
for j, t in enumerate(tasks):
    xs = FOLD[t]; ok = [x for x in xs if x["ver"] and x["held"]]
    A[j, 0] = sum(x["right"] for x in ok) / len(xs); A[j, 1] = len(ok) / len(xs)
    if FULL[t]["ver"]:
        A[j, 2] = FULL[t]["right"]; A[j, 3] = 1
W = np.random.default_rng(0).multinomial(len(tasks), np.full(len(tasks), 1 / len(tasks)), size=10000)
pa = (W @ A[:, 0]) / (W @ A[:, 1]); pb = (W @ A[:, 2]) / (W @ A[:, 3])
e1, e2 = A[:, 0].sum() / A[:, 1].sum(), A[:, 2].sum() / A[:, 3].sum()
print(f"one random passing fold per task: expected answered {A[:,1].sum():.1f}, right {A[:,0].sum():.1f}, {100*e1:.1f}% ; full verified {100*e2:.1f}% ; diff {100*(e1-e2):+.1f} [{100*np.percentile(pa-pb,2.5):+.1f}, {100*np.percentile(pa-pb,97.5):+.1f}]")
J["fold_vs_full"] = dict(e1=e1, e2=e2, ci=(np.percentile(pa - pb, 2.5), np.percentile(pa - pb, 97.5)))
# ---- D. discordant test
HR = np.array([sum(x["held"] for x in FOLD[t]) for t in tasks], float)
TR = np.array([sum(x["right"] for x in FOLD[t]) for t in tasks])
NF = np.array([len(FOLD[t]) for t in tasks], float)
AA = np.array([sum((1 - x["right"]) for x in FOLD[t] if x["held"]) for t in tasks])
BB = np.array([sum(x["right"] for x in FOLD[t] if not x["held"]) for t in tasks])
W = np.random.default_rng(0).multinomial(len(tasks), np.full(len(tasks), 1 / len(tasks)), size=10000)
dd = (W @ (HR - TR)) / (W @ NF)
more, less = int(((AA - BB) > 1e-9).sum()), int(((AA - BB) < -1e-9).sum())
p = st.binomtest(more, more + less, .5).pvalue
print(f"discordant: folds {int(NF.sum())}; held {HR.sum():.0f} ({100*HR.sum()/NF.sum():.1f}%), test {TR.sum():.1f} ({100*TR.sum()/NF.sum():.1f}%), diff {100*(HR.sum()-TR.sum())/NF.sum():+.1f} [{100*np.percentile(dd,2.5):+.1f}, {100*np.percentile(dd,97.5):+.1f}]; held-only {AA.sum():.1f}, test-only {BB.sum():.1f}; tasks {more}:{less}, two-sided sign p {p:.4f}")
J["discordant"] = dict(folds=int(NF.sum()), held=float(HR.sum()), test=float(TR.sum()), ci=(np.percentile(dd, 2.5), np.percentile(dd, 97.5)), a=float(AA.sum()), b=float(BB.sum()), more=more, less=less, p=float(p))
# single-test tasks only, and verified-only subset, to see the effect is not an artefact of multi-test tasks
st1 = [t for t in tasks if len(SOL[t]) == 1]
print(f"  single-test tasks only ({len(st1)}): held {sum(HR[tasks.index(t)] for t in st1):.0f}, test {sum(TR[tasks.index(t)] for t in st1):.1f} of {sum(NF[tasks.index(t)] for t in st1):.0f}")
mt = [t for t in tasks if len(SOL[t]) > 1]
print(f"  multi-test tasks ({len(mt)}): held {sum(HR[tasks.index(t)] for t in mt):.0f}, test {sum(TR[tasks.index(t)] for t in mt):.1f} of {sum(NF[tasks.index(t)] for t in mt):.0f}")
vt = [x for x in allf if x["ver"]]
print(f"  among fold programs verified on what they saw ({len(vt)}): held {sum(x['held'] for x in vt)}, test {sum(x['right'] for x in vt):.1f}")
ni = np.array([len(CH[t]["train"]) for t in tasks], float)
print(f"mean held rate over folds {HR.sum()/NF.sum():.4f}; full-data right {sum(FULL[t]['right'] for t in tasks)}/120 = {100*sum(FULL[t]['right'] for t in tasks)/120:.1f}%")
# ---- E2. cost
full = sum(FULL[t]["cost"] for t in tasks); folds = sum(x["cost"] for x in allf)
vf_f = sum(x["cost"] for t in fv for x in FOLD[t]); nvf = sum(len(FOLD[t]) for t in fv)
ee = ec = 0
for t in fv:
    for x in FOLD[t]:
        ee += x["cost"]; ec += 1
        if not x["held"]:
            break
print(f"cost: full {full/1e6:.2f}M; all folds {folds/1e6:.2f}M -> {(full+folds)/full:.2f}x; folds on {len(fv)} verified tasks: {nvf} folds {vf_f/1e6:.2f}M -> {(full+vf_f)/full:.2f}x; early exit: {ec} folds {ee/1e6:.2f}M -> {(full+ee)/full:.2f}x")
J["cost"] = dict(full=full, folds=folds, r_all=(full + folds) / full, nvf=nvf, r_v=(full + vf_f) / full, ee=ec, r_ee=(full + ee) / full)
cert = [t for t in tasks if FULL[t]["ver"] and all(x["held"] for x in FOLD[t]) and len({json.dumps(x["tests"]) for x in FOLD[t]}) == 1 and json.dumps(FOLD[t][0]["tests"]) == json.dumps(FULL[t]["tests"])]
aonly = [t for t in tasks if all(x["held"] for x in FOLD[t])]
agree = [t for t in aonly if len({json.dumps(x["tests"]) for x in FOLD[t]}) == 1]
print("certified", len(cert), [FULL[t]["right"] for t in cert], "| (a) passes", len(aonly), [(t, FULL[t]["ver"], FULL[t]["right"]) for t in aonly if t not in cert], "| (a)+(b)", len(agree))
# ---- 3. same-token comparison
P = collections.defaultdict(list)
for fn in ("qwen38_ps_b16384.jsonl", "qwen38_ps_xhigh_b16384.jsonl"):
    for l in open(R + "llm/results/" + fn):
        r = json.loads(l)
        if "error" in r or r.get("task_id") not in SOL:
            continue
        t = r["task_id"]; nt = len(SOL[t])
        rs = [x for x in r.get("rounds", []) if "n_ok" in x]
        v = [x for x in rs if x.get("verified")]
        c = v[0] if v else (rs[-1] if rs else None)
        tests = [None] * nt if c is None or "test_out" not in c else (c["test_out"] + [None] * nt)[:nt]
        P[t].append(dict(ver=bool(v), tests=tests, cost=r.get("cost", 0)))
def pass2(cands, t):
    nt = len(SOL[t]); ok = 0
    for k in range(nt):
        seen = []
        for _, tests in sorted(cands, key=lambda c: c[0]):
            g = tests[k]
            if g is None:
                continue
            if g not in seen:
                seen.append(g)
            if len(seen) == 2:
                break
        ok += SOL[t][k] in seen
    return ok / nt
com = [t for t in tasks if len(P[t]) >= 3]
print("tasks with >=3 plain samples", len(com), "mean plain runs", np.mean([len(P[t]) for t in com]), "mean full+fold runs", np.mean([1 + len(FOLD[t]) for t in com]))
print("tokens per task: plain %.1fk; full+folds %.1fk" % (np.mean([sum(x["cost"] for x in P[t]) for t in com]) / 1e3, np.mean([FULL[t]["cost"] + sum(x["cost"] for x in FOLD[t]) for t in com]) / 1e3))
pl = {t: pass2([(0 if x["ver"] else 1, x["tests"]) for x in P[t]], t) for t in com}
ff = {t: pass2([(0 if FULL[t]["ver"] else 2, FULL[t]["tests"])] + [(0 if (x["ver"] and x["held"]) else (1 if x["ver"] else 2), x["tests"]) for x in FOLD[t]], t) for t in com}
dv = np.array([ff[t] - pl[t] for t in com])
W = np.random.default_rng(0).multinomial(len(com), np.full(len(com), 1 / len(com)), size=10000)
ci = np.percentile(W @ dv, [2.5, 97.5])
print(f"plain {sum(pl.values()):.1f}; full+folds {sum(ff.values()):.1f}; difference {dv.sum():+.1f} [{ci[0]:+.1f}, {ci[1]:+.1f}]; tasks better {int((dv>0).sum())}, worse {int((dv<0).sum())}")
J["same_token"] = dict(plain=sum(pl.values()), ff=sum(ff.values()), diff=float(dv.sum()), ci=ci.tolist(), n=len(com))
fail = [t for t in tasks if not FULL[t]["ver"]]
plr = [x for t in fail for x in P[t]]
plv = [(t, x) for t in fail for x in P[t] if x["ver"]]
right = lambda t, x: sum(x["tests"][k] == SOL[t][k] for k in range(len(SOL[t]))) / len(SOL[t])
flr = [x for t in fail for x in FOLD[t]]
flv = [(t, x) for t in fail for x in FOLD[t] if x["ver"] and x["held"]]
print(f"full run not verified: {len(fail)} tasks; plain runs {len(plr)}, verified {len(plv)}, right {sum(right(t,x) for t,x in plv):.1f}; folds {len(flr)}, passing {len(flv)}, right {sum(x['right'] for _,x in flv):.1f}")
J["fail"] = dict(tasks=len(fail), plain=len(plr), plv=len(plv), plr=sum(right(t, x) for t, x in plv), folds=len(flr), flv=len(flv), flr=sum(x["right"] for _, x in flv))
json.dump(J, open(R + "research/paper/v8_notes/revise_llm.json", "w"), indent=1, default=float)
