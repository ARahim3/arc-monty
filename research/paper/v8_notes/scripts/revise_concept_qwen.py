"""v8 revision: own re-derivation of sampling Qwen on ConceptARC (160 tasks, 480 pairs), and what stops verified-but-wrong tasks on both LLM sets.
Does not import faloo_sampling_analyze.py. Read-only, single process. Output ../revise_concept_qwen.txt"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, glob, json, math, os, re, sys
import numpy as np
from scipy import stats as st
R = (_REPO + "/")
sys.path.insert(0, R + "research/monty_heldout")
from stats import load_rows
CDIR = R + "external/judge/conceptarc/repo/corpus"
CH, SOL = {}, {}
for f in sorted(glob.glob(CDIR + "/*/*.json")):
    d = json.load(open(f)); t = os.path.relpath(f, CDIR)[:-5]
    CH[t] = d; SOL[t] = [p["output"] for p in d["test"]]
REC = {}
errs = 0
for l in open(R + "llm/results/qwen38_faloo_sampling_concept_b32768.jsonl"):
    r = json.loads(l)
    if "error" in r:
        errs += 1; continue
    REC.setdefault((r["kind"], r["task_id"], r["fold"]), r)
print("records", collections.Counter(k[0] for k in REC), "errors", errs, "tasks", len(CH), "pairs", sum(len(v) for v in SOL.values()), "tokens", sum(r["gen_tokens"] for r in REC.values()))
def canon(d):
    return sorted(d, key=lambda p: (len(p["input"]) * len(p["input"][0]), len(p["input"]), len(p["input"][0]), json.dumps(p["input"])))
def view(r, t):
    nt = len(SOL[t])
    rs = [x for x in r.get("rounds", []) if "test_out" in x]
    if rs:
        v = [x for x in rs if x.get("verified")]; x = v[0] if v else rs[-1]
        d = dict(zip(r["query_ids"], x["test_out"])); ver = bool(v)
    else:
        d, ver = {}, False
    tests = [d.get(f"test:{k}") for k in range(nt)]
    o = dict(ver=ver, tests=tests, right=sum(tests[k] == SOL[t][k] for k in range(nt)) / nt, code=[x.get("code") or "" for x in r.get("rounds", [])])
    if r["kind"] == "fold":
        o["held"] = d.get(f"demo:{r['fold']}") == canon(CH[t]["train"])[r["fold"]]["output"]
    return o
T = sorted(CH)
FULL = {t: view(REC[("full", t, -1)], t) for t in T}
FOLD = {t: [view(REC[("fold", t, i)], t) for i in range(len(CH[t]["train"]))] for t in T}
print("folds", sum(len(v) for v in FOLD.values()))
def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * (c + h), 1)
A = lambda t: all(x["held"] for x in FOLD[t])
def B(t):
    a = [json.dumps(x["tests"]) for x in FOLD[t]]
    return len(set(a)) == 1 and all(g is not None for g in FOLD[t][0]["tests"])
C = lambda t: FULL[t]["ver"] and FULL[t]["tests"] == FOLD[t][0]["tests"]
ver = [t for t in T if FULL[t]["ver"]]
vr = sum(FULL[t]["right"] for t in ver)
ab = [t for t in T if A(t) and B(t)]; abc = [t for t in ab if C(t)]
print(f"task level: verified {len(ver)}, right {vr:.2f}, {100*vr/len(ver):.1f}%, Wilson rounded {wilson(round(vr),len(ver))}, unrounded {wilson(vr,len(ver))}; (a)+(b) {len(ab)}, right {sum(FOLD[t][0]['right'] for t in ab):.2f}; (a)+(b)+(c) {len(abc)}, right {sum(FOLD[t][0]['right'] for t in abc):.2f}, Wilson {wilson(sum(FOLD[t][0]['right'] for t in abc),len(abc))}, coverage {100*len(abc)/160:.1f}%")
W_ = [t for t in ver if FULL[t]["right"] < 1]; RR = [t for t in ver if FULL[t]["right"] == 1]
print(f"verified not fully right {len(W_)}; kept {len([t for t in abc if t in W_])}; fully right {len(RR)}; rejected {len([t for t in RR if t not in abc])}; random avoid p {math.comb(len(ver)-len(W_),len(abc))/math.comb(len(ver),len(abc)):.3g}")
sa = [t for t in W_ if not A(t)]; sb = [t for t in W_ if A(t) and not B(t)]; sc = [t for t in W_ if A(t) and B(t) and not C(t)]
print(f"stops: (a) {len(sa)}, (b) {len(sb)}, (c) {len(sc)}")
rate = {t: sum(x["held"] for x in FOLD[t]) / len(FOLD[t]) for t in ver}
print("verified at held-out rate 1.0:", sum(rate[t] == 1 for t in ver), "wrong among them:", sum(rate[t] == 1 and FULL[t]["right"] < 1 for t in ver))
def auroc(ts):
    a = [rate[t] for t in ts if FULL[t]["right"] == 1]; b = [rate[t] for t in ts if FULL[t]["right"] < 1]
    if not a or not b: return None
    return sum((x > y) + .5 * (x == y) for x in a for y in b) / (len(a) * len(b))
rng = np.random.default_rng(0); bs = []
for row in rng.integers(0, len(ver), size=(10000, len(ver))):
    v = auroc([ver[i] for i in row])
    if v is not None: bs.append(v)
ranks = st.rankdata([rate[t] for t in ver]); dr = [int(round(2 * r)) for r in ranks]
dp = [collections.Counter() for _ in range(len(RR) + 1)]; dp[0][0] = 1
for v in dr:
    for k in range(len(RR) - 1, -1, -1):
        for s, c in dp[k].items():
            dp[k + 1][s + v] += c
tot = sum(dp[len(RR)].values()); obs = sum(d for d, t in zip(dr, ver) if FULL[t]["right"] == 1)
print(f"AUROC {auroc(ver):.3f} [{np.percentile(bs,2.5):.2f}, {np.percentile(bs,97.5):.2f}]; exact one-sided p {sum(c for s,c in dp[len(RR)].items() if s>=obs)/tot:.4f}")
# ---- pairs
pa = pb = pc = 0; pcr = pbr = 0; par = pam = 0; vp = vpr = 0; one = 0; Q = {}
nin = 0
for t in T:
    a = A(t)
    for k in range(len(SOL[t])):
        fv = [x["tests"][k] for x in FOLD[t]]
        bt = all(g is not None for g in fv) and all(g == fv[0] for g in fv)
        fg = FULL[t]["tests"][k]; s = SOL[t][k]
        one += fg == s
        if FULL[t]["ver"]:
            vp += 1; vpr += fg == s
        if a and fg is not None:
            pam += 1; par += fg == s
        if a and bt:
            pb += 1; pbr += fv[0] == s
            if FULL[t]["ver"] and fg == fv[0]:
                pc += 1; pcr += fv[0] == s
                Q[f"{t}#{k}"] = fv[0] == s
print(f"pairs: FA-LOO+(c) {pcr}/{pc} = coverage {100*pc/480:.1f}%, joint {pc-pcr}/480; (a)+(b) {pbr}/{pb}; (a) with full {par}/{pam} = {100*par/pam:.1f}%; verified {vpr}/{vp} = {100*vpr/vp:.1f}%; one attempt {one}/480 = {100*one/480:.1f}%")
tasks_ans = {k.split('#')[0] for k in Q}
lo = st.beta.ppf(0.025, len(tasks_ans), 1)
print(f"tasks answered {len(tasks_ans)}, with a wrong answer {len({k.split('#')[0] for k,v in Q.items() if not v})}; Clopper-Pearson {100*lo:.1f}, 100")
mean_b = np.mean([1 / (len(CH[t]["train"]) + 1) for t in T for _ in SOL[t]]); task_b = np.mean([1 / (len(CH[t]["train"]) + 1) for t in T])
print(f"mean worst case per pair {100*mean_b:.2f}%, per task {100*task_b:.2f}%; floor at pair coverage {100*(1-mean_b/(pc/480)):.1f}%, at task coverage {100*(1-task_b/(len(abc)/160)):.1f}%")
M = load_rows(R + "research/monty_heldout/results/concept_base.jsonl")
Mo = {k: r["cfg"]["full"][str(r["m"] - 1)]["fc"] for k, r in M.items() if r["cfg"]["full"][str(r["m"] - 1)]["fc"] is not None}
both = set(Q) & set(Mo)
print(f"both answer {len(both)}; Qwen right {sum(Q[k] for k in both)}; Monty right {sum(float(Mo[k]) for k in both):.0f}; Qwen alone {len(set(Q)-set(Mo))}, right {sum(Q[k] for k in set(Q)-set(Mo))}; Monty alone {len(set(Mo)-set(Q))}, right {sum(float(Mo[k]) for k in set(Mo)-set(Q)):.0f}")
# ---- P1
vf = [(t, x) for t in T for x in FOLD[t] if x["ver"]]
hx = [x for _, x in vf if x["held"]]; mx = [x for _, x in vf if not x["held"]]
pr = lambda xs: sum(x["right"] for x in xs) / len(xs)
print(f"P1: {len(vf)} programs in {len({t for t,_ in vf})} tasks, {100*pr([x for _,x in vf]):.1f}%; predict {len(hx)}, {100*pr(hx):.1f}%; miss {len(mx)}, {100*pr(mx):.1f}%")
by = collections.defaultdict(list)
for t, x in vf: by[t].append(x)
ts = sorted(by)
CC = np.array([[sum(x["right"] for x in by[t] if x["held"]), sum(x["held"] for x in by[t]), sum(x["right"] for x in by[t] if not x["held"]), sum(not x["held"] for x in by[t])] for t in ts], float)
Wm = np.random.default_rng(0).multinomial(len(ts), np.full(len(ts), 1 / len(ts)), size=10000)
with np.errstate(invalid="ignore", divide="ignore"):
    d = (Wm @ CC[:, 0]) / (Wm @ CC[:, 1]) - (Wm @ CC[:, 2]) / (Wm @ CC[:, 3])
d = d[~np.isnan(d)]
print(f"  difference {100*(CC[:,0].sum()/CC[:,1].sum()-CC[:,2].sum()/CC[:,3].sum()):+.1f} [{100*np.percentile(d,2.5):+.1f}, {100*np.percentile(d,97.5):+.1f}]")
bt = [t for t in ts if any(x["held"] for x in by[t]) and any(not x["held"] for x in by[t])]
pd_ = np.array([np.mean([x["right"] for x in by[t] if x["held"]]) - np.mean([x["right"] for x in by[t] if not x["held"]]) for t in bt])
Wb = np.random.default_rng(0).multinomial(len(bt), np.full(len(bt), 1 / len(bt)), size=10000); bb = (Wb @ pd_) / len(bt)
print(f"  within {len(bt)} tasks with both kinds: {100*pd_.mean():+.1f} [{100*np.percentile(bb,2.5):+.1f}, {100*np.percentile(bb,97.5):+.1f}]")
# ---- P2
H = np.array([sum(x["held"] for x in FOLD[t]) for t in T], float); Te = np.array([sum(x["right"] for x in FOLD[t]) for t in T]); N = np.array([len(FOLD[t]) for t in T], float)
Aa = np.array([sum(1 - x["right"] for x in FOLD[t] if x["held"]) for t in T]); Bb = np.array([sum(x["right"] for x in FOLD[t] if not x["held"]) for t in T])
Wm = np.random.default_rng(0).multinomial(160, np.full(160, 1 / 160), size=10000); dd = (Wm @ (H - Te)) / (Wm @ N)
sg = H - Te; more, less = int((sg > 1e-9).sum()), int((sg < -1e-9).sum())
print(f"P2: folds {int(N.sum())}; held {H.sum():.0f} ({100*H.sum()/N.sum():.1f}%), test {Te.sum():.2f} ({100*Te.sum()/N.sum():.1f}%), diff {100*(H.sum()-Te.sum())/N.sum():+.1f} [{100*np.percentile(dd,2.5):+.1f}, {100*np.percentile(dd,97.5):+.1f}]; held-only {Aa.sum():.2f}, test-only {Bb.sum():.2f}; tasks {more}:{less}, sign p {st.binomtest(more,more+less,.5).pvalue:.4f}")
# ---- memorisation proxy: long literal rows in programs; test pair equal to a demo
lit = re.compile(r"\[\s*\d\s*(?:,\s*\d\s*){7,}\]")
n_prog = n_lit = 0; ex = []
for r in REC.values():
    for rd in r.get("rounds", []):
        c = rd.get("code") or ""
        if c:
            n_prog += 1
            if lit.search(c):
                n_lit += 1; ex.append((r["task_id"], r["kind"]))
print(f"programs {n_prog}; with a literal list of 8+ single digits {n_lit}; examples {ex[:5]}")
print("test pair equals a demo of its task:", sum(1 for t in T for i, p in enumerate(CH[t]["test"]) for q in CH[t]["train"] if p["input"] == q["input"]))
# ---- ARC-AGI-2 stops, same definitions
CH2 = json.load(open(R + "data/kaggle_format/agi2_eval_challenges.json")); SOL2 = json.load(open(R + "data/kaggle_format/agi2_eval_solutions.json"))
REC2 = {}
for l in open(R + "llm/results/qwen38_faloo_sampling_b32768.jsonl"):
    r = json.loads(l)
    if "error" not in r: REC2.setdefault((r["kind"], r["task_id"], r["fold"]), r)
CH, SOL = CH2, SOL2
T2 = sorted(CH2); FULL = {t: view(REC2[("full", t, -1)], t) for t in T2}; FOLD = {t: [view(REC2[("fold", t, i)], t) for i in range(len(CH2[t]["train"]))] for t in T2}
ver = [t for t in T2 if FULL[t]["ver"]]; W_ = [t for t in ver if FULL[t]["right"] < 1]
print(f"ARC-AGI-2 stops of {len(W_)}: (a) {len([t for t in W_ if not A(t)])}, (b) {len([t for t in W_ if A(t) and not B(t)])}, (c) {len([t for t in W_ if A(t) and B(t) and not C(t)])}; certified {len([t for t in T2 if A(t) and B(t) and C(t)])}")
print(f"at held-out rate 1.0 among verified: {sum(A(t) for t in ver)}, wrong {sum(A(t) and FULL[t]['right']<1 for t in ver)}")
