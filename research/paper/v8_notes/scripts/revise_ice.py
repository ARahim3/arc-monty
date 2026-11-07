"""v8 revision: own re-derivation of FA-LOO on the 2020 first-place program from raw run lines. Does not import analyse.py and runs no third-party code;
run lines are parsed as data. Output: ../revise_ice.txt, ../revise_ice.json"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import collections, glob, json, os, sys
ROOT = (_REPO + "/")
HL = ROOT + "research/monty_heldout"
sys.path.insert(0, HL)
import numpy as np
from scipy import stats as st
from stats import load_rows, _pct
from xlsx_read import rows as xlrows
ICE = ROOT + "research/icecuber_faloo/"
CFG = {3, 23, 33, 4}
by = collections.defaultdict(dict)
for p in sorted(glob.glob(ICE + "raw/runs_*.jsonl")):
    for l in open(p, errors="replace"):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if isinstance(r.get("rid"), str) and int(r.get("cfg", -1)) in CFG:
            by[r["rid"]].setdefault(int(r["cfg"]), r)
print("rids", len(by), "complete", sum(len(v) == 4 for v in by.values()))
def s_grid(g):
    return "|" + "|".join("".join(str(c) for c in row) for row in g) + "|"
def merged(rid):
    per = by.get(rid)
    if per is None or len(per) < 4:
        return None
    c = []
    for r in per.values():
        if r.get("status") != "ok":
            continue
        for ln in r.get("lines", []):
            try:
                img, sc = ln[0], float(ln[1])
            except Exception:
                continue
            if sc >= 0 and img.startswith("|") and img.endswith("|"):
                c.append((sc, img))
    c.sort(reverse=True)
    out, sc = [], []
    for a, b in c:
        if b not in out:
            out.append(b); sc.append(a)
        if len(out) == 3:
            break
    nd = next(iter(per.values())).get("nd")
    return dict(ans=out, sc=sc, nd=nd, status=[r.get("status") for r in per.values()])
M = {rid: merged(rid) for rid in by}
top = lambda rid: (M[rid]["ans"][0] if rid and M.get(rid) and M[rid]["ans"] else None)
J = {}
def report(tag, name, monty=None):
    items = [json.loads(l) for l in open(ICE + f"export/items_{tag}.jsonl")]
    cl = sorted({it["cluster"] for it in items}); ix = {c: i for i, c in enumerate(cl)}
    T = len(cl)
    W = np.random.default_rng(0).multinomial(T, np.full(T, 1 / T), size=10000)
    U, Uf, FC, A_, FA = [np.zeros((T, 2)) for _ in range(5)]
    pass_ = [0, 0, 0]
    Hs = np.zeros((T, 4)); EX = np.zeros((T, 5))
    passa = bfail = bright = bwrong = cfail = 0
    nofit = has = 0
    mean_b = []
    ans_fc = {}
    tasks_ans = collections.defaultdict(list)
    fold_fit = []
    for it in items:
        i = ix[it["cluster"]]; truth = s_grid(it["truth"]); n = it["n"]; mean_b.append(1 / (n + 1))
        f = M.get(it["full"])
        a = f["ans"] if f else []
        y = a[0] if a else None
        for k in (1, 2, 3):
            pass_[k - 1] += truth in a[:k]
        if y is not None:
            has += 1
            U[i] += [y == truth, 1]
            fits = f["sc"][0] > f["nd"] - 0.499
            nofit += not fits
            if fits:
                Uf[i] += [y == truth, 1]
        H, Tt = [], []
        for x in it["folds"]:
            h = top(x["held_rid"]); t = top(x["test_rid"])
            H.append(h); Tt.append(t)
            hr = h is not None and h == s_grid(x["held_truth"]); tr = t is not None and t == truth
            EX[i] += [hr, tr, hr * (1 - tr), (1 - hr) * tr, 1]
            if t is not None:
                if hr:
                    Hs[i, 0] += tr; Hs[i, 1] += 1
                else:
                    Hs[i, 2] += tr; Hs[i, 3] += 1
        a_ok = n >= 2 and all(h is not None and h == s_grid(x["held_truth"]) for h, x in zip(H, it["folds"]))
        agree = n >= 2 and all(t is not None for t in Tt) and len(set(Tt)) == 1
        if a_ok:
            passa += 1
            if y is not None:
                A_[i] += [y == truth, 1]
            if not agree:
                bfail += 1
                bright += y == truth; bwrong += y != truth
        if a_ok and agree:
            FA[i] += [Tt[0] == truth, 1]
            if y == Tt[0]:
                FC[i] += [Tt[0] == truth, 1]
                ans_fc[it["key"]] = Tt[0] == truth
                tasks_ans[it["task"]].append(Tt[0] == truth)
            else:
                cfail += 1
    N = len(items); mb = float(np.mean(mean_b))
    def pr(x):
        if not x[:, 1].sum():
            return "0/0"
        with np.errstate(invalid="ignore", divide="ignore"):
            b = (W @ x[:, 0]) / (W @ x[:, 1])
        ci = _pct(b)
        return f"{x[:,0].sum():.0f}/{x[:,1].sum():.0f} = {100*x[:,0].sum()/x[:,1].sum():.1f}% [{100*ci[0]:.1f}, {100*ci[1]:.1f}]"
    def df(x, y):
        if not x[:, 1].sum() or not y[:, 1].sum():
            return "n/a"
        with np.errstate(invalid="ignore", divide="ignore"):
            b = (W @ x[:, 0]) / (W @ x[:, 1]) - (W @ y[:, 0]) / (W @ y[:, 1])
        ci = _pct(b)
        return f"{100*(x[:,0].sum()/x[:,1].sum()-y[:,0].sum()/y[:,1].sum()):+.1f} [{100*ci[0]:+.1f}, {100*ci[1]:+.1f}]"
    print(f"\n=== {name}: items {N}, clusters {T}, has {has}, mean 1/(n+1) {100*mb:.1f}%")
    print(f"usual {pr(U)}; top fits {pr(Uf)}; (a) {pr(A_)}; (a)+(b) {pr(FA)}; FA-LOO+(c) {pr(FC)}; coverage {100*FC[:,1].sum()/N:.1f}%")
    print(f"pass@1,2,3 {pass_}; FC minus usual {df(FC,U)}; FC minus top-fits {df(FC,Uf)}; FC minus (a) {df(FC,A_)}")
    print(f"clusters answered {int((FC[:,1]>0).sum())}, with wrong {int(((FC[:,1]-FC[:,0])>0).sum())}; tasks answered {len(tasks_ans)}, with wrong {sum(not all(v) for v in tasks_ans.values())}; joint {100*(FC[:,1].sum()-FC[:,0].sum())/N:.2f}%")
    if Hs[:, 1].sum() and Hs[:, 3].sum():
        with np.errstate(invalid="ignore", divide="ignore"):
            bp = (W @ Hs[:, 0]) / (W @ Hs[:, 1]); bm = (W @ Hs[:, 2]) / (W @ Hs[:, 3])
        c = _pct(bp - bm)
        print(f"split: predict {100*Hs[:,0].sum()/Hs[:,1].sum():.1f}% of {Hs[:,1].sum():.0f}; miss {100*Hs[:,2].sum()/Hs[:,3].sum():.1f}% of {Hs[:,3].sum():.0f}; diff {100*(Hs[:,0].sum()/Hs[:,1].sum()-Hs[:,2].sum()/Hs[:,3].sum()):+.1f} [{100*c[0]:+.1f}, {100*c[1]:+.1f}]")
    dd = (W @ (EX[:, 0] - EX[:, 1])) / (W @ EX[:, 4]); c = _pct(dd)
    more = int((EX[:, 2] - EX[:, 3] > 1e-9).sum()); less = int((EX[:, 2] - EX[:, 3] < -1e-9).sum())
    p = st.binomtest(more, more + less, .5).pvalue if more + less else None
    print(f"exch: folds {EX[:,4].sum():.0f}; held {100*EX[:,0].sum()/EX[:,4].sum():.1f}% test {100*EX[:,1].sum()/EX[:,4].sum():.1f}%; diff {100*(EX[:,0].sum()-EX[:,1].sum())/EX[:,4].sum():+.1f} [{100*c[0]:+.1f}, {100*c[1]:+.1f}]; discordant {EX[:,2].sum():.0f}/{EX[:,3].sum():.0f}; clusters {more}:{less}; sign p {p}")
    print(f"(a) passes {passa}; (b) fails {bfail} (full-data answer right {bright}, wrong {bwrong}); (c) fails {cfail}; top answers not fitting {nofit} of {has}")
    cov = FC[:, 1].sum() / N
    print(f"floor {100*(1-mb/cov):.1f}%" if cov else "floor n/a")
    if monty:
        Mo = load_rows(f"{HL}/results/{monty}_base.jsonl")
        mo = {k: r["cfg"]["full"][str(r["m"] - 1)]["fc"] for k, r in Mo.items()}
        mo = {k: v for k, v in mo.items() if v is not None}
        both = set(mo) & set(ans_fc)
        print(f"overlap: both {len(both)}; ice right {sum(ans_fc[k] for k in both)}, Monty right {sum(float(mo[k]) for k in both):.0f}; ice only {len(set(ans_fc)-set(mo))}, right {sum(ans_fc[k] for k in set(ans_fc)-set(mo))}; Monty only {len(set(mo)-set(ans_fc))}, right {sum(float(mo[k]) for k in set(mo)-set(ans_fc)):.0f}; union {len(set(mo)|set(ans_fc))}")
    return dict(items=N)
report("concept", "ConceptARC", "concept")
report("mini", "Mini-ARC", "mini")
report("oned", "1D-ARC", "oned")
report("minimal", "MinimalTasks", "minimal")
report("agi2", "ARC-AGI-2 eval, 113 tasks")
# ---- reproduction against the authors' sheet
X = xlrows(ROOT + "external/judge/conceptarc/repo/data.xlsx")
head = X["Machine Solver Performance"][0]; ic = head.index("First Place ARC-Kaggle")
auth = {}
for r in X["Machine Solver Performance"][1:]:
    if r and r[0] and "Minimal" not in r[0]:
        auth[(r[0].replace(".json", ""), int(r[1]))] = r[ic] == "CORRECT"
items = [json.loads(l) for l in open(ICE + "export/items_concept.jsonl")]
mine = {}
for it in items:
    t = it["key"].split("/")[1].split("#")
    mine[(t[0], int(t[1]))] = s_grid(it["truth"]) in (M[it["full"]]["ans"][:3] if M.get(it["full"]) else [])
common = set(mine) & set(auth)
print(f"\nreproduction: common {len(common)}; mine {sum(mine[k] for k in common)}; authors {sum(auth[k] for k in common)}; agree {sum(mine[k]==auth[k] for k in common)} = {100*sum(mine[k]==auth[k] for k in common)/len(common):.1f}%")
nat = {}
nj = [json.loads(l) for l in open(ICE + "export/jobs_native.jsonl")]
print("native jobs", len(nj), {k: (v if not isinstance(v, (list, dict)) else type(v).__name__) for k, v in nj[0].items()})
tr = {it["key"]: s_grid(it["truth"]) for it in items}
for j in nj:
    key = j.get("key") or j.get("item") or j.get("native_key")
    if key is None:
        continue
    m = M.get(j["rid"])
    t = key.split("/")[1].split("#") if "/" in key else None
    if m and t:
        nat[(t[0], int(t[1]))] = tr.get(key) in m["ans"][:3]
if nat:
    cm = set(nat) & set(auth)
    print(f"native: items {len(cm)}; pass@3 {sum(nat[k] for k in cm)}; agree {sum(nat[k]==auth[k] for k in cm)} = {100*sum(nat[k]==auth[k] for k in cm)/len(cm):.1f}%")
oned = [json.loads(l) for l in open(ICE + "export/items_oned.jsonl")]
wide = 0
print("1D items with no full-data answer:", sum(not (M.get(it["full"]) and M[it["full"]]["ans"]) for it in oned))
st_ = collections.Counter(s for it in oned if M.get(it["full"]) for s in M[it["full"]]["status"])
print("1D full-run statuses", st_)
