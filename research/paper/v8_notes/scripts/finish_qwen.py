"""Finisher pass. Independent recount of every Qwen number in paper.md (sampling 32k on ARC-AGI-2 and ConceptARC; greedy first look) from the raw JSONL.
Written from the plan in research/arc2/faloo_qwen_sampling.md; imports neither faloo_sampling_analyze.py nor revise_*.py. Parsed as data, single process.
Output: ../finish_qwen.txt"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, glob, json, math, os, zlib
import numpy as np
from scipy import stats as st
R = (_REPO + "/")
B = 10000
def pct(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))
def wts(T):
    return np.random.default_rng(0).multinomial(T, np.full(T, 1 / T), size=B)
def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * (c + h), 1)
def F(x, ci):
    return f"{100*x:+.1f} [{100*ci[0]:+.1f}, {100*ci[1]:+.1f}]"

def agi2():
    ch = json.load(open(R + "data/kaggle_format/agi2_eval_challenges.json")); so = json.load(open(R + "data/kaggle_format/agi2_eval_solutions.json"))
    return {t: dict(train=ch[t]["train"], sol=so[t]) for t in ch}
def concept():
    base = R + "external/judge/conceptarc/repo/corpus/"; d = {}
    for f in glob.glob(base + "*/*.json"):
        x = json.load(open(f)); d[os.path.relpath(f, base)[:-5]] = dict(train=x["train"], sol=[p["output"] for p in x["test"]])
    return d
def load(path):
    out = {}; dup = err = 0
    for l in open(path):
        r = json.loads(l)
        if "error" in r:
            err += 1; continue
        k = (r["kind"], r["task_id"], r["fold"])
        if k in out:
            dup += 1
            if r.get("started_at", 1e18) < out[k].get("started_at", 1e18):
                out[k] = r
        else:
            out[k] = r
    return out, dup, err

class Run:
    """One logged run. Output = first verified round, else the last round that ran a program, on every query."""
    def __init__(self, rec, task):
        self.kind, self.fold, self.tokens = rec["kind"], rec["fold"], rec["gen_tokens"]
        rounds = [x for x in rec.get("rounds", []) if x.get("test_out") is not None]
        good = [x for x in rounds if x.get("verified")]
        pick = good[0] if good else (rounds[-1] if rounds else None)
        self.ver = bool(good)
        ans = dict(zip(rec["query_ids"], pick["test_out"])) if pick else {}
        self.tests = [ans.get(f"test:{i}") for i in range(len(task["sol"]))]
        self.rights = [a == b for a, b in zip(self.tests, task["sol"])]
        self.right = sum(self.rights) / len(self.rights)
        self.held = None
        if rec["kind"] == "fold":
            order = sorted(task["train"], key=lambda p: (len(p["input"]) * len(p["input"][0]), len(p["input"]), len(p["input"][0]), json.dumps(p["input"])))
            self.held = ans.get(f"demo:{rec['fold']}") == order[rec["fold"]]["output"]
            self.vh = self.ver and self.held
        # cross-check against the harness's own 'correct' field where present
        self.chk = None
        if pick is not None and "correct" in pick and pick["correct"] is not None:
            self.chk = dict(zip(rec["query_ids"], pick["correct"]))

def within(rows):
    g = collections.defaultdict(lambda: [[], []])
    for c, r, p in rows:
        g[c][0 if p else 1].append(r)
    both = sorted(c for c, v in g.items() if v[0] and v[1])
    d = np.array([np.mean(g[c][0]) - np.mean(g[c][1]) for c in both])
    b = (wts(len(d)) @ d) / len(d)
    pos, neg = int((d > 1e-12).sum()), int((d < -1e-12).sum())
    return f"{F(d.mean(), pct(b))} over {len(both)} tasks; {pos}:{neg} (ties {len(d)-pos-neg}), sign p {st.binomtest(pos, pos+neg, .5).pvalue:.4f}"

def analyse(name, D, recs, plain=None):
    T = sorted(D); Tn = len(T)
    full = {t: Run(recs[("full", t, -1)], D[t]) for t in T}
    folds = {t: [Run(recs[("fold", t, i)], D[t]) for i in range(len(D[t]["train"]))] for t in T}
    print(f"\n=== {name}: tasks {Tn}, pairs {sum(len(D[t]['sol']) for t in T)}, folds {sum(map(len, folds.values()))}, mean 1/(n+1) {100*np.mean([1/(len(D[t]['train'])+1) for t in T]):.2f}%")
    badchk = sum(1 for t in T for r in [full[t]] + folds[t] if r.chk for i in range(len(D[t]["sol"])) if f"test:{i}" in r.chk and bool(r.chk[f"test:{i}"]) != r.rights[i])
    print("  harness 'correct' field disagrees with my comparison on", badchk, "outputs")
    A = {t: all(f.held for f in folds[t]) for t in T}
    def agree(t):
        a = [json.dumps(f.tests) for f in folds[t]]
        return len(set(a)) == 1 and all(g is not None for g in folds[t][0].tests)
    Bt = {t: agree(t) for t in T}
    C = {t: Bt[t] and full[t].ver and full[t].tests == folds[t][0].tests for t in T}
    ver = [t for t in T if full[t].ver]
    vr = sum(full[t].right for t in ver)
    ab = [t for t in T if A[t] and Bt[t]]; abc = [t for t in ab if C[t]]
    print(f"  verified {len(ver)}: right {vr:.2f} = {100*vr/len(ver):.1f}%, Wilson on rounded count {wilson(round(vr), len(ver))}; (a)+(b) {len(ab)}, right {sum(folds[t][0].right for t in ab):.2f}; (a)+(b)+(c) {len(abc)}, right {sum(folds[t][0].right for t in abc):.2f}, Wilson {wilson(sum(folds[t][0].right for t in abc), len(abc))}, coverage {100*len(abc)/Tn:.1f}%")
    wrong = [t for t in ver if full[t].right < 1]; rightt = [t for t in ver if full[t].right == 1]
    print(f"  verified not fully right {len(wrong)}; kept {sum(t in abc for t in wrong)}; fully right {len(rightt)}, rejected {sum(t not in abc for t in rightt)}; random subset avoids all wrong p = {math.comb(len(ver)-len(wrong), len(abc))/math.comb(len(ver), len(abc)):.3g}")
    print(f"  stops among verified-but-wrong: (a) {sum(not A[t] for t in wrong)}, (b) {sum(A[t] and not Bt[t] for t in wrong)}, (c) {sum(A[t] and Bt[t] and not C[t] for t in wrong)}")
    rate = {t: np.mean([f.held for f in folds[t]]) for t in ver}
    def auc(ts):
        a = [rate[t] for t in ts if full[t].right == 1]; b = [rate[t] for t in ts if full[t].right < 1]
        if not a or not b:
            return float("nan")
        return np.mean([[(x > y) + .5 * (x == y) for y in b] for x in a])
    rng = np.random.default_rng(0)
    bs = [auc([ver[i] for i in row]) for row in rng.integers(0, len(ver), size=(B, len(ver)))]
    # exact one-sided permutation p with midranks
    rk = st.rankdata([rate[t] for t in ver]); dbl = [int(round(2 * x)) for x in rk]
    ways = [collections.Counter() for _ in range(len(rightt) + 1)]; ways[0][0] = 1
    for v in dbl:
        for k in range(len(rightt) - 1, -1, -1):
            for s, c in ways[k].items():
                ways[k + 1][s + v] += c
    obs = sum(v for v, t in zip(dbl, ver) if full[t].right == 1); tot = sum(ways[len(rightt)].values())
    print(f"  AUROC {auc(ver):.3f} [{pct(bs)[0]:.2f}, {pct(bs)[1]:.2f}], exact one-sided p {sum(c for s, c in ways[len(rightt)].items() if s >= obs)/tot:.4f}; verified at rate 1.0: {sum(rate[t]==1 for t in ver)}, wrong {sum(rate[t]==1 and full[t].right<1 for t in ver)}")
    # Table 5
    rows = [(t, f.right, f.held) for t in T for f in folds[t] if f.ver]
    pr = [r for _, r, h in rows if h]; ms = [r for _, r, h in rows if not h]
    arr = {t: [0., 0., 0., 0.] for t in T}
    for t, r, h in rows:
        arr[t][0 if h else 2] += r; arr[t][1 if h else 3] += 1
    Q = np.array([arr[t] for t in T]); W = wts(Tn)
    with np.errstate(invalid="ignore", divide="ignore"):
        d = (W @ Q[:, 0]) / (W @ Q[:, 1]) - (W @ Q[:, 2]) / (W @ Q[:, 3])
    print(f"  Table 5: verified fold programs {len(rows)} in {len({t for t,_,_ in rows})} tasks; predict {len(pr)}: {100*np.mean(pr):.1f}%; miss {len(ms)}: {100*np.mean(ms):.1f}%; difference {F(np.mean(pr)-np.mean(ms), pct(d))}")
    print(f"  WITHIN task, verified fold programs: {within(rows)}")
    # Table 4
    H = np.array([sum(f.held for f in folds[t]) for t in T], float); Te = np.array([sum(f.right for f in folds[t]) for t in T]); N = np.array([len(folds[t]) for t in T], float)
    ho = sum((1 - f.right) for t in T for f in folds[t] if f.held); to = sum(f.right for t in T for f in folds[t] if not f.held)
    d = (W @ (H - Te)) / (W @ N); s = H - Te; m, l = int((s > 1e-9).sum()), int((s < -1e-9).sum())
    print(f"  Table 4: folds {N.sum():.0f}; held {H.sum():.0f} = {100*H.sum()/N.sum():.1f}%; test {Te.sum():.2f} = {100*Te.sum()/N.sum():.1f}%; diff {F((H.sum()-Te.sum())/N.sum(), pct(d))}; held only {ho:.2f}, test only {to:.2f}; tasks {m}:{l}, sign p {st.binomtest(m, m+l, .5).pvalue:.4f}")
    # pair level
    c = collections.Counter(); ansp = {}
    for t in T:
        for k in range(len(D[t]["sol"])):
            y = D[t]["sol"][k]; fv = [f.tests[k] for f in folds[t]]; fg = full[t].tests[k]
            c["one"] += fg == y; c["pairs"] += 1
            if full[t].ver:
                c["fit"] += 1; c["fit_r"] += fg == y
            if A[t] and fg is not None:
                c["a"] += 1; c["a_r"] += fg == y
            if A[t] and all(g is not None for g in fv) and all(g == fv[0] for g in fv):
                c["ab"] += 1; c["ab_r"] += fv[0] == y
                if full[t].ver and fg == fv[0]:
                    c["fc"] += 1; c["fc_r"] += fv[0] == y; ansp[f"{t}#{k}"] = fv[0] == y
    ta = {k.split("#")[0] for k in ansp}
    print(f"  pairs {c['pairs']}: one attempt {c['one']} = {100*c['one']/c['pairs']:.1f}%; fit {c['fit_r']}/{c['fit']} = {100*c['fit_r']/c['fit']:.1f}%; (a) {c['a_r']}/{c['a']} = {100*c['a_r']/max(c['a'],1):.1f}%; (a)+(b) {c['ab_r']}/{c['ab']}; FA-LOO {c['fc_r']}/{c['fc']}, coverage {100*c['fc']/c['pairs']:.1f}%, joint {c['fc']-c['fc_r']}; tasks {len(ta)}, CP lower {100*st.beta.ppf(.025, len(ta), 1):.1f}")
    mb = np.mean([1 / (len(D[t]["train"]) + 1) for t in T for _ in D[t]["sol"]])
    print(f"  mean worst case per pair {100*mb:.2f}%; floor {100*(1 - mb/(c['fc']/c['pairs'])):.1f}%")
    if name == "ConceptARC":
        mo = {}
        for l_ in open(R + "research/monty_heldout/results/concept_base.jsonl"):
            x = json.loads(l_); o = x["cfg"]["full"][str(x["m"] - 1)]
            if o["fc"] is not None:
                mo[x["task"]] = float(o["fc"])
        bo = set(mo) & set(ansp)
        print(f"  both answer {len(bo)}: Qwen right {sum(ansp[k] for k in bo)}, Monty right {sum(mo[k] for k in bo):.0f}")
    if plain is None:
        return full, folds
    return full, folds

D2 = agi2(); DC = concept()
r2, d2, e2 = load(R + "llm/results/qwen38_faloo_sampling_b32768.jsonl"); print("ARC-AGI-2 records", collections.Counter(k[0] for k in r2), "duplicates", d2, "errors", e2)
rp, dp, ep = load(R + "llm/results/qwen38_faloo_sampling_plain_b32768.jsonl"); print("plain records", collections.Counter(k[0] for k in rp), "duplicates", dp, "errors", ep)
rc, dc, ec = load(R + "llm/results/qwen38_faloo_sampling_concept_b32768.jsonl"); print("ConceptARC records", collections.Counter(k[0] for k in rc), "duplicates", dc, "errors", ec)
full2, folds2 = analyse("ARC-AGI-2", D2, r2)
analyse("ConceptARC", DC, rc)
rg, dg, eg = load(R + "llm/results/qwen38_faloo_greedy_b16384.jsonl"); print("\ngreedy records", collections.Counter(k[0] for k in rg), "duplicates", dg, "errors", eg)
analyse("ARC-AGI-2 greedy 16k", D2, rg)

# ---------- stage 1b
T = sorted(D2)
plain = {t: [full2[t]] + [Run(rp[("plain", t, k)], D2[t]) for k in (1, 2, 3)] for t in T}
print("\n=== P3, per run, yield, cost, replay (ARC-AGI-2)")
def pass2(runs, t):
    """runs: (tier, tests) in run order; lower tier first, stable; first two distinct non-null grids per output."""
    s = 0
    for k, y in enumerate(D2[t]["sol"]):
        seen = []
        for _, tests in sorted(runs, key=lambda x: x[0]):
            g = tests[k]
            if g is not None and g not in seen:
                seen.append(g)
            if len(seen) == 2:
                break
        s += y in seen
    return s / len(D2[t]["sol"])
fo_ord = {t: sorted(range(len(D2[t]["train"])), key=lambda i: zlib.crc32(f"20261101|p3|{t}|{i}".encode())) for t in T}
W = wts(120)
for cap in (2, 3, 4):
    sp, sf, s3, tp, tf = [], [], [], 0, 0
    for t in T:
        k = min(len(D2[t]["train"]) + 1, cap)
        P = plain[t][:k]; Fo = [full2[t]] + [folds2[t][i] for i in fo_ord[t]]; Fo = Fo[:k]
        sp.append(pass2([(0 if x.ver else 1, x.tests) for x in P], t))
        sf.append(pass2([((0 if x.vh else 1) if x.kind == "fold" else (0 if x.ver else 1), x.tests) for x in Fo], t))
        s3.append(pass2([((0 if x.vh else 1 if x.ver else 2) if x.kind == "fold" else (0 if x.ver else 2), x.tests) for x in Fo], t))
        tp += sum(x.tokens for x in P); tf += sum(x.tokens for x in Fo)
    sp, sf, s3 = map(np.array, (sp, sf, s3)); dv = sf - sp
    print(f"  cap {cap}: plain {sp.sum():.2f}, fold {sf.sum():.2f}, fold minus plain {dv.sum():+.2f} [{pct(W @ dv)[0]:+.1f}, {pct(W @ dv)[1]:+.1f}]; three tiers {s3.sum():.2f}; tokens {tp/1e6:.1f}M / {tf/1e6:.1f}M")
Q = np.array([[sum(x.right for x in plain[t] if x.ver), sum(x.ver for x in plain[t]), sum(x.right for x in folds2[t] if x.vh), sum(x.vh for x in folds2[t])] for t in T], float)
with np.errstate(invalid="ignore", divide="ignore"):
    a, b = (W @ Q[:, 0]) / (W @ Q[:, 1]), (W @ Q[:, 2]) / (W @ Q[:, 3])
print(f"  per run: plain verified {Q[:,0].sum():.2f}/{Q[:,1].sum():.0f} = {100*Q[:,0].sum()/Q[:,1].sum():.1f}% [{100*pct(a)[0]:.1f}, {100*pct(a)[1]:.1f}]; fold verified and held {Q[:,2].sum():.2f}/{Q[:,3].sum():.0f} = {100*Q[:,2].sum()/Q[:,3].sum():.1f}% [{100*pct(b)[0]:.1f}, {100*pct(b)[1]:.1f}]; difference {F(Q[:,2].sum()/Q[:,3].sum()-Q[:,0].sum()/Q[:,1].sum(), pct(b-a))}")
hard = [t for t in T if not full2[t].ver]
Y = np.array([[3, sum(x.ver for x in plain[t][1:]), sum(x.right for x in plain[t][1:] if x.ver), len(folds2[t]), sum(x.vh for x in folds2[t]), sum(x.right for x in folds2[t] if x.vh)] for t in hard], float)
Wh = wts(len(hard)); dy = (Wh @ Y[:, 5]) / (Wh @ Y[:, 3]) - (Wh @ Y[:, 2]) / (Wh @ Y[:, 0])
print(f"  first sample unverified {len(hard)} tasks: plain runs {Y[:,0].sum():.0f}, verified {Y[:,1].sum():.0f}, right {Y[:,2].sum():.1f}; folds {Y[:,3].sum():.0f}, pass {Y[:,4].sum():.0f}, right {Y[:,5].sum():.1f}; per run {Y[:,5].sum()/Y[:,3].sum()-Y[:,2].sum()/Y[:,0].sum():+.3f} [{pct(dy)[0]:+.3f}, {pct(dy)[1]:+.3f}]")
ver = [t for t in T if full2[t].ver]
tf_all = sum(x.tokens for t in T for x in folds2[t]); tfull = sum(full2[t].tokens for t in T); tfv = sum(x.tokens for t in ver for x in folds2[t]); nfv = sum(len(folds2[t]) for t in ver)
ee = ec = 0
for t in ver:
    for x in folds2[t]:
        ee += x.tokens; ec += 1
        if not x.held:
            break
print(f"  cost: full {tfull/1e6:.2f}M, folds {tf_all/1e6:.2f}M: {(tfull+tf_all)/tfull:.2f}x; verified tasks {len(ver)} = v {len(ver)/120:.3f}, folds {nfv}: {(tfull+tfv)/tfull:.2f}x; early exit {ec} folds: {(tfull+ee)/tfull:.2f}x; 1+vn with mean n on verified {1+len(ver)/120*np.mean([len(D2[t]['train']) for t in ver]):.2f}")
# replay
order = sorted(T, key=lambda t: zlib.crc32(f"20261101|order|{t}".encode()))
def cert_after_all_folds(t):
    fs = folds2[t]; ok = all(f.held for f in fs); a = [json.dumps(f.tests) for f in fs]
    return ok and len(set(a)) == 1 and all(g is not None for g in fs[0].tests) and full2[t].ver and full2[t].tests == fs[0].tests
def replay(pol):
    seqs = {}
    for t in order:
        if pol in "ii":
            seqs[t] = [(x, x.ver, False) for x in plain[t]]
        else:
            fs = [folds2[t][i] for i in fo_ord[t]]
            seqs[t] = [(full2[t], full2[t].ver, False)] + [(f, f.vh, False) for f in fs[:-1]] + [(fs[-1], fs[-1].vh, cert_after_all_folds(t))] + [(x, x.ver, False) for x in plain[t][1:]]
    pos = dict.fromkeys(order, 0); stopped = set(); spent = 0; grid = [32, 64, 96, 128, 160, 192, 224, 256, 288, 320]; gi = 0; out = {}
    def score():
        tot = 0
        for t in order:
            used = seqs[t][:pos[t]]
            if used:
                runs = [(0 if u[1] else 1, u[0].tests) for u in used]
                c = [u[0].tests for u in used if u[2]]
                if c:
                    runs.insert(0, (-1, c[0]))
                tot += pass2(runs, t)
        return tot
    active = True
    while active and gi < len(grid):
        active = False
        for t in order:
            if t in stopped or pos[t] >= len(seqs[t]):
                continue
            u = seqs[t][pos[t]]; pos[t] += 1; spent += u[0].tokens; active = True
            if (pol == "ii" and u[1]) or (pol == "iii" and u[2]):
                stopped.add(t)
            while gi < len(grid) and spent >= grid[gi] * 120000:
                out[grid[gi]] = round(score(), 2); gi += 1
    return out, round(score(), 2), round(spent / 120 / 1000), len(stopped)
for p in ("i", "ii", "iii"):
    print("  replay", p, replay(p))
