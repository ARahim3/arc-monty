"""Final pass, own code. FA-LOO minus fit on the new rows; column development pass@2; (S) on the unseen sets and Monty-ARC's fold-level split from the direct run of final_s_check.py.
usage: python -I -B final_tables.py <dir with s_*.jsonl>"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, os, random, sys, collections
ROOT = _REPO
def boot(items, stat, B=10000, seed=0):
    r = random.Random(seed); m = len(items); v = []
    for _ in range(B):
        x = stat([items[r.randrange(m)] for _ in range(m)])
        if x is not None: v.append(x)
    v.sort()
    return round(v[int(.025 * len(v))], 1), round(v[min(len(v) - 1, int(.975 * len(v)))], 1)
def fa_fit(clusters):
    """clusters: list of lists of (fc, fit), None=abstain, True/False right."""
    def stat(s):
        F = [x[0] for G in s for x in G if x[0] is not None]; T = [x[1] for G in s for x in G if x[1] is not None]
        if not F or not T: return None
        return 100 * (sum(F) / len(F) - sum(T) / len(T))
    return round(stat(clusters), 1), boot(clusters, stat)
yes = lambda v: None if v is None else bool(v)
C = collections.defaultdict(list)
for l in open(ROOT + "/research/generator_control/monty/results/rearc_base.jsonl"):
    r = json.loads(l); o = r["cfg"]["full"]["3"]; C[r["task"]].append((yes(o["fc"]), yes(o["fit"])))
print("Monty re-arc FA-LOO minus fit", fa_fit(list(C.values())))
for label, names, cl in (("hand", ("arc-community", "nosound", "dbigham", "sequence"), lambda n, k: n + ":" + k.split("#")[0]), ("tama", ("tama",), lambda n, k: k.split("/")[0])):
    C = collections.defaultdict(list)
    for n in names:
        for l in open(ROOT + f"/research/tbt_proper/column/results/monty_{n}.jsonl"):
            r = json.loads(l); o = r["cfg"]["full"][str(r["m"] - 1)]; C[cl(n, r["task"])].append((yes(o["fc"]), yes(o["fit"])))
    print("Monty", label, "FA-LOO minus fit", fa_fit(list(C.values())))
J = json.load(open(ROOT + "/research/generator_control.json"))
print("2020 re-arc rules", {k: (v.get("correct"), v.get("answered")) if isinstance(v, dict) else v for k, v in J["ice"]["rules"].items()})
# 2020 program, re-arc, FA-LOO minus fit, from raw lines
raw = collections.defaultdict(dict)
for line in open(ROOT + "/research/generator_control/ice/raw/runs_r5.jsonl"):
    r = json.loads(line)
    raw[r["rid"]].setdefault(r["cfg"], r)
def okimg(s):
    if not (isinstance(s, str) and s.startswith("|") and s.endswith("|") and len(s) > 2): return False
    x = s[1:-1].split("|")
    return all(c.isdigit() for c in x) and len({len(c) for c in x}) == 1
def merged(rid):
    c = []
    for cfg, r in raw.get(rid, {}).items():
        if r.get("status") == "ok":
            c += [(float(a), i) for i, a in r.get("lines", []) if float(a) >= 0 and okimg(i)]
    c.sort(key=lambda t: (t[0], t[1]), reverse=True)
    ans, sc = [], []
    for a, i in c:
        if i not in ans: ans.append(i); sc.append(a)
    return ans, sc, (raw[rid].get(3) or {}).get("nd")
S_ = lambda g: "|" + "|".join("".join(map(str, r)) for r in g) + "|"
pairs = []
for l in open(ROOT + "/research/generator_control/ice/export/items_rearc.jsonl"):
    it = json.loads(l); y = S_(it["truth"])
    a, sc, nd = merged(it["full"])
    fit = (a[0] == y) if a and sc[0] > nd - 0.499 else None
    held = [merged(x["held_rid"])[0][:1] for x in it["folds"]]; tests = [merged(x["test_rid"])[0][:1] for x in it["folds"]]
    ok = all(h and h[0] == S_(x["held_truth"]) for h, x in zip(held, it["folds"])) and all(tests) and len({t[0] for t in tests}) == 1 and a and a[0] == tests[0][0]
    pairs.append([((a[0] == y) if ok else None, fit)])
print("2020 re-arc: fit", sum(1 for p_ in pairs if p_[0][1] is True), sum(1 for p_ in pairs if p_[0][1] is not None), "FA-LOO", sum(1 for p_ in pairs if p_[0][0] is True), sum(1 for p_ in pairs if p_[0][0] is not None), "minus fit", fa_fit(pairs))
for d, tag in (("static_new233_base.jsonl", "233 new"), ("static_agi2-eval_base.jsonl", "ARC-AGI-2 eval")):
    rows = [json.loads(l) for l in open(ROOT + "/research/tbt_proper/column/dev/" + d)]
    print(tag, "column development: tasks", len(rows), "pass@2 score sum", round(sum(r["score"] for r in rows), 2))
if len(sys.argv) > 1:
    D = sys.argv[1]
    total = sq = sd = 0
    for tag in ("concept", "mini", "oned", "minimal"):
        p = f"{D}/s_{tag}.jsonl"
        if not os.path.exists(p): continue
        R = [json.loads(l) for l in open(p)]
        folds = [f for r in R for f in r["folds"]]
        total += len(folds); sq += sum(not f["sq"] for f in folds); sd += sum(not f["sd"] for f in folds)
        h = sum(f["h"] for f in folds); t = sum(f["t"] for f in folds)
        print(f"{tag}: items {len(R)}, folds {len(folds)}, query swap changes {sum(not f['sq'] for f in folds)}, demo reversal changes {sum(not f['sd'] for f in folds)}; h {100 * h / len(folds):.1f}% t {100 * t / len(folds):.1f}%, h only {sum(f['h'] and not f['t'] for f in folds)}, t only {sum(f['t'] and not f['h'] for f in folds)}")
        cl = (lambda k: k.split("/")[0]) if tag == "oned" else (lambda k: k.split("#")[0])
        CL = collections.defaultdict(list); TK = collections.defaultdict(list)
        for r in R:
            for f in r["folds"]:
                if f["has"]:
                    CL[cl(r["key"])].append((f["h"], f["t"])); TK[r["key"].split("#")[0]].append((f["h"], f["t"]))
        def d(s):
            A = [x[1] for G in s for x in G if x[0]]; B = [x[1] for G in s for x in G if not x[0]]
            return None if not A or not B else 100 * (sum(A) / len(A) - sum(B) / len(B))
        A = [x for G in CL.values() for x in G if x[0]]; B = [x for G in CL.values() for x in G if not x[0]]
        print(f"   split predict {sum(x[1] for x in A)}/{len(A)} = {100 * sum(x[1] for x in A) / len(A):.1f}, miss {sum(x[1] for x in B)}/{len(B)} = {100 * sum(x[1] for x in B) / len(B):.1f}, between {d(list(CL.values())):.1f} {boot(list(CL.values()), d)}")
        W = collections.defaultdict(list)
        for k, G in TK.items():
            a = [x[1] for x in G if x[0]]; b = [x[1] for x in G if not x[0]]
            if a and b: W[cl(k + "#0")].append(100 * (sum(a) / len(a) - sum(b) / len(b)))
        vs = [x for v in W.values() for x in v]
        f = lambda s: (lambda L: sum(L) / len(L) if L else None)([x for v in s for x in v])
        if vs: print(f"   within {sum(vs) / len(vs):.1f} {boot(list(W.values()), f)} tasks {len(vs)}")
    print("total real-role folds", total, "query swap changes", sq, "demo reversal changes", sd)
