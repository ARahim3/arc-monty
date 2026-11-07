"""Stage C recount, own code: Qwen on ConceptARC with one test input per prompt (research/generator_control.md Addendum 4, section 7).
Reads raw JSONL and task JSON only; imports nothing from the project (not analyse_c.py, not faloo_sampling_analyze.py).
    .venv/bin/python -I -B research/paper/v8_notes/scripts/final_stage_c.py > research/paper/v8_notes/final_stage_c.txt
Intervals: percentile cluster bootstrap by task, 10,000 resamples, random.Random(0); exact intervals Clopper-Pearson (scipy beta)."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import glob
import json
import os
import random
from collections import Counter
from math import comb

from scipy.stats import beta

ROOT = _REPO
RAW = ROOT + "/research/generator_control/raw/"
S2_FILE = ROOT + "/llm/results/qwen38_faloo_sampling_concept_b32768.jsonl"
B = 10000


def dumps(g):
    return None if g is None else json.dumps(g, separators=(",", ":"))


def gkey(g):  # the harness's canonical order: area, height, width, content
    return (len(g) * len(g[0]), len(g), len(g[0]), json.dumps(g))


def read(path):
    """Earliest-started good record per (kind, task, fold); also lines, error lines, distinct keys."""
    best, n, err, keys = {}, 0, 0, Counter()
    for line in open(path, errors="replace"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        n += 1
        if "error" in r:
            err += 1
            continue
        k = (r["kind"], r["task_id"], r["fold"])
        keys[k] += 1
        if k not in best or r.get("started_at", 0) < best[k].get("started_at", 0):
            best[k] = r
    return best, n, err, keys


def out(rec):
    """-> (dict query id -> grid, verified). First verified round, else last round with output."""
    rounds = [x for x in (rec or {}).get("rounds", []) if "test_out" in x]
    if not rounds:
        return None, False
    v = [x for x in rounds if x.get("verified")]
    x = v[0] if v else rounds[-1]
    return dict(zip(rec["query_ids"], x["test_out"])), bool(v)


def load_concept():
    base = ROOT + "/external/judge/conceptarc/repo/corpus"
    T = {}
    for f in sorted(glob.glob(base + "/*/*.json")):
        d = json.load(open(f))
        T[os.path.relpath(f, base)[:-5]] = dict(train=d["train"], test=d["test"])
    return T


def load_rearc():
    T = {}
    for f in sorted(glob.glob(ROOT + "/research/generator_control/data/tasks/*.json")):
        d = json.load(open(f))
        T[os.path.basename(f)[:-5]] = dict(train=d["train"], test=d["test"])
    return T


def demos_of(task):
    return sorted(task["train"], key=lambda p: gkey(p["input"]))


def eq(a, b):
    return a is not None and dumps(a) == dumps(b)


def pct(xs):
    xs = sorted(xs)
    return xs[int(0.025 * len(xs))], xs[min(len(xs) - 1, int(0.975 * len(xs)))]


def boot(items, stat, seed=0):
    rng = random.Random(seed)
    v = []
    for _ in range(B):
        s = stat(rng.choices(items, k=len(items)))
        if s is not None:
            v.append(s)
    return pct(v)


def cp(k, n):
    lo = 0.0 if k == 0 else beta.ppf(0.025, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(0.975, k + 1, n - k)
    return float(lo), float(hi)


def hyper_le(V, W, C, x):
    return sum(comb(W, i) * comb(V - W, C - i) for i in range(x + 1)) / comb(V, C)


def P(x):
    return round(100 * x, 2)


def folds_ht(task, S, kind="fold", key=lambda i: i, test_k=(0,)):
    """Per fold: h (held-out demonstration right), t (fraction of the listed test pairs right), v (fold program verified)."""
    dm = demos_of(task)
    L = []
    for i in range(len(dm)):
        d, v = out(S.get((kind, task["id"], key(i))))
        h = bool(d) and eq(d.get("demo:%d" % i), dm[i]["output"])
        t = sum(bool(d) and eq(d.get("test:%d" % k), task["test"][k]["output"]) for k in test_k) / len(test_k)
        L.append(dict(h=float(h), t=float(t), v=v))
    return L


def task_row(task, S):
    """Task level, first test pair only: fit, (a), (b), (c) as the rule defines them."""
    dm = demos_of(task)
    n = len(dm)
    truth = task["test"][0]["output"]
    fo, fv = out(S.get(("full", task["id"], -1)))
    fg = fo.get("test:0") if fo else None
    held, tests = [], []
    for i in range(n):
        d, _ = out(S.get(("fold", task["id"], i)))
        held.append(bool(d) and eq(d.get("demo:%d" % i), dm[i]["output"]))
        tests.append(dumps(d.get("test:0")) if d else None)
    a = all(held)
    b = all(x is not None for x in tests) and len(set(tests)) == 1
    cons = json.loads(tests[0]) if b else None
    c = b and dumps(fg) == tests[0]
    return dict(task=task["id"], n=n, ver=fv, full_right=eq(fg, truth), a=a, b=b, c=c, held=sum(held),
                ab=a and b, abc=a and b and c and fv, cons_right=b and eq(cons, truth))


def rules(rows, mb):
    N = len(rows)
    for name, sel, right in (("fit", "ver", "full_right"), ("(a)+(b)", "ab", "cons_right"), ("(a)+(b)+(c)", "abc", "cons_right")):
        A = [r for r in rows if r[sel]]
        k = sum(r[right] for r in A)
        w = len(A) - k
        cov = len(A) / N
        lo, hi = boot([int(r[sel]) for r in rows], lambda s: sum(s) / len(s))
        print(f"{name}: {k}/{len(A)} = {P(k / len(A))}% exact {[P(x) for x in cp(k, len(A))]}; coverage {P(cov)}% [{P(lo)}, {P(hi)}];"
              f" joint {w}/{N} = {P(w / N)}% exact {[round(100 * x, 2) for x in cp(w, N)]}; floor 1 - {mb:.4f}/c = {P(1 - mb / cov)}% [{P(1 - mb / lo)}, {P(1 - mb / hi)}];"
              f" wrong: {[r['task'] for r in A if not r[right]]}")


def verified(rows):
    V = [r for r in rows if r["ver"]]
    W = [r for r in V if not r["full_right"]]
    C = [r for r in V if r["abc"]]
    kept = [r for r in C if not r["full_right"]]
    print(f"verified {len(V)}, fully right {len(V) - len(W)}, not right {len(W)}; certified {len(C)}; wrong kept {len(kept)} {[r['task'] for r in kept]},"
          f" rejected {len(W) - len(kept)}; hypergeometric P(kept <= {len(kept)}) = {hyper_le(len(V), len(W), len(C), len(kept)):.4f}")
    return V, W


CO = load_concept()
for t in CO:
    CO[t]["id"] = t
TASKS = sorted(CO)

print("=== 0. Run checks, stage C")
M, n_m, e_m, keys_m = read(RAW + "gc_qwen_c1.jsonl")
R, n_r, e_r, keys_r = read(RAW + "gc_qwen_c1_retry.jsonl")
print(f"main: {n_m} lines, {e_m} error records, {len(M)} distinct keys, duplicates {sum(c > 1 for c in keys_m.values())}, kinds {dict(Counter(k[0] for k in M))}")
print(f"retry: {n_r} lines, {e_r} error records, {len(R)} distinct keys")
missing = [t for t in TASKS if ("full", t, -1) not in M or any(("fold", t, i) not in M for i in range(len(CO[t]["train"])))]
print("tasks", len(TASKS), "complete", len(TASKS) - len(missing), "first test pair by file order; query ids name test:0 only:",
      all(all(not q.startswith("test:") or q == "test:0" for q in r["query_ids"]) for r in M.values()))
tok = Counter()
for k, r in M.items():
    tok[k[0]] += r.get("gen_tokens", 0)
rounds = [x for r in M.values() for x in r.get("rounds", [])]
print(f"tokens: full {tok['full']:,}, fold {tok['fold']:,}, total {sum(tok.values()):,}; retries {sum(r.get('gen_tokens', 0) for r in R.values()):,};"
      f" all {sum(tok.values()) + sum(r.get('gen_tokens', 0) for r in R.values()):,}")
print(f"rounds {len(rounds)}, at the 32k cap (forced) {sum(bool(x.get('forced')) for x in rounds)}, without code (n_ok = -1) {sum(x.get('n_ok') == -1 for x in rounds)},"
      f" largest prompt {max(x.get('prompt_len', 0) for x in rounds)}, resumed {sum(r.get('resumed_from_round', 0) > 0 for r in M.values())}, VMs {sorted({r.get('vm') for r in M.values()})}")
mb = sum(1 / (len(CO[t]["train"]) + 1) for t in TASKS) / len(TASKS)
print(f"mean 1/(n+1) over {len(TASKS)} tasks = {mb:.4f}; tasks with n = 1: {sum(len(CO[t]['train']) == 1 for t in TASKS)}")

print("\n=== 1. Held-out minus test, stage C, all folds, abstaining = wrong")
FC = {t: folds_ht(CO[t], M) for t in TASKS}
F = [x for t in TASKS for x in FC[t]]
h, tt = sum(x["h"] for x in F), sum(x["t"] for x in F)
items = [(sum(x["h"] - x["t"] for x in FC[t]), sum(x["h"] for x in FC[t]), sum(x["t"] for x in FC[t]), len(FC[t])) for t in TASKS]
ci = boot(items, lambda s: sum(a[0] for a in s) / sum(a[3] for a in s))
cih = boot(items, lambda s: sum(a[1] for a in s) / sum(a[3] for a in s))
cit = boot(items, lambda s: sum(a[2] for a in s) / sum(a[3] for a in s))
print(f"folds {len(F)}, held-out right {h:.0f} = {P(h / len(F))}% [{P(cih[0])}, {P(cih[1])}], test right {tt:.0f} = {P(tt / len(F))}% [{P(cit[0])}, {P(cit[1])}]")
print(f"difference {P((h - tt) / len(F))} points [{P(ci[0])}, {P(ci[1])}] (seed 0), half-width {P((ci[1] - ci[0]) / 2)}")
SUM = dict(E=((h - tt) / len(F), ci))
print(f"discordant: held-out only {sum(x['h'] and not x['t'] for x in F):.0f}, test only {sum(x['t'] and not x['h'] for x in F):.0f}")

print("\n=== 2. Rules, task level, first test pair")
rows = [task_row(CO[t], M) for t in TASKS]
rules(rows, mb)
V, W = verified(rows)
print("verified-but-wrong tasks:", [r["task"] for r in W])
why = Counter("(a)" if not r["a"] else "(b)" if not r["b"] else "(c)" if not r["c"] else "passes" for r in W)
print("what stops them (first failing condition):", dict(why), {r["task"]: ("(a)" if not r["a"] else "(b)" if not r["b"] else "(c)" if not r["c"] else "passes") for r in W})

print("\n=== 3. Held-out split, fold programs verified on what they saw")
VS = [[x for x in FC[t] if x["v"]] for t in TASKS]
VS = [s for s in VS if s]
def split(s):
    hit = [x["t"] for r in s for x in r if x["h"]]
    miss = [x["t"] for r in s for x in r if not x["h"]]
    return hit, miss
hit, miss = split(VS)
dsplit = lambda s: (sum(split(s)[0]) / len(split(s)[0]) - sum(split(s)[1]) / len(split(s)[1])) if split(s)[0] and split(s)[1] else None
print(f"tasks {len(VS)}, programs {len(hit) + len(miss)}; predict held-out {sum(hit):.0f}/{len(hit)} = {P(sum(hit) / len(hit))}%; miss {sum(miss):.0f}/{len(miss)} = {P(sum(miss) / len(miss))}%;"
      f" between {P(sum(hit) / len(hit) - sum(miss) / len(miss))} {[P(x) for x in boot(VS, dsplit)]}")
pairs = [(sum(x["t"] for x in r if x["h"]) / sum(x["h"] for x in r), sum(x["t"] for x in r if not x["h"]) / sum(1 - x["h"] for x in r))
         for r in VS if any(x["h"] for x in r) and any(not x["h"] for x in r)]
md = lambda s: sum(a - b for a, b in s) / len(s)
print(f"within tasks: {len(pairs)} tasks, mean paired difference {P(md(pairs))} {[P(x) for x in boot(pairs, md)]}")
SUM["split"] = (sum(hit) / len(hit) - sum(miss) / len(miss), boot(VS, dsplit))
SUM["within"] = (md(pairs), boot(pairs, md))

print("\n=== 4. Retry rule: on tasks whose full run verified, a fold that does not fit its own n-1 demonstrations gets up to two more samples")
M2 = dict(M)
st = Counter()
for r in rows:
    if not r["ver"]:
        continue
    t = r["task"]
    for i in range(r["n"]):
        if out(M[("fold", t, i)])[1]:
            continue
        st["not fitting"] += 1
        for att in (1, 2):
            rr = R.get(("retry", t, i * 100 + att))
            if rr is None:
                continue
            st[f"retried {att}"] += 1
            st["tokens"] += rr.get("gen_tokens", 0)
            if out(rr)[1]:
                st[f"fit at {att}"] += 1
                M2[("fold", t, i)] = rr
                break
        else:
            st["never fit"] += 1
print(dict(st), "runs", st["retried 1"] + st["retried 2"])
rows2 = [task_row(CO[t], M2) for t in TASKS]
rules(rows2, mb)
verified(rows2)
print("tasks newly answered by (a)+(b)+(c):", [b["task"] for a, b in zip(rows, rows2) if b["abc"] and not a["abc"]],
      "right:", [b["cons_right"] for a, b in zip(rows, rows2) if b["abc"] and not a["abc"]])

print("\n=== 5. Against stage 2 (all three test inputs per prompt), same tasks; comparison added in Addendum 4")
S2, n2, e2, k2 = read(S2_FILE)
print(f"stage 2: {n2} lines, {e2} errors, {len(S2)} keys, duplicates {sum(c > 1 for c in k2.values())}")
ALL3 = {t: folds_ht(CO[t], S2, test_k=tuple(range(len(CO[t]["test"])))) for t in TASKS}
F3 = [x for t in TASKS for x in ALL3[t]]
print(f"stage 2, all test pairs: folds {len(F3)}, held-out {P(sum(x['h'] for x in F3) / len(F3))}%, test {P(sum(x['t'] for x in F3) / len(F3))}%,"
      f" difference {P(sum(x['h'] - x['t'] for x in F3) / len(F3))}")
FP = {t: folds_ht(CO[t], S2) for t in TASKS}
common = [t for t in TASKS if len(FP[t]) == len(FC[t])]
s2d = lambda t: sum(x["h"] - x["t"] for x in FP[t])
scd = lambda t: sum(x["h"] - x["t"] for x in FC[t])
nf = lambda t: len(FC[t])
rng = random.Random(0)
bs, bc, bd = [], [], []
for _ in range(B):
    idx = rng.choices(common, k=len(common))
    a = sum(s2d(t) for t in idx)
    b = sum(scd(t) for t in idx)
    nn = sum(nf(t) for t in idx)
    bs.append(a / nn)
    bc.append(b / nn)
    bd.append((b - a) / nn)
N = sum(nf(t) for t in common)
e_s2 = sum(s2d(t) for t in common) / N
e_c = sum(scd(t) for t in common) / N
print(f"tasks {len(common)}, folds {N}; stage 2 first pairs {P(e_s2)} {[P(x) for x in pct(bs)]}; stage C {P(e_c)} {[P(x) for x in pct(bc)]} (same resamples);"
      f" stage C minus stage 2, paired by task {P(e_c - e_s2)} {[P(x) for x in pct(bd)]}")
SUM["s2first"] = (e_s2, pct(bs))
SUM["paired"] = (e_c - e_s2, pct(bd))
print(f"stage 2 first pair: held-out {P(sum(x['h'] for t in common for x in FP[t]) / N)}%, test {P(sum(x['t'] for t in common for x in FP[t]) / N)}%")

print("\n=== 6. re-arc, same harness (generator control), and re-arc minus stage C, post hoc, independent bootstraps")
TR = load_rearc()
for t in TR:
    TR[t]["id"] = t
GM, ng, eg, _ = read(RAW + "gc_qwen_main.jsonl")
FR = {t: folds_ht(TR[t], GM) for t in sorted(TR)}
ff = lambda s: sum(x["h"] - x["t"] for L in s for x in L) / sum(len(L) for L in s)
XR, XC = list(FR.values()), [FC[t] for t in TASKS]
FRl = [x for L in XR for x in L]
print(f"re-arc: tasks {len(XR)}, folds {len(FRl)}, held-out {P(sum(x['h'] for x in FRl) / len(FRl))}%, test {P(sum(x['t'] for x in FRl) / len(FRl))}%, difference {P(ff(XR))} {[P(x) for x in boot(XR, ff)]}")
rng = random.Random(0)
v = []
for _ in range(B):
    a = [XR[rng.randrange(len(XR))] for _ in XR]
    b = [XC[rng.randrange(len(XC))] for _ in XC]
    v.append(ff(a) - ff(b))
print(f"re-arc minus stage C {P(ff(XR) - ff(XC))} {[P(x) for x in pct(v)]}")
SUM["rearc"] = (ff(XR), boot(XR, ff))
SUM["rearc_minus_c"] = (ff(XR) - ff(XC), pct(v))

print("\n=== 7. The one wrong FA-LOO answer")
for r in rows:
    if r["abc"] and not r["cons_right"]:
        t = r["task"]
        task = CO[t]
        fo, _ = out(M[("full", t, -1)])
        g = fo["test:0"]
        dm = demos_of(task)
        print(t, "n =", r["n"], "held-out right", r["held"], "of", r["n"])
        same = [dumps(out(M[("fold", t, i)])[0]["test:0"]) == dumps(g) for i in range(r["n"])]
        print("full and every fold give the same test output:", all(same))
        truth = task["test"][0]["output"]
        line = [i for i, row in enumerate(truth) if len(set(row)) == 1 and row[0] != 0]
        print("test 0: divider row", line, "; truth keeps rows above it:", all(all(c == 0 for c in row) for row in truth[line[0] + 1:]),
              "; output keeps rows below it:", all(all(c == 0 for c in row) for row in g[:line[0]]))
        def contact(gr):
            L = [i for i, row in enumerate(gr) if len(set(row)) == 1 and row[0] != 0][0]
            col = gr[L][0]
            above = sum(c not in (0, col) for c in gr[L - 1]) if L > 0 else 0
            below = sum(c not in (0, col) for c in gr[L + 1]) if L + 1 < len(gr) else 0
            return above, below
        print("cells touching the divider (above, below): demonstrations", [contact(p["input"]) for p in task["train"]], "test 0", contact(task["test"][0]["input"]))
        d2, _ = out(S2.get(("full", t, -1)))
        print("stage 2 (three test inputs), full run's test:0 right:", bool(d2) and eq(d2.get("test:0"), truth),
              "; stage 2 folds' test:0 right:", [x["t"] for x in FP[t]], "held-out right:", [x["h"] for x in FP[t]])

print("\n=== 8. Paper format, own intervals (seed 0), one decimal")
f1 = lambda x: ("+" if x > 0.00049 else "−" if x < -0.00049 else "") + f"{abs(100 * x):.1f}"
for k, label in (("E", "held-out minus test, one test input"), ("s2first", "stage 2 on the same first pairs"), ("paired", "stage C minus stage 2, paired by task"),
                 ("rearc", "re-arc"), ("rearc_minus_c", "re-arc minus stage C, post hoc"), ("split", "held-out split, between"), ("within", "held-out split, within tasks")):
    e, (lo, hi) = SUM[k]
    print(f"{label}: {f1(e)} [{f1(lo)}, {f1(hi)}]")
