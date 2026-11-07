"""Finisher pass. Monty-ARC numbers that sit in Tables 4, 5, 6, C6, C7, recounted from research/monty_heldout/results/*_base.jsonl and the sets on disk,
without importing stats.py or hl_common. Also: can Monty-ARC have the within-task control? Fold-level split and within-task difference, and the evidence measure inside tasks.
Output: ../finish_monty.txt"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, glob, hashlib, json, os
import numpy as np
from scipy import stats as st
R = (_REPO + "/")
HL = R + "research/monty_heldout/results/"
B = 10000
def pct(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))
def wts(T):
    return np.random.default_rng(0).multinomial(T, np.full(T, 1 / T), size=B)
def h(g):
    a = np.ascontiguousarray(np.array(g, dtype=np.int8))
    return hashlib.md5(str(a.shape).encode() + a.tobytes()).hexdigest()[:12]
SETS = dict(concept="external/judge/conceptarc/repo/corpus", mini="external/heldout/mini-arc/data/MiniARC", oned="external/heldout/1d-arc/dataset", minimal="external/judge/conceptarc/repo/MinimalTasks")
def cluster(tag, key):
    return key.split("/")[0] if tag == "oned" else key.split("#")[0]
def task(key):
    return key.split("#")[0]
def within(rows):
    g = collections.defaultdict(lambda: [[], []])
    for c, right, pred in rows:
        g[c][0 if pred else 1].append(right)
    both = sorted(c for c, v in g.items() if v[0] and v[1])
    d = np.array([np.mean(g[c][0]) - np.mean(g[c][1]) for c in both], float)
    if not len(d):
        return dict(clusters=0)
    b = (wts(len(d)) @ d) / len(d)
    pos, neg = int((d > 1e-12).sum()), int((d < -1e-12).sum())
    return dict(clusters=len(both), diff=round(100 * float(d.mean()), 1), ci=[round(100 * v, 1) for v in pct(b)], pos=pos, neg=neg, zero=len(d) - pos - neg, n_pred=sum(len(g[c][0]) for c in both), n_miss=sum(len(g[c][1]) for c in both))
for tag, path in SETS.items():
    rows = [json.loads(l) for l in open(HL + f"{tag}_base.jsonl")]
    # truth in the same demonstration order as the pool: demos in file order, then the test pair
    disk = {}
    for f in glob.glob(R + path + "/**/*.json", recursive=True):
        disk[os.path.relpath(f, R + path)[:-5]] = json.load(open(f))
    cl = sorted({cluster(tag, r["task"]) for r in rows}); ix = {c: i for i, c in enumerate(cl)}; T = len(cl); W = wts(T)
    top = np.zeros((T, 2)); hi = np.zeros((T, 2)); lo = np.zeros((T, 2)); bk = collections.Counter()
    fit = np.zeros((T, 2)); v5 = np.zeros((T, 2)); fc = np.zeros((T, 2)); fa = np.zeros((T, 2)); a_ = np.zeros((T, 2))
    Hs = np.zeros((T, 4)); EX = np.zeros((T, 5)); frows = []; erows = []; frows_type = []
    p2 = 0
    for r in rows:
        key = r["task"]; m = r["m"]; t, q = key.rsplit("#", 1); d = disk[t]; i = ix[cluster(tag, key)]
        pool = [(p["input"], p["output"]) for p in d["train"]] + [(d["test"][int(q)]["input"], d["test"][int(q)]["output"])]
        H = [h(y) for _, y in pool]
        o = r["cfg"]["full"][str(m - 1)]
        p2 += o["p2"]
        if o["top_ok"] is not None:
            top[i] += (float(o["top_ok"]), 1)
            e = o["top_ev"]; ok = float(o["top_ok"])
            (hi if e >= .99 else lo)[i] += (ok, 1)
            erows.append((task(key), ok, e >= .99))
            bk[(">=.99" if e >= .99 else "[.5,.99)" if e >= .5 else "(0,.5)" if e > 0 else "0", ok)] += 1
        for name, arr in (("fit", fit), ("v5", v5), ("fc", fc), ("fa", fa), ("a", a_)):
            if o[name] is not None:
                arr[i] += (float(o[name]), 1)
        for b in range(m - 1):
            pr = o["fold_h"][str(b)]
            hr, tr = (0., 0.) if pr is None else (float(pr[0] == H[b]), float(pr[1] == H[m - 1]))
            EX[i] += (hr, tr, hr * (1 - tr), (1 - hr) * tr, 1)
            if pr is not None:
                Hs[i] += (tr * hr, hr, tr * (1 - hr), 1 - hr)
                frows.append((task(key), tr, bool(hr)))
    def pr_(x):
        with np.errstate(invalid="ignore", divide="ignore"):
            c = pct((W @ x[:, 0]) / (W @ x[:, 1]))
        return f"{x[:,0].sum():.0f}/{x[:,1].sum():.0f} = {100*x[:,0].sum()/max(x[:,1].sum(),1):.1f}% [{100*c[0]:.1f}, {100*c[1]:.1f}]"
    def df(x, y):
        with np.errstate(invalid="ignore", divide="ignore"):
            c = pct((W @ x[:, 0]) / (W @ x[:, 1]) - (W @ y[:, 0]) / (W @ y[:, 1]))
        return f"{100*(x[:,0].sum()/x[:,1].sum()-y[:,0].sum()/y[:,1].sum()):+.1f} [{100*c[0]:+.1f}, {100*c[1]:+.1f}]"
    print(f"\n=== {tag}: items {len(rows)}, clusters {T}, pass@2 {p2:.0f}")
    print(f"  top {pr_(top)}; fit {pr_(fit)}; v5 {pr_(v5)}; plain (a) {pr_(a_)}; (a)+(b) {pr_(fa)}; FA-LOO {pr_(fc)}; coverage {100*fc[:,1].sum()/len(rows):.1f}%; joint {fc[:,1].sum()-fc[:,0].sum():.0f}/{len(rows)}")
    print(f"  FA-LOO minus fit {df(fc, fit)}; v5 minus fit {df(v5, fit)}; FA-LOO minus v5 {df(fc, v5)}")
    print(f"  Table 5 as captioned: evidence >= .99 {pr_(hi)}; below {pr_(lo)}; difference {df(hi, lo)}; buckets { {k: v for k, v in sorted(bk.items())} }")
    d = (W @ (EX[:, 0] - EX[:, 1])) / (W @ EX[:, 4]); sg = EX[:, 2] - EX[:, 3]
    print(f"  Table 4: folds {EX[:,4].sum():.0f}; held {100*EX[:,0].sum()/EX[:,4].sum():.1f}% test {100*EX[:,1].sum()/EX[:,4].sum():.1f}%; diff {100*(EX[:,0].sum()-EX[:,1].sum())/EX[:,4].sum():+.1f} [{100*pct(d)[0]:+.1f}, {100*pct(d)[1]:+.1f}]; held only {EX[:,2].sum():.0f} test only {EX[:,3].sum():.0f}; clusters {(sg>0).sum()}:{(sg<0).sum()}")
    if Hs[:, 1].sum() and Hs[:, 3].sum():
        with np.errstate(invalid="ignore", divide="ignore"):
            c = pct((W @ Hs[:, 0]) / (W @ Hs[:, 1]) - (W @ Hs[:, 2]) / (W @ Hs[:, 3]))
        print(f"  FOLD-LEVEL split (same measure as the other learners; fold models that give a test answer): predict {Hs[:,0].sum():.0f}/{Hs[:,1].sum():.0f} = {100*Hs[:,0].sum()/Hs[:,1].sum():.1f}%; miss {Hs[:,2].sum():.0f}/{Hs[:,3].sum():.0f} = {100*Hs[:,2].sum()/Hs[:,3].sum():.1f}%; difference {100*(Hs[:,0].sum()/Hs[:,1].sum()-Hs[:,2].sum()/Hs[:,3].sum()):+.1f} [{100*c[0]:+.1f}, {100*c[1]:+.1f}]")
    wf_ = within(frows)
    print(f"  FOLD-LEVEL within task: {wf_}")
    if wf_.get("clusters"):
        print(f"  FOLD-LEVEL within task, formatted: {wf_['diff']:+.1f} [{wf_['ci'][0]:+.1f}, {wf_['ci'][1]:+.1f}], {wf_['clusters']} tasks")
    print(f"  EVIDENCE inside tasks (top answer >= .99 vs below, tasks with both): {within(erows)}")
    mults = collections.Counter(collections.Counter(task(r['task']) for r in rows).values())
    print(f"  test pairs per task: {dict(mults)}")

# 1D-ARC: the fold-level within-task control with the bootstrap over types, as for the 2020 program
print("\n=== oned: fold-level within-task, resampling types")
rows = [json.loads(l) for l in open(HL + "oned_base.jsonl")]
disk = {os.path.relpath(f, R + SETS["oned"])[:-5]: json.load(open(f)) for f in glob.glob(R + SETS["oned"] + "/**/*.json", recursive=True)}
g = collections.defaultdict(lambda: [[], []]); ty = {}
for r in rows:
    key = r["task"]; m = r["m"]; t, q = key.rsplit("#", 1); d = disk[t]
    pool = [p["output"] for p in d["train"]] + [d["test"][int(q)]["output"]]
    H = [h(y) for y in pool]; o = r["cfg"]["full"][str(m - 1)]
    for b in range(m - 1):
        pr = o["fold_h"][str(b)]
        if pr is not None:
            g[key][0 if pr[0] == H[b] else 1].append(float(pr[1] == H[m - 1])); ty[key] = key.split("/")[0]
per = collections.defaultdict(list)
for c, v in g.items():
    if v[0] and v[1]:
        per[ty[c]].append(np.mean(v[0]) - np.mean(v[1]))
types = sorted(per); s = np.array([sum(per[t]) for t in types]); n = np.array([len(per[t]) for t in types], float); W = wts(len(types))
tk_ = collections.defaultdict(float)
for r in rows:
    key = r["task"]; m = r["m"]; t, q = key.rsplit("#", 1); d = disk[t]
    pool = [p["output"] for p in d["train"]] + [d["test"][int(q)]["output"]]
    H = [h(y) for y in pool]; o = r["cfg"]["full"][str(m - 1)]
    for b in range(m - 1):
        pr = o["fold_h"][str(b)]
        if pr is not None:
            tk_[key] += float(pr[0] == H[b]) - float(pr[1] == H[m - 1])
m_, l_ = sum(v > 0 for v in tk_.values()), sum(v < 0 for v in tk_.values())
print(f"Table 4 by task, descriptive: tasks {m_}:{l_}, sign p {st.binomtest(m_, m_ + l_, .5).pvalue:.2e}")
print(f"tasks {int(n.sum())} in {len(types)} types: {100*s.sum()/n.sum():+.1f} [{100*pct((W @ s) / (W @ n))[0]:+.1f}, {100*pct((W @ s) / (W @ n))[1]:+.1f}]; { {t: len(per[t]) for t in types} }")
