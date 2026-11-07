"""Final pass recount of the one-column report, own code, from raw rows. Imports nothing from the project."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, os, random
from collections import defaultdict
ROOT = _REPO
R = ROOT + "/research/tbt_proper/column/results/"
def rd(n): return [json.loads(l) for l in open(R + n)]
def top(c): return next((x for x in c if x[3] is not None), None)
def rules(r):
    t = top(r["full"]); o = dict()
    seen = []; ok = False
    for c in r["full"]:
        if c[3] is not None and c[3] not in seen:
            seen.append(c[3]); ok = ok or c[4]
            if len(seen) == 2: break
    o["p2"] = float(ok)
    o["top"] = None if t is None else bool(t[4])
    o["fit"] = None if t is None or not t[5] else bool(t[4])
    F = {b: top(v) for b, v in r["folds"].items()}
    o["prog"] = [(bool(c[5]), bool(c[4])) for c in F.values() if c is not None]
    o["fc"] = None
    if r["n"] >= 2 and len(F) >= r["n"] and t is not None and all(c is not None for c in F.values()):
        if all(c[5] for c in F.values()):
            ans = {c[3] for c in F.values()}
            if len(ans) == 1 and t[3] in ans:
                o["fc"] = bool(next(iter(F.values()))[4])
    return o
def boot(items, stat, B=10000, seed=0):
    rng = random.Random(seed); m = len(items); v = []
    for _ in range(B):
        s = [items[rng.randrange(m)] for _ in range(m)]
        x = stat(s)
        if x is not None: v.append(x)
    v.sort()
    return round(v[int(.025 * len(v))], 1), round(v[min(len(v) - 1, int(.975 * len(v)))], 1)
HAND = ("arc-community", "nosound", "dbigham", "sequence")
def cl_task(k): return k.split("#")[0]
def cl_type(k): return k.split("/")[0]
def split_stats(rows, clus):
    C = defaultdict(list)
    for name, key, o in rows: C[clus(name, key)].extend(o["prog"])
    allp = [p for v in C.values() for p in v]
    a = [p for p in allp if p[0]]; b = [p for p in allp if not p[0]]
    def d(s):
        A = [p[1] for v in s for p in v if p[0]]; B = [p[1] for v in s for p in v if not p[0]]
        return None if not A or not B else 100 * (sum(A) / len(A) - sum(B) / len(B))
    return sum(p[1] for p in a), len(a), sum(p[1] for p in b), len(b), (None if d(list(C.values())) is None else round(d(list(C.values())), 1)), (None if d(list(C.values())) is None else boot(list(C.values()), d))
def within_stats(rows, clus):
    T = defaultdict(list); cl_of = {}
    for name, key, o in rows:
        T[(name, key.split("#")[0])].extend(o["prog"]); cl_of[(name, key.split("#")[0])] = clus(name, key)
    W = defaultdict(list)
    for t, ps in T.items():
        P = [r for h, r in ps if h]; Q = [r for h, r in ps if not h]
        if P and Q: W[cl_of[t]].append(100 * (sum(P) / len(P) - sum(Q) / len(Q)))
    vs = [x for v in W.values() for x in v]
    if not vs: return None
    f = lambda s: (lambda L: sum(L) / len(L) if L else None)([x for v in s for x in v])
    return round(sum(vs) / len(vs), 1), boot(list(W.values()), f), len(vs)
for label, names, clus in (("A hand-made", HAND, lambda n, k: n + ":" + cl_task(k)), ("B tama", ("tama",), lambda n, k: cl_type(k)), ("PQA", ("pqa",), lambda n, k: cl_type(k)),
                            ("ConceptARC", ("concept",), lambda n, k: cl_task(k)), ("Mini-ARC", ("mini",), lambda n, k: cl_task(k)), ("1D-ARC", ("oned",), lambda n, k: cl_type(k))):
    rows = []; MO = []
    for n in names:
        for r in rd(f"static_{n}.jsonl"): rows.append((n, r["task"], rules(r)))
        if os.path.exists(R + f"monty_{n}.jsonl"):
            for r in rd(f"monty_{n}.jsonl"): MO.append((n, r["task"], r["cfg"]["full"][str(r["m"] - 1)]))
    items = [o for _, _, o in rows]
    tally = lambda f: (sum(1 for o in items if o[f] is True), sum(1 for o in items if o[f] is not None))
    print("==", label, "items", len(rows), "clusters", len({clus(n, k) for n, k, _ in rows}))
    print(" pass2", sum(o["p2"] for o in items), "FA-LOO+(c)", tally("fc"), "cov", round(100 * tally("fc")[1] / len(rows), 1), "fit", tally("fit"), "top", tally("top"))
    print(" split", split_stats(rows, clus), "within", within_stats(rows, clus))
    print(" folds (n summed where n>1)", sum(r["n"] for n in names for r in rd(f"static_{n}.jsonl") if r["n"] > 1), "held-out minus test", (lambda H, T, N: (round(100 * H / N, 1), round(100 * T / N, 1), round(100 * (H - T) / N, 1)))(sum(h for _, _, o in rows for h, _ in o["prog"]), sum(t for _, _, o in rows for _, t in o["prog"]), sum(r["n"] for n in names for r in rd(f"static_{n}.jsonl") if r["n"] > 1)))
    if MO:
        ms = [o for _, _, o in MO]
        tm = lambda f: (sum(1 for o in ms if o.get(f) in (True, 1, 1.0)), sum(1 for o in ms if o.get(f) is not None))
        print(" Monty pass2", sum(o["p2"] for o in ms), "FA-LOO+(c)", tm("fc"), "cov", round(100 * tm("fc")[1] / len(ms), 1), "v5", tm("v5"), "fit", tm("fit"))
        mrows = [(n, k, dict(prog=[(bool(a), bool(b)) for a, b in o.get("fold_programs", [])])) for n, k, o in MO]
        print(" Monty split", split_stats(mrows, clus), "within", within_stats(mrows, clus))
print("== games, changed transitions")
games = {n: json.load(open(R + f"games/{n}.json")) for n in os.listdir(R + "games") for n in [n[:-5]]}
def arm(n, sel=lambda r: r["n_ch"] > 0): 
    C = defaultdict(lambda: [0, 0])
    for r in games[n]:
        if sel(r): C[r["game"]][0] += float(r["col"]); C[r["game"]][1] += 1
    return C
def diff(a, b, label):
    G = sorted(a)
    pa = [(a[g][0], b[g][0], a[g][1]) for g in G]
    f = lambda s: (lambda x, y, n: None if n == 0 else 100 * (x - y) / n)(sum(t[0] for t in s), sum(t[1] for t in s), sum(t[2] for t in s))
    print(label, "x", round(100 * sum(t[0] for t in pa) / sum(t[2] for t in pa), 1), "y", round(100 * sum(t[1] for t in pa) / sum(t[2] for t in pa), 1), "diff", round(f(pa), 1), boot(pa, f), "games", len(G), "n", sum(t[2] for t in pa))
diff(arm("full"), arm("nomotor"), "M1 motor")
diff(arm("full"), arm("colour_only"), "M5 displacement")
diff(arm("local+moving"), arm("local"), "M4a pop")
diff(arm("local+near"), arm("local"), "M4b pop")
diff(arm("single+moving"), arm("single"), "M4a single")
diff(arm("single+near"), arm("single"), "M4b single")
full = {(r["game"], r["i"]): r for r in games["full"]}
names = {r["game"] for r in games["full"]}
comp = {}
for line in open(ROOT + "/research/arc3_wm/results/wm2_m2.jsonl"):
    r = json.loads(line)
    if r["k"] == 3 and r["game"] in names: comp[(r["game"], r["i"])] = r
X = defaultdict(lambda: [0, 0]); Mo = defaultdict(lambda: [0, 0]); B1 = defaultdict(lambda: [0, 0])
for key, r in comp.items():
    if key not in full or r["B0_play"]: continue
    g = key[0]; x = full[key]
    X[g][0] += float(x["col"]); X[g][1] += 1
    Mo[g][0] += float(bool(r.get("M_play_fallback"))); Mo[g][1] += 1
    B1[g][0] += float(bool(r["B1rel_play_play"])); B1[g][1] += 1
diff(X, Mo, "M2 vs Monty columns k=3")
diff(X, B1, "M3 vs repeat k=3")
for h in (4,):
    A = defaultdict(lambda: [0, 0]); U = defaultdict(lambda: [0, 0])
    for r in games["full"]:
        if f"roll{h}" in r:
            A[r["game"]][0] += float(r[f"roll{h}"]); A[r["game"]][1] += 1
            U[r["game"]][0] += float(r[f"still{h}"]); U[r["game"]][1] += 1
    diff(A, U, f"M6 rollout h={h}")
Aa = defaultdict(lambda: [0, 0]); Bb = defaultdict(lambda: [0, 0])
for r in games["local"]:
    Aa[r["game"]][0] += float(r["col"]); Aa[r["game"]][1] += 1
for r in games["local+library"]:
    Bb[r["game"]][0] += float(r["col"]); Bb[r["game"]][1] += 1
diff(Bb, Aa, "E2 games library minus alone, all")
print("== static arms: S2 object sensors, S3 count, E2: from analysis.json (read directly)")
J = json.load(open(R + "analysis.json"))
for s in ("hand", "tama"):
    print(s, "S2", J["strata"][s]["S2 all minus cells"], "count", J["strata"][s]["with minus without count sensor"])
print("S3a", J["S3"]["S3a with count minus Monty-ARC"]["diff"], J["S3"]["S3a with count minus Monty-ARC"]["ci"], "S3b", J["S3"]["S3b with count minus without count"]["diff"], J["S3"]["S3b with count minus without count"]["ci"])
print("E2", J["E2"]["pass2"], J["E2"]["E2 same concept minus alone, CI by concept group"]["diff"], J["E2"]["E2 same concept minus alone, CI by concept group"]["ci"])
PH = json.load(open(R + "post_hoc.json"))
for k in ("hand", "tama", "concept", "mini", "oned"):
    print(k, {a: PH[k][a] for a in ("pass1_column", "pass1_monty", "answered_column", "answered_monty", "pass2_cells_only")}, "first right by reach", PH[k]["first_right_column_by_reach"])
