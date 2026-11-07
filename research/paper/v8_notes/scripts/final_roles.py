"""Final pass, own code. (1) Monty-ARC, all roles from per-module caches, top answer by frozen vote.pool only: exact role-permutation test, null of the sign statistic, events,
(a)+(b) role-averaged. (2) 2020 program on re-arc from raw lines. (3) re-arc minus other sets, held-out minus test. Output on stdout."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import os, sys, json, hashlib, random, collections, glob
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[v] = "1"
sys.dont_write_bytecode = True
ROOT = _REPO
sys.path.insert(0, ROOT)
import numpy as np
from arcmonty import vote
MODS = ["self-model", "periodic", "behavior", "dynamics", "composition", "association", "pattern", "field"]
def H(a):
    a = np.ascontiguousarray(a)
    return hashlib.md5(str(a.shape).encode() + a.astype(np.int8).tobytes()).hexdigest()[:12]
def exact(D):
    """D: list of per-role lists with real role last. Exact two-sided p for the sum, uniform role per item."""
    dist = {0: 1.0}
    for row in D:
        nd = collections.defaultdict(float)
        for s, p in dist.items():
            for d in row:
                nd[s + d] += p / len(row)
        dist = nd
    obs = sum(r[-1] for r in D)
    return obs, sum(p for s, p in dist.items() if abs(s) >= abs(obs) - 1e-9)
def boot(items, stat, B=10000, seed=0):
    r = random.Random(seed); m = len(items); v = []
    for _ in range(B):
        x = stat([items[r.randrange(m)] for _ in range(m)])
        if x is not None: v.append(x)
    v.sort()
    return round(v[int(.025 * len(v))], 1), round(v[min(len(v) - 1, int(.975 * len(v)))], 1)
def process(path, label):
    ev_ms = []; D = []; ev_items = ev2 = real_ev = 0; exp = 0.0; ans = wrong = 0; roles = 0; sym = symn = 0
    sign_pos = sign_neg = 0.0; o_pos = o_neg = 0
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            G = [np.array(g, dtype=np.int8) for g in r["grids"]]
            GH = [H(g) for g in G]
            m = r["m"]; truth = r["truth"]
            tops = {}
            for a in range(m):
                for b in range(m):
                    if a == b: continue
                    run = r["runs"][f"{a},{b}"]
                    C = []
                    for mod in MODS:
                        for c in run.get(mod, {"cands": []})["cands"]:
                            C.append(dict(lm=c["lm"], hyp=c["hyp"], evidence=c["ev"], preds=[G[i] for i in c["p"]], _p=c["p"]))
                    tops[(a, b)] = vote.pool(C)[0]["_p"] if C else None
            # (a, b) run: queries [x_b, x_a], model trained without a and b
            miss = {}
            for a in range(m):
                for b in range(m):
                    if a == b: continue
                    p = tops[(a, b)]
                    miss[(a, b)] = 1 if p is None else int(GH[p[1]] != truth[a])
            row = []; evs = 0
            for rr in range(m):
                others = [b for b in range(m) if b != rr]
                h = sum(1 - miss[(b, rr)] for b in others); t = sum(1 - miss[(rr, b)] for b in others)
                row.append(h - t)
                e = all(miss[(rr, b)] == 1 and miss[(b, rr)] == 0 for b in others)
                evs += e
                if rr == m - 1: real_ev += e
                a_ok = all(miss[(b, rr)] == 0 for b in others)
                ansg = [tops[(rr, b)][1] if tops[(rr, b)] is not None else None for b in others]
                hs = [GH[x] if x is not None else None for x in ansg]
                roles += 1
                if a_ok and None not in hs and len(set(hs)) == 1:
                    ans += 1; wrong += hs[0] != truth[rr]
            D.append(row)
            ev_items += evs > 0; ev2 += evs > 1
            if evs: ev_ms.append(m)
            if evs: exp += 1 / m
            sign_pos += sum(d > 0 for d in row) / m; sign_neg += sum(d < 0 for d in row) / m
            o_pos += row[-1] > 0; o_neg += row[-1] < 0
    obs, p = exact(D)
    print(f"{label}: items {len(D)}, identity broken {sum(sum(x) != 0 for x in D)}, events items {ev_items}, two+ {ev2}, on real role {real_ev}, expected {exp:.2f}; sum D real {obs}, exact two-sided p {p:.4f}")
    print(f"   events on the real role: exact P(X >= {real_ev}) = {pb_upper(ev_ms, real_ev):.3f}")
    print(f"   sign statistic: observed more-held:more-test {o_pos}:{o_neg}; null expected {sign_pos:.1f}:{sign_neg:.1f}; (a)+(b) all roles answered {ans}, wrong {wrong}, right {ans - wrong}, roles {roles}, coverage {100 * ans / roles:.1f}%")
    return D
def pb_upper(ms, k):
    """P(X >= k), X = sum of independent Bernoulli(1/m) over items with an event."""
    dist = [1.0]
    for m in ms:
        nd = [0.0] * (len(dist) + 1)
        for i, v in enumerate(dist):
            nd[i] += v * (1 - 1 / m); nd[i + 1] += v / m
        dist = nd
    return sum(dist[k:])
CA = ROOT + "/research/monty_heldout/cache/{}_p0.jsonl"
if "--ice-only" not in sys.argv:
    for tag in ("concept", "mini", "oned", "minimal"):
        process(CA.format(tag), "Monty " + tag)
    process(ROOT + "/research/generator_control/monty/cache/rearc_p0.jsonl", "Monty re-arc")
# Monty re-arc real role, from re-vote file
rows = [json.loads(l) for l in open(ROOT + "/research/generator_control/monty/results/rearc_base.jsonl")]
tally = lambda f: (sum(1 for r in rows if r["cfg"]["full"]["3"].get(f) in (True, 1, 1.0)), sum(1 for r in rows if r["cfg"]["full"]["3"].get(f) is not None))
print("Monty re-arc real: fit", tally("fit"), "fc", tally("fc"), "v5", tally("v5"), "p2", sum(r["cfg"]["full"]["3"]["p2"] for r in rows))
print("=== 2020 program, re-arc, raw lines")
ICE = ROOT + "/research/generator_control/ice/"
raw = collections.defaultdict(dict)
for line in open(ICE + "raw/runs_r5.jsonl"):
    r = json.loads(line)
    if r["cfg"] not in raw[r["rid"]]: raw[r["rid"]][r["cfg"]] = r
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
    ans = []; sc = []
    for a, i in c:
        if i not in ans: ans.append(i); sc.append(a)
    return ans, sc, raw[rid][3].get("nd") if rid in raw and 3 in raw[rid] else None
S = lambda g: "|" + "|".join("".join(map(str, r)) for r in g) + "|"
tasks = {}
for f in sorted(glob.glob(ROOT + "/research/generator_control/data/tasks/*.json")):
    tasks[os.path.basename(f)[:-5]] = json.load(open(f))
items = {r: {json.loads(l)["task"]: json.loads(l) for l in open(ICE + f"export/items_rearc{'' if r == 3 else '_role%d' % r}.jsonl")} for r in range(4)}
def role_out(it, truth_test):
    fans = []; h = []; t = []
    for x in it["folds"]:
        ha = merged(x["held_rid"])[0]; ta = merged(x["test_rid"])[0]
        h.append(bool(ha) and ha[0] == S(x["held_truth"]))
        tt = ta[0] if ta else None
        t.append(tt == S(truth_test)); fans.append(tt)
    fa = all(h) and None not in fans and len(set(fans)) == 1
    return dict(h=h, t=t, fans=fans, a=all(h), fa=fa, right=fa and fans[0] == S(truth_test))
D = []; real_rows = []; hrows = []; ans = wrong = 0; evc = collections.Counter(); per = []
for t, it in items[3].items():
    tr = tasks[t]["test"][0]["output"]
    full = merged(it["full"])[0]; top = full[0] if full else None
    o = role_out(it, tr)
    fc = o["fa"] and top == o["fans"][0]
    real_rows.append(dict(fc=fc, right=o["right"], top=top == S(tr), has=top is not None))
    hrows.append(list(zip(o["h"], o["t"])))
    row = []; evs = 0; a = 0
    demos = sorted(tasks[t]["train"], key=lambda p: (len(p["input"]) * len(p["input"][0]), len(p["input"]), len(p["input"][0]), json.dumps(p["input"])))
    for r in range(4):
        itr = items[r][t]
        # truth for role r: test output if r==3, else demonstration r in canonical order
        tru = itr["truth"]
        q = role_out(itr, tru)
        row.append(sum(q["h"]) - sum(q["t"]))
        e = all(q["h"]) and not any(q["t"]); evs += e
        if q["fa"]:
            a += 1; ans += 1; wrong += not q["right"]
    # order so real role is last: role 3
    D.append(row); evc[min(evs, 2)] += 1; per.append(a / 4)
fc = [r for r in real_rows if r["fc"]]
print("top", sum(r["top"] for r in real_rows), sum(r["has"] for r in real_rows), "fc", sum(r["right"] for r in fc), len(fc), "coverage", 100 * len(fc) / 200)
obs, p = exact(D)
print("role test: sum D", obs, "mean h-t", 100 * obs / 600, "exact p", round(p, 4), "identity broken", sum(sum(x) != 0 for x in D), "events", dict(evc), "role-avg (a)+(b)", ans - wrong, ans)
f = lambda s: 100 * sum(int(a) - int(b) for x in s for a, b in x) / sum(len(x) for x in s)
print("h-t", round(f(hrows), 1), boot(hrows, f))
print("=== held-out split on re-arc, fold programs with a test answer")
def split_report(T, name):
    A = [x[1] for G in T for x in G if x[0]]; B = [x[1] for G in T for x in G if not x[0]]
    def d(s):
        a = [x[1] for G in s for x in G if x[0]]; b = [x[1] for G in s for x in G if not x[0]]
        return None if not a or not b else 100 * (sum(a) / len(a) - sum(b) / len(b))
    W = []
    for G in T:
        a = [x[1] for x in G if x[0]]; b = [x[1] for x in G if not x[0]]
        if a and b: W.append(100 * (sum(a) / len(a) - sum(b) / len(b)))
    f = lambda s: sum(s) / len(s)
    print(name, "predict", sum(A), len(A), "miss", sum(B), len(B), "between", round(d(T), 1), boot(T, d), "within", round(f(W), 1), boot(W, f), "tasks", len(W))
T = []
for t, it in items[3].items():
    tr = S(it["truth"]); G = []
    for x in it["folds"]:
        ha = merged(x["held_rid"])[0]; ta = merged(x["test_rid"])[0]
        if ta: G.append((bool(ha) and ha[0] == S(x["held_truth"]), ta[0] == tr))
    T.append(G)
split_report(T, "2020 program")
T = []; hs = ts = ho = to = n = 0
with open(ROOT + "/research/generator_control/monty/cache/rearc_p0.jsonl") as fh:
    for line in fh:
        r = json.loads(line); Gs = [np.array(g, dtype=np.int8) for g in r["grids"]]; GH = [H(g) for g in Gs]; G = []
        m = r["m"]; truth = r["truth"]; real = m - 1
        for b in range(m - 1):
            run = r["runs"][f"{real},{b}"]; C = []
            for mod in MODS:
                for c in run.get(mod, {"cands": []})["cands"]:
                    C.append(dict(lm=c["lm"], hyp=c["hyp"], evidence=c["ev"], preds=[Gs[i] for i in c["p"]], _p=c["p"]))
            n += 1
            if C:
                p = vote.pool(C)[0]["_p"]; h = GH[p[0]] == truth[b]; t_ = GH[p[1]] == truth[real]
                G.append((h, t_)); hs += h; ts += t_; ho += h and not t_; to += t_ and not h
        T.append(G)
split_report(T, "Monty-ARC")
print("Monty-ARC re-arc folds", n, "h", round(100 * hs / n, 1), "t", round(100 * ts / n, 1), "h only", ho, "t only", to)
